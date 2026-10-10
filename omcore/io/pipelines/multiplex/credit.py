# ruff: noqa: UP006 UP007 UP045 UP037
# @om-lite
"""
Credit accounting for multiplexed streams.

Sending: the peer grants credit per stream and, depending on the strategy, per connection. Credit is signed - a peer
may shift every stream's credit at once by a negative amount - and a flow-controlled unit may be sent only while its
cost fits within every applicable credit.

Receiving: credit is advertised to the peer per stream (and per connection). Inbound flow-controlled cost is debited on
arrival; the multiplexer reports consumption - delivery into the stream's consumer - and a replenish policy decides when
consumed credit is re-advertised. Arrivals beyond advertised credit are protocol violations.

All amounts are opaque cost units; protocols decide what a unit costs (bytes, bytes plus padding, ...).
"""
import abc
import dataclasses as dc
import typing as ta

from ....lite.abstract import Abstract
from ....lite.check import check
from .types import FlowControlMultiplexIoPipelineError
from .types import IoPipelineMultiplexStreamKey
from .types import UnknownStreamMultiplexIoPipelineError


##


class IoPipelineMultiplexCreditReplenishPolicy(Abstract):
    @abc.abstractmethod
    def replenish(self, window: int, unadvertised: int) -> int:
        """
        Given a receive window size and the consumed credit not yet re-advertised, returns how much to advertise now
        (zero to wait).
        """

        raise NotImplementedError


@ta.final
class HalfWindowIoPipelineMultiplexCreditReplenishPolicy(IoPipelineMultiplexCreditReplenishPolicy):
    """Re-advertises all consumed credit once at least half of the window has been consumed."""

    def __repr__(self) -> str:
        return f'{type(self).__name__}()'

    def replenish(self, window: int, unadvertised: int) -> int:
        if unadvertised > 0 and unadvertised * 2 >= window:
            return unadvertised
        return 0


@ta.final
class ImmediateIoPipelineMultiplexCreditReplenishPolicy(IoPipelineMultiplexCreditReplenishPolicy):
    """Re-advertises consumed credit as soon as any is consumed."""

    def __repr__(self) -> str:
        return f'{type(self).__name__}()'

    def replenish(self, window: int, unadvertised: int) -> int:
        return max(unadvertised, 0)


##


@ta.final
@dc.dataclass(frozen=True)
class IoPipelineMultiplexCreditGrant:
    """Credit to advertise to the peer: for a stream, or for the whole connection when `key` is None."""

    key: ta.Optional[IoPipelineMultiplexStreamKey]
    amount: int


@ta.final
@dc.dataclass(frozen=True)
class IoPipelineMultiplexCreditTotals:
    """Cumulative accounting, for conservation checks: granted == consumed + available, per direction."""

    send_granted: int
    send_consumed: int
    send_available: int

    recv_advertised: int
    recv_received: int
    recv_outstanding: int


