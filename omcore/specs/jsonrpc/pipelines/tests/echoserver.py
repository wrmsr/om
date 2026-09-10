"""
A small JSON-RPC peer over stdio for subprocess tests: echoes params back, and can call back into its client.

Methods:
 - echo(**params) -> params
 - add(a, b) -> a + b
 - fail() -> raises a custom error
 - boom() -> raises an unexpected exception
 - callback(value) -> asks the client to `double(value)` and returns the result
 - sleep(s) -> waits s seconds before returning
 - shutdown() -> closes the connection after responding
"""
import asyncio
import typing as ta

from ...dispatch import AsyncDictJsonrpcDispatcher
from ...dispatch import JsonrpcDispatchContext
from ...dispatch import JsonrpcMethod
from ...errors import JsonrpcMethodError
from ..asyncio import AsyncioJsonrpcConnection
from ..asyncio import AsyncioJsonrpcConnections
from ..configs import JsonrpcPipelineConfig


def build_dispatcher() -> AsyncDictJsonrpcDispatcher:
    async def echo(**kwargs: ta.Any) -> ta.Any:
        return kwargs

    def add(a: int, b: int) -> int:
        return a + b

    def fail() -> None:
        raise JsonrpcMethodError(1234, 'nope', {'why': 'because'})

    def boom() -> None:
        raise RuntimeError('boom')

    async def callback(ctx: JsonrpcDispatchContext, value: int) -> int:
        conn: AsyncioJsonrpcConnection = ctx.connection
        return await conn.request('double', {'value': value})

    async def sleep(s: float) -> str:
        await asyncio.sleep(s)
        return 'slept'

    async def shutdown(ctx: JsonrpcDispatchContext) -> str:
        conn: AsyncioJsonrpcConnection = ctx.connection

        async def later() -> None:
            await asyncio.sleep(.05)
            await conn.close()

        asyncio.create_task(later())  # noqa
        return 'bye'

    return AsyncDictJsonrpcDispatcher({
        'echo': echo,
        'add': add,
        'fail': fail,
        'boom': boom,
        'callback': JsonrpcMethod(callback, with_context=True),
        'sleep': sleep,
        'shutdown': JsonrpcMethod(shutdown, with_context=True),
    })


async def _a_main() -> None:
    conn = await AsyncioJsonrpcConnections.of_stdio(
        JsonrpcPipelineConfig(),
        dispatcher=build_dispatcher(),
    )
    async with conn:
        await conn.wait_closed()


def _main() -> None:
    asyncio.run(_a_main())


if __name__ == '__main__':
    _main()
