from matchbook.endpoints import Endpoints
from matchbook.heartbeat.resources import Heartbeat


class HeartbeatEndpoints(Endpoints):
    """
    The account's dead-man's switch.
    """

    def get_heartbeat(self) -> Heartbeat:
        """
        Fetch the heartbeat's state: ``GET /edge/rest/v1/heartbeat``.

        :returns: The active heartbeat.
        :raises MatchbookAPIError: 404 if no heartbeat is active.
        """
        return self.conn.call(Heartbeat, "GET", "/edge/rest/v1/heartbeat")

    def send_heartbeat(self, timeout: int) -> Heartbeat:
        """
        Arm or refresh the dead-man's switch: ``POST /edge/rest/v1/heartbeat``.

        If no heartbeat arrives within the timeout, Matchbook cancels the account's
        open offers (``cancellation_reason="heartbeat_expiry"``).

        :param timeout: Window in seconds; the server may apply a different one.
        :returns: The heartbeat, with the ``actual_timeout`` applied.
        """
        return self.conn.call(
            Heartbeat, "POST", "/edge/rest/v1/heartbeat", json={"timeout": timeout})

    def delete_heartbeat(self) -> Heartbeat:
        """
        Disarm the dead-man's switch: ``DELETE /edge/rest/v1/heartbeat``.

        :returns: ``action_performed == "HEARTBEAT_TERMINATED"``.
        """
        return self.conn.call(Heartbeat, "DELETE", "/edge/rest/v1/heartbeat")
