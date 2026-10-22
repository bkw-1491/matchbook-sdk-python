from collections.abc import Sequence
from datetime import datetime

from matchbook.endpoints import Endpoints
from matchbook.reports.resources import (
    CurrentMarketsResponse,
    SettledBetsResponse,
    TransactionsResponse,
)
from matchbook.resources import OddsType, TransactionType


class ReportsEndpoints(Endpoints):
    """
    Wallet transactions, and current and settled bet reports.
    """

    def get_transactions(
        self,
        *,
        transaction_types: Sequence[TransactionType] | None = None,
        after: datetime | None = None,
        before: datetime | None = None,
        offset: int | None = None,
        per_page: int | None = None,
    ) -> TransactionsResponse:
        """
        Fetch wallet transactions: ``GET /edge/rest/reports/v1/transactions``.

        :param transaction_types: Types to match, e.g. ``["payout", "commission"]``.
        :param after: Created after.
        :param before: Created before.
        :param offset: Position of the first row.
        :param per_page: Rows per page; the API defaults to 20.
        :returns: One page of transactions.
        """
        return self.conn.call(
            TransactionsResponse, "GET", "/edge/rest/reports/v1/transactions", params={
                "transaction-type": transaction_types,
                "after": after,
                "before": before,
                "offset": offset,
                "per-page": per_page,
            })

    def get_current_offers(
        self,
        *,
        sport_ids: Sequence[int] | None = None,
        event_ids: Sequence[int] | None = None,
        market_ids: Sequence[int] | None = None,
        odds_type: OddsType | None = None,
        after: datetime | None = None,
        before: datetime | None = None,
        offset: int | None = None,
        per_page: int | None = None,
    ) -> CurrentMarketsResponse:
        """
        Fetch offers on markets not yet settled: ``GET /edge/rest/reports/v2/offers/current``.

        :param sport_ids: Sport ids to match.
        :param event_ids: Event ids to match.
        :param market_ids: Market ids to match.
        :param odds_type: Format of the odds returned; the API defaults to ``"DECIMAL"``.
        :param after: Window start.
        :param before: Window end.
        :param offset: Position of the first row.
        :param per_page: Rows per page; the API defaults to 20.
        :returns: One page of markets, their offers under ``selections[].offers``.
        """
        return self.conn.call(
            CurrentMarketsResponse, "GET", "/edge/rest/reports/v2/offers/current", params={
                "sport-ids": sport_ids,
                "event-ids": event_ids,
                "market-ids": market_ids,
                "odds-type": odds_type,
                "after": after,
                "before": before,
                "offset": offset,
                "per-page": per_page,
            })

    def get_current_bets(
        self,
        *,
        sport_ids: Sequence[int] | None = None,
        event_ids: Sequence[int] | None = None,
        market_ids: Sequence[int] | None = None,
        odds_type: OddsType | None = None,
        after: datetime | None = None,
        before: datetime | None = None,
        offset: int | None = None,
        per_page: int | None = None,
    ) -> CurrentMarketsResponse:
        """
        Fetch matched bets on markets not yet settled: ``GET /edge/rest/reports/v2/bets/current``.

        :param sport_ids: Sport ids to match.
        :param event_ids: Event ids to match.
        :param market_ids: Market ids to match.
        :param odds_type: Format of the odds returned; the API defaults to ``"DECIMAL"``.
        :param after: Window start.
        :param before: Window end.
        :param offset: Position of the first row.
        :param per_page: Rows per page; the API defaults to 50.
        :returns: One page of markets, their bets under ``selections[].bets``.
        """
        return self.conn.call(
            CurrentMarketsResponse, "GET", "/edge/rest/reports/v2/bets/current", params={
                "sport-ids": sport_ids,
                "event-ids": event_ids,
                "market-ids": market_ids,
                "odds-type": odds_type,
                "after": after,
                "before": before,
                "offset": offset,
                "per-page": per_page,
            })

    def get_settled_bets(
        self,
        *,
        sport_ids: Sequence[int] | None = None,
        event_ids: Sequence[int] | None = None,
        market_ids: Sequence[int] | None = None,
        after: datetime | None = None,
        before: datetime | None = None,
        offset: int | None = None,
        per_page: int | None = None,
    ) -> SettledBetsResponse:
        """
        Fetch settled bets with profit and loss: ``GET /edge/rest/reports/v2/bets/settled``.

        :param sport_ids: Sport ids to match.
        :param event_ids: Event ids to match.
        :param market_ids: Market ids to match.
        :param after: Settled after.
        :param before: Settled before.
        :param offset: Position of the first row.
        :param per_page: Rows per page; the API defaults to 20.
        :returns: One page of settled markets with their bets.
        """
        return self.conn.call(
            SettledBetsResponse, "GET", "/edge/rest/reports/v2/bets/settled", params={
                "sport-ids": sport_ids,
                "event-ids": event_ids,
                "market-ids": market_ids,
                "after": after,
                "before": before,
                "offset": offset,
                "per-page": per_page,
            })
