# ruff: noqa: UP006 UP007 UP045 UP037
# @om-lite
"""
The multiplexing handler: many streams over one parent pipeline, each stream backed by a child pipeline it drives.

The handler follows the TLS handler's turn discipline. Entry points - inbound protocol messages, open requests,
writability and flush signals, child timers, parent fence completions - only record state and then call `_turn()`.
A turn alternates two phases until quiescent:

 - PUMP establishes accepted streams, delivers queued input into children under their input flow, collects their
   output into per-stream queues, aborts failed children, and releases finished streams. It never feeds the parent.
 - EMIT is the only place the parent is fed, always in this order:

     1. completions of open requests,
     2. control output (opens, acceptances, refusals, resets, credit grants) - never gated by credit, per-stream
        backlog, or parent writability,
     3. Awaits forwarded from children,
     4. stream output, chosen by the output scheduler while the parent is writable, bounded per turn by credit and by
        the turn budget (continuing later through a parent Defer),
     5. one parent FlushOutput covering every child fence reached in this turn,
     6. a parent read request, and finally parent FinalOutput once a shutdown has drained.

A nested entry during EMIT - the parent reacting synchronously to what was fed - only records its state and marks the
turn dirty; the outer turn loops. The handler never caches its context: anything happening later reaches it through a
parent Defer, a parent-scheduled callback, or a completion listener holding the context weakly.
"""
import collections
import contextlib
import dataclasses as dc
import functools
import typing as ta
import weakref

from ....lite.check import check
from ...streambufs.segmented import SegmentedByteStreamBufferView
from ..asyncs import AsyncIoPipelineMessages
from ..core import IoPipelineHandler
from ..core import IoPipelineHandlerContext
from ..core import IoPipelineHandlerNotification
from ..core import IoPipelineHandlerNotifications
from ..core import IoPipelineMessages
from ..errors import AbortedIoPipelineError
from ..flow.types import IoPipelineFlow
from ..flow.types import IoPipelineFlowMessages
from ..yielding import IoPipelineYieldPolicy
from ..yielding import NeverIoPipelineYieldPolicy
from .adapters import IoPipelineMultiplexAdapter
from .adapters import IoPipelineMultiplexConnection
from .adapters import IoPipelineMultiplexConnectionStats
from .children import IoPipelineMultiplexChild
from .children import IoPipelineMultiplexChildConfig
from .children import IoPipelineMultiplexChildHost
from .credit import IoPipelineMultiplexCreditGrant
from .credit import IoPipelineMultiplexCreditStrategy
from .credit import StreamMultiplexCreditStrategy
from .schedulers import IoPipelineMultiplexOutputScheduler
from .schedulers import RoundRobinIoPipelineMultiplexOutputScheduler
from .streams import UNSET
from .streams import IoPipelineMultiplexOutputFence
from .streams import IoPipelineMultiplexOutputMessage
from .streams import IoPipelineMultiplexStream
from .streams import IoPipelineMultiplexStreamTable
from .types import ConnectionClosedMultiplexIoPipelineError
from .types import ControlOutputLimitMultiplexIoPipelineError
from .types import InputLimitMultiplexIoPipelineError
from .types import IoPipelineMultiplexMessages
from .types import IoPipelineMultiplexOpenedStream
from .types import IoPipelineMultiplexRefusal
from .types import IoPipelineMultiplexStreamKey
from .types import IoPipelineMultiplexStreamOpening
from .types import MultiplexStreamSpecFactory
from .types import StreamLimitMultiplexIoPipelineError
from .types import StreamRefusedMultiplexIoPipelineError
from .types import StreamResetMultiplexIoPipelineError
from .types import StreamStateMultiplexIoPipelineError
from .types import StreamTruncatedMultiplexIoPipelineError


T = ta.TypeVar('T')


##


@ta.final
@dc.dataclass(frozen=True)
class IoPipelineMultiplexConfig:
    child: IoPipelineMultiplexChildConfig = dc.field(default_factory=IoPipelineMultiplexChildConfig)

    max_local_streams: ta.Optional[int] = None
    max_remote_streams: ta.Optional[int] = None

    # The most flow-controlled cost emitted into the parent in one turn before continuing through a parent Defer. The
    # parent's driver only reports writability after processing queued output, which happens after a turn returns, so
    # without this one turn could move an unbounded amount of data into the parent's output queue.
    turn_output_budget: int = 256 * 1024

    # Additionally bounds the units of stream output per turn.
    yield_policy: ta.Optional[IoPipelineYieldPolicy] = None

    # Uncontrolled typed messages queued for one stream before further ones are refused.
    max_stream_input_messages: int = 1024

    # Control output emitted while the parent is paused before the connection is failed. Control output is never
    # gated, as gating it can deadlock a protocol, so a peer which keeps provoking replies without reading is bounded
    # here instead.
    max_control_during_pause: int = 10_000

    def __post_init__(self) -> None:
        """Validate bounds."""

        if self.turn_output_budget < 1:
            raise ValueError(self.turn_output_budget)
        if self.max_stream_input_messages < 0:
            raise ValueError(self.max_stream_input_messages)
        if self.max_control_during_pause < 1:
            raise ValueError(self.max_control_during_pause)


##


