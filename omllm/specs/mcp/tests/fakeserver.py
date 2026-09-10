"""A minimal fake MCP server over stdio, enough to exercise the client: initialize and a paginated tools/list."""
import asyncio
import typing as ta

from omcore.specs import jsonrpc as jr
from omcore.specs.jsonrpc import pipelines as jpl


_TOOLS = [
    {'name': 'alpha', 'description': 'first', 'inputSchema': {'type': 'object'}},
    {'name': 'beta', 'description': 'second', 'inputSchema': {'type': 'object'}},
    {'name': 'gamma', 'inputSchema': {'type': 'object'}},
]


def build_dispatcher() -> jr.AsyncDictDispatcher:
    def initialize(**kwargs: ta.Any) -> ta.Any:
        return {
            'protocolVersion': kwargs.get('protocolVersion', '2025-06-18'),
            'capabilities': {'tools': {}},
            'serverInfo': {'name': 'fake', 'version': '0'},
        }

    def list_tools(cursor: str | None = None, **kwargs: ta.Any) -> ta.Any:
        # Two pages of tools.
        if cursor is None:
            return {'tools': _TOOLS[:2], 'nextCursor': 'page2'}
        elif cursor == 'page2':
            return {'tools': _TOOLS[2:]}
        else:
            raise jr.JsonrpcMethodError(jr.KnownErrors.INVALID_PARAMS, data=cursor)

    def ping() -> ta.Any:
        return {}

    return jr.AsyncDictDispatcher({
        'initialize': initialize,
        'tools/list': list_tools,
        'ping': ping,
    })


async def _a_main() -> None:
    conn = await jpl.AsyncioConnections.of_stdio(
        dispatcher=build_dispatcher(),
    )
    async with conn:
        await conn.wait_closed()


def _main() -> None:
    asyncio.run(_a_main())


if __name__ == '__main__':
    _main()
