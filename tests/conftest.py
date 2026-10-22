import dataclasses
import os
import types
import typing
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from dotenv import load_dotenv

from matchbook import MatchbookClient, MatchbookError
from matchbook.markets import Event, Market, Runner
from matchbook.resources import BaseModel
from matchbook.utils import get_fields, parse_datetime, to_snake_case

load_dotenv(Path(__file__).parents[1] / ".env")


M = typing.TypeVar("M", bound=BaseModel)
NOW = datetime.now(timezone.utc)
WEEK_AGO = NOW - timedelta(days=7)
CREDENTIALS = ("MATCHBOOK_USERNAME", "MATCHBOOK_PASSWORD")

# Matchbook has no sandbox: tests that place offers only run when this is "1".
ALLOW_BETTING = os.environ.get("MATCHBOOK_ALLOW_BETTING") == "1"


@pytest.fixture(scope="session")
def client() -> typing.Iterator[MatchbookClient]:
    """
    A logged-in client; skips when credentials are missing. Logs out at the end.
    """
    missing = [name for name in CREDENTIALS if not os.environ.get(name)]
    if missing:
        pytest.skip(f"credentials not set: {', '.join(missing)}")
    live = MatchbookClient(*(os.environ[name] for name in CREDENTIALS))
    live.login()
    yield live
    live.logout()


@pytest.fixture(scope="session")
def open_event(client: MatchbookClient) -> Event:
    """
    An open soccer event starting at least two hours from now, with priced markets.
    """
    page = client.get_events(
        sport_ids=[15], states=["open"], after=NOW + timedelta(hours=2),
        include_prices=True, per_page=20)
    for event in page.events:
        if any(r.prices for m in event.markets for r in m.runners):
            return event
    pytest.skip("no open event to read")


@pytest.fixture(scope="session")
def open_market(open_event: Event) -> Market:
    """
    An open market on ``open_event`` with runners.
    """
    for market in open_event.markets:
        if market.status == "open" and market.runners:
            return market
    pytest.skip("no open market on the event")


@pytest.fixture(scope="session")
def open_runner(open_market: Market) -> Runner:
    """
    An open runner on ``open_market``.
    """
    for runner in open_market.runners:
        if runner.status == "open":
            return runner
    pytest.skip("no open runner on the market")


def schema_errors(tp: typing.Any, value: typing.Any, path: str = "$") -> list[str]:
    """
    Ways a decoded JSON ``value`` doesn't match type ``tp``: keys the model doesn't
    declare, required fields missing or null, wrong types, unparseable timestamps
    and enum values outside the declared set.
    """
    args = [a for a in typing.get_args(tp) if a is not type(None)]
    origin = typing.get_origin(tp)
    optional = origin in (typing.Union, types.UnionType) and len(args) < len(typing.get_args(tp))
    if value is None:
        return [] if optional or tp is typing.Any else [f"{path}: null for non-optional {tp}"]
    if origin in (typing.Union, types.UnionType):
        models = [a for a in args if dataclasses.is_dataclass(a)]
        if models and isinstance(value, dict):
            keys = {to_snake_case(k) for k in value}
            best = max(models, key=lambda m: len(keys & set(get_fields(m))))
            return schema_errors(best, value, path)
        return schema_errors(args[0], value, path) if len(args) == 1 else []
    if origin is typing.Literal:
        return [] if value in typing.get_args(tp) else [f"{path}: {value!r} not in {tp}"]
    if origin is list:
        if not isinstance(value, list):
            return [f"{path}: expected a list, got {type(value).__name__}"]
        return [p for i, v in enumerate(value) for p in schema_errors(args[0], v, f"{path}[{i}]")]
    if origin is dict:
        if not isinstance(value, dict):
            return [f"{path}: expected an object, got {type(value).__name__}"]
        return [p for k, v in value.items() for p in schema_errors(args[1], v, f"{path}.{k}")]
    if dataclasses.is_dataclass(tp):
        model: typing.Any = tp
        if not isinstance(value, dict):
            return [f"{path}: expected an object, got {type(value).__name__}"]
        model_fields = get_fields(tp)
        given = {to_snake_case(k): (k, v) for k, v in value.items()}
        found = [f"{path}.{k}: not declared by {model.__name__}"
                 for name, (k, _) in given.items() if name not in model_fields]
        for field in dataclasses.fields(tp):
            if not field.init or field.name == "raw":
                continue
            required = (field.default is dataclasses.MISSING
                        and field.default_factory is dataclasses.MISSING)
            if field.name not in given:
                if required:
                    found.append(f"{path}: {model.__name__}.{field.name} missing")
                continue
            key, sub = given[field.name]
            found += schema_errors(model_fields[field.name], sub, f"{path}.{key}")
        return found
    if tp is datetime:
        try:
            parse_datetime(value)
        except MatchbookError:
            return [f"{path}: {value!r} is not a timestamp"]
        return []
    if tp is float:
        ok = isinstance(value, (int, float)) and not isinstance(value, bool)
        return [] if ok else [f"{path}: expected a number, got {value!r}"]
    if tp is int:
        ok = (isinstance(value, int) and not isinstance(value, bool)) or (
            isinstance(value, str) and value.lstrip("-").isdigit())
        return [] if ok else [f"{path}: expected int, got {value!r}"]
    if tp in (str, bool):
        return [] if isinstance(value, tp) else [f"{path}: expected {tp.__name__}, got {value!r}"]
    return []


def check(result: M) -> M:
    """
    Assert a live response matches its model exactly, and return it.
    """
    raw = getattr(result, "raw", None)
    found = schema_errors(type(result), raw)
    assert not found, f"{type(result).__name__} doesn't match the API:\n" + "\n".join(found[:20])
    return result
