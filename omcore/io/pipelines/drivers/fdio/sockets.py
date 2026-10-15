# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import socket
import typing as ta

from .....lite.check import check
from .....sockets.addresses import SocketAddress
from ....fdio.handlers import SocketFdioHandler
from ....streambufs.types import BytesLike
from ...core import IoPipeline
from ...posting.types import IoPipelinePost
from ...posting.types import IoPipelinePostingTarget
from ...posting.types import TargetIoPipelinePostingService
from ..types import IoPipelineDriverState
from .core import IoPipelineFdioDriver
from .core import IoPipelineFdioTransport


##


class SocketIoPipelineFdioTransport(IoPipelineFdioTransport):
    """A transport over an owned nonblocking socket, closed with it."""

    def __init__(self, sock: socket.socket) -> None:
        super().__init__()

        self._sock = sock

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}'

    @property
    def socket(self) -> socket.socket:
        return self._sock

    def read_into(self, buf: memoryview) -> int:
        return self._sock.recv_into(buf)

    def write(self, data: BytesLike) -> int:
        return self._sock.send(data)

    def shutdown_output(self) -> None:
        self._sock.shutdown(socket.SHUT_WR)

    def close(self) -> None:
        self._sock.close()


##


class IoPipelineDriverSocketFdioHandler(SocketFdioHandler, IoPipelinePostingTarget):
    """
    Drive a pipeline over an owned nonblocking socket registered with an `FdioManager`: the socket form of
    `IoPipelineFdioDriver`, which it exposes as `driver` and whose stepping surface it mirrors.

    ShutdownOutput is queued behind the bytes preceding it, then performed with `shutdown(SHUT_WR)`; reading continues
    afterwards. FinalOutput still drains and closes the socket. Enqueued messages and posted work wake the manager.
    """

    Config = IoPipelineFdioDriver.Config

    ACTIVE_STATES: ta.ClassVar[ta.Tuple[IoPipelineDriverState, ...]] = IoPipelineFdioDriver.ACTIVE_STATES

    def __init__(
            self,
            sock: socket.socket,
            addr: SocketAddress,
            spec: IoPipeline.Spec,
            config: ta.Optional[IoPipelineFdioDriver.Config] = None,
    ) -> None:
        sock.setblocking(False)
        super().__init__(sock, addr)

        self._driver = IoPipelineFdioDriver(SocketIoPipelineFdioTransport(sock), spec, config)

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._driver.state.name}>'

    @property
    def driver(self) -> IoPipelineFdioDriver:
        return self._driver

    @property
    def config(self) -> IoPipelineFdioDriver.Config:
        return self._driver.config

    @property
    def pipeline(self) -> IoPipeline:
        return self._driver.pipeline

    @property
    def posting(self) -> TargetIoPipelinePostingService:
        return self._driver.posting

    @property
    def state(self) -> IoPipelineDriverState:
        return self._driver.state

    @property
    def is_active(self) -> bool:
        return self._driver.is_active

    @property
    def output_shutdown(self) -> bool:
        return self._driver.output_shutdown

    #

    @property
    def closed(self) -> bool:
        return self._sock is None or self._driver.closed

    def close(self) -> None:
        """Abort the driver and discard any queued transport output."""

        try:
            self._driver.close()
        finally:
            super().close()

    #

    def enqueue(self, *in_msgs: ta.Any) -> None:
        self._driver.enqueue(*in_msgs)

    def accept_post(self, post: IoPipelinePost) -> None:
        self._driver.accept_post(post)

    def poll(self) -> ta.Union[
        ta.Tuple[ta.Literal['unhandled'], ta.Any],
        ta.Literal['read', 'stop', 'destroyed'],
        None,
    ]:
        return self._driver.poll()

    def next(
            self,
            *,
            read: bool = True,
            raise_on_stall: bool = True,
    ) -> ta.Optional[ta.Any]:
        return self._driver.next(read=read, raise_on_stall=raise_on_stall)

    def loop_until_done(self) -> None:
        try:
            self._driver.loop_until_done()
        finally:
            self.close()

    ##

    def fd(self) -> int:
        return check.not_none(self._sock).fileno()

    def readable(self) -> bool:
        return self._driver.wants_read()

    def writable(self) -> bool:
        return self._driver.wants_write()

    def next_deadline(self) -> ta.Optional[float]:
        return self._driver.next_deadline()

    def on_readable(self) -> None:
        self._driver.on_readable()

    def on_writable(self) -> None:
        self._driver.on_writable()

    def on_timeout(self) -> None:
        self._driver.on_timeout()
