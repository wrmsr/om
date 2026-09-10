import asyncio
import contextlib
import subprocess
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import marshal as msh
from omcore.specs import jsonrpc as jr
from omcore.specs.jsonrpc import pipelines as jpl

from . import protocolold as pt


##


class McpServerConnection:
    """
    A client-side connection to an MCP server over newline-delimited JSON-RPC on a byte stream, typically a spawned
    server process's stdio.

    Server-initiated requests (sampling, elicitation) and notifications are routed to the overridable handler methods,
    which do nothing by default.
    """

    def __init__(
            self,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            *,
            config: jpl.Config | None = None,
            default_timeout_s: float | None = 30.,
    ) -> None:
        super().__init__()

        if config is None:
            config = jpl.Config(
                default_request_timeout_s=default_timeout_s,
            )

        self._conn = jpl.AsyncioConnections.of_streams(
            reader,
            writer,
            config,
            dispatcher=self._Dispatcher(self),
            notification_handler=self._handle_notification,
        )

    @property
    def connection(self) -> jpl.AsyncioConnection:
        return self._conn

    #

    @classmethod
    def from_process(
            cls,
            proc: asyncio.subprocess.Process,
            **kwargs: ta.Any,
    ) -> McpServerConnection:
        return cls(
            check.not_none(proc.stdout),
            check.not_none(proc.stdin),
            **kwargs,
        )

    @classmethod
    def open_process(
            cls,
            cmd: ta.Sequence[str],
            open_kwargs: ta.Mapping[str, ta.Any] | None = None,
            *,
            exit_timeout_s: float = 5.,
            **kwargs: ta.Any,
    ) -> ta.AsyncContextManager[tuple[asyncio.subprocess.Process, McpServerConnection]]:
        """
        Spawn a server process and connect to it over its stdio.

        On exit the connection is closed, which closes the server's stdin, and the server is given `exit_timeout_s`
        to exit on its own before being terminated and then killed.
        """

        @contextlib.asynccontextmanager
        async def inner() -> ta.AsyncGenerator[tuple[asyncio.subprocess.Process, McpServerConnection]]:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                **(open_kwargs or {}),
            )

            try:
                async with cls.from_process(
                        proc,
                        **kwargs,
                ) as client:
                    yield (proc, client)

            finally:
                await cls._finish_process(proc, exit_timeout_s=exit_timeout_s)

        return inner()

    @staticmethod
    async def _finish_process(proc: asyncio.subprocess.Process, *, exit_timeout_s: float) -> None:
        if proc.returncode is not None:
            with contextlib.suppress(Exception):
                await proc.wait()
            return

        if proc.stdin is not None:
            proc.stdin.close()
            with contextlib.suppress(Exception):
                await proc.stdin.wait_closed()

        try:
            await asyncio.wait_for(proc.wait(), timeout=exit_timeout_s)
            return
        except TimeoutError:
            pass

        proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=exit_timeout_s)
        except TimeoutError:
            proc.kill()
            with contextlib.suppress(Exception):
                await proc.wait()

    #

    async def __aenter__(self) -> ta.Self:
        await self._conn.__aenter__()
        return self

    async def __aexit__(self, et, e, tb) -> None:
        await self._conn.__aexit__(et, e, tb)

    async def close(self, *, graceful: bool = True) -> None:
        await self._conn.close(graceful=graceful)

    #

    class _Dispatcher(jr.AsyncDispatcher):
        def __init__(self, owner: McpServerConnection) -> None:
            super().__init__()

            self._owner = owner

        async def dispatch(self, connection: ta.Any, request: jr.Request) -> ta.Any:
            return await self._owner._handle_request(request)  # noqa

    async def _handle_request(self, req: jr.Request) -> ta.Any:
        """Answer a server-initiated request. Raise jr.MethodError to answer with a specific error."""

        raise jr.JsonrpcMethodError(jr.KnownErrors.METHOD_NOT_FOUND, data=req.method)

    async def _handle_notification(self, _conn: jpl.AsyncioConnection, no: jr.Request) -> None:
        pass

    #

    async def request(self, req: pt.ClientRequest[pt.ClientResultT]) -> pt.ClientResultT:
        res_cls = pt.MESSAGE_TYPES_BY_JSON_RPC_METHOD_NAME[pt.ClientResult][req.json_rpc_method_name]  # type: ignore[type-abstract]  # noqa
        req_mv = msh.marshal(req)
        res_mv = await self._conn.request(req.json_rpc_method_name, req_mv)  # type: ignore[arg-type]
        res = msh.unmarshal(res_mv, res_cls)
        return ta.cast(pt.ClientResultT, res)

    async def notify(self, no: pt.Notification) -> None:
        no_mv = msh.marshal(no)
        await self._conn.notify(no.json_rpc_method_name, no_mv)  # type: ignore[arg-type]

    #

    async def yield_cursor_request(
            self,
            req: pt.CursorClientRequest[pt.CursorClientResultT],
    ) -> ta.AsyncGenerator[pt.CursorClientResultT]:
        check.none(req.cursor)

        cursor: str | None = None
        while True:
            res = await self.request(dc.replace(req, cursor=cursor))  # noqa
            yield res

            if (cursor := res.next_cursor) is None:
                break

    async def list_cursor_request(
            self,
            req: pt.CursorClientRequest[pt.CursorClientResultT],
    ) -> list[pt.CursorClientResultT]:
        return [res async for res in self.yield_cursor_request(req)]

    #

    async def list_tools(self) -> list[pt.Tool]:
        return [
            tool
            async for res in self.yield_cursor_request(pt.ListToolsRequest())
            for tool in res.tools
        ]

    async def list_prompts(self) -> list[pt.Prompt]:
        return [
            prompt
            async for res in self.yield_cursor_request(pt.ListPromptsRequest())
            for prompt in res.prompts
        ]
