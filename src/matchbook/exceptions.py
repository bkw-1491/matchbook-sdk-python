from datetime import datetime
from typing import Any

import requests


class MatchbookError(Exception):
    """
    Base class for every error this SDK raises.
    """


class MatchbookConfigurationError(MatchbookError):
    """
    The connection is set up wrongly, e.g. an unknown environment.
    """


class MatchbookInvalidRequestError(MatchbookError):
    """
    A call is missing a required value; raised before anything is sent.
    """


class MatchbookInvalidPriceError(MatchbookError):
    """
    A price is off the odds ladder, or a ladder operation would leave it.
    """


class MatchbookDecodeError(MatchbookError):
    """
    A 2xx response body could not be decoded; the cause is the ``__cause__``.
    """


class MatchbookTransportError(MatchbookError):
    """
    The request got no response; the ``requests`` error is the ``__cause__``.

    :param message: What failed.
    :param sent_at: When the request was sent (UTC).
    :param latency_ms: Milliseconds from sending until it failed.
    """

    def __init__(self, message: str, *, sent_at: datetime, latency_ms: float) -> None:
        """
        Create the error; see the class docstring for parameters.
        """
        super().__init__(message)
        self.sent_at = sent_at
        self.latency_ms = latency_ms


class MatchbookAPIError(MatchbookError):
    """
    The API answered with a non-2xx status.

    Matchbook error bodies look like
    ``{"errors": [{"field": ..., "messages": [...], "codes": [...]}]}``.

    :param response: The failed response.
    :param sent_at: When the request was sent (UTC).
    :param received_at: When the response arrived (UTC).
    :param latency_ms: Milliseconds from sending to the response.

    :ivar status_code: HTTP status code, e.g. 404.
    :ivar messages: Every ``errors[].messages`` entry, flattened.
    :ivar codes: Every ``errors[].codes`` entry, flattened, e.g. ``"LOGIN_MFA_REQUIRED"``.
    :ivar fields: The ``errors[].field`` names, where given.
    :ivar body: The decoded JSON body, or the text if not JSON.
    :ivar response: The ``requests.Response``.
    """

    def __init__(
        self,
        response: requests.Response,
        *,
        sent_at: datetime,
        received_at: datetime,
        latency_ms: float,
    ) -> None:
        """
        Create the error from a failed response; see the class docstring for parameters.
        """
        try:
            body: Any = response.json()
        except ValueError:
            body = response.text

        messages: list[str] = []
        codes: list[str] = []
        fields: list[str] = []
        errors = body.get("errors") if isinstance(body, dict) else None
        if isinstance(errors, list):
            for error in errors:
                if not isinstance(error, dict):
                    continue
                messages += [str(m) for m in error.get("messages") or []]
                codes += [str(c) for c in error.get("codes") or []]
                if error.get("field"):
                    fields.append(str(error["field"]))

        self.status_code = response.status_code
        self.messages = messages
        self.codes = codes
        self.fields = fields
        self.body = body
        self.response = response
        self.sent_at = sent_at
        self.received_at = received_at
        self.latency_ms = latency_ms
        summary = "; ".join(messages) or response.reason or "error"
        super().__init__(f"{self.status_code} {summary}")
