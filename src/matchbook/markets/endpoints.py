from collections.abc import Sequence
from datetime import datetime

from matchbook.endpoints import Endpoints
from matchbook.markets.resources import (
    Event,
    EventsResponse,
    Market,
    MarketsResponse,
    Navigation,
    PopularMarketsResponse,
    PopularSportsResponse,
    PricesResponse,
    Runner,
    RunnersResponse,
    SportsResponse,
)
from matchbook.resources import (
    Currency,
    EventState,
    ExchangeType,
    MarketState,
    OddsType,
    PriceMode,
    RunnerState,
    Side,
    SportOrder,
)
from matchbook.utils import to_epoch


class MarketsEndpoints(Endpoints):
    """
    Sports, navigation, events, markets, runners and prices.

    The price filters shared by most of these calls:

    - ``include_prices``: return each runner's book.
    - ``price_depth``: price levels per side, default 3.
    - ``price_mode``: ``"expanded"`` (every level to ``price_depth``) or ``"aggregated"``.
    - ``side``: only prices on one side; both if omitted.
    - ``exchange_type``, ``odds_type``, ``currency``: format of the prices.
    - ``minimum_liquidity``: hide levels with less available; the API defaults
      to 2 on racing and 10 elsewhere.
    - ``exclude_mirrored_prices``: on binary markets, only the originator prices.
    """

    def get_sports(
        self,
        *,
        statuses: Sequence[str] | None = None,
        order: SportOrder | None = None,
        offset: int | None = None,
        per_page: int | None = None,
    ) -> SportsResponse:
        """
        Fetch the sports Matchbook offers: ``GET /edge/rest/lookups/sports``.

        :param statuses: Sport statuses to match; the API defaults to ``["active"]``.
        :param order: Sort order, e.g. ``"name asc"``.
        :param offset: Position of the first row.
        :param per_page: Rows per page; the API defaults to 20.
        :returns: One page of sports.
        """
        return self.conn.call(SportsResponse, "GET", "/edge/rest/lookups/sports", params={
            "status": statuses,
            "order": order,
            "offset": offset,
            "per-page": per_page,
        })

    def get_popular_sports(self, num_sports: int | None = None) -> PopularSportsResponse:
        """
        Fetch the most popular sports: ``GET /edge/rest/popular/sports``.

        :param num_sports: How many, 1–8; the API defaults to 5.
        :returns: The popular sports.
        """
        return self.conn.call(
            PopularSportsResponse, "GET", "/edge/rest/popular/sports",
            params={"num-sports": num_sports})

    def get_navigation(
        self,
        *,
        offset: int | None = None,
        per_page: int | None = None,
    ) -> Navigation:
        """
        Fetch the navigation tree of tags: ``GET /edge/rest/navigation``.

        :param offset: Position of the first row.
        :param per_page: Rows per page.
        :returns: The tree's root.
        """
        return self.conn.call(Navigation, "GET", "/edge/rest/navigation", params={
            "offset": offset,
            "per-page": per_page,
        })

    def get_events(
        self,
        *,
        ids: Sequence[int] | None = None,
        sport_ids: Sequence[int] | None = None,
        category_ids: Sequence[int] | None = None,
        tag_url_names: Sequence[str] | None = None,
        states: Sequence[EventState] | None = None,
        after: datetime | None = None,
        before: datetime | None = None,
        include_prices: bool | None = None,
        price_depth: int | None = None,
        price_mode: PriceMode | None = None,
        side: Side | None = None,
        exchange_type: ExchangeType | None = None,
        odds_type: OddsType | None = None,
        currency: Currency | None = None,
        minimum_liquidity: float | None = None,
        exclude_mirrored_prices: bool | None = None,
        include_event_participants: bool | None = None,
        markets_limit: int | None = None,
        offset: int | None = None,
        per_page: int | None = None,
    ) -> EventsResponse:
        """
        Fetch events matching the filters, by start time: ``GET /edge/rest/events``.

        See the class docstring for the price filters.

        :param ids: Event ids to match.
        :param sport_ids: Sport ids to match.
        :param category_ids: Category (tag) ids to match.
        :param tag_url_names: Tag ``url_name``s to match.
        :param states: Event states to match; the API defaults to all of them.
        :param after: Starting after; sent as Unix seconds.
        :param before: Starting before; sent as Unix seconds.
        :param include_event_participants: Return each event's participants.
        :param markets_limit: Most markets to return per event.
        :param offset: Position of the first row.
        :param per_page: Rows per page; the API defaults to 20.
        :returns: One page of events.
        """
        return self.conn.call(EventsResponse, "GET", "/edge/rest/events", params={
            "ids": ids,
            "sport-ids": sport_ids,
            "category-ids": category_ids,
            "tag-url-names": tag_url_names,
            "states": states,
            "after": to_epoch(after) if after else None,
            "before": to_epoch(before) if before else None,
            "include-prices": include_prices,
            "price-depth": price_depth,
            "price-mode": price_mode,
            "side": side,
            "exchange-type": exchange_type,
            "odds-type": odds_type,
            "currency": currency,
            "minimum-liquidity": minimum_liquidity,
            "exclude-mirrored-prices": exclude_mirrored_prices,
            "include-event-participants": include_event_participants,
            "markets-limit": markets_limit,
            "offset": offset,
            "per-page": per_page,
        })

    def get_event(
        self,
        event_id: int,
        *,
        include_prices: bool | None = None,
        price_depth: int | None = None,
        price_mode: PriceMode | None = None,
        side: Side | None = None,
        exchange_type: ExchangeType | None = None,
        odds_type: OddsType | None = None,
        currency: Currency | None = None,
        minimum_liquidity: float | None = None,
        exclude_mirrored_prices: bool | None = None,
        include_event_participants: bool | None = None,
        markets_limit: int | None = None,
    ) -> Event:
        """
        Fetch one event with its markets: ``GET /edge/rest/events/{event_id}``.

        See the class docstring for the price filters.

        :param event_id: Event id.
        :param include_event_participants: Return the event's participants.
        :param markets_limit: Most markets to return.
        :returns: The event.
        """
        return self.conn.call(
            Event, "GET", "/edge/rest/events/{event_id}",
            path_params={"event_id": event_id},
            params={
                "include-prices": include_prices,
                "price-depth": price_depth,
                "price-mode": price_mode,
                "side": side,
                "exchange-type": exchange_type,
                "odds-type": odds_type,
                "currency": currency,
                "minimum-liquidity": minimum_liquidity,
                "exclude-mirrored-prices": exclude_mirrored_prices,
                "include-event-participants": include_event_participants,
                "markets-limit": markets_limit,
            })

    def get_markets(
        self,
        event_id: int,
        *,
        names: Sequence[str] | None = None,
        types: Sequence[str] | None = None,
        states: Sequence[MarketState] | None = None,
        include_prices: bool | None = None,
        price_depth: int | None = None,
        price_mode: PriceMode | None = None,
        side: Side | None = None,
        exchange_type: ExchangeType | None = None,
        odds_type: OddsType | None = None,
        currency: Currency | None = None,
        minimum_liquidity: float | None = None,
        exclude_mirrored_prices: bool | None = None,
        offset: int | None = None,
        per_page: int | None = None,
    ) -> MarketsResponse:
        """
        Fetch an event's markets: ``GET /edge/rest/events/{event_id}/markets``.

        See the class docstring for the price filters.

        :param event_id: Event id.
        :param names: Market names to match, e.g. ``["Match Odds"]``.
        :param types: Market types to match, e.g. ``["one_x_two"]``.
        :param states: Market states to match; the API defaults to ``open`` and ``suspended``.
        :param offset: Position of the first row.
        :param per_page: Rows per page; the API defaults to 20.
        :returns: One page of markets.
        """
        return self.conn.call(
            MarketsResponse, "GET", "/edge/rest/events/{event_id}/markets",
            path_params={"event_id": event_id},
            params={
                "names": names,
                "types": types,
                "states": states,
                "include-prices": include_prices,
                "price-depth": price_depth,
                "price-mode": price_mode,
                "side": side,
                "exchange-type": exchange_type,
                "odds-type": odds_type,
                "currency": currency,
                "minimum-liquidity": minimum_liquidity,
                "exclude-mirrored-prices": exclude_mirrored_prices,
                "offset": offset,
                "per-page": per_page,
            })

    def get_market(
        self,
        event_id: int,
        market_id: int,
        *,
        include_prices: bool | None = None,
        price_depth: int | None = None,
        price_mode: PriceMode | None = None,
        side: Side | None = None,
        exchange_type: ExchangeType | None = None,
        odds_type: OddsType | None = None,
        currency: Currency | None = None,
        minimum_liquidity: float | None = None,
        exclude_mirrored_prices: bool | None = None,
    ) -> Market:
        """
        Fetch one market: ``GET /edge/rest/events/{event_id}/markets/{market_id}``.

        See the class docstring for the price filters.

        :param event_id: Event id.
        :param market_id: Market id.
        :returns: The market with its runners.
        """
        return self.conn.call(
            Market, "GET", "/edge/rest/events/{event_id}/markets/{market_id}",
            path_params={"event_id": event_id, "market_id": market_id},
            params={
                "include-prices": include_prices,
                "price-depth": price_depth,
                "price-mode": price_mode,
                "side": side,
                "exchange-type": exchange_type,
                "odds-type": odds_type,
                "currency": currency,
                "minimum-liquidity": minimum_liquidity,
                "exclude-mirrored-prices": exclude_mirrored_prices,
            })

    def get_runners(
        self,
        event_id: int,
        market_id: int,
        *,
        states: Sequence[RunnerState] | None = None,
        include_withdrawn: bool | None = None,
        include_prices: bool | None = None,
        price_depth: int | None = None,
        price_mode: PriceMode | None = None,
        side: Side | None = None,
        exchange_type: ExchangeType | None = None,
        odds_type: OddsType | None = None,
        currency: Currency | None = None,
        minimum_liquidity: float | None = None,
        exclude_mirrored_prices: bool | None = None,
    ) -> RunnersResponse:
        """
        Fetch a market's runners:
        ``GET /edge/rest/events/{event_id}/markets/{market_id}/runners``.

        See the class docstring for the price filters; here ``include_prices``
        defaults to true.

        :param event_id: Event id.
        :param market_id: Market id.
        :param states: Runner states to match; the API defaults to ``open`` and ``suspended``.
        :param include_withdrawn: Return withdrawn runners; the API defaults to true.
        :returns: The runners.
        """
        return self.conn.call(
            RunnersResponse, "GET", "/edge/rest/events/{event_id}/markets/{market_id}/runners",
            path_params={"event_id": event_id, "market_id": market_id},
            params={
                "states": states,
                "include-withdrawn": include_withdrawn,
                "include-prices": include_prices,
                "price-depth": price_depth,
                "price-mode": price_mode,
                "side": side,
                "exchange-type": exchange_type,
                "odds-type": odds_type,
                "currency": currency,
                "minimum-liquidity": minimum_liquidity,
                "exclude-mirrored-prices": exclude_mirrored_prices,
            })

    def get_runner(
        self,
        event_id: int,
        market_id: int,
        runner_id: int,
        *,
        include_prices: bool | None = None,
        price_depth: int | None = None,
        price_mode: PriceMode | None = None,
        side: Side | None = None,
        exchange_type: ExchangeType | None = None,
        odds_type: OddsType | None = None,
        currency: Currency | None = None,
        minimum_liquidity: float | None = None,
        exclude_mirrored_prices: bool | None = None,
    ) -> Runner:
        """
        Fetch one runner:
        ``GET /edge/rest/events/{event_id}/markets/{market_id}/runners/{runner_id}``.

        See the class docstring for the price filters.

        :param event_id: Event id.
        :param market_id: Market id.
        :param runner_id: Runner id.
        :returns: The runner.
        """
        return self.conn.call(
            Runner, "GET",
            "/edge/rest/events/{event_id}/markets/{market_id}/runners/{runner_id}",
            path_params={"event_id": event_id, "market_id": market_id, "runner_id": runner_id},
            params={
                "include-prices": include_prices,
                "price-depth": price_depth,
                "price-mode": price_mode,
                "side": side,
                "exchange-type": exchange_type,
                "odds-type": odds_type,
                "currency": currency,
                "minimum-liquidity": minimum_liquidity,
                "exclude-mirrored-prices": exclude_mirrored_prices,
            })

    def get_prices(
        self,
        event_id: int,
        market_id: int,
        runner_id: int,
        *,
        depth: int | None = None,
        price_mode: PriceMode | None = None,
        side: Side | None = None,
        exchange_type: ExchangeType | None = None,
        odds_type: OddsType | None = None,
        currency: Currency | None = None,
        minimum_liquidity: float | None = None,
        exclude_mirrored_prices: bool | None = None,
    ) -> PricesResponse:
        """
        Fetch one runner's book:
        ``GET /edge/rest/events/{event_id}/markets/{market_id}/runners/{runner_id}/prices``.

        See the class docstring for the price filters.

        :param event_id: Event id.
        :param market_id: Market id.
        :param runner_id: Runner id.
        :param depth: Price levels per side; the API defaults to 3.
        :returns: The runner's prices.
        """
        return self.conn.call(
            PricesResponse, "GET",
            "/edge/rest/events/{event_id}/markets/{market_id}/runners/{runner_id}/prices",
            path_params={"event_id": event_id, "market_id": market_id, "runner_id": runner_id},
            params={
                "depth": depth,
                "price-mode": price_mode,
                "side": side,
                "exchange-type": exchange_type,
                "odds-type": odds_type,
                "currency": currency,
                "minimum-liquidity": minimum_liquidity,
                "exclude-mirrored-prices": exclude_mirrored_prices,
            })

    def get_popular_markets(
        self,
        *,
        old_format: bool | None = None,
        price_depth: int | None = None,
        price_mode: PriceMode | None = None,
        side: Side | None = None,
        exchange_type: ExchangeType | None = None,
        odds_type: OddsType | None = None,
        currency: Currency | None = None,
        minimum_liquidity: float | None = None,
    ) -> PopularMarketsResponse:
        """
        Fetch the most popular markets: ``GET /edge/rest/popular-markets``.

        See the class docstring for the price filters.

        :param old_format: Nest markets inside their events instead of listing them apart.
        :returns: The popular markets and their events.
        """
        return self.conn.call(
            PopularMarketsResponse, "GET", "/edge/rest/popular-markets", params={
                "old-format": old_format,
                "price-depth": price_depth,
                "price-mode": price_mode,
                "side": side,
                "exchange-type": exchange_type,
                "odds-type": odds_type,
                "currency": currency,
                "minimum-liquidity": minimum_liquidity,
            })
