"""
The repl's pty seam over the harness's process manager: a shell the repl starts is an ordinary managed process - in a
scope of its own, with the manager's teardown guarantees - on whatever the bound manager manages, this machine or a
remote agent's. Nothing here knows which.
"""
import asyncio
import signal
import typing as ta

from omdev import repl

from .....core import processes
from .....core.rpc.errors import RpcError


##


class ProcessPtyProcess(repl.PtyProcess):
    def __init__(self, process: processes.Process) -> None:
        super().__init__()

        self._process = process
        self._cursor = 0

        self._exit_watcher: asyncio.Task[None] | None = asyncio.get_running_loop().create_task(self._close_on_exit())

    @property
    def process(self) -> processes.Process:
        return self._process

    async def _close_on_exit(self) -> None:
        """
        Output ends when the last holder of the terminal lets go of it, which need not be the process started on it: a
        shell's background jobs outlive it, terminal in hand. A reader is owed an end when the process itself exits, so
        the process is closed as soon as it does - sweeping its group, as a terminal going away would, and with that
        ending its output.
        """

        try:
            await self._process.wait()
        except processes.ProcessError:
            return
        await self._process.aclose()

    async def write(self, data: bytes) -> None:
        if self._process.exited:
            raise BrokenPipeError(repr(self._process))
        try:
            await self._process.write(data)
        except BrokenPipeError:
            raise
        except (OSError, processes.ProcessError, RpcError) as e:
            raise BrokenPipeError(str(e)) from e

    # The spool takes no timeout to mean "do not wait": an unbounded read is a long one, repeated.
    _UNBOUNDED_POLL_S: ta.ClassVar[float] = 3600.

    async def read(self, timeout: float | None = None) -> bytes | None:
        spool = self._process.spool
        while True:
            read = await spool.poll(
                self._cursor,
                timeout=timeout if timeout is not None else self._UNBOUNDED_POLL_S,
            )
            self._cursor = read.end

            if (data := read.data()):
                return data
            if read.ended:
                return b''
            if timeout is not None:
                return None

    async def resize(self, rows: int, cols: int) -> None:
        try:
            await self._process.resize(rows, cols)
        except processes.ProcessNotAliveError:
            pass

    async def aclose(self) -> None:
        if (watcher := self._exit_watcher) is not None:
            self._exit_watcher = None
            watcher.cancel()
            await asyncio.gather(watcher, return_exceptions=True)

        try:
            await self._process.aclose()
        finally:
            self._process.spool.close()


class ProcessScopePtySpawner(repl.PtySpawner):
    # A terminal going away is a hangup, which is what an interactive shell (deaf to SIGTERM) exits on, passing it on
    # to its jobs. Jobs which outlive the shell are not waited on for long: their output has nowhere to go.
    _TERMINATION_POLICY: ta.ClassVar[processes.TerminationPolicy] = processes.TerminationPolicy(
        signal=signal.SIGHUP,
        grace_s=2.,
        kill_s=2.,
        drain_s=.25,
    )

    # Output is consumed as it arrives and never read again: nothing is spilled, and what nobody is there to read (an
    # abandoned command's) is dropped past the cap.
    _SPOOL_POLICY: ta.ClassVar[processes.SpoolPolicy] = processes.SpoolPolicy(
        memory_cap=4 * 1024 * 1024,
        spill=False,
    )

    def __init__(
            self,
            scope: processes.ProcessScope,
            *,
            cwd: str | None = None,
            name: str | None = 'repl',
    ) -> None:
        super().__init__()

        self._scope = scope
        self._cwd = cwd
        self._name = name

    async def spawn(
            self,
            argv: ta.Sequence[str],
            *,
            rows: int,
            cols: int,
    ) -> repl.PtyProcess:
        process = await self._scope.spawn(
            processes.ProcessSpec(
                tuple(argv),
                cwd=self._cwd,
                stdio=processes.PtyStdio(rows=rows, cols=cols),
                name=self._name,
            ),
            self._TERMINATION_POLICY,
            self._SPOOL_POLICY,
        )
        return ProcessPtyProcess(process)
