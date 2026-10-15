# ruff: noqa: PYI034 UP006 UP007 UP037 UP045
# @om-lite
"""What the host implementations share: handle ownership, outcome delivery by posting, and teardown."""
import dataclasses as dc
import functools
import socket
import typing as ta
import weakref

from ....lite.abstract import Abstract
from ....lite.check import check
from ....sockets.endpoints import SocketEndpoint
from ....sockets.endpoints import TcpSocketEndpoint
from ....sockets.endpoints import UnixSocketEndpoint
from ..core import IoPipeline
from ..core import IoPipelineHandlerContext
from ..core import IoPipelineHandlerRef
from ..core import IoPipelineHandlerUpdate
from ..posting.types import IoPipelinePosting
from .types import ClosedIoPipelineHostError
from .types import IoPipelineHost
from .types import IoPipelineHostCallback
from .types import IoPipelineHostHandle
from .types import IoPipelineHostResolver
from .types import IoPipelineHostResolveResult
from .types import ResolveIoPipelineHostError


T = ta.TypeVar('T')


##


class BaseIoPipelineHostHandle(IoPipelineHostHandle, Abstract):
    """Holds its owner's context weakly: an owner which is gone owns nothing, and the host closes what it owned."""

    # Listeners close first when the host closes, so nothing new is accepted while the rest closes.
    _closes_first: ta.ClassVar[bool] = False

    def __init__(self, host: 'BaseIoPipelineHost', owner: ta.Optional[IoPipelineHandlerRef]) -> None:
        super().__init__()

        self.__host_ref = weakref.ref(host)
        self.__owner_ctx_ref: ta.Optional[weakref.ReferenceType] = None
        self._set_owner(owner)

        host._register_handle(self)  # noqa

    @property
    def _host(self) -> ta.Optional['BaseIoPipelineHost']:
        return self.__host_ref()

    def _set_owner(self, owner: ta.Optional[IoPipelineHandlerRef]) -> None:
        if owner is None:
            self.__owner_ctx_ref = None
            return
        check.state(not owner.invalidated)
        # Outcomes are posted into the owner's pipeline, which must therefore be able to run them.
        check.not_none(owner.pipeline.services.find(IoPipelinePosting))
        self.__owner_ctx_ref = weakref.ref(owner._context)  # noqa

    def _owner_ctx(self) -> ta.Optional[IoPipelineHandlerContext]:
        if (ref := self.__owner_ctx_ref) is None:
            return None
        if (ctx := ref()) is None or ctx.invalidated:
            return None
        return ctx

    def _is_owned_by_ctx(self, ctx: IoPipelineHandlerContext) -> bool:
        return (ref := self.__owner_ctx_ref) is not None and ref() is ctx

    @property
    def owner(self) -> ta.Optional[IoPipelineHandlerRef]:
        if (ctx := self._owner_ctx()) is None:
            return None
        return ctx.ref

    def release(self) -> None:
        self.__owner_ctx_ref = None

    def transfer(self, owner: IoPipelineHandlerRef) -> None:
        self._set_owner(owner)

    #

    def _deliver(self, fn: IoPipelineHostCallback[T], result: T) -> None:
        """
        Delivers an outcome: posted into the owner's pipeline with the owner's context, or, with no owner, run here
        and now with none. An owner which is gone before the post runs loses the outcome; the host closes what it
        owned.
        """

        if self.__owner_ctx_ref is None:
            if (host := self._host) is not None:
                host._run_unowned(functools.partial(fn, None, result))  # noqa
            return

        if (ctx := self._owner_ctx()) is None:
            return

        try:
            ctx.pipeline.services[IoPipelinePosting].post_context(
                ctx.ref,
                lambda owner_ctx: fn(owner_ctx, result),
            )
        except ClosedIoPipelineHostError:
            pass
        except Exception:  # noqa  # ClosedIoPipelinePostingError and the like: the owner's driver is gone.
            pass

    def _unregister(self) -> None:
        if (host := self._host) is not None:
            host._unregister_handle(self)  # noqa


##


