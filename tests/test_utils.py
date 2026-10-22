from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import pytest

from matchbook.exceptions import MatchbookDecodeError
from matchbook.markets.resources import Price, Runner
from matchbook.resources import BaseModel
from matchbook.utils import decode


@dataclass(kw_only=True, slots=True)
class Inner(BaseModel):
    seen_at: datetime
    price: float = 0.0


@dataclass(kw_only=True, slots=True)
class Outer(BaseModel):
    name: str
    inners: list[Inner] = field(default_factory=list)
    by_id: dict[str, Inner] = field(default_factory=dict)
    inner: Inner | None = None
    extra: Any = None


PRICE = {"available-amount": 10, "odds": 2, "side": "back", "decimal-odds": 2.0}


def test_decodes_nested_models_from_kebab_and_camel_case_ignoring_unknown_keys():
    outer = decode(Outer, {"name": "a", "unknown-key": 1, "extra": {"x": [1]},
                           "inners": [{"seen-at": "2026-10-22T13:41:15Z", "price": 2}, None],
                           "byId": {"k": {"seenAt": "2026-10-22T13:41:15.5+0100"}},
                           "inner": None})
    assert outer.inners[0] == Inner(seen_at=datetime(2026, 10, 22, 13, 41, 15,
                                                     tzinfo=timezone.utc), price=2.0)
    assert type(outer.inners[0].price) is float and outer.inners[1] is None
    assert outer.by_id["k"].seen_at.utcoffset().total_seconds() == 3600
    assert (outer.inner, outer.extra) == (None, {"x": [1]})


def test_a_list_sent_as_null_keeps_its_default():
    assert decode(Outer, {"name": "a", "inners": None}).inners == []


def test_ints_become_floats_but_bools_stay():
    assert decode(float, 2) == 2.0 and type(decode(float, 2)) is float
    assert decode(float, True) is True
    assert type(decode(Price, PRICE).available_amount) is float


def test_numeric_string_ids_become_ints_and_other_strings_stay():
    runner = decode(Runner, {"id": "123", "name": "Home", "event-id": "-4", "prices": [PRICE]})
    assert (runner.id, runner.event_id) == (123, -4)
    assert decode(int, "12a") == "12a" and decode(int, 7) == 7


@pytest.mark.parametrize("tp, value", [
    (Price, {"side": "back"}),  # required fields missing
    (Price, "not an object"),
    (list[int], 5),
    (Inner, {"seen-at": "yesterday"}),
])
def test_a_wrong_shape_is_a_decode_error(tp, value):
    with pytest.raises(MatchbookDecodeError):
        decode(tp, value)


def test_decoding_again_gives_the_same():
    assert decode(Runner, {"id": 1, "name": "a", "prices": [PRICE]}) == decode(
        Runner, {"id": 1, "name": "a", "prices": [dict(PRICE)]})
