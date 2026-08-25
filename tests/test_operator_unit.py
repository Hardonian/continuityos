"""Unit tests for Kubernetes Operator module with mocked k8s client.

Targets: operator.py coverage from 51% → ≥85%.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from continuityos.operator import (
    CRD_GROUP,
    CRD_VERSION,
    PLURAL_NETWORK,
    PLURAL_POLICY,
    ContinuityOperator,
)

pytestmark = pytest.mark.anyio


class TestContinuityOperatorInit:
    """Test operator initialization with various kubeconfig scenarios."""

    @patch("continuityos.operator.config")
    @patch("continuityos.operator.client")
    def test_init_in_cluster(self, mock_client: MagicMock, mock_config: MagicMock) -> None:
        """When KUBERNETES_SERVICE_HOST is set, use in-cluster config."""
        with patch.dict("os.environ", {"KUBERNETES_SERVICE_HOST": "10.0.0.1"}):
            operator = ContinuityOperator(max_actions=10)

        mock_config.load_incluster_config.assert_called_once()
        mock_config.load_kube_config.assert_not_called()
        assert operator.compiler.max_actions == 10

    @patch("continuityos.operator.config")
    @patch("continuityos.operator.client")
    def test_init_local_kubeconfig(self, mock_client: MagicMock, mock_config: MagicMock) -> None:
        """When not in cluster, fall back to local kubeconfig."""
        with patch.dict("os.environ", {}, clear=True):
            # Ensure KUBERNETES_SERVICE_HOST is not set
            import os

            env = os.environ.copy()
            env.pop("KUBERNETES_SERVICE_HOST", None)
            with patch.dict("os.environ", env, clear=True):
                operator = ContinuityOperator(max_actions=50)

        mock_config.load_kube_config.assert_called_once()
        assert operator is not None

    @patch("continuityos.operator.config")
    @patch("continuityos.operator.client")
    def test_init_kubeconfig_load_failure(
        self, mock_client: MagicMock, mock_config: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Gracefully handle kubeconfig load failure with a warning."""
        mock_config.load_kube_config.side_effect = Exception("no kubeconfig found")
        with patch.dict("os.environ", {}, clear=True):
            import os

            env = os.environ.copy()
            env.pop("KUBERNETES_SERVICE_HOST", None)
            with (
                patch.dict("os.environ", env, clear=True),
                caplog.at_level(logging.WARNING, logger="continuityos.operator"),
            ):
                operator = ContinuityOperator()

        assert operator is not None
        assert any("Could not load kubeconfig" in r.message for r in caplog.records)


