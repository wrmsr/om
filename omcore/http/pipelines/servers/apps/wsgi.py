# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import collections
import dataclasses as dc
import enum
import io
import sys
import typing as ta
import urllib.parse

from .....io.pipelines.core import IoPipelineHandler
from .....io.pipelines.core import IoPipelineHandlerContext
from .....io.pipelines.core import IoPipelineHandlerNotification
from .....io.pipelines.core import IoPipelineHandlerNotifications
from .....io.pipelines.core import IoPipelineMessages
from .....io.pipelines.flow.types import IoPipelineFlow
from .....io.pipelines.flow.types import IoPipelineFlowMessages
from .....io.pipelines.yielding import CountingIoPipelineYieldPolicy
from .....io.pipelines.yielding import IoPipelineYieldPolicy
from .....io.streambufs.utils import ByteStreamBuffers
from .....lite.check import check
from ....headers import HttpHeaders
from ...bodymodes import IoPipelineHttpBodyMode
from ...requests import FullIoPipelineHttpRequest
from ...responses import IoPipelineHttpResponseBodyData
from ...responses import IoPipelineHttpResponseEnd
from ...responses import IoPipelineHttpResponseHead


##


@dc.dataclass(frozen=True)
class IoPipelineWsgiSpec:
    app: ta.Any
    host: str = '127.0.0.1'
    port: int = 8087


##


@dc.dataclass(frozen=True)
class IoPipelineWsgiConfig:
    DEFAULT: ta.ClassVar['IoPipelineWsgiConfig']

    # How much of the app's iterable to consume before deferring back to the driver. Note that this bounds only how
    # many chunks are *attempted* per turn - see the WsgiIoPipelineHandler docstring on blocking apps.
    yield_policy: ta.Optional[IoPipelineYieldPolicy] = None

    DEFAULT_YIELD_POLICY: ta.ClassVar[IoPipelineYieldPolicy] = CountingIoPipelineYieldPolicy(1)

    def resolve_yield_policy(self) -> IoPipelineYieldPolicy:
        if (yp := self.yield_policy) is not None:
            return yp
        return self.DEFAULT_YIELD_POLICY


IoPipelineWsgiConfig.DEFAULT = IoPipelineWsgiConfig()


##


