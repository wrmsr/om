import contextlib

import pytest

from ..exitstack import AsyncKeyedExitStack
from ..exitstack import KeyedExitStack


def test_key_reusable_after_early_exit() -> None:
    exits = []

    @contextlib.contextmanager
    def cm(value):
        yield value
        exits.append(value)

    with KeyedExitStack() as stack:
        assert stack.enter_context(cm(1), key='key') == 1
        stack.exit_keyed_context('key')
        assert exits == [1]

        assert stack.enter_context(cm(2), key='key') == 2

    assert exits == [1, 2]


@pytest.mark.asyncs('asyncio')
async def test_async_key_reusable_after_early_exit() -> None:
    exits = []

    @contextlib.asynccontextmanager
    async def cm(value):
        yield value
        exits.append(value)

    async with AsyncKeyedExitStack() as stack:
        assert await stack.enter_async_context(cm(1), key='key') == 1
        await stack.async_exit_keyed_context('key')
        assert exits == [1]

        assert await stack.enter_async_context(cm(2), key='key') == 2

    assert exits == [1, 2]
