import json
from datetime import datetime, timezone
from typing import Any

import pytest
import requests

from matchbook import (
    MatchbookAPIError,
    MatchbookClient,
    MatchbookConfigurationError,
    MatchbookInvalidRequestError,
    OfferRequest,
)
from matchbook.utils import batch, paginate


class FakeSession(requests.Session):
    """
    Answers each request with the next queued ``(status, body)`` and records what was sent.
    """

    def __init__(self, *replies: tuple[int, Any]) -> None:
        super().__init__()
        self.replies = list(replies)
        self.sent: list[dict[str, Any]] = []

    def request(self, method, url, params=None, json=None, headers=None, **kwargs):  # type: ignore[override]
        self.sent.append(
            {"method": method, "url": url, "params": params, "json": json, "headers": headers})
        status, body = self.replies.pop(0)
        response = requests.Response()
        response.status_code = status
        response._content = b"" if body is None else _dumps(body)
        response.reason = "Bad Request" if status == 400 else "OK"
        return response


def _dumps(body: Any) -> bytes:
    return json.dumps(body).encode()


def client_with(*replies: tuple[int, Any]) -> tuple[MatchbookClient, FakeSession]:
    session = FakeSession(*replies)
    return MatchbookClient("user", "pass", session=session), session


def test_login_stores_and_sends_the_session_token():
    """
    Login posts the credentials; later calls carry the token as a header; logout clears it.
    """
    client, http = client_with(
        (200, {"session-token": "abc", "user-id": 1, "account": {"id": 2, "username": "u"}}),
        (200, {"id": 2, "balance": 10, "exposure": 0, "commission-reserve": 0, "free-funds": 10}),
        (200, {"session-token": "abc", "user-id": 1, "username": "u"}),
    )
    session = client.login(mfa_code="123")
    assert session.session_token == "abc" and session.account and session.account.id == 2
    assert http.sent[0]["url"] == "https://api.matchbook.com/bpapi/rest/security/session"
    assert http.sent[0]["json"] == {"username": "user", "password": "pass", "mfa-code": "123"}

    balance = client.get_balance()
    assert balance.free_funds == 10.0 and isinstance(balance.free_funds, float)
    assert http.sent[1]["headers"]["session-token"] == "abc"

    client.logout()
    assert client.conn.session_token is None


def test_query_params_are_encoded_the_matchbook_way():
    """
    Lists are comma-joined, booleans lower-case, event windows in epoch seconds
    and report windows in ISO 8601.
    """
    client, http = client_with((200, {"events": []}), (200, {"transactions": []}))
    after = datetime(2026, 1, 1, tzinfo=timezone.utc)
    client.get_events(sport_ids=[15, 9], include_prices=True, after=after, per_page=5)
    assert http.sent[0]["params"] == {
        "sport-ids": "15,9", "include-prices": "true", "after": "1767225600", "per-page": "5"}

    client.get_transactions(transaction_types=["payout"], after=after)
    assert http.sent[1]["params"] == {
        "transaction-type": "payout", "after": "2026-01-01T00:00:00.000Z"}


def test_submit_offers_sends_kebab_case_and_decodes_each_offer():
    """
    Offer requests are sent with kebab-case keys; string ids in the reply decode to ints.
    """
    client, http = client_with((200, {"offers": [
        {"id": "11", "runner-id": 5, "status": "open", "stake": 2, "remaining": 2},
        {"status": "failed", "errors": [{"field": "odds", "messages": ["bad odds"]}]},
    ]}))
    result = client.submit_offers(
        [OfferRequest(runner_id=5, side="back", odds=2.0, stake=2, keep_in_play=True)],
        odds_type="DECIMAL")
    assert http.sent[0]["json"] == {
        "odds-type": "DECIMAL",
        "offers": [
            {"runner-id": 5, "side": "back", "odds": 2.0, "stake": 2, "keep-in-play": True}],
    }
    placed, failed = result.offers
    assert placed.id == 11 and placed.stake_matched == 0
    assert failed.errors[0].field == "odds" and failed.errors[0].messages == ["bad odds"]


def test_edit_offer_puts_to_the_offer_path():
    """
    A single edit goes to the offer's own path, without its id in the body.
    """
    client, http = client_with((200, {"id": 7, "status": "edited", "offer-edit": {
        "id": 8, "offer-id": 7, "status": "applied", "edit-time": "2018-10-02T10:14:38.315Z"}}))
    offer = client.edit_offer(7, new_odds=3.0)
    assert http.sent[0]["method"] == "PUT"
    assert http.sent[0]["url"].endswith("/edge/rest/v2/offers/7")
    assert http.sent[0]["json"] == {"new-odds": 3.0}
    assert offer.offer_edit and offer.offer_edit.status == "applied"
    with pytest.raises(MatchbookInvalidRequestError):
        client.edit_offer(7)


def test_api_errors_carry_matchbooks_messages_and_codes():
    """
    Error bodies are flattened into messages, codes and fields.
    """
    client, _ = client_with((400, {"errors": [{
        "field": "mfa-code",
        "messages": ["MFA code required."],
        "codes": ["LOGIN_MFA_REQUIRED"],
    }]}))
    with pytest.raises(MatchbookAPIError) as error:
        client.login()
    assert error.value.status_code == 400
    assert error.value.codes == ["LOGIN_MFA_REQUIRED"]
    assert error.value.fields == ["mfa-code"]
    assert str(error.value) == "400 MFA code required."


def test_paginate_walks_offsets_until_total():
    """
    Paging advances by the page size the API reports and stops at the total.
    """
    pages = [(200, {"offset": o, "per-page": 2, "total": 5, "events": []}) for o in (0, 2, 4)]
    client, http = client_with(*pages)
    assert [p.offset for p in paginate(client.get_events, per_page=2)] == [0, 2, 4]
    assert [s["params"].get("offset") for s in http.sent] == ["0", "2", "4"]


def test_batch_chunks_items():
    """
    Items go out ``size`` at a time.
    """
    assert list(batch(len, list(range(7)), 3)) == [3, 3, 1]
    with pytest.raises(MatchbookInvalidRequestError):
        list(batch(len, [1], 0))


def test_unknown_environment_is_rejected():
    """
    Only ``prod`` exists unless a base URL is given.
    """
    with pytest.raises(MatchbookConfigurationError):
        MatchbookClient(environment="sandbox")
    assert MatchbookClient(base_url="http://localhost/").conn.base_url == "http://localhost"
