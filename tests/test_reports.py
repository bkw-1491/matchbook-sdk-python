from conftest import NOW, WEEK_AGO, check

from matchbook import MatchbookClient


def test_transactions(client: MatchbookClient):
    """
    Wallet transactions can be read for a window.
    """
    page = check(client.get_transactions(after=WEEK_AGO, before=NOW, per_page=10))
    assert all(WEEK_AGO <= t.time <= NOW for t in page.transactions)


def test_current_offers_and_bets(client: MatchbookClient):
    """
    The current offers and bets reports can be read.
    """
    check(client.get_current_offers())
    check(client.get_current_bets())


def test_settled_bets(client: MatchbookClient):
    """
    Settled bets can be read for a window.
    """
    page = check(client.get_settled_bets(after=WEEK_AGO, before=NOW))
    assert all(m.settled_time is None or m.settled_time >= WEEK_AGO for m in page.markets)
