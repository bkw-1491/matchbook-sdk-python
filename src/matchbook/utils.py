import dataclasses
import inspect
import re
import types
import typing
from collections.abc import Callable, Iterator, Mapping, Sequence
from datetime import datetime, timezone
from functools import cache
from typing import Any, Literal, TypeVar, Union

from matchbook.exceptions import MatchbookDecodeError, MatchbookInvalidRequestError

T = TypeVar("T")
Item = TypeVar("Item")

CAMEL_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")
ISO_DATETIME = re.compile(
    r"(?P<base>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?)"
    r"(?:\.(?P<frac>\d+))?"
    r"(?P<tz>Z|[+-]\d{2}:?\d{2})?$"
)
INTEGER = re.compile(r"-?\d+$")


@cache
def to_snake_case(key: str) -> str:
    """
    Convert an API key to its field name.

    Matchbook mostly uses kebab-case (``event-id`` -> ``event_id``), with the odd
    camelCase (``pnlOnWin`` -> ``pnl_on_win``) or snake_case key.

    :param key: JSON key.
    :returns: Field name.
    """
    return CAMEL_BOUNDARY.sub("_", key.lstrip("_")).replace("-", "_").lower()


def to_kebab_case(name: str) -> str:
    """
    Convert a field name to its API key, e.g. ``keep_in_play`` -> ``keep-in-play``.

    :param name: Field name.
    :returns: JSON key.
    """
    return name.replace("_", "-")


def parse_datetime(value: str) -> datetime:
    """
    Parse an API timestamp into an aware datetime.

    Digits beyond microseconds are truncated; no offset means UTC.

    :param value: ISO 8601 string, e.g. ``"2017-02-16T19:49:32.771Z"``.
    :returns: The timestamp.
    :raises MatchbookDecodeError: If ``value`` is not an ISO 8601 date-time.
    """
    match = ISO_DATETIME.match(value)
    if not match:
        raise MatchbookDecodeError(f"not an ISO 8601 date-time: {value!r}")
    text = match["base"]
    if match["frac"]:
        text += "." + match["frac"][:6].ljust(6, "0")
    tz = match["tz"]
    if tz and tz != "Z":
        text += tz if ":" in tz else f"{tz[:3]}:{tz[3:]}"
    parsed = datetime.fromisoformat(text)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def format_datetime(value: datetime) -> str:
    """
    Format a datetime for a query filter.

    :param value: Aware datetime, or naive meaning UTC.
    :returns: UTC with milliseconds, e.g. ``"2017-01-01T12:00:00.000Z"``.
    """
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc)
    return value.strftime("%Y-%m-%dT%H:%M:%S.") + f"{value.microsecond // 1000:03d}Z"


