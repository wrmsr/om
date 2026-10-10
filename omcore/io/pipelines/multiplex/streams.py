# ruff: noqa: UP006 UP007 UP045 UP037
# @om-lite
"""
Streams and the stream table, independent of how a stream's endpoint is realized (a child pipeline, or tagged
messages).

A stream's lifecycle is the product of its two halves plus a terminal outcome:

 - local:    OPENING (a locally requested stream awaiting confirmation) -> OPEN -> ENDED (end-of-output emitted)
             -> FINISHED (the local endpoint is done)
 - remote:   OPEN -> ENDED (the peer ended its output)
 - terminal: CLOSED, RESET, or REFUSED, after which the stream leaves the table.

Both directions ending does not close a stream by itself: protocols differ on whether typed messages may follow
end-of-data and on whether closure needs a handshake. The protocol adapter closes, and the multiplexer resets or
refuses, explicitly.
"""
import collections
import dataclasses as dc
import typing as ta

from ....lite.check import check
from ...streambufs.utils import ByteStreamBuffers
from .types import DuplicateStreamMultiplexError
from .types import MultiplexStreamKey
from .types import MultiplexStreamOrigin
from .types import MultiplexStreamState
from .types import StreamLimitMultiplexError
from .types import StreamStateMultiplexError
from .types import UnknownStreamMultiplexError


##


MultiplexOutputFenceKind = ta.Literal['flush', 'shutdown', 'final']  # ta.TypeAlias


@ta.final
@dc.dataclass(frozen=True)
class MultiplexOutputFence:
    """A fence in a stream's outbound queue, ordered with the output around it."""

    kind: MultiplexOutputFenceKind
    msg: ta.Any = None


@ta.final
@dc.dataclass(frozen=True)
class MultiplexOutputMessage:
    """
    A typed message in a stream's outbound queue, keeping its place in order. A positive cost makes it flow-controlled
    like data; an uncontrolled message costs nothing.
    """

    msg: ta.Any
    cost: int = 0


@ta.final
@dc.dataclass(frozen=True)
class MultiplexInputData:
    data: ta.Any
    cost: int


@ta.final
@dc.dataclass(frozen=True)
class MultiplexInputMessage:
    msg: ta.Any
    cost: int = 0  # positive for flow-controlled typed messages (SSH extended data, say)


@ta.final
class MultiplexInputEnd:
    def __repr__(self) -> str:
        return f'{type(self).__name__}()'


MultiplexInputItem = ta.Union[MultiplexInputData, MultiplexInputMessage, MultiplexInputEnd]  # ta.TypeAlias  # noqa


##


