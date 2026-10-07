"""
The session: what a frontend holds. Named interpreters, one of them active, and the switch between them. Hosts decide
what the interpreters are - a python namespace seeded with their internals, a fresh javascript engine, a restored one -
and register them under names; the frontend only ever lists, switches, and executes.
"""
import types
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from .interpreters import Interpreter
from .interpreters import Result
from .outputs import OutputSink


SessionListener: ta.TypeAlias = ta.Callable[['Session'], None]


##


class SessionError(Exception):
    pass


@dc.dataclass()
class NoSuchInterpreterError(SessionError):
    name: str


@dc.dataclass()
class DuplicateInterpreterError(SessionError):
    name: str


class NoActiveInterpreterError(SessionError):
    pass


##


class Session:
    def __init__(
            self,
            interpreters: ta.Mapping[str, Interpreter] | None = None,
            *,
            active: str | None = None,
    ) -> None:
        super().__init__()

        self._interpreters: dict[str, Interpreter] = {}
        self._active: str | None = None
        self._listeners: list[SessionListener] = []

        for name, interpreter in (interpreters or {}).items():
            self.add(name, interpreter)
        if active is not None:
            self.switch(active)

    async def __aenter__(self) -> ta.Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    ##
    # Interpreters

    @property
    def names(self) -> ta.Sequence[str]:
        return tuple(self._interpreters)

    @property
    def interpreters(self) -> ta.Mapping[str, Interpreter]:
        return types.MappingProxyType(self._interpreters)

    def get(self, name: str) -> Interpreter:
        try:
            return self._interpreters[name]
        except KeyError:
            raise NoSuchInterpreterError(name) from None

    def add(self, name: str, interpreter: Interpreter, *, activate: bool = False) -> None:
        """Register an interpreter. The first one registered becomes active; `activate` makes any one so."""

        check.non_empty_str(name)
        if name in self._interpreters:
            raise DuplicateInterpreterError(name)
        self._interpreters[name] = interpreter
        if activate or self._active is None:
            self.switch(name)

    def remove(self, name: str) -> Interpreter:
        """Deregister an interpreter (not closing it). Removing the active one activates the next, if any."""

        interpreter = self.get(name)
        del self._interpreters[name]
        if self._active == name:
            self._active = next(iter(self._interpreters), None)
            self._notify()
        return interpreter

    ##
    # The active interpreter

    @property
    def active_name(self) -> str | None:
        return self._active

    @property
    def active(self) -> Interpreter:
        if self._active is None:
            raise NoActiveInterpreterError
        return self._interpreters[self._active]

    def switch(self, name: str) -> Interpreter:
        interpreter = self.get(name)
        if self._active != name:
            self._active = name
            self._notify()
        return interpreter

    def add_listener(self, listener: SessionListener) -> None:
        self._listeners.append(listener)

    def remove_listener(self, listener: SessionListener) -> None:
        self._listeners.remove(listener)

    def _notify(self) -> None:
        for listener in list(self._listeners):
            listener(self)

    ##
    # Execution

    def execute(self, source: str, sink: OutputSink) -> ta.Awaitable[Result]:
        return self.active.execute(source, sink)

    async def aclose(self) -> None:
        for interpreter in list(self._interpreters.values()):
            await interpreter.aclose()