class BaseIoPipelineHost(IoPipelineHost, Abstract):
    def __init__(self, *, resolver: ta.Optional[IoPipelineHostResolver] = None) -> None:
        super().__init__()

        if resolver is None:
            resolver = BlockingIoPipelineHostResolver()
        self._resolver = resolver

        self._handles: ta.Dict[int, BaseIoPipelineHostHandle] = {}
        self._closed = False

    @property
    def resolver(self) -> IoPipelineHostResolver:
        return self._resolver

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def handles(self) -> ta.Sequence[IoPipelineHostHandle]:
        return list(self._handles.values())

    #

    def _register_handle(self, handle: BaseIoPipelineHostHandle) -> None:
        self._handles[id(handle)] = handle

    def _unregister_handle(self, handle: BaseIoPipelineHostHandle) -> None:
        self._handles.pop(id(handle), None)

    def _check_open(self) -> None:
        if self._closed:
            raise ClosedIoPipelineHostError('host is closed')

    def _run_unowned(self, fn: ta.Callable[[], None]) -> None:
        """Runs an outcome callback of a request without an owner: here and now, by default."""

        fn()

    def _hosted_spec(self, spec: IoPipeline.Spec) -> IoPipeline.Spec:
        """Every hosted pipeline finds its host in its services."""

        if self in spec.services:
            return spec
        return dc.replace(spec, services=[*spec.services, self])

    #

    def handler_update(self, handler_ref: IoPipelineHandlerRef, kind: IoPipelineHandlerUpdate) -> None:
        if kind != 'removing':
            return
        ctx = handler_ref._context  # noqa
        for handle in list(self._handles.values()):
            if handle._is_owned_by_ctx(ctx):  # noqa
                handle.close()

    def _close_handles(self) -> None:
        """Listeners first, so that nothing new is accepted while the rest closes; errors are collected."""

        first_exc: ta.Optional[BaseException] = None
        handles = list(self._handles.values())
        handles.sort(key=lambda h: 0 if h._closes_first else 1)  # noqa
        for handle in handles:
            try:
                handle.close()
            except Exception as e:  # noqa
                if first_exc is None:
                    first_exc = e
        self._handles.clear()
        if first_exc is not None:
            raise first_exc

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._close_handles()

    def __enter__(self) -> 'BaseIoPipelineHost':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    #

    @staticmethod
    def literal_addresses(endpoint: SocketEndpoint) -> ta.Optional[IoPipelineHostResolveResult]:
        """The addresses of an endpoint needing no resolution - a unix path or a literal IP address - or None."""

        if isinstance(endpoint, UnixSocketEndpoint):
            return [(socket.AF_UNIX, socket.SOCK_STREAM, 0, endpoint.path)]

        if isinstance(endpoint, TcpSocketEndpoint):
            for family in (socket.AF_INET, socket.AF_INET6):
                try:
                    socket.inet_pton(family, endpoint.host)
                except (OSError, ValueError):
                    continue
                return [(family, socket.SOCK_STREAM, 0, (endpoint.host, endpoint.port))]
            return None

        raise TypeError(endpoint)

    def _resolve(
            self,
            endpoint: SocketEndpoint,
            on_done: ta.Callable[[ta.Union[IoPipelineHostResolveResult, BaseException]], None],
    ) -> None:
        if (addresses := self.literal_addresses(endpoint)) is not None:
            on_done(addresses)
            return

        tcp = check.isinstance(endpoint, TcpSocketEndpoint)
        self._resolver.resolve(tcp.host, tcp.port, on_done)


##


class BlockingIoPipelineHostResolver(IoPipelineHostResolver):
    """Resolves with `getaddrinfo` on the calling thread, blocking it - the host's loop - for the lookup's duration."""

    def __repr__(self) -> str:
        return f'{type(self).__name__}()'

    def resolve(
            self,
            host: str,
            port: int,
            on_done: ta.Callable[[ta.Union[IoPipelineHostResolveResult, BaseException]], None],
    ) -> None:
        try:
            infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except OSError as e:
            on_done(ResolveIoPipelineHostError(TcpSocketEndpoint(host, port), [e]))
            return
        on_done([(family, type_, proto, sockaddr) for family, type_, proto, _, sockaddr in infos])
