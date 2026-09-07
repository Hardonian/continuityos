import pytest

from continuityos.demo import run_demo


class TestResilienceDemonstration:
    """Tests verifying repeatable demonstration runs for Arctic and Civilian scenarios."""

    def test_run_arctic_demonstration_offline(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Run Arctic 12-step demonstration end-to-end completely offline."""
        exit_code = run_demo("arctic", no_color=True)
        assert exit_code == 0

        captured = capsys.readouterr()
        out = captured.out
        assert "CONTINUITYOS v1.0 — RESILIENCE-AS-CODE LIVE ENGINE DEMO" in out
        assert "Scenario: ARCTIC" in out
        assert "[STEP 1/12]" in out
        assert "[STEP 6/12]" in out
        assert "OPEN_BUT_UNINSURABLE" in out
        assert "[STEP 10/12]" in out
        assert "Effective substitution:                 PASS" in out
        assert "[STEP 12/12]" in out
        assert "DEMONSTRATION COMPLETE: 12/12" in out

    def test_run_civilian_demonstration_offline(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Run Civilian public health demonstration end-to-end completely offline."""
        exit_code = run_demo("civilian", no_color=True)
        assert exit_code == 0

        captured = capsys.readouterr()
        out = captured.out
        assert "CONTINUITYOS v1.0 — RESILIENCE-AS-CODE LIVE ENGINE DEMO" in out
        assert "Scenario: CIVILIAN" in out
        assert "[STEP 1/12]" in out
        assert "[STEP 12/12]" in out
        assert "DEMONSTRATION COMPLETE: 12/12" in out
