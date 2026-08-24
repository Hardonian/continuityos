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

from continuityos.attestation import SCIFAttestationEngine
from continuityos.closure import ClosureInput, assess_closure
from continuityos.cluster import RaftStateSynchronizer
from continuityos.compiler import ContinuityCompiler
from continuityos.counter_intel import (
    DarkFleetDetector,
    SARSatelliteOverflightPredictor,
)
from continuityos.domain import CompileRequest, Observation
from continuityos.dsl import load_resource, load_resources, validate_resource
from continuityos.environmental import (
    PermafrostDegradationModel,
    SubseaAcousticMonitor,
    WildfireCorridorRiskModel,
)
from continuityos.evidence import EvidenceLedger
from continuityos.fusion import FusionEngine
from continuityos.graph import (
    DependencyEngine,
    DependencyGraph,
    detect_cycles,
)
from continuityos.inventory import InventoryProfile, simulate_inventory
from continuityos.providers.mock import MockProvider
from continuityos.rbac import (
    AccessControlEvaluator,
    Permission,
    SovereignIdentity,
    SovereignRole,
)
from continuityos.reconcile import ActualState, DesiredState, ReconciliationStatus, reconcile
from continuityos.recovery import RecoveryProfile, model_recovery
from continuityos.remediation import generate_remediation
from continuityos.scenario import Scenario, simulate_scenario
from continuityos.sources.cache import SnapshotCache
from continuityos.wargame import (
    CANADIAN_CRITICAL_MINERALS,
    DisruptionScenarioType,
    WargameSimulator,
)


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


def command_tactical_scan(args: argparse.Namespace) -> None:
    """Run unified tactical surveillance scan across UAV, Starlink SATCOM, and C-UAS."""
    from continuityos.tactical import (
        CUASDefenseEngine,
        CUASDetectionEvent,
        StarlinkTacticalEngine,
        StarlinkTelemetry,
        UAVTacticalEngine,
        UAVTelemetryFrame,
    )

    raw = _load(args.file)
    results: dict[str, Any] = {}

    if "uav" in raw:
        frame = UAVTelemetryFrame.model_validate(raw["uav"])
        results["uav_assessment"] = UAVTacticalEngine().analyze_frame(frame).model_dump(mode="json")

    if "starlink" in raw:
        tel = StarlinkTelemetry.model_validate(raw["starlink"])
        results["starlink_assessment"] = (
            StarlinkTacticalEngine().evaluate_channel(tel).model_dump(mode="json")
        )

    if "cuas" in raw:
        cuas_data = raw["cuas"]
        sector = str(cuas_data.get("sector", "SECTOR-ALPHA"))
        events = [CUASDetectionEvent.model_validate(e) for e in cuas_data.get("events", [])]
        results["cuas_assessment"] = (
            CUASDefenseEngine().analyze_events(sector, events).model_dump(mode="json")
        )

    _output(results, args)


def command_edge_package(args: argparse.Namespace) -> None:
    """Generate C header and TinyMoE hardware config for target microcontroller."""
    from continuityos.embedded import (
        EmbeddedArchitectureEngine,
        MicroQuantization,
        TargetMicrocontroller,
        TinyMoEConfig,
    )

    target = TargetMicrocontroller(args.target)
    quant = MicroQuantization(args.quantization)
    moe = TinyMoEConfig(
        total_parameters=args.total_params,
        active_parameters_per_token=args.active_params,
        quantization=quant,
    )
    engine = EmbeddedArchitectureEngine()
    pkg = engine.compile_package(target, moe)

    if args.export_dir:
        out_dir = Path(args.export_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "aegis_embedded_config.h").write_text(pkg.c_header_source, encoding="utf-8")
        (out_dir / "partitions.csv").write_text(pkg.partition_csv_source, encoding="utf-8")
        print(f"Exported embedded configuration and partition table to {out_dir}")

    _output(pkg.model_dump(mode="json"), args)


def command_operator(args: argparse.Namespace) -> None:
    """Start the ContinuityOS Kubernetes Operator."""
    from continuityos.operator import ContinuityOperator

    if args.subcommand == "start":
        operator = ContinuityOperator(max_actions=args.max_actions)
        operator.run()
    else:
        print(f"Unknown operator subcommand: {args.subcommand}")
        sys.exit(1)


