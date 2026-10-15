# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import typing as ta

from ....fdio.handlers import FdioHandler
from ....fdio.manager import FdioManager
from ...core import IoPipeline
from ...posting.types import IoPipelinePost
from ...posting.types import IoPipelinePostingTarget
from ...posting.types import TargetIoPipelinePostingService
from ..types import IoPipelineDriverState
from .core import IoPipelineFdioDriver
from .descriptors import DescriptorIoPipelineFdioTransport


##


class FdPairReadIoPipelineFdioHandler(FdioHandler):
    """The read side of a descriptor pair: reports the driver's read interest and its deadline."""

    def __init__(self, fd: int, driver: IoPipelineFdioDriver) -> None:
        super().__init__()

        self._fd = fd
        self._driver = driver

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._fd}>'

    def fd(self) -> int:
        return self._fd

    @property
    def closed(self) -> bool:
        return self._driver.closed

    def close(self) -> None:
        self._driver.close()

    def readable(self) -> bool:
        return self._driver.wants_read()

    def next_deadline(self) -> ta.Optional[float]:
        return self._driver.next_deadline()

    def on_readable(self) -> None:
        self._driver.on_readable()

    def on_timeout(self) -> None:
        self._driver.on_timeout()


class FdPairWriteIoPipelineFdioHandler(FdioHandler):
    """The write side of a descriptor pair: reports the driver's write interest; done once the write descriptor is."""

    def __init__(self, fd: int, driver: IoPipelineFdioDriver, transport: DescriptorIoPipelineFdioTransport) -> None:
        super().__init__()

        self._fd = fd
        self._driver = driver
        self._transport = transport

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._fd}>'

    def fd(self) -> int:
        return self._fd

    @property
    def closed(self) -> bool:
        return self._driver.closed or self._transport.write_fd_closed

    def close(self) -> None:
        self._driver.close()

    def writable(self) -> bool:
        return not self._transport.write_fd_closed and self._driver.wants_write()

    def on_writable(self) -> None:
        self._driver.on_writable()


##


class IoPipelineDriverFdPairFdioHandlers(IoPipelinePostingTarget):
    """
    Drive a pipeline over a read descriptor and a write descriptor - a pipe pair, a process's own standard streams -
    with an `FdioManager`: the pair form of `IoPipelineFdioDriver`, exposed to the manager as two handlers sharing one
    core, both of which `register` registers.

    The descriptors are the caller's unless `owned`: their blocking mode is restored on release and they are closed
    only if owned. ShutdownOutput closes the write descriptor if it is owned or `close_write_fd_on_output_shutdown`
    permits it, after which the write handler reports itself closed; otherwise the message fails with
    UnsupportedIoPipelineError and both descriptors are left intact. Closing either handler closes the driver and both.
    """

    def __init__(
            self,
            read_fd: int,
            write_fd: int,
            spec: IoPipeline.Spec,
            config: ta.Optional[IoPipelineFdioDriver.Config] = None,
            *,
            owned: bool = False,
            close_write_fd_on_output_shutdown: bool = False,
    ) -> None:
        super().__init__()

        self._transport = transport = DescriptorIoPipelineFdioTransport(
            read_fd,
            write_fd,
            owned=owned,
            close_write_fd_on_output_shutdown=close_write_fd_on_output_shutdown,
        )
        self._driver = driver = IoPipelineFdioDriver(transport, spec, config)

        self._read_handler = FdPairReadIoPipelineFdioHandler(read_fd, driver)
        self._write_handler = FdPairWriteIoPipelineFdioHandler(write_fd, driver, transport)

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._transport.read_fd}, {self._transport.write_fd}, {self._driver.state.name}>'  # noqa

    @property
    def driver(self) -> IoPipelineFdioDriver:
        return self._driver

    @property
    def read_handler(self) -> FdPairReadIoPipelineFdioHandler:
        return self._read_handler

    @property
    def write_handler(self) -> FdPairWriteIoPipelineFdioHandler:
        return self._write_handler

    @property
    def handlers(self) -> ta.Tuple[FdioHandler, FdioHandler]:
        return (self._read_handler, self._write_handler)

    def register(self, manager: FdioManager) -> None:
        manager.register(self._read_handler)
        manager.register(self._write_handler)

    def unregister(self, manager: FdioManager) -> None:
        """Unregisters whichever of the two the manager has not dropped already."""

        for h in self.handlers:
            try:
                manager.unregister(h)
            except KeyError:
                pass

    #

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
    def closed(self) -> bool:
        return self._driver.closed

    @property
    def output_shutdown(self) -> bool:
        return self._driver.output_shutdown

    def close(self) -> None:
        self._driver.close()

    def enqueue(self, *in_msgs: ta.Any) -> None:
        self._driver.enqueue(*in_msgs)

    def accept_post(self, post: IoPipelinePost) -> None:
        self._driver.accept_post(post)

    def next(
            self,
            *,
            read: bool = True,
            raise_on_stall: bool = True,
    ) -> ta.Optional[ta.Any]:
        return self._driver.next(read=read, raise_on_stall=raise_on_stall)
