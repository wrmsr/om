# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import typing as ta

from ....fdio.handlers import FdioHandler
from ...core import IoPipeline
from ...posting.types import IoPipelinePost
from ...posting.types import IoPipelinePostingTarget
from ...posting.types import TargetIoPipelinePostingService
from ..types import IoPipelineDriverState
from .core import IoPipelineFdioDriver
from .descriptors import DescriptorIoPipelineFdioTransport


##


class IoPipelineDriverDuplexFdioHandler(FdioHandler, IoPipelinePostingTarget):
    """
    Drive a pipeline over one descriptor read and written both ways - a terminal master, or a socket by number -
    registered with an `FdioManager`: the duplex form of `IoPipelineFdioDriver`.

    The descriptor is the caller's unless `owned`: its blocking mode is restored on release and it is closed only if
    owned. A socket descriptor is half-closed by ShutdownOutput through a temporary duplicate; any other single
    descriptor cannot be half-closed, so the message fails with UnsupportedIoPipelineError and the transport is left
    intact.
    """

    def __init__(
            self,
            fd: int,
            spec: IoPipeline.Spec,
            config: ta.Optional[IoPipelineFdioDriver.Config] = None,
            *,
            owned: bool = False,
    ) -> None:
        super().__init__()

        self._fd = fd
        self._driver = IoPipelineFdioDriver(
            DescriptorIoPipelineFdioTransport(fd, fd, owned=owned),
            spec,
            config,
        )

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._fd}, {self._driver.state.name}>'

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

    ##

    def fd(self) -> int:
        return self._fd

    @property
    def closed(self) -> bool:
        return self._driver.closed

    def close(self) -> None:
        self._driver.close()

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
