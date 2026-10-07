"""
The javascript interpreter, over the vendored quickjs engine - a strictly quarantined optional dependency (the extension
may not be built; `quickjs_available()` says). One engine context per interpreter, which may be handed in: a fresh one,
one some other part of the host is already running, one restored from a snapshot.

Evaluation goes through the executor - off the loop on a thread by default under asyncio, since the engine releases the
GIL and its interrupt flag is thread-safe - and `print` / `console.*` are python callables bound into the context. Those
run on the engine's thread, so their output is parked in a list (append is atomic) and written to the sink on the
caller's context once the evaluation returns: correct, at the cost of not streaming mid-evaluation.
"""
import importlib
import json
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ..executors import Executor
from ..executors import ImmediateExecutor
from ..interpreters import Interpreter
from ..interpreters import InterpreterBusyError
from ..interpreters import Result
from ..interpreters import ResultStatus
from ..languages import JAVASCRIPT_LANGUAGE
from ..languages import Language
from ..outputs import ErrorOutput
from ..outputs import Output
from ..outputs import OutputSink
from ..outputs import ResultOutput
from ..outputs import StdoutOutput


with lang.auto_proxy_import(globals()):
    from ...js import quickjs


##


_FORMATTER_SOURCE = """
(v) => {
    if (typeof v === 'function') {
        return '[Function' + (v.name ? ': ' + v.name : ' (anonymous)') + ']';
    }
    if (v instanceof Error) {
        return String(v);
    }
    if (typeof v === 'symbol') {
        return v.toString();
    }
    const s = JSON.stringify(v);
    return s === undefined ? String(v) : s;
}
"""


@lang.cached_function
def quickjs_available() -> bool:
    try:
        importlib.import_module('...js.quickjs', __package__)
    except ImportError:
        return False
    return True


##


class QuickjsInterpreter(Interpreter):
    @dc.dataclass(frozen=True, kw_only=True)
    class Config:
        filename: str = '<input>'
        strict: bool = False

        # Only for a context made here, not one handed in.
        with_std: bool = False
        with_bjson: bool = False
        memory_limit: int | None = None
        max_stack_size: int | None = None

        install_console: bool = True  # bind `print` and `console.*` into the context

    def __init__(
            self,
            context: quickjs.Context | None = None,
            *,
            config: Config | None = None,
            executor: Executor | None = None,
    ) -> None:
        super().__init__()

        self._config = config if config is not None else self.Config()
        self._executor = executor if executor is not None else ImmediateExecutor()

        if context is None:
            context = quickjs.Context(
                with_std=self._config.with_std,
                with_bjson=self._config.with_bjson,
            )
            if self._config.memory_limit is not None:
                context.set_memory_limit(self._config.memory_limit)
            if self._config.max_stack_size is not None:
                context.set_max_stack_size(self._config.max_stack_size)
        self._context = context

        # Output emitted on the engine's thread, awaiting the caller's context. list.append is atomic.
        self._parked: list[Output] = []
        self._busy = False

        # A js-side formatter, held as a handle rather than bound to a global: what json cannot say (functions, errors,
        # symbols) the engine can.
        self._formatter = self._context.eval(_FORMATTER_SOURCE, filename='<repl>')

        if self._config.install_console:
            self._install_console()

    @property
    def language(self) -> Language:
        return JAVASCRIPT_LANGUAGE

    @property
    def context(self) -> quickjs.Context:
        """The live engine context - the host's hook for binding its own objects in, or sharing the context out."""

        return self._context

    ##
    # Console

    def _install_console(self) -> None:
        def emit(*args: ta.Any) -> None:
            self._parked.append(StdoutOutput(' '.join(self._format_arg(a) for a in args) + '\n'))

        self._context.set('print', emit)
        self._context.set('console', {
            'log': emit,
            'info': emit,
            'warn': emit,
            'error': emit,
            'debug': emit,
        })

    def _format_arg(self, value: ta.Any) -> str:
        """A console argument: strings as they are, like console.log; everything else as a result would show."""

        return value if isinstance(value, str) else self.format_value(value)

    def format_value(self, value: ta.Any) -> str:
        if value is None:
            return 'undefined'
        if isinstance(value, bool):
            return 'true' if value else 'false'
        if isinstance(value, (int, float, str)):
            return json.dumps(value)
        if isinstance(value, quickjs.Object):
            try:
                text = self._formatter(value)
            except quickjs.JsError:
                text = value.json()
            return text if isinstance(text, str) else '[object]'
        return repr(value)

    def _format_error(self, e: BaseException) -> str:
        text = str(e)
        if (stack := getattr(e, 'js_stack', None)):
            text = f'{text}\n{stack.rstrip()}'
        return text

    ##
    # Execution

    def _flush(self, sink: OutputSink) -> None:
        parked, self._parked = self._parked, []
        for output in parked:
            sink.write(output)

    async def execute(self, source: str, sink: OutputSink) -> Result:
        if self._busy:
            raise InterpreterBusyError

        self._busy = True
        try:
            return await self._execute(source, sink)
        finally:
            self._busy = False

    async def _execute(self, source: str, sink: OutputSink) -> Result:
        config = self._config
        context = self._context

        try:
            value = await self._executor.run(
                lambda: context.eval(source, filename=config.filename, strict=config.strict),
                interrupt=context.interrupt,
            )

            # Settle the jobs the evaluation queued - then-callbacks, async function bodies - before judging a promise.
            await self._executor.run(context.execute_pending_jobs, interrupt=context.interrupt)

        except quickjs.JsError as e:
            self._flush(sink)
            sink.write(ErrorOutput(self._format_error(e)))
            return Result(ResultStatus.ERROR, error=e)

        self._flush(sink)

        if isinstance(value, quickjs.Object) and (state := value.promise_state()) is not None:
            if state == 'fulfilled':
                value = value.promise_result()
            elif state == 'rejected':
                try:
                    reason = self._format_arg(value.promise_result())
                except quickjs.JsError as e:
                    reason = self._format_error(e)
                sink.write(ErrorOutput(f'Uncaught (in promise) {reason}'))
                return Result(ResultStatus.ERROR)
            else:
                sink.write(ResultOutput('Promise { <pending> }'))
                return Result(ResultStatus.OK, lang.just(value))

        if value is not None:
            sink.write(ResultOutput(self.format_value(value)))

        return Result(ResultStatus.OK, lang.just(value))

    def interrupt(self) -> None:
        self._context.interrupt()
