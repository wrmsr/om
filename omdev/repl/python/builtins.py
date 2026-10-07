"""
The builtins a python interpreter's namespace sees: a copy of the real ones with the repl-aware substitutes laid over.
Nothing here touches the real `builtins` module, `sys.stdout`, or anything else process-wide.

`print` writes to the sink of the execution it is called from - a contextvar set for the duration of each `execute`, so
concurrent executions keep their output apart. Called with no execution under way (a function defined at the repl and
later called back from elsewhere in the process) it falls back to the interpreter's default sink, so the output still
lands in the frontend rather than on the raw terminal; with neither it is the real print. An explicit `file` is honored
as it is.
"""
import builtins
import contextvars
import io
import typing as ta

from omcore import lang

from ..outputs import OutputSink
from ..outputs import StdoutOutput


##


_CURRENT_SINK: contextvars.ContextVar[OutputSink | None] = contextvars.ContextVar(
    f'{__name__}._CURRENT_SINK',
    default=None,
)


def current_sink() -> OutputSink | None:
    return _CURRENT_SINK.get()


def current_sink_setting(sink: OutputSink | None) -> ta.ContextManager[None]:
    return lang.context_var_setting(_CURRENT_SINK, sink)


##


class SinkPrint:
    """The `print` substitute: callable like the builtin."""

    def __init__(self, default_sink: ta.Callable[[], OutputSink | None]) -> None:
        super().__init__()

        self._default_sink = default_sink

    def __repr__(self) -> str:
        return '<repl print>'

    def __call__(
            self,
            *args: ta.Any,
            sep: str | None = ' ',
            end: str | None = '\n',
            file: ta.Any = None,
            flush: bool = False,
    ) -> None:
        if file is not None:
            builtins.print(*args, sep=sep, end=end, file=file, flush=flush)
            return

        sink = _CURRENT_SINK.get()
        if sink is None:
            sink = self._default_sink()
        if sink is None:
            builtins.print(*args, sep=sep, end=end, flush=flush)
            return

        buf = io.StringIO()
        builtins.print(*args, sep=sep, end=end, file=buf)
        if (text := buf.getvalue()):
            sink.write(StdoutOutput(text))


class Quitter:
    """`exit` / `quit`: a SystemExit the interpreter turns into an EXIT result rather than letting near the process."""

    def __init__(self, name: str) -> None:
        super().__init__()

        self._name = name

    def __repr__(self) -> str:
        return f'Use {self._name}() to leave the repl'

    def __call__(self, code: ta.Any = None) -> ta.NoReturn:
        raise SystemExit(code)


def make_builtins(
        print_fn: ta.Callable[..., None],
        *,
        base: ta.Mapping[str, ta.Any] | None = None,
) -> dict[str, ta.Any]:
    """A fresh builtins dict: `base` (the real builtins by default) with the substitutes laid over."""

    out = dict(vars(builtins)) if base is None else dict(base)
    out['print'] = print_fn
    out['exit'] = Quitter('exit')
    out['quit'] = Quitter('quit')
    return out
