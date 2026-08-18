"""Tests for Functional Closure engine (multi-layer decomposition)."""

from __future__ import annotations

from continuityos.closure import (
    ClosureInput,
    LayerState,
    assess_closure,
)
from continuityos.domain import CorridorState


class TestFunctionalClosure:
    def test_all_layers_healthy(self) -> None:
        inp = ClosureInput(
            resource_ref="corridor/nsr",
            physically_accessible=True,
            physical_capacity_ratio=1.0,
            navigation_available=True,
            navigation_trust=0.95,
            communications_available=True,
            communications_trust=0.95,
            insurance_available=True,
            insurance_coverage=0.9,
            carrier_capacity_available=True,
            carrier_capacity_ratio=0.9,
            data_integrity=0.95,
        )
        assessment = assess_closure(inp)
        assert assessment.effective_state == CorridorState.OPEN
        assert assessment.physical_state.state == LayerState.AVAILABLE
        assert assessment.operational_state.state == LayerState.AVAILABLE
        assert assessment.commercial_state.state == LayerState.AVAILABLE
        assert assessment.trust_state.state == LayerState.AVAILABLE

    def test_physically_closed(self) -> None:
        inp = ClosureInput(
            resource_ref="corridor/nsr",
            physically_accessible=False,
        )
        assessment = assess_closure(inp)
        assert assessment.effective_state == CorridorState.PHYSICALLY_CLOSED
        assert assessment.physical_state.state == LayerState.UNAVAILABLE
        assert "physically_inaccessible" in assessment.reason_codes

    def test_open_but_uninsurable(self) -> None:
        inp = ClosureInput(
            resource_ref="corridor/nsr",
            physically_accessible=True,
            insurance_available=False,
            insurance_coverage=0.0,
        )
        assessment = assess_closure(inp)
        assert assessment.effective_state == CorridorState.OPEN_BUT_UNINSURABLE
        assert "uninsurable" in assessment.reason_codes

    def test_open_but_no_carrier_capacity(self) -> None:
        inp = ClosureInput(
            resource_ref="corridor/nsr",
            physically_accessible=True,
            carrier_capacity_available=False,
            carrier_capacity_ratio=0.0,
        )
        assessment = assess_closure(inp)
        assert assessment.effective_state == CorridorState.OPEN_BUT_NO_CARRIER_CAPACITY
        assert "no_carrier_capacity" in assessment.reason_codes

    def test_open_but_navigation_untrusted(self) -> None:
        inp = ClosureInput(
            resource_ref="corridor/nsr",
            physically_accessible=True,
            navigation_available=True,
            navigation_trust=0.3,
        )
        assessment = assess_closure(inp)
        assert assessment.effective_state == CorridorState.OPEN_BUT_NAVIGATION_UNTRUSTED
        assert "navigation_untrusted" in assessment.reason_codes

    def test_open_but_communications_degraded(self) -> None:
        inp = ClosureInput(
            resource_ref="corridor/nsr",
            physically_accessible=True,
            communications_available=True,
            communications_trust=0.4,
        )
        assessment = assess_closure(inp)
        assert assessment.effective_state == CorridorState.OPEN_BUT_COMMUNICATIONS_DEGRADED
        assert "communications_degraded" in assessment.reason_codes

    def test_functionally_closed_when_operational_unavailable(self) -> None:
        inp = ClosureInput(
            resource_ref="corridor/nsr",
            physically_accessible=True,
            navigation_available=False,
            communications_available=False,
        )
        assessment = assess_closure(inp)
        assert assessment.effective_state == CorridorState.FUNCTIONALLY_CLOSED