class TestReconcile:
    """Test the reconcile method for custom resources."""

    @patch("continuityos.operator.config")
    @patch("continuityos.operator.client")
    async def test_reconcile_success(self, mock_client: MagicMock, mock_config: MagicMock) -> None:
        """Successful reconciliation updates CRD status."""
        operator = ContinuityOperator()
        mock_api = MagicMock()
        operator.custom_api = mock_api

        obj: dict[str, Any] = {
            "metadata": {"name": "test-policy", "namespace": "sovereign-ns"},
            "spec": {"corridors": ["arctic-nwp"]},
        }

        await operator.reconcile(PLURAL_POLICY, obj)

        mock_api.patch_namespaced_custom_object_status.assert_called_once()
        call_kwargs = mock_api.patch_namespaced_custom_object_status.call_args
        assert call_kwargs.kwargs["name"] == "test-policy"
        assert call_kwargs.kwargs["namespace"] == "sovereign-ns"
        body = call_kwargs.kwargs["body"]
        assert body["status"]["phase"] == "Reconciled"

    @patch("continuityos.operator.config")
    @patch("continuityos.operator.client")
    async def test_reconcile_default_namespace(
        self, mock_client: MagicMock, mock_config: MagicMock
    ) -> None:
        """Missing namespace defaults to 'default'."""
        operator = ContinuityOperator()
        mock_api = MagicMock()
        operator.custom_api = mock_api

        obj: dict[str, Any] = {
            "metadata": {"name": "test-network"},
        }

        await operator.reconcile(PLURAL_NETWORK, obj)

        call_kwargs = mock_api.patch_namespaced_custom_object_status.call_args
        assert call_kwargs.kwargs["namespace"] == "default"

    @patch("continuityos.operator.config")
    @patch("continuityos.operator.client")
    async def test_reconcile_failure_patches_error_status(
        self, mock_client: MagicMock, mock_config: MagicMock
    ) -> None:
        """When reconciliation fails, the error status is patched onto the CRD."""
        operator = ContinuityOperator()
        mock_api = MagicMock()
        # First call (the successful patch in try block) raises, second call (error patch) succeeds
        mock_api.patch_namespaced_custom_object_status.side_effect = [
            Exception("API server error"),
            None,
        ]
        operator.custom_api = mock_api

        obj: dict[str, Any] = {
            "metadata": {"name": "broken-cr", "namespace": "ns"},
        }

        await operator.reconcile(PLURAL_POLICY, obj)

        assert mock_api.patch_namespaced_custom_object_status.call_count == 2
        error_call = mock_api.patch_namespaced_custom_object_status.call_args_list[1]
        assert error_call.kwargs["body"]["status"]["phase"] == "Failed"

    @patch("continuityos.operator.config")
    @patch("continuityos.operator.client")
    async def test_reconcile_failure_error_patch_also_fails(
        self, mock_client: MagicMock, mock_config: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """When both the reconcile and the error-status patch fail, log both errors."""
        operator = ContinuityOperator()
        mock_api = MagicMock()
        mock_api.patch_namespaced_custom_object_status.side_effect = [
            Exception("first failure"),
            Exception("second failure"),
        ]
        operator.custom_api = mock_api

        obj: dict[str, Any] = {
            "metadata": {"name": "double-fail", "namespace": "ns"},
        }

        with caplog.at_level(logging.ERROR, logger="continuityos.operator"):
            await operator.reconcile(PLURAL_POLICY, obj)

        error_messages = [r.message for r in caplog.records if r.levelno >= logging.ERROR]
        assert len(error_messages) >= 2


class TestWatchResource:
    """Test the watch_resource loop error handling paths."""

    @patch("continuityos.operator.config")
    @patch("continuityos.operator.client")
    @patch("continuityos.operator.watch")
    async def test_watch_404_crd_not_found(
        self, mock_watch_mod: MagicMock, mock_client: MagicMock, mock_config: MagicMock
    ) -> None:
        """When CRD is not installed (404), log error and retry."""
        from kubernetes.client.rest import ApiException

        operator = ContinuityOperator()
        mock_api = MagicMock()
        operator.custom_api = mock_api

        mock_watcher = MagicMock()
        mock_watch_mod.Watch.return_value = mock_watcher
        mock_watcher.stream.side_effect = ApiException(status=404)

        task = asyncio.create_task(operator.watch_resource(PLURAL_POLICY))
        await asyncio.sleep(0.1)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    @patch("continuityos.operator.config")
    @patch("continuityos.operator.client")
    @patch("continuityos.operator.watch")
    async def test_watch_unexpected_error(
        self, mock_watch_mod: MagicMock, mock_client: MagicMock, mock_config: MagicMock
    ) -> None:
        """Unexpected exceptions are caught, logged, and retried."""
        operator = ContinuityOperator()
        mock_api = MagicMock()
        operator.custom_api = mock_api

        mock_watcher = MagicMock()
        mock_watch_mod.Watch.return_value = mock_watcher
        mock_watcher.stream.side_effect = RuntimeError("network blip")

        task = asyncio.create_task(operator.watch_resource(PLURAL_NETWORK))
        await asyncio.sleep(0.1)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


class TestConstants:
    """Verify CRD constants are correct."""

    def test_crd_group(self) -> None:
        assert CRD_GROUP == "continuity.io"

    def test_crd_version(self) -> None:
        assert CRD_VERSION == "v1"

    def test_plurals(self) -> None:
        assert PLURAL_POLICY == "continuitypolicies"
        assert PLURAL_NETWORK == "supplynetworks"
