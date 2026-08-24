"""Multi-Tenant Sovereign Role-Based Access Control (RBAC) & Clearance Engine.

Provides:
  1. SovereignRole: Granular roles from SOVEREIGN_COMMANDER down to NATO_LIAISON_VIEWER.
  2. Permission: Detailed authorizations (plan compilation, wargaming, ledger reads).
  3. SovereignIdentity: Identity model carrying clearance, nationality, and tenant enclave ID.
  4. AccessControlEvaluator: Deterministic engine enforcing labels, caveats & tenancy.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from continuityos.sovereign import ClassificationLevel, DisseminationControl


class SovereignRole(StrEnum):
    SOVEREIGN_COMMANDER = "sovereign_commander"
    TENANT_ADMIN = "tenant_admin"
    OPERATOR_ANALYST = "operator_analyst"
    SECURITY_AUDITOR = "security_auditor"
    SCIF_AIRGAP_OPERATOR = "scif_airgap_operator"
    NATO_LIAISON_VIEWER = "nato_liaison_viewer"


class Permission(StrEnum):
    READ_PUBLIC = "read_public"
    READ_PROTECTED = "read_protected"
    READ_SECRET = "read_secret"
    READ_TOP_SECRET = "read_top_secret"
    INGEST_TELEMETRY = "ingest_telemetry"
    COMPILE_PLAN = "compile_plan"
    TRIGGER_WARGAME = "trigger_wargame"
    MUTATE_NETWORK = "mutate_network"
    VERIFY_LEDGER = "verify_ledger"
    EXPORT_COP = "export_cop"
    MANAGE_CLUSTER = "manage_cluster"
    ADMIN_TENANTS = "admin_tenants"


ROLE_PERMISSIONS: dict[SovereignRole, set[Permission]] = {
    SovereignRole.SOVEREIGN_COMMANDER: {
        Permission.READ_PUBLIC,
        Permission.READ_PROTECTED,
        Permission.READ_SECRET,
        Permission.READ_TOP_SECRET,
        Permission.INGEST_TELEMETRY,
        Permission.COMPILE_PLAN,
        Permission.TRIGGER_WARGAME,
        Permission.MUTATE_NETWORK,
        Permission.VERIFY_LEDGER,
        Permission.EXPORT_COP,
        Permission.MANAGE_CLUSTER,
        Permission.ADMIN_TENANTS,
    },
    SovereignRole.TENANT_ADMIN: {
        Permission.READ_PUBLIC,
        Permission.READ_PROTECTED,
        Permission.READ_SECRET,
        Permission.INGEST_TELEMETRY,
        Permission.COMPILE_PLAN,
        Permission.TRIGGER_WARGAME,
        Permission.MUTATE_NETWORK,
        Permission.VERIFY_LEDGER,
        Permission.EXPORT_COP,
        Permission.MANAGE_CLUSTER,
    },
    SovereignRole.OPERATOR_ANALYST: {
        Permission.READ_PUBLIC,
        Permission.READ_PROTECTED,
        Permission.READ_SECRET,
        Permission.INGEST_TELEMETRY,
        Permission.COMPILE_PLAN,
        Permission.TRIGGER_WARGAME,
        Permission.EXPORT_COP,
    },
    SovereignRole.SECURITY_AUDITOR: {
        Permission.READ_PUBLIC,
        Permission.READ_PROTECTED,
        Permission.READ_SECRET,
        Permission.VERIFY_LEDGER,
    },
    SovereignRole.SCIF_AIRGAP_OPERATOR: {
        Permission.READ_PUBLIC,
        Permission.READ_PROTECTED,
        Permission.READ_SECRET,
        Permission.INGEST_TELEMETRY,
        Permission.COMPILE_PLAN,
        Permission.MANAGE_CLUSTER,
        Permission.VERIFY_LEDGER,
    },
    SovereignRole.NATO_LIAISON_VIEWER: {
        Permission.READ_PUBLIC,
        Permission.READ_PROTECTED,
        Permission.EXPORT_COP,
    },
}


class SovereignIdentity(BaseModel):
    """Authenticated user/service identity carrying sovereign credentials."""

    user_id: str
    tenant_id: str
    roles: list[SovereignRole]
    clearance_level: ClassificationLevel
    citizenship_nation: str = "CAN"
    authorized_caveats: list[DisseminationControl] = Field(default_factory=list)


class AuthorizationDecision(BaseModel):
    """Result of an RBAC and clearance validation check."""

    decision_id: UUID = Field(default_factory=uuid4)
    user_id: str
    tenant_id: str
    is_authorized: bool
    requested_permission: Permission
    resource_classification: ClassificationLevel
    rejection_reason: str | None = None


class AccessControlEvaluator:
    """Evaluates multi-tenant isolation, role authorizations, and classification guards."""

    def evaluate_access(
        self,
        *,
        identity: SovereignIdentity,
        target_tenant_id: str,
        required_permission: Permission,
        resource_classification: ClassificationLevel = ClassificationLevel.PROTECTED_B,
        required_dissemination: DisseminationControl | None = None,
    ) -> AuthorizationDecision:
        # 1. Multi-Tenant Boundary Enforcement
        if (
            identity.tenant_id != target_tenant_id
            and SovereignRole.SOVEREIGN_COMMANDER not in identity.roles
        ):
            return AuthorizationDecision(
                user_id=identity.user_id,
                tenant_id=identity.tenant_id,
                is_authorized=False,
                requested_permission=required_permission,
                resource_classification=resource_classification,
                rejection_reason=(
                    f"Cross-tenant isolation violation: User tenant '{identity.tenant_id}' "
                    f"cannot access target tenant '{target_tenant_id}'"
                ),
            )

        # 2. RBAC Role Permissions Check
        user_perms: set[Permission] = set()
        for role in identity.roles:
            user_perms.update(ROLE_PERMISSIONS.get(role, set()))

        if required_permission not in user_perms:
            return AuthorizationDecision(
                user_id=identity.user_id,
                tenant_id=identity.tenant_id,
                is_authorized=False,
                requested_permission=required_permission,
                resource_classification=resource_classification,
                rejection_reason=f"Role lacks permission '{required_permission.value}'",
            )

        # 3. Security Clearance Level Check
        user_rank = self._classification_rank(identity.clearance_level)
        resource_rank = self._classification_rank(resource_classification)

        if user_rank < resource_rank:
            return AuthorizationDecision(
                user_id=identity.user_id,
                tenant_id=identity.tenant_id,
                is_authorized=False,
                requested_permission=required_permission,
                resource_classification=resource_classification,
                rejection_reason=(
                    f"Insufficient security clearance: User has '{identity.clearance_level.value}' "
                    f"but resource requires '{resource_classification.value}'"
                ),
            )

        # 4. Dissemination Cavity & National Nationality Guard
        if (
            required_dissemination == DisseminationControl.CANADIAN_EYES_ONLY
            and identity.citizenship_nation != "CAN"
        ):
            return AuthorizationDecision(
                user_id=identity.user_id,
                tenant_id=identity.tenant_id,
                is_authorized=False,
                requested_permission=required_permission,
                resource_classification=resource_classification,
                rejection_reason=(
                    f"Nationality restriction: Resource is CANADIAN_EYES_ONLY "
                    f"but user is '{identity.citizenship_nation}'"
                ),
            )

        return AuthorizationDecision(
            user_id=identity.user_id,
            tenant_id=identity.tenant_id,
            is_authorized=True,
            requested_permission=required_permission,
            resource_classification=resource_classification,
            rejection_reason=None,
        )

    @staticmethod
    def _classification_rank(level: ClassificationLevel) -> int:
        ranks = {
            ClassificationLevel.UNCLASSIFIED: 0,
            ClassificationLevel.PROTECTED_A: 1,
            ClassificationLevel.PROTECTED_B: 2,
            ClassificationLevel.PROTECTED_C: 3,
            ClassificationLevel.SECRET: 4,
            ClassificationLevel.TOP_SECRET: 5,
            ClassificationLevel.COSMIC_TOP_SECRET: 6,
        }
        return ranks.get(level, 0)
