class ZmtpError(Exception):
    pass


class ZmtpProtocolError(ZmtpError):
    """A violation of the wire protocol or of configured bounds. Fatal to the connection."""


class ZmtpLimitError(ZmtpProtocolError):
    pass


class ZmtpTruncatedError(ZmtpProtocolError):
    """The connection ended inside a greeting, frame, or multipart message."""


class ZmtpHandshakeError(ZmtpProtocolError):
    """The peer is incompatible, or its handshake is malformed or out of order."""


class ZmtpHandshakeTimeoutError(ZmtpHandshakeError):
    pass


class ZmtpPeerError(ZmtpError):
    """The peer sent an ERROR command."""

    def __init__(self, reason: bytes) -> None:
        super().__init__(reason)

        self.reason = reason
