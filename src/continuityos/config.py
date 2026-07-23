from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CONTINUITYOS_", env_file=".env", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    data_dir: Path = Path("./var")
    evidence_private_key_path: Path | None = None
    evidence_public_key_path: Path | None = None
    operator_webhook_secret: str | None = Field(default=None, min_length=32)
    api_key: str | None = Field(default=None, min_length=32)
    outbound_http_enabled: bool = False
    outbound_timeout_seconds: float = Field(default=20.0, gt=0, le=120)
    max_snapshot_age_hours: int = Field(default=72, ge=1, le=720)
    compiler_max_actions: int = Field(default=24, ge=1, le=64)
    max_request_bytes: int = Field(default=1_048_576, ge=16_384, le=10_485_760)
    rate_limit_per_minute: int = Field(default=60, ge=1, le=10_000)

    @model_validator(mode="after")
    def validate_production_controls(self) -> Settings:
        if self.environment == "production":
            missing: list[str] = []
            if self.evidence_private_key_path is None:
                missing.append("CONTINUITYOS_EVIDENCE_PRIVATE_KEY_PATH")
            if self.evidence_public_key_path is None:
                missing.append("CONTINUITYOS_EVIDENCE_PUBLIC_KEY_PATH")
            if self.operator_webhook_secret is None:
                missing.append("CONTINUITYOS_OPERATOR_WEBHOOK_SECRET")
            if self.api_key is None:
                missing.append("CONTINUITYOS_API_KEY")
            if missing:
                raise ValueError(f"production configuration missing: {', '.join(missing)}")
        return self

    @property
    def snapshots_dir(self) -> Path:
        return self.data_dir / "snapshots"

    @property
    def evidence_dir(self) -> Path:
        return self.data_dir / "evidence"
