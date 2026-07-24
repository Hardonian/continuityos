from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from time import perf_counter
from typing import Annotated, Any, cast
from uuid import uuid4

import orjson
from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from pydantic import BaseModel

from continuityos.analysis import RegressionRequest, RegressionResult, run_regression
from continuityos.compiler import ContinuityCompiler
from continuityos.config import Settings
from continuityos.decision import DecisionPacket, DecisionPacketRequest, build_decision_packet
from continuityos.domain import CompiledPlan, CompileRequest, CorridorAssessment, Observation
from continuityos.evidence import EvidenceLedger, EvidenceRecord
from continuityos.exchange import (
    GeoJSONFeatureCollection,
    export_manifest,
    feature_collection,
    geopackage_bytes,
    ndjson_bytes,
)
from continuityos.fusion import FusionEngine
from continuityos.graph import DependencyEngine, DependencyGraph, GraphAssessment
from continuityos.interoperability import (
    SUPPORTED_CLOUD_EVENT_TYPES,
    CAPAlert,
    ContinuityCloudEvent,
    interoperability_manifest,
    parse_cap_alert,
)
from continuityos.metrics import Metrics
from continuityos.public_data import (
    PUBLIC_SOURCE_SPECS,
    CanadianDisasterDatabaseAdapter,
    DFOIWLSAdapter,
    ECCCGeoMetAdapter,
    NormalizedIndicator,
    PublicDataPlane,
    PublicSnapshot,
)
from continuityos.security import (
    FixedWindowLimiter,
    RateLimitExceeded,
    enforce_rate_limit,
    require_api_key,
)
from continuityos.sources.cache import SnapshotCache
from continuityos.sources.policy import SourcePolicyError, validate_observation_source
from continuityos.sources.registry import SOURCES
from continuityos.state import IdempotencyConflict, PersistentState
from continuityos.strategic import (
    StrategicAnalysisReport,
    StrategicAnalysisRequest,
    build_strategic_report,
)
from continuityos.telemetry import (
    TelemetryAuthenticationError,
    normalized_operator_observation,
    verify_operator_signature,
)

logger = logging.getLogger("continuityos.access")


class AssessmentRequest(BaseModel):
    corridor_id: str
    observations: list[Observation]
    as_of: datetime | None = None


class TelemetryResponse(BaseModel):
    accepted: bool
    observation: Observation


class CAPAlertResponse(BaseModel):
    accepted: bool
    alert: CAPAlert


class PublicSnapshotRequest(BaseModel):
    source_id: str
    force: bool = False


class PublicSnapshotResponse(BaseModel):
    source_id: str
    snapshot_id: str
    content_sha256: str
    retrieved_at: datetime
    status_code: int
    parser: str
    record_count: int
    freshness_hours: float
    quality_flags: list[str]

    @classmethod
    def from_snapshot(cls, snapshot: PublicSnapshot) -> PublicSnapshotResponse:
        return cls(
            source_id=snapshot.source_id,
            snapshot_id=snapshot.snapshot_id,
            content_sha256=snapshot.content_sha256,
            retrieved_at=snapshot.retrieved_at,
            status_code=snapshot.status_code,
            parser=snapshot.parser,
            record_count=snapshot.record_count,
            freshness_hours=snapshot.freshness_hours,
            quality_flags=list(snapshot.quality_flags),
        )


class PublicIndicatorRequest(BaseModel):
    source_id: str
    region: str = "QUE"
    start: datetime | None = None
    end: datetime | None = None
    force: bool = False


class PublicIndicatorResponse(BaseModel):
    indicator_id: str
    observed_at: datetime
    value: float
    unit: str
    source_id: str
    provenance_snapshot_ids: list[str]
    quality_flags: list[str]
    metadata: dict[str, str]

    @classmethod
    def from_indicator(cls, indicator: NormalizedIndicator) -> PublicIndicatorResponse:
        return cls(
            indicator_id=indicator.indicator_id,
            observed_at=indicator.observed_at,
            value=indicator.value,
            unit=indicator.unit,
            source_id=indicator.source_id,
            provenance_snapshot_ids=list(indicator.provenance_snapshot_ids),
            quality_flags=list(indicator.quality_flags),
            metadata=indicator.metadata,
        )


