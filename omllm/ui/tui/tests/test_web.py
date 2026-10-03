import http.server
import threading

import pytest

from omcore import check
from omcore import inject as inj
from omcore.testing import pytest as ptu

from .... import agent as agn
from .... import llm
from ....agent.tests.scripted import text_message
from ....agent.tests.scripted import tool_call_message
from ....agent.web.backends.duckduckgo.search import DuckduckgoWebSearcher
from ....agent.web.fetching import HttpWebFetcher
from ....agent.web.fetching import WebFetcher
from ....agent.web.search import WebSearcher
from ....agent.web.search import WebSearchHit
from ....agent.web.search import WebSearchResult
from ..config import Config
from .headless import bind_headless_tui
from .headless import bind_scripted_backend
from .headless import headless_tui


##


class _AllowingAsker(agn.PermissionAsker):
    def __init__(self):
        super().__init__()

        self.targets = []

    async def ask(self, requestor, target, rule):
        self.targets.append(target)
        return agn.PermissionState.ALLOW


class _Searcher(WebSearcher):
    async def search(self, request):
        return WebSearchResult(hits=[WebSearchHit(title=request.query, url='https://example.com/')])


class _Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        body = b'<html><body><h1>Harness web verification</h1><p>Local HTTP response.</p></body></html>'
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.mark.asyncs('asyncio')
async def test_web_defaults_resolve_through_injection():
    async with headless_tui(bind_headless_tui(Config(
        model='scripted', in_memory=True, web=True, no_skills=True,
    ))) as tui:
        assert isinstance(await tui.injector[WebFetcher], HttpWebFetcher)
        assert isinstance(await tui.injector[WebSearcher], DuckduckgoWebSearcher)
        assert {t.name for t in check.not_none(tui.agent.state.context.tools)} == {'web_search', 'web_fetch'}


@pytest.mark.asyncs('asyncio')
async def test_web_tools_make_http_requests_and_ask_permission(tmp_path):
    asker = _AllowingAsker()
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f'http://127.0.0.1:{server.server_address[1]}/'
    try:
        async with headless_tui(inj.override(
            bind_headless_tui(Config(model='scripted', in_memory=True, web=True, no_skills=True)),
            inj.bind(agn.PermissionAsker, to_const=asker),
            inj.bind(WebSearcher, to_const=_Searcher()),
            bind_scripted_backend(
                tool_call_message(
                    llm.ToolCall('fetch', 'web_fetch', {'url': url}),
                    llm.ToolCall('search', 'web_search', {'query': 'verification'}),
                ),
                text_message('done'),
            ),
        )) as tui:
            await tui.session.prompt('Fetch and search.')
            messages = check.not_none(tui.agent.state.context.messages)
            results = {m.tool_name: m for m in messages if isinstance(m, llm.ToolResultMessage)}
            assert all(not r.is_error for r in results.values())
            assert 'Harness web verification' in results['web_fetch'].content[0].text
            assert 'https://example.com/' in results['web_search'].content[0].text
            assert [t.url for t in asker.targets] == [url]
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


@ptu.skip.if_cant_import('ddgs')
@pytest.mark.online
@pytest.mark.asyncs('asyncio')
async def test_live_search_and_fetch_through_the_tui_tools():
    async with headless_tui(inj.override(
        bind_headless_tui(Config(model='scripted', in_memory=True, web=True, no_skills=True)),
        inj.bind(agn.PermissionAsker, to_const=_AllowingAsker()),
    )) as tui:
        tools = await tui.injector[agn.ToolSet]
        search = await tools['web_search'].executor(agn.ToolContext(args={'query': 'Python official documentation'}))
        assert search.error is None, search.error
        assert 'https://' in search.content.text
        fetch = await tools['web_fetch'].executor(agn.ToolContext(args={'url': 'https://example.com/'}))
        assert fetch.error is None, fetch.error
        assert 'Example Domain' in fetch.content.text
