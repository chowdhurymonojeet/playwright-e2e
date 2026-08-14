from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

import requests

if TYPE_CHECKING:
    from src.services.test_context import TestContext


class ApiError(RuntimeError):
    """Raised when a service call fails or returns an unexpected result."""


class BaseClient:
    """Thin wrapper around an HTTP session with consistent error handling."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float = 15.0,
        session: Any | None = None,
        context: TestContext | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()
        self.context = context

    def _build_url(self, path: str) -> str:
        return urljoin(self.base_url, path.lstrip("/"))

    def _request(
        self,
        method: str,
        path: str,
        *,
        expected_status: int | Sequence[int] = 200,
        **kwargs: Any,
    ) -> requests.Response:
        expected_statuses = (
            (expected_status,)
            if isinstance(expected_status, int)
            else tuple(expected_status)
        )

        # Inject correlation headers if context available
        if self.context:
            headers = dict(kwargs.get("headers", {}))
            headers.setdefault("X-Correlation-ID", self.context.correlation_id)
            headers.setdefault("X-Run-ID", self.context.run_id)
            kwargs["headers"] = headers

        try:
            response = self.session.request(
                method=method,
                url=self._build_url(path),
                timeout=self.timeout_seconds,
                **kwargs,
            )
        except requests.RequestException as error:
            raise ApiError(f"{method.upper()} {path} failed: {error}") from error

        if response.status_code not in expected_statuses:
            summary = response.text[:500]
            raise ApiError(
                f"{method.upper()} {path} returned {response.status_code}; "
                f"expected {expected_statuses}. Response: {summary}"
            )

        return response

    def get_json(
        self,
        method: str,
        path: str,
        *,
        expected_status: int | Sequence[int] = 200,
        headers: Mapping[str, str] | None = None,
        json: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        response = self._request(
            method,
            path,
            expected_status=expected_status,
            headers=headers,
            json=json,
            params=params,
        )

        try:
            return response.json()
        except ValueError as error:
            raise ApiError(f"{method.upper()} {path} returned invalid JSON") from error
