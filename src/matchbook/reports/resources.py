from dataclasses import dataclass, field
from datetime import datetime

from matchbook.resources import BaseModel, PagedResponse


@dataclass(kw_only=True, slots=True)
class Transaction(BaseModel):
    """
    A wallet transaction.

    :param balance: Balance after the transaction.
    :param transaction_type: e.g. ``"Payout"``, ``"Commission"``, ``"Transfer"``.
    :param product: e.g. ``"Exchange"``, ``"Account"``.
    """
    id: int
    time: datetime
    balance: float | None = None
    credit: float | None = None
    debit: float | None = None
    detail: str | None = None
    transaction_type: str | None = None
    product: str | None = None


@dataclass(kw_only=True, slots=True)
class TransactionsResponse(PagedResponse):
    """
    One page of wallet transactions.
    """
    currency: str | None = None
    language: str | None = None
    transactions: list[Transaction] = field(default_factory=list)


@dataclass(kw_only=True, slots=True)
class CurrentBet(BaseModel):
    """
    A matched bet on a market not yet settled.
    """
    id: int
    odds: float
    stake: float
    in_play: bool | None = None
    matched_time: datetime | None = None
    adjusted: bool | None = None
    potential_profit: float | None = None
    liability: float | None = None


@dataclass(kw_only=True, slots=True)
class CurrentOffer(BaseModel):
    """
    An offer on a market not yet settled.
    """
    id: int
    odds: float
    stake: float
    in_play: bool | None = None
    submitted_time: datetime | None = None
    potential_profit: float | None = None
    liability: float | None = None


@dataclass(kw_only=True, slots=True)
class CurrentSelection(BaseModel):
    """
    Bets or offers on one runner and side, with their totals.

    :param bets: On ``get_current_bets``.
    :param offers: On ``get_current_offers``.
    """
    runner_id: int
    runner_name: str | None = None
    side: str | None = None
    odds: float | None = None
    stake: float | None = None
    liability: float | None = None
    potential_profit: float | None = None
    bets: list[CurrentBet] = field(default_factory=list)
    offers: list[CurrentOffer] = field(default_factory=list)


@dataclass(kw_only=True, slots=True)
class CurrentMarket(BaseModel):
    """
    An unsettled market's bets or offers, with totals.
    """
    id: int
    name: str | None = None
    event_id: int | None = None
    event_name: str | None = None
    sport_id: int | None = None
    start_time: datetime | None = None
    liability: float | None = None
    potential_profit: float | None = None
    selections: list[CurrentSelection] = field(default_factory=list)


@dataclass(kw_only=True, slots=True)
class CurrentMarketsResponse(PagedResponse):
    """
    One page of unsettled markets with their bets or offers, and grand totals.
    """
    language: str | None = None
    currency: str | None = None
    odds_type: str | None = None
    liability: float | None = None
    potential_profit: float | None = None
    markets: list[CurrentMarket] = field(default_factory=list)


@dataclass(kw_only=True, slots=True)
class SettledBet(BaseModel):
    """
    A settled bet.

    :param result: e.g. ``"WIN"``, ``"LOSE"``.
    :param originator: Whether this side's offer was in the market first.
    """
    id: int
    offer_id: int | None = None
    odds: float | None = None
    stake: float | None = None
    adjusted: bool | None = None
    originator: bool | None = None
    in_play: bool | None = None
    submitted_time: datetime | None = None
    matched_time: datetime | None = None
    settled_time: datetime | None = None
    result: str | None = None
    profit_and_loss: float | None = None
    commission_type: str | None = None
    commission: float | None = None
    net_profit_and_loss: float | None = None


@dataclass(kw_only=True, slots=True)
class SettledSelection(BaseModel):
    """
    Settled bets on one runner and side, with totals.
    """
    runner_id: int
    runner_name: str | None = None
    side: str | None = None
    odds: float | None = None
    stake: float | None = None
    profit_and_loss: float | None = None
    commission: float | None = None
    net_profit_and_loss: float | None = None
    bets: list[SettledBet] = field(default_factory=list)


@dataclass(kw_only=True, slots=True)
class SettledMarket(BaseModel):
    """
    A settled market's bets, with totals.
    """
    id: int
    name: str | None = None
    event_id: int | None = None
    event_name: str | None = None
    sport_id: int | None = None
    start_time: datetime | None = None
    settled_time: datetime | None = None
    profit_and_loss: float | None = None
    commission_type: str | None = None
    commission: float | None = None
    net_profit_and_loss: float | None = None
    selections: list[SettledSelection] = field(default_factory=list)


@dataclass(kw_only=True, slots=True)
class SettledBetsResponse(PagedResponse):
    """
    One page of settled markets with their bets, and grand totals.
    """
    language: str | None = None
    currency: str | None = None
    odds_type: str | None = None
    profit_and_loss: float | None = None
    commission: float | None = None
    net_profit_and_loss: float | None = None
    markets: list[SettledMarket] = field(default_factory=list)
