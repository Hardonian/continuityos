# Operator onboarding and safe demonstration

ContinuityOS is a controlled evaluation/reference API. The demonstration data is fictional and must not be presented as live port, Arctic, military, insurer, carrier, cyber, or government data.

## Five-minute local demonstration

```bash
cd /home/scott/ai-workspace/repos/continuityos
uv run python scripts/demo.py > /tmp/continuityos-demo.json
python - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path('/tmp/continuityos-demo.json').read_text())
assert set(payload) == {'assessment', 'plan', 'dependency_impact'}
assert payload['plan']['approval_required'] is True
assert payload['dependency_impact']['failed_nodes'] == ['shared-idp']
print('demo_contract=PASS')
PY
```

The demo intentionally shows:

- source provenance and confidence separation;
- an assessment for a fictional northern maritime corridor;
- dependency blast radius for a shared identity provider;
- a mitigation plan that requires human approval;
- no action execution, live navigation, classified data, or operational command.

## Before a pilot

- Identify the customer-owned corridor, assets, data controller, and decision owner.
- Agree on data residency, retention, deletion, export, and incident contacts.
- Use synthetic or customer-approved observations only.
- Record source licences and snapshot hashes.
- Define what the system may recommend and what it must never execute.
- Establish a labelled-outcome calibration protocol before measuring accuracy.
- Establish an independent review path for safety, cyber, privacy, procurement, insurance, and liability claims.

## Strategic and national-security audience boundary

The system can support continuity-analysis discussion for ports, Arctic logistics, supply chains, infrastructure operators, international partners, and public-sector planners. It does not provide classified handling, targeting, command-and-control, autonomous action, accreditation, export-control clearance, or alliance endorsement. Any such use requires the relevant authority, legal review, security accreditation, data-sharing agreement, and human decision process.