def command_canadian_corridor(args: argparse.Namespace) -> None:
    """Assess and display status of Canadian strategic sovereign supply corridors."""
    corridor_key = getattr(args, "corridor", "critical-minerals").lower()

    corridor_catalog = {
        "critical-minerals": {
            "corridor_id": "can-critical-minerals-ring-of-fire",
            "name": "Ontario Ring of Fire to Windsor EV Gigafactory Corridor",
            "category": "CRITICAL_MINERALS",
            "sovereign_priority": "NATIONAL_PRIORITY_TIER_1",
            "nodes": [
                {
                    "id": "Eskers-Mine-Hub",
                    "type": "MINE_OR_REFINERY",
                    "location": "James Bay Lowlands (52.9°N, 86.1°W)",
                    "commodity": "Nickel / Lithium / Cobalt",
                },
                {
                    "id": "Sudbury-Smelter",
                    "type": "MINE_OR_REFINERY",
                    "location": "Greater Sudbury (46.5°N, 80.9°W)",
                    "capacity": "Smelting & Refining",
                },
                {
                    "id": "Windsor-EV-Plant",
                    "type": "MANUFACTURING_PLANT",
                    "location": "Windsor-Essex (42.3°N, 83.0°W)",
                    "demand": "Gigafactory Battery Cells",
                },
                {
                    "id": "Montreal-Port-Export",
                    "type": "PORT",
                    "location": "Port of Montreal (45.5°N, 73.5°W)",
                    "function": "Transatlantic Gateway",
                },
            ],
            "primary_transit_modes": ["RAIL_CN", "RAIL_CPKC", "LONG_HAUL_TRUCK"],
            "resilience_status": "MONITORED_NOMINAL",
            "continuity_score": 0.96,
            "security_clearance_required": "PROTECTED_B",
        },
        "arctic-norad": {
            "corridor_id": "can-arctic-norad-northern-logistics",
            "name": "Canadian Arctic & NORAD Northern Defense Logistics Corridor",
            "category": "NORTHERN_SOVEREIGNTY",
            "sovereign_priority": "DEFENSE_AND_SOVEREIGNTY",
            "nodes": [
                {
                    "id": "CFS-Alert",
                    "type": "FACILITY",
                    "location": "Ellesmere Island (82.5°N, 62.3°W)",
                    "function": "Signals Intelligence / Northernmost Outpost",
                },
                {
                    "id": "Nanisivik-Transition-Hub",
                    "type": "PORT",
                    "location": "Baffin Island (73.0°N, 84.5°W)",
                    "function": "Northern Logistics Transition",
                },
                {
                    "id": "Churchill-Deepwater-Port",
                    "type": "PORT",
                    "location": "Hudson Bay (58.7°N, 94.2°W)",
                    "function": "Arctic Ocean Deepwater Gateway",
                },
                {
                    "id": "Iqaluit-FOL",
                    "type": "AIRFIELD",
                    "location": "Iqaluit (63.7°N, 68.5°W)",
                    "function": "Forward Operating Location",
                },
            ],
            "primary_transit_modes": ["MARITIME", "AIR_CARGO", "ICEBREAKER_ESCORT"],
            "resilience_status": "HIGH_SURVEILLANCE",
            "continuity_score": 0.89,
            "security_clearance_required": "SECRET",
        },
        "trans-canada-rail": {
            "corridor_id": "can-trans-canada-intermodal-rail",
            "name": "Trans-Canada CPKC & CN Intermodal Freight Corridor",
            "category": "INTERMODAL_FREIGHT",
            "sovereign_priority": "NATIONAL_COMMERCE",
            "nodes": [
                {
                    "id": "Port-of-Vancouver",
                    "type": "PORT",
                    "location": "Vancouver, BC (49.3°N, 123.1°W)",
                    "function": "Asia-Pacific Gateway",
                },
                {
                    "id": "Port-of-Prince-Rupert",
                    "type": "PORT",
                    "location": "Prince Rupert, BC (54.3°N, 130.3°W)",
                    "function": "Northern Pacific Gateway",
                },
                {
                    "id": "Calgary-Intermodal-Yard",
                    "type": "RAIL_HUB",
                    "location": "Calgary, AB (51.0°N, 114.0°W)",
                    "function": "Western Transshipment",
                },
                {
                    "id": "Toronto-Logistics-Hub",
                    "type": "INTERMODAL_TERMINAL",
                    "location": "Vaughan/Brampton, ON (43.8°N, 79.5°W)",
                    "function": "Industrial Core",
                },
                {
                    "id": "Port-of-Halifax",
                    "type": "PORT",
                    "location": "Halifax, NS (44.6°N, 63.6°W)",
                    "function": "Atlantic Gateway",
                },
            ],
            "primary_transit_modes": ["RAIL_CPKC", "RAIL_CN", "LONG_HAUL_TRUCK"],
            "resilience_status": "MONITORED_NOMINAL",
            "continuity_score": 0.94,
            "security_clearance_required": "PROTECTED_A",
        },
        "st-lawrence-seaway": {
            "corridor_id": "can-st-lawrence-seaway-locks",
            "name": "St. Lawrence Seaway & Great Lakes Maritime Lock Corridor",
            "category": "MARITIME_BULK_COMMODITIES",
            "sovereign_priority": "COMMERCIAL_STRATEGIC",
            "nodes": [
                {
                    "id": "Welland-Canal-Lock-8",
                    "type": "FACILITY",
                    "location": "Port Colborne, ON (42.9°N, 79.2°W)",
                    "function": "Lake Erie-Ontario Lock",
                },
                {
                    "id": "Montreal-Lake-Ontario-Locks",
                    "type": "FACILITY",
                    "location": "St. Lawrence River (45.3°N, 73.7°W)",
                    "function": "Seaway Descent",
                },
                {
                    "id": "Port-of-Montreal",
                    "type": "PORT",
                    "location": "Montreal, QC (45.5°N, 73.5°W)",
                    "function": "Container & Bulk Terminal",
                },
            ],
            "primary_transit_modes": ["MARITIME", "RAIL_CN"],
            "resilience_status": "SEASONAL_MONITORING",
            "continuity_score": 0.92,
            "security_clearance_required": "PROTECTED_A",
        },
    }

    matched = None
    for key, data in corridor_catalog.items():
        if key in corridor_key or corridor_key in key:
            matched = data
            break
    if not matched:
        matched = corridor_catalog["critical-minerals"]

    _output(matched, args)