class PublicIndicatorsResponse(BaseModel):
    source_id: str
    snapshot_ids: list[str]
    indicators: list[PublicIndicatorResponse]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def create_app(settings: Settings | None = None) -> FastAPI:
    configured = settings or get_settings()
    configured.data_dir.mkdir(parents=True, exist_ok=True)
    ledger = EvidenceLedger.from_key_files(
        configured.evidence_dir / "ledger.jsonl",
        configured.evidence_private_key_path,
        configured.evidence_public_key_path,
    )
    fusion = FusionEngine()
    compiler = ContinuityCompiler(configured.compiler_max_actions)
    dependency_engine = DependencyEngine()

    app = FastAPI(
        title="ContinuityOS Reference API",
        version="0.1.0",
        default_response_class=JSONResponse,
        docs_url="/docs" if configured.environment != "production" else None,
        openapi_url="/openapi.json" if configured.environment != "production" else None,
        redoc_url=None,
    )
    app.state.settings = configured
    app.state.ledger = ledger
    app.state.metrics = Metrics()
    app.state.rate_limiter = FixedWindowLimiter()
    app.state.persistent_state = PersistentState(configured.data_dir / "state.json")
    app.state.public_data = PublicDataPlane(
        SnapshotCache(configured.data_dir / "public-snapshots"),
        outbound_enabled=configured.outbound_http_enabled,
        timeout_seconds=configured.outbound_timeout_seconds,
    )

    async def idempotency_context(
        request: Request, namespace: str
    ) -> tuple[str | None, str | None, str | None]:
        key = request.headers.get("idempotency-key")
        if key is None:
            return None, None, None
        if not key or len(key) > 128 or any(char.isspace() for char in key):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="invalid idempotency key"
            )
        body = await request.body()
        fingerprint = hashlib.sha256(body + request.url.query.encode("utf-8")).hexdigest()
        try:
            cached = app.state.persistent_state.get_idempotent(namespace, key, fingerprint)
        except IdempotencyConflict as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return key, fingerprint, cached

    def save_idempotency(
        namespace: str, key: str | None, fingerprint: str | None, response: BaseModel
    ) -> None:
        if key is None or fingerprint is None:
            return
        try:
            app.state.persistent_state.save_idempotent(
                namespace, key, fingerprint, response.model_dump_json()
            )
        except IdempotencyConflict as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(_request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "rate limit exceeded", "retry_after": exc.retry_after},
            headers={"Retry-After": str(exc.retry_after)},
        )

    @app.middleware("http")
    async def request_guard(request: Request, call_next: Any) -> Any:
        request_id = request.headers.get("x-request-id") or str(uuid4())
        content_length = request.headers.get("content-length")
        try:
            oversized = (
                content_length is not None and int(content_length) > configured.max_request_bytes
            )
        except ValueError:
            oversized = True
        if oversized:
            response = JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "request body too large", "request_id": request_id},
            )
            response.headers["X-Request-ID"] = request_id
            return response
        started = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            app.state.metrics.observe(perf_counter() - started, 500)
            raise
        app.state.metrics.observe(perf_counter() - started, response.status_code)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
        )
        response.headers["Cache-Control"] = "no-store"
        if request.headers.get("x-forwarded-proto", request.url.scheme) == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        logger.info(
            json.dumps(
                {
                    "event": "request",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": round((perf_counter() - started) * 1000, 3),
                },
                sort_keys=True,
            )
        )
        return response

    @app.get("/livez")
    async def livez() -> dict[str, str]:
        return {"status": "ok"}

    def readiness_payload() -> tuple[dict[str, Any], int]:
        checks = {
            "evidence_directory": configured.evidence_dir.is_dir(),
            "ledger_integrity": not ledger.verify(),
        }
        if configured.environment == "production":
            checks.update(
                {
                    "evidence_private_key": configured.evidence_private_key_path is not None
                    and configured.evidence_private_key_path.is_file(),
                    "evidence_public_key": configured.evidence_public_key_path is not None
                    and configured.evidence_public_key_path.is_file(),
                }
            )
        ready = all(checks.values())
        return {
            "status": "ready" if ready else "not_ready",
            "environment": configured.environment,
            "checks": checks,
        }, (status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE)

    @app.get("/readyz")
    async def readyz() -> JSONResponse:
        payload, code = readiness_payload()
        return JSONResponse(status_code=code, content=payload)

    @app.get("/healthz")
    async def healthz() -> JSONResponse:
        payload, code = readiness_payload()
        payload["status"] = "ok" if code == status.HTTP_200_OK else "degraded"
        payload["outbound_http_enabled"] = configured.outbound_http_enabled
        payload["evidence_ledger_valid"] = bool(payload["checks"]["ledger_integrity"])
        return JSONResponse(status_code=code, content=payload)

    @app.get("/v1/sources")
    async def list_sources() -> list[dict[str, Any]]:
        return [
            {
                "source_id": item.source_id,
                "name": item.name,
                "base_url": item.base_url,
                "trust": item.trust,
                "allowed_assertions": sorted(value.value for value in item.allowed_assertions),
                "licence": item.licence,
                "notes": item.notes,
                "access": item.access,
                "api_key_required": item.api_key_required,
                "cadence": item.cadence,
            }
            for item in sorted(SOURCES.values(), key=lambda source: source.source_id)
        ]

    @app.get(
        "/v1/interoperability",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def interoperability() -> dict[str, object]:
        return interoperability_manifest()

    @app.get(
        "/v1/public-data/sources",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def list_public_data_sources() -> list[dict[str, Any]]:
        return [
            {
                "source_id": spec.source_id,
                "name": spec.name,
                "url": spec.url,
                "method": spec.method,
                "key_env": spec.key_env,
                "key_required": spec.key_env is not None,
                "freshness_hours": spec.freshness_hours,
                "licence": spec.licence,
                "parser": spec.parser,
            }
            for spec in sorted(PUBLIC_SOURCE_SPECS.values(), key=lambda item: item.source_id)
        ]

    @app.post(
        "/v1/public-data/snapshots",
        response_model=PublicSnapshotResponse,
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def fetch_public_snapshot(
        request: Request, snapshot_request: PublicSnapshotRequest
    ) -> PublicSnapshotResponse:
        key, fingerprint, cached = await idempotency_context(request, "public_snapshot")
        if cached is not None:
            return PublicSnapshotResponse.model_validate_json(cached)
        try:
            snapshot = await cast(PublicDataPlane, app.state.public_data).fetch(
                snapshot_request.source_id,
                force=snapshot_request.force,
            )
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
            ) from exc
        except (KeyError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        response = PublicSnapshotResponse.from_snapshot(snapshot)
        ledger.append(
            "public_data_snapshot", snapshot.snapshot_id, response.model_dump(mode="json")
        )
        save_idempotency("public_snapshot", key, fingerprint, response)
        return response

    @app.post(
        "/v1/public-data/indicators",
        response_model=PublicIndicatorsResponse,
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def fetch_public_indicators(
        request: Request, indicator_request: PublicIndicatorRequest
    ) -> PublicIndicatorsResponse:
        key, fingerprint, cached = await idempotency_context(request, "public_indicators")
        if cached is not None:
            return PublicIndicatorsResponse.model_validate_json(cached)
        plane = cast(PublicDataPlane, app.state.public_data)
        try:
            if indicator_request.source_id == "eccc-geomet-alerts":
                snapshot, indicators = await ECCCGeoMetAdapter.fetch(
                    plane, force=indicator_request.force
                )
                snapshot_ids = [snapshot.snapshot_id]
            elif indicator_request.source_id == "canadian-disaster-database":
                snapshot, indicators = await CanadianDisasterDatabaseAdapter.fetch(
                    plane, force=indicator_request.force
                )
                snapshot_ids = [snapshot.snapshot_id]
            elif indicator_request.source_id == "dfo-iwls":
                if indicator_request.start is None or indicator_request.end is None:
                    raise ValueError("DFO indicators require timezone-aware start and end")
                (
                    station_snapshot,
                    data_snapshot,
                    _station,
                    indicators,
                ) = await DFOIWLSAdapter.fetch_current(
                    plane,
                    region=indicator_request.region,
                    start=indicator_request.start,
                    end=indicator_request.end,
                    force=indicator_request.force,
                )
                snapshot_ids = [station_snapshot.snapshot_id, data_snapshot.snapshot_id]
            else:
                raise ValueError("indicator adapter is not implemented for this source")
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
            ) from exc
        except (KeyError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        response = PublicIndicatorsResponse(
            source_id=indicator_request.source_id,
            snapshot_ids=snapshot_ids,
            indicators=[PublicIndicatorResponse.from_indicator(item) for item in indicators],
        )
        ledger.append(
            "public_data_indicators",
            ":".join(snapshot_ids),
            response.model_dump(mode="json"),
        )
        save_idempotency("public_indicators", key, fingerprint, response)
        return response

    @app.get("/metrics", response_class=PlainTextResponse)
    async def metrics() -> str:
        return cast(Metrics, app.state.metrics).prometheus()

    @app.post(
        "/v1/assess",
        response_model=CorridorAssessment,
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def assess(request: Request, assessment_request: AssessmentRequest) -> CorridorAssessment:
        key, fingerprint, cached = await idempotency_context(request, "assess")
        if cached is not None:
            return CorridorAssessment.model_validate_json(cached)
        try:
            assessment = fusion.assess(
                assessment_request.corridor_id,
                assessment_request.observations,
                as_of=assessment_request.as_of,
            )
        except (SourcePolicyError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        ledger.append(
            "corridor_assessment",
            str(assessment.assessment_id),
            assessment.model_dump(mode="json"),
        )
        save_idempotency("assess", key, fingerprint, assessment)
        return assessment

    @app.post(
        "/v1/analysis/regression",
        response_model=RegressionResult,
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def regression_analysis(
        request: Request, regression_request: RegressionRequest
    ) -> RegressionResult:
        key, fingerprint, cached = await idempotency_context(request, "regression")
        if cached is not None:
            return RegressionResult.model_validate_json(cached)
        try:
            result = run_regression(regression_request)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        ledger.append(
            "multivariate_regression",
            regression_request.dataset_id,
            result.model_dump(mode="json"),
        )
        save_idempotency("regression", key, fingerprint, result)
        return result

    @app.post(
        "/v1/graph/analyze",
        response_model=GraphAssessment,
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def analyze_graph(
        request: Request,
        graph: DependencyGraph,
        failed_nodes: Annotated[list[str], Query(min_length=1)],
    ) -> GraphAssessment:
        key, fingerprint, cached = await idempotency_context(request, "graph-analyze")
        if cached is not None:
            return GraphAssessment.model_validate_json(cached)
        try:
            result = dependency_engine.analyze(graph, set(failed_nodes))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        ledger.append("dependency_graph_assessment", graph.graph_id, result.model_dump(mode="json"))
        save_idempotency("graph-analyze", key, fingerprint, result)
        return result

    @app.post(
        "/v1/compile",
        response_model=CompiledPlan,
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def compile_plan(request: Request, compile_request: CompileRequest) -> CompiledPlan:
        key, fingerprint, cached = await idempotency_context(request, "compile")
        if cached is not None:
            return CompiledPlan.model_validate_json(cached)
        try:
            plan = compiler.compile(compile_request)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        ledger.append("compiled_plan", str(plan.plan_id), plan.model_dump(mode="json"))
        save_idempotency("compile", key, fingerprint, plan)
        return plan

    @app.post(
        "/v1/decision-packets",
        response_model=DecisionPacket,
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def create_decision_packet(
        request: Request,
        packet_request: DecisionPacketRequest,
    ) -> DecisionPacket:
        key, fingerprint, cached = await idempotency_context(request, "decision-packets")
        if cached is not None:
            return DecisionPacket.model_validate_json(cached)
        try:
            packet = build_decision_packet(
                packet_request,
                fusion=fusion,
                dependency_engine=dependency_engine,
                compiler=compiler,
                evidence_manifest=export_manifest(ledger.records(0, 1000)),
            )
        except (SourcePolicyError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        ledger.append(
            "corridor_assessment",
            str(packet.assessment.assessment_id),
            packet.assessment.model_dump(mode="json"),
        )
        ledger.append(
            "dependency_graph_assessment",
            packet.dependency_assessment.graph_id,
            packet.dependency_assessment.model_dump(mode="json"),
        )
        ledger.append(
            "compiled_plan",
            str(packet.plan.plan_id),
            packet.plan.model_dump(mode="json"),
        )
        ledger.append("decision_packet", str(packet.packet_id), packet.model_dump(mode="json"))
        save_idempotency("decision-packets", key, fingerprint, packet)
        return packet

    @app.post(
        "/v1/strategic/analyze",
        response_model=StrategicAnalysisReport,
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def strategic_analyze(
        request: Request,
        analysis_request: StrategicAnalysisRequest,
    ) -> StrategicAnalysisReport:
        key, fingerprint, cached = await idempotency_context(request, "strategic-analyze")
        if cached is not None:
            return StrategicAnalysisReport.model_validate_json(cached)
        try:
            report = build_strategic_report(analysis_request)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        ledger.append("strategic_analysis", str(report.report_id), report.model_dump(mode="json"))
        save_idempotency("strategic-analyze", key, fingerprint, report)
        return report

    def accept_operator_payload(
        payload: dict[str, Any],
        body: bytes,
        timestamp: str,
        signature: str,
        key: str | None,
        fingerprint: str | None,
    ) -> TelemetryResponse:
        if configured.operator_webhook_secret is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="telemetry disabled",
            )
        try:
            verify_operator_signature(
                body=body,
                timestamp=timestamp,
                signature=signature,
                secret=configured.operator_webhook_secret,
            )
            observation = normalized_operator_observation(payload, body)
            validate_observation_source(observation)
        except (TelemetryAuthenticationError, SourcePolicyError, ValueError, KeyError) as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
        tenant_id = str(observation.metadata["tenant_id"])
        asset_id = str(observation.metadata["asset_id"])
        sequence = int(observation.metadata["sequence"])
        if not app.state.persistent_state.claim_sequence(tenant_id, asset_id, sequence):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="telemetry replay rejected",
            )
        ledger.append(
            "operator_observation",
            str(observation.observation_id),
            observation.model_dump(mode="json"),
        )
        response = TelemetryResponse(accepted=True, observation=observation)
        save_idempotency("operator-observations", key, fingerprint, response)
        return response

    @app.post(
        "/v1/operator-observations",
        response_model=TelemetryResponse,
        dependencies=[Depends(enforce_rate_limit)],
    )
    async def ingest_operator_observation(
        request: Request,
        x_continuity_timestamp: Annotated[str, Header()],
        x_continuity_signature: Annotated[str, Header()],
        payload: Annotated[dict[str, Any], Body(...)],
    ) -> TelemetryResponse:
        key, fingerprint, cached = await idempotency_context(request, "operator-observations")
        if cached is not None:
            return TelemetryResponse.model_validate_json(cached)
        body = orjson.dumps(payload, option=orjson.OPT_SORT_KEYS)
        return accept_operator_payload(
            payload, body, x_continuity_timestamp, x_continuity_signature, key, fingerprint
        )

    @app.post(
        "/v1/integrations/cloudevents",
        response_model=TelemetryResponse,
        dependencies=[Depends(enforce_rate_limit)],
    )
    async def ingest_cloudevent(
        request: Request,
        x_continuity_timestamp: Annotated[str, Header()],
        x_continuity_signature: Annotated[str, Header()],
        event: ContinuityCloudEvent,
    ) -> TelemetryResponse:
        if event.type not in SUPPORTED_CLOUD_EVENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="unsupported CloudEvent type",
            )
        body = orjson.dumps(event.model_dump(mode="json"), option=orjson.OPT_SORT_KEYS)
        key = request.headers.get("idempotency-key") or event.id
        if not key or len(key) > 128 or any(char.isspace() for char in key):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="invalid idempotency key"
            )
        fingerprint = hashlib.sha256(body + request.url.query.encode("utf-8")).hexdigest()
        try:
            cached = app.state.persistent_state.get_idempotent(
                "operator-observations", key, fingerprint
            )
        except IdempotencyConflict as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        if cached is not None:
            return TelemetryResponse.model_validate_json(cached)
        return accept_operator_payload(
            event.data, body, x_continuity_timestamp, x_continuity_signature, key, fingerprint
        )

    @app.post(
        "/v1/integrations/cap",
        response_model=CAPAlertResponse,
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def ingest_cap_alert(
        request: Request, payload: Annotated[bytes, Body(...)]
    ) -> CAPAlertResponse:
        key, fingerprint, cached = await idempotency_context(request, "cap-alerts")
        if cached is not None:
            return CAPAlertResponse.model_validate_json(cached)
        try:
            alert = parse_cap_alert(payload)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        response = CAPAlertResponse(accepted=True, alert=alert)
        ledger.append("cap_alert", alert.identifier, response.model_dump(mode="json"))
        save_idempotency("cap-alerts", key, fingerprint, response)
        return response

    @app.get(
        "/v1/ogc/collections",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def ogc_collections(request: Request) -> dict[str, Any]:
        base = str(request.base_url).rstrip("/")
        return {
            "title": "ContinuityOS evidence collections",
            "links": [{"rel": "self", "href": f"{base}/v1/ogc/collections"}],
            "collections": [
                {
                    "id": "evidence",
                    "title": "Immutable continuity evidence",
                    "description": "Read-only bounded evidence snapshot; not a live feature feed.",
                    "itemType": "feature",
                    "crs": ["http://www.opengis.net/def/crs/OGC/1.3/CRS84"],
                    "links": [
                        {
                            "rel": "items",
                            "href": f"{base}/v1/ogc/collections/evidence/items",
                            "type": "application/geo+json",
                        }
                    ],
                }
            ],
        }

    @app.get(
        "/v1/ogc/collections/evidence/items",
        response_model=GeoJSONFeatureCollection,
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def ogc_evidence_items(
        request: Request,
        offset: Annotated[int, Query(ge=0, le=1_000_000)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 100,
    ) -> GeoJSONFeatureCollection:
        bounded = ledger.records(0, 1000)
        page = bounded[offset : offset + limit]
        return feature_collection(page, str(request.url).split("?")[0])

    @app.get(
        "/v1/exports/evidence/manifest",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def evidence_export_manifest() -> dict[str, Any]:
        return export_manifest(ledger.records(0, 1000)).model_dump(mode="json")

    @app.get(
        "/v1/exports/evidence/ndjson",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def evidence_ndjson() -> Response:
        return Response(
            content=ndjson_bytes(ledger.records(0, 1000)),
            media_type="application/x-ndjson",
            headers={"Content-Disposition": 'attachment; filename="continuityos-evidence.ndjson"'},
        )

    @app.get(
        "/v1/exports/evidence/geopackage",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def evidence_geopackage() -> Response:
        return Response(
            content=geopackage_bytes(ledger.records(0, 1000)),
            media_type="application/geopackage+sqlite3",
            headers={"Content-Disposition": 'attachment; filename="continuityos-evidence.gpkg"'},
        )

    @app.get(
        "/v1/stac/catalog",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def stac_catalog(request: Request) -> dict[str, Any]:
        base = str(request.base_url).rstrip("/")
        return {
            "stac_version": "1.0.0",
            "id": "continuityos-evidence",
            "type": "Catalog",
            "title": "ContinuityOS evidence catalog",
            "description": (
                "Metadata catalog for immutable evidence exports; no imagery assets are implied."
            ),
            "links": [
                {"rel": "self", "href": f"{base}/v1/stac/catalog", "type": "application/json"},
                {
                    "rel": "child",
                    "href": f"{base}/v1/exports/evidence/manifest",
                    "type": "application/json",
                },
            ],
        }

    @app.get(
        "/v1/evidence/verify",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def verify_evidence() -> dict[str, Any]:
        errors = ledger.verify()
        return {"valid": not errors, "errors": errors}

    @app.get(
        "/v1/evidence",
        response_model=list[EvidenceRecord],
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def read_evidence(
        offset: Annotated[int, Query(ge=0, le=1_000_000)] = 0,
        limit: Annotated[int, Query(ge=1, le=1_000)] = 100,
    ) -> list[EvidenceRecord]:
        path: Path = ledger.path
        if not path.exists():
            return []
        lines = path.read_text().splitlines()[offset : offset + limit]
        return [EvidenceRecord.model_validate_json(line) for line in lines]

    return app


app = create_app()
