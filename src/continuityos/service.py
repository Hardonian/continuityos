from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

import orjson
from fastapi import Body, FastAPI, Header, HTTPException, Query, status
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel

from continuityos.compiler import ContinuityCompiler
from continuityos.config import Settings
from continuityos.domain import CompiledPlan, CompileRequest, CorridorAssessment, Observation
from continuityos.evidence import EvidenceLedger, EvidenceRecord
from continuityos.fusion import FusionEngine
from continuityos.graph import DependencyEngine, DependencyGraph, GraphAssessment
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
        redoc_url=None,
    )
    app.state.settings = configured
    app.state.ledger = ledger

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

    @app.post("/v1/assess", response_model=CorridorAssessment)
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

    @app.post("/v1/graph/analyze", response_model=GraphAssessment)
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

    @app.post("/v1/compile", response_model=CompiledPlan)
    async def compile_plan(request: CompileRequest) -> CompiledPlan:
        try:
            plan = compiler.compile(request)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        ledger.append("compiled_plan", str(plan.plan_id), plan.model_dump(mode="json"))
        return plan

    @app.post("/v1/operator-observations", response_model=TelemetryResponse)
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

    @app.get("/v1/evidence/verify")
    async def verify_evidence() -> dict[str, Any]:
        errors = ledger.verify()
        return {"valid": not errors, "errors": errors}

    @app.get("/v1/evidence", response_model=list[EvidenceRecord])
    async def read_evidence() -> list[EvidenceRecord]:
        path: Path = ledger.path
        if not path.exists():
            return []
        return [EvidenceRecord.model_validate_json(line) for line in path.read_text().splitlines()]

    return app


app = create_app()
