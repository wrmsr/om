# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
The transport host service: how a handler, or application code, asks the runtime hosting a pipeline for more
transports - a connection to an endpoint, a listener, or the adoption of a transport it already holds - and gets back
a handle to the pipeline driven over it.

Everything a handler requests is owned by that handler's ref, as scheduled callbacks are: removing the handler, or
destroying its pipeline, closes what it owns, unless it has released or transferred the handle. Outcomes which arrive
later - connected, failed, accepted - are delivered into the owner's pipeline by posting, with the owner's context,
never by a callback run outside a pipeline; a request made without an owner gets its callbacks run on the host's
thread, outside any pipeline, with no context. One host and everything it hosts run on one thread, and nothing here is
thread-safe.
"""
import abc
import dataclasses as dc
import typing as ta

from ....lite.abstract import Abstract
from ....sockets.endpoints import SocketEndpoint
from ..core import IoPipeline
from ..core import IoPipelineHandlerContext
from ..core import IoPipelineHandlerRef
from ..core import IoPipelineService
from ..drivers.types import IoPipelineDriverState
from ..errors import IoPipelineError
from ..posting.types import IoPipelinePosting


T = ta.TypeVar('T')

IoPipelineHostCallback = ta.Callable[[ta.Optional[IoPipelineHandlerContext], T], None]  # ta.TypeAlias

IoPipelineHostSpecFactory = ta.Callable[['IoPipelineHostTransportInfo'], IoPipeline.Spec]  # ta.TypeAlias


##


class IoPipelineHostError(IoPipelineError):
    pass


class ClosedIoPipelineHostError(IoPipelineHostError):
    """The host, the request, or the owner it was made for is gone."""


class ConnectIoPipelineHostError(IoPipelineHostError):
    """No address of the endpoint could be connected to; `errors` holds each attempt's failure, in order."""

    def __init__(self, endpoint: ta.Any, errors: ta.Sequence[BaseException] = ()) -> None:
        super().__init__(endpoint, errors)

        self.endpoint = endpoint
        self.errors = errors


class ConnectTimeoutIoPipelineHostError(ConnectIoPipelineHostError, TimeoutError):
    pass


class ResolveIoPipelineHostError(ConnectIoPipelineHostError):
    """The endpoint's host name could not be resolved."""


class ListenIoPipelineHostError(IoPipelineHostError):
    pass


##


@dc.dataclass(frozen=True)
class IoPipelineHostTransportInfo:
    """What a hosted pipeline's spec factory, and its handle, know about the transport."""

    endpoint: ta.Optional[SocketEndpoint] = None

    local_address: ta.Any = None
    peer_address: ta.Any = None


##


