from dataclasses import dataclass
from datetime import datetime

from matchbook.resources import Response


@dataclass(kw_only=True, slots=True)
class Heartbeat(Response):
    """
    The account's dead-man's switch.

    :param action_performed: ``"HEARTBEAT_ACTIVATED"`` or ``"HEARTBEAT_TERMINATED"``.
    :param actual_timeout: Seconds the server applied, which may differ from the
        one asked for; pace later heartbeats by it.
    :param timeout_time: When open offers are cancelled unless another heartbeat arrives.
    """
    action_performed: str
    actual_timeout: int | None = None
    timeout_time: datetime | None = None
