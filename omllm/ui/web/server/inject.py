import contextlib
import socket
import typing as ta

from omcore import inject as inj
from omcore.http import asgi
from omcore.http.apps.base import BaseServerUrl
from omcore.logs import all as logs

from ..config import DEFAULT_WEB_HOST
from ..config import DEFAULT_WEB_PORT
from ..config import WebConfig
from .api import WebApiHandlers
from .app import WebApp
from .resources import WebResources
from .security import WebRequestGuard
from .security import WebToken
from .security import build_allowed_hosts
from .security import is_loopback_host
from .serving import AsgiPipelineServer
from .serving import WebServerAddress
from .serving import bind_web_server_socket
from .serving import get_web_server_socket_address
from .sse import FeedSseStreamer
from .static import WebStaticHandlers


log = logs.get_module_logger(globals())


##


WebServerSocket = ta.NewType('WebServerSocket', socket.socket)


def _provide_web_server_socket(config: WebConfig) -> WebServerSocket:
    return WebServerSocket(bind_web_server_socket(
        config.host if config.host is not None else DEFAULT_WEB_HOST,
        config.port if config.port is not None else DEFAULT_WEB_PORT,
    ))


@contextlib.asynccontextmanager
async def _closing_web_server_socket(sock: WebServerSocket) -> ta.AsyncIterator[WebServerSocket]:
    try:
        yield sock
    finally:
        sock.close()


def _provide_web_server_address(sock: WebServerSocket) -> WebServerAddress:
    return get_web_server_socket_address(sock)


def _provide_web_request_guard(token: WebToken, address: WebServerAddress) -> WebRequestGuard:
    if not is_loopback_host(address.host):
        log.warning(
            'Serving on %s, beyond this machine: anyone who can reach it can load the page, and so drive the agent.',
            address.host,
        )

    return WebRequestGuard(
        token=token,
        allowed_hosts=build_allowed_hosts(address.host, address.port),
    )


def _provide_web_app(
        api: WebApiHandlers,
        static: WebStaticHandlers,
        guard: WebRequestGuard,
        address: WebServerAddress,
) -> WebApp:
    return WebApp(
        handlers=[api, static],
        guard=guard,
        base_server_url=BaseServerUrl(address.url),
    )


def _provide_asgi_pipeline_server(app: WebApp, sock: WebServerSocket) -> AsgiPipelineServer:
    return AsgiPipelineServer(
        app=ta.cast(asgi.App, app),
        sock=sock,
    )


##


def bind_server(config: WebConfig) -> inj.Elements:
    lst: list[inj.Elemental] = [
        inj.bind(
            WebServerSocket,
            singleton=True,
            to_async_fn=inj.make_async_managed_provider(_provide_web_server_socket, _closing_web_server_socket),
        ),
        inj.bind(_provide_web_server_address, singleton=True),

        inj.bind(WebToken.generate()),
        inj.bind(_provide_web_request_guard, singleton=True),

        inj.bind(WebResources, singleton=True),
        inj.bind(FeedSseStreamer, singleton=True),

        inj.bind(WebApiHandlers, singleton=True),
        inj.bind(WebStaticHandlers, singleton=True),
        inj.bind(_provide_web_app, singleton=True),

        inj.bind(_provide_asgi_pipeline_server, singleton=True),
    ]

    return inj.as_elements(*lst)
