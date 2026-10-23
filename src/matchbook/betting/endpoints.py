from collections.abc import Sequence

from matchbook.betting.resources import (
    AggregatedMatchedBetsResponse,
    MatchedBetsResponse,
    Offer,
    OfferEdit,
    OfferEditRequest,
    OfferEditsResponse,
    OfferRequest,
    OffersResponse,
    PositionsResponse,
)
from matchbook.endpoints import Endpoints
from matchbook.exceptions import MatchbookAPIError, MatchbookInvalidRequestError
from matchbook.resources import (
    AggregationType,
    CancellationReason,
    ExchangeType,
    OddsType,
    OfferStatus,
    Side,
)
from matchbook.utils import decode, encode


class BettingEndpoints(Endpoints):
    """
    Offers, their edits, matched bets and positions (the v2 offer API).
    """

    def submit_offers(
        self,
        offers: Sequence[OfferRequest],
        *,
        odds_type: OddsType | None = None,
        exchange_type: ExchangeType | None = None,
    ) -> OffersResponse:
        """
        Submit offers: ``POST /edge/rest/v2/offers``.

        Each offer succeeds or fails on its own; see ``OffersResponse``. Matchbook
        answers HTTP 400 when any offer fails, yet still places the rest, so that
        answer is returned like a 2xx one rather than raised. In play, an offer that
        would match comes back ``"delayed"`` and is matched or failed once the delay
        passes.

        :param offers: Offers to submit; see ``utils.batch`` to send many in chunks.
        :param odds_type: Format of every offer's ``odds``; the account's default if omitted.
        :param exchange_type: ``"back-lay"``; Matchbook no longer takes new binary offers.
        :returns: One ``Offer`` per request, failed ones with ``errors``.
        :raises MatchbookAPIError: On an error that carries no per-offer answer.
        """
        body = {
            "odds-type": odds_type,
            "exchange-type": exchange_type,
            "offers": encode(list(offers)),
        }
        try:
            return self.conn.call(
                OffersResponse, "POST", "/edge/rest/v2/offers",
                json={k: v for k, v in body.items() if v is not None})
        except MatchbookAPIError as exc:
            if exc.status_code != 400 or not isinstance(exc.body, dict) or "offers" not in exc.body:
                raise
            result = decode(OffersResponse, exc.body)
            result.sent_at = exc.sent_at
            result.received_at = exc.received_at
            result.latency_ms = exc.latency_ms
            return result

    def submit_offer(
        self,
        runner_id: int,
        side: Side,
        odds: float,
        stake: float,
        *,
        keep_in_play: bool | None = None,
        temp_id: str | None = None,
        odds_type: OddsType | None = None,
        exchange_type: ExchangeType | None = None,
    ) -> OffersResponse:
        """
        Submit one offer: ``POST /edge/rest/v2/offers``.

        :param runner_id: Runner to bet on.
        :param side: ``"back"`` or ``"lay"``.
        :param odds: In ``odds_type`` format.
        :param stake: Amount staked.
        :param keep_in_play: Keep the unmatched part when the event goes in play.
        :param temp_id: Your own reference for the offer, echoed as ``Offer.temp_id``.
        :param odds_type: Format of ``odds``; the account's default if omitted.
        :param exchange_type: ``"back-lay"``.
        :returns: The offer, in ``offers[0]``.
        """
        offer = OfferRequest(
            runner_id=runner_id, side=side, odds=odds, stake=stake, keep_in_play=keep_in_play,
            temp_id=temp_id)
        return self.submit_offers([offer], odds_type=odds_type, exchange_type=exchange_type)

    def edit_offers(self, edits: Sequence[OfferEditRequest]) -> OffersResponse:
        """
        Change the odds or remaining stake of unmatched offers: ``PUT /edge/rest/v2/offers``.

        In play, the edit is registered at once (``offer_edit.status == "delayed"``)
        and applied once the delay passes.

        :param edits: Changes to make.
        :returns: The offers, each with its ``offer_edit``.
        :raises MatchbookAPIError: 400 if an edit is rejected; the body lists each offer's errors.
        """
        return self.conn.call(
            OffersResponse, "PUT", "/edge/rest/v2/offers",
            json={"offers": encode(list(edits))})

    def edit_offer(
        self,
        offer_id: int,
        *,
        new_odds: float | None = None,
        new_stake: float | None = None,
        current_odds: float | None = None,
        current_stake: float | None = None,
    ) -> Offer:
        """
        Change one unmatched offer's odds or remaining stake:
        ``PUT /edge/rest/v2/offers/{offer_id}``.

        :param offer_id: Offer to edit.
        :param new_odds: Odds after the edit.
        :param new_stake: Remaining unmatched stake after the edit.
        :param current_odds: Odds before the edit; if given and stale, the edit fails.
        :param current_stake: Remaining stake before the edit; if given and stale, the edit fails.
        :returns: The offer, with its ``offer_edit``.
        :raises MatchbookInvalidRequestError: If neither ``new_odds`` nor ``new_stake`` is given.
        """
        if new_odds is None and new_stake is None:
            raise MatchbookInvalidRequestError("edit_offer needs new_odds or new_stake")
        edit = OfferEditRequest(
            id=offer_id, new_odds=new_odds, new_stake=new_stake,
            current_odds=current_odds, current_stake=current_stake)
        body = encode(edit)
        del body["id"]
        return self.conn.call(
            Offer, "PUT", "/edge/rest/v2/offers/{offer_id}",
            path_params={"offer_id": offer_id}, json=body)

    def cancel_offers(
        self,
        *,
        offer_ids: Sequence[int] | None = None,
        event_ids: Sequence[int] | None = None,
        market_ids: Sequence[int] | None = None,
        runner_ids: Sequence[int] | None = None,
    ) -> OffersResponse:
        """
        Cancel unmatched offers matching the filters: ``DELETE /edge/rest/v2/offers``.

        With no filters this cancels every open offer on the account.

        :param offer_ids: Offers to cancel.
        :param event_ids: Cancel offers on these events.
        :param market_ids: Cancel offers on these markets.
        :param runner_ids: Cancel offers on these runners.
        :returns: The cancelled offers.
        """
        return self.conn.call(OffersResponse, "DELETE", "/edge/rest/v2/offers", params={
            "offer-ids": offer_ids,
            "event-ids": event_ids,
            "market-ids": market_ids,
            "runner-ids": runner_ids,
        })

    def cancel_offer(self, offer_id: int) -> Offer:
        """
        Cancel one unmatched offer: ``DELETE /edge/rest/v2/offers/{offer_id}``.

        :param offer_id: Offer to cancel.
        :returns: The cancelled offer.
        :raises MatchbookAPIError: 400 if the offer is no longer open or edited.
        """
        return self.conn.call(
            Offer, "DELETE", "/edge/rest/v2/offers/{offer_id}",
            path_params={"offer_id": offer_id})

    def get_offers(
        self,
        *,
        sport_ids: Sequence[int] | None = None,
        event_ids: Sequence[int] | None = None,
        market_ids: Sequence[int] | None = None,
        runner_ids: Sequence[int] | None = None,
        side: Side | None = None,
        statuses: Sequence[OfferStatus] | None = None,
        interval: int | None = None,
        include_edits: bool | None = None,
        cancellation_reason: CancellationReason | None = None,
        aggregation_type: AggregationType | None = None,
        offset: int | None = None,
        per_page: int | None = None,
    ) -> OffersResponse:
        """
        Fetch unsettled offers matching the filters: ``GET /edge/rest/v2/offers``.

        Unmatched offers drop out about an hour after they are cancelled or flushed.

        :param sport_ids: Sport ids to match.
        :param event_ids: Event ids to match.
        :param market_ids: Market ids to match.
        :param runner_ids: Runner ids to match.
        :param side: Side to match.
        :param statuses: Statuses to match: ``open``, ``cancelled``, ``edited``,
            ``flushed``, ``matched`` or ``unmatched``.
        :param interval: Only offers submitted or changed in the last this-many seconds.
        :param include_edits: Return each offer's ``offer_edits``.
        :param cancellation_reason: On cancelled offers, ``"user_request"`` or
            ``"heartbeat_expiry"``.
        :param aggregation_type: ``"average"`` or ``"summary"`` to aggregate offers.
        :param offset: Position of the first row.
        :param per_page: Rows per page; the API defaults to 20.
        :returns: One page of offers.
        """
        return self.conn.call(OffersResponse, "GET", "/edge/rest/v2/offers", params={
            "sport-ids": sport_ids,
            "event-ids": event_ids,
            "market-ids": market_ids,
            "runner-ids": runner_ids,
            "side": side,
            "status": statuses,
            "interval": interval,
            "include-edits": include_edits,
            "cancellation-reason": cancellation_reason,
            "aggregation-type": aggregation_type,
            "offset": offset,
            "per-page": per_page,
        })

    def get_offer(self, offer_id: int, *, include_edits: bool | None = None) -> Offer:
        """
        Fetch one unsettled offer: ``GET /edge/rest/v2/offers/{offer_id}``.

        :param offer_id: Offer id.
        :param include_edits: Return the offer's ``offer_edits``.
        :returns: The offer.
        """
        return self.conn.call(
            Offer, "GET", "/edge/rest/v2/offers/{offer_id}",
            path_params={"offer_id": offer_id},
            params={"include-edits": include_edits})

    def get_offer_edits(
        self,
        offer_id: int,
        *,
        offset: int | None = None,
        per_page: int | None = None,
    ) -> OfferEditsResponse:
        """
        Fetch an offer's edits: ``GET /edge/rest/v2/offers/{offer_id}/offer-edits``.

        The docs give no response example; the shape here is inferred.

        :param offer_id: Offer id.
        :param offset: Position of the first row.
        :param per_page: Rows per page.
        :returns: The offer's edits.
        """
        return self.conn.call(
            OfferEditsResponse, "GET", "/edge/rest/v2/offers/{offer_id}/offer-edits",
            path_params={"offer_id": offer_id},
            params={"offset": offset, "per-page": per_page})

    def get_offer_edit(self, offer_id: int, offer_edit_id: int) -> OfferEdit:
        """
        Fetch one offer edit:
        ``GET /edge/rest/v2/offers/{offer_id}/offer-edits/{offer_edit_id}``.

        :param offer_id: Offer id.
        :param offer_edit_id: Edit id.
        :returns: The edit.
        """
        return self.conn.call(
            OfferEdit, "GET", "/edge/rest/v2/offers/{offer_id}/offer-edits/{offer_edit_id}",
            path_params={"offer_id": offer_id, "offer_edit_id": offer_edit_id})

    def get_aggregated_matched_bets(
        self,
        *,
        event_ids: Sequence[int] | None = None,
        market_ids: Sequence[int] | None = None,
        runner_ids: Sequence[int] | None = None,
        side: Side | None = None,
        aggregation_type: AggregationType | None = None,
        offset: int | None = None,
        per_page: int | None = None,
    ) -> AggregatedMatchedBetsResponse:
        """
        Fetch matched bets rolled up per runner and side:
        ``GET /edge/rest/v2/matched-bets/aggregated``.

        :param event_ids: Event ids to match.
        :param market_ids: Market ids to match.
        :param runner_ids: Runner ids to match.
        :param side: Side to match.
        :param aggregation_type: ``"average"`` (the default) or ``"summary"``.
        :param offset: Position of the first row.
        :param per_page: Rows per page; the API defaults to 20.
        :returns: One page of aggregated bets.
        """
        return self.conn.call(
            AggregatedMatchedBetsResponse, "GET", "/edge/rest/v2/matched-bets/aggregated",
            params={
                "event-ids": event_ids,
                "market-ids": market_ids,
                "runner-ids": runner_ids,
                "side": side,
                "aggregation-type": aggregation_type,
                "offset": offset,
                "per-page": per_page,
            })

    def get_cancelled_matched_bets(
        self,
        *,
        offset: int | None = None,
        per_page: int | None = None,
    ) -> MatchedBetsResponse:
        """
        Fetch matched bets that were later cancelled: ``GET /edge/rest/bets?status=cancelled``.

        The docs give this path only as ``/bets?status=cancelled``; the
        ``/edge/rest`` prefix is assumed from every other betting endpoint.

        :param offset: Position of the first row.
        :param per_page: Rows per page; the API defaults to 20.
        :returns: One page of cancelled bets.
        """
        return self.conn.call(MatchedBetsResponse, "GET", "/edge/rest/bets", params={
            "status": "cancelled",
            "offset": offset,
            "per-page": per_page,
        })

    def get_positions(
        self,
        *,
        event_ids: Sequence[int] | None = None,
        market_ids: Sequence[int] | None = None,
        runner_ids: Sequence[int] | None = None,
        offset: int | None = None,
        per_page: int | None = None,
    ) -> PositionsResponse:
        """
        Fetch potential profit or loss per runner: ``GET /edge/rest/account/positions``.

        :param event_ids: Event ids to match.
        :param market_ids: Market ids to match.
        :param runner_ids: Runner ids to match.
        :param offset: Position of the first row.
        :param per_page: Rows per page; the API defaults to 200.
        :returns: One page of positions.
        """
        return self.conn.call(PositionsResponse, "GET", "/edge/rest/account/positions", params={
            "event-ids": event_ids,
            "market-ids": market_ids,
            "runner-ids": runner_ids,
            "offset": offset,
            "per-page": per_page,
        })
