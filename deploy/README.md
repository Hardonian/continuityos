# Local production deployment

This reference deployment runs on the EPYC host behind the existing Caddy/Cloudflare ingress.

- Local bind: `127.0.0.1:8082`
- Public path: `https://aiautomatedsystems.ca/continuityos/`
- Service: `continuityos.service` (systemd user service)
- Data: `/home/scott/.local/share/continuityos`
- Secrets: `/home/scott/.config/continuityos.env` and `/home/scott/.local/share/continuityos/secrets/`
- Outbound HTTP: disabled

The public route is an evaluation/reference surface. It is not a multi-tenant production control plane. Do not place customer or classified data in it.

## Install/update

```bash
python3.12 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install .
mkdir -p ~/.config/systemd/user
install -m 0644 deploy/continuityos.service ~/.config/systemd/user/continuityos.service
systemctl --user daemon-reload
systemctl --user enable --now continuityos.service
```

Generate keys once with the installed CLI and create the environment file outside Git:

```bash
mkdir -p ~/.local/share/continuityos/secrets
.venv/bin/continuityos generate-evidence-keys ~/.local/share/continuityos/secrets
umask 077
python3 - <<'PY'
from pathlib import Path
import secrets
p = Path.home()/'.config/continuityos.env'
p.write_text('\n'.join([
    'CONTINUITYOS_ENVIRONMENT=production',
    'CONTINUITYOS_DATA_DIR=/home/scott/.local/share/continuityos',
    'CONTINUITYOS_EVIDENCE_PRIVATE_KEY_PATH=/home/scott/.local/share/continuityos/secrets/evidence-private.pem',
    'CONTINUITYOS_EVIDENCE_PUBLIC_KEY_PATH=/home/scott/.local/share/continuityos/secrets/evidence-public.pem',
    f'CONTINUITYOS_OPERATOR_WEBHOOK_SECRET={secrets.token_urlsafe(32)}',
    'CONTINUITYOS_OUTBOUND_HTTP_ENABLED=false',
    'CONTINUITYOS_MAX_SNAPSHOT_AGE_HOURS=72',
    'CONTINUITYOS_COMPILER_MAX_ACTIONS=24',
])+'\n')
p.chmod(0o600)
PY
```

## Verify/rollback

```bash
systemctl --user status continuityos.service --no-pager
curl -fsS http://127.0.0.1:8082/healthz
curl -fsS https://aiautomatedsystems.ca/continuityos/healthz
```

Rollback is a service stop/disable plus removal of the Caddy route. Keep the previous Caddyfile backup and use the repo commit history to reinstall an earlier application version.
