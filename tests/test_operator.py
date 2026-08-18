from unittest.mock import MagicMock

import pytest

from continuityos.operator import ContinuityOperator


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_operator_reconcile_success() -> None:
    operator = ContinuityOperator(max_actions=10)

    # Mock the Kubernetes API
    operator.custom_api = MagicMock()
    operator.custom_api.patch_namespaced_custom_object_status = MagicMock()

    # Create a mock Custom Resource Object
    mock_crd = {
        "metadata": {"name": "arctic-supply-network", "namespace": "continuity-system"},
        "spec": {"objectives": {"minimum_continuity": 0.95}},
    }

    # Run the reconcile loop manually
    await operator.reconcile("supplynetworks", mock_crd)

    # Assert that the API was called to patch the status
    operator.custom_api.patch_namespaced_custom_object_status.assert_called_once()

    call_kwargs = operator.custom_api.patch_namespaced_custom_object_status.call_args.kwargs
    assert call_kwargs["group"] == "continuity.io"
    assert call_kwargs["version"] == "v1"
    assert call_kwargs["namespace"] == "continuity-system"
    assert call_kwargs["plural"] == "supplynetworks"
    assert call_kwargs["name"] == "arctic-supply-network"

    status_patch = call_kwargs["body"]["status"]
    assert status_patch["phase"] == "Reconciled"
    assert "ContinuityOS Compiler successfully verified desired state" in status_patch["message"]


@pytest.mark.anyio
async def test_operator_reconcile_failure_handling() -> None:
    operator = ContinuityOperator(max_actions=10)
    operator.custom_api = MagicMock()

    # First call fails, second call (patching failed status) succeeds
    operator.custom_api.patch_namespaced_custom_object_status = MagicMock(
        side_effect=[RuntimeError("K8s API Timeout"), None]
    )

    mock_crd = {
        "metadata": {"name": "faulty-policy", "namespace": "default"},
        "spec": {},
    }

    await operator.reconcile("continuitypolicies", mock_crd)
    assert operator.custom_api.patch_namespaced_custom_object_status.call_count == 2
    second_call_kwargs = operator.custom_api.patch_namespaced_custom_object_status.call_args_list[
        1
    ].kwargs
    assert second_call_kwargs["body"]["status"]["phase"] == "Failed"