class _IoPipelineWsgiResponseStream:
    """
    Drives one WSGI app invocation, pulling its iterable lazily.

    PEP 3333 requires the header block to be withheld until the first non-empty chunk, which is what makes the
    `exc_info` re-invocation of `start_response` meaningful: until then a failing app may still replace the response
    wholesale.
    """

    def __init__(
            self,
            ctx: IoPipelineHandlerContext,
            app: ta.Any,
            req: FullIoPipelineHttpRequest,
            config: IoPipelineWsgiConfig,
            *,
            output_writable: bool = True,
    ) -> None:
        super().__init__()

        self._ctx = ctx
        self._config = config
        self._yield_policy = config.resolve_yield_policy()

        self._output_writable = output_writable

        self._started_response: ta.Optional[ta.Tuple[ta.Any, ta.Any]] = None
        self._written: ta.Deque[bytes] = collections.deque()

        self._head_sent = False
        self._it: ta.Optional[ta.Iterator[ta.Any]] = None
        self._exhausted = False
        self._ret: ta.Any = None

        self._ret = app(self._build_environ(req), self._start_response)

    #

    class State(enum.Enum):
        STREAMING = 'streaming'
        FINISHED = 'finished'
        CLOSED = 'closed'

    _state: State = State.STREAMING

    @property
    def state(self) -> State:
        return self._state

    @property
    def output_writable(self) -> bool:
        return self._output_writable

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

    def _write(self, data: bytes) -> None:
        # PEP 3333 says write() should transmit immediately. Buffering until the next pump step instead keeps the
        # ordering guarantee against the iterable without feeding outbound from inside the app's own call stack.
        self._written.append(data)

    def _start_response(self, status, headers, exc_info=None):  # noqa
        if exc_info is not None:
            try:
                if self._head_sent:
                    # Too late to replace anything - the peer already has the header block.
                    raise exc_info[1].with_traceback(exc_info[2])
            finally:
                exc_info = None

        elif self._started_response is not None:
            raise RuntimeError('start_response called twice without exc_info')

        self._started_response = (status, headers)

        return self._write

    #

    def _has_flow(self) -> bool:
        return self._ctx.services.find(IoPipelineFlow) is not None

    def _make_head(self) -> IoPipelineHttpResponseHead:
        status, headers = check.not_none(self._started_response)
        status_code_str, _, status_reason = status.partition(' ')

        hs = HttpHeaders(headers)

        # The app declares its own framing. With neither a length nor chunked coding the body can only be delimited by
        # closing the connection, so say so rather than leaving the peer to guess.
        if not (
                'content-length' in hs or
                IoPipelineHttpBodyMode.is_chunked_transfer_encoding(hs)
        ):
            hs = hs.update(('Connection', 'close'), if_present='skip')

        return IoPipelineHttpResponseHead(
            status=int(status_code_str),
            reason=status_reason,
            headers=hs,
        )

    def _emit_head(self, out: ta.List[ta.Any]) -> None:
        if self._head_sent:
            return

        self._head_sent = True
        out.append(self._make_head())

    def _emit_data(self, out: ta.List[ta.Any], data: ta.Any) -> None:
        if not len(data):
            return

        self._emit_head(out)
        out.append(IoPipelineHttpResponseBodyData(data))

    def _feed_out(self, out: ta.List[ta.Any]) -> None:
        if not out:
            return

        if self._has_flow():
            # Nothing may follow FinalOutput at the terminal, so the fence goes just before it.
            if out and isinstance(out[-1], IoPipelineMessages.FinalOutput):
                out.insert(len(out) - 1, IoPipelineFlowMessages.FlushOutput())
            else:
                out.append(IoPipelineFlowMessages.FlushOutput())

        for msg in out:
            self._ctx.feed_out(msg)

    #

    def _take_written(self) -> ta.List[ta.Any]:
        out = list(self._written)
        self._written.clear()
        return out

    def _next_units(self) -> ta.Optional[ta.List[ta.Any]]:
        """Returns the next data to emit, in order, or none once the app is exhausted."""

        # Anything already handed to write() goes out before we pull again.
        if self._written:
            return self._take_written()

        if self._exhausted:
            return None

        if (it := self._it) is None:
            ret = self._ret
            if isinstance(ret, (bytes, bytearray)):
                # Not conforming - iterating bytes yields ints, not chunks - but historically accepted here.
                self._it = it = iter([bytes(ret)])
            else:
                self._it = it = iter(ret)

        try:
            chunk = next(it)
        except StopIteration:
            self._exhausted = True
            # A trailing write() still owes its data.
            return self._take_written() or None

        # write() calls made while producing this chunk precede it.
        units = self._take_written()
        units.append(chunk)
        return units

    def _finish(self, out: ta.List[ta.Any]) -> None:
        # An app which produced nothing still owes a response.
        self._emit_head(out)

        out.append(IoPipelineHttpResponseEnd())
        out.append(IoPipelineMessages.FinalOutput())

        self._state = _IoPipelineWsgiResponseStream.State.FINISHED

    def pump(self, ctx: IoPipelineHandlerContext) -> None:
        self._ctx = ctx

        if self._state is not _IoPipelineWsgiResponseStream.State.STREAMING:
            return

        should_yield = self._yield_policy.new_turn()

        out: ta.List[ta.Any] = []
        want_defer = False
        finished = False
        try:
            while True:
                if not self._output_writable:
                    # Parked - resumption comes from ReadyForOutput, not from a deferral.
                    break

                if should_yield():
                    want_defer = True
                    break

                units = self._next_units()
                if units is None:
                    self._finish(out)
                    finished = True
                    break

                for unit in units:
                    self._emit_data(out, unit)

        except BaseException:
            self.close()
            raise

        finally:
            self._feed_out(out)

        # After the data, so the driver hands this turn's bytes to the transport before resuming us.
        if want_defer:
            ctx.defer(self._on_deferred)

        if finished:
            self.close()

    def _on_deferred(self, ctx: IoPipelineHandlerContext) -> None:
        self.pump(ctx)

    #

    def on_output_writability(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        was_writable = self._output_writable
        self._output_writable = isinstance(msg, IoPipelineFlowMessages.ReadyForOutput)

        if (
                self._output_writable and
                not was_writable and
                self._state is _IoPipelineWsgiResponseStream.State.STREAMING
        ):
            self.pump(ctx)

    def close(self) -> None:
        if self._state is _IoPipelineWsgiResponseStream.State.CLOSED:
            return
        self._state = _IoPipelineWsgiResponseStream.State.CLOSED

        if (close := getattr(self._ret, 'close', None)) is not None:
            close()


##


class WsgiIoPipelineHandler(IoPipelineHandler):
    """
    Runs a WSGI app, streaming its response.

    The app's iterable is pulled lazily and emitted as Head / BodyData* / End, deferring back to the driver between
    chunks so that other pipeline work interleaves, and parking entirely while the transport is unwritable.

    Framing is the app's to declare: a Content-Length or chunked Transfer-Encoding is honored as given, and a response
    with neither is close-delimited (and marked `Connection: close`). A chunked app requires an
    IoPipelineHttpResponseChunker in the pipeline to do the framing.

    NOTE: chunks only actually reach the transport as they are produced when an IoPipelineFlow service is present.
    FlushOutput is a flow message and is only emitted when one is, and without it downstream buffering (the chunker
    especially) coalesces the whole body before releasing any of it - correct, but not streamed.

    NOTE: this does not make a blocking app concurrent, and cannot. A WSGI app is a plain call returning an iterable,
    so both the call itself and each `next()` on the iterable run to completion on the driver's thread - the only
    suspension points available are *between* chunks. Deferring bounds how much work is attempted per turn; it cannot
    interrupt work in progress. An app that blocks on IO will stall the driver (and, under the asyncio driver, the
    whole event loop) for the duration. Host such apps with a thread per connection.
    """

    def __init__(
            self,
            app: ta.Any,
            *,
            config: IoPipelineWsgiConfig = IoPipelineWsgiConfig.DEFAULT,
    ) -> None:
        super().__init__()

        self._app = app
        self._config = config

        self._stream: ta.Optional[_IoPipelineWsgiResponseStream] = None
        self._output_writable = True

    #

    def notify(self, ctx: IoPipelineHandlerContext, no: IoPipelineHandlerNotification) -> None:
        if isinstance(no, IoPipelineHandlerNotifications.Removed):
            self._close_stream()

    def _close_stream(self) -> None:
        if (stream := self._stream) is not None:
            self._stream = None
            stream.close()

    def _maybe_reset_stream(self) -> None:
        if (stream := self._stream) is not None and stream.state is not _IoPipelineWsgiResponseStream.State.STREAMING:
            self._stream = None

    #

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, (
                IoPipelineFlowMessages.ReadyForOutput,
                IoPipelineFlowMessages.PauseOutput,
        )):
            self._output_writable = isinstance(msg, IoPipelineFlowMessages.ReadyForOutput)
            if (stream := self._stream) is not None:
                stream.on_output_writability(ctx, msg)
                self._maybe_reset_stream()
            ctx.feed_in(msg)
            return

        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)

            IoPipelineFlow.maybe_ready_for_input(ctx)

            return

        if isinstance(msg, IoPipelineMessages.FinalInput):
            # The peer is gone; whatever the app has left to say has nowhere to go.
            self._close_stream()
            ctx.feed_in(msg)
            return

        if not isinstance(msg, FullIoPipelineHttpRequest):
            ctx.feed_in(msg)
            return

        #

        check.none(self._stream)

        self._stream = stream = _IoPipelineWsgiResponseStream(
            ctx,
            self._app,
            msg,
            self._config,
            output_writable=self._output_writable,
        )

        try:
            stream.pump(ctx)
        finally:
            self._maybe_reset_stream()
