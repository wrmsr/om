import os

import pytest

from ..examples import directed
from ..examples import pubsub
from .support import backend_names
from .support import new_backend
from .support import short_tmp_dir


@pytest.mark.parametrize('backend_name', backend_names())
@pytest.mark.asyncs('asyncio')
async def test_directed(backend_name):
    with short_tmp_dir() as tmp:
        async with new_backend(backend_name) as be:
            replies = await directed.run(be, f'ipc://{os.path.join(tmp, "r")}', clients=2, requests=3)
    assert replies == {
        b'client-%d' % i: [(b'reply', b'client-%d/%d' % (i, j)) for j in range(3)]
        for i in range(2)
    }


@pytest.mark.parametrize('backend_name', backend_names())
@pytest.mark.asyncs('asyncio')
async def test_pubsub(backend_name):
    async with new_backend(backend_name) as be:
        received = await pubsub.run(be, 'tcp://127.0.0.1:*', topic=b't', updates=4)
    assert received == [(b't', b'update %d' % i) for i in range(4)]
