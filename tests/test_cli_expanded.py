"""Comprehensive tests for expanded ContinuityOS CLI commands."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from continuityos.cli import (
    build_parser,
    command_doctor,
    command_explain,
    command_generate_keys,
    command_graph,
    command_init,
    command_inventory,
    command_observe,
    command_recovery,
    command_remediate,
    command_simulate,
    command_validate,
)


class TestCLIExpanded:
    def test_parser_subcommands_registered(self) -> None:
        parser = build_parser()
        commands = [
            "init",
            "validate",
            "graph",
            "observe",
            "assess",
            "compile",
            "plan",
            "reconcile",
            "drift",
            "simulate",
            "inventory",
            "recovery",
            "remediate",
            "explain",
            "doctor",
            "import-snapshot",
            "verify-ledger",
            "generate-evidence-keys",
        ]
        subparsers_actions = [
            a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
        ]
        assert len(subparsers_actions) > 0
        choices = subparsers_actions[0].choices
        for cmd in commands:
            assert cmd in choices

    def test_init_command(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        parser = build_parser()
        args = parser.parse_args(["init", str(tmp_path / "scaffold"), "--name", "test-network"])
        command_init(args)
        out = capsys.readouterr().out
        assert "scaffolded" in out
        assert (tmp_path / "scaffold" / "network.yaml").exists()
        assert (tmp_path / "scaffold" / "policy.yaml").exists()

    def test_validate_command_valid(self, capsys: pytest.CaptureFixture[str]) -> None:
        parser = build_parser()
        args = parser.parse_args(["validate", "examples/arctic/network.yaml"])
        command_validate(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["valid"] is True

    def test_graph_command(self, capsys: pytest.CaptureFixture[str]) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "graph",
                "examples/arctic/graph.yaml",
                "--from-node",
                "port_kirkenes",
                "--to-node",
                "facility_yamal_lng",
                "--blast-radius",
                "satcom_iridium",
            ]
        )
        command_graph(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["nodes_count"] >= 5
        assert data["cycles_detected"] == 0
        assert "blast_radius" in data

    def test_observe_mock_command(self, capsys: pytest.CaptureFixture[str]) -> None:
        parser = build_parser()
        args = parser.parse_args(["observe", "--mock", "--scenario", "degraded"])
        command_observe(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert isinstance(data, list)
        assert len(data) >= 8

    def test_doctor_command(self, capsys: pytest.CaptureFixture[str]) -> None:
        parser = build_parser()
        args = parser.parse_args(["doctor"])
        command_doctor(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["status"] in {"HEALTHY", "DEGRADED"}
        assert data["passed"] >= 3

    def test_generate_keys_command(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        parser = build_parser()
        args = parser.parse_args(["generate-evidence-keys", str(tmp_path / "keys")])
        command_generate_keys(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "private_key" in data
        assert (tmp_path / "keys" / "evidence-private.pem").exists()
        assert (tmp_path / "keys" / "evidence-public.pem").exists()

    def test_simulate_command(self, capsys: pytest.CaptureFixture[str]) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "simulate",
                "--scenario",
                "examples/arctic/scenarios/scenario_c_port_icebreaker.yaml",
                "--graph",
                "examples/arctic/graph.yaml",
            ]
        )
        command_simulate(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["events_applied"] == 2
        assert "port_murmansk" in data["failed_nodes"]
        assert "icebreaker_50let" in data["failed_nodes"]

    def test_inventory_command(self, capsys: pytest.CaptureFixture[str]) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "inventory",
                "examples/arctic/scenarios/scenario_f_fuel_depletion.yaml",
                "--days",
                "30",
            ]
        )
        command_inventory(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["starting_quantity"] == 50000.0
        assert len(data["daily_log"]) == 30

    def test_recovery_command(self, capsys: pytest.CaptureFixture[str]) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "recovery",
                "examples/arctic/scenarios/scenario_g_recovery_lag.yaml",
                "--days-since",
                "15",
            ]
        )
        command_recovery(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["total_recovery_days"] > 20
        assert len(data["milestones"]) == 6

    def test_remediate_command(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        recon_input = {
            "desired": {"satcom_provider_count": 2, "fuel_reserve_days": 45.0},
            "actual": {"satcom_provider_count": 1, "fuel_reserve_days": 20.0},
        }
        file_path = tmp_path / "recon.json"
        file_path.write_text(json.dumps(recon_input))

        parser = build_parser()
        args = parser.parse_args(["remediate", str(file_path)])
        command_remediate(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert len(data["options"]) >= 2
        assert data["total_estimated_improvement"] > 0.0

    def test_explain_command(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        closure_input = {
            "resource_ref": "corridor/nsr",
            "physically_accessible": True,
            "insurance_available": False,
            "insurance_coverage": 0.0,
        }
        file_path = tmp_path / "closure.json"
        file_path.write_text(json.dumps(closure_input))

        parser = build_parser()
        args = parser.parse_args(["explain", str(file_path)])
        command_explain(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["effective_state"] == "open_but_uninsurable"
        assert "uninsurable" in data["reason_codes"]
