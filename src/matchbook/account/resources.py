from dataclasses import dataclass, field
from datetime import datetime

from matchbook.markets.resources import Sport
from matchbook.resources import BaseModel, Response


@dataclass(kw_only=True, slots=True)
class Name(BaseModel):
    """
    An account holder's name.
    """
    first: str | None = None
    last: str | None = None


@dataclass(kw_only=True, slots=True)
class Country(BaseModel):
    """
    A country, as used for account registration.
    """
    country_id: int
    name: str
    country_code: str | None = None


@dataclass(kw_only=True, slots=True)
class Region(BaseModel):
    """
    A region within a country, as used for account registration.
    """
    region_id: int
    name: str


@dataclass(kw_only=True, slots=True)
class Address(BaseModel):
    """
    An account holder's address.
    """
    address_id: int | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    address_line_3: str | None = None
    city: str | None = None
    region_name: str | None = None
    post_code: str | None = None
    country: Country | None = None


@dataclass(kw_only=True, slots=True)
class SessionAccount(BaseModel):
    """
    The account summary returned on login.
    """
    id: int
    username: str
    name: Name | None = None
    email: str | None = None
    phone_number: str | None = None
    address: Address | None = None
    date_of_birth: datetime | None = None
    currency: str | None = None
    balance: float | None = None
    exposure: float | None = None
    commission_credit: float | None = None
    free_funds: float | None = None
    language: str | None = None
    odds_type: str | None = None
    exchange_type: str | None = None
    bet_confirmation: bool | None = None
    display_p_and_l: bool | None = None
    odds_rounding: bool | None = None
    bet_slip_pinned: bool | None = None


@dataclass(kw_only=True, slots=True)
class Session(Response):
    """
    A Matchbook session; ``session_token`` authenticates later calls.

    Login fills in ``account`` and the MFA fields; ``get_session`` and ``logout``
    return only the token and user.
    """
    session_token: str
    user_id: int
    username: str | None = None
    role: str | None = None
    account: SessionAccount | None = None
    mfa_enabled: bool | None = None
    mfa_enabled_time: datetime | None = None
    mfa_disabled_time: datetime | None = None
    last_login: datetime | None = None


@dataclass(kw_only=True, slots=True)
class Account(Response):
    """
    The logged-in account's details, preferences and funds.
    """
    id: int
    username: str
    status: str | None = None
    commission_type: str | None = None
    currency: str | None = None
    country: str | None = None
    balance: float | None = None
    exposure: float | None = None
    commission_reserve: float | None = None
    free_funds: float | None = None
    language: str | None = None
    exchange_type: str | None = None
    odds_type: str | None = None
    show_bet_confirmation: bool | None = None
    show_position: bool | None = None
    show_odds_rounding_message: bool | None = None
    bet_slip_pinned: bool | None = None
    roles: list[str] = field(default_factory=list)


@dataclass(kw_only=True, slots=True)
class Balance(Response):
    """
    The logged-in account's funds.

    :param exposure: Funds at risk on open offers and bets.
    :param free_funds: Funds available to bet with.
    """
    id: int
    balance: float
    exposure: float
    commission_reserve: float
    free_funds: float


@dataclass(kw_only=True, slots=True)
class AccountSportsResponse(Response):
    """
    The sports the account has placed offers on.

    The docs give no example of this response; check ``raw`` if ``sports`` is empty.
    """
    sports: list[Sport] = field(default_factory=list)


@dataclass(kw_only=True, slots=True)
class CountriesResponse(Response):
    """
    Every country.
    """
    countries: list[Country] = field(default_factory=list)


@dataclass(kw_only=True, slots=True)
class RegionsResponse(Response):
    """
    A country's regions.
    """
    regions: list[Region] = field(default_factory=list)
