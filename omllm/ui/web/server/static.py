"""The page, at `/`, and its files, at `/static/<path>`."""
import re
import typing as ta

from omcore import check
from omcore.http import asgi
from omcore.http.apps.routes import Route
from omcore.http.apps.routes import RouteHandlerHolder
from omcore.http.apps.routes import handles

from .resources import WebResources
from .responses import send_bytes_response
from .responses import send_error_response
from .security import WebToken


##


class WebStaticHandlers(RouteHandlerHolder):
    INDEX_TOKEN_PLACEHOLDER: ta.ClassVar[bytes] = b'__OMLLM_WEB_TOKEN__'

    # Nothing but the server's own files runs, styles, or is fetched, and nothing frames the page: what model output the
    # page renders gets no further than the page's own rendering lets it, should that ever fall short.
    CONTENT_SECURITY_POLICY: ta.ClassVar[bytes] = b'; '.join([
        b"default-src 'self'",
        b"img-src 'self' data:",
        b"object-src 'none'",
        b"base-uri 'none'",
        b"form-action 'none'",
        b"frame-ancestors 'none'",
    ])

    def __init__(
            self,
            *,
            resources: WebResources,
            token: WebToken,
    ) -> None:
        super().__init__()

        self._resources = resources
        self._token = token

    @handles(Route.get('/'))
    async def handle_get_index(self, scope: asgi.Scope, recv: asgi.Recv, send: asgi.Send) -> None:
        resource = check.not_none(self._resources.read('index.html'))

        check.state(resource.body.count(self.INDEX_TOKEN_PLACEHOLDER) == 1)
        body = resource.body.replace(self.INDEX_TOKEN_PLACEHOLDER, self._token.v.encode('ascii'))

        await send_bytes_response(
            send,
            200,
            body,
            content_type=resource.content_type,
            headers=[
                (b'content-security-policy', self.CONTENT_SECURITY_POLICY),
                (b'x-frame-options', b'DENY'),
                (b'referrer-policy', b'no-referrer'),
            ],
        )

    @handles(Route.get(re.compile(r'/static/.+')))
    async def handle_get_static(self, scope: asgi.Scope, recv: asgi.Recv, send: asgi.Send) -> None:
        path = scope['path'].removeprefix('/static/')

        if (resource := self._resources.read(path)) is None:
            await send_error_response(send, 404, 'not_found')
            return

        await send_bytes_response(send, 200, resource.body, content_type=resource.content_type)
