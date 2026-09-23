import asyncio
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import typedvalues as tv
from omcore.os.pyremote.bestpython import get_best_python_sh
from omcore.os.pyremote.core import PyremoteBootstrapDriver
from omcore.os.pyremote.core import pyremote_build_bootstrap_source
from omcore.subprocesses.wrap import subprocess_maybe_shell_wrap_exec

from ...core.rpc.channels import AsyncioStreamRpcChannel
from .client import RemoteAgentClient
from .payload import RemoteAgentPayloadFile
from .payload import get_remote_agent_payload_src


##


class DockerContainerIdt(tv.UniqueScalarTypedValue[str], final=True):
    def __post_init__(self) -> None:
        check.non_empty_str(self.v)


@dc.dataclass(frozen=True, kw_only=True)
class DockerRemoteAgentConfig:
    docker: str = 'docker'

    payload_file: RemoteAgentPayloadFile | None = None

    startup_timeout_s: float = 30.
    shutdown_timeout_s: float = 10.

    stderr_tail_bytes: int = 64 * 1024

    def __post_init__(self) -> None:
        check.non_empty_str(self.docker)
        check.arg(self.startup_timeout_s > 0.)
        check.arg(self.shutdown_timeout_s > 0.)
        check.arg(self.stderr_tail_bytes > 0)


class DockerRemoteAgentError(RuntimeError):
    pass


def build_docker_remote_agent_argv(
        container_id: DockerContainerIdt,
        config: DockerRemoteAgentConfig = DockerRemoteAgentConfig(),
) -> tuple[str, ...]:
    return subprocess_maybe_shell_wrap_exec(
        config.docker,
        'exec',
        '-i',
        container_id.v,
        'sh',
        '-c',
        get_best_python_sh(),
        '--',
        '-c',
        pyremote_build_bootstrap_source('omllm-agent'),
    )


##


class DockerRemoteAgentConnection:
    def __init__(
            self,
            container_id: DockerContainerIdt,
            config: DockerRemoteAgentConfig = DockerRemoteAgentConfig(),
    ) -> None:
        super().__init__()

        self._container_id = container_id
        self._config = config

        self._process: asyncio.subprocess.Process | None = None
        self._client: RemoteAgentClient | None = None
        self._stderr_task: asyncio.Task[None] | None = None
        self._stderr_tail = bytearray()

        self._started = False
        self._closed = False

    @property
    def container_id(self) -> DockerContainerIdt:
        return self._container_id

    @property
    def client(self) -> RemoteAgentClient:
        if self._client is None:
            raise RuntimeError('Docker remote agent connection has not been started')
        return self._client

    @property
    def stderr_tail(self) -> bytes:
        return bytes(self._stderr_tail)

    async def _drain_stderr(self, reader: asyncio.StreamReader) -> None:
        while data := await reader.read(64 * 1024):
            self._stderr_tail.extend(data)
            excess = len(self._stderr_tail) - self._config.stderr_tail_bytes
            if excess > 0:
                del self._stderr_tail[:excess]

    async def _wait_process(self) -> int:
        process = check.not_none(self._process)
        try:
            return await asyncio.wait_for(process.wait(), self._config.shutdown_timeout_s)
        except TimeoutError:
            if process.returncode is None:
                try:
                    process.terminate()
                except ProcessLookupError:
                    pass
        try:
            return await asyncio.wait_for(process.wait(), self._config.shutdown_timeout_s)
        except TimeoutError:
            if process.returncode is None:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
            return await process.wait()

    async def _finish_stderr(self) -> None:
        if self._stderr_task is not None:
            await self._stderr_task

    def _error_message(self, message: str, *, returncode: int | None = None) -> str:
        parts = [message, f'container={self._container_id.v!r}']
        if returncode is not None:
            parts.append(f'returncode={returncode}')
        if self._stderr_tail:
            parts.append(f'stderr={self._stderr_tail.decode("utf-8", "replace").strip()!r}')
        return '; '.join(parts)

    async def _close_failed_start(self) -> int | None:
        if self._process is None:
            return None
        if self._process.stdin is not None:
            self._process.stdin.close()
            try:
                await self._process.stdin.wait_closed()
            except (BrokenPipeError, ConnectionError, OSError):
                pass
        returncode = await self._wait_process()
        await self._finish_stderr()
        return returncode

    async def start(self) -> None:
        if self._started:
            raise RuntimeError('Docker remote agent connection has already been started')
        if self._closed:
            raise RuntimeError('Docker remote agent connection is closed')
        self._started = True

        try:
            process = await asyncio.create_subprocess_exec(
                *build_docker_remote_agent_argv(self._container_id, self._config),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self._process = process

            stdin = check.not_none(process.stdin)
            stdout = check.not_none(process.stdout)
            stderr = check.not_none(process.stderr)
            self._stderr_task = asyncio.create_task(
                self._drain_stderr(stderr),
                name='docker-remote-agent-stderr',
            )

            await asyncio.wait_for(
                PyremoteBootstrapDriver([
                    get_remote_agent_payload_src(file=self._config.payload_file),
                    'remote_agent_main()',
                ]).async_run(stdout, stdin),
                self._config.startup_timeout_s,
            )

            client = RemoteAgentClient(AsyncioStreamRpcChannel(stdout, stdin))
            self._client = client
            await client.start()

        except BaseException as e:
            if self._client is not None:
                try:
                    await self._client.aclose(timeout_s=self._config.shutdown_timeout_s)
                except BaseException as close_error:  # noqa: BLE001
                    e.add_note(f'Additionally failed to close remote agent client: {close_error!r}')
            returncode = await self._close_failed_start()
            self._closed = True
            if isinstance(e, asyncio.CancelledError):
                raise
            raise DockerRemoteAgentError(self._error_message(
                'Failed to start Docker remote agent',
                returncode=returncode,
            )) from e

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True

        error: BaseException | None = None
        if self._client is not None:
            try:
                await self._client.aclose(timeout_s=self._config.shutdown_timeout_s)
            except BaseException as e:  # noqa: BLE001
                error = e

        returncode = await self._close_failed_start()
        if error is not None:
            raise error
        if returncode not in (None, 0):
            raise DockerRemoteAgentError(self._error_message(
                'Docker remote agent exited unsuccessfully',
                returncode=returncode,
            ))

    async def __aenter__(self) -> ta.Self:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()
