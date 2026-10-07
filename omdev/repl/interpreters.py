"""
Interpreters: the stateful half of a backend - a python namespace, a javascript engine context - which runs source and
reports what happened. One interface for every language and every way of hosting one: a frontend holds interpreters
through a `Session` and never learns which it is talking to.
"""
import abc
import enum
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from .languages import Language
from .outputs import OutputSink


##


class ResultStatus(enum.Enum):
    OK = enum.auto()
    ERROR = enum.auto()  # the code raised; the error went to the sink, and `Result.error` carries the exception
    EXIT = enum.auto()   # the code asked to leave the repl: exit(), quit(), a SystemExit


@dc.dataclass(frozen=True)
class Result(lang.Final):
    status: ResultStatus
    value: lang.Maybe[ta.Any] = lang.nothing()  # the last expression's value, when the source ended in one
    error: BaseException | None = None

    @property
    def ok(self) -> bool:
        return self.status is ResultStatus.OK


@dc.dataclass(frozen=True)
class Completion(lang.Final):
    text: str  # the completed word, whole - what replaces the stem being completed


##


class InterpreterError(Exception):
    pass


class InterpreterBusyError(InterpreterError):
    """An execution is already in progress on an interpreter which runs one at a time."""


##


class Interpreter(lang.Abstract):
    @property
    @abc.abstractmethod
    def language(self) -> Language:
        raise NotImplementedError

    @abc.abstractmethod
    def execute(self, source: str, sink: OutputSink) -> ta.Awaitable[Result]:
        """
        Run `source` to completion, writing what it prints and its result or error to `sink` - on the caller's own
        context, never from another thread. Raises only for what is not the code's own doing (a busy interpreter, a
        cancellation of the caller); an error in the code is a Result.
        """

        raise NotImplementedError

    def complete(self, source: str, cursor: int) -> ta.Sequence[Completion]:
        """Completions for the word ending at `cursor` in `source`. None by default."""

        return ()

    def interrupt(self) -> None:
        """Ask a running execution to stop, from any thread. Best effort; the default does nothing."""

    async def aclose(self) -> None:
        pass
