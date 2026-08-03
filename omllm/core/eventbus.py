import typing as ta

from omcore import lang


E = ta.TypeVar('E')
E_contra = ta.TypeVar('E_contra', contravariant=True)


##


class EventSubscriber(ta.Protocol[E_contra]):
    def __call__(self, event: E_contra, /) -> None | ta.Awaitable[None]: ...


class EventBus(ta.Generic[E]):
    def __init__(
            self,
            initial_subscribers: ta.Iterable[EventSubscriber[E]] | None = None,
    ) -> None:
        super().__init__()

        self._subscribers: list[EventSubscriber[E]] = []

        for subs in initial_subscribers or []:
            self.subscribe(subs)

    def subscribe(self, subscriber: EventSubscriber[E]) -> None:
        self._subscribers.append(subscriber)

    async def publish(self, *events: E) -> None:
        for e in events:
            for subs in self._subscribers:
                if (aw := subs(e)) is not None:
                    await aw


##


class EventPublisher(lang.Abstract, ta.Generic[E]):
    __event_bus: EventBus[E]

    def _event_bus(self) -> EventBus[E]:
        try:
            return self.__event_bus
        except AttributeError:
            pass
        eb = self.__event_bus = EventBus()
        return eb

    def subscribe(self, subscriber: EventSubscriber[E]) -> None:
        self._event_bus().subscribe(subscriber)

    async def _publish(self, *events: E) -> None:
        await self._event_bus().publish(*events)
