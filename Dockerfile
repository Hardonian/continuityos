# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
WORKDIR /build
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-compile .

FROM python:3.12-slim AS runtime
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CONTINUITYOS_ENVIRONMENT=production \
    CONTINUITYOS_DATA_DIR=/var/lib/continuityos \
    CONTINUITYOS_OUTBOUND_HTTP_ENABLED=false
RUN groupadd --system --gid 10001 continuityos \
    && useradd --system --uid 10001 --gid 10001 --home-dir /nonexistent \
        --shell /usr/sbin/nologin continuityos \
    && mkdir -p /var/lib/continuityos /run/continuityos \
    && chown -R continuityos:continuityos /var/lib/continuityos /run/continuityos
COPY --from=builder /opt/venv /opt/venv
USER continuityos
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2)" || exit 1
ENTRYPOINT ["uvicorn", "continuityos.service:app"]
CMD ["--host", "0.0.0.0", "--port", "8080", "--workers", "1", "--proxy-headers"]