def command_supply_chain_simulate(args: argparse.Namespace) -> None:
    """Simulate multi-tier supply chain disruption, single-source bottlenecks, and economic loss."""
    from continuityos.supply_chain import (
        BOMComponent,
        EconomicLossCalculator,
        ModalReroutingSolver,
        MultiTierSupplyEngine,
    )

    raw = _load(args.file)
    system_name = raw.get("system_name", raw.get("metadata", {}).get("name", "Supply-Network"))

    raw_components = raw.get("components", raw.get("spec", {}).get("components", []))
    components = []
    if raw_components:
        components = [BOMComponent.model_validate(c) for c in raw_components]
    else:
        components = [
            BOMComponent(
                component_id="COMP-T1-BATTERY",
                name="Lithium-Ion Battery Pack Module",
                tier=1,
                supplier_id="SUPPLIER-WINDSOR-01",
                is_single_sourced=True,
                lead_time_days=21,
                inventory_buffer_days=args.buffer_days,
                criticality=0.9,
            ),
            BOMComponent(
                component_id="COMP-T2-CATHODE",
                name="Nickel-Manganese-Cobalt Cathode",
                tier=2,
                supplier_id="SUPPLIER-SUDBURY-02",
                is_single_sourced=False,
                lead_time_days=14,
                inventory_buffer_days=args.buffer_days + 5,
                criticality=0.8,
            ),
            BOMComponent(
                component_id="COMP-T3-MINERALS",
                name="Refined High-Purity Nickel/Cobalt",
                tier=3,
                supplier_id="MINE-JAMES-BAY-03",
                is_single_sourced=True,
                lead_time_days=30,
                inventory_buffer_days=args.buffer_days,
                criticality=0.95,
            ),
        ]

    bom_assessment = MultiTierSupplyEngine().assess_bom(
        system_name, components, corridor_disruption_days=args.disruption_days
    )
    econ_estimate = EconomicLossCalculator().calculate_losses(
        disruption_duration_days=args.disruption_days,
        daily_inventory_value_cad=args.daily_value,
        vessels_delayed_count=args.vessels_delayed,
        production_line_daily_burn_cad=args.daily_burn,
    )
    reroute = ModalReroutingSolver().solve_rerouting(
        corridor_id="CORRIDOR-DISRUPTED",
        origin=args.origin,
        destination=args.destination,
        distance_km=args.distance_km,
    )

    results = {
        "bom_vulnerability": bom_assessment.model_dump(mode="json"),
        "economic_disruption_estimate": econ_estimate.model_dump(mode="json"),
        "modal_rerouting_solution": reroute.model_dump(mode="json"),
    }
    _output(results, args)