def to_epoch(value: datetime) -> int:
    """
    Convert a datetime to whole Unix seconds, for filters that take epochs.

    :param value: Aware datetime, or naive meaning UTC.
    :returns: Seconds since 1970-01-01 UTC.
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return int(value.timestamp())


@cache
def get_fields(cls: type) -> dict[str, Any]:
    """
    Resolve a dataclass's init field types, cached per class.

    :param cls: Model class.
    :returns: Field name to resolved type.
    """
    hints = typing.get_type_hints(cls)
    return {f.name: hints[f.name] for f in dataclasses.fields(cls) if f.init}


def decode(tp: Any, value: Any) -> Any:
    """
    Convert decoded JSON into ``tp``.

    Models ignore keys they don't declare; a union of models picks the one whose
    fields cover most of the object's keys. Ids the API sends as numeric strings
    are converted to ``int`` where the model declares one.

    :param tp: A model, ``list[...]``, ``dict[str, ...]``, ``X | None``, ``datetime``,
        ``Literal`` alias or scalar.
    :param value: Decoded JSON value.
    :returns: The converted value; ``None`` stays ``None``.
    :raises MatchbookDecodeError: If ``value`` doesn't have the shape of ``tp``.
    """
    return None if value is None else decoder(tp)(value)


@cache
def decoder(tp: Any) -> Callable[[Any], Any]:
    """
    A function converting a non-null JSON value into ``tp``, worked out once per type:
    ``decode`` runs on every response, and big ones repeat the same models many times.
    """
    origin = typing.get_origin(tp)

    if origin in (Union, types.UnionType):
        options = [a for a in typing.get_args(tp) if a is not type(None)]
        models = [o for o in options if dataclasses.is_dataclass(o)]
        if len(options) == 1 or not models:
            return decoder(options[0])
        first = decoder(options[0])

        def union(value: Any) -> Any:
            if not isinstance(value, dict):
                return first(value)
            # Untagged unions: the model covering most of the object's keys wins;
            # ties go to the first.
            keys = {to_snake_case(k) for k in value}
            return decoder(max(models, key=lambda m: len(keys & set(get_fields(m)))))(value)
        return checked(tp, union)

    if origin is list:
        (item,) = typing.get_args(tp)
        each = decoder(item)
        return checked(tp, lambda value: [None if v is None else each(v) for v in value])

    if origin is dict:
        _, item = typing.get_args(tp)
        each = decoder(item)
        return checked(tp, lambda value: {k: None if v is None else each(v)
                                          for k, v in value.items()})

    if origin is Literal or tp is Any:
        return identity

    if dataclasses.is_dataclass(tp):
        return checked(tp, model_decoder(tp))

    if tp is datetime:
        return checked(tp, parse_datetime)

    if tp is float:
        return checked(tp, lambda value: float(value) if type(value) is int else value)

    if tp is int:
        return checked(tp, lambda value: int(value)
                       if isinstance(value, str) and INTEGER.match(value) else value)

    return identity


def model_decoder(tp: Any) -> Callable[[dict[str, Any]], Any]:
    """
    A model's decoder: each JSON key's field, and how to decode it, looked up once per key.
    """
    fields = get_fields(tp)
    keys: dict[str, tuple[str, Callable[[Any], Any], bool] | None] = {}
    has_raw = "raw" in fields

    def field(key: str) -> tuple[str, Callable[[Any], Any], bool] | None:
        name = to_snake_case(key)
        if name not in fields:
            return None
        return name, decoder(fields[name]), typing.get_origin(fields[name]) is list

    def model(value: dict[str, Any]) -> Any:
        kwargs: dict[str, Any] = {}
        for key, item in value.items():
            spec = keys[key] if key in keys else keys.setdefault(key, field(key))
            if spec is None:
                continue
            name, each, is_list = spec
            if item is None:
                # A list field the API sent as null keeps its empty-list default.
                if not is_list:
                    kwargs[name] = None
            else:
                kwargs[name] = item if each is identity else each(item)
        if has_raw and "raw" not in kwargs:
            kwargs["raw"] = value
        try:
            return tp(**kwargs)
        except TypeError as exc:  # a required field is missing
            raise MatchbookDecodeError(f"{tp.__name__}: {exc}") from exc
    return model


def checked(tp: Any, convert: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """
    ``convert``, raising ``MatchbookDecodeError`` for a value of the wrong shape.
    """
    def run(value: Any) -> Any:
        try:
            return convert(value)
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            # Wrong shapes (a string where a list belongs, say) surface here.
            raise MatchbookDecodeError(f"cannot decode {value!r:.100} as {tp}") from exc
    return run


def identity(value: Any) -> Any:
    return value


def encode(value: Any) -> Any:
    """
    Convert a model, or a structure of models, to JSON-ready data.

    ``None`` fields are omitted, so optional request fields are only sent when set.

    :param value: Model, list, dict, datetime or scalar.
    :returns: The JSON-ready equivalent, with kebab-case keys.
    """
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            to_kebab_case(f.name): encode(getattr(value, f.name))
            for f in dataclasses.fields(value)
            if f.init and f.name != "raw" and getattr(value, f.name) is not None
        }
    if isinstance(value, list):
        return [encode(v) for v in value]
    if isinstance(value, dict):
        return {k: encode(v) for k, v in value.items()}
    if isinstance(value, datetime):
        return format_datetime(value)
    return value


def format_query_params(params: Mapping[str, Any]) -> dict[str, Any]:
    """
    Encode query parameters the way the API expects.

    :param params: Raw parameters; ``None`` values are dropped, lists comma-joined,
        booleans lower-case and datetimes UTC ISO 8601.
    :returns: Parameters ready for ``requests``.
    """
    out: dict[str, Any] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, str):
            out[key] = value
        elif isinstance(value, bool):
            out[key] = "true" if value else "false"
        elif isinstance(value, datetime):
            out[key] = format_datetime(value)
        elif isinstance(value, Sequence):
            out[key] = ",".join(str(v) for v in value)
        else:
            out[key] = str(value)
    return out


def paginate(method: Callable[..., T], *args: Any, **kwargs: Any) -> Iterator[T]:
    """
    Call a paged endpoint repeatedly, yielding each page's response.

    Matchbook pages by ``offset`` and ``per_page``; each response says how many
    rows exist in ``total``. Stop early with ``itertools.islice`` or ``break``.

    :param method: A client method, e.g. ``client.get_events``.
    :param args: Positional arguments for ``method``.
    :param kwargs: Keyword arguments for ``method``; ``offset`` sets where to start
        and ``per_page`` the page size (the endpoint's default if omitted).
    :returns: An iterator of page responses, in order.
    :raises MatchbookInvalidRequestError: If ``method`` is not paged (on first iteration).
    """
    if "offset" not in inspect.signature(method).parameters:
        raise MatchbookInvalidRequestError(f"{getattr(method, '__name__', method)} is not paged")
    offset = kwargs.pop("offset", None) or 0
    while True:
        response: Any = method(*args, offset=offset, **kwargs)
        yield response
        total, per_page = response.total, response.per_page
        if total is None or not per_page:
            return
        offset += per_page
        if offset >= total:
            return


def batch(
    method: Callable[[Sequence[Item]], T],
    items: Sequence[Item],
    size: int,
) -> Iterator[T]:
    """
    Send ``items`` through a list-taking endpoint ``size`` at a time, yielding each response.

    Nothing is sent until the iterator is consumed, one call per step, so you
    can see what each batch did before the next goes, and ``break`` to stop.
    If a call raises, the batches before it have already been sent::

        for result in batch(client.submit_offers, offers, 10):
            placed += [o for o in result.offers if o.status != "failed"]

    :param method: A client method taking a list, e.g. ``client.submit_offers``.
    :param items: Everything to send, in order.
    :param size: Items per call, at least 1.
    :returns: An iterator of responses, one per batch, in order.
    :raises MatchbookInvalidRequestError: If ``size`` is below 1 (on first iteration).
    """
    if size < 1:
        raise MatchbookInvalidRequestError(f"size must be at least 1, not {size}")
    for start in range(0, len(items), size):
        yield method(items[start:start + size])
