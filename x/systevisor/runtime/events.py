# ruff: noqa: SLF001 UP006 UP007 UP037 UP045
import collections
import dataclasses as dc
import typing as ta


@dc.dataclass(frozen=True)
class SystevisorBusEvent:
    sequence: int
    at: float
    topic: str
    payload: ta.Any


@dc.dataclass(frozen=True)
class SystevisorEventBatch:
    events: ta.Sequence[SystevisorBusEvent]
    dropped_count: int


@dc.dataclass(frozen=True)
class SystevisorEventCallbackFailure:
    subscription_id: int
    exception: Exception


class SystevisorEventStream:
    def __init__(self, subscription_id: int, capacity: int) -> None:
        if capacity < 1:
            raise ValueError(capacity)
        self._subscription_id = subscription_id
        self._capacity = capacity
        self._events: ta.Deque[SystevisorBusEvent] = collections.deque()
        self._dropped_count = 0
        self._closed = False

    @property
    def subscription_id(self) -> int:
        return self._subscription_id

    @property
    def closed(self) -> bool:
        return self._closed

    def close(self) -> None:
        self._closed = True
        self._events.clear()

    def _publish(self, event: SystevisorBusEvent) -> None:
        if self._closed:
            return
        if len(self._events) >= self._capacity:
            self._events.popleft()
            self._dropped_count += 1
        self._events.append(event)

    def read(self, max_events: ta.Optional[int] = None) -> SystevisorEventBatch:
        if max_events is not None and max_events < 1:
            raise ValueError(max_events)
        count = len(self._events) if max_events is None else min(len(self._events), max_events)
        events = tuple(self._events.popleft() for _ in range(count))
        dropped_count = self._dropped_count
        self._dropped_count = 0
        return SystevisorEventBatch(events=events, dropped_count=dropped_count)


class SystevisorEventSubscription:
    def __init__(self, event_bus: 'SystevisorEventBus', subscription_id: int) -> None:
        self._event_bus = event_bus
        self._subscription_id = subscription_id
        self._closed = False

    @property
    def subscription_id(self) -> int:
        return self._subscription_id

    def close(self) -> None:
        if not self._closed:
            self._event_bus.unsubscribe(self._subscription_id)
            self._closed = True


class SystevisorEventBus:
    def __init__(self, journal_capacity: int = 4096) -> None:
        if journal_capacity < 1:
            raise ValueError(journal_capacity)
        self._journal: ta.Deque[SystevisorBusEvent] = collections.deque(maxlen=journal_capacity)
        self._callbacks: ta.Dict[int, ta.Callable[[SystevisorBusEvent], None]] = {}
        self._streams: ta.Dict[int, SystevisorEventStream] = {}
        self._next_subscription_id = 1
        self._next_sequence = 1

    @property
    def next_sequence(self) -> int:
        return self._next_sequence

    @property
    def journal_capacity(self) -> int:
        return ta.cast(int, self._journal.maxlen)

    def set_journal_capacity(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError(capacity)
        if capacity != self._journal.maxlen:
            self._journal = collections.deque(self._journal, maxlen=capacity)

    def journal(self, after_sequence: int = 0) -> ta.Sequence[SystevisorBusEvent]:
        return tuple(event for event in self._journal if event.sequence > after_sequence)

    def subscribe_callback(
            self,
            callback: ta.Callable[[SystevisorBusEvent], None],
    ) -> SystevisorEventSubscription:
        subscription_id = self._allocate_subscription_id()
        self._callbacks[subscription_id] = callback
        return SystevisorEventSubscription(self, subscription_id)

    def subscribe_stream(self, capacity: int = 1024) -> SystevisorEventStream:
        subscription_id = self._allocate_subscription_id()
        stream = SystevisorEventStream(subscription_id, capacity)
        self._streams[subscription_id] = stream
        return stream

    def _allocate_subscription_id(self) -> int:
        subscription_id = self._next_subscription_id
        self._next_subscription_id += 1
        return subscription_id

    def unsubscribe(self, subscription_id: int) -> None:
        self._callbacks.pop(subscription_id, None)
        stream = self._streams.pop(subscription_id, None)
        if stream is not None:
            stream.close()

    def publish(
            self,
            topic: str,
            payload: ta.Any,
            at: float,
    ) -> ta.Tuple[SystevisorBusEvent, ta.Sequence[SystevisorEventCallbackFailure]]:
        if not topic:
            raise ValueError(topic)
        event = SystevisorBusEvent(
            sequence=self._next_sequence,
            at=at,
            topic=topic,
            payload=payload,
        )
        self._next_sequence += 1
        self._journal.append(event)
        for subscription_id, stream in tuple(self._streams.items()):
            if stream.closed:
                self._streams.pop(subscription_id, None)
            else:
                stream._publish(event)

        failures: ta.List[SystevisorEventCallbackFailure] = []
        for subscription_id, callback in tuple(self._callbacks.items()):
            try:
                callback(event)
            except Exception as exc:  # noqa: BLE001
                failures.append(SystevisorEventCallbackFailure(subscription_id, exc))
                self._callbacks.pop(subscription_id, None)
        return event, tuple(failures)
