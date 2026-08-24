from __future__ import annotations

import asyncio
import hashlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from time import perf_counter
from typing import Annotated, Any, cast
from uuid import uuid4

import orjson
from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, Response, StreamingResponse
from pydantic import BaseModel

from continuityos.analysis import RegressionRequest, RegressionResult, run_regression
from continuityos.compiler import ContinuityCompiler
from continuityos.config import Settings
from continuityos.counter_intel import (
    DarkFleetDetector,
    SARSatelliteOverflightPredictor,
)
from continuityos.crypto import ZKPReserveProof
from continuityos.decision import DecisionPacket, DecisionPacketRequest, build_decision_packet
from continuityos.domain import CompiledPlan, CompileRequest, CorridorAssessment, Observation
from continuityos.edge import EdgeNode
from continuityos.environmental import (
    PermafrostDegradationModel,
    SubseaAcousticMonitor,
    WildfireCorridorRiskModel,
)
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
from continuityos.intelligence import AgenticIntelligenceEngine
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


class VerifyReserveResponse(BaseModel):
    valid: bool
    policy_minimum: int
    commitment_hash_hex: str
    message: str


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

    @asynccontextmanager
    async def app_lifespan(app_instance: FastAPI) -> AsyncIterator[None]:
        if configured.edge_enabled:
            app_instance.state.edge_node.start()
        yield
        if configured.edge_enabled:
            await app_instance.state.edge_node.stop()

    app = FastAPI(
        lifespan=app_lifespan,
        title="Aegis Continuity (Sovereign Edition) API",
        version="0.1.0",
        description=(
            "Sovereign Resilience-as-Code & Cyber-Physical Corridor Assurance Engine "
            "for Ministries of Defense and critical trade corridors."
        ),
        contact={
            "name": "ContinuityOS",
            "url": "https://continuityos.io",
        },
        license_info={
            "name": "Apache 2.0",
            "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
        },
        default_response_class=JSONResponse,
        docs_url="/docs" if configured.environment != "production" else None,
        openapi_url="/openapi.json" if configured.environment != "production" else None,
        redoc_url=None,
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=configured.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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

    app.state.intelligence_engine = AgenticIntelligenceEngine(
        llm_endpoint=configured.llm_endpoint,
        model=configured.llm_model,
    )

    app.state.edge_node = EdgeNode(
        node_id=str(uuid4())[:8],
        cache=app.state.public_data.cache,
        gossip_interval=configured.edge_gossip_interval_seconds,
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
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Resource-Policy"] = "same-site"
        response.headers["Cache-Control"] = "no-store"
        if request.headers.get("x-forwarded-proto", request.url.scheme) == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        logger.info(
            orjson.dumps(
                {
                    "event": "request",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": round((perf_counter() - started) * 1000, 3),
                },
                option=orjson.OPT_SORT_KEYS,
            ).decode("utf-8")
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
        "/v1/crypto/verify-reserve-proof",
        response_model=VerifyReserveResponse,
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def verify_reserve_proof(
        request: Request, proof: ZKPReserveProof
    ) -> VerifyReserveResponse:
        key, fingerprint, cached = await idempotency_context(request, "verify-reserve")
        if cached is not None:
            return VerifyReserveResponse.model_validate_json(cached)

        is_valid = proof.verify()
        response = VerifyReserveResponse(
            valid=is_valid,
            policy_minimum=proof.policy_minimum,
            commitment_hash_hex=proof.commitment_hash_hex,
            message="Zero-Knowledge Proof mathematically verified."
            if is_valid
            else "Zero-Knowledge Proof verification failed.",
        )
        ledger.append(
            "zkp_reserve_verification", proof.commitment_hash_hex, response.model_dump(mode="json")
        )
        save_idempotency("verify-reserve", key, fingerprint, response)

        if not is_valid:
            raise HTTPException(status_code=400, detail="ZKP Reserve Proof verification failed.")

        return response

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
            cached_report = StrategicAnalysisReport.model_validate_json(cached)
            for alert in cached_report.alerts:
                previous = app.state.persistent_state.get_value("strategic_alerts", alert.alert_key)
                if isinstance(previous, dict) and previous.get("acknowledged"):
                    alert.delivery_state = "acknowledged"
            app.state.persistent_state.set_value(
                "strategic", "latest", cached_report.model_dump(mode="json")
            )
            return cached_report
        try:
            report = build_strategic_report(analysis_request)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        now = datetime.now(UTC)
        for alert in report.alerts:
            previous = app.state.persistent_state.get_value("strategic_alerts", alert.alert_key)
            previous = previous if isinstance(previous, dict) else {}
            acknowledged = bool(previous.get("acknowledged", False))
            last_emitted = previous.get("last_emitted_at")
            in_cooldown = False
            if isinstance(last_emitted, str):
                try:
                    elapsed = (now - datetime.fromisoformat(last_emitted)).total_seconds()
                    in_cooldown = elapsed < analysis_request.alert_cooldown_seconds
                except ValueError:
                    in_cooldown = False
            alert.delivery_state = (
                "acknowledged" if acknowledged else ("cooldown" if in_cooldown else "ready")
            )
            due_at = previous.get("escalation_due_at")
            if not isinstance(due_at, str):
                seconds = 900 if alert.severity == "critical" else 3600
                due_at = (now + timedelta(seconds=seconds)).isoformat()
            alert.escalation_due_at = datetime.fromisoformat(due_at)
            app.state.persistent_state.set_value(
                "strategic_alerts",
                alert.alert_key,
                {
                    "acknowledged": acknowledged,
                    "last_emitted_at": now.isoformat() if not in_cooldown else last_emitted,
                    "escalation_due_at": due_at,
                    "dimension": alert.dimension,
                },
            )
        report_payload = report.model_dump(mode="json")
        app.state.persistent_state.set_value("strategic", "latest", report_payload)
        ledger.append("strategic_analysis", str(report.report_id), report_payload)
        save_idempotency("strategic-analyze", key, fingerprint, report)
        return report

    @app.post(
        "/v1/strategic/alerts/{alert_key}/ack",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def acknowledge_strategic_alert(alert_key: str) -> dict[str, Any]:
        if len(alert_key) > 512 or not alert_key:
            raise HTTPException(status_code=400, detail="invalid alert key")
        previous = app.state.persistent_state.get_value("strategic_alerts", alert_key)
        record = previous if isinstance(previous, dict) else {}
        record["acknowledged"] = True
        record["acknowledged_at"] = datetime.now(UTC).isoformat()
        app.state.persistent_state.set_value("strategic_alerts", alert_key, record)
        latest = app.state.persistent_state.get_value("strategic", "latest")
        if isinstance(latest, dict):
            for alert in latest.get("alerts", []):
                if isinstance(alert, dict) and alert.get("alert_key") == alert_key:
                    alert["delivery_state"] = "acknowledged"
            app.state.persistent_state.set_value("strategic", "latest", latest)
        ledger.append("strategic_alert_acknowledgement", alert_key, {"alert_key": alert_key})
        return {"alert_key": alert_key, "acknowledged": True}

    @app.post(
        "/v1/strategic/alerts/{alert_key}/unack",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def unacknowledge_strategic_alert(alert_key: str) -> dict[str, Any]:
        if len(alert_key) > 512 or not alert_key:
            raise HTTPException(status_code=400, detail="invalid alert key")
        record = app.state.persistent_state.get_value("strategic_alerts", alert_key)
        record = record if isinstance(record, dict) else {}
        record["acknowledged"] = False
        record["unacknowledged_at"] = datetime.now(UTC).isoformat()
        app.state.persistent_state.set_value("strategic_alerts", alert_key, record)
        latest = app.state.persistent_state.get_value("strategic", "latest")
        if isinstance(latest, dict):
            for alert in latest.get("alerts", []):
                if isinstance(alert, dict) and alert.get("alert_key") == alert_key:
                    alert["delivery_state"] = "ready"
            app.state.persistent_state.set_value("strategic", "latest", latest)
        ledger.append("strategic_alert_unacknowledgement", alert_key, {"alert_key": alert_key})
        return {"alert_key": alert_key, "acknowledged": False}

    @app.get(
        "/v1/strategic/stream",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def strategic_stream(
        duration_seconds: Annotated[int, Query(ge=1, le=60)] = 15,
    ) -> StreamingResponse:
        async def events() -> AsyncIterator[str]:
            deadline = asyncio.get_running_loop().time() + duration_seconds
            sent_report_id: str | None = None
            while asyncio.get_running_loop().time() < deadline:
                latest = app.state.persistent_state.get_value("strategic", "latest")
                if isinstance(latest, dict):
                    report_id = str(latest.get("report_id"))
                    if report_id != sent_report_id:
                        payload = orjson.dumps(latest).decode("utf-8")
                        yield f"event: strategic\ndata: {payload}\n\n"
                        sent_report_id = report_id
                yield ": heartbeat\n\n"
                await asyncio.sleep(2)

        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

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

    @app.post(
        "/v1/sovereign/audit",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def sovereign_audit() -> dict[str, Any]:
        from continuityos.sovereign import AirGapAuditor

        report = AirGapAuditor().audit(Path("."))
        return report.model_dump(mode="json")

    @app.post(
        "/v1/readiness",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def evaluate_readiness_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        from continuityos.domain import CorridorState
        from continuityos.readiness import ReadinessEngine

        theater_id = str(payload.get("theater_id", "theater-1"))
        overall_continuity = float(payload.get("overall_continuity", 0.95))
        inventory_reserve_days = float(payload.get("inventory_reserve_days", 30.0))
        corridor_state = CorridorState.from_str(str(payload.get("corridor_state", "open")))
        res = ReadinessEngine().evaluate_readiness(
            theater_id,
            overall_continuity=overall_continuity,
            inventory_reserve_days=inventory_reserve_days,
            corridor_state=corridor_state,
        )
        return res.model_dump(mode="json")

    @app.post(
        "/v1/cop/export",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def export_cop_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        from continuityos.cop import export_cop_feature, export_cop_feature_collection
        from continuityos.domain import CorridorAssessment

        assessment = CorridorAssessment.model_validate(payload.get("assessment", payload))
        corridor_id = str(payload.get("corridor_id", "corridor-1"))
        banner = str(payload.get("security_banner", "UNCLASSIFIED"))
        coords = payload.get("coordinates")
        feature = export_cop_feature(
            corridor_id, assessment, coordinates=coords, security_banner=banner
        )
        return export_cop_feature_collection([feature])

    @app.post(
        "/v1/inventory/simulate",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def simulate_inventory_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        from continuityos.inventory import InventoryProfile, simulate_inventory

        profile = InventoryProfile.model_validate(payload.get("profile", payload))
        days = int(payload.get("simulation_days", 90))
        degraded = bool(payload.get("degraded", False))
        disrupted = bool(payload.get("disrupted_replenishment", False))
        res = simulate_inventory(
            profile,
            simulation_days=days,
            degraded=degraded,
            disrupted_replenishment=disrupted,
        )
        return res.model_dump(mode="json")

    @app.post(
        "/v1/recovery/model",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def model_recovery_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        from continuityos.recovery import RecoveryProfile, model_recovery

        profile = RecoveryProfile.model_validate(payload.get("profile", payload))
        days_since = int(payload.get("days_since_incident", 0))
        res = model_recovery(profile, days_since_incident=days_since)
        return res.model_dump(mode="json")

    @app.post(
        "/v1/scenarios/simulate",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def simulate_scenario_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        from continuityos.graph import DependencyGraph
        from continuityos.scenario import Scenario, simulate_scenario

        scenario = Scenario.model_validate(payload["scenario"])
        graph = DependencyGraph.model_validate(payload["graph"])
        res = simulate_scenario(scenario, graph)
        return res.model_dump(mode="json")

    @app.post(
        "/v1/threats/scan",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def threat_scan_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        from continuityos.threat import ThreatDetectionEngine

        engine = ThreatDetectionEngine()
        scan = engine.run_full_scan(
            resource_ref=str(payload.get("resource_ref", "corridor-target")),
            gnss_residuals=payload.get("gnss_residuals"),
            cno_ratios=payload.get("cno_ratios"),
            clock_drift_ppm=float(payload.get("clock_drift_ppm", 0.0)),
            scada_cmd_rate=float(payload.get("scada_cmd_rate", 5.0)),
            unauthorized_fc=payload.get("unauthorized_fc"),
            untrusted_ips=int(payload.get("untrusted_ips", 0)),
            plc_hashes=payload.get("plc_hashes"),
            expected_plc_hash=str(payload.get("expected_plc_hash", "a1b2c3d4e5f6")),
            ais_coords=tuple(payload["ais_coords"]) if "ais_coords" in payload else None,
        )
        return scan.model_dump(mode="json")

    @app.post(
        "/v1/intelligence/forecast",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def intelligence_forecast_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        from continuityos.graph import DependencyGraph
        from continuityos.intelligence import BayesianCascadeForecaster

        graph = DependencyGraph.model_validate(payload["graph"])
        target_node = str(payload.get("target_node", graph.nodes[0].node_id))
        degradations = {
            str(k): float(v) for k, v in payload.get("observed_degradations", {}).items()
        }
        res = BayesianCascadeForecaster().forecast(graph, target_node, degradations)
        return res.model_dump(mode="json")

    @app.post(
        "/v1/intelligence/xai",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def intelligence_xai_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        from continuityos.domain import CorridorAssessment
        from continuityos.intelligence import XAIRiskExplainer

        assessment = CorridorAssessment.model_validate(payload.get("assessment", payload))
        res = XAIRiskExplainer().explain(assessment)
        return res.model_dump(mode="json")

    @app.post(
        "/v1/crypto/merkle-verify",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def crypto_merkle_verify_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        from continuityos.crypto import MerkleInclusionProof

        proof = MerkleInclusionProof.model_validate(payload)
        is_valid = proof.verify()
        return {"valid": is_valid, "root_hash": proof.root_hash, "leaf_hash": proof.leaf_hash}

    @app.post(
        "/v1/intelligence/briefing",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def intelligence_briefing_endpoint(
        payload: dict[str, Any], request: Request
    ) -> dict[str, Any]:
        packet = DecisionPacket.model_validate(payload)
        engine: AgenticIntelligenceEngine = request.app.state.intelligence_engine
        briefing = await engine.generate_briefing(packet)
        return briefing.model_dump(mode="json")

    @app.get("/v1/edge/manifest")
    async def edge_manifest_endpoint(request: Request) -> dict[str, Any]:
        if not request.app.state.settings.edge_enabled:
            raise HTTPException(status_code=403, detail="Edge protocol disabled")
        node: EdgeNode = request.app.state.edge_node
        return node.get_manifest().model_dump(mode="json")

    @app.get("/v1/edge/sync/{snapshot_id}")
    async def edge_sync_endpoint(request: Request, snapshot_id: str) -> dict[str, Any]:
        if not request.app.state.settings.edge_enabled:
            raise HTTPException(status_code=403, detail="Edge protocol disabled")

        # In a real app we'd fetch the exact snapshot payload and metadata from SnapshotCache.
        # Here we just look through the cache directories for simplicity.
        cache = request.app.state.public_data.cache
        for metadata_path in cache.root.glob("*/*/*/metadata.json"):
            import json

            try:
                data = json.loads(metadata_path.read_text())
                if data["snapshot_id"] == snapshot_id:
                    payload_path = metadata_path.parent / "payload.bin"
                    body = payload_path.read_bytes()
                    return {"metadata": data, "payload": body.hex()}
            except (json.JSONDecodeError, KeyError, FileNotFoundError):
                continue
        raise HTTPException(status_code=404, detail="Snapshot not found")

    @app.post("/v1/edge/peers")
    async def edge_add_peer_endpoint(request: Request, payload: dict[str, str]) -> dict[str, str]:
        if not request.app.state.settings.edge_enabled:
            raise HTTPException(status_code=403, detail="Edge protocol disabled")

        peer_url = payload.get("url")
        if not peer_url:
            raise HTTPException(status_code=400, detail="Missing peer url")

        node: EdgeNode = request.app.state.edge_node
        node.add_peer(peer_url)
        return {"status": "ok", "message": f"Added peer {peer_url}"}

    @app.post(
        "/v1/tactical/uav/analyze",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def tactical_uav_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        from continuityos.tactical import TacticalFusionBridge, UAVTacticalEngine, UAVTelemetryFrame

        frame = UAVTelemetryFrame.model_validate(payload)
        assessment = UAVTacticalEngine().analyze_frame(frame)
        observations = TacticalFusionBridge.uav_to_observations(assessment, frame)
        return {
            "assessment": assessment.model_dump(mode="json"),
            "observations": [o.model_dump(mode="json") for o in observations],
        }

    @app.post(
        "/v1/tactical/starlink/analyze",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def tactical_starlink_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        from continuityos.tactical import (
            StarlinkTacticalEngine,
            StarlinkTelemetry,
            TacticalFusionBridge,
        )

        telemetry = StarlinkTelemetry.model_validate(payload)
        assessment = StarlinkTacticalEngine().evaluate_channel(telemetry)
        observations = TacticalFusionBridge.starlink_to_observations(assessment, telemetry)
        return {
            "assessment": assessment.model_dump(mode="json"),
            "observations": [o.model_dump(mode="json") for o in observations],
        }

    @app.post(
        "/v1/tactical/cuas/analyze",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def tactical_cuas_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        from continuityos.tactical import (
            CUASDefenseEngine,
            CUASDetectionEvent,
            TacticalFusionBridge,
        )

        sector = str(payload.get("sector", "SECTOR-ALPHA"))
        raw_events = payload.get("events", [])
        events = [CUASDetectionEvent.model_validate(e) for e in raw_events]
        assessment = CUASDefenseEngine().analyze_events(sector, events)
        observations = TacticalFusionBridge.cuas_to_observations(assessment, sector)
        return {
            "assessment": assessment.model_dump(mode="json"),
            "observations": [o.model_dump(mode="json") for o in observations],
        }

    @app.post(
        "/v1/embedded/compile-package",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def embedded_compile_package_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        from continuityos.embedded import (
            EmbeddedArchitectureEngine,
            TargetMicrocontroller,
            TinyMoEConfig,
        )

        target_str = payload.get("target", "esp32-s3")
        target = TargetMicrocontroller(target_str)
        moe_dict = payload.get("moe_config")
        moe_config = TinyMoEConfig.model_validate(moe_dict) if moe_dict else None

        pkg = EmbeddedArchitectureEngine().compile_package(target, moe_config)
        return pkg.model_dump(mode="json")

    @app.post(
        "/v1/embedded/micro-telemetry/encode",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def embedded_micro_encode_endpoint(payload: dict[str, Any]) -> dict[str, str]:
        from continuityos.embedded import CompactBinaryProtocolCodec

        frame_bytes = CompactBinaryProtocolCodec.encode(
            node_id=int(payload.get("node_id", 1)),
            sequence_id=int(payload.get("sequence_id", 0)),
            timestamp_unix=int(payload.get("timestamp_unix", 1700000000)),
            latitude=float(payload.get("latitude", 0.0)),
            longitude=float(payload.get("longitude", 0.0)),
            altitude_m=int(payload.get("altitude_m", 0)),
            threat_flags=int(payload.get("threat_flags", 0)),
            risk_score=float(payload.get("risk_score", 0.0)),
            rssi_dbm=int(payload.get("rssi_dbm", -70)),
            battery_pct=int(payload.get("battery_pct", 100)),
        )
        return {"frame_hex": frame_bytes.hex(), "size_bytes": str(len(frame_bytes))}

    @app.post(
        "/v1/embedded/micro-telemetry/decode",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def embedded_micro_decode_endpoint(payload: dict[str, str]) -> dict[str, Any]:
        from continuityos.embedded import CompactBinaryProtocolCodec

        frame_hex = payload.get("frame_hex", "")
        frame_bytes = bytes.fromhex(frame_hex)
        packet = CompactBinaryProtocolCodec.decode(frame_bytes)
        return packet.model_dump(mode="json")

    # --- Canadian Sovereign & Enterprise Supply Chain Endpoints ---

    @app.get("/v1/canadian/corridors")
    async def list_canadian_corridors() -> dict[str, Any]:
        corridors = [
            {
                "corridor_id": "can-critical-minerals-ring-of-fire",
                "name": "Ontario Ring of Fire to Windsor EV Gigafactory Corridor",
                "category": "CRITICAL_MINERALS",
                "strategic_importance": "TIER_1_SOVEREIGN",
                "key_nodes": [
                    "Eskers-Mine-Hub",
                    "Sudbury-Smelter",
                    "Windsor-EV-Plant",
                    "Montreal-Port-Export",
                ],
                "transport_modes": ["RAIL_CN", "RAIL_CPKC", "LONG_HAUL_TRUCK", "MARITIME"],
                "resilience_status": "MONITORED_NOMINAL",
            },
            {
                "corridor_id": "can-arctic-norad-northern-logistics",
                "name": "Canadian Arctic & NORAD Northern Defense Corridor",
                "category": "NORTHERN_SOVEREIGNTY",
                "strategic_importance": "NATIONAL_DEFENSE",
                "key_nodes": [
                    "Nanisivik-Transition-Hub",
                    "CFS-Alert",
                    "Churchill-Deepwater-Port",
                    "Iqaluit-Forward-Operating-Location",
                ],
                "transport_modes": ["MARITIME", "AIR_CARGO", "ICEBREAKER_ESCORT"],
                "resilience_status": "HIGH_SURVEILLANCE",
            },
            {
                "corridor_id": "can-trans-canada-intermodal-rail",
                "name": "Trans-Canada CPKC & CN Intermodal Freight Corridor",
                "category": "INTERMODAL_FREIGHT",
                "strategic_importance": "NATIONAL_COMMERCE",
                "key_nodes": [
                    "Port-of-Vancouver",
                    "Prince-Rupert",
                    "Calgary-Intermodal-Yard",
                    "Toronto-Logistics-Hub",
                    "Port-of-Halifax",
                ],
                "transport_modes": ["RAIL_CPKC", "RAIL_CN", "LONG_HAUL_TRUCK"],
                "resilience_status": "MONITORED_NOMINAL",
            },
            {
                "corridor_id": "can-st-lawrence-seaway-locks",
                "name": "St. Lawrence Seaway & Great Lakes Maritime Lock Corridor",
                "category": "MARITIME_BULK_COMMODITIES",
                "strategic_importance": "COMMERCIAL_STRATEGIC",
                "key_nodes": [
                    "Welland-Canal-Lock-8",
                    "Montreal-Lake-Ontario-Locks",
                    "Port-of-Montreal",
                    "Port-of-Quebec",
                ],
                "transport_modes": ["MARITIME", "RAIL_CN"],
                "resilience_status": "SEASONAL_MONITORING",
            },
        ]
        return {"corridors": corridors, "count": len(corridors), "sovereign_region": "CANADA"}

    @app.post(
        "/v1/supply-chain/bom-assess",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def assess_supply_chain_bom(payload: dict[str, Any]) -> dict[str, Any]:
        from continuityos.supply_chain import BOMComponent, MultiTierSupplyEngine

        system_name = str(payload.get("system_name", "Critical-Supply-Network"))
        raw_components = payload.get("components", [])
        disruption_days = int(payload.get("disruption_days", 0))

        if not raw_components:
            raise HTTPException(status_code=400, detail="components list must not be empty")

        components = [BOMComponent.model_validate(c) for c in raw_components]
        assessment = MultiTierSupplyEngine().assess_bom(
            system_name, components, corridor_disruption_days=disruption_days
        )
        return assessment.model_dump(mode="json")

    @app.post(
        "/v1/supply-chain/economic-impact",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def calculate_economic_impact(payload: dict[str, Any]) -> dict[str, Any]:
        from continuityos.supply_chain import EconomicLossCalculator

        duration_days = int(payload.get("disruption_duration_days", 7))
        daily_inv = float(payload.get("daily_inventory_value_cad", 5_000_000.0))
        vessels = int(payload.get("vessels_delayed_count", 2))
        demurrage_rate = float(payload.get("demurrage_rate_per_vessel_daily_cad", 25_000.0))
        prod_loss = float(payload.get("production_line_daily_burn_cad", 150_000.0))

        estimate = EconomicLossCalculator().calculate_losses(
            disruption_duration_days=duration_days,
            daily_inventory_value_cad=daily_inv,
            vessels_delayed_count=vessels,
            demurrage_rate_per_vessel_daily_cad=demurrage_rate,
            production_line_daily_burn_cad=prod_loss,
        )
        return estimate.model_dump(mode="json")

    @app.post(
        "/v1/supply-chain/reroute",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def solve_modal_rerouting(payload: dict[str, Any]) -> dict[str, Any]:
        from continuityos.supply_chain import ModalReroutingSolver

        corridor_id = str(payload.get("corridor_id", "CORRIDOR-PRIMARY"))
        origin = str(payload.get("origin", "Vancouver"))
        destination = str(payload.get("destination", "Toronto"))
        distance_km = float(payload.get("distance_km", 4350.0))
        time_critical = bool(payload.get("time_critical", False))
        budget_constrained = bool(payload.get("budget_constrained", False))

        result = ModalReroutingSolver().solve_rerouting(
            corridor_id=corridor_id,
            origin=origin,
            destination=destination,
            distance_km=distance_km,
            time_critical=time_critical,
            budget_constrained=budget_constrained,
        )
        return result.model_dump(mode="json")

    @app.post(
        "/v1/sovereign/pbmm-audit",
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def audit_pbmm_compliance(payload: dict[str, Any] | None = None) -> dict[str, Any]:
        from continuityos.sovereign import PBMMComplianceValidator

        req = payload or {}
        region = str(req.get("region", "ca-central-1"))
        encryption_cmk = bool(req.get("encryption_at_rest_cmk", True))
        tls_ver = str(req.get("tls_version", "1.3"))
        airgap = bool(req.get("airgap_capable", True))
        immutable_chain = bool(req.get("immutable_evidence_chain", True))
        rbac_clearance = bool(req.get("rbac_clearance_filtering", True))

        report = PBMMComplianceValidator().validate_deployment(
            region=region,
            encryption_at_rest_cmk=encryption_cmk,
            tls_version=tls_ver,
            airgap_capable=airgap,
            immutable_evidence_chain=immutable_chain,
            rbac_clearance_filtering=rbac_clearance,
        )
        return report.model_dump(mode="json")

    @app.get("/v1/rfp/package-summary")
    async def get_rfp_package_summary() -> dict[str, Any]:
        return {
            "platform_name": "Aegis Continuity / ContinuityOS Sovereign Suite",
            "version": "0.1.0-sovereign-cad",
            "target_buyers": [
                "Public Services and Procurement Canada (PSPC)",
                "Department of National Defence / Canadian Armed Forces (DND/CAF)",
                "Shared Services Canada (SSC)",
                "Transport Canada (EMSA / Corridors)",
                "Public Safety Canada (Emergency Management)",
                "Natural Resources Canada (Critical Minerals Strategy)",
            ],
            "security_certification_profile": (
                "ITSG-33 Protected B / Medium Integrity / Medium Availability (PBMM)"
            ),
            "canadian_data_residency": [
                "ca-central-1 (Montreal)",
                "ca-west-1 (Calgary)",
                "canadacentral (Toronto)",
            ],
            "industrial_technological_benefits": {
                "canadian_content_value": "100% Sovereign Canadian IP and Operations",
                "domestic_cyber_workforce": True,
                "smb_defense_prime_integration": True,
            },
            "sla_and_recovery_objectives": {
                "availability_sla": "99.99%",
                "recovery_point_objective_minutes": 15,
                "recovery_time_objective_minutes": 60,
                "multi_region_failover": "Active-Active / Active-Standby",
            },
            "infrastructure_as_code_supported": [
                "Terraform (AWS Canada / Azure Canada)",
                "Hardened Kubernetes Helm",
            ],
        }

    @app.post("/v1/intel/counter-surveillance/assess")
    async def assess_counter_surveillance(payload: dict[str, Any]) -> dict[str, Any]:
        """Evaluate orbital SAR / Earth Observation reconnaissance exposure and EMCON posture."""
        corridor_id = payload.get("corridor_id", "CORRIDOR-DEFAULT")
        orbital_ephemeris = payload.get("orbital_ephemeris", [])
        corridor_length_km = float(payload.get("corridor_length_km", 100.0))

        predictor = SARSatelliteOverflightPredictor()
        report = predictor.evaluate_exposure(
            corridor_id=corridor_id,
            orbital_ephemeris=orbital_ephemeris,
            critical_corridor_length_km=corridor_length_km,
        )
        return report.model_dump()

    @app.post("/v1/intel/dark-fleet/correlate")
    async def correlate_dark_fleet(payload: dict[str, Any]) -> dict[str, Any]:
        """Correlate radar contacts against active AIS MMSIs to detect dark vessels."""
        corridor_id = payload.get("corridor_id", "MARITIME-CHOKEPOINT")
        contacts = payload.get("contacts", [])
        active_mmsis = set(payload.get("active_mmsis", []))
        asset_lat = float(payload.get("asset_latitude", 48.0))
        asset_lon = float(payload.get("asset_longitude", -65.0))

        from continuityos.domain import GeoPoint

        detector = DarkFleetDetector()
        report = detector.correlate_contacts(
            corridor_id=corridor_id,
            radar_optical_contacts=contacts,
            active_ais_mmsis=active_mmsis,
            asset_location=GeoPoint(latitude=asset_lat, longitude=asset_lon),
        )
        return report.model_dump()

    @app.post("/v1/environmental/permafrost-assess")
    async def assess_permafrost_thaw(payload: dict[str, Any]) -> dict[str, Any]:
        """Simulate permafrost active-layer thaw depth and track embankment stability."""
        corridor_id = payload.get("corridor_id", "HUDSON-BAY-RAILWAY")
        ddt = float(payload.get("degree_days_of_thaw", 450.0))
        peat_cover = float(payload.get("insulating_peat_cover_cm", 15.0))

        model = PermafrostDegradationModel()
        report = model.evaluate_corridor_thaw(
            corridor_id=corridor_id,
            degree_days_of_thaw=ddt,
            insulating_peat_cover_cm=peat_cover,
        )
        return report.model_dump()

    @app.post("/v1/environmental/wildfire-corridor-risk")
    async def assess_wildfire_corridor(payload: dict[str, Any]) -> dict[str, Any]:
        """Evaluate Canadian Fire Weather Index and wildfire proximity to transport corridors."""
        corridor_id = payload.get("corridor_id", "TRANS-CANADA-MAINLINE")
        fwi = float(payload.get("fire_weather_index_fwi", 28.5))
        closest_km = float(payload.get("closest_fire_distance_km", 12.0))
        wind_speed = float(payload.get("wind_speed_kmh", 30.0))
        wind_towards = bool(payload.get("wind_direction_towards_corridor", True))

        model = WildfireCorridorRiskModel()
        report = model.evaluate_wildfire_risk(
            corridor_id=corridor_id,
            fwi=fwi,
            closest_fire_distance_km=closest_km,
            wind_speed_kmh=wind_speed,
            wind_direction_towards_corridor=wind_towards,
        )
        return report.model_dump()

    @app.post("/v1/environmental/subsea-integrity")
    async def assess_subsea_integrity(payload: dict[str, Any]) -> dict[str, Any]:
        """Monitor subsea telecom cable and seabed energy conduit acoustic integrity."""
        infra_id = payload.get("infrastructure_id", "TRANSATLANTIC-SUBSEA-01")
        acoustic_db = float(payload.get("acoustic_anomaly_db", 14.5))
        anchor_km = float(payload.get("closest_anchoring_vessel_dist_km", 3.2))

        monitor = SubseaAcousticMonitor()
        report = monitor.evaluate_subsea_risk(
            infrastructure_id=infra_id,
            acoustic_anomaly_db=acoustic_db,
            closest_anchoring_vessel_dist_km=anchor_km,
        )
        return report.model_dump()

    ui_index = Path(__file__).resolve().parent.parent.parent / "ui" / "index.html"
    if ui_index.exists():

        @app.get("/ui", response_class=PlainTextResponse)
        async def ui_dashboard() -> Response:
            return Response(content=ui_index.read_text(encoding="utf-8"), media_type="text/html")

    return app


app = create_app()
