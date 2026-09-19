import typing as ta

from ... import dataclasses as dc
from ... import lang
from . import ast
from .builtins import build_native_functions
from .compiler import Compiler
from .errors import JqInputEofError
from .options import JqRuntimeOptions
from .options import JqValueOptions
from .parsing import parse
from .regex import RegexEngine
from .regex import stdlib_regex_engine
from .runtime import CompiledFilter
from .runtime import JqEnvironment
from .runtime import JqEvalContext
from .runtime import JqFunction
from .runtime import JqInputSource
from .runtime import JqResult
from .values import JqValueOps


##


_DEFAULT_REGEX_ENGINE = object()


@lang.cached_function
def _prelude_ast() -> ast.Node:
    source = lang.get_relative_resources(globals=globals())['prelude.jq'].read_text()
    return parse(source)


def _link_prelude(node: ast.Node, query: ast.Node) -> ast.Node:
    if not isinstance(node, ast.FunctionDefinition):
        return query
    return dc.replace(node, next=_link_prelude(node.next, query))


##


@dc.dataclass(frozen=True)
class JqProgram:
    source: str
    filter: CompiledFilter
    native_functions: ta.Mapping[tuple[str, int], JqFunction]
    value_options: JqValueOptions = JqValueOptions()
    runtime_options: JqRuntimeOptions = JqRuntimeOptions()
    regex_engine: RegexEngine | None = dc.field(default_factory=stdlib_regex_engine)

    @staticmethod
    def _environment(variables: ta.Mapping[str, ta.Any] | None) -> JqEnvironment:
        if variables is None:
            return JqEnvironment()
        return JqEnvironment(variables={
            name.removeprefix('$'): JqResult(value)
            for name, value in variables.items()
        })

    def _context(
            self,
            input_source: JqInputSource,
            *,
            runtime_options: JqRuntimeOptions | None,
    ) -> JqEvalContext:
        return JqEvalContext(
            value_ops=JqValueOps(self.value_options),
            options=runtime_options if runtime_options is not None else self.runtime_options,
            input_source=input_source,
            native_functions=self.native_functions,
            regex_engine=self.regex_engine,
        )

    def evaluate(
            self,
            value: ta.Any,
            *,
            inputs: ta.Iterable[ta.Any] = (),
            variables: ta.Mapping[str, ta.Any] | None = None,
            runtime_options: JqRuntimeOptions | None = None,
    ) -> ta.Iterator[ta.Any]:
        source = JqInputSource(inputs)
        context = self._context(source, runtime_options=runtime_options)
        environment = self._environment(variables)
        context.value_ops.type_name(value)
        for result in self.filter(context, JqResult(value, ()), environment):
            yield result.value

    def run(
            self,
            inputs: ta.Iterable[ta.Any],
            *,
            null_input: bool = False,
            variables: ta.Mapping[str, ta.Any] | None = None,
            runtime_options: JqRuntimeOptions | None = None,
    ) -> ta.Iterator[ta.Any]:
        source = JqInputSource(inputs)
        context = self._context(source, runtime_options=runtime_options)
        environment = self._environment(variables)
        if null_input:
            for result in self.filter(context, JqResult(None, ()), environment):
                yield result.value
            return

        while True:
            try:
                value = source.take()
            except JqInputEofError:
                return
            context.value_ops.type_name(value)
            for result in self.filter(context, JqResult(value, ()), environment):
                yield result.value


def compile_jq(
        source: str,
        *,
        value_options: JqValueOptions = JqValueOptions(),
        runtime_options: JqRuntimeOptions = JqRuntimeOptions(),
        regex_engine: RegexEngine | None | object = _DEFAULT_REGEX_ENGINE,
        include_prelude: bool = True,
) -> JqProgram:
    native_functions = build_native_functions()
    parsed = parse(source)
    if include_prelude:
        parsed = _link_prelude(_prelude_ast(), parsed)
    compiled = Compiler().compile(parsed)
    if regex_engine is _DEFAULT_REGEX_ENGINE:
        regex_engine = stdlib_regex_engine()
    return JqProgram(
        source,
        compiled,
        native_functions,
        value_options,
        runtime_options,
        ta.cast('RegexEngine | None', regex_engine),
    )
