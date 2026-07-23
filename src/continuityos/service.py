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
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel

from continuityos.compiler import ContinuityCompiler
from continuityos.config import Settings
from continuityos.domain import CompiledPlan, CompileRequest, CorridorAssessment, Observation
from continuityos.evidence import EvidenceLedger, EvidenceRecord
from continuityos.fusion import FusionEngine
from continuityos.graph import DependencyEngine, DependencyGraph, GraphAssessment
from continuityos.metrics import Metrics
from continuityos.security import (
    FixedWindowLimiter,
    RateLimitExceeded,
    enforce_rate_limit,
    require_api_key,
)
from continuityos.sources.policy import SourcePolicyError, validate_observation_source
from continuityos.sources.registry import SOURCES
from continuityos.state import IdempotencyConflict, PersistentState
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
        response.headers["Cache-Control"] = "no-store"
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
            }
            for item in sorted(SOURCES.values(), key=lambda source: source.source_id)
        ]

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
        if configured.operator_webhook_secret is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="telemetry disabled",
            )
        body = orjson.dumps(payload, option=orjson.OPT_SORT_KEYS)
        try:
            verify_operator_signature(
                body=body,
                timestamp=x_continuity_timestamp,
                signature=x_continuity_signature,
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
