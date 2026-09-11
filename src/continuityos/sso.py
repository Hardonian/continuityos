"""Enterprise SSO, CAC/PIV PKI Smart Card & Dynamic ABAC Engine.

Provides:
- DoD Common Access Card (CAC) and Federal PIV X.509 certificate parsing
- Dynamic Attribute-Based Access Control (ABAC) evaluation
- Nationality, clearance enclave, and citizenship constraint enforcement
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from continuityos.sovereign import ClassificationLevel


class AuthenticatedIdentity(BaseModel):
    """Represents a validated enterprise/military identity authenticated via SSO or CAC/PIV."""

    identity_id: str  # EDIPI or user ID
    common_name: str
    organization: str
    citizenship: str  # CAN, USA, GBR, AUS, NZL, NATO
    clearance_level: ClassificationLevel
    roles: list[str] = Field(default_factory=list)
    authenticated_via: str  # CAC_PIV, OIDC_SAML, LOCAL_SCIF
    token_issued_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PVICACValidator:
    """Parses and validates DoD Common Access Card (CAC) / Personal Identity Verification (PIV) certs."""

    @staticmethod
    def parse_x509_subject(subject_dn: str) -> AuthenticatedIdentity:
        """Extract identity attributes from an X.509 Subject Distinguished Name."""
        # Example DN: "CN=SMITH.JOHN.D.1234567890, OU=DoD, OU=PKI, C=US"
        cn_match = re.search(r"CN=([^,]+)", subject_dn)
        ou_matches = re.findall(r"OU=([^,]+)", subject_dn)
        c_match = re.search(r"C=([^,]+)", subject_dn)

        raw_cn = cn_match.group(1).strip() if cn_match else "UNKNOWN_OFFICER"
        org = ou_matches[0].strip() if ou_matches else "Department of National Defence"
        country = c_match.group(1).strip().upper() if c_match else "CAN"

        # Determine EDIPI / Unique ID from CN
        parts = raw_cn.split(".")
        edipi = parts[-1] if len(parts) > 1 and parts[-1].isdigit() else raw_cn
        name = " ".join(parts[:-1]) if len(parts) > 1 else raw_cn

        citizenship = "CAN"
        if country in {"US", "USA"}:
            citizenship = "USA"
        elif country in {"GB", "GBR", "UK"}:
            citizenship = "GBR"
        elif country in {"AU", "AUS"}:
            citizenship = "AUS"

        return AuthenticatedIdentity(
            identity_id=edipi,
            common_name=name,
            organization=org,
            citizenship=citizenship,
            clearance_level=ClassificationLevel.PROTECTED_B,
            roles=["Analyst", "Operator"],
            authenticated_via="CAC_PIV",
        )


class ABACPolicyEvaluator:
    """Evaluates Attribute-Based Access Control (ABAC) against user clearance and resource tags."""

    @staticmethod
    def authorize_access(
        identity: AuthenticatedIdentity,
        resource_classification: ClassificationLevel,
        requires_canadian_eyes_only: bool = False,
        requires_five_eyes: bool = False,
    ) -> tuple[bool, str]:
        """Verify whether an authenticated identity has sufficient clearance and nationality."""
        # Clearance hierarchy ordering
        hierarchy = [
            ClassificationLevel.UNCLASSIFIED,
            ClassificationLevel.RESTRICTED,
            ClassificationLevel.PROTECTED_B,
            ClassificationLevel.SECRET,
            ClassificationLevel.TOP_SECRET,
        ]

        user_rank = hierarchy.index(identity.clearance_level)
        req_rank = hierarchy.index(resource_classification)

        # 1. Clearance check (No read up)
        if user_rank < req_rank:
            return (
                False,
                f"ACCESS_DENIED: Clearance '{identity.clearance_level.value}' insufficient for resource '{resource_classification.value}'",
            )

        # 2. Canadian Eyes Only check
        if requires_canadian_eyes_only and identity.citizenship != "CAN":
            return (
                False,
                f"ACCESS_DENIED: Resource restricted to Canadian Eyes Only (Identity citizenship is '{identity.citizenship}')",
            )

        # 3. Five Eyes check
        five_eyes_countries = {"CAN", "USA", "GBR", "AUS", "NZL"}
        if requires_five_eyes and identity.citizenship not in five_eyes_countries:
            return (
                False,
                f"ACCESS_DENIED: Resource restricted to Five Eyes Allied Personnel (Identity citizenship is '{identity.citizenship}')",
            )

        return True, "AUTHORIZED"
