from dataclasses import dataclass, field
from datetime import datetime

from matchbook.resources import BaseModel, PagedResponse, Response


@dataclass(kw_only=True, slots=True)
class Sport(BaseModel):
    """
    A sport.
    """
    id: int
    name: str
    type: str | None = None
    slug: str | None = None


@dataclass(kw_only=True, slots=True)
class SportsResponse(PagedResponse):
    """
    One page of sports.
    """
    sports: list[Sport] = field(default_factory=list)


@dataclass(kw_only=True, slots=True)
class MetaTag(BaseModel):
    """
    A navigation tag: a sport, country, competition, location or date.

    :param type: e.g. ``"SPORT"``, ``"COUNTRY"``, ``"COMPETITION"``, ``"DATE"``.
    :param url_name: Usable as an ``get_events(tag_url_names=...)`` filter.
    :param meta_tags: Child tags, in the navigation tree.
    """
    id: int
    name: str
    type: str | None = None
    url_name: str | None = None
    meta_tags: list["MetaTag"] = field(default_factory=list)


@dataclass(kw_only=True, slots=True)
class PopularSportsResponse(Response):
    """
    The most popular sports in the caller's country.
    """
    sports: list[Sport] = field(default_factory=list)
    country_id: str | None = None
    last_updated: datetime | None = None
    meta_tags: list[MetaTag] = field(default_factory=list)


@dataclass(kw_only=True, slots=True)
class Navigation(Response):
    """
    The root of the navigation tree; walk ``meta_tags`` down to events' tags.
    """
    id: int
    name: str
    tree_id: int | None = None
    url_name: str | None = None
    meta_tags: list[MetaTag] = field(default_factory=list)


@dataclass(kw_only=True, slots=True)
class Price(BaseModel):
    """
    One level of a runner's book.

    :param available_amount: Stake available at ``odds``.
    :param side: ``"back"`` (or ``"win"``) prices can be backed; ``"lay"`` (or ``"lose"``) laid.
    :param odds: In ``odds_type`` format.
    :param decimal_odds: ``odds`` in decimal.
    """
    available_amount: float
    odds: float
    side: str
    decimal_odds: float | None = None
    odds_type: str | None = None
    exchange_type: str | None = None
    currency: str | None = None


def side_of(prices: list[Price], sides: tuple[str, ...]) -> list[Price]:
    """
    The prices on the given sides, in the order the API gave them (best first).
    """
    return [p for p in prices if p.side in sides]


@dataclass(kw_only=True, slots=True)
class Runner(Response):
    """
    A selection in a market.

    :param prices: The book, if prices were requested; see ``available_to_back``.
    :param handicap: Line, on handicap and total markets.
    """
    id: int
    name: str
    event_id: int | None = None
    market_id: int | None = None
    status: str | None = None
    withdrawn: bool | None = None
    volume: float | None = None
    handicap: float | None = None
    event_participant_id: int | None = None
    prices: list[Price] = field(default_factory=list)

    def available_to_back(self) -> list[Price]:
        """
        Prices you can back at, best (highest) first.

        :returns: The ``back`` and ``win`` side prices.
        """
        return side_of(self.prices, ("back", "win"))

    def available_to_lay(self) -> list[Price]:
        """
        Prices you can lay at, best (lowest) first.

        :returns: The ``lay`` and ``lose`` side prices.
        """
        return side_of(self.prices, ("lay", "lose"))


@dataclass(kw_only=True, slots=True)
class RunnersResponse(PagedResponse):
    """
    A market's runners.
    """
    runners: list[Runner] = field(default_factory=list)


@dataclass(kw_only=True, slots=True)
class Market(Response):
    """
    A market on an event.

    :param market_type: e.g. ``"one_x_two"``, ``"handicap"``, ``"total"``, ``"outright"``.
    :param type: ``"multirunner"`` or ``"binary"``.
    :param in_running_flag: Whether the market is in play now.
    :param allow_live_betting: Whether the market stays open in play.
    :param back_overround: Sum of implied probabilities of the best backs, in percent.
    :param lay_overround: Sum of implied probabilities of the best lays, in percent.
    """
    id: int
    name: str
    event_id: int | None = None
    status: str | None = None
    market_type: str | None = None
    type: str | None = None
    start: datetime | None = None
    live: bool | None = None
    in_running_flag: bool | None = None
    allow_live_betting: bool | None = None
    short_listed: bool | None = None
    volume: float | None = None
    handicap: float | None = None
    number_of_winners: int | None = None
    back_overround: float | None = None
    lay_overround: float | None = None
    runners: list[Runner] = field(default_factory=list)

    def runner(self, runner_id: int) -> Runner | None:
        """
        Find a runner by id.

        :param runner_id: Runner id.
        :returns: The runner, or ``None`` if it isn't in this market.
        """
        return next((r for r in self.runners if r.id == runner_id), None)


@dataclass(kw_only=True, slots=True)
class MarketsResponse(PagedResponse):
    """
    One page of an event's markets.
    """
    markets: list[Market] = field(default_factory=list)


@dataclass(kw_only=True, slots=True)
class EventParticipant(BaseModel):
    """
    A team or competitor in an event.
    """
    id: int
    participant_name: str | None = None
    number: str | None = None
    event_id: int | None = None


@dataclass(kw_only=True, slots=True)
class Event(Response):
    """
    A sporting event.

    :param category_id: Ids of the tags the event sits under (sport, country, ...).
    :param in_running_flag: Whether the event is in play now.
    :param markets: Its markets, on the event endpoints.
    :param market_ids: Its markets' ids, on ``get_popular_markets``.
    """
    id: int
    name: str
    sport_id: int | None = None
    start: datetime | None = None
    status: str | None = None
    in_running_flag: bool | None = None
    allow_live_betting: bool | None = None
    volume: float | None = None
    category_id: list[int] = field(default_factory=list)
    markets: list[Market] = field(default_factory=list)
    market_ids: list[int] = field(default_factory=list)
    meta_tags: list[MetaTag] = field(default_factory=list)
    event_participants: list[EventParticipant] = field(default_factory=list)

    def market(self, market_id: int) -> Market | None:
        """
        Find a market by id.

        :param market_id: Market id.
        :returns: The market, or ``None`` if it isn't in ``markets``.
        """
        return next((m for m in self.markets if m.id == market_id), None)


@dataclass(kw_only=True, slots=True)
class EventsResponse(PagedResponse):
    """
    One page of events, ordered by start time.
    """
    events: list[Event] = field(default_factory=list)


@dataclass(kw_only=True, slots=True)
class PopularMarketsResponse(Response):
    """
    The most popular markets, with their events.

    By default ``events`` and ``markets`` are flat lists joined on ``Event.market_ids``;
    with ``old_format=True`` the markets are nested in ``Event.markets`` instead.
    """
    events: list[Event] = field(default_factory=list)
    markets: list[Market] = field(default_factory=list)


@dataclass(kw_only=True, slots=True)
class PricesResponse(Response):
    """
    A runner's book.
    """
    prices: list[Price] = field(default_factory=list)

    def available_to_back(self) -> list[Price]:
        """
        Prices you can back at, best (highest) first.

        :returns: The ``back`` and ``win`` side prices.
        """
        return side_of(self.prices, ("back", "win"))

    def available_to_lay(self) -> list[Price]:
        """
        Prices you can lay at, best (lowest) first.

        :returns: The ``lay`` and ``lose`` side prices.
        """
        return side_of(self.prices, ("lay", "lose"))