class IoPipelineHostHandle(Abstract):
    """Something the host does on a requester's behalf: owned by a handler's ref, or by nobody but the host."""

    @property
    @abc.abstractmethod
    def owner(self) -> ta.Optional[IoPipelineHandlerRef]:
        """The owning handler's ref, or None if the handle is host-owned: closed only explicitly or with the host."""

        raise NotImplementedError

    @property
    @abc.abstractmethod
    def closed(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def close(self) -> None:
        """Abortive and idempotent."""

        raise NotImplementedError

    @abc.abstractmethod
    def release(self) -> None:
        """Makes the handle host-owned, so that its requester's removal no longer closes it."""

        raise NotImplementedError

    @abc.abstractmethod
    def transfer(self, owner: IoPipelineHandlerRef) -> None:
        """Makes another handler's ref the owner."""

        raise NotImplementedError


class IoPipelineHostedDriver(IoPipelineHostHandle, Abstract):
    """
    A pipeline driven over a hosted transport. The driver has started - its pipeline exists and has had `InitialInput`
    - at once on the in-memory and fdio hosts, and once its task has first run on asyncio; `on_connected` and
    `on_accepted` are delivered after that. Until then `pipeline` is None and `posting` unavailable.
    """

    @property
    @abc.abstractmethod
    def info(self) -> IoPipelineHostTransportInfo:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def state(self) -> IoPipelineDriverState:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def pipeline(self) -> ta.Optional[IoPipeline]:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def posting(self) -> IoPipelinePosting:
        """Raises StateIoPipelineError until the driver has started."""

        raise NotImplementedError


class IoPipelineHostedConnect(IoPipelineHostHandle, Abstract):
    """A connect in progress: closing it cancels the attempt, and its `on_failed` is told with a closed error."""


class IoPipelineHostedListener(IoPipelineHostHandle, Abstract):
    """
    A listener. Each accepted connection is a hosted driver of its own, with the listener's owner as its owner, and
    is reported through the listener's `on_accepted`; closing the listener does not close them.
    """

    @property
    @abc.abstractmethod
    def bound_endpoint(self) -> SocketEndpoint:
        raise NotImplementedError


##


class IoPipelineHost(IoPipelineService, Abstract):
    """
    The transport host service, looked up from `ctx.services` by this interface. A host is also an
    `IoPipelineService` which it installs into every pipeline it hosts, and which may be put into any other pipeline's
    spec - a multiplexed stream's, say - so that handlers there can use it too; it is through that service's view of
    handler removals that ownership is enforced.
    """

    @abc.abstractmethod
    def connect(
            self,
            endpoint: SocketEndpoint,
            spec_factory: IoPipelineHostSpecFactory,
            *,
            on_connected: IoPipelineHostCallback[IoPipelineHostedDriver],
            on_failed: IoPipelineHostCallback[IoPipelineHostError],
            timeout_s: ta.Optional[float] = None,
            owner: ta.Optional[IoPipelineHandlerRef] = None,
    ) -> IoPipelineHostedConnect:
        """
        Connects to the endpoint - resolving a host name as the host's resolver does, then trying each address in
        order under the timeout - and drives the connection with a pipeline built from the factory, which is given the
        connection's addresses. One of the callbacks is delivered later: `on_failed` with a
        `ConnectIoPipelineHostError` (a `ConnectTimeoutIoPipelineHostError` when the last attempt timed out), or with
        a `ClosedIoPipelineHostError` if the connect, or the host, was closed first.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def listen(
            self,
            endpoint: SocketEndpoint,
            spec_factory: IoPipelineHostSpecFactory,
            *,
            on_accepted: ta.Optional[IoPipelineHostCallback[IoPipelineHostedDriver]] = None,
            backlog: int = 128,
            unix_socket_mode: int = 0o600,
            owner: ta.Optional[IoPipelineHandlerRef] = None,
    ) -> IoPipelineHostedListener:
        """
        Listens on the endpoint - at once, raising ListenIoPipelineHostError - and drives each accepted connection with
        a pipeline built from the factory, which is given its addresses; the listener reports its bound endpoint, so
        port zero may be asked for. A factory raising refuses that connection, which is closed.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def adopt(
            self,
            transport: ta.Any,
            spec: IoPipeline.Spec,
            *,
            info: ta.Optional[IoPipelineHostTransportInfo] = None,
            owned: bool = False,
            owner: ta.Optional[IoPipelineHandlerRef] = None,
    ) -> IoPipelineHostedDriver:
        """
        Drives a transport the requester already holds: what a transport is depends on the host - a connected socket,
        a duplex descriptor, or a (read, write) descriptor pair for the descriptor hosts; a link end for the in-memory
        one. Unless `owned`, the transport stays the requester's: it is restored on release and never closed.
        """

        raise NotImplementedError

    @property
    @abc.abstractmethod
    def closed(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def close(self) -> None:
        """Closes everything hosted, listeners first, abortively."""

        raise NotImplementedError


##


IoPipelineHostResolveResult = ta.Sequence[ta.Tuple[int, int, int, ta.Any]]  # ta.TypeAlias  # family, type, proto, addr


class IoPipelineHostResolver(Abstract):
    """
    Resolves a host name and port to addresses to try in order, reporting through a callback on the host's thread -
    at once, for a resolver which blocks, or later, for one which resolves elsewhere.
    """

    @abc.abstractmethod
    def resolve(
            self,
            host: str,
            port: int,
            on_done: ta.Callable[[ta.Union[IoPipelineHostResolveResult, BaseException]], None],
    ) -> None:
        raise NotImplementedError

    def close(self) -> None:
        pass
