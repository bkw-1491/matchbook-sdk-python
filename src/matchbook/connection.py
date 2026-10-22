import time
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import requests

from matchbook.exceptions import (
    MatchbookAPIError,
    MatchbookConfigurationError,
    MatchbookDecodeError,
    MatchbookInvalidRequestError,
    MatchbookTransportError,
)
from matchbook.utils import decode, format_query_params

__all__ = ["ENVIRONMENTS", "MatchbookConnection"]

ENVIRONMENTS: dict[str, str] = {
    "prod": "https://api.matchbook.com",
}


class MatchbookConnection:
    """
    Where and how to reach the Matchbook API.

    Every endpoint group takes one::

        conn = MatchbookConnection(username, password)
        AccountEndpoints(conn).login()
        MarketsEndpoints(conn).get_events(sport_ids=[15])

    :param username: Used by ``login``.
    :param password: Used by ``login``.
    :param environment: ``"prod"``; ignored if ``base_url`` is given. Matchbook has no sandbox.
    :param base_url: API root, overriding ``environment``.
    :param session: ``requests.Session`` to send through; created if omitted.
    :param timeout: Seconds to wait per request; ``None`` waits forever.
    """

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        *,
        environment: str = "prod",
        base_url: str | None = None,
        session: requests.Session | None = None,
        timeout: float | None = 30.0,
    ) -> None:
        """
        Create a connection; see the class docstring for parameters.

        :raises MatchbookConfigurationError: If ``environment`` is unknown and no
            ``base_url`` is given.
        """
        if base_url is None and environment not in ENVIRONMENTS:
            raise MatchbookConfigurationError(
                f"unknown environment {environment!r}; "
                f"expected one of {sorted(ENVIRONMENTS)} or a base_url")
        base_url = base_url or ENVIRONMENTS[environment]

        self.username = username
        self.password = password
        self.base_url = base_url.rstrip("/")
        self.http = session or requests.Session()
        self.timeout = timeout

        # Sent as the ``session-token`` header. Set by ``login``, cleared by
        # ``logout``; may also be assigned directly to reuse a session obtained elsewhere.
        self.session_token: str | None = None

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
    ) -> Any:
        """
        Send a request to any path, e.g. one this SDK does not cover yet.

        :param method: HTTP method.
        :param path: Path below ``base_url``, e.g. ``"/edge/rest/v2/offers"``.
        :param params: Query parameters; ``None`` dropped, lists comma-joined,
            datetimes as UTC ISO 8601, booleans lower-case.
        :param json: Request body.
        :returns: The decoded JSON body, or ``None`` if empty.
        :raises MatchbookAPIError: On a non-2xx response.
        :raises MatchbookTransportError: If no response was received.
        :raises MatchbookDecodeError: If a 2xx body is not JSON.
        """
        return self._send(method, path, params, json)[0]

    def call(
        self,
        model: Any,
        method: str,
        path: str,
        *,
        path_params: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
    ) -> Any:
        """
        Send a request and decode the body into ``model``, stamped with its timings.

        :param model: Response model to decode into.
        :param method: HTTP method.
        :param path: Path below ``base_url``, with ``{placeholders}``.
        :param path_params: Placeholder values; URL-escaped.
        :param params: Query parameters, encoded as in ``request``.
        :param json: Request body.
        :returns: The decoded model.
        :raises MatchbookInvalidRequestError: If a path parameter is empty.
        :raises MatchbookDecodeError: If the body does not fit ``model``.
        """
        if path_params:
            missing = [k for k, v in path_params.items() if v is None or v == ""]
            if missing:
                raise MatchbookInvalidRequestError(f"{path} needs a value for {', '.join(missing)}")
            path = path.format_map(
                {k: quote(str(v), safe="") for k, v in path_params.items()})
        body, sent_at, received_at, latency_ms = self._send(method, path, params, json)
        try:
            result = decode(model, body or {})
        except MatchbookDecodeError as exc:
            raise MatchbookDecodeError(
                f"{method} {path}: body does not fit {model.__name__}") from exc
        result.sent_at = sent_at
        result.received_at = received_at
        result.latency_ms = latency_ms
        return result

    def _send(
        self,
        method: str,
        path: str,
        params: Mapping[str, Any] | None,
        json: Any,
    ) -> tuple[Any, datetime, datetime, float]:
        """
        Send a request, timing it.

        :returns: The decoded JSON body (or ``None`` if empty), when it was sent and
            when the response arrived (UTC), and the round trip in milliseconds.
        """
        headers = {"Accept": "application/json"}
        if self.session_token:
            headers["session-token"] = self.session_token
        sent_at = datetime.now(timezone.utc)
        started = time.perf_counter()
        try:
            response = self.http.request(
                method,
                self.base_url + path,
                params=format_query_params(params or {}),
                json=json,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise MatchbookTransportError(
                f"{method} {path} failed: {exc}", sent_at=sent_at,
                latency_ms=(time.perf_counter() - started) * 1000) from exc
        # The monotonic clock times the trip; the wall clock can jump.
        latency_ms = (time.perf_counter() - started) * 1000
        received_at = datetime.now(timezone.utc)
        if not response.ok:
            raise MatchbookAPIError(
                response, sent_at=sent_at, received_at=received_at, latency_ms=latency_ms)
        if not response.content:
            return None, sent_at, received_at, latency_ms
        try:
            return response.json(), sent_at, received_at, latency_ms
        except ValueError as exc:
            raise MatchbookDecodeError(f"{method} {path} returned a non-JSON body") from exc
