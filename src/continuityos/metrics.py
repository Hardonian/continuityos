from __future__ import annotations

from dataclasses import dataclass
from threading import Lock


@dataclass
class MetricSnapshot:
    requests_total: int = 0
    errors_total: int = 0
    request_seconds_total: float = 0.0


class Metrics:
    def __init__(self) -> None:
        self._snapshot = MetricSnapshot()
        self._lock = Lock()

    def observe(self, elapsed: float, status_code: int) -> None:
        with self._lock:
            self._snapshot.requests_total += 1
            self._snapshot.request_seconds_total += elapsed
            if status_code >= 500:
                self._snapshot.errors_total += 1

    def prometheus(self) -> str:
        with self._lock:
            snapshot = MetricSnapshot(**vars(self._snapshot))
        return "\n".join(
            [
                "# HELP continuityos_requests_total Total HTTP requests.",
                "# TYPE continuityos_requests_total counter",
                f"continuityos_requests_total {snapshot.requests_total}",
                "# HELP continuityos_errors_total Total HTTP 5xx responses.",
                "# TYPE continuityos_errors_total counter",
                f"continuityos_errors_total {snapshot.errors_total}",
                "# HELP continuityos_request_seconds_total Total request duration in seconds.",
                "# TYPE continuityos_request_seconds_total counter",
                f"continuityos_request_seconds_total {snapshot.request_seconds_total:.6f}",
                "",
            ]
        )
