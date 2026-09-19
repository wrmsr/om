import abc
import typing as ta

from ... import dataclasses as dc
from ... import lang
from .errors import JqInputEofError
from .errors import JqRecursionError
from .errors import JqRuntimeError
from .options import JqRuntimeOptions
from .values import JqPath
from .values import JqValueOps


##


@dc.dataclass(frozen=True)
class JqResult:
    value: ta.Any
    path: JqPath | None = None


type CompiledFilter = ta.Callable[['JqEvalContext', JqResult, 'JqEnvironment'], ta.Iterator[JqResult]]


@dc.dataclass(frozen=True)
class FilterArgument:
    filter: CompiledFilter
    environment: JqEnvironment

    def evaluate(self, context: JqEvalContext, value: JqResult) -> ta.Iterator[JqResult]:
        yield from self.filter(context, value, self.environment)


class JqFunction(lang.Abstract):
    name: str

    @abc.abstractmethod
    def invoke(
            self,
            context: JqEvalContext,
            value: JqResult,
            arguments: ta.Sequence[FilterArgument],
    ) -> ta.Iterator[JqResult]:
        raise NotImplementedError


@dc.dataclass(frozen=True)
class JqEnvironment:
    parent: JqEnvironment | None = None
    variables: ta.Mapping[str, JqResult] = dc.field(default_factory=dict)
    functions: ta.Mapping[tuple[str, int], JqFunction] = dc.field(default_factory=dict)

    def with_variables(self, variables: ta.Mapping[str, JqResult]) -> JqEnvironment:
        return JqEnvironment(parent=self, variables=variables)

    def with_functions(self, functions: ta.Mapping[tuple[str, int], JqFunction]) -> JqEnvironment:
        return JqEnvironment(parent=self, functions=functions)

    def find_variable(self, name: str) -> JqResult:
        environment: JqEnvironment | None = self
        while environment is not None:
            if name in environment.variables:
                return environment.variables[name]
            environment = environment.parent
        raise JqRuntimeError(f'undefined jq variable ${name}')

    def find_function(self, name: str, arity: int) -> JqFunction | None:
        key = (name, arity)
        environment: JqEnvironment | None = self
        while environment is not None:
            if (function := environment.functions.get(key)) is not None:
                return function
            environment = environment.parent
        return None


class JqInputSource:
    def __init__(self, values: ta.Iterable[ta.Any] = ()) -> None:
        super().__init__()

        self._iterator = iter(values)

    def take(self) -> ta.Any:
        try:
            return next(self._iterator)
        except StopIteration:
            raise JqInputEofError('input exhausted') from None


@dc.dataclass(kw_only=True)
class JqEvalContext:
    value_ops: JqValueOps
    options: JqRuntimeOptions
    input_source: JqInputSource
    native_functions: ta.Mapping[tuple[str, int], JqFunction]
    regex_engine: ta.Any = None

    recursion_depth: int = 0

    def invoke(
            self,
            environment: JqEnvironment,
            name: str,
            value: JqResult,
            arguments: ta.Sequence[FilterArgument],
    ) -> ta.Iterator[JqResult]:
        function = environment.find_function(name, len(arguments))
        if function is None:
            function = self.native_functions.get((name, len(arguments)))
        if function is None:
            raise JqRuntimeError(f'function not defined: {name}/{len(arguments)}')
        yield from function.invoke(self, value, arguments)

    def enter_user_function(self) -> None:
        self.recursion_depth += 1
        if (limit := self.options.max_recursion_depth) is not None and self.recursion_depth > limit:
            self.recursion_depth -= 1
            raise JqRecursionError(f'jq recursion depth exceeds {limit}')

    def leave_user_function(self) -> None:
        self.recursion_depth -= 1


class BreakSignal(Exception):  # noqa: N818
    def __init__(self, token: object) -> None:
        super().__init__()

        self.token = token