class MultiplexIoPipelineHandler(IoPipelineMultiplexChildHost, IoPipelineHandler):
    """
    Hosts many streams over one parent pipeline, each driven as a child pipeline, for a protocol given by `adapter`.

    Normally placed innermost, inside the handlers decoding and encoding the protocol's frames. Remote streams get
    their child spec from `spec_factory`, which may refuse them; local streams are opened by feeding it a
    `MultiplexMessages.OpenStream`.
    """

    def __init__(
            self,
            adapter: IoPipelineMultiplexAdapter,
            spec_factory: MultiplexStreamSpecFactory,
            *,
            config: ta.Optional[IoPipelineMultiplexConfig] = None,
            credit: ta.Optional[IoPipelineMultiplexCreditStrategy] = None,
            scheduler: ta.Optional[IoPipelineMultiplexOutputScheduler] = None,
    ) -> None:
        super().__init__()

        if config is None:
            config = IoPipelineMultiplexConfig()
        self._config = config
        self._adapter = adapter
        self._spec_factory = spec_factory

        if credit is None:
            credit = StreamMultiplexCreditStrategy()
        self._credit = credit
        if scheduler is None:
            scheduler = RoundRobinIoPipelineMultiplexOutputScheduler()
        self._scheduler = scheduler
        self._yield_policy = config.yield_policy or NeverIoPipelineYieldPolicy()

        self._table = IoPipelineMultiplexStreamTable(
            max_local=config.max_local_streams,
            max_remote=config.max_remote_streams,
        )
        self._children: ta.Dict[IoPipelineMultiplexStreamKey, IoPipelineMultiplexChild] = {}

        # Accepted or confirmed streams whose child is created in the next pump.
        self._pending_establish: ta.Dict[IoPipelineMultiplexStreamKey, ta.Tuple[ta.Any, ta.Optional[IoPipelineMultiplexMessages.OpenStream]]] = {}  # noqa
        # Explicitly opened local streams awaiting the peer's confirmation.
        self._pending_opens: ta.Dict[IoPipelineMultiplexStreamKey, IoPipelineMultiplexMessages.OpenStream] = {}
        # Streams closed by the peer while their child still runs: its further output is discarded.
        self._remote_closed: ta.Set[IoPipelineMultiplexStreamKey] = set()
        # Streams whose finish was emitted, awaiting the adapter's decision.
        self._finished_hooks: ta.List[IoPipelineMultiplexStreamKey] = []
        # Messages to feed into streams' pipelines at their boundary.
        self._pending_feeds: ta.List[IoPipelineMultiplexMessages.FeedStream] = []

        self._control_q: ta.Deque[ta.Any] = collections.deque()
        # The connection error of a failed connection: emitted ahead of its FinalOutput, outside the pause bound.
        self._goodbye_q: ta.Deque[ta.Any] = collections.deque()
        self._completions: ta.Deque[ta.Tuple[IoPipelineMessages.Completable, ta.Any, ta.Optional[BaseException]]] = collections.deque()  # noqa
        self._child_awaits: ta.Deque[ta.Tuple[IoPipelineMultiplexChild, AsyncIoPipelineMessages.Await]] = collections.deque()  # noqa
        # Awaits forwarded to the parent on behalf of each stream, failed when the stream ends so the parent's driver
        # cancels the work it started for them.
        self._parent_awaits: ta.Dict[IoPipelineMultiplexStreamKey, ta.List[AsyncIoPipelineMessages.Await]] = {}
        self._flush_fences: ta.List[ta.Tuple[IoPipelineMultiplexChild, IoPipelineMessages.Completable, str]] = []

        self._parent_writable = True
        self._control_during_pause = 0
        self._received_since_flush = False
        # While a parent read batch is in progress, input is only queued: delivering it into children at the batch's
        # end coalesces what arrived together, as the reference drivers batch a read. A batch ends at FlushInput or, for
        # input which arrives without one, when a parent Defer requested at its start runs.
        self._parent_batch_open = False
        self._batch_defer_pending = False
        self._want_parent_read = False
        self._input_ended = False
        self._shutting_down = False
        self._failed: ta.Optional[BaseException] = None
        self._final_output_sent = False
        self._removed = False

        self._continuation_pending = False
        self._in_turn = False
        self._dirty = False

        # The stream output budget and yield policy apply to a whole turn, across its loops.
        self._turn_budget = 0
        self._turn_should_yield: ta.Callable[[], bool] = lambda: False

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{len(self._table)}>'

    ##
    # inspection

    @property
    def config(self) -> IoPipelineMultiplexConfig:
        return self._config

    @property
    def adapter(self) -> IoPipelineMultiplexAdapter:
        return self._adapter

    @property
    def credit(self) -> IoPipelineMultiplexCreditStrategy:
        return self._credit

    @property
    def streams(self) -> IoPipelineMultiplexStreamTable:
        return self._table

    def child_pipeline(self, key: IoPipelineMultiplexStreamKey) -> ta.Optional[ta.Any]:
        if (child := self._children.get(key)) is None:
            return None
        return child.pipeline

    @property
    def stats(self) -> IoPipelineMultiplexConnectionStats:
        return IoPipelineMultiplexConnectionStats(
            streams=self._table.stats,
            control_during_pause=self._control_during_pause,
            queued_input={s.key: (s.in_cost, s.in_messages) for s in self._table},
        )

    @property
    def accepting(self) -> bool:
        return not (
            self._shutting_down or
            self._failed is not None or
            self._input_ended or
            self._final_output_sent or
            self._removed
        )

    ##
    # adapter facade

    @ta.final
    class _Connection(IoPipelineMultiplexConnection):
        def __init__(self, h: 'MultiplexIoPipelineHandler') -> None:
            super().__init__()

            self._h: ta.Optional['MultiplexIoPipelineHandler'] = h

        @property
        def h(self) -> 'MultiplexIoPipelineHandler':
            return check.not_none(self._h, 'MultiplexConnection used outside of its adapter call')

        def get(self, key: IoPipelineMultiplexStreamKey) -> ta.Optional[IoPipelineMultiplexStream]:
            return self.h._table.get(key)  # noqa

        def streams(self) -> ta.Sequence[IoPipelineMultiplexStream]:
            return list(self.h._table)  # noqa

        @property
        def stats(self) -> IoPipelineMultiplexConnectionStats:
            return self.h.stats

        @property
        def accepting(self) -> bool:
            return self.h.accepting

        def send(self, *msgs: ta.Any) -> None:
            self.h._control_q.extend(msgs)  # noqa

        def open_remote(
                self,
                key: IoPipelineMultiplexStreamKey,
                info: ta.Any = None,
                *,
                recv_window: int,
                send_credit: int = 0,
                weight: int = 1,
        ) -> ta.Optional[IoPipelineMultiplexStream]:
            return self.h._open_remote(  # noqa
                key,
                info,
                recv_window=recv_window,
                send_credit=send_credit,
                weight=weight,
            )

        def confirm(self, key: IoPipelineMultiplexStreamKey, *, send_credit: int = 0) -> None:
            self.h._confirm(key, send_credit=send_credit)  # noqa

        def refuse(self, key: IoPipelineMultiplexStreamKey, reason: ta.Any = None) -> None:
            self.h._refuse(key, reason)  # noqa

        def data(self, key: IoPipelineMultiplexStreamKey, data: ta.Any, *, cost: ta.Optional[int] = None) -> None:
            self.h._data(key, data, cost=cost)  # noqa

        def discard(self, cost: int) -> None:
            h = self.h
            h._queue_grants(h._credit.discard_receive(cost))  # noqa

        def message(self, key: IoPipelineMultiplexStreamKey, msg: ta.Any, *, cost: int = 0) -> None:
            self.h._message(key, msg, cost=cost)  # noqa

        def end(self, key: IoPipelineMultiplexStreamKey) -> None:
            self.h._end(key)  # noqa

        def close(self, key: IoPipelineMultiplexStreamKey) -> None:
            self.h._close(key)  # noqa

        def reset(self, key: IoPipelineMultiplexStreamKey, reason: ta.Any = None) -> None:
            h = self.h
            h._reset_stream(h._table[key], reason, by='remote')  # noqa

        def grant(self, key: ta.Optional[IoPipelineMultiplexStreamKey], delta: int) -> None:
            self.h._credit.grant_send(key, delta)  # noqa

        def adjust_all(self, delta: int) -> None:
            self.h._credit.adjust_all_send(delta)  # noqa

        def reset_local(self, key: IoPipelineMultiplexStreamKey, reason: ta.Any = None) -> None:
            h = self.h
            h._reset_stream(h._table[key], reason, by='local', encode=True)  # noqa

        def set_limits(
                self,
                *,
                max_local: ta.Optional[int] = UNSET,
                max_remote: ta.Optional[int] = UNSET,
        ) -> None:
            self.h._table.set_limits(max_local=max_local, max_remote=max_remote)  # noqa

        def set_weight(self, key: IoPipelineMultiplexStreamKey, weight: int) -> None:
            h = self.h
            h._table[key]  # noqa  # raises UnknownStreamMultiplexError
            h._scheduler.set_weight(key, weight)  # noqa

        def begin_shutdown(self) -> None:
            self.h._shutting_down = True  # noqa

        def fail(self, exc: BaseException) -> None:
            self.h._fail(exc)  # noqa

    @contextlib.contextmanager
    def _connection(self) -> ta.Iterator[IoPipelineMultiplexConnection]:
        conn = MultiplexIoPipelineHandler._Connection(self)
        try:
            yield conn
        finally:
            conn._h = None  # noqa

    ##
    # entry points (apply)

    def notify(self, ctx: IoPipelineHandlerContext, no: IoPipelineHandlerNotification) -> None:
        if isinstance(no, IoPipelineHandlerNotifications.Removed):
            self._removed = True
            self._teardown(ConnectionClosedMultiplexIoPipelineError('multiplexing handler removed'))

    def on_child_activity(self, ctx: IoPipelineHandlerContext) -> None:
        if not ctx.invalidated:
            self._turn(ctx)

    @staticmethod
    def _resume(ctx: IoPipelineHandlerContext) -> None:
        h = check.isinstance(ctx.handler, MultiplexIoPipelineHandler)
        h._continuation_pending = False  # noqa
        h._turn(ctx)  # noqa

    @staticmethod
    def _end_batch(ctx: IoPipelineHandlerContext) -> None:
        h = check.isinstance(ctx.handler, MultiplexIoPipelineHandler)
        h._batch_defer_pending = False  # noqa
        if h._parent_batch_open:  # noqa
            h._parent_batch_open = False  # noqa
            h._turn(ctx)  # noqa

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            self._want_parent_read = True

        elif isinstance(msg, IoPipelineMessages.FinalInput):
            ctx.feed_in(msg)
            self._parent_batch_open = False
            self._on_input_ended()

        elif isinstance(msg, IoPipelineFlowMessages.FlushInput):
            self._parent_batch_open = False
            # Request more input only after a batch we consumed something from; a decoder which consumed a batch
            # without producing anything requests more itself.
            if self._received_since_flush:
                self._received_since_flush = False
                self._want_parent_read = True

        elif isinstance(msg, IoPipelineFlowMessages.PauseOutput):
            self._parent_writable = False

        elif isinstance(msg, IoPipelineFlowMessages.ReadyForOutput):
            self._parent_writable = True
            self._control_during_pause = 0

        elif isinstance(msg, IoPipelineMessages.Error):
            self._fail(msg.exc)

        elif isinstance(msg, IoPipelineMultiplexMessages.OpenStream):
            self._open_local(msg)

        elif isinstance(msg, IoPipelineMultiplexMessages.Shutdown):
            self._on_shutdown()

        elif isinstance(msg, IoPipelineMultiplexMessages.FeedStream):
            self._pending_feeds.append(msg)

        else:
            self._received_since_flush = True
            if not self._parent_batch_open and not self._final_output_sent:
                self._parent_batch_open = True
                if not self._batch_defer_pending:
                    self._batch_defer_pending = True
                    ctx.defer(MultiplexIoPipelineHandler._end_batch)
            try:
                with self._connection() as conn:
                    claimed = self._adapter.inbound(conn, msg)
            except Exception as e:  # noqa
                self._fail(e)
            else:
                if not claimed:
                    ctx.feed_in(msg)
                    return

        self._turn(ctx)

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMultiplexMessages.OpenStream):
            self._open_local(msg)
            self._turn(ctx)
            return

        if isinstance(msg, IoPipelineMultiplexMessages.Shutdown):
            self._on_shutdown()
            self._turn(ctx)
            return

        if isinstance(msg, IoPipelineMultiplexMessages.FeedStream):
            self._pending_feeds.append(msg)
            self._turn(ctx)
            return

        ctx.feed_out(msg)

    ##
    # stream events

    def _guard(self, fn: ta.Callable[..., T], *args: ta.Any, default: ta.Any) -> T:
        """
        Calls into the adapter. An adapter failing fails the connection - as when decoding - and the call site
        proceeds with a value which makes it a no-op, so the turn still finishes the connection.
        """

        try:
            return fn(*args)
        except Exception as e:  # noqa
            self._fail(e)
            return default

    def _queue_grants(self, grants: ta.Iterable[IoPipelineMultiplexCreditGrant]) -> None:
        for g in grants:
            stream: ta.Optional[IoPipelineMultiplexStream] = None
            if g.key is not None:
                if not self._credit.has_stream(g.key):
                    continue
                # Nothing more will arrive on a stream the peer ended or closed: the credit stays unadvertised. One
                # whose local side finished may still receive, so its grant is offered; the adapter knows whether its
                # protocol lets it be sent (SSH may send nothing after its CLOSE, HTTP/2 may grant after END_STREAM).
                if (
                        (stream := self._table.get(g.key)) is None or
                        stream.is_terminal or
                        stream.remote_ended or
                        g.key in self._remote_closed
                ):
                    self._credit.withdraw(g.key, g.amount)
                    continue
            if frames := self._guard(self._adapter.encode_credit, stream, g.amount, default=()):
                self._control_q.extend(frames)
            else:
                # Declined: the accounting follows the wire.
                self._credit.withdraw(g.key, g.amount)

    def _discard_input(self, stream: IoPipelineMultiplexStream) -> None:
        """Drops input nothing will consume any more, returning its credit as if it had been consumed."""

        for cost in stream.clear_in():
            if self._credit.has_stream(stream.key):
                self._queue_grants(self._credit.consume_receive(stream.key, cost))

    def _fail_parent_awaits(self, key: IoPipelineMultiplexStreamKey, exc: BaseException) -> None:
        """Fails the Awaits forwarded for a stream which is ending, so the parent's driver cancels their work."""

        for pawt in self._parent_awaits.pop(key, ()):
            if not pawt.is_done():
                try:
                    pawt.set_failed(exc)
                except Exception:  # noqa
                    pass

    def _complete_later(
            self,
            msg: IoPipelineMessages.Completable,
            result: ta.Any = None,
            exc: ta.Optional[BaseException] = None,
    ) -> None:
        self._completions.append((msg, result, exc))

    def _open_local(self, msg: IoPipelineMultiplexMessages.OpenStream) -> None:
        if msg.is_done():
            return
        if not self.accepting:
            self._complete_later(
                msg,
                exc=ConnectionClosedMultiplexIoPipelineError('connection is not accepting streams'),
            )
            return
        if not self._table.can_open('local'):
            self._complete_later(
                msg,
                exc=StreamLimitMultiplexIoPipelineError('local'),
            )
            return

        try:
            with self._connection() as conn:
                params = self._adapter.open_local(conn, msg.info)
            stream = IoPipelineMultiplexStream(
                params.key,
                'local',
                info=msg.info,
                opening=params.explicit,
            )
            self._table.add(stream)
        except Exception as e:  # noqa
            self._complete_later(msg, exc=e)
            return

        self._credit.add_stream(
            stream.key,
            send_credit=params.send_credit,
            recv_window=params.recv_window,
        )
        self._scheduler.add(stream.key, weight=params.weight)
        self._control_q.extend(self._guard(self._adapter.encode_open, stream, default=()))

        if params.explicit:
            self._pending_opens[stream.key] = msg
        else:
            self._pending_establish[stream.key] = (msg.spec, msg)

    def _open_remote(
            self,
            key: IoPipelineMultiplexStreamKey,
            info: ta.Any,
            *,
            recv_window: int,
            send_credit: int,
            weight: int,
    ) -> ta.Optional[IoPipelineMultiplexStream]:
        opening = IoPipelineMultiplexStreamOpening(key, 'remote', info)

        reason: ta.Any
        if not self.accepting:
            reason = ConnectionClosedMultiplexIoPipelineError('connection is not accepting streams')
        elif not self._table.can_open('remote'):
            reason = StreamLimitMultiplexIoPipelineError('remote')
        else:
            try:
                res = self._spec_factory(opening)
            except Exception as e:  # noqa
                # An application error for one stream refuses that stream, like a child which cannot be built.
                res = IoPipelineMultiplexRefusal(e)
            if not isinstance(res, IoPipelineMultiplexRefusal):
                stream = IoPipelineMultiplexStream(key, 'remote', info=info)
                self._table.add(stream)
                self._credit.add_stream(key, send_credit=send_credit, recv_window=recv_window)
                self._scheduler.add(key, weight=weight)
                self._pending_establish[key] = (res, None)
                return stream
            reason = res.reason

        self._table.count_refused('remote')
        self._control_q.extend(self._guard(self._adapter.encode_refuse, opening, reason, default=()))
        return None

    def _confirm(self, key: IoPipelineMultiplexStreamKey, *, send_credit: int) -> None:
        stream = self._table[key]
        stream.confirm()
        if send_credit:
            self._credit.grant_send(key, send_credit)
        msg = self._pending_opens.pop(key)
        self._pending_establish[key] = (msg.spec, msg)

    def _refuse(self, key: IoPipelineMultiplexStreamKey, reason: ta.Any) -> None:
        stream = self._table[key]
        stream.refuse(reason)
        if (msg := self._pending_opens.pop(key, None)) is not None:
            self._complete_later(msg, exc=StreamRefusedMultiplexIoPipelineError(reason))

    def _data(self, key: IoPipelineMultiplexStreamKey, data: ta.Any, *, cost: ta.Optional[int]) -> None:
        stream = self._table[key]
        if cost is None:
            cost = len(data)
        if stream.is_terminal:
            # Frames in flight when the stream ended still occupied the peer's connection window.
            self._queue_grants(self._credit.discard_receive(cost))
            return
        if not stream.can_receive_data:
            raise StreamStateMultiplexIoPipelineError(
                f'stream {key!r} cannot receive data in state {stream.state.name}',
            )
        self._queue_grants(self._credit.receive(key, cost))
        if stream.local_finished or not len(data):
            # Nothing will consume it, or there is nothing to consume - an empty frame, which queued would be bounded
            # neither by the window nor by the message limit: its credit is freed at once.
            if cost:
                self._queue_grants(self._credit.consume_receive(key, cost))
            return
        stream.push_in_data(data, cost)

    def _message(self, key: IoPipelineMultiplexStreamKey, msg: ta.Any, *, cost: int) -> None:
        stream = self._table[key]
        if not stream.can_receive_message:
            raise StreamStateMultiplexIoPipelineError(
                f'stream {key!r} cannot receive messages in state {stream.state.name}',
            )
        if cost:
            self._queue_grants(self._credit.receive(key, cost))
        elif stream.in_messages >= self._config.max_stream_input_messages:
            raise InputLimitMultiplexIoPipelineError(key)
        if stream.local_finished:
            if cost:
                self._queue_grants(self._credit.consume_receive(key, cost))
            return
        stream.push_in_message(msg, cost)

    def _end(self, key: IoPipelineMultiplexStreamKey) -> None:
        stream = self._table[key]
        stream.end_remote()
        if not stream.local_finished:
            stream.push_in_end()

    def _close(self, key: IoPipelineMultiplexStreamKey) -> None:
        stream = self._table[key]
        if stream.is_terminal:
            return
        child = self._children.get(key)
        if child is None and key not in self._pending_establish:
            # Nothing was accepted: a local open still awaiting the peer's confirmation.
            if (msg := self._pending_opens.pop(key, None)) is not None:
                self._complete_later(msg, exc=StreamResetMultiplexIoPipelineError('closed', by='remote'))
            stream.close()
            return
        if child is not None and not child.is_running:
            stream.close()
            return

        # Graceful remote close: the child - built in the next pump, if the stream was accepted in this same read -
        # still receives what was queued, then FinalInput.
        if not stream.remote_ended:
            stream.end_remote()
            stream.push_in_end()
        self._remote_closed.add(key)

    def _reset_stream(
            self,
            stream: IoPipelineMultiplexStream,
            reason: ta.Any,
            *,
            by: ta.Literal['local', 'remote'],
            encode: bool = False,
            exc: ta.Optional[BaseException] = None,
    ) -> None:
        if stream.is_terminal:
            return

        key = stream.key
        if encode:
            self._control_q.extend(self._guard(self._adapter.encode_reset, stream, reason, default=()))
        stream.reset(reason, by=by)

        if exc is None:
            exc = StreamResetMultiplexIoPipelineError(reason, by=by)

        if (pe := self._pending_establish.pop(key, None)) is not None and (pmsg := pe[1]) is not None:
            self._complete_later(pmsg, exc=exc)
        if (msg := self._pending_opens.pop(key, None)) is not None:
            self._complete_later(msg, exc=exc)

        self._discard_input(stream)
        self._remote_closed.discard(key)
        if (child := self._children.get(key)) is not None and not stream.local_finished:
            child.abort(exc)
            self._fail_parent_awaits(key, exc)

    def _on_shutdown(self) -> None:
        if self._shutting_down:
            return
        try:
            with self._connection() as conn:
                self._adapter.on_shutdown(conn)
        except Exception as e:  # noqa
            self._fail(e)

    def _on_input_ended(self) -> None:
        self._input_ended = True
        for stream in self._table:
            if stream.is_terminal:
                continue
            if stream.is_opening:
                self._reset_stream(
                    stream,
                    'connection input ended',
                    by='remote',
                    exc=ConnectionClosedMultiplexIoPipelineError(
                        'connection input ended before the stream was confirmed',
                    ),
                )
            elif not stream.remote_ended:
                self._reset_stream(
                    stream,
                    'truncated',
                    by='remote',
                    exc=StreamTruncatedMultiplexIoPipelineError(stream.key),
                )

        try:
            with self._connection() as conn:
                self._adapter.on_input_ended(conn)
        except Exception as e:  # noqa
            self._fail(e)

    def _fail(self, exc: BaseException) -> None:
        if self._failed is not None:
            return
        self._failed = exc
        self._shutting_down = True
        # May be reached during emission: the turn must run again to release streams and finish the connection.
        self._dirty = True

        # A failed connection emits its connection error and nothing else of the control output it had queued.
        self._control_q.clear()
        try:
            self._goodbye_q.extend(self._adapter.encode_connection_error(exc))
        except Exception:  # noqa
            pass

        cce = ConnectionClosedMultiplexIoPipelineError('connection failed')
        cce.__cause__ = exc
        for stream in self._table:
            self._reset_stream(stream, 'connection failed', by='local', exc=cce)

    def _teardown(self, exc: BaseException) -> None:
        """Abortive teardown on removal: nothing may be fed to the parent any more."""

        for stream in self._table:
            if not stream.is_terminal:
                stream.reset(exc, by='local')
            if (msg := self._pending_opens.pop(stream.key, None)) is not None and not msg.is_done():
                self._completions.append((msg, None, exc))
            if (child := self._children.pop(stream.key, None)) is not None:
                child.abort(exc)
            self._fail_parent_awaits(stream.key, exc)
            # Nothing can process a stream's queued input or output any more; nothing retains them.
            stream.clear_in()
            stream.clear_out()

        for stream in list(self._table):
            self._table.remove(stream.key)
            self._credit.remove_stream(stream.key)
            self._scheduler.remove(stream.key)
        self._children.clear()
        self._parent_awaits.clear()

        for _, pmsg in self._pending_establish.values():
            if pmsg is not None and not pmsg.is_done():
                self._completions.append((pmsg, None, exc))
        self._pending_establish.clear()
        self._remote_closed.clear()
        self._control_q.clear()
        self._goodbye_q.clear()
        self._child_awaits.clear()
        self._flush_fences.clear()
        self._finished_hooks.clear()
        self._pending_feeds.clear()

        while self._completions:
            cmsg, _, _ = self._completions.popleft()
            if not cmsg.is_done():
                try:
                    cmsg.set_failed(exc)
                except Exception:  # noqa
                    pass

    ##
    # turn

    def _turn(self, ctx: IoPipelineHandlerContext) -> None:
        if self._removed:
            return

        if self._in_turn:
            # A reentrant event: its state is recorded; the outer turn picks it up so emission stays ordered.
            self._dirty = True
            return

        self._in_turn = True
        self._turn_budget = self._config.turn_output_budget
        self._turn_should_yield = self._yield_policy.new_turn()
        try:
            while not self._removed:
                self._dirty = False
                self._pump(ctx)
                self._emit(ctx)
                if not self._dirty:
                    break
        finally:
            self._in_turn = False

    ##
    # pump

    def _pump(self, ctx: IoPipelineHandlerContext) -> None:
        progressed = True
        while progressed:
            progressed = False

            if self._pending_establish:
                pending = self._pending_establish
                self._pending_establish = {}
                for key, (spec, msg) in pending.items():
                    self._establish(ctx, key, spec, msg)
                progressed = True

            if self._pending_feeds:
                feeds = self._pending_feeds
                self._pending_feeds = []
                for feed in feeds:
                    if (child := self._children.get(feed.key)) is not None:
                        child.feed(*feed.msgs)
                progressed = True

            for child in list(self._children.values()):
                progressed |= self._pump_child(child)

            progressed |= self._drain_remote_closed()

            if self._finished_hooks:
                keys = self._finished_hooks
                self._finished_hooks = []
                for key in keys:
                    if (stream := self._table.get(key)) is not None and not stream.is_terminal:
                        try:
                            with self._connection() as conn:
                                self._adapter.on_stream_finished(conn, stream)
                        except Exception as e:  # noqa
                            self._fail(e)
                progressed = True

        self._release_done()

        for stream in self._table:
            self._refresh_ready(stream)

    def _establish(
            self,
            ctx: IoPipelineHandlerContext,
            key: IoPipelineMultiplexStreamKey,
            spec: ta.Any,
            msg: ta.Optional[IoPipelineMultiplexMessages.OpenStream],
    ) -> None:
        stream = self._table.get(key)
        if stream is None or stream.is_terminal:
            if msg is not None:
                self._complete_later(msg, exc=ConnectionClosedMultiplexIoPipelineError('stream ended before establishment'))  # noqa
            return

        child = IoPipelineMultiplexChild(
            stream,
            spec,
            IoPipelineMultiplexStreamOpening(key, stream.origin, stream.info),
            config=self._config.child,
            parent_ctx=ctx,
        )
        if (failure := child.failure) is not None:
            if stream.origin == 'remote':
                # Nothing was accepted yet, so the stream is refused rather than reset.
                self._control_q.extend(self._guard(
                    self._adapter.encode_refuse,
                    IoPipelineMultiplexStreamOpening(key, stream.origin, stream.info),
                    failure,
                    default=(),
                ))
                stream.refuse_remote(failure)
            else:
                self._reset_stream(stream, failure, by='local', encode=True, exc=failure)
            if msg is not None:
                self._complete_later(msg, exc=failure)
            return

        self._children[key] = child
        if stream.origin == 'remote':
            self._control_q.extend(self._guard(self._adapter.encode_accept, stream, default=()))

        child.start()
        if msg is not None:
            self._complete_later(msg, IoPipelineMultiplexOpenedStream(key, check.not_none(child.pipeline)))

    def _claim_output(self, stream: IoPipelineMultiplexStream, msg: ta.Any) -> ta.Optional[int]:
        """The flow-control cost of a stream's typed output message, or None if the adapter does not claim it."""

        if not self._guard(self._adapter.claim_output, stream, msg, default=False):
            return None
        return max(self._guard(self._adapter.message_cost, stream, msg, default=0), 0)

    def _pump_child(self, child: IoPipelineMultiplexChild) -> bool:
        stream = child.stream
        if not child.is_running:
            if stream.in_items:
                # Finished or failed, it will consume no more; what it left queued must not hold the credit it occupies.
                self._discard_input(stream)
            if child.failure is not None and not stream.is_terminal:
                self._reset_stream(stream, child.failure, by='local', encode=True, exc=child.failure)
                return True
            return False

        before = (stream.in_items, stream.out_items, stream.out_bytes)

        if not self._parent_batch_open:
            for cost in child.deliver_input():
                self._queue_grants(self._credit.consume_receive(stream.key, cost))

        child.collect_output(functools.partial(self._claim_output, stream))

        for awt in child.take_awaits():
            self._child_awaits.append((child, awt))

        if child.failure is not None:
            self._reset_stream(stream, child.failure, by='local', encode=True, exc=child.failure)
            return True

        child.update_writability()

        pipeline = child.pipeline
        return (
            (stream.in_items, stream.out_items, stream.out_bytes) != before or
            (pipeline is not None and pipeline.output.peek() is not None) or
            (child.wants_input and stream.in_head() is not None and not self._parent_batch_open) or
            child.failure is not None
        )

    def _drain_remote_closed(self) -> bool:
        progressed = False
        for key in list(self._remote_closed):
            stream = self._table.get(key)
            child = self._children.get(key)
            if stream is None:
                self._remote_closed.discard(key)
                continue
            if child is None:
                if key not in self._pending_establish:
                    self._remote_closed.discard(key)
                continue  # Accepted and closed in one read: the child is built in this pump, and drained afterwards.

            while (head := stream.out_head()) is not None:
                progressed = True
                if isinstance(head, memoryview):
                    stream.pop_out_data(stream.out_head_data_bytes())
                    continue

                item = stream.pop_out_item()
                if not isinstance(item, IoPipelineMultiplexOutputFence):
                    if isinstance(item.msg, IoPipelineMessages.Completable):
                        child.complete(item.msg, StreamResetMultiplexIoPipelineError('closed', by='remote'))
                    continue

                if item.kind == 'final':
                    if not stream.local_finished:
                        stream.finish_local()
                    # Completed - and the child finished - behind the parent flush, like a final reached normally: a
                    # fence of this stream emitted earlier may still await that flush, and a later fence must not
                    # complete ahead of it (DESIGN 5), nor may finishing the child now fail it.
                    self._flush_fences.append((child, item.msg, 'final'))
                else:
                    child.complete(item.msg, StreamResetMultiplexIoPipelineError('closed', by='remote'))

            if not child.is_running and not stream.is_terminal:
                stream.close()
                self._remote_closed.discard(key)
                progressed = True

        return progressed

    def _release_done(self) -> None:
        for stream in self._table:
            key = stream.key
            child = self._children.get(key)
            child_done = child is None or not child.is_running
            if not child_done or key in self._pending_establish:
                continue

            if not stream.is_terminal:
                if key in self._remote_closed:
                    stream.close()
                elif child is not None and child.failure is not None:
                    self._reset_stream(stream, child.failure, by='local', encode=True, exc=child.failure)
                else:
                    continue

            self._table.remove(key)
            self._credit.remove_stream(key)
            self._scheduler.remove(key)
            self._children.pop(key, None)
            self._remote_closed.discard(key)
            self._fail_parent_awaits(key, ConnectionClosedMultiplexIoPipelineError('stream ended'))
            self._queue_grants(self._credit.pending_grants())
            self._guard(self._adapter.on_stream_released, stream, default=None)

    def _refresh_ready(self, stream: IoPipelineMultiplexStream) -> None:
        key = stream.key
        self._scheduler.set_ready(key, self._is_ready(stream))

    def _is_ready(self, stream: IoPipelineMultiplexStream) -> bool:
        key = stream.key
        if (
                stream.is_terminal or
                stream.is_opening or
                key in self._remote_closed or
                key not in self._children or
                (head := stream.out_head()) is None
        ):
            return False

        adapter = self._adapter
        if isinstance(head, memoryview):
            return (
                stream.can_send_data and
                self._guard(adapter.max_data_unit, stream, default=0) > 0 and
                self._credit.send_available(key) - self._guard(adapter.data_unit_overhead, stream, default=0) > 0
            )

        if isinstance(head, IoPipelineMultiplexOutputMessage):
            if (cost := head.cost) <= 0:
                return True
            limit = min(self._credit.send_available(key), self._guard(adapter.max_data_unit, stream, default=0))
            # A message which does not fit must be splittable to make progress now; otherwise it waits for credit.
            return cost <= limit or (
                limit > 0 and
                self._guard(adapter.split_message, stream, head.msg, limit, default=None) is not None
            )

        return True

    ##
    # emit

    def _is_removed(self) -> bool:
        # A method, not the attribute, as feeding can remove this handler between checks.
        return self._removed

    def _emit(self, ctx: IoPipelineHandlerContext) -> None:
        # Anything fed - including completing an open, whose listener may react - can remove this handler, after which
        # nothing more may be fed: every step checks.

        while self._completions:
            msg, result, exc = self._completions.popleft()
            if msg.is_done():
                continue
            if exc is None:
                msg.set_succeeded(result)
            else:
                msg.set_failed(exc)
        if self._is_removed():
            return

        if self._final_output_sent:
            self._control_q.clear()
            self._goodbye_q.clear()
            return

        while self._control_q:
            if self._is_removed():
                return
            ctx.feed_out(self._control_q.popleft())
            if not self._parent_writable:
                self._control_during_pause += 1
                if self._control_during_pause > self._config.max_control_during_pause:
                    self._fail(ControlOutputLimitMultiplexIoPipelineError(self._control_during_pause))
            if self._failed is not None:
                # Whether by the bound just crossed or by a reaction to what was fed: the rest of the batch is not
                # emitted, only the connection error.
                self._control_q.clear()
                break

        while self._goodbye_q:
            if self._is_removed():
                return
            ctx.feed_out(self._goodbye_q.popleft())

        while self._child_awaits:
            if self._is_removed():
                return
            child, cawt = self._child_awaits.popleft()
            pawt: AsyncIoPipelineMessages.Await = AsyncIoPipelineMessages.Await(cawt.obj)
            key = child.stream.key
            pawt.add_listener(functools.partial(
                MultiplexIoPipelineHandler._on_parent_await_done,
                weakref.ref(ctx),
                weakref.ref(child),
                weakref.ref(cawt),
                key,
            ))
            self._parent_awaits.setdefault(key, []).append(pawt)
            ctx.feed_out(pawt)

        self._emit_streams(ctx)
        if self._is_removed():
            return

        if self._flush_fences:
            entries = [(weakref.ref(c), weakref.ref(f), k) for c, f, k in self._flush_fences]
            self._flush_fences = []
            fo = IoPipelineFlowMessages.FlushOutput()
            fo.add_listener(functools.partial(
                MultiplexIoPipelineHandler._on_parent_flush_done,
                weakref.ref(ctx),
                entries,
            ))
            ctx.feed_out(fo)
            if self._is_removed():
                return

        if self._want_parent_read and not self._input_ended:
            self._want_parent_read = False
            IoPipelineFlow.maybe_ready_for_input(ctx)

        if self._shutting_down and not len(self._table) and not self._final_output_sent:
            self._final_output_sent = True
            ctx.feed_out(IoPipelineMessages.FinalOutput())

    def _emit_streams(self, ctx: IoPipelineHandlerContext) -> None:
        while self._parent_writable and not self._final_output_sent and not self._is_removed():
            if (key := self._scheduler.next()) is None:
                return

            # Readiness may be stale: emitting can reenter - a reset arriving, a failure, credit spent by another
            # stream on the shared connection window - so it is checked again against current state.
            if (stream := self._table.get(key)) is None or not self._is_ready(stream):
                self._scheduler.set_ready(key, False)
                continue

            if self._turn_budget <= 0 or self._turn_should_yield():
                if not self._continuation_pending:
                    self._continuation_pending = True
                    ctx.defer(MultiplexIoPipelineHandler._resume)
                return

            before = (stream.out_items, stream.out_bytes)
            cost = self._emit_unit(ctx, stream)
            if self._is_removed():
                return  # Torn down while the unit was fed: nothing of this stream remains to account.
            self._scheduler.account(key, cost)
            self._turn_budget -= cost
            if cost <= 0 and (stream.out_items, stream.out_bytes) == before:
                # Defensive: a unit which made no progress must not be retried at once, or this would spin.
                self._scheduler.set_ready(key, False)
            else:
                self._refresh_ready(stream)
                # The stream's queue shrank: the next pump re-derives its child's writability, which may resume it.
                self._dirty = True

    def _emit_unit(self, ctx: IoPipelineHandlerContext, stream: IoPipelineMultiplexStream) -> int:
        key = stream.key
        adapter = self._adapter
        head = check.not_none(stream.out_head())

        if isinstance(head, memoryview):
            overhead = self._guard(adapter.data_unit_overhead, stream, default=0)
            n = min(
                stream.out_head_data_bytes(),
                self._guard(adapter.max_data_unit, stream, default=0),
                self._credit.send_available(key) - overhead,
            )
            if n <= 0:
                return 0
            segs = stream.pop_out_data(n)
            cost = n + overhead
            self._credit.consume_send(key, cost)
            self._feed_frames(ctx, self._guard(
                adapter.encode_data,
                stream,
                SegmentedByteStreamBufferView(segs),
                default=(),
            ))
            return cost

        if isinstance(head, IoPipelineMultiplexOutputMessage):
            msg = head.msg
            cost = head.cost
            if cost > 0:
                limit = min(self._credit.send_available(key), self._guard(adapter.max_data_unit, stream, default=0))
                if cost > limit:
                    if (split := self._guard(adapter.split_message, stream, msg, limit, default=None)) is None:
                        self._scheduler.set_ready(key, False)
                        return 0
                    msg, tail = split
                    head_cost = self._guard(adapter.message_cost, stream, msg, default=0)
                    check.state(0 < head_cost <= limit)
                    stream.replace_out_head_message(tail, cost - head_cost)
                    self._credit.consume_send(key, head_cost)
                    self._feed_frames(ctx, self._guard(adapter.encode_message, stream, msg, default=()))
                    return head_cost
                self._credit.consume_send(key, cost)
            stream.pop_out_item()
            self._feed_frames(ctx, self._guard(adapter.encode_message, stream, msg, default=()))
            return cost

        fence = check.isinstance(stream.pop_out_item(), IoPipelineMultiplexOutputFence)
        child = self._children[key]
        if fence.kind == 'shutdown':
            stream.end_local()
            self._feed_frames(ctx, self._guard(adapter.encode_end, stream, default=()))
        elif fence.kind == 'final':
            outs = self._guard(adapter.encode_finish, stream, default=())
            stream.finish_local()
            self._feed_frames(ctx, outs)
            self._finished_hooks.append(key)
            self._dirty = True
        self._flush_fences.append((child, fence.msg, fence.kind))
        return 0

    def _feed_frames(self, ctx: IoPipelineHandlerContext, frames: ta.Iterable[ta.Any]) -> None:
        # Feeding a frame can remove this handler (an outer handler reacting to it); the remaining frames of the unit
        # must then not go through the invalidated context.
        for out in frames:
            if self._is_removed():
                return
            ctx.feed_out(out)

    ##
    # completion listeners - hold the context and child side weakly

    @staticmethod
    def _on_parent_flush_done(
            ctx_ref: ta.Callable[[], ta.Optional[IoPipelineHandlerContext]],
            entries: ta.Sequence[ta.Tuple[
                ta.Callable[[], ta.Optional[IoPipelineMultiplexChild]],
                ta.Callable[[], ta.Optional[IoPipelineMessages.Completable]],
                str,
            ]],
            fo: IoPipelineFlowMessages.FlushOutput,
    ) -> None:
        exc: ta.Optional[BaseException] = None
        if not fo.is_succeeded():
            exc = fo.get_exception() or AbortedIoPipelineError('connection flush failed')

        for child_ref, fence_ref, kind in entries:
            if (child := child_ref()) is None or (fence := fence_ref()) is None:
                continue
            if kind != 'final':
                child.complete(fence, exc)
            elif exc is None:
                child.finish(fence)
            else:
                child.complete(fence, exc)
                child.abort(exc, notify=False)

        if (ctx := ctx_ref()) is not None and not ctx.invalidated:
            check.isinstance(ctx.handler, MultiplexIoPipelineHandler).on_child_activity(ctx)

    @staticmethod
    def _on_parent_await_done(
            ctx_ref: ta.Callable[[], ta.Optional[IoPipelineHandlerContext]],
            child_ref: ta.Callable[[], ta.Optional[IoPipelineMultiplexChild]],
            cawt_ref: ta.Callable[[], ta.Optional[AsyncIoPipelineMessages.Await]],
            key: IoPipelineMultiplexStreamKey,
            pawt: AsyncIoPipelineMessages.Await,
    ) -> None:
        if (child := child_ref()) is not None and (cawt := cawt_ref()) is not None:
            if pawt.is_succeeded():
                child.complete_await(cawt, result=pawt.get_result())
            else:
                child.complete_await(cawt, exc=pawt.get_exception() or AbortedIoPipelineError('await failed'))

        if (ctx := ctx_ref()) is not None and not ctx.invalidated:
            h = check.isinstance(ctx.handler, MultiplexIoPipelineHandler)
            if (lst := h._parent_awaits.get(key)) is not None:  # noqa
                try:
                    lst.remove(pawt)
                except ValueError:
                    pass
                if not lst:
                    h._parent_awaits.pop(key, None)  # noqa
            h.on_child_activity(ctx)
