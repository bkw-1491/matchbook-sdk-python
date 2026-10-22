from matchbook.account.resources import (
    Account,
    AccountSportsResponse,
    Balance,
    CountriesResponse,
    RegionsResponse,
    Session,
)
from matchbook.endpoints import Endpoints
from matchbook.exceptions import MatchbookInvalidRequestError


class AccountEndpoints(Endpoints):
    """
    Sessions, the account, its balance and registration lookups.
    """

    def login(
        self,
        username: str | None = None,
        password: str | None = None,
        *,
        mfa_code: str | None = None,
    ) -> Session:
        """
        Log in: ``POST /bpapi/rest/security/session``.

        Stores the session token on the connection. Sessions last about six hours;
        Matchbook asks that the same session is reused for that long.

        :param username: Defaults to the connection's ``username``.
        :param password: Defaults to the connection's ``password``.
        :param mfa_code: One-time code, if the account has multi-factor auth on.
        :returns: The new session, with an account summary.
        :raises MatchbookInvalidRequestError: If no username or password is available.
        :raises MatchbookAPIError: 400 with code ``LOGIN_MFA_REQUIRED`` if a code is needed.
        """
        body = {
            "username": username or self.conn.username,
            "password": password or self.conn.password,
        }
        if not body["username"] or not body["password"]:
            raise MatchbookInvalidRequestError("username and password are required to log in")
        if mfa_code:
            body["mfa-code"] = mfa_code
        result = self.conn.call(Session, "POST", "/bpapi/rest/security/session", json=body)
        self.conn.session_token = result.session_token
        return result

    def logout(self) -> Session:
        """
        End the session: ``DELETE /bpapi/rest/security/session``.

        Clears the session token from the connection.

        :returns: The session that was ended.
        """
        result = self.conn.call(Session, "DELETE", "/bpapi/rest/security/session")
        self.conn.session_token = None
        return result

    def get_session(self) -> Session:
        """
        Check the session is still live: ``GET /bpapi/rest/security/session``.

        :returns: The current session.
        :raises MatchbookAPIError: 401 if the session has expired.
        """
        return self.conn.call(Session, "GET", "/bpapi/rest/security/session")

    def get_account(self) -> Account:
        """
        Fetch the logged-in account: ``GET /edge/rest/account``.

        :returns: The account's details, preferences and funds.
        """
        return self.conn.call(Account, "GET", "/edge/rest/account")

    def get_balance(self) -> Balance:
        """
        Fetch the logged-in account's funds: ``GET /edge/rest/account/balance``.

        :returns: Balance, exposure and free funds.
        """
        return self.conn.call(Balance, "GET", "/edge/rest/account/balance")

    def get_account_sports(self) -> AccountSportsResponse:
        """
        Fetch the sports the account has placed offers on: ``GET /edge/rest/account/sports``.

        :returns: Those sports.
        """
        return self.conn.call(AccountSportsResponse, "GET", "/edge/rest/account/sports")

    def get_countries(self) -> CountriesResponse:
        """
        Fetch the countries used for registration: ``GET /bpapi/rest/lookups/countries``.

        :returns: Every country.
        """
        return self.conn.call(CountriesResponse, "GET", "/bpapi/rest/lookups/countries")

    def get_regions(self, country_id: int) -> RegionsResponse:
        """
        Fetch a country's regions: ``GET /bpapi/rest/lookups/regions/{country_id}``.

        :param country_id: Country id, from ``get_countries``.
        :returns: The country's regions.
        """
        return self.conn.call(
            RegionsResponse, "GET", "/bpapi/rest/lookups/regions/{country_id}",
            path_params={"country_id": country_id})
