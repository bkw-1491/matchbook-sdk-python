import requests

from matchbook.account import AccountEndpoints
from matchbook.betting import BettingEndpoints
from matchbook.connection import MatchbookConnection
from matchbook.heartbeat import HeartbeatEndpoints
from matchbook.markets import MarketsEndpoints
from matchbook.reports import ReportsEndpoints


class MatchbookClient(
    AccountEndpoints,
    MarketsEndpoints,
    BettingEndpoints,
    ReportsEndpoints,
    HeartbeatEndpoints,
):
    """
    Top-level client for matchbook.
    """

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        *,
        environment: str = "prod",
        base_url: str | None = None,
        session: requests.Session | None = None,
        timeout: float | None = 30.0,
    ) -> None:
        """
        Create the client and its connection; see ``MatchbookConnection`` for parameters.
        """
        super().__init__(MatchbookConnection(
            username,
            password,
            environment=environment,
            base_url=base_url,
            session=session,
            timeout=timeout,
        ))
