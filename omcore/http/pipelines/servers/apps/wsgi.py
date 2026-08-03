# ruff: noqa: UP006 UP045
# @om-lite
import dataclasses as dc
import io
import sys
import typing as ta
import urllib.parse

from .....io.pipelines.core import IoPipelineHandler
from .....io.pipelines.core import IoPipelineHandlerContext
from .....io.pipelines.core import IoPipelineMessages
from .....io.pipelines.flow.types import IoPipelineFlow
from .....io.streambufs.utils import ByteStreamBuffers
from .....lite.check import check
from ....headers import HttpHeaders
from ...requests import FullIoPipelineHttpRequest
from ...responses import FullIoPipelineHttpResponse
from ...responses import IoPipelineHttpResponseHead


##


@dc.dataclass(frozen=True)
class IoPipelineWsgiSpec:
    app: ta.Any
    host: str = '127.0.0.1'
    port: int = 8087


##


class WsgiIoPipelineHandler(IoPipelineHandler):
    def __init__(self, app: ta.Any) -> None:
        super().__init__()

        self._app = app

    #

    @staticmethod
    def _build_environ(req: FullIoPipelineHttpRequest) -> ta.Dict[str, ta.Any]:
        head = req.head

        # PEP 3333: PATH_INFO is the url-decoded path *without* the query string, which lives in QUERY_STRING.
        raw_path, _, query_string = head.target.partition('?')

        environ: ta.Dict[str, ta.Any] = {
            'REQUEST_METHOD': head.method,
            'SCRIPT_NAME': '',
            'PATH_INFO': urllib.parse.unquote(raw_path),
            'QUERY_STRING': query_string,
            'SERVER_PROTOCOL': str(head.version),

            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'http',
            'wsgi.input': io.BytesIO(ByteStreamBuffers.to_bytes(req.body)),
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
        }

        for k, v in head.headers.all:
            if k == 'content-type':
                environ['CONTENT_TYPE'] = v
            elif k == 'content-length':
                environ['CONTENT_LENGTH'] = v
            else:
                ek = 'HTTP_' + k.upper().replace('-', '_')
                if (ev := environ.get(ek)) is not None:
                    v = ev + ',' + v
                environ[ek] = v

        return environ

    #

    def _run_app(self, req: FullIoPipelineHttpRequest) -> FullIoPipelineHttpResponse:
        environ = self._build_environ(req)

        #

        started_response: ta.Optional[ta.Tuple[ta.Any, ta.Any]] = None
        written: ta.List[bytes] = []

        def write(data: bytes) -> None:
            written.append(data)

        def start_response(status, headers, exc_info=None):  # noqa
            nonlocal started_response

            # Nothing is transmitted until the app returns, so the spec-permitted exc_info re-invocation may always
            # just replace the buffered response rather than having to re-raise.
            if exc_info is None:
                check.none(started_response)

            started_response = (status, headers)

            return write

        #

        ret = self._app(environ, start_response)

        #

        chunks: ta.List[bytes] = []
        try:
            if isinstance(ret, bytes):
                # Not conforming - iterating bytes yields ints, not chunks - but historically accepted here.
                chunks.append(ret)

            else:
                for chunk in ret:
                    # Anything handed to write() before this chunk was produced must precede it.
                    chunks.extend(written)
                    del written[:]

                    chunks.append(chunk)

        finally:
            if (close := getattr(ret, 'close', None)) is not None:
                close()

        chunks.extend(written)

        #

        status, headers = check.not_none(started_response)
        status_code_str, _, status_reason = status.partition(' ')
        status_code = int(status_code_str)

        #

        return FullIoPipelineHttpResponse(
            head=IoPipelineHttpResponseHead(
                status=status_code,
                reason=status_reason,
                headers=HttpHeaders(headers),
            ),
            body=b''.join(chunks),
        )

    #

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)

            IoPipelineFlow.maybe_ready_for_input(ctx)

            return

        if not isinstance(msg, FullIoPipelineHttpRequest):
            ctx.feed_in(msg)
            return

        #

        resp = self._run_app(msg)

        #

        ctx.feed_out(resp)
        ctx.feed_out(IoPipelineMessages.FinalOutput())
