from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx


@dataclass(frozen=True, slots=True)
class SnapshotMetadata:
    snapshot_id: str
    source_id: str
    url: str
    retrieved_at: str
    content_sha256: str
    content_type: str | None
    etag: str | None
    last_modified: str | None
    status_code: int


class SnapshotCache:
    """Content-addressed immutable snapshot cache with atomic writes."""

    def __init__(self, root: Path, timeout_seconds: float = 20.0) -> None:
        self.root = root
        self.timeout_seconds = timeout_seconds
        self.root.mkdir(parents=True, exist_ok=True)

    def store(
        self,
        source_id: str,
        url: str,
        body: bytes,
        headers: dict[str, str],
        status: int,
    ) -> SnapshotMetadata:
        digest = hashlib.sha256(body).hexdigest()
        snapshot_id = f"{source_id}-{digest[:20]}"
        directory = self.root / source_id / digest[:2] / digest
        directory.mkdir(parents=True, exist_ok=True)
        payload_path = directory / "payload.bin"
        metadata_path = directory / "metadata.json"
        metadata = SnapshotMetadata(
            snapshot_id=snapshot_id,
            source_id=source_id,
            url=url,
            retrieved_at=datetime.now(UTC).isoformat(),
            content_sha256=digest,
            content_type=headers.get("content-type"),
            etag=headers.get("etag"),
            last_modified=headers.get("last-modified"),
            status_code=status,
        )
        self._atomic_write(payload_path, body)
        self._atomic_write(metadata_path, json.dumps(asdict(metadata), sort_keys=True).encode())
        return metadata

    async def fetch(
        self, source_id: str, url: str, *, outbound_enabled: bool
    ) -> tuple[SnapshotMetadata, bytes]:
        if not outbound_enabled:
            raise RuntimeError("outbound HTTP disabled; use an imported or existing snapshot")
        async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "ContinuityOS-Reference/0.1"})
            response.raise_for_status()
        metadata = self.store(
            source_id, url, response.content, dict(response.headers), response.status_code
        )
        return metadata, response.content

    def import_file(
        self,
        source_id: str,
        url: str,
        path: Path,
        content_type: str | None = None,
    ) -> SnapshotMetadata:
        body = path.read_bytes()
        headers = {"content-type": content_type} if content_type else {}
        return self.store(source_id, url, body, headers, 200)

    def latest(
        self,
        source_id: str,
        *,
        url: str | None = None,
        max_age_hours: float | None = None,
    ) -> tuple[SnapshotMetadata, bytes] | None:
        source_root = self.root / source_id
        if not source_root.exists():
            return None
        candidates: list[SnapshotMetadata] = []
        for metadata_path in source_root.glob("*/*/metadata.json"):
            try:
                raw: dict[str, Any] = json.loads(metadata_path.read_text())
                metadata = SnapshotMetadata(**raw)
                retrieved_at = datetime.fromisoformat(metadata.retrieved_at)
            except (OSError, ValueError, TypeError):
                continue
            if url is not None and metadata.url != url:
                continue
            if max_age_hours is not None:
                age_hours = (datetime.now(UTC) - retrieved_at).total_seconds() / 3600.0
                if age_hours > max_age_hours:
                    continue
            candidates.append(metadata)
        if not candidates:
            return None
        newest = max(candidates, key=lambda item: item.retrieved_at)
        _raw, body = self.read(newest.source_id, newest.content_sha256)
        return newest, body

    def read(self, source_id: str, sha256: str) -> tuple[dict[str, Any], bytes]:
        directory = self.root / source_id / sha256[:2] / sha256
        metadata = json.loads((directory / "metadata.json").read_text())
        body = (directory / "payload.bin").read_bytes()
        if hashlib.sha256(body).hexdigest() != sha256:
            raise ValueError("snapshot hash mismatch")
        return metadata, body

    @staticmethod
    def _atomic_write(path: Path, content: bytes) -> None:
        if path.exists():
            if path.read_bytes() != content:
                raise ValueError(f"immutable snapshot collision: {path}")
            return
        fd, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, path)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)
