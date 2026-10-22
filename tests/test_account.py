import os
from datetime import datetime, timezone

import pytest
from conftest import CREDENTIALS, check

from matchbook import MatchbookAPIError, MatchbookClient


def test_login_authenticates_later_calls(client: MatchbookClient):
    """
    Logging in stores the token, turning a 401 into a successful call; logging
    out clears it and ends the session.
    """
    fresh = MatchbookClient(*(os.environ[name] for name in CREDENTIALS))
    with pytest.raises(MatchbookAPIError) as error:
        fresh.get_balance()
    assert error.value.status_code == 401

    session = check(fresh.login())
    assert fresh.conn.session_token == session.session_token
    assert session.account and session.account.username
    assert check(fresh.get_session()).session_token == session.session_token
    assert fresh.get_balance().id

    check(fresh.logout())
    assert fresh.conn.session_token is None
    fresh.conn.session_token = session.session_token
    with pytest.raises(MatchbookAPIError) as error:
        fresh.get_session()
    assert error.value.status_code == 401


def test_get_account_and_balance(client: MatchbookClient):
    """
    The account and its funds can be read, and agree.
    """
    account = check(client.get_account())
    balance = check(client.get_balance())
    assert account.id == balance.id
    assert balance.free_funds <= balance.balance + 1e-9


def test_get_account_sports(client: MatchbookClient):
    """
    The sports the account has bet on can be read.
    """
    check(client.get_account_sports())


def test_countries_and_regions(client: MatchbookClient):
    """
    Countries can be listed, and a country's regions fetched by its id.
    """
    countries = check(client.get_countries()).countries
    ireland = next(c for c in countries if c.country_code == "IE")
    assert check(client.get_regions(ireland.country_id)).regions


def test_responses_and_errors_are_timed(client: MatchbookClient):
    """
    Responses and API errors carry when the request was sent, when the answer
    arrived and the round trip.
    """
    before = datetime.now(timezone.utc)
    result = client.get_balance()
    assert before <= result.sent_at <= result.received_at <= datetime.now(timezone.utc)
    assert 0 < result.latency_ms < 30_000

    with pytest.raises(MatchbookAPIError) as error:
        client.get_offer(1)
    failed = error.value
    assert result.received_at <= failed.sent_at <= failed.received_at
    assert 0 < failed.latency_ms < 30_000
