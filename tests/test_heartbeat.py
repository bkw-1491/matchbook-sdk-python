import pytest
from conftest import check

from matchbook import MatchbookAPIError, MatchbookClient


def test_heartbeat_lifecycle(client: MatchbookClient):
    """
    The heartbeat can be armed, read, refreshed and disarmed.
    """
    try:
        armed = check(client.send_heartbeat(60))
        assert armed.action_performed == "HEARTBEAT_ACTIVATED"
        assert armed.actual_timeout and armed.timeout_time

        assert check(client.get_heartbeat()).action_performed == "HEARTBEAT_ACTIVATED"

        refreshed = check(client.send_heartbeat(60))
        assert refreshed.timeout_time and refreshed.timeout_time >= armed.timeout_time
    finally:
        removed = check(client.delete_heartbeat())

    assert removed.action_performed == "HEARTBEAT_TERMINATED"
    with pytest.raises(MatchbookAPIError) as error:
        client.get_heartbeat()
    assert error.value.status_code == 404
