import itertools

from conftest import check

from matchbook import MatchbookClient
from matchbook.markets import Event, Market, Runner
from matchbook.utils import paginate


def test_sports(client: MatchbookClient):
    """
    Sports and popular sports can be listed; soccer is among them.
    """
    sports = check(client.get_sports(per_page=100)).sports
    assert any(s.id == 15 for s in sports)
    assert check(client.get_popular_sports(3)).sports


def test_navigation(client: MatchbookClient):
    """
    The navigation tree has sports beneath its root.
    """
    root = check(client.get_navigation())
    assert any(tag.type == "SPORT" for tag in root.meta_tags)


def test_events(client: MatchbookClient, open_event: Event):
    """
    Events filter by sport and can be fetched by id.
    """
    page = check(client.get_events(sport_ids=[15], per_page=5))
    assert page.events and all(e.sport_id == 15 for e in page.events)
    one = check(client.get_event(open_event.id, include_event_participants=True))
    assert one.id == open_event.id
    assert [m.id for m in one.markets] == [m.id for m in open_event.markets]


def test_events_paginate(client: MatchbookClient):
    """
    Paging walks forward without repeating events.
    """
    pages = list(itertools.islice(paginate(client.get_events, sport_ids=[15], per_page=5), 3))
    ids = [e.id for page in pages for e in page.events]
    assert len(ids) == len(set(ids))
    assert [p.offset for p in pages] == [0, 5, 10][:len(pages)]


def test_markets(client: MatchbookClient, open_event: Event, open_market: Market):
    """
    An event's markets can be listed and fetched by id, with prices.
    """
    markets = check(client.get_markets(open_event.id, include_prices=True)).markets
    assert open_market.id in [m.id for m in markets]
    one = check(client.get_market(open_event.id, open_market.id, include_prices=True))
    assert one.id == open_market.id


def test_runners_and_prices(
    client: MatchbookClient, open_event: Event, open_market: Market, open_runner: Runner,
):
    """
    A market's runners and a runner's book can be read; backs are best-first.
    """
    runners = check(client.get_runners(open_event.id, open_market.id)).runners
    assert open_runner.id in [r.id for r in runners]
    runner = check(client.get_runner(
        open_event.id, open_market.id, open_runner.id, include_prices=True))
    assert runner.id == open_runner.id

    book = check(client.get_prices(open_event.id, open_market.id, open_runner.id, depth=5))
    backs = [p.odds for p in book.available_to_back()]
    lays = [p.odds for p in book.available_to_lay()]
    assert backs == sorted(backs, reverse=True)
    assert lays == sorted(lays)


def test_popular_markets(client: MatchbookClient):
    """
    Popular markets come with their events, flat or nested.
    """
    flat = check(client.get_popular_markets())
    assert flat.markets and flat.events
    nested = check(client.get_popular_markets(old_format=True))
    assert any(e.markets for e in nested.events)
