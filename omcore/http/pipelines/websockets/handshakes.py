# ruff: noqa: UP006 UP007 UP045
# @om-lite
import base64
import hashlib
import os
import typing as ta

from ....io.pipelines.core import IoPipelineHandler
from ....io.pipelines.core import IoPipelineHandlerContext
from ....lite.check import check
from ....lite.namespaces import NamespaceClass
from ...headers import HttpHeaders
from ..clients.requests import IoPipelineHttpRequestEncoder
from ..clients.responses import IoPipelineHttpResponseDecoder
from ..requests import FullIoPipelineHttpRequest
from ..requests import IoPipelineHttpRequestEnd
from ..requests import IoPipelineHttpRequestHead
from ..responses import FullIoPipelineHttpResponse
from ..responses import IoPipelineHttpResponseEnd
from ..responses import IoPipelineHttpResponseHead
from ..servers.requests import IoPipelineHttpRequestDecoder
from ..servers.responses import IoPipelineHttpResponseEncoder
from .objects import IoPipelineWebsocketOpen


##


class IoPipelineWebsocketHandshakes(NamespaceClass):
    WS_GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

    @classmethod
    def compute_accept_for_key(cls, key_b64: str) -> str:
        s = (key_b64 + cls.WS_GUID).encode('ascii')
        d = hashlib.sha1(s).digest()  # noqa
        return base64.b64encode(d).decode('ascii')


class IoPipelineWebsocketServerUpgradeHandler(IoPipelineHandler):
    """
    Detects and accepts an HTTP/1.1 Websocket Upgrade request, responds with 101, and emits WsOpen. After upgrade,
    passes through subsequent messages unchanged.
    """

    def __init__(
            self,
            *,
            subprotocols: ta.Sequence[str] = (),
    ) -> None:
        super().__init__()

        self._subprotocols = subprotocols

    _upgraded: bool = False

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if self._upgraded:
            if isinstance(msg, IoPipelineHttpRequestEnd):
                return
            ctx.feed_in(msg)
            return

        if isinstance(msg, IoPipelineHttpRequestHead):
            if not self._is_ws_upgrade_request(msg.headers):
                ctx.feed_in(msg)
                return

            key = msg.headers.single.get('Sec-Websocket-Key')

            accept = IoPipelineWebsocketHandshakes.compute_accept_for_key(check.not_none(key))

            chosen_proto: ta.Optional[str] = None
            if self._subprotocols:
                # Simple selection: first matching requested subprotocol (if present). Per RFC 6455 §4.1 the client may
                # split its requested subprotocols across multiple header lines as well as comma-separating them.
                for req_subp in msg.headers.get('Sec-Websocket-Protocol', ()):
                    for s in req_subp.split(','):
                        if (s := s.strip()) and s in self._subprotocols:
                            chosen_proto = s
                            break
                    if chosen_proto is not None:
                        break

            hdrs = HttpHeaders.of(None).update(
                ('Upgrade', 'websocket'),
                ('Connection', 'Upgrade'),
                ('Sec-Websocket-Accept', accept),
                ('Sec-Websocket-Protocol', chosen_proto) if chosen_proto else ('', None),  # ignored
                if_present='skip',
            )

            resp = IoPipelineHttpResponseHead(
                status=101,
                reason='Switching Protocols',
                headers=hdrs,
            )
            ctx.feed_out(resp)

            self._upgraded = True
            ctx.defer_no_context(lambda: self._remove_http_handlers(ctx))
            ctx.feed_in(IoPipelineWebsocketOpen(subprotocol=chosen_proto))
            return

        elif isinstance(msg, FullIoPipelineHttpRequest):
            # If a handler up the chain aggregates into Full, treat the same as head - but *only* when it actually is an
            # upgrade, as unwrapping a non-upgrade Full would drop its body and its end.
            if self._is_ws_upgrade_request(msg.head.headers):
                self.inbound(ctx, msg.head)
            else:
                ctx.feed_in(msg)
            return

        ctx.feed_in(msg)

    def _is_ws_upgrade_request(self, headers: HttpHeaders) -> bool:
        # Both Upgrade and Connection are comma-separated `#`-lists - `Connection: keep-alive, Upgrade` is both legal
        # and common.
        if not headers.contains_list_value('Upgrade', 'websocket', ignore_case=True):
            return False
        if not headers.contains_list_value('Connection', 'upgrade', ignore_case=True):
            return False
        ver = headers.single.get('Sec-Websocket-Version')
        if ver != '13':
            return False
        if headers.single.get('Sec-Websocket-Key') is None:
            return False
        return True

    def _remove_http_handlers(self, ctx: IoPipelineHandlerContext) -> None:
        for ty in (
                IoPipelineHttpRequestDecoder,
                IoPipelineHttpResponseEncoder,
        ):
            for ref in ctx.pipeline.find_handlers_of_type(ty):
                ctx.pipeline.remove(ref)