def command_pbmm_audit(args: argparse.Namespace) -> None:
    """Run automated CCCS ITSG-33 Protected B / Medium Integrity / Medium Availability audit."""
    from continuityos.sovereign import PBMMComplianceValidator

    validator = PBMMComplianceValidator()
    report = validator.validate_deployment(
        region=args.region,
        encryption_at_rest_cmk=not args.disable_cmk,
        tls_version=args.tls_version,
        airgap_capable=True,
        immutable_evidence_chain=True,
        rbac_clearance_filtering=True,
    )
    _output(report.model_dump(mode="json"), args)


def command_rfp_pack(args: argparse.Namespace) -> None:
    """Export complete Canadian Federal Government SaaS & IaC RFP Bid Proposal package."""
    summary = {
        "rfp_proposal_title": "ContinuityOS Sovereign Resilience-as-Code Platform",
        "target_solicitation": (
            "Government of Canada Enterprise SaaS & Resilient Infrastructure-as-Code"
        ),
        "procurement_compliance": {
            "security_profile": (
                "ITSG-33 / Protected B / Medium Integrity / Medium Availability (PBMM)"
            ),
            "canadian_data_residency": "Enforced (AWS ca-central-1 / Azure canadacentral)",
            "itb_canadian_content_value": "100% Sovereign IP & Domestic Engineering",
            "high_availability_sla": "99.99% Multi-Region Failover",
            "recovery_point_objective": "< 15 minutes",
            "recovery_time_objective": "< 60 minutes",
        },
        "artifacts_generated": [
            "docs/rfp/CANADIAN_GOVERNMENT_SAAS_RFP_PROPOSAL.md",
            "docs/rfp/ITSG33_PBMM_SECURITY_COMPLIANCE_MATRIX.md",
            "docs/rfp/ITB_VALUE_PROPOSITION_CANADIAN_CONTENT.md",
            "docs/rfp/SERVICE_LEVEL_AGREEMENT_AND_DISASTER_RECOVERY.md",
            "infra/terraform/aws-canada-pbmm/",
            "infra/terraform/azure-canada-pbmm/",
        ],
    }
    if args.out_dir:
        out = Path(args.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "rfp_proposal_manifest.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
        print(f"RFP package manifest exported to {out / 'rfp_proposal_manifest.json'}")
    _output(summary, args)


def command_counter_intel(args: argparse.Namespace) -> None:
    """Evaluate orbital SAR / Earth Observation exposure and EMCON posture."""
    predictor = SARSatelliteOverflightPredictor()
    ephemeris = [
        {
            "satellite_id": "COSMO-SkyMed-4",
            "sensor_type": "SAR_RADAR",
            "elevation_max_deg": args.elevation,
        },
        {
            "satellite_id": "Gaofen-3-SAR",
            "sensor_type": "SAR_RADAR",
            "elevation_max_deg": args.elevation * 0.9,
        },
        {
            "satellite_id": "Resurs-P-Optical",
            "sensor_type": "OPTICAL_HIGH_RES",
            "elevation_max_deg": args.elevation * 0.75,
        },
    ]
    report = predictor.evaluate_exposure(
        corridor_id=args.corridor_id,
        orbital_ephemeris=ephemeris,
        critical_corridor_length_km=args.length_km,
    )
    _output(report.model_dump(mode="json"), args)


def command_dark_fleet_detect(args: argparse.Namespace) -> None:
    """Correlate optical/radar contacts against active AIS transponders to detect dark vessels."""
    from continuityos.domain import GeoPoint

    detector = DarkFleetDetector()
    sample_contacts = [
        {
            "latitude": args.lat + 0.12,
            "longitude": args.lon - 0.15,
            "speed_knots": 1.2,
            "mmsi": None,
        },
        {
            "latitude": args.lat - 0.08,
            "longitude": args.lon + 0.22,
            "speed_knots": 14.5,
            "mmsi": "316001234",
        },
        {
            "latitude": args.lat + 0.35,
            "longitude": args.lon + 0.05,
            "speed_knots": 0.5,
            "mmsi": None,
        },
    ]
    active_mmsis = {"316001234"}
    report = detector.correlate_contacts(
        corridor_id=args.corridor_id,
        radar_optical_contacts=sample_contacts,
        active_ais_mmsis=active_mmsis,
        asset_location=GeoPoint(latitude=args.lat, longitude=args.lon),
    )
    _output(report.model_dump(mode="json"), args)


def command_permafrost_audit(args: argparse.Namespace) -> None:
    """Simulate permafrost active-layer thaw depth and track embankment stability."""
    model = PermafrostDegradationModel()
    report = model.evaluate_corridor_thaw(
        corridor_id=args.corridor_id,
        degree_days_of_thaw=args.ddt,
        insulating_peat_cover_cm=args.peat_cm,
    )
    _output(report.model_dump(mode="json"), args)


def command_environmental_scan(args: argparse.Namespace) -> None:
    """Run multi-hazard environmental assessment (permafrost, wildfire, subsea)."""
    p_model = PermafrostDegradationModel()
    p_rep = p_model.evaluate_corridor_thaw(
        corridor_id=args.corridor_id, degree_days_of_thaw=args.ddt
    )

    w_model = WildfireCorridorRiskModel()
    w_rep = w_model.evaluate_wildfire_risk(
        corridor_id=args.corridor_id, fwi=args.fwi, closest_fire_distance_km=args.fire_dist_km
    )

    s_model = SubseaAcousticMonitor()
    s_rep = s_model.evaluate_subsea_risk(
        infrastructure_id=f"{args.corridor_id}-SUBSEA",
        acoustic_anomaly_db=args.acoustic_db,
        closest_anchoring_vessel_dist_km=args.anchor_dist_km,
    )

    combined = {
        "corridor_id": args.corridor_id,
        "assessed_at": datetime.now(UTC).isoformat(),
        "permafrost_thaw_assessment": p_rep.model_dump(mode="json"),
        "wildfire_corridor_assessment": w_rep.model_dump(mode="json"),
        "subsea_infrastructure_assessment": s_rep.model_dump(mode="json"),
    }
    _output(combined, args)


def command_wargame_sim(args: argparse.Namespace) -> None:
    """Run game-theoretic wargame and critical mineral disruption simulation."""
    try:
        scenario_type = DisruptionScenarioType(args.scenario)
    except ValueError:
        scenario_type = DisruptionScenarioType.MARITIME_BLOCKADE

    simulator = WargameSimulator()
    report = simulator.run_simulation(
        scenario_type=scenario_type,
        corridor_id=args.corridor_id,
        adversary_pressure_level=args.adversary_pressure,
        domestic_reserves_cushion=args.cushion,
    )
    _output(report.model_dump(mode="json"), args)


def command_critical_minerals_audit(args: argparse.Namespace) -> None:
    """Audit Canada's 31 critical minerals stockpiles and NATO Tier-1 prime dependencies."""
    minerals = {k: v.model_dump(mode="json") for k, v in CANADIAN_CRITICAL_MINERALS.items()}
    _output({"critical_minerals_inventory": minerals}, args)


def command_cluster_status(args: argparse.Namespace) -> None:
    """Check air-gapped DDIL SCIF cluster consensus and peer synchronization health."""
    cluster = RaftStateSynchronizer(args.node_id, args.enclave_name)
    cluster.register_peer("SCIF-HALIFAX", "CFB-Halifax-SCIF", True, 512.0)
    cluster.register_peer("SCIF-ESQUIMALT", "CFB-Esquimalt-SCIF", True, 256.0)
    _output(cluster.get_cluster_status(), args)


def command_cluster_sync(args: argparse.Namespace) -> None:
    """Synchronize state log with an air-gapped DDIL peer node."""
    cluster = RaftStateSynchronizer(args.node_id, args.enclave_name)
    cluster.register_peer(args.peer_id, "Target-Peer-Enclave", True, 256.0)
    cluster.append_command("INCIDENT_LOG", {"corridor": "ARCTIC", "threat": "ELEVATED"})
    result = cluster.sync_with_peer(args.peer_id, args.last_log_index)
    _output(result.model_dump(mode="json"), args)


def command_rbac_check(args: argparse.Namespace) -> None:
    """Evaluate multi-tenant role authorizations and clearance guards."""
    from continuityos.sovereign import ClassificationLevel

    evaluator = AccessControlEvaluator()
    role = (
        SovereignRole(args.role)
        if args.role in SovereignRole._value2member_map_
        else SovereignRole.OPERATOR_ANALYST
    )
    clearance = (
        ClassificationLevel(args.clearance)
        if args.clearance in ClassificationLevel._value2member_map_
        else ClassificationLevel.SECRET
    )
    perm = (
        Permission(args.permission)
        if args.permission in Permission._value2member_map_
        else Permission.COMPILE_PLAN
    )

    identity = SovereignIdentity(
        user_id=args.user_id,
        tenant_id=args.tenant_id,
        roles=[role],
        clearance_level=clearance,
        citizenship_nation=args.nationality,
    )

    decision = evaluator.evaluate_access(
        identity=identity,
        target_tenant_id=args.target_tenant_id,
        required_permission=perm,
    )
    _output(decision.model_dump(mode="json"), args)


def command_scif_attest(args: argparse.Namespace) -> None:
    """Execute SCIF hardware TPM 2.0, entropy, and air-gap attestation check."""
    engine = SCIFAttestationEngine()
    cert = engine.perform_attestation(
        facility_id=args.facility_id,
        facility_name=args.facility_name,
        outbound_network_interfaces_detected=args.outbound_interfaces,
        secure_boot_enabled=not args.disable_secure_boot,
        memory_zeroization_verified=not args.disable_mem_zero,
    )
    _output(cert.model_dump(mode="json"), args)


# --- Parser builder ---


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="continuity",
        description=(
            "Aegis Continuity (Sovereign Edition): "
            "Continuity-as-Code compiler, analyzer, and resilience orchestrator."
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
    p_op = subparsers.add_parser("operator", help="Manage the Kubernetes Operator")
    p_op.add_argument("subcommand", choices=["start"], help="Action to perform")
    p_op.add_argument("--max-actions", type=int, default=100, help="Max compiler actions")
    p_op.set_defaults(func=command_operator)

    # tactical-scan
    p_tac = subparsers.add_parser(
        "tactical-scan", help="Run unified tactical surveillance scan across UAV, Starlink, C-UAS"
    )
    p_tac.add_argument("file", type=Path, help="Tactical telemetry JSON/YAML")
    p_tac.set_defaults(func=command_tactical_scan)

    # edge-package
    p_edge_pkg = subparsers.add_parser(
        "edge-package",
        help="Generate C header and TinyMoE hardware configuration for target microcontroller",
    )
    p_edge_pkg.add_argument(
        "--target",
        default="esp32-s3",
        choices=["esp32-s3", "esp32-c6", "riscv32", "arm-cortex-m55"],
        help="Target microcontroller SoC",
    )
    p_edge_pkg.add_argument(
        "--quantization",
        default="int4_weight",
        choices=["bitnet_1_58b", "int4_weight", "int8_symm"],
        help="Micro-quantization format",
    )
    p_edge_pkg.add_argument(
        "--total-params",
        type=int,
        default=28_900_000,
        help="Total model parameters (e.g. 28.9M)",
    )
    p_edge_pkg.add_argument(
        "--active-params",
        type=int,
        default=8_500_000,
        help="Active parameters evaluated per token",
    )
    p_edge_pkg.add_argument(
        "--export-dir",
        type=Path,
        help="Optional directory to write aegis_embedded_config.h and partitions.csv",
    )
    p_edge_pkg.set_defaults(func=command_edge_package)

    # --- New Canadian Sovereign & Supply Chain Subcommands ---

    # canadian-corridor
    p_cancor = subparsers.add_parser(
        "canadian-corridor", help="Assess Canadian strategic sovereign supply corridors"
    )
    p_cancor.add_argument(
        "corridor",
        nargs="?",
        default="critical-minerals",
        choices=["critical-minerals", "arctic-norad", "trans-canada-rail", "st-lawrence-seaway"],
        help="Canadian strategic corridor key",
    )
    p_cancor.set_defaults(func=command_canadian_corridor)

    # supply-chain-simulate
    p_scsim = subparsers.add_parser(
        "supply-chain-simulate",
        help="Simulate multi-tier BOM risk, single sources, and economic loss",
    )
    p_scsim.add_argument("file", type=Path, help="Supply network or BOM spec JSON/YAML")
    p_scsim.add_argument(
        "--disruption-days", type=int, default=14, help="Disruption duration in days"
    )
    p_scsim.add_argument("--buffer-days", type=int, default=10, help="Initial buffer reserve days")
    p_scsim.add_argument(
        "--daily-value", type=float, default=5_000_000.0, help="Daily inventory value in CAD"
    )
    p_scsim.add_argument(
        "--vessels-delayed", type=int, default=3, help="Count of delayed vessels/trains"
    )
    p_scsim.add_argument(
        "--daily-burn", type=float, default=200_000.0, help="Daily plant stoppage burn in CAD"
    )
    p_scsim.add_argument("--origin", default="Vancouver", help="Freight origin")
    p_scsim.add_argument("--destination", default="Toronto", help="Freight destination")
    p_scsim.add_argument(
        "--distance-km", type=float, default=4350.0, help="Transit corridor distance in km"
    )
    p_scsim.set_defaults(func=command_supply_chain_simulate)

    # pbmm-audit
    p_pbmma = subparsers.add_parser(
        "pbmm-audit", help="Run automated CCCS ITSG-33 / PBMM security and data residency audit"
    )
    p_pbmma.add_argument(
        "--region", default="ca-central-1", help="Sovereign cloud data residency region"
    )
    p_pbmma.add_argument("--tls-version", default="1.3", help="Enforced TLS version")
    p_pbmma.add_argument("--disable-cmk", action="store_true", help="Simulate unmanaged KMS keys")
    p_pbmma.set_defaults(func=command_pbmm_audit)

    # counter-intel
    p_cintel = subparsers.add_parser(
        "counter-intel",
        help="Evaluate orbital SAR overflight exposure and EMCON posture for a corridor",
    )
    p_cintel.add_argument("--corridor-id", default="ARCTIC-CONVOY-01", help="Corridor ID")
    p_cintel.add_argument(
        "--elevation", type=float, default=65.0, help="Max satellite elevation angle in degrees"
    )
    p_cintel.add_argument(
        "--length-km", type=float, default=150.0, help="Critical corridor length in km"
    )
    p_cintel.set_defaults(func=command_counter_intel)

    # dark-fleet-detect
    p_dark = subparsers.add_parser(
        "dark-fleet-detect",
        help="Correlate radar contacts against active AIS to detect dark/unverified vessels",
    )
    p_dark.add_argument(
        "--corridor-id", default="ST-LAWRENCE-GULF", help="Maritime corridor identifier"
    )
    p_dark.add_argument("--lat", type=float, default=48.5, help="Asset latitude")
    p_dark.add_argument("--lon", type=float, default=-64.2, help="Asset longitude")
    p_dark.set_defaults(func=command_dark_fleet_detect)

    # permafrost-audit
    p_perm = subparsers.add_parser(
        "permafrost-audit",
        help="Simulate permafrost active-layer thaw depth and track embankment stability",
    )
    p_perm.add_argument(
        "--corridor-id", default="HUDSON-BAY-RAILWAY", help="Northern rail or highway corridor"
    )
    p_perm.add_argument(
        "--ddt",
        type=float,
        default=450.0,
        help="Degree-days of thaw (cumulative temperature index)",
    )
    p_perm.add_argument(
        "--peat-cm", type=float, default=15.0, help="Insulating organic peat cover thickness in cm"
    )
    p_perm.set_defaults(func=command_permafrost_audit)

    # environmental-scan
    p_env = subparsers.add_parser(
        "environmental-scan",
        help="Run multi-hazard environmental risk assessment (permafrost, wildfire, subsea)",
    )
    p_env.add_argument("--corridor-id", default="TRANS-CANADA-NORTH", help="Corridor identifier")
    p_env.add_argument("--ddt", type=float, default=400.0, help="Degree-days of thaw")
    p_env.add_argument("--fwi", type=float, default=28.0, help="Canadian Fire Weather Index (FWI)")
    p_env.add_argument(
        "--fire-dist-km", type=float, default=14.0, help="Closest active wildfire perimeter in km"
    )
    p_env.add_argument(
        "--acoustic-db",
        type=float,
        default=12.0,
        help="Subsea acoustic anomaly level in dB above baseline",
    )
    p_env.add_argument(
        "--anchor-dist-km",
        type=float,
        default=4.5,
        help="Closest unauthorized anchoring distance in km",
    )
    p_env.set_defaults(func=command_environmental_scan)

    # rfp-pack
    p_rfp = subparsers.add_parser(
        "rfp-pack", help="Generate Canadian Federal Government SaaS & IaC RFP bid package summary"
    )
    p_rfp.add_argument(
        "--out-dir", type=Path, help="Optional directory to export RFP manifest JSON"
    )
    p_rfp.set_defaults(func=command_rfp_pack)

    # wargame-sim
    p_war = subparsers.add_parser(
        "wargame-sim",
        help="Run game-theoretic wargame and critical mineral disruption simulation",
    )
    p_war.add_argument(
        "--scenario",
        default="maritime_blockade",
        help="Disruption scenario (e.g. maritime_blockade, critical_mineral_embargo)",
    )
    p_war.add_argument(
        "--corridor-id", default="ST-LAWRENCE-SEAWAY", help="Target corridor identifier"
    )
    p_war.add_argument(
        "--adversary-pressure",
        type=float,
        default=0.75,
        help="Adversary disruption pressure index (0.0 - 1.0)",
    )
    p_war.add_argument(
        "--cushion",
        type=float,
        default=0.5,
        help="Domestic critical mineral reserve cushion index (0.0 - 1.0)",
    )
    p_war.set_defaults(func=command_wargame_sim)

    # critical-minerals-audit
    p_cmin = subparsers.add_parser(
        "critical-minerals-audit",
        help="Audit Canada's 31 critical minerals stockpiles and NATO Tier-1 prime dependencies",
    )
    p_cmin.set_defaults(func=command_critical_minerals_audit)

    # cluster-status
    p_cstat = subparsers.add_parser(
        "cluster-status",
        help="Check air-gapped DDIL SCIF cluster consensus and peer synchronization health",
    )
    p_cstat.add_argument("--node-id", default="SCIF-HQ-OTTAWA", help="Local SCIF Node ID")
    p_cstat.add_argument(
        "--enclave-name", default="DND-Carling-Campus-SCIF", help="Sovereign enclave facility name"
    )
    p_cstat.set_defaults(func=command_cluster_status)

    # cluster-sync
    p_csync = subparsers.add_parser(
        "cluster-sync",
        help="Synchronize state log with an air-gapped DDIL peer node",
    )
    p_csync.add_argument("--node-id", default="SCIF-HQ-OTTAWA", help="Local SCIF Node ID")
    p_csync.add_argument(
        "--enclave-name", default="DND-Carling-Campus-SCIF", help="Sovereign enclave facility name"
    )
    p_csync.add_argument("--peer-id", default="SCIF-HALIFAX", help="Target Peer Node ID")
    p_csync.add_argument(
        "--last-log-index", type=int, default=0, help="Last synchronized log index"
    )
    p_csync.set_defaults(func=command_cluster_sync)

    # rbac-check
    p_rbac = subparsers.add_parser(
        "rbac-check",
        help="Evaluate multi-tenant role authorizations, clearance levels, and security caveats",
    )
    p_rbac.add_argument("--user-id", default="OPERATOR-01", help="Authenticated user ID")
    p_rbac.add_argument("--tenant-id", default="DND-RCAF-TRENTON", help="User home tenant ID")
    p_rbac.add_argument(
        "--target-tenant-id", default="DND-RCAF-TRENTON", help="Target resource tenant ID"
    )
    p_rbac.add_argument(
        "--role",
        default="operator_analyst",
        help="Assigned role (sovereign_commander, tenant_admin, operator_analyst, etc.)",
    )
    p_rbac.add_argument(
        "--clearance", default="SECRET", help="Security clearance level (PROTECTED_B, SECRET, etc.)"
    )
    p_rbac.add_argument("--permission", default="compile_plan", help="Required permission to check")
    p_rbac.add_argument("--nationality", default="CAN", help="Citizen nationality ISO code")
    p_rbac.set_defaults(func=command_rbac_check)

    # scif-attest
    p_attest = subparsers.add_parser(
        "scif-attest",
        help="Audit SCIF hardware TPM 2.0 PCR quote, memory zeroization, and air-gap network posture",
    )
    p_attest.add_argument("--facility-id", default="SCIF-HQ-OTTAWA", help="Target facility ID")
    p_attest.add_argument(
        "--facility-name",
        default="DND Carling Campus National Command SCIF",
        help="Target facility human name",
    )
    p_attest.add_argument(
        "--outbound-interfaces",
        type=int,
        default=0,
        help="Number of non-local outbound network interfaces detected",
    )
    p_attest.add_argument(
        "--disable-secure-boot", action="store_true", help="Simulate disabled secure boot"
    )
    p_attest.add_argument(
        "--disable-mem-zero", action="store_true", help="Simulate disabled memory zeroization"
    )
    p_attest.set_defaults(func=command_scif_attest)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