@ta.final
class MultiplexStream:
    """One logical bidirectional flow: its lifecycle state machine and its ordered inbound and outbound queues."""

    def __init__(
            self,
            key: MultiplexStreamKey,
            origin: MultiplexStreamOrigin,
            *,
            info: ta.Any = None,
            opening: bool = False,
    ) -> None:
        super().__init__()

        check.in_(origin, ('local', 'remote'))
        check.arg(not opening or origin == 'local')

        self._key = key
        self._origin = origin
        self._info = info

        self._local: ta.Literal['opening', 'open', 'ended', 'finished'] = 'opening' if opening else 'open'
        self._remote: ta.Literal['open', 'ended'] = 'open'
        self._terminal: ta.Optional[ta.Literal['closed', 'reset', 'refused']] = None
        self._terminal_reason: ta.Any = None
        self._reset_by: ta.Optional[MultiplexStreamOrigin] = None

        # Outbound: data segments (memoryviews) interleaved with typed messages and fences, in exact order.
        self._out_q: ta.Deque[ta.Union[memoryview, MultiplexOutputMessage, MultiplexOutputFence]] = collections.deque()
        self._out_bytes = 0

        # Inbound, in exact order.
        self._in_q: ta.Deque[MultiplexInputItem] = collections.deque()
        self._in_cost = 0
        self._in_bytes = 0
        self._in_messages = 0
        self._in_end_queued = False

    # Owned by the protocol adapter - peer channel numbers, maximum packet sizes, and the like.
    protocol: ta.Any = None

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._key!r}, {self._origin}, {self.state.name}>'

    @property
    def key(self) -> MultiplexStreamKey:
        return self._key

    @property
    def origin(self) -> MultiplexStreamOrigin:
        return self._origin

    @property
    def info(self) -> ta.Any:
        return self._info

    ##
    # state

    @property
    def state(self) -> MultiplexStreamState:
        if (t := self._terminal) is not None:
            return {
                'closed': MultiplexStreamState.CLOSED,
                'reset': MultiplexStreamState.RESET,
                'refused': MultiplexStreamState.REFUSED,
            }[t]

        if self._local == 'opening':
            return MultiplexStreamState.OPENING

        local_done = self._local in ('ended', 'finished')
        remote_done = self._remote == 'ended'
        if local_done and remote_done:
            return MultiplexStreamState.ENDED
        elif local_done:
            return MultiplexStreamState.HALF_CLOSED_LOCAL
        elif remote_done:
            return MultiplexStreamState.HALF_CLOSED_REMOTE
        else:
            return MultiplexStreamState.OPEN

    @property
    def is_terminal(self) -> bool:
        return self._terminal is not None

    @property
    def is_opening(self) -> bool:
        return self._terminal is None and self._local == 'opening'

    @property
    def local_ended(self) -> bool:
        return self._local in ('ended', 'finished')

    @property
    def local_finished(self) -> bool:
        return self._local == 'finished'

    @property
    def remote_ended(self) -> bool:
        return self._remote == 'ended'

    @property
    def terminal_reason(self) -> ta.Any:
        return self._terminal_reason

    @property
    def reset_by(self) -> ta.Optional[MultiplexStreamOrigin]:
        return self._reset_by

    @property
    def can_send_data(self) -> bool:
        return self._terminal is None and self._local == 'open'

    @property
    def can_receive_data(self) -> bool:
        return self._terminal is None and self._local != 'opening' and self._remote == 'open'

    @property
    def can_receive_message(self) -> bool:
        # Typed messages may follow end-of-data in some protocols (SSH channel requests after EOF); the adapter enforces
        # anything stricter.
        return self._terminal is None and self._local != 'opening'

    def _require(self, ok: bool, op: str) -> None:
        if not ok:
            raise StreamStateMultiplexError(f'{op} not permitted in stream {self._key!r} state {self.state.name}')

    def confirm(self) -> None:
        self._require(self._terminal is None and self._local == 'opening', 'confirm')
        self._local = 'open'

    def refuse(self, reason: ta.Any = None) -> None:
        self._require(self._terminal is None and self._local == 'opening', 'refuse')
        self._terminal = 'refused'
        self._terminal_reason = reason

    def refuse_remote(self, reason: ta.Any = None) -> None:
        """Refuses a peer-opened stream which was never accepted, as if it had been refused on arrival."""

        self._require(self._terminal is None and self._origin == 'remote' and self._local == 'open', 'refuse_remote')
        self._terminal = 'refused'
        self._terminal_reason = reason

    def end_local(self) -> None:
        self._require(self._terminal is None and self._local == 'open', 'end_local')
        self._local = 'ended'

    def finish_local(self) -> None:
        self._require(self._terminal is None and self._local in ('open', 'ended'), 'finish_local')
        self._local = 'finished'

    def end_remote(self) -> None:
        self._require(self._terminal is None and self._local != 'opening' and self._remote == 'open', 'end_remote')
        self._remote = 'ended'

    def close(self, reason: ta.Any = None) -> None:
        self._require(self._terminal is None, 'close')
        self._terminal = 'closed'
        self._terminal_reason = reason

    def reset(self, reason: ta.Any = None, *, by: MultiplexStreamOrigin) -> None:
        self._require(self._terminal is None, 'reset')
        check.in_(by, ('local', 'remote'))
        self._terminal = 'reset'
        self._terminal_reason = reason
        self._reset_by = by

    ##
    # outbound queue

    @property
    def out_bytes(self) -> int:
        """Queued flow-controlled cost: data bytes plus the costs of flow-controlled typed messages."""

        return self._out_bytes

    @property
    def out_items(self) -> int:
        return len(self._out_q)

    def push_out_data(self, data: ta.Any) -> None:
        for seg in ByteStreamBuffers.iter_segments(data):
            if seg:
                self._out_q.append(seg)
                self._out_bytes += len(seg)

    def push_out_message(self, msg: ta.Any, cost: int = 0) -> None:
        check.arg(cost >= 0)
        self._out_q.append(MultiplexOutputMessage(msg, cost))
        self._out_bytes += cost

    def push_out_fence(self, kind: MultiplexOutputFenceKind, msg: ta.Any = None) -> None:
        self._out_q.append(MultiplexOutputFence(kind, msg))

    def out_head(self) -> ta.Union[memoryview, MultiplexOutputMessage, MultiplexOutputFence, None]:
        if not self._out_q:
            return None
        return self._out_q[0]

    def out_head_data_bytes(self) -> int:
        """Bytes of data at the head of the queue, up to the next message or fence."""

        n = 0
        for item in self._out_q:
            if not isinstance(item, memoryview):
                break
            n += len(item)
        return n

    def pop_out_data(self, max_bytes: int) -> ta.List[memoryview]:
        """Takes up to `max_bytes` from the data at the head of the queue, gathering consecutive segments."""

        check.arg(max_bytes > 0)
        out: ta.List[memoryview] = []
        remaining = max_bytes
        while remaining and self._out_q and isinstance(head := self._out_q[0], memoryview):
            if len(head) <= remaining:
                self._out_q.popleft()
                out.append(head)
                remaining -= len(head)
            else:
                out.append(head[:remaining])
                self._out_q[0] = head[remaining:]
                remaining = 0
        self._out_bytes -= max_bytes - remaining
        return out

    def replace_out_head_message(self, msg: ta.Any, cost: int = 0) -> None:
        """Replaces the typed message at the head of the queue - with the remainder of a split message, say."""

        check.arg(cost >= 0)
        old = check.isinstance(self._out_q[0], MultiplexOutputMessage)
        self._out_q[0] = MultiplexOutputMessage(msg, cost)
        self._out_bytes += cost - old.cost

    def pop_out_item(self) -> ta.Union[MultiplexOutputMessage, MultiplexOutputFence]:
        head = self._out_q.popleft()
        if isinstance(head, memoryview):
            self._out_q.appendleft(head)
            raise TypeError('head of queue is data')
        if isinstance(head, MultiplexOutputMessage):
            self._out_bytes -= head.cost
        return head

    def clear_out(self) -> ta.List[ta.Union[MultiplexOutputMessage, MultiplexOutputFence]]:
        """Discards all queued output, returning the non-data items (so their fences can be failed)."""

        items = [item for item in self._out_q if not isinstance(item, memoryview)]
        self._out_q.clear()
        self._out_bytes = 0
        return items

    ##
    # inbound queue

    @property
    def in_cost(self) -> int:
        """Queued flow-controlled input cost."""

        return self._in_cost

    @property
    def in_bytes(self) -> int:
        return self._in_bytes

    @property
    def in_messages(self) -> int:
        """Queued uncontrolled typed input messages."""

        return self._in_messages

    @property
    def in_items(self) -> int:
        return len(self._in_q)

    @property
    def in_end_queued(self) -> bool:
        return self._in_end_queued

    def push_in_data(self, data: ta.Any, cost: int) -> None:
        check.arg(cost >= 0)
        check.state(not self._in_end_queued)
        self._in_q.append(MultiplexInputData(data, cost))
        self._in_cost += cost
        self._in_bytes += len(data)

    def push_in_message(self, msg: ta.Any, cost: int = 0) -> None:
        check.arg(cost >= 0)
        self._in_q.append(MultiplexInputMessage(msg, cost))
        if cost:
            self._in_cost += cost
        else:
            self._in_messages += 1

    def push_in_end(self) -> None:
        check.state(not self._in_end_queued)
        self._in_q.append(MultiplexInputEnd())
        self._in_end_queued = True

    def in_head(self) -> ta.Optional[MultiplexInputItem]:
        if not self._in_q:
            return None
        return self._in_q[0]

    def pop_in(self) -> MultiplexInputItem:
        item = self._in_q.popleft()
        if isinstance(item, MultiplexInputData):
            self._in_cost -= item.cost
            self._in_bytes -= len(item.data)
        elif isinstance(item, MultiplexInputMessage):
            if item.cost:
                self._in_cost -= item.cost
            else:
                self._in_messages -= 1
        return item

    def clear_in(self) -> ta.List[int]:
        """
        Discards all queued input, returning the flow-controlled costs discarded (so their credit can be returned).
        """

        costs = [item.cost for item in self._in_q if not isinstance(item, MultiplexInputEnd) and item.cost]
        self._in_q.clear()
        self._in_cost = 0
        self._in_bytes = 0
        self._in_messages = 0
        return costs


