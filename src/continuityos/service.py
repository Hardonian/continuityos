from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from pathlib import Path
from time import perf_counter
from typing import Annotated, Any, cast
from uuid import uuid4

import orjson
from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.responses import ORJSONResponse, PlainTextResponse
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
from continuityos.telemetry import (
    TelemetryAuthenticationError,
    normalized_operator_observation,
    verify_operator_signature,
)


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
        default_response_class=ORJSONResponse,
        docs_url="/docs" if configured.environment != "production" else None,
        openapi_url="/openapi.json" if configured.environment != "production" else None,
        redoc_url=None,
    )
    app.state.settings = configured
    app.state.ledger = ledger
    app.state.metrics = Metrics()
    app.state.rate_limiter = FixedWindowLimiter()

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(_request: Request, exc: RateLimitExceeded) -> ORJSONResponse:
        return ORJSONResponse(
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
            response = ORJSONResponse(
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
        return response

    @app.get("/healthz")
    async def healthz() -> dict[str, Any]:
        ledger_errors = ledger.verify()
        return {
            "status": "ok" if not ledger_errors else "degraded",
            "environment": configured.environment,
            "evidence_ledger_valid": not ledger_errors,
            "outbound_http_enabled": configured.outbound_http_enabled,
        }

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
    async def assess(request: AssessmentRequest) -> CorridorAssessment:
        try:
            assessment = fusion.assess(
                request.corridor_id, request.observations, as_of=request.as_of
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
        return assessment

    @app.post(
        "/v1/graph/analyze",
        response_model=GraphAssessment,
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def analyze_graph(
        graph: DependencyGraph,
        failed_nodes: Annotated[list[str], Query(min_length=1)],
    ) -> GraphAssessment:
        try:
            result = dependency_engine.analyze(graph, set(failed_nodes))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        ledger.append("dependency_graph_assessment", graph.graph_id, result.model_dump(mode="json"))
        return result

    @app.post(
        "/v1/compile",
        response_model=CompiledPlan,
        dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
    )
    async def compile_plan(request: CompileRequest) -> CompiledPlan:
        try:
            plan = compiler.compile(request)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        ledger.append("compiled_plan", str(plan.plan_id), plan.model_dump(mode="json"))
        return plan

    @app.post(
        "/v1/operator-observations",
        response_model=TelemetryResponse,
        dependencies=[Depends(enforce_rate_limit)],
    )
    async def ingest_operator_observation(
        x_continuity_timestamp: Annotated[str, Header()],
        x_continuity_signature: Annotated[str, Header()],
        payload: Annotated[dict[str, Any], Body(...)],
    ) -> TelemetryResponse:
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
        ledger.append(
            "operator_observation",
            str(observation.observation_id),
            observation.model_dump(mode="json"),
        )
        return TelemetryResponse(accepted=True, observation=observation)

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
