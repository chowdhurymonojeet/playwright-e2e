from __future__ import annotations

from src.api.base_client import ApiError, BaseClient


class AuthClient(BaseClient):
    """Handles authentication flows for lower test environments."""

    def login(self, username: str, password: str) -> str:
        payload = {"username": username, "password": password}
        response_json = self.get_json(
            "POST",
            "/auth/login",
            expected_status=(200, 201),
            json=payload,
        )

        if not isinstance(response_json, dict):
            raise ApiError("Authentication response must be a JSON object")

        token = response_json.get("access_token")
        if not token or not isinstance(token, str):
            raise ApiError("Authentication response did not include access_token")

        return token
