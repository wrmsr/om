import math
import typing as ta

from .... import dataclasses as dc
from ..parsing import ParseOptions


##


def _check_opt_timeout(v: float | None) -> None:
    if v is not None and (not math.isfinite(v) or v <= 0.):
        raise ValueError(f'timeout must be a positive finite number or None: {v!r}')


def _check_opt_limit(v: int | None) -> None:
    if v is not None and v < 1:
        raise ValueError(f'limit must be a positive integer or None: {v!r}')


@dc.dataclass(frozen=True, kw_only=True)
class JsonrpcPipelineConfig:
    """
    Every knob for a JSON-RPC pipeline, from wire framing up through session policy. All timeouts are in seconds and a
    value of None disables the corresponding timeout or limit.
    """

    ##
    # wire

    framing: ta.Literal['ndjson', 'content-length'] = 'ndjson'

    # Enforced on both received and sent frames. An oversized received frame is fatal to the connection, as the stream
    # cannot be resynchronized; an oversized sent message fails only that message.
    max_frame_bytes: int = 16 * 1024 * 1024

    parse_options: ParseOptions = ParseOptions.DEFAULT

    ##
    # batches

    # Received batches are dispatched item by item and answered with a single batch response. When disabled, a received
    # batch is answered with a single Invalid Request response.
    accept_batches: bool = True
    max_batch_size: int | None = 64

    ##
    # outbound requests

    default_request_timeout_s: float | None = 60.
    max_pending_outbound: int | None = 1024

    ##
    # inbound requests

    # How long the host may take to answer an inbound request before the session answers it with an error itself.
    inbound_handling_timeout_s: float | None = None

    max_inflight_inbound: int | None = 1024

    # What to do when the in-flight limit is reached: 'reject' answers further requests with an error immediately,
    # 'pause' stops reading from the transport until in-flight requests complete. Pausing is only safe for pure server
    # roles - a session which also sends requests can deadlock waiting for responses it has stopped reading.
    inflight_limit_policy: ta.Literal['reject', 'pause'] = 'reject'

    ##
    # connection

    # Closes the connection if no complete message is received or sent for this long.
    idle_timeout_s: float | None = None

    # Fails the connection if output cannot be flushed to the transport within this long.
    write_timeout_s: float | None = 30.

    # How long a graceful close waits for in-flight inbound requests to be answered before giving up on them.
    close_drain_timeout_s: float | None = 10.

    ##
    # policies

    # A response whose id matches no pending request. Late responses to timed-out requests are expected, so the
    # default is to drop them.
    on_unmatched_response: ta.Literal['ignore', 'close'] = 'ignore'

    # An unparseable or malformed received message. The spec calls for an error response; 'close' instead treats it
    # as fatal.
    on_invalid_message: ta.Literal['respond', 'close'] = 'respond'

    # Closes the connection after this many consecutive invalid messages regardless of the above, so a peer sending
    # garbage cannot spin the connection forever.
    max_consecutive_invalid: int | None = 8

    # What to do when the peer closes its side of the transport while inbound requests are in flight: 'close' aborts
    # them immediately, 'drain' waits for them to be answered (up to close_drain_timeout_s) so the responses still reach
    # a half-closed peer.
    on_peer_eof: ta.Literal['close', 'drain'] = 'close'

    # Whether inbound requests aborted by a graceful close or handling timeout are answered with an error response
    # before the connection closes.
    respond_to_aborted_inbound: bool = True

    ##

    def __post_init__(self) -> None:
        if self.framing not in ('ndjson', 'content-length'):
            raise ValueError(self.framing)
        if self.max_frame_bytes < 1:
            raise ValueError(self.max_frame_bytes)

        _check_opt_limit(self.max_batch_size)

        _check_opt_timeout(self.default_request_timeout_s)
        _check_opt_limit(self.max_pending_outbound)

        _check_opt_timeout(self.inbound_handling_timeout_s)
        _check_opt_limit(self.max_inflight_inbound)
        if self.inflight_limit_policy not in ('reject', 'pause'):
            raise ValueError(self.inflight_limit_policy)

        _check_opt_timeout(self.idle_timeout_s)
        _check_opt_timeout(self.write_timeout_s)
        _check_opt_timeout(self.close_drain_timeout_s)

        if self.on_unmatched_response not in ('ignore', 'close'):
            raise ValueError(self.on_unmatched_response)
        if self.on_invalid_message not in ('respond', 'close'):
            raise ValueError(self.on_invalid_message)
        _check_opt_limit(self.max_consecutive_invalid)
        if self.on_peer_eof not in ('close', 'drain'):
            raise ValueError(self.on_peer_eof)

    DEFAULT: ta.ClassVar[JsonrpcPipelineConfig]


JsonrpcPipelineConfig.DEFAULT = JsonrpcPipelineConfig()