class IoPipelineMultiplexCreditStrategy(Abstract):
    """Send and receive credit accounting for one multiplexed connection."""

    #
    # streams

    @abc.abstractmethod
    def add_stream(
            self,
            key: IoPipelineMultiplexStreamKey,
            *,
            send_credit: int = 0,
            recv_window: int,
    ) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def remove_stream(self, key: IoPipelineMultiplexStreamKey) -> None:
        """
        Forgets a stream. Its unconsumed received cost is released as consumed for connection-level purposes, so a
        closed stream cannot permanently shrink the connection's receive window.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def has_stream(self, key: IoPipelineMultiplexStreamKey) -> bool:
        raise NotImplementedError

    #
    # sending

    @abc.abstractmethod
    def send_available(self, key: IoPipelineMultiplexStreamKey) -> int:
        """The cost a flow-controlled unit on the stream may have right now: the minimum applicable credit."""

        raise NotImplementedError

    @abc.abstractmethod
    def consume_send(self, key: IoPipelineMultiplexStreamKey, cost: int) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def grant_send(self, key: ta.Optional[IoPipelineMultiplexStreamKey], delta: int) -> None:
        """Adds (possibly negative) send credit to one stream, or to the connection when `key` is None."""

        raise NotImplementedError

    @abc.abstractmethod
    def adjust_all_send(self, delta: int) -> None:
        """Shifts every current stream's send credit by `delta`, which may drive credit negative."""

        raise NotImplementedError

    #
    # receiving

    @abc.abstractmethod
    def receive(self, key: IoPipelineMultiplexStreamKey, cost: int) -> ta.Sequence[IoPipelineMultiplexCreditGrant]:
        """
        Debits arriving flow-controlled cost, returning any credit to advertise now. Raises FlowControlMultiplexError,
        debiting nothing, if the cost exceeds advertised credit.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def consume_receive(
            self,
            key: IoPipelineMultiplexStreamKey,
            cost: int,
    ) -> ta.Sequence[IoPipelineMultiplexCreditGrant]:
        """Records delivery of received cost to the stream's consumer, returning any credit to advertise now."""

        raise NotImplementedError

    @abc.abstractmethod
    def discard_receive(self, cost: int) -> ta.Sequence[IoPipelineMultiplexCreditGrant]:
        """
        Debits and at once frees cost arriving for no live stream against any connection-level window, returning any
        credit to advertise now. Raises FlowControlMultiplexError, debiting nothing, if it exceeds advertised credit.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def pending_grants(self) -> ta.Sequence[IoPipelineMultiplexCreditGrant]:
        """Credit to advertise now outside of a receive or consume - for example once stream removal released some."""

        raise NotImplementedError

    @abc.abstractmethod
    def withdraw(self, key: ta.Optional[IoPipelineMultiplexStreamKey], amount: int) -> None:
        """
        Takes back a grant returned by `receive`, `consume_receive`, `discard_receive` or `pending_grants` which was not
        sent to the peer, so the accounting follows the wire: the credit is unadvertised again and will be proposed
        afresh.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def recv_queued(self, key: IoPipelineMultiplexStreamKey) -> int:
        """Received but not yet consumed cost."""

        raise NotImplementedError

    @abc.abstractmethod
    def totals(self, key: ta.Optional[IoPipelineMultiplexStreamKey] = None) -> IoPipelineMultiplexCreditTotals:
        """Cumulative accounting for a stream, or for the connection-level windows when `key` is None."""

        raise NotImplementedError


##


class _BaseIoPipelineMultiplexCreditStrategy(IoPipelineMultiplexCreditStrategy, Abstract):
    class _SendAccount:
        def __init__(self, credit: int) -> None:
            self.credit = credit
            self.granted = credit
            self.consumed = 0

        def consume(self, cost: int) -> None:
            check.arg(cost >= 0)
            self.credit -= cost
            self.consumed += cost

        def grant(self, delta: int) -> None:
            self.credit += delta
            self.granted += delta

    class _RecvAccount:
        def __init__(self, window: int) -> None:
            check.arg(window >= 0)
            self.window = window
            self.outstanding = window  # advertised and not yet used by the peer
            self.queued = 0            # received, not yet consumed
            self.unadvertised = 0      # consumed, not yet re-advertised
            self.advertised = window
            self.received = 0

        def receive(self, cost: int) -> bool:
            check.arg(cost >= 0)
            if cost > self.outstanding:
                return False
            self.outstanding -= cost
            self.queued += cost
            self.received += cost
            return True

        def consume(self, cost: int) -> None:
            check.arg(0 <= cost <= self.queued)
            self.queued -= cost
            self.unadvertised += cost

        def advertise(self, amount: int) -> None:
            check.arg(0 < amount <= self.unadvertised)
            self.unadvertised -= amount
            self.outstanding += amount
            self.advertised += amount

        def withdraw(self, amount: int) -> None:
            """Takes back credit just advertised which was not, after all, sent to the peer."""

            check.arg(0 < amount <= self.outstanding)
            self.outstanding -= amount
            self.advertised -= amount
            self.unadvertised += amount

    class _StreamAccounts:
        def __init__(self, send_credit: int, recv_window: int) -> None:
            self.send = _BaseIoPipelineMultiplexCreditStrategy._SendAccount(send_credit)
            self.recv = _BaseIoPipelineMultiplexCreditStrategy._RecvAccount(recv_window)

    def __init__(
            self,
            *,
            stream_replenish: ta.Optional[IoPipelineMultiplexCreditReplenishPolicy] = None,
    ) -> None:
        super().__init__()

        if stream_replenish is None:
            stream_replenish = HalfWindowIoPipelineMultiplexCreditReplenishPolicy()
        self._stream_replenish = stream_replenish

        self._streams: ta.Dict[IoPipelineMultiplexStreamKey, _BaseIoPipelineMultiplexCreditStrategy._StreamAccounts] = {}  # noqa

    def _accounts(self, key: IoPipelineMultiplexStreamKey) -> _StreamAccounts:
        try:
            return self._streams[key]
        except KeyError:
            raise UnknownStreamMultiplexIoPipelineError(key) from None

    #

    def add_stream(
            self,
            key: IoPipelineMultiplexStreamKey,
            *,
            send_credit: int = 0,
            recv_window: int,
    ) -> None:
        check.not_in(key, self._streams)
        self._streams[key] = _BaseIoPipelineMultiplexCreditStrategy._StreamAccounts(send_credit, recv_window)

    def remove_stream(self, key: IoPipelineMultiplexStreamKey) -> None:
        self._streams.pop(key, None)

    def has_stream(self, key: IoPipelineMultiplexStreamKey) -> bool:
        return key in self._streams

    #

    def grant_send(self, key: ta.Optional[IoPipelineMultiplexStreamKey], delta: int) -> None:
        check.not_none(key)
        self._accounts(key).send.grant(delta)

    def adjust_all_send(self, delta: int) -> None:
        for acc in self._streams.values():
            acc.send.grant(delta)

    #

    def _stream_receive(self, key: IoPipelineMultiplexStreamKey, cost: int) -> _StreamAccounts:
        acc = self._accounts(key)
        if not acc.recv.receive(cost):
            raise FlowControlMultiplexIoPipelineError('stream', key)
        return acc

    def _stream_consume(self, key: IoPipelineMultiplexStreamKey, cost: int) -> ta.List[IoPipelineMultiplexCreditGrant]:
        acc = self._accounts(key)
        acc.recv.consume(cost)

        out: ta.List[IoPipelineMultiplexCreditGrant] = []
        if (amount := self._stream_replenish.replenish(acc.recv.window, acc.recv.unadvertised)) > 0:
            acc.recv.advertise(amount)
            out.append(IoPipelineMultiplexCreditGrant(key, amount))
        return out

    def recv_queued(self, key: IoPipelineMultiplexStreamKey) -> int:
        return self._accounts(key).recv.queued

    def withdraw(self, key: ta.Optional[IoPipelineMultiplexStreamKey], amount: int) -> None:
        check.not_none(key)
        self._accounts(key).recv.withdraw(amount)

    def _stream_totals(self, key: IoPipelineMultiplexStreamKey) -> IoPipelineMultiplexCreditTotals:
        acc = self._accounts(key)
        return IoPipelineMultiplexCreditTotals(
            send_granted=acc.send.granted,
            send_consumed=acc.send.consumed,
            send_available=acc.send.credit,
            recv_advertised=acc.recv.advertised,
            recv_received=acc.recv.received,
            recv_outstanding=acc.recv.outstanding,
        )