class IoPipelineWebsocketClientUpgradeHandler(IoPipelineHandler):
    """
    Injects required headers in outbound HTTP request for Websocket upgrade. Validates 101 response inbound and emits
    WsOpen.
    """

    def __init__(
            self,
            *,
            host: str,
            subprotocols: ta.Sequence[str] = (),
    ) -> None:
        super().__init__()

        self._host = host
        self._subprotocols = subprotocols

    _key_b64: ta.Optional[str] = None
    _upgraded: bool = False
    _awaiting_upgrade_end: bool = False

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if self._upgraded:
            ctx.feed_out(msg)
            return

        if isinstance(msg, IoPipelineHttpRequestHead):
            ctx.feed_out(self._with_ws_upgrade_headers(msg))
            return

        elif isinstance(msg, FullIoPipelineHttpRequest):
            new_head = self._with_ws_upgrade_headers(msg.head)
            ctx.feed_out(FullIoPipelineHttpRequest(head=new_head, body=msg.body))
            return

        ctx.feed_out(msg)

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if self._upgraded:
            if self._awaiting_upgrade_end and isinstance(msg, IoPipelineHttpResponseEnd):
                self._awaiting_upgrade_end = False
                return
            ctx.feed_in(msg)
            return

        if isinstance(msg, IoPipelineHttpResponseHead):
            if msg.status != 101:
                ctx.feed_in(msg)
                return

            check.state(self._key_b64 is not None)
            accept = msg.headers.single.get('Sec-Websocket-Accept')
            check.not_none(accept)
            check.equal(accept, IoPipelineWebsocketHandshakes.compute_accept_for_key(self._key_b64))  # type: ignore[arg-type]  # noqa

            chosen_proto = msg.headers.single.get('Sec-Websocket-Protocol')

            self._upgraded = True
            self._awaiting_upgrade_end = True
            ctx.defer_no_context(lambda: self._remove_http_handlers(ctx))
            ctx.feed_in(IoPipelineWebsocketOpen(subprotocol=chosen_proto))
            return

        elif isinstance(msg, FullIoPipelineHttpResponse):
            # Only unwrap to the head when it actually is the upgrade response - anything else (a 403 rejection with an
            # error body, say) must be forwarded intact.
            if msg.head.status == 101:
                self.inbound(ctx, msg.head)
                # The aggregated Full message subsumes the response end - there will be no separate one to consume.
                self._awaiting_upgrade_end = False
            else:
                ctx.feed_in(msg)
            return

        ctx.feed_in(msg)

    def _with_ws_upgrade_headers(self, head: IoPipelineHttpRequestHead) -> IoPipelineHttpRequestHead:
        # Reuse any key already present on the head - the recorded key must match what actually goes on the wire or the
        # accept check will reject a successful handshake.
        if (key := head.headers.single.get('Sec-Websocket-Key')) is None:
            key = base64.b64encode(os.urandom(16)).decode('ascii')
        self._key_b64 = key

        hdrs = HttpHeaders.of(head.headers).update(
            ('Host', self._host),
            ('Sec-Websocket-Version', '13'),
            ('Sec-Websocket-Key', key),
            ('Sec-Websocket-Protocol', ', '.join(self._subprotocols)) if self._subprotocols else ('', None),
            if_present='skip',
        ).update(
            # These must take effect regardless of what the head already carried - a pre-existing `Connection:
            # keep-alive` would otherwise be left un-upgraded.
            ('Upgrade', 'websocket'),
            ('Connection', 'Upgrade'),
            if_present='override',
        )

        return IoPipelineHttpRequestHead(
            method=head.method,
            target=head.target,
            headers=hdrs,
            parsed=head.parsed,
            version=head.version,
        )

    def _remove_http_handlers(self, ctx: IoPipelineHandlerContext) -> None:
        for ty in (
                IoPipelineHttpResponseDecoder,
                IoPipelineHttpRequestEncoder,
        ):
            for ref in ctx.pipeline.find_handlers_of_type(ty):
                ctx.pipeline.remove(ref)
