"""ContinuityOS Command-Line Interface (CLI).

Continuity-as-Code compiler, linter, analyzer, and resilience orchestrator.
Defensive planning and resilience assurance CLI for cyber-physical supply corridors.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import yaml
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from continuityos.closure import ClosureInput, assess_closure
from continuityos.compiler import ContinuityCompiler
from continuityos.domain import CompileRequest, Observation
from continuityos.dsl import load_resource, load_resources, validate_resource
from continuityos.evidence import EvidenceLedger
from continuityos.fusion import FusionEngine
from continuityos.graph import (
    DependencyEngine,
    DependencyGraph,
    detect_cycles,
)
from continuityos.inventory import InventoryProfile, simulate_inventory
from continuityos.providers.mock import MockProvider
from continuityos.reconcile import ActualState, DesiredState, ReconciliationStatus, reconcile
from continuityos.recovery import RecoveryProfile, model_recovery
from continuityos.remediation import generate_remediation
from continuityos.scenario import Scenario, simulate_scenario
from continuityos.sources.cache import SnapshotCache


def _load(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        payload: Any
        if path.suffix.lower() in {".yaml", ".yml"}:
            payload = yaml.safe_load(handle)
        else:
            payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"expected an object at document root: {path}")
    return cast(dict[str, Any], payload)


def _output(data: Any, args: argparse.Namespace) -> None:
    output_format = getattr(args, "format", "json")
    if hasattr(data, "model_dump"):
        dumped = data.model_dump(mode="json")
    elif isinstance(data, dict | list):
        dumped = data
    else:
        print(str(data))
        return

    if output_format == "yaml":
        print(yaml.safe_dump(dumped, sort_keys=False))
    else:
        print(json.dumps(dumped, indent=2, sort_keys=False))


# --- Commands ---


def command_init(args: argparse.Namespace) -> None:
    """Scaffold a new Continuity-as-Code directory."""
    target_dir = args.directory
    target_dir.mkdir(parents=True, exist_ok=True)

    network_spec = {
        "apiVersion": "continuity.io/v1",
        "kind": "SupplyNetwork",
        "metadata": {
            "name": args.name or "supply-network",
            "namespace": "default",
            "labels": {"scaffolded": "true"},
        },
        "spec": {
            "objectives": {
                "minimum_continuity": 0.95,
                "maximum_critical_shortage_days": 7,
                "maximum_recovery_days": 30,
            },
            "redundancy": {
                "minimum_routes": 2,
                "minimum_ports": 2,
                "minimum_satcom_providers": 2,
            },
            "inventory": {
                "fuel_reserve_days": 30,
                "medical_reserve_days": 60,
            },
        },
    }
    policy_spec = {
        "apiVersion": "continuity.io/v1",
        "kind": "ContinuityPolicy",
        "metadata": {
            "name": f"{args.name or 'supply'}-policy",
        },
        "spec": {
            "rules": [
                {
                    "rule_id": "SAT-001",
                    "description": "SATCOM provider redundancy",
                    "assertion": {"minimum_providers": 2},
                },
                {
                    "rule_id": "INV-001",
                    "description": "Strategic fuel reserves",
                    "assertion": {"minimum_reserve_days": 30},
                },
            ],
        },
    }

    (target_dir / "network.yaml").write_text(
        yaml.safe_dump(network_spec, sort_keys=False), encoding="utf-8"
    )
    (target_dir / "policy.yaml").write_text(
        yaml.safe_dump(policy_spec, sort_keys=False), encoding="utf-8"
    )
    _output(
        {
            "status": "scaffolded",
            "directory": str(target_dir),
            "files": ["network.yaml", "policy.yaml"],
        },
        args,
    )


def command_validate(args: argparse.Namespace) -> None:
    """Validate declarative YAML specification against DSL rules."""
    path: Path = args.file
    try:
        resources = load_resources(path) if args.all else [load_resource(path)]
    except Exception as exc:
        print(
            json.dumps(
                {"valid": False, "errors": [{"path": str(path), "message": str(exc)}]}, indent=2
            )
        )
        sys.exit(1)

    all_errors: list[dict[str, Any]] = []
    for resource in resources:
        errors = validate_resource(resource)
        for err in errors:
            all_errors.append(err.model_dump())

    valid = len(all_errors) == 0
    _output({"valid": valid, "resources_checked": len(resources), "errors": all_errors}, args)
    if not valid:
        sys.exit(1)


def command_graph(args: argparse.Namespace) -> None:
    """Analyze dependency graph: cycles, alternative paths, SPOFs, and blast radius."""
    raw = _load(args.file)
    if "graph" in raw:
        graph = DependencyGraph.model_validate(raw["graph"])
    else:
        graph = DependencyGraph.model_validate(raw)

    engine = DependencyEngine()
    cycles = detect_cycles(graph)

    res: dict[str, Any] = {
        "graph_id": graph.graph_id,
        "nodes_count": len(graph.nodes),
        "edges_count": len(graph.edges),
        "cycles_detected": len(cycles),
        "cycles": cycles,
    }

    if args.from_node and args.to_node:
        failed_set = set(args.fail_nodes.split(",")) if args.fail_nodes else set()
        paths = engine.find_alternative_paths(
            graph, args.from_node, args.to_node, failed=failed_set
        )
        res["alternative_paths"] = paths
        res["path_count"] = len(paths)

    if args.blast_radius:
        failed = set(args.blast_radius.split(","))
        res["blast_radius"] = engine.calculate_blast_radius(graph, failed)

    _output(res, args)


def command_observe(args: argparse.Namespace) -> None:
    """Ingest or synthesize observations."""
    if args.mock:
        provider = MockProvider(scenario=args.scenario or "normal")
        observations = provider.fetch()
        _output([obs.model_dump(mode="json") for obs in observations], args)
        return

    payload = _load(args.file)
    obs_list = payload.get("observations", [payload]) if isinstance(payload, dict) else payload
    observations = [Observation.model_validate(item) for item in obs_list]
    _output(
        {
            "observations_count": len(observations),
            "sources": sorted({o.source_id for o in observations}),
            "metrics": sorted({str(o.metric) for o in observations}),
        },
        args,
    )


def command_assess(args: argparse.Namespace) -> None:
    """Run fusion assessment on corridor observations."""
    payload = _load(args.input)
    observations = [Observation.model_validate(item) for item in payload["observations"]]
    assessment = FusionEngine().assess(payload["corridor_id"], observations)
    _output(assessment, args)


def command_compile(args: argparse.Namespace) -> None:
    """Compile mitigation plan using the bounded exact solver."""
    request = CompileRequest.model_validate(_load(args.input))
    plan = ContinuityCompiler(args.max_actions).compile(request)
    _output(plan, args)


def command_reconcile(args: argparse.Namespace) -> None:
    """Reconcile declared resilience policy against observed actual state."""
    raw = _load(args.file)
    desired = DesiredState.model_validate(raw.get("desired", {}))
    actual = ActualState.model_validate(raw.get("actual", {}))
    result = reconcile(desired, actual)
    _output(result, args)
    if result.overall_status in {ReconciliationStatus.FAIL}:
        sys.exit(1)


def command_simulate(args: argparse.Namespace) -> None:
    """Simulate correlated failure scenario against dependency graph."""
    raw_scenario = _load(args.scenario)
    scenario_spec = raw_scenario.get("spec", raw_scenario)
    scenario = Scenario(
        scenario_id=raw_scenario.get("metadata", {}).get("name", "scenario-1"),
        name=scenario_spec.get("description", "Scenario"),
        events=scenario_spec.get("events", []),
        duration_days=scenario_spec.get("duration_days", 30),
    )

    raw_graph = _load(args.graph)
    graph = DependencyGraph.model_validate(raw_graph.get("graph", raw_graph))

    result = simulate_scenario(scenario, graph)
    _output(result, args)


def command_inventory(args: argparse.Namespace) -> None:
    """Simulate time-series strategic inventory depletion."""
    raw = _load(args.file)
    spec = raw.get("spec", raw)
    profile = InventoryProfile.model_validate(spec)
    result = simulate_inventory(
        profile,
        simulation_days=args.days,
        degraded=args.degraded,
        disrupted_replenishment=args.disrupted_replenishment,
    )
    _output(result, args)


def command_recovery(args: argparse.Namespace) -> None:
    """Model T0-T5 recovery lag timeline."""
    raw = _load(args.file)
    spec = raw.get("spec", raw)
    profile = RecoveryProfile.model_validate(spec)
    timeline = model_recovery(profile, days_since_incident=args.days_since)
    _output(timeline, args)


def command_remediate(args: argparse.Namespace) -> None:
    """Generate advisory remediation options from reconciliation findings."""
    raw = _load(args.file)
    desired = DesiredState.model_validate(raw.get("desired", {}))
    actual = ActualState.model_validate(raw.get("actual", {}))
    recon_result = reconcile(desired, actual)
    plan = generate_remediation(recon_result)
    _output(plan, args)


def command_explain(args: argparse.Namespace) -> None:
    """Explain why a corridor is degraded or why functional closure occurred."""
    raw = _load(args.file)
    closure_input = ClosureInput.model_validate(raw.get("spec", raw))
    assessment = assess_closure(closure_input)
    _output(assessment, args)


def command_doctor(args: argparse.Namespace) -> None:
    """Run comprehensive system diagnostics and environment health check."""
    checks: list[dict[str, Any]] = []

    # 1. Python version check
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    checks.append(
        {
            "check": "PYTHON_RUNTIME",
            "status": "PASS" if sys.version_info >= (3, 12) else "WARN",
            "details": f"Python {py_ver}",
        }
    )

    # 2. Cryptography check
    try:
        key = Ed25519PrivateKey.generate()
        key.public_key()
        checks.append(
            {"check": "CRYPTOGRAPHY_ED25519", "status": "PASS", "details": "Ed25519 functional"}
        )
    except Exception as exc:
        checks.append({"check": "CRYPTOGRAPHY_ED25519", "status": "FAIL", "details": str(exc)})

    # 3. Mock provider check (offline capability)
    try:
        mock = MockProvider()
        obs = mock.fetch()
        checks.append(
            {
                "check": "OFFLINE_MOCK_PROVIDER",
                "status": "PASS",
                "details": f"{len(obs)} synthetic observations generated",
            }
        )
    except Exception as exc:
        checks.append({"check": "OFFLINE_MOCK_PROVIDER", "status": "FAIL", "details": str(exc)})

    # 4. JSON Schema validation check
    try:
        from continuityos.schemas import get_resource_schema

        schema = get_resource_schema()
        checks.append(
            {
                "check": "JSON_SCHEMA_VALIDATOR",
                "status": "PASS" if schema else "FAIL",
                "details": f"{len(schema.get('properties', {}))} resource properties loaded",
            }
        )
    except Exception as exc:
        checks.append({"check": "JSON_SCHEMA_VALIDATOR", "status": "FAIL", "details": str(exc)})

    passed = sum(1 for c in checks if c["status"] == "PASS")
    overall = "HEALTHY" if passed == len(checks) else "DEGRADED"

    _output(
        {
            "status": overall,
            "timestamp": datetime.now(UTC).isoformat(),
            "passed": passed,
            "total": len(checks),
            "checks": checks,
        },
        args,
    )


def command_import_snapshot(args: argparse.Namespace) -> None:
    cache = SnapshotCache(args.cache_dir)
    metadata = cache.import_file(args.source_id, args.uri, args.file, args.content_type)
    _output(metadata.__dict__, args)


def command_verify_ledger(args: argparse.Namespace) -> None:
    ledger = EvidenceLedger.from_key_files(args.ledger, None, args.public_key)
    errors = ledger.verify()
    _output({"valid": not errors, "errors": errors}, args)
    if errors:
        sys.exit(1)


def command_generate_keys(args: argparse.Namespace) -> None:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    private_key = Ed25519PrivateKey.generate()
    private_path = args.output_dir / "evidence-private.pem"
    public_path = args.output_dir / "evidence-public.pem"
    private_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_path.write_bytes(
        private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    private_path.chmod(0o600)
    _output({"private_key": str(private_path), "public_key": str(public_path)}, args)


def command_sovereign_audit(args: argparse.Namespace) -> None:
    """Audit air-gapped readiness, cryptographic isolation, and zero-egress compliance."""
    from continuityos.sovereign import AirGapAuditor

    report = AirGapAuditor().audit(args.repo_dir)
    _output(report, args)
    if not report.compliant:
        sys.exit(1)


def command_readiness(args: argparse.Namespace) -> None:
    """Evaluate Defense Readiness Reporting System (DRRS) & NATO C-Level capability rating."""
    from continuityos.domain import CorridorState
    from continuityos.readiness import ReadinessEngine

    raw = _load(args.file)
    spec = raw.get("spec", raw)
    overall_continuity = float(spec.get("overall_continuity", 0.95))
    inventory_days = float(spec.get("inventory_reserve_days", 30.0))
    corridor_state_str = spec.get("corridor_state", "open")
    corridor_state = CorridorState.from_str(corridor_state_str)

    assessment = ReadinessEngine().evaluate_readiness(
        spec.get("theater_id", "theater-1"),
        overall_continuity=overall_continuity,
        inventory_reserve_days=inventory_days,
        corridor_state=corridor_state,
    )
    _output(assessment, args)


def command_export_cop(args: argparse.Namespace) -> None:
    """Export corridor operational status as Mil-Std-2525D / NATO APP-6D GeoJSON COP layer."""
    from continuityos.cop import export_cop_feature, export_cop_feature_collection
    from continuityos.domain import CorridorAssessment

    raw = _load(args.file)
    assessment = CorridorAssessment.model_validate(raw.get("assessment", raw))
    corridor_id = raw.get("corridor_id", "corridor-1")
    feature = export_cop_feature(
        corridor_id,
        assessment,
        coordinates=args.coordinates,
        security_banner=args.classification or "UNCLASSIFIED",
    )
    collection = export_cop_feature_collection([feature])
    _output(collection, args)


def command_cross_domain_filter(args: argparse.Namespace) -> None:
    """Filter and sanitize payload across classification and compartment boundaries."""
    from continuityos.domain import DataClassification
    from continuityos.sovereign import CrossDomainFilter, SecurityLabel

    payload = _load(args.file)
    source_class = DataClassification(args.source_classification or "secret")
    target_class = DataClassification(args.target_classification or "unclassified")
    source_label = SecurityLabel(
        classification=source_class,
        dissemination_controls=set(args.controls.split(",")) if args.controls else set(),
        owner_nation=args.owner_nation or "USA",
    )
    result = CrossDomainFilter().filter_payload(
        payload,
        source_label=source_label,
        target_clearance=target_class,
        target_nation=args.target_nation or "USA",
        target_compartments=set(args.compartments.split(",")) if args.compartments else set(),
    )
    _output(result, args)
    if not result.allowed:
        sys.exit(1)


def command_threat_scan(args: argparse.Namespace) -> None:
    """Run cyber-physical threat scanning (GNSS spoofing, Port SCADA, AIS kinematics)."""
    from continuityos.threat import ThreatDetectionEngine

    raw = _load(args.file)
    engine = ThreatDetectionEngine()
    scan = engine.run_full_scan(
        resource_ref=raw.get("resource_ref", "corridor-target"),
        gnss_residuals=raw.get("gnss_residuals"),
        cno_ratios=raw.get("cno_ratios"),
        clock_drift_ppm=float(raw.get("clock_drift_ppm", 0.0)),
        scada_cmd_rate=float(raw.get("scada_cmd_rate", 5.0)),
        unauthorized_fc=raw.get("unauthorized_fc"),
        untrusted_ips=int(raw.get("untrusted_ips", 0)),
        plc_hashes=raw.get("plc_hashes"),
        expected_plc_hash=raw.get("expected_plc_hash", "a1b2c3d4e5f6"),
        ais_coords=tuple(raw["ais_coords"]) if "ais_coords" in raw else None,
    )
    _output(scan, args)


def command_ai_forecast(args: argparse.Namespace) -> None:
    """Run Bayesian cascade failure probability forecasting across supply graph."""
    from continuityos.graph import DependencyGraph
    from continuityos.intelligence import BayesianCascadeForecaster

    graph_raw = _load(args.graph)
    graph = DependencyGraph.model_validate(graph_raw.get("graph", graph_raw))
    obs_raw = _load(args.degradations) if args.degradations else {}
    degradations = {str(k): float(v) for k, v in obs_raw.get("degradations", obs_raw).items()}

    forecaster = BayesianCascadeForecaster()
    target_node = args.target or graph.nodes[0].node_id
    res = forecaster.forecast(graph, target_node, degradations)
    _output(res, args)


def command_xai_explain(args: argparse.Namespace) -> None:
    """Explain corridor risk breakdown using Shapley factor attribution (XAI)."""
    from continuityos.domain import CorridorAssessment
    from continuityos.intelligence import XAIRiskExplainer

    raw = _load(args.file)
    assessment = CorridorAssessment.model_validate(raw.get("assessment", raw))
    explainer = XAIRiskExplainer()
    explanation = explainer.explain(assessment)
    _output(explanation, args)


def command_merkle_proof(args: argparse.Namespace) -> None:
    """Generate and verify zero-knowledge Merkle inclusion proof for a ledger record."""
    from continuityos.crypto import MerkleTree
    from continuityos.evidence import EvidenceLedger

    ledger = EvidenceLedger(args.ledger)
    records = ledger.records(0, 10000)
    if not records:
        print(json.dumps({"error": "Ledger is empty"}))
        sys.exit(1)

    hashes = [r.record_hash for r in records]
    tree = MerkleTree(hashes)
    idx = min(args.index, len(records) - 1)
    proof = tree.generate_inclusion_proof(idx)
    verified = proof.verify()

    result = {
        "merkle_root_hash": tree.root_hash,
        "record_index": idx,
        "leaf_hash": proof.leaf_hash,
        "inclusion_proof_valid": verified,
        "audit_path_depth": len(proof.audit_path),
    }
    _output(result, args)
    
    if proof.verify():
        print("\n✅ Zero-Knowledge Merkle Proof Verified Mathematically.")
    else:
        print("\n❌ Proof Verification Failed.")
        sys.exit(1)


def command_operator(args: argparse.Namespace) -> None:
    """Start the ContinuityOS Kubernetes Operator."""
    from continuityos.operator import ContinuityOperator
    
    if args.subcommand == "start":
        operator = ContinuityOperator(max_actions=args.max_actions)
        operator.run()
    else:
        print(f"Unknown operator subcommand: {args.subcommand}")
        sys.exit(1)


# --- Parser builder ---


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="continuity",
        description=(
            "ContinuityOS: Continuity-as-Code compiler, analyzer, and resilience orchestrator."
        ),
    )
    parser.add_argument("--format", choices=["json", "yaml"], default="json", help="Output format")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = subparsers.add_parser("init", help="Scaffold a new Continuity-as-Code directory")
    p_init.add_argument("directory", type=Path, help="Target directory")
    p_init.add_argument("--name", default="supply-network", help="Network name")
    p_init.set_defaults(func=command_init)

    # validate
    p_val = subparsers.add_parser("validate", help="Validate YAML DSL files against JSON Schema")
    p_val.add_argument("file", type=Path, help="File to validate")
    p_val.add_argument(
        "--all", action="store_true", help="Validate all documents in multi-doc YAML"
    )
    p_val.set_defaults(func=command_validate)

    # graph
    p_graph = subparsers.add_parser(
        "graph", help="Analyze dependency graph, cycles, alternative paths"
    )
    p_graph.add_argument("file", type=Path, help="Graph JSON/YAML file")
    p_graph.add_argument("--from-node", help="Source node for alternative paths")
    p_graph.add_argument("--to-node", help="Target node for alternative paths")
    p_graph.add_argument("--fail-nodes", help="Comma-separated nodes to fail")
    p_graph.add_argument("--blast-radius", help="Calculate blast radius for failed node(s)")
    p_graph.set_defaults(func=command_graph)

    # observe
    p_obs = subparsers.add_parser("observe", help="Ingest or generate observations")
    p_obs.add_argument("file", type=Path, nargs="?", help="Observation file")
    p_obs.add_argument("--mock", action="store_true", help="Generate synthetic observations")
    p_obs.add_argument("--scenario", choices=["normal", "degraded", "disrupted"], default="normal")
    p_obs.set_defaults(func=command_observe)

    # assess
    p_assess = subparsers.add_parser("assess", help="Assess corridor risk and operational state")
    p_assess.add_argument("input", type=Path, help="Assessment input JSON/YAML")
    p_assess.set_defaults(func=command_assess)

    # compile / plan
    p_comp = subparsers.add_parser("compile", help="Compile mitigation plan")
    p_comp.add_argument("input", type=Path, help="Compile request JSON/YAML")
    p_comp.add_argument("--max-actions", type=int, default=24)
    p_comp.set_defaults(func=command_compile)

    p_plan = subparsers.add_parser("plan", help="Alias for compile")
    p_plan.add_argument("input", type=Path, help="Compile request JSON/YAML")
    p_plan.add_argument("--max-actions", type=int, default=24)
    p_plan.set_defaults(func=command_compile)

    # reconcile / drift
    p_rec = subparsers.add_parser("reconcile", help="Reconcile desired vs actual resilience state")
    p_rec.add_argument("file", type=Path, help="Reconciliation spec JSON/YAML")
    p_rec.set_defaults(func=command_reconcile)

    p_drift = subparsers.add_parser("drift", help="Alias for reconcile")
    p_drift.add_argument("file", type=Path, help="Reconciliation spec JSON/YAML")
    p_drift.set_defaults(func=command_reconcile)

    # simulate
    p_sim = subparsers.add_parser("simulate", help="Simulate correlated failure scenario")
    p_sim.add_argument("--scenario", required=True, type=Path, help="Scenario YAML/JSON")
    p_sim.add_argument("--graph", required=True, type=Path, help="Dependency graph YAML/JSON")
    p_sim.set_defaults(func=command_simulate)

    # inventory
    p_inv = subparsers.add_parser("inventory", help="Simulate strategic inventory depletion")
    p_inv.add_argument("file", type=Path, help="Inventory profile JSON/YAML")
    p_inv.add_argument("--days", type=int, default=90, help="Simulation duration in days")
    p_inv.add_argument("--degraded", action="store_true", help="Use degraded consumption rate")
    p_inv.add_argument(
        "--disrupted-replenishment", action="store_true", help="Disable replenishment"
    )
    p_inv.set_defaults(func=command_inventory)

    # recovery
    p_recov = subparsers.add_parser("recovery", help="Model T0-T5 recovery lag timeline")
    p_recov.add_argument("file", type=Path, help="Recovery profile JSON/YAML")
    p_recov.add_argument("--days-since", type=int, default=0, help="Days elapsed since incident")
    p_recov.set_defaults(func=command_recovery)

    # remediate
    p_rem = subparsers.add_parser("remediate", help="Generate advisory remediation options")
    p_rem.add_argument("file", type=Path, help="Reconciliation input JSON/YAML")
    p_rem.set_defaults(func=command_remediate)

    # explain
    p_exp = subparsers.add_parser(
        "explain", help="Explain functional closure and degradation causes"
    )
    p_exp.add_argument("file", type=Path, help="Closure input JSON/YAML")
    p_exp.set_defaults(func=command_explain)

    # doctor
    p_doc = subparsers.add_parser("doctor", help="Check system health, dependencies, and keys")
    p_doc.set_defaults(func=command_doctor)

    # Ledger / cache utilities
    p_snap = subparsers.add_parser("import-snapshot", help="Import snapshot into cache")
    p_snap.add_argument("--source-id", required=True)
    p_snap.add_argument("--uri", required=True)
    p_snap.add_argument("--file", required=True, type=Path)
    p_snap.add_argument("--content-type")
    p_snap.add_argument("--cache-dir", type=Path, default=Path("./var/snapshots"))
    p_snap.set_defaults(func=command_import_snapshot)

    p_vled = subparsers.add_parser("verify-ledger", help="Verify evidence ledger integrity")
    p_vled.add_argument("ledger", type=Path)
    p_vled.add_argument("--public-key", type=Path)
    p_vled.set_defaults(func=command_verify_ledger)

    p_keys = subparsers.add_parser("generate-evidence-keys", help="Generate Ed25519 signing keys")
    p_keys.add_argument("output_dir", type=Path)
    p_keys.set_defaults(func=command_generate_keys)

    # sovereign-audit
    p_sova = subparsers.add_parser(
        "sovereign-audit", help="Audit air-gapped readiness and SCIF compliance"
    )
    p_sova.add_argument("--repo-dir", type=Path, default=Path("."), help="Repository root")
    p_sova.set_defaults(func=command_sovereign_audit)

    # readiness
    p_read = subparsers.add_parser(
        "readiness", help="Evaluate Defense Readiness (DRRS) & C-Level capability rating"
    )
    p_read.add_argument("file", type=Path, help="Theater readiness spec JSON/YAML")
    p_read.set_defaults(func=command_readiness)

    # export-cop
    p_cop = subparsers.add_parser(
        "export-cop", help="Export corridor status as Mil-Std-2525D / NATO APP-6D GeoJSON COP"
    )
    p_cop.add_argument("file", type=Path, help="Assessment file JSON/YAML")
    p_cop.add_argument("--classification", default="UNCLASSIFIED", help="Security banner marking")
    p_cop.add_argument(
        "--coordinates",
        type=json.loads,
        default=None,
        help="Optional GeoJSON coordinate list [[lon,lat],...]",
    )
    p_cop.set_defaults(func=command_export_cop)

    # cross-domain-filter
    p_xdom = subparsers.add_parser(
        "cross-domain-filter", help="Filter and sanitize payload across security enclaves"
    )
    p_xdom.add_argument("file", type=Path, help="Payload JSON/YAML")
    p_xdom.add_argument("--source-classification", default="secret")
    p_xdom.add_argument("--target-classification", default="unclassified")
    p_xdom.add_argument("--owner-nation", default="USA")
    p_xdom.add_argument("--target-nation", default="USA")
    p_xdom.add_argument("--controls", help="Comma-separated dissemination controls (e.g. NOFORN)")
    p_xdom.add_argument("--compartments", help="Comma-separated target compartments")
    p_xdom.set_defaults(func=command_cross_domain_filter)

    # threat-scan
    p_threat = subparsers.add_parser(
        "threat-scan", help="Scan telemetry for cyber-physical threats (GNSS EW, SCADA, AIS)"
    )
    p_threat.add_argument("file", type=Path, help="Threat telemetry JSON/YAML")
    p_threat.set_defaults(func=command_threat_scan)

    # ai-forecast
    p_aif = subparsers.add_parser(
        "ai-forecast", help="Bayesian cascade failure probability forecasting across supply graph"
    )
    p_aif.add_argument("--graph", required=True, type=Path, help="Dependency graph JSON/YAML")
    p_aif.add_argument("--degradations", type=Path, help="Observed node degradations JSON/YAML")
    p_aif.add_argument("--target", help="Target node ID to forecast")
    p_aif.set_defaults(func=command_ai_forecast)

    # xai-explain
    p_xai = subparsers.add_parser(
        "xai-explain", help="Explain corridor risk with Shapley factor attribution (XAI)"
    )
    p_xai.add_argument("file", type=Path, help="Corridor assessment JSON/YAML")
    p_xai.set_defaults(func=command_xai_explain)

    # merkle-proof
    p_mkl = subparsers.add_parser(
        "merkle-proof", help="Generate zero-knowledge Merkle inclusion proof for ledger record"
    )
    p_mkl.add_argument("ledger", type=Path, help="Evidence ledger file")
    p_mkl.add_argument("--index", type=int, default=0, help="Record index to prove")
    p_mkl.set_defaults(func=command_merkle_proof)
    
    # operator
    p_op = subparsers.add_parser(
        "operator", help="Manage the Kubernetes Operator"
    )
    p_op.add_argument("subcommand", choices=["start"], help="Action to perform")
    p_op.add_argument("--max-actions", type=int, default=100, help="Max compiler actions")
    p_op.set_defaults(func=command_operator)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
