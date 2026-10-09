class PeerRejectedError(Exception):
    """An endpoint refused a ready connection: duplicate identity, too many peers, or a closed endpoint."""


class PeerViolationError(Exception):
    """A peer sent traffic its role forbids or exceeded a bound. Fatal to its connection, not to the endpoint."""