##


@ta.final
class StreamMultiplexCreditStrategy(_BaseIoPipelineMultiplexCreditStrategy):
    """Per-stream credit only, as in SSH channels."""

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}'

    def send_available(self, key: IoPipelineMultiplexStreamKey) -> int:
        return self._accounts(key).send.credit

    def consume_send(self, key: IoPipelineMultiplexStreamKey, cost: int) -> None:
        acc = self._accounts(key)
        check.state(cost <= acc.send.credit)
        acc.send.consume(cost)

    def grant_send(self, key: ta.Optional[IoPipelineMultiplexStreamKey], delta: int) -> None:
        if key is None:
            raise TypeError('connection-level credit is not part of this strategy')
        super().grant_send(key, delta)

    def receive(self, key: IoPipelineMultiplexStreamKey, cost: int) -> ta.Sequence[IoPipelineMultiplexCreditGrant]:
        self._stream_receive(key, cost)
        return ()

    def consume_receive(
            self,
            key: IoPipelineMultiplexStreamKey,
            cost: int,
    ) -> ta.Sequence[IoPipelineMultiplexCreditGrant]:
        return self._stream_consume(key, cost)

    def discard_receive(self, cost: int) -> ta.Sequence[IoPipelineMultiplexCreditGrant]:
        return ()

    def pending_grants(self) -> ta.Sequence[IoPipelineMultiplexCreditGrant]:
        return ()

    def withdraw(self, key: ta.Optional[IoPipelineMultiplexStreamKey], amount: int) -> None:
        if key is None:
            raise TypeError('connection-level credit is not part of this strategy')
        super().withdraw(key, amount)

    def totals(self, key: ta.Optional[IoPipelineMultiplexStreamKey] = None) -> IoPipelineMultiplexCreditTotals:
        if key is None:
            raise TypeError('connection-level credit is not part of this strategy')
        return self._stream_totals(key)


