class ZmqError(Exception):
    pass


class InvalidMessageError(ZmqError, ValueError):
    pass


class InvalidAddressError(ZmqError, ValueError):
    pass


class InvalidRoutingIdError(ZmqError, ValueError):
    pass


class SocketClosedError(ZmqError):
    pass


class ConcurrentReceiveError(ZmqError):
    """Raised when a receive is attempted while another is outstanding on the same socket."""


class ZmqTimeoutError(ZmqError, TimeoutError):
    pass


class UnroutableError(ZmqError):
    """Raised by a router send to a route with no current peer."""


class WouldBlockError(ZmqError):
    """Raised by a router send to a known route with no local capacity."""


class AddressInUseError(ZmqError):
    pass


class TransportError(ZmqError):
    """A transport or native failure, carrying the original exception as its cause."""


class BackendUnavailableError(ZmqError):
    pass
