"""The http client matrix the S3 tests run over, and test-only store factories."""
import typing as ta

from omcore import dataclasses as dc
from omcore import lang
from omcore.http import all as http

from ...tests.runners import AsyncioScenarioRunner
from ...tests.runners import ScenarioRunner
from ...tests.runners import SyncAwaitScenarioRunner


with lang.auto_proxy_import(globals()):
    from omcore.http.clients import httpx as _httpx
    from omcore.http.clients import urllib as _urllib
    from omcore.http.clients.pipelines import asyncio as _pipelines_asyncio
    from omcore.http.clients.pipelines import sync as _pipelines_sync


##


@dc.dataclass(frozen=True, kw_only=True)
class S3TestClient:
    id: str
    make: ta.Callable[[], http.AsyncHttpClient]
    make_runner: ta.Callable[[], ScenarioRunner]
    needs_httpx: bool = False


S3_TEST_CLIENTS: ta.Sequence[S3TestClient] = [
    S3TestClient(
        id='pipelines-sync',
        make=lambda: http.SyncAsyncHttpClient(_pipelines_sync.IoPipelineHttpClient()),
        make_runner=SyncAwaitScenarioRunner,
    ),
    S3TestClient(
        id='urllib',
        make=lambda: http.SyncAsyncHttpClient(_urllib.UrllibHttpClient()),
        make_runner=SyncAwaitScenarioRunner,
    ),
    S3TestClient(
        id='httpx-sync',
        make=lambda: http.SyncAsyncHttpClient(_httpx.HttpxHttpClient()),
        make_runner=SyncAwaitScenarioRunner,
        needs_httpx=True,
    ),
    S3TestClient(
        id='pipelines-asyncio',
        make=lambda: _pipelines_asyncio.AsyncioIoPipelineAsyncHttpClient(),
        make_runner=AsyncioScenarioRunner,
    ),
    S3TestClient(
        id='httpx-asyncio',
        make=lambda: _httpx.HttpxAsyncHttpClient(),
        make_runner=AsyncioScenarioRunner,
        needs_httpx=True,
    ),
]

S3_TEST_CLIENTS_BY_ID: ta.Mapping[str, S3TestClient] = {c.id: c for c in S3_TEST_CLIENTS}


def has_httpx() -> bool:
    try:
        import httpx  # noqa
    except ImportError:
        return False
    return True
