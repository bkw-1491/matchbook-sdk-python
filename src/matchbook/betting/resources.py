from dataclasses import dataclass, field
from datetime import datetime

from matchbook.resources import BaseModel, FieldError, PagedResponse, Response, Side


@dataclass(kw_only=True, slots=True)
class OfferRequest(BaseModel):
    """
    One offer to submit with ``submit_offers``.

    :param runner_id: Runner to bet on.
    :param side: ``"back"`` or ``"lay"`` (``"win"``/``"lose"`` on binary markets).
    :param odds: In the request's ``odds_type`` (the account's default if not given).
    :param stake: Amount staked.
    :param keep_in_play: Keep the unmatched part when the event goes in play;
        the API defaults to false.
    :param temp_id: Your own reference for the offer, echoed as ``Offer.temp_id`` on the
        submit, get and cancel responses. Undocumented by Matchbook; other unknown fields are
        silently dropped.
    """
    runner_id: int
    side: Side
    odds: float
    stake: float
    keep_in_play: bool | None = None
    temp_id: str | None = None


@dataclass(kw_only=True, slots=True)
class OfferEditRequest(BaseModel):
    """
    One change to submit with ``edit_offers``.

    :param id: Offer to edit.
    :param new_odds: Odds after the edit.
    :param new_stake: Remaining unmatched stake after the edit.
    :param current_odds: Odds before the edit; if given and stale, the edit fails.
    :param current_stake: Remaining stake before the edit; if given and stale, the edit fails.
    """
    id: int
    new_odds: float | None = None
    new_stake: float | None = None
    current_odds: float | None = None
    current_stake: float | None = None


@dataclass(kw_only=True, slots=True)
class OfferEdit(Response):
    """
    An edit to an offer's odds or stake.

    :param status: ``"applied"``, ``"delayed"`` (waiting out the in-play delay) or ``"failed"``.
    :param failure_reason: Why a delayed edit failed, e.g. ``"market_status"``.
    :param delay: In-play delay in seconds.
    :param errors: Why the edit was rejected, on a failed request.
    """
    id: int | None = None
    offer_id: int | None = None
    runner_id: int | None = None
    odds_type: str | None = None
    odds_before: float | None = None
    decimal_odds_before: float | None = None
    odds_after: float | None = None
    decimal_odds_after: float | None = None
    stake_before: float | None = None
    stake_after: float | None = None
    status: str | None = None
    failure_reason: str | None = None
    delay: float | None = None
    edit_time: datetime | None = None
    errors: list[FieldError] = field(default_factory=list)


@dataclass(kw_only=True, slots=True)
class OfferEditsResponse(PagedResponse):
    """
    An offer's edits.
    """
    offer_edits: list[OfferEdit] = field(default_factory=list)


@dataclass(kw_only=True, slots=True)
class MatchedBet(BaseModel):
    """
    A bet: the part of an offer matched against another user.
    """
    id: int
    offer_id: int | None = None
    odds: float | None = None
    odds_type: str | None = None
    decimal_odds: float | None = None
    stake: float | None = None
    potential_profit: float | None = None
    potential_liability: float | None = None
    commission: float | None = None
    currency: str | None = None
    created_at: datetime | None = None
    status: str | None = None
    in_play: bool | None = None
    block_trade_id: int | None = None


@dataclass(kw_only=True, slots=True)
class Offer(Response):
    """
    An offer: a willingness to bet, matched in whole or part into ``matched_bets``.

    :param status: See ``OfferStatus``; ``"delayed"`` while waiting out an in-play delay.
    :param remaining: Stake still unmatched.
    :param potential_profit: On a back; ``potential_liability`` on a lay.
    :param delay: In-play delay in seconds, when one applies.
    :param offer_edit: The edit just made, on ``edit_offer(s)`` responses.
    :param offer_edits: Every edit, when asked for with ``include_edits``.
    :param errors: Why the offer failed, when ``status`` is ``"failed"``.
    """
    id: int | None = None
    event_id: int | None = None
    event_name: str | None = None
    market_id: int | None = None
    market_name: str | None = None
    market_type: str | None = None
    runner_id: int | None = None
    runner_name: str | None = None
    sport_id: int | None = None
    temp_id: str | None = None
    exchange_type: str | None = None
    side: str | None = None
    odds: float | None = None
    odds_type: str | None = None
    decimal_odds: float | None = None
    stake: float | None = None
    remaining: float | None = None
    potential_profit: float | None = None
    remaining_potential_profit: float | None = None
    potential_liability: float | None = None
    remaining_potential_liability: float | None = None
    commission_type: str | None = None
    originator_commission_rate: float | None = None
    acceptor_commission_rate: float | None = None
    commission_reserve: float | None = None
    currency: str | None = None
    created_at: datetime | None = None
    status: str | None = None
    in_play: bool | None = None
    keep_in_play: bool | None = None
    delay: float | None = None
    matched_bets: list[MatchedBet] = field(default_factory=list)
    offer_edit: OfferEdit | None = None
    offer_edits: list[OfferEdit] = field(default_factory=list)
    errors: list[FieldError] = field(default_factory=list)

    @property
    def stake_matched(self) -> float:
        """
        Stake matched so far.

        :returns: ``stake - remaining``, or 0 if either is missing.
        """
        if self.stake is None or self.remaining is None:
            return 0.0
        return self.stake - self.remaining


@dataclass(kw_only=True, slots=True)
class OffersResponse(PagedResponse):
    """
    Offers submitted, edited, cancelled or fetched.

    On a submit, each offer succeeds or fails on its own: check each ``status``
    (``"failed"`` with ``errors``). Matchbook sends that answer with HTTP 400 when
    any offer failed; ``submit_offers`` returns it all the same.
    """
    language: str | None = None
    currency: str | None = None
    exchange_type: str | None = None
    odds_type: str | None = None
    offers: list[Offer] = field(default_factory=list)


@dataclass(kw_only=True, slots=True)
class AggregatedMatchedBet(BaseModel):
    """
    Matched bets on one runner and side, rolled into one.
    """
    runner_id: int
    side: str
    odds: float | None = None
    odds_type: str | None = None
    decimal_odds: float | None = None
    stake: float | None = None
    potential_profit: float | None = None
    potential_liability: float | None = None
    event_id: int | None = None
    event_name: str | None = None
    market_id: int | None = None
    market_name: str | None = None
    runner_name: str | None = None


@dataclass(kw_only=True, slots=True)
class AggregatedMatchedBetsResponse(PagedResponse):
    """
    Matched bets aggregated per runner and side.
    """
    currency: str | None = None
    exchange_type: str | None = None
    odds_type: str | None = None
    matched_bets: list[AggregatedMatchedBet] = field(default_factory=list)


@dataclass(kw_only=True, slots=True)
class MatchedBetsResponse(PagedResponse):
    """
    One page of matched bets.
    """
    matched_bets: list[MatchedBet] = field(default_factory=list)


@dataclass(kw_only=True, slots=True)
class Position(BaseModel):
    """
    Profit or loss on a runner if it wins.

    Depending on the account, the API reports either ``potential_profit`` or
    ``potential_loss``, or both ``pnl_on_win`` and ``pnl_on_lose``.
    """
    event_id: int
    market_id: int
    runner_id: int
    potential_profit: float | None = None
    potential_loss: float | None = None
    pnl_on_win: float | None = None
    pnl_on_lose: float | None = None


@dataclass(kw_only=True, slots=True)
class PositionsResponse(PagedResponse):
    """
    One page of positions.
    """
    positions: list[Position] = field(default_factory=list)
