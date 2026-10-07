"""
The python interpreter: the builtin repl's semantics as a good citizen inside a process it does not own.

Per statement, as the builtin repl: the source parses to a module, each statement compiles and runs on its own, and a
final bare expression evaluates with its value shown (and bound to `_`). The namespace is this interpreter's own dict,
with its own copy of the builtins (`print` writing to the execution's sink; `exit`/`quit` ending the execution, not the
process) - nothing on `sys` is read or written: no displayhook, no excepthook, no `last_*`, no prompts. Tracebacks are
trimmed to the frames of the executed code.

Top-level `await` is allowed by default (the asyncio repl's compile flag): a statement which awaits compiles to a
coroutine, awaited inline - on whichever loop the caller is on, with whatever the caller can reach. A frontend without a
loop drives under `lang.sync_await`, where a source which really awaits fails as it should; such frontends turn the
flag off and get a syntax error instead.
"""
import ast
import inspect
import traceback
import types
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang

from ..executors import Executor
from ..executors import ImmediateExecutor
from ..interpreters import Completion
from ..interpreters import Interpreter
from ..interpreters import Result
from ..interpreters import ResultStatus
from ..languages import PYTHON_LANGUAGE
from ..languages import Language
from ..outputs import ErrorOutput
from ..outputs import OutputSink
from ..outputs import ResultOutput
from .builtins import SinkPrint
from .builtins import current_sink_setting
from .builtins import make_builtins
from .completion import complete_python


##


class PythonInterpreter(Interpreter):
    @dc.dataclass(frozen=True, kw_only=True)
    class Config:
        module_name: str = '__console__'
        filename: str = '<input>'
        allow_await: bool = True
        bind_result: bool = True  # the `_` convention

    def __init__(
            self,
            namespace: ta.Mapping[str, ta.Any] | None = None,
            *,
            config: Config | None = None,
            builtins_base: ta.Mapping[str, ta.Any] | None = None,
            executor: Executor | None = None,
            default_sink: OutputSink | None = None,
    ) -> None:
        """
        `namespace` seeds the interpreter's own; `builtins_base` stands in for the real builtins as what the substitutes
        lay over (a restricted set, for a sandbox). `default_sink` is where `print` goes with no execution under way.
        """

        super().__init__()

        self._config = config if config is not None else self.Config()
        self._executor = executor if executor is not None else ImmediateExecutor()
        self._default_sink = default_sink

        self._namespace: dict[str, ta.Any] = {
            '__name__': self._config.module_name,
            '__doc__': None,
            '__builtins__': make_builtins(SinkPrint(lambda: self._default_sink), base=builtins_base),
        }
        if namespace:
            self._namespace.update(namespace)

    @property
    def language(self) -> Language:
        return PYTHON_LANGUAGE

    @property
    def config(self) -> Config:
        return self._config

    @property
    def namespace(self) -> dict[str, ta.Any]:
        """The live globals - deliberately the mutable dict itself: the host's hook for seeding and poking."""

        return self._namespace

    @property
    def default_sink(self) -> OutputSink | None:
        return self._default_sink

    def set_default_sink(self, sink: OutputSink | None) -> None:
        self._default_sink = sink

    ##
    # Execution

    def _compile_flags(self) -> int:
        return ast.PyCF_ALLOW_TOP_LEVEL_AWAIT if self._config.allow_await else 0

    async def execute(self, source: str, sink: OutputSink) -> Result:
        with current_sink_setting(sink):
            return await self._execute(source, sink)

    async def _execute(self, source: str, sink: OutputSink) -> Result:
        try:
            tree = compile(source, self._config.filename, 'exec', ast.PyCF_ONLY_AST | self._compile_flags())
        except (SyntaxError, OverflowError, ValueError) as e:
            return self._fail(sink, e)

        body = check.isinstance(tree, ast.Module).body
        if not body:
            return Result(ResultStatus.OK)

        *leading, last = body
        for stmt in leading:
            result = await self._run_node(ast.Module(body=[stmt], type_ignores=[]), 'exec', sink)
            if not result.ok:
                return result

        if isinstance(last, ast.Expr):
            return await self._run_node(ast.Expression(body=last.value), 'eval', sink)
        return await self._run_node(ast.Module(body=[last], type_ignores=[]), 'exec', sink)

    async def _run_node(self, node: ast.Module | ast.Expression, mode: str, sink: OutputSink) -> Result:
        ast.fix_missing_locations(node)
        try:
            code: types.CodeType = compile(node, self._config.filename, mode, self._compile_flags())
        except (SyntaxError, OverflowError, ValueError) as e:
            return self._fail(sink, e)

        namespace = self._namespace

        def run() -> ta.Any:
            # A function over the code object rather than exec/eval: it hands back the coroutine a top-level await
            # compiles to, and the value of an expression, alike.
            return types.FunctionType(code, namespace)()

        try:
            value = await self._executor.run(run)
            if code.co_flags & inspect.CO_COROUTINE:
                value = await value
        except SystemExit as e:
            return Result(ResultStatus.EXIT, error=e)
        except Exception as e:  # noqa: BLE001
            return self._fail(sink, e)

        if mode != 'eval':
            return Result(ResultStatus.OK)

        if value is not None:
            if self._config.bind_result:
                namespace['_'] = value
            try:
                text = self.format_value(value)
            except Exception as e:  # noqa: BLE001
                return self._fail(sink, e)
            sink.write(ResultOutput(text))

        return Result(ResultStatus.OK, lang.just(value))

    def format_value(self, value: ta.Any) -> str:
        return repr(value)

    ##
    # Errors

    def _fail(self, sink: OutputSink, e: BaseException) -> Result:
        sink.write(ErrorOutput(self.format_error(e)))
        return Result(ResultStatus.ERROR, error=e)

    def format_error(self, e: BaseException) -> str:
        """The traceback as the builtin repl shows it: the user's frames only, none of the machinery around them."""

        if isinstance(e, SyntaxError):
            return ''.join(traceback.format_exception(type(e), e, None)).rstrip('\n')

        tb = e.__traceback__
        while tb is not None and tb.tb_frame.f_code.co_filename != self._config.filename:
            tb = tb.tb_next
        return ''.join(traceback.format_exception(type(e), e, tb)).rstrip('\n')

    ##
    # Completion

    def complete(self, source: str, cursor: int) -> ta.Sequence[Completion]:
        return complete_python(self._namespace, source, cursor)
