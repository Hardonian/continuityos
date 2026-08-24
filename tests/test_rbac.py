"""Test suite for Multi-Tenant Sovereign RBAC, Clearances, and Caveats."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from continuityos.rbac import (
    AccessControlEvaluator,
    Permission,
    SovereignIdentity,
    SovereignRole,
)
from continuityos.service import create_app
from continuityos.sovereign import ClassificationLevel, DisseminationControl


class TestAccessControlEvaluator:
    """Test RBAC and security clearance checks."""

    def test_authorized_same_tenant_operator(self) -> None:
        evaluator = AccessControlEvaluator()
        identity = SovereignIdentity(
            user_id="USER-01",
            tenant_id="TENANT-DND-HQ",
            roles=[SovereignRole.OPERATOR_ANALYST],
            clearance_level=ClassificationLevel.SECRET,
            citizenship_nation="CAN",
        )

        decision = evaluator.evaluate_access(
            identity=identity,
            target_tenant_id="TENANT-DND-HQ",
            required_permission=Permission.COMPILE_PLAN,
            resource_classification=ClassificationLevel.SECRET,
        )
        assert decision.is_authorized is True
        assert decision.rejection_reason is None

    def test_rejected_cross_tenant_isolation(self) -> None:
        evaluator = AccessControlEvaluator()
        identity = SovereignIdentity(
            user_id="USER-01",
            tenant_id="TENANT-DND-HQ",
            roles=[SovereignRole.OPERATOR_ANALYST],
            clearance_level=ClassificationLevel.SECRET,
            citizenship_nation="CAN",
        )

        decision = evaluator.evaluate_access(
            identity=identity,
            target_tenant_id="TENANT-COAST-GUARD",
            required_permission=Permission.COMPILE_PLAN,
            resource_classification=ClassificationLevel.SECRET,
        )
        assert decision.is_authorized is False
        assert "Cross-tenant isolation violation" in str(decision.rejection_reason)

    def test_sovereign_commander_cross_tenant_access(self) -> None:
        evaluator = AccessControlEvaluator()
        identity = SovereignIdentity(
            user_id="ADMIRAL-01",
            tenant_id="TENANT-DND-HQ",
            roles=[SovereignRole.SOVEREIGN_COMMANDER],
            clearance_level=ClassificationLevel.TOP_SECRET,
            citizenship_nation="CAN",
        )

        decision = evaluator.evaluate_access(
            identity=identity,
            target_tenant_id="TENANT-COAST-GUARD",
            required_permission=Permission.MUTATE_NETWORK,
            resource_classification=ClassificationLevel.SECRET,
        )
        assert decision.is_authorized is True

    def test_rejected_insufficient_clearance(self) -> None:
        evaluator = AccessControlEvaluator()
        identity = SovereignIdentity(
            user_id="USER-LOW-CLEAR",
            tenant_id="TENANT-DND-HQ",
            roles=[SovereignRole.OPERATOR_ANALYST],
            clearance_level=ClassificationLevel.PROTECTED_B,
            citizenship_nation="CAN",
        )

        decision = evaluator.evaluate_access(
            identity=identity,
            target_tenant_id="TENANT-DND-HQ",
            required_permission=Permission.COMPILE_PLAN,
            resource_classification=ClassificationLevel.SECRET,
        )
        assert decision.is_authorized is False
        assert "Insufficient security clearance" in str(decision.rejection_reason)

    def test_rejected_nationality_dissemination_restriction(self) -> None:
        evaluator = AccessControlEvaluator()
        identity = SovereignIdentity(
            user_id="ALLIED-LIAISON",
            tenant_id="TENANT-DND-HQ",
            roles=[SovereignRole.OPERATOR_ANALYST],
            clearance_level=ClassificationLevel.SECRET,
            citizenship_nation="USA",
        )

        decision = evaluator.evaluate_access(
            identity=identity,
            target_tenant_id="TENANT-DND-HQ",
            required_permission=Permission.COMPILE_PLAN,
            resource_classification=ClassificationLevel.SECRET,
            required_dissemination=DisseminationControl.CANADIAN_EYES_ONLY,
        )
        assert decision.is_authorized is False
        assert "Nationality restriction" in str(decision.rejection_reason)


class TestRBACAPI:
    """Test RBAC REST endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        app = create_app()
        return TestClient(app)

    def test_rbac_evaluate_endpoint(self, client: TestClient) -> None:
        payload = {
            "user_id": "TEST-OP",
            "tenant_id": "DND-HQ",
            "roles": ["operator_analyst"],
            "clearance_level": "SECRET",
            "citizenship_nation": "CAN",
            "target_tenant_id": "DND-HQ",
            "required_permission": "compile_plan",
        }
        resp = client.post("/v1/rbac/evaluate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_authorized"] is True
