# matchbook-sdk

A Python client for the [Matchbook Betting Exchange API](https://developers.matchbook.com) (REST).

- One typed method per endpoint on a single `MatchbookClient`
- Responses are dataclasses; each keeps its raw JSON (`.raw`) plus `sent_at`, `received_at` and `latency_ms`
- Endpoints are grouped as `account`, `markets`, `betting`, `reports` and `heartbeat`

```sh
pip install matchbook-sdk
```

```python
import matchbook
```

## Quick Start

```python
from matchbook import MatchbookClient

client = MatchbookClient(username, password)
client.login()                     # one session lasts ~6 hours; reuse it

events = client.get_events(sport_ids=[15], states=["open"], include_prices=True).events
market = events[0].markets[0]
runner = market.runners[0]

best_back = runner.available_to_back()[:1]
best_lay = runner.available_to_lay()[:1]
```

## Offers

```python
from matchbook import OfferRequest
from matchbook.utils import batch

offer = client.submit_offer(runner_id, "back", odds=2.5, stake=10,
                            keep_in_play=False, odds_type="DECIMAL").offers[0]
print(offer.status, offer.stake_matched, offer.remaining)

client.edit_offer(offer.id, new_odds=2.6)
client.cancel_offer(offer.id)

offers = [OfferRequest(runner_id=r, side="lay", odds=1.5, stake=5) for r in runner_ids]
for result in batch(client.submit_offers, offers, 10):    # 10 per call
    failed = [o for o in result.offers if o.status == "failed"]

client.cancel_offers(market_ids=[market_id])    # no filters cancels everything
```

- Each submitted offer succeeds or fails on its own; check `status` (and `errors` when `"failed"`)
- In play, an offer or edit that would match comes back `"delayed"` and resolves after the delay

## Paging

- Many endpoints are offset-paged (`offset`, `per_page`). A `paginate` utility is supplied:

```python
from matchbook.utils import paginate

for page in paginate(client.get_events, sport_ids=[15], per_page=100):
    ...
```

## Heartbeat

```python
client.send_heartbeat(60)      # cancel all open offers if nothing arrives for ~60s
client.delete_heartbeat()
```

## Errors

- All errors derive from `MatchbookError`:

```python
from matchbook import MatchbookAPIError, MatchbookTransportError

try:
    client.get_offer(123)
except MatchbookAPIError as exc:          # error status: status_code, messages, codes, body
    print(exc.status_code, exc.messages, exc.latency_ms)
except MatchbookTransportError as exc:    # no response
    print(exc, exc.latency_ms)
```

## Execution

```python
from matchbook.execution import add_ticks, round_down_to_nearest_price

round_down_to_nearest_price(5.55)    # 5.5
add_ticks(1.99, 2)                   # 2.02
```

## Tests

The live tests read `MATCHBOOK_USERNAME` and `MATCHBOOK_PASSWORD` from the
environment or `.env`, and skip without them. Matchbook has no sandbox, so the
tests that place offers also need `MATCHBOOK_ALLOW_BETTING=1`; they back at
1000.0 with `MATCHBOOK_TEST_STAKE` (default 1) and cancel straight away.
