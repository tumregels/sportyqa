from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import requests

from . import config


@dataclass
class ApiError(Exception):
    """Raised for any non-2xx response, carrying the payload and code."""

    status: int
    error_code: str | None
    payload: dict[str, Any] | list | None

    def __str__(self) -> str:  # pragma: no cover - debug aid
        return (
            f"ApiError(status={self.status}, code={self.error_code}, "
            f"payload={self.payload})"
        )


class ApiClient:
    def __init__(
        self,
        base_url: str = config.API_BASE_URL,
        user_id: str = config.QA_USER_ID,
        timeout: float = config.API_TIMEOUT_SECONDS,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.user_id = user_id
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({config.USER_ID_HEADER: user_id})

    # -- transport helpers ---------------------------------------------------
    def _request(self, method: str, path: str, json: Any = None) -> tuple[int, Any]:
        resp = self.session.request(
            method, f"{self.base_url}{path}", json=json, timeout=self.timeout
        )
        payload: Any = {}
        if resp.content:
            try:
                payload = resp.json()
            except ValueError:
                payload = resp.text
        return resp.status_code, payload

    def _expect(self, method: str, path: str, json: Any = None) -> tuple[int, Any]:
        status, payload = self._request(method, path, json)
        if not 200 <= status < 300:
            code = payload.get("error") if isinstance(payload, dict) else None
            raise ApiError(status, code, payload)
        return status, payload

    # -- endpoints -----------------------------------------------------------
    def get_matches(self) -> list[dict[str, Any]]:
        """GET /api/matches -> list of match cards."""
        _, payload = self._expect("GET", "/api/matches")
        return payload if isinstance(payload, list) else []

    def get_balance(self) -> dict[str, Any]:
        """GET /api/balance -> {balance, currency}."""
        _, payload = self._expect("GET", "/api/balance")
        return payload

    def reset_balance(self) -> dict[str, Any]:
        """POST /api/reset-balance -> {message, balance, currency}."""
        _, payload = self._expect("POST", "/api/reset-balance")
        return payload

    def place_bet(
        self, match_id: str, selection: str, stake: float
    ) -> tuple[int, dict[str, Any]]:
        """POST /api/place-bet.

        Returns ``(status, payload)`` for BOTH success and 4xx/5xx, letting
        tests assert on validation/insufficient/conflict responses directly.
        """
        body = {"matchId": match_id, "selection": selection, "stake": stake}
        status, payload = self._request("POST", "/api/place-bet", json=body)
        return status, payload

    def upcoming_match(self) -> dict[str, Any] | None:
        """Return the first fixture that kicks off on/after today (match lists
        are dominated by PAST fixtures - see bug report BUG-07)."""

        today = datetime.now(UTC).date().isoformat()
        for m in self.get_matches():
            if m.get("kickoffDate", "") >= today:
                return m
        return None
