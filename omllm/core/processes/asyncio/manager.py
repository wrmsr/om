"""
The asyncio `ProcessManager`: `BaseProcessManager` with asyncio for its runtime hooks - tasks, a bounded concurrent
close, native pipe transports for stdin / output / the exec-status handshake, and the loop-bound spool notifier and
process handle. Everything asyncio-specific in this package lives here and in its siblings; the manager logic itself is
in `../managers/`.
"""
import asyncio
import functools
import typing as ta

from omcore import check
from omcore.asyncs.asynclite.asyncio.api import AsyncioAsynclite

from ..launch.launcher import Launcher
from ..managers.base import BaseProcessManager
from ..managers.process import BaseProcess
from ..managers.process import ProcessStdinWriter
from ..managers.types import ManagerConfig
from ..spool.spool import SpoolNotifier
from ..types.ids import ProcessIdGenerator
from .notifier import AsyncioSpoolNotifier
from .pipes import ReadPipeProtocol
from .pipes import StatusPipeProtocol
from .pipes import StdinWriter
from .pipes import WritePipeProtocol
from .process import AsyncioProcess


##


class AsyncioProcessManager(BaseProcessManager):
    def __init__(
            self,
            config: ManagerConfig | None = None,
            *,
            launcher: Launcher | None = None,
            id_generator: ProcessIdGenerator | None = None,
    ) -> None:
        super().__init__(
            config,
            asynclite=AsyncioAsynclite(),
            launcher=launcher,
            id_generator=id_generator,
        )

        self._loop: asyncio.AbstractEventLoop | None = None
        self._tasks: set[asyncio.Task] = set()

    @property
    def _running_loop(self) -> asyncio.AbstractEventLoop:
        return check.not_none(self._loop)

    ##
    # Runtime hooks

    async def _start_runtime(self) -> None:
        self._loop = asyncio.get_running_loop()

    def _spawn_task(self, coro: ta.Coroutine[ta.Any, ta.Any, ta.Any]) -> None:
        t = self._running_loop.create_task(coro)
        self._tasks.add(t)
        t.add_done_callback(self._tasks.discard)

    async def _join_tasks(self) -> None:
        while self._tasks:
            await asyncio.gather(*list(self._tasks), return_exceptions=True)
            # `gather` completes eagerly (without yielding) when every task is already done, and a finished task stays
            # in `_tasks` until its discard callback has run - so give the loop a turn to run those.
            await asyncio.sleep(0)

    async def _run_all_bounded(
            self,
            coros: ta.Sequence[ta.Coroutine[ta.Any, ta.Any, ta.Any]],
            timeout: float | None,
    ) -> bool:
        loop = self._running_loop
        tasks = [loop.create_task(c) for c in coros]
        try:
            async with asyncio.timeout(timeout):
                await asyncio.gather(*tasks)
        except TimeoutError:
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            return False
        return True

    def _new_spool_notifier(self) -> SpoolNotifier:
        return AsyncioSpoolNotifier(self._running_loop)

    def _new_process(self, **kwargs: ta.Any) -> BaseProcess:
        return AsyncioProcess(loop=self._running_loop, **kwargs)

    async def _connect_stdin(self, fd: int) -> ProcessStdinWriter:
        # The transport owns the file object (and so the fd) - including on a failed / cancelled connect.
        transport, protocol = await self._running_loop.connect_write_pipe(
            WritePipeProtocol,
            open(fd, 'wb', buffering=0),  # noqa
        )
        return StdinWriter(transport, protocol)

    async def _connect_output(self, process: BaseProcess, fd_num: int, fd: int) -> None:
        transport, _ = await self._running_loop.connect_read_pipe(
            functools.partial(
                ReadPipeProtocol,
                functools.partial(process._on_data, fd_num),  # noqa
                functools.partial(process._on_output_eof, fd_num),  # noqa
            ),
            open(fd, 'rb', buffering=0),  # noqa
        )
        process._add_output_channel(fd_num, transport.close)  # noqa

    async def _read_exec_status(self, fd: int, timeout: float) -> bytes | None:
        loop = self._running_loop
        fut: asyncio.Future[bytes] = loop.create_future()
        await loop.connect_read_pipe(
            functools.partial(StatusPipeProtocol, fut),
            open(fd, 'rb', buffering=0),  # noqa
        )
        try:
            return await asyncio.wait_for(fut, timeout)
        except TimeoutError:
            return None
