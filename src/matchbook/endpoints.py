from matchbook.connection import MatchbookConnection


class Endpoints:
    """
    Base for the endpoint groups: holds the ``MatchbookConnection`` they send through.

    :param conn: Connection to send through.
    """

    def __init__(self, conn: MatchbookConnection) -> None:
        """
        Create the group; see the class docstring for parameters.
        """
        self.conn = conn
