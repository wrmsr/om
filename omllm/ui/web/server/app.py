"""
The http surface: the page and its files (`static`), and the api (`api`), behind the `WebRequestGuard`. Responses close
their connections.
"""
import typing as ta

from omcore.http import asgi
from omcore.http.apps.base import BaseServerUrl
from omcore.http.apps.routes import HANDLES_APP_MARKER_PROCESSORS
from omcore.http.apps.routes import RouteHandlerApp
from omcore.http.apps.routes import RouteHandlerHolder
from omcore.http.apps.routes import build_route_handler_map
from omcore.logs import all as logs

from .responses import BadWebRequestError
from .responses import send_error_response
from .security import WebRequestGuard
from .security import WebRequestRejectedError


log = logs.get_module_logger(globals())


##


class WebApp(asgi.App_):
    """Routes requests to the handlers, once they are past the guard, and turns a bad request into a 400."""

    def __init__(
            self,
            *,
            handlers: ta.Sequence[RouteHandlerHolder],
            guard: WebRequestGuard,
            base_server_url: BaseServerUrl,
    ) -> None:
        super().__init__()

        self._guard = guard

        self._router = RouteHandlerApp(
            build_route_handler_map(handlers, HANDLES_APP_MARKER_PROCESSORS),
            base_server_url,
        )

    async def __call__(self, scope: asgi.Scope, recv: asgi.Recv, send: asgi.Send) -> None:
        if scope['type'] != 'http':
            await self._router(scope, recv, send)
            return

        try:
            self._guard.check(scope, api=scope['path'].startswith('/api/'))
        except WebRequestRejectedError as e:
            log.warning('Rejected request: %s %s: %s', scope['method'], scope['path'], e)
            await send_error_response(send, 403, 'forbidden')
            return

        try:
            await self._router(scope, recv, send)
        except BadWebRequestError as e:
            await send_error_response(send, 400, 'bad_request', str(e))
