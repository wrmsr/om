"""
What an execution produces besides its result: a stream of typed outputs - what the code printed, the displayable form
of its value, the error it died of - written to a sink as they happen. Frontends render these and nothing else, so a
backend knows nothing of terminals, and a frontend nothing of languages.
"""
import abc
import typing as ta

from omcore import dataclasses as dc
from omcore import lang


##


class Output(lang.Abstract):
    text: str


@dc.dataclass(frozen=True)
class StdoutOutput(Output, lang.Final):
    """What the code printed, exactly - newlines included."""

    text: str


@dc.dataclass(frozen=True)
class ResultOutput(Output, lang.Final):
    """The displayable form of an expression's value: a python repr, a javascript json rendering."""

    text: str


@dc.dataclass(frozen=True)
class ErrorOutput(Output, lang.Final):
    """A formatted error - a python traceback, a javascript stack - already trimmed to what the user should see."""

    text: str


def output_text(output: Output) -> str:
    """The plain-text form of an output: printed text as it is, a result or an error on a line of its own."""

    if isinstance(output, StdoutOutput):
        return output.text
    if isinstance(output, (ResultOutput, ErrorOutput)):
        return output.text if output.text.endswith('\n') else output.text + '\n'
    raise TypeError(output)


##


class OutputSink(lang.Abstract):
    @abc.abstractmethod
    def write(self, output: Output) -> None:
        """
        Called on the execution's own context - the task or thread which called `Interpreter.execute` - so
        implementations need not be thread-safe. Interpreters which run code elsewhere marshal back before writing.
        """

        raise NotImplementedError


class NopOutputSink(OutputSink):
    def write(self, output: Output) -> None:
        pass


class ListOutputSink(OutputSink):
    def __init__(self) -> None:
        super().__init__()

        self._outputs: list[Output] = []

    @property
    def outputs(self) -> ta.Sequence[Output]:
        return tuple(self._outputs)

    def text(self) -> str:
        return ''.join(output_text(o) for o in self._outputs)

    def clear(self) -> None:
        self._outputs.clear()

    def write(self, output: Output) -> None:
        self._outputs.append(output)


class CallbackOutputSink(OutputSink):
    def __init__(self, fn: ta.Callable[[Output], None]) -> None:
        super().__init__()

        self._fn = fn

    def write(self, output: Output) -> None:
        self._fn(output)


class TextOutputSink(OutputSink):
    """Flattens outputs to plain text through one writer - the line frontends' sink."""

    def __init__(self, write: ta.Callable[[str], ta.Any]) -> None:
        super().__init__()

        self._write = write

    def write(self, output: Output) -> None:
        self._write(output_text(output))
