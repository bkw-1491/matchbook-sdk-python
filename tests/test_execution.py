import pytest

from matchbook import MatchbookInvalidPriceError
from matchbook.execution import (
    MATCHBOOK_PRICES,
    MAX_PRICE,
    MIN_PRICE,
    add_ticks,
    round_down_to_nearest_price,
    round_up_to_nearest_price,
    subtract_ticks,
)


def test_ladder_shape():
    """
    The ladder has 350 sorted prices from 1.01 to 1000 in the expected increments.
    """
    assert len(MATCHBOOK_PRICES) == 350
    assert (MIN_PRICE, MAX_PRICE) == (1.01, 1000.0)
    assert list(MATCHBOOK_PRICES) == sorted(set(MATCHBOOK_PRICES))
    pairs = zip(MATCHBOOK_PRICES[:-1], MATCHBOOK_PRICES[1:], strict=True)
    increments = {round(b - a, 2) for a, b in pairs}
    assert increments == {0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0}


@pytest.mark.parametrize(("price", "below", "above"), [
    (1.995, 1.99, 2.0),
    (2.01, 2.0, 2.02),
    (3.33, 3.3, 3.35),
    (5.55, 5.5, 5.6),
    (7.1, 7.0, 7.2),
    (15.2, 15.0, 15.5),
    (33.0, 32.0, 34.0),
    (77.0, 75.0, 80.0),
    (123.0, 120.0, 130.0),
])
def test_rounding_between_ticks(price, below, above):
    """
    Prices between ticks round to the ticks either side.
    """
    assert round_down_to_nearest_price(price) == below
    assert round_up_to_nearest_price(price) == above


def test_rounding_on_a_tick_is_a_no_op():
    """
    Every ladder price rounds to itself.
    """
    for price in MATCHBOOK_PRICES:
        assert round_down_to_nearest_price(price) == price
        assert round_up_to_nearest_price(price) == price


def test_float_noise_is_tolerated():
    """
    Float noise doesn't push a price onto the wrong tick.
    """
    assert round_down_to_nearest_price(1.1000000000000003) == 1.1
    assert round_up_to_nearest_price(1.0999999999999999) == 1.1
    assert round_down_to_nearest_price(0.1 + 0.2 + 2.7) == 3.0
    assert add_ticks(1.1000000000000003, 1) == 1.11


def test_rounding_at_the_ends():
    """
    Rounding clamps inside the ladder and raises when no tick exists.
    """
    assert round_up_to_nearest_price(1.0) == MIN_PRICE
    assert round_down_to_nearest_price(5000.0) == MAX_PRICE
    with pytest.raises(MatchbookInvalidPriceError):
        round_down_to_nearest_price(1.0)
    with pytest.raises(MatchbookInvalidPriceError):
        round_up_to_nearest_price(1000.5)


@pytest.mark.parametrize(("price", "ticks", "expected"), [
    (1.01, 1, 1.02),
    (1.99, 1, 2.0),
    (2.0, 1, 2.02),
    (1.98, 3, 2.02),
    (2.0, -1, 1.99),
    (3.95, 2, 4.1),
    (100.0, -1, 95.0),
    (1.01, 349, 1000.0),
    (5.0, 0, 5.0),
])
def test_add_ticks(price, ticks, expected):
    """
    Adding and subtracting ticks cross band boundaries correctly.
    """
    assert add_ticks(price, ticks) == expected
    assert subtract_ticks(expected, ticks) == price


def test_ticks_round_trip_across_the_whole_ladder():
    """
    Every ladder price is reachable by ticks from the bottom and back.
    """
    for i, price in enumerate(MATCHBOOK_PRICES):
        assert add_ticks(MIN_PRICE, i) == price
        assert subtract_ticks(price, i) == MIN_PRICE


def test_tick_errors():
    """
    Off-ladder prices and moves past either end raise MatchbookInvalidPriceError.
    """
    with pytest.raises(MatchbookInvalidPriceError):
        add_ticks(1.015, 1)  # not on the ladder
    with pytest.raises(MatchbookInvalidPriceError):
        add_ticks(1000.0, 1)
    with pytest.raises(MatchbookInvalidPriceError):
        subtract_ticks(1.01, 1)

