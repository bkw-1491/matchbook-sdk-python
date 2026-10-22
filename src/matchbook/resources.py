from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from matchbook.utils import decode, encode

OddsType = Literal["DECIMAL", "US", "HK", "MALAY", "INDO", "%"]
ExchangeType = Literal["back-lay", "binary"]
Side = Literal["back", "lay", "win", "lose"]
Currency = Literal["USD", "EUR", "GBP", "AUD", "CAD", "HKD"]
PriceMode = Literal["expanded", "aggregated"]
EventState = Literal["open", "suspended", "closed", "graded"]
MarketState = Literal["open", "suspended", "closed", "graded"]
RunnerState = Literal["open", "suspended", "closed", "graded"]
AggregationType = Literal["average", "summary"]
CancellationReason = Literal["user_request", "heartbeat_expiry"]
SportOrder = Literal["name asc", "name desc", "id asc", "id desc"]

OfferStatus = Literal[
    "open", "cancelled", "edited", "matched", "unmatched", "flushed", "failed", "delayed",
]

TransactionType = Literal["payout", "commission", "transfer", "cancel", "manual", "bonus"]


@dataclass(kw_only=True, slots=True)
class BaseModel:
    """
    Base class for every model.
    """

    @classmethod
    def from_json(cls: Any, data: dict[str, Any]) -> Any:
        """
        Build the model from a decoded JSON object.

        :param data: Object as the API returns it; undeclared keys are ignored.
        :returns: The model.
        """
        return decode(cls, data)

    def to_json(self) -> dict[str, Any]:
        """
        Convert the model to a JSON-ready dict.

        :returns: The non-``None`` fields, with kebab-case keys.
        """
        return encode(self)


@dataclass(kw_only=True, slots=True)
class Response(BaseModel):
    """
    Base class for a model an endpoint can return at the top level.

    Matchbook returns single documents (an offer, an event) bare rather than
    wrapped, so those models are responses too. Nested inside another response
    they still carry ``raw``, but the timings are only set on the top level.

    :param raw: The decoded body, for fields the model does not declare.

    :ivar sent_at: When the request was sent (UTC).
    :ivar received_at: When the response arrived (UTC).
    :ivar latency_ms: Milliseconds from sending to the response, timed on a
        monotonic clock, so not exactly ``received_at - sent_at``.
    """
    raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)
    sent_at: datetime = field(init=False, repr=False, compare=False)
    received_at: datetime = field(init=False, repr=False, compare=False)
    latency_ms: float = field(init=False, repr=False, compare=False)


@dataclass(kw_only=True, slots=True)
class PagedResponse(Response):
    """
    Base class for an offset-paged response.

    :param offset: Position of this page's first row.
    :param per_page: Rows asked for per page.
    :param total: Rows across all pages.
    """
    offset: int | None = None
    per_page: int | None = None
    total: int | None = None


@dataclass(kw_only=True, slots=True)
class FieldError(BaseModel):
    """
    A validation error on one field, e.g. on a failed offer or offer edit.
    """
    messages: list[str] = field(default_factory=list)
    codes: list[str] = field(default_factory=list)
    # Declared last: the name shadows ``dataclasses.field`` in the class body.
    field: str | None = None
