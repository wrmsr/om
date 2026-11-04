# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import dataclasses as dc
import math
import typing as ta


##


def _rpc_config_check_opt_timeout(v: ta.Optional[float]) -> None:
    if v is not None and (not math.isfinite(v) or v <= 0.):
        raise ValueError(f'timeout must be a positive finite number or None: {v!r}')


def _rpc_config_check_opt_limit(v: ta.Optional[int]) -> None:
    if v is not None and v < 1:
        raise ValueError(f'limit must be a positive integer or None: {v!r}')


@dc.dataclass(frozen=True)
class RpcConfig:
    """
    Every knob for an rpc pipeline and the connection driving it, from wire framing up through session policy. All
    timeouts are in seconds, and a value of None disables the corresponding timeout or limit.

    The defaults suit the toolbox's home use: two ends of the same code, over a stream the harness owns, exchanging
    requests which may legitimately run for a long time. In particular no request timeout is applied by default.
    """

    ##
    # wire

    # Enforced on both received and sent frames, excluding the length prefix. An oversized received frame is fatal to
    # the connection, as the stream cannot be resynchronized; an oversized sent message fails only that message.
    max_frame_bytes: int = 16 * 1024 * 1024

    ##
    # outbound requests

    default_request_timeout_s: ta.Optional[float] = None
    max_pending_outbound: ta.Optional[int] = 1024

    # Whether abandoning a sent request - because it timed out or its caller gave up - also sends the peer a cancel
    # envelope, so it may stop handling it.
    cancel_abandoned_requests: bool = True

    default_ping_timeout_s: ta.Optional[float] = 10.

    ##
    # inbound requests

    # How long the host may take to answer an inbound request before the session answers it with an error itself.
    inbound_handling_timeout_s: ta.Optional[float] = None

    max_inflight_inbound: ta.Optional[int] = 1024

    # What to do when the in-flight limit is reached: 'reject' answers further requests with a `busy` error
    # immediately, 'pause' stops reading from the transport until in-flight requests complete. Pausing is only safe for
    # pure server roles - a session which also sends requests can deadlock waiting for responses it has stopped
    # reading.
    inflight_limit_policy: ta.Literal['reject', 'pause'] = 'reject'

    ##
    # connection

    # Closes the connection if no complete envelope is received or sent for this long while nothing is in flight.
    idle_timeout_s: ta.Optional[float] = None

    # Keepalive: after this long without receiving anything, send a ping; if nothing at all is received within
    # `keepalive_timeout_s` of that, fail the connection. Both None means no keepalive handler is installed.
    keepalive_interval_s: ta.Optional[float] = None
    keepalive_timeout_s: ta.Optional[float] = None

    # Fails the connection if output cannot be flushed to the transport within this long.
    write_timeout_s: ta.Optional[float] = 30.

    # How long a graceful close waits for in-flight inbound requests to be answered before giving up on them.
    close_drain_timeout_s: ta.Optional[float] = 10.

    ##
    # policies

    # A response whose id matches no pending request. Late responses to timed-out or cancelled requests are expected,
    # so the default is to drop them.
    on_unmatched_response: ta.Literal['ignore', 'close'] = 'ignore'

    # What to do when the peer closes its side of the transport while inbound requests are in flight: 'close' aborts
    # them immediately, 'drain' waits for them to be answered (up to close_drain_timeout_s) so the responses still reach
    # a half-closed peer.
    on_peer_eof: ta.Literal['close', 'drain'] = 'close'

    # Whether inbound requests aborted by a graceful close or handling timeout are answered with an error response
    # before the connection closes.
    respond_to_aborted_inbound: bool = True

    ##
    # errors

    # Whether handler exceptions are reported to the peer with their traceback, bounded by `max_traceback_chars`.
    include_tracebacks: bool = True
    max_traceback_chars: int = 64 * 1024

    ##

    def __post_init__(self) -> None:
        if self.max_frame_bytes < 1:
            raise ValueError(self.max_frame_bytes)

        _rpc_config_check_opt_timeout(self.default_request_timeout_s)
        _rpc_config_check_opt_limit(self.max_pending_outbound)
        _rpc_config_check_opt_timeout(self.default_ping_timeout_s)

        _rpc_config_check_opt_timeout(self.inbound_handling_timeout_s)
        _rpc_config_check_opt_limit(self.max_inflight_inbound)
        if self.inflight_limit_policy not in ('reject', 'pause'):
            raise ValueError(self.inflight_limit_policy)

        _rpc_config_check_opt_timeout(self.idle_timeout_s)
        _rpc_config_check_opt_timeout(self.keepalive_interval_s)
        _rpc_config_check_opt_timeout(self.keepalive_timeout_s)
        if (self.keepalive_interval_s is None) != (self.keepalive_timeout_s is None):
            raise ValueError('keepalive_interval_s and keepalive_timeout_s must be set together')
        _rpc_config_check_opt_timeout(self.write_timeout_s)
        _rpc_config_check_opt_timeout(self.close_drain_timeout_s)

        if self.on_unmatched_response not in ('ignore', 'close'):
            raise ValueError(self.on_unmatched_response)
        if self.on_peer_eof not in ('close', 'drain'):
            raise ValueError(self.on_peer_eof)

        if self.max_traceback_chars < 0:
            raise ValueError(self.max_traceback_chars)

    def update(self, **kwargs: ta.Any) -> 'RpcConfig':
        return dc.replace(self, **kwargs)

    DEFAULT: ta.ClassVar['RpcConfig']


RpcConfig.DEFAULT = RpcConfig()