##


@ta.final
@dc.dataclass(frozen=True)
class MultiplexStreamStats:
    """Read-only counters a protocol layer may use for its own defenses (open/reset floods, control backlogs)."""

    opened_local: int = 0
    opened_remote: int = 0
    refused_local: int = 0
    refused_remote: int = 0
    reset_local: int = 0
    reset_remote: int = 0
    closed: int = 0

    active_local: int = 0
    active_remote: int = 0


@ta.final
class _Unset:
    def __repr__(self) -> str:
        return 'UNSET'


# Leaves a setting unchanged.
UNSET: ta.Any = _Unset()


@ta.final
class MultiplexStreamTable:
    """The streams of one connection, with per-origin concurrency limits which may be changed at any time."""

    def __init__(
            self,
            *,
            max_local: ta.Optional[int] = None,
            max_remote: ta.Optional[int] = None,
    ) -> None:
        super().__init__()

        self._max_local = max_local
        self._max_remote = max_remote

        self._streams: ta.Dict[MultiplexStreamKey, MultiplexStream] = {}
        self._active = {'local': 0, 'remote': 0}

        self._counters: ta.Dict[str, int] = dict.fromkeys([
            'opened_local',
            'opened_remote',
            'refused_local',
            'refused_remote',
            'reset_local',
            'reset_remote',
            'closed',
        ], 0)

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{len(self._streams)}>'

    def __len__(self) -> int:
        return len(self._streams)

    def __contains__(self, key: MultiplexStreamKey) -> bool:
        return key in self._streams

    def __iter__(self) -> ta.Iterator[MultiplexStream]:
        return iter(list(self._streams.values()))

    def get(self, key: MultiplexStreamKey) -> ta.Optional[MultiplexStream]:
        return self._streams.get(key)

    def __getitem__(self, key: MultiplexStreamKey) -> MultiplexStream:
        try:
            return self._streams[key]
        except KeyError:
            raise UnknownStreamMultiplexError(key) from None

    #

    @property
    def max_local(self) -> ta.Optional[int]:
        return self._max_local

    @property
    def max_remote(self) -> ta.Optional[int]:
        return self._max_remote

    def set_limits(
            self,
            *,
            max_local: ta.Optional[int] = UNSET,
            max_remote: ta.Optional[int] = UNSET,
    ) -> None:
        """Changes limits. Streams above a lowered limit are unaffected, but no new ones open until below it."""

        if max_local is not UNSET:
            check.arg(max_local is None or max_local >= 0)
            self._max_local = max_local
        if max_remote is not UNSET:
            check.arg(max_remote is None or max_remote >= 0)
            self._max_remote = max_remote

    def count(self, origin: MultiplexStreamOrigin) -> int:
        return self._active[origin]

    def can_open(self, origin: MultiplexStreamOrigin) -> bool:
        limit = self._max_local if origin == 'local' else self._max_remote
        return limit is None or self._active[origin] < limit

    #

    def add(self, stream: MultiplexStream) -> None:
        if stream.key in self._streams:
            raise DuplicateStreamMultiplexError(stream.key)
        if not self.can_open(stream.origin):
            raise StreamLimitMultiplexError(stream.origin)
        check.state(not stream.is_terminal)

        self._streams[stream.key] = stream
        self._active[stream.origin] += 1
        self._counters[f'opened_{stream.origin}'] += 1

    def count_refused(self, origin: MultiplexStreamOrigin) -> None:
        """Counts a refusal of a stream which never entered the table."""

        self._counters[f'refused_{origin}'] += 1

    def remove(self, key: MultiplexStreamKey) -> MultiplexStream:
        """Removes a terminal stream, counting its outcome."""

        stream = self[key]
        check.state(stream.is_terminal)
        del self._streams[key]
        self._active[stream.origin] -= 1

        st = stream.state
        if st is MultiplexStreamState.CLOSED:
            self._counters['closed'] += 1
        elif st is MultiplexStreamState.RESET:
            self._counters[f'reset_{stream.reset_by}'] += 1
        elif st is MultiplexStreamState.REFUSED:
            self._counters[f'refused_{stream.origin}'] += 1

        return stream

    @property
    def stats(self) -> MultiplexStreamStats:
        return MultiplexStreamStats(
            **self._counters,
            active_local=self._active['local'],
            active_remote=self._active['remote'],
        )
