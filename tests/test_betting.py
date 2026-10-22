import os

import pytest
from conftest import ALLOW_BETTING, check

from matchbook import MatchbookAPIError, MatchbookClient
from matchbook.execution import MAX_PRICE, subtract_ticks
from matchbook.markets import Runner


def test_get_offers(client: MatchbookClient):
    """
    Offers can be listed, with their edits.
    """
    check(client.get_offers(include_edits=True, per_page=10))


def test_get_offer_unknown(client: MatchbookClient):
    """
    An unknown offer id is an API error, not a decode failure.
    """
    with pytest.raises(MatchbookAPIError) as error:
        client.get_offer(1)
    assert 400 <= error.value.status_code < 500


def test_aggregated_matched_bets(client: MatchbookClient):
    """
    Matched bets can be read aggregated either way.
    """
    check(client.get_aggregated_matched_bets())
    check(client.get_aggregated_matched_bets(aggregation_type="summary"))


def test_cancelled_matched_bets(client: MatchbookClient):
    """
    Cancelled matched bets can be read.
    """
    check(client.get_cancelled_matched_bets())


def test_positions(client: MatchbookClient):
    """
    Positions can be read.
    """
    check(client.get_positions())


@pytest.mark.skipif(not ALLOW_BETTING, reason="set MATCHBOOK_ALLOW_BETTING=1 to place offers")
def test_offer_lifecycle(client: MatchbookClient, open_runner: Runner):
    """
    An offer can be submitted, read, edited and cancelled.

    Backs at the top of the ladder so it rests unmatched; at worst it costs the stake.
    """
    stake = float(os.environ.get("MATCHBOOK_TEST_STAKE", "1"))
    placed = check(client.submit_offer(
        open_runner.id, "back", MAX_PRICE, stake, odds_type="DECIMAL")).offers[0]
    offer_id = placed.id
    assert offer_id is not None, placed.errors
    try:
        assert placed.status == "open"
        assert placed.runner_id == open_runner.id and placed.stake_matched == 0

        assert check(client.get_offer(offer_id)).id == offer_id
        listed = check(client.get_offers(runner_ids=[open_runner.id], statuses=["open"]))
        assert offer_id in [o.id for o in listed.offers]

        new_odds = subtract_ticks(MAX_PRICE, 1)
        edited = check(client.edit_offer(
            offer_id, new_odds=new_odds, current_odds=MAX_PRICE, current_stake=stake))
        assert edited.offer_edit and edited.offer_edit.status == "applied"
        assert edited.decimal_odds == new_odds

        edits = check(client.get_offer_edits(offer_id)).offer_edits
        assert edits and edits[0].offer_id == offer_id and edits[0].id is not None
        check(client.get_offer_edit(offer_id, edits[0].id))
    finally:
        cancelled = check(client.cancel_offer(offer_id))
    assert cancelled.status == "cancelled"


@pytest.mark.skipif(not ALLOW_BETTING, reason="set MATCHBOOK_ALLOW_BETTING=1 to place offers")
def test_cancel_offers_by_runner(client: MatchbookClient, open_runner: Runner):
    """
    Cancelling by runner cancels only that runner's offers.
    """
    stake = float(os.environ.get("MATCHBOOK_TEST_STAKE", "1"))
    placed = client.submit_offer(open_runner.id, "back", MAX_PRICE, stake).offers[0]
    offer_id = placed.id
    assert offer_id is not None, placed.errors
    try:
        result = check(client.cancel_offers(runner_ids=[open_runner.id]))
    except MatchbookAPIError:
        client.cancel_offer(offer_id)
        raise
    assert offer_id in [o.id for o in result.offers]
    assert {o.runner_id for o in result.offers} == {open_runner.id}