@ta.final
class ConnectionMultiplexCreditStrategy(_BaseIoPipelineMultiplexCreditStrategy):
    """
    Per-stream plus connection-wide credit, as in HTTP/2.

    Sending is bounded by both the stream's and the connection's credit. Receiving debits both advertised windows.

    The connection window is replenished by its own policy, and `connection_replenish_on` decides what frees it. With
    the default, 'receive', the connection window bounds only cost in flight: credit is freed as input arrives, while
    the per-stream windows bound what each stream may buffer - so one slow stream cannot stall the others. With
    'consume', credit is freed only as streams' input is consumed (or discarded with a removed stream), bounding the
    connection's total buffering at the price of letting slow streams hold shared credit.
    """

    def __init__(
            self,
            *,
            send_credit: int,
            recv_window: int,
            stream_replenish: ta.Optional[IoPipelineMultiplexCreditReplenishPolicy] = None,
            connection_replenish: ta.Optional[IoPipelineMultiplexCreditReplenishPolicy] = None,
            connection_replenish_on: ta.Literal['receive', 'consume'] = 'receive',
    ) -> None:
        super().__init__(stream_replenish=stream_replenish)

        if connection_replenish is None:
            connection_replenish = HalfWindowIoPipelineMultiplexCreditReplenishPolicy()
        self._connection_replenish = connection_replenish
        check.in_(connection_replenish_on, ('receive', 'consume'))
        self._connection_replenish_on = connection_replenish_on

        self._send = _BaseIoPipelineMultiplexCreditStrategy._SendAccount(send_credit)  # noqa
        self._recv = _BaseIoPipelineMultiplexCreditStrategy._RecvAccount(recv_window)  # noqa

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}'

    def remove_stream(self, key: IoPipelineMultiplexStreamKey) -> None:
        acc = self._streams.pop(key, None)
        if acc is not None and acc.recv.queued and self._connection_replenish_on == 'consume':
            # Discarded input no longer occupies the connection window.
            self._recv.consume(acc.recv.queued)

    def pending_grants(self) -> ta.Sequence[IoPipelineMultiplexCreditGrant]:
        if (amount := self._connection_replenish.replenish(self._recv.window, self._recv.unadvertised)) > 0:
            self._recv.advertise(amount)
            return [IoPipelineMultiplexCreditGrant(None, amount)]
        return []

    def send_available(self, key: IoPipelineMultiplexStreamKey) -> int:
        return min(self._accounts(key).send.credit, self._send.credit)

    def consume_send(self, key: IoPipelineMultiplexStreamKey, cost: int) -> None:
        acc = self._accounts(key)
        check.state(cost <= min(acc.send.credit, self._send.credit))
        acc.send.consume(cost)
        self._send.consume(cost)

    def grant_send(self, key: ta.Optional[IoPipelineMultiplexStreamKey], delta: int) -> None:
        if key is None:
            self._send.grant(delta)
        else:
            super().grant_send(key, delta)

    def receive(self, key: IoPipelineMultiplexStreamKey, cost: int) -> ta.Sequence[IoPipelineMultiplexCreditGrant]:
        acc = self._accounts(key)
        if cost > self._recv.outstanding:
            raise FlowControlMultiplexIoPipelineError('connection', key)
        if not acc.recv.receive(cost):
            raise FlowControlMultiplexIoPipelineError('stream', key)
        check.state(self._recv.receive(cost))

        if self._connection_replenish_on == 'receive':
            self._recv.consume(cost)
            return self.pending_grants()
        return ()

    def consume_receive(
            self,
            key: IoPipelineMultiplexStreamKey,
            cost: int,
    ) -> ta.Sequence[IoPipelineMultiplexCreditGrant]:
        out = self._stream_consume(key, cost)
        if self._connection_replenish_on == 'consume':
            self._recv.consume(cost)
            out.extend(self.pending_grants())
        return out

    def discard_receive(self, cost: int) -> ta.Sequence[IoPipelineMultiplexCreditGrant]:
        if not self._recv.receive(cost):
            raise FlowControlMultiplexIoPipelineError('connection', None)
        self._recv.consume(cost)
        return self.pending_grants()

    def withdraw(self, key: ta.Optional[IoPipelineMultiplexStreamKey], amount: int) -> None:
        if key is None:
            self._recv.withdraw(amount)
        else:
            super().withdraw(key, amount)

    def totals(self, key: ta.Optional[IoPipelineMultiplexStreamKey] = None) -> IoPipelineMultiplexCreditTotals:
        if key is not None:
            return self._stream_totals(key)
        return IoPipelineMultiplexCreditTotals(
            send_granted=self._send.granted,
            send_consumed=self._send.consumed,
            send_available=self._send.credit,
            recv_advertised=self._recv.advertised,
            recv_received=self._recv.received,
            recv_outstanding=self._recv.outstanding,
        )
