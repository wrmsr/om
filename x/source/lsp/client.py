"""
TODO:
 - -> omdev.specs.lsp
"""
import asyncio
import dataclasses as dc
import typing as ta

from omcore import marshal as msh
from omcore.specs import jsonrpc as jr
from omcore.specs.jsonrpc import pipelines as jpl


##


class LspClient:
    """
    A thin LSP-flavored wrapper over a JSON-RPC connection using Content-Length framing.

    Dataclass params are marshaled on the way out; responses come back raw, since their types depend on the method.
    """

    CONFIG: ta.ClassVar[jpl.Config] = jpl.Config(
        framing='content-length',
        default_request_timeout_s=60.,
    )

    def __init__(
            self,
            conn: jpl.AsyncioConnection,
    ) -> None:
        super().__init__()

        self._conn = conn

    @property
    def connection(self) -> jpl.AsyncioConnection:
        return self._conn

    @classmethod
    def of_subprocess(
            cls,
            proc: asyncio.subprocess.Process,
            *,
            config: jpl.Config | None = None,
            **kwargs: ta.Any,
    ) -> LspClient:
        return cls(jpl.AsyncioConnections.of_subprocess(
            proc,
            config if config is not None else cls.CONFIG,
            **kwargs,
        ))

    async def __aenter__(self) -> ta.Self:
        await self._conn.__aenter__()
        return self

    async def __aexit__(self, et, e, tb) -> None:
        await self._conn.__aexit__(et, e, tb)

    #

    @staticmethod
    def _marshal_params(params: ta.Any) -> jr.Params | None:
        if dc.is_dataclass(params) and not isinstance(params, type):
            return msh.marshal(params)  # type: ignore[return-value]
        return params

    async def request(
            self,
            method: str,
            params: ta.Any = None,
            *,
            timeout_s: float | None | type[jr.NotSpecified] = jr.NotSpecified,
    ) -> jr.Response:
        return await self._conn.send_request(
            self._conn._new_request(method, self._marshal_params(params)),  # noqa
            timeout_s=timeout_s,
        )

    async def notify(self, method: str, params: ta.Any = None) -> None:
        await self._conn.notify(method, self._marshal_params(params))
