import collections.abc
import typing as ta

from ... import dataclasses as dc
from . import ast
from .errors import JqNameError
from .errors import JqPathError
from .errors import JqRecursionError
from .errors import JqRuntimeError
from .errors import JqTypeError
from .runtime import BreakSignal
from .runtime import CompiledFilter
from .runtime import FilterArgument
from .runtime import JqEnvironment
from .runtime import JqEvalContext
from .runtime import JqFunction
from .runtime import JqResult


##


@dc.dataclass(frozen=True)
class FilterParameterFunction(JqFunction):
    name: str
    argument: FilterArgument

    @property
    def arity(self) -> int:
        return 0

    def invoke(
            self,
            context: JqEvalContext,
            value: JqResult,
            arguments: ta.Sequence[FilterArgument],
    ) -> ta.Iterator[JqResult]:
        if arguments:
            raise JqRuntimeError(f'filter parameter {self.name} does not accept arguments')
        yield from self.argument.evaluate(context, value)


@dc.dataclass(frozen=True)
class UserFunction(JqFunction):
    name: str
    parameters: tuple[ast.FunctionParameter, ...]
    body: CompiledFilter
    environment: JqEnvironment

    @property
    def arity(self) -> int:
        return len(self.parameters)

    def _invoke_bindings(
            self,
            context: JqEvalContext,
            value: JqResult,
            arguments: ta.Sequence[FilterArgument],
            offset: int,
            variables: dict[str, JqResult],
            functions: dict[tuple[str, int], JqFunction],
    ) -> ta.Iterator[JqResult]:
        if offset == len(self.parameters):
            environment = JqEnvironment(
                parent=self.environment,
                variables=variables,
                functions=functions,
            )
            yield from self.body(context, value, environment)
            return

        parameter = self.parameters[offset]
        argument = arguments[offset]
        if not parameter.binding:
            next_functions = {
                **functions,
                (parameter.name, 0): FilterParameterFunction(parameter.name, argument),
            }
            yield from self._invoke_bindings(
                context,
                value,
                arguments,
                offset + 1,
                variables,
                next_functions,
            )
            return

        for bound in argument.evaluate(context, value):
            yield from self._invoke_bindings(
                context,
                value,
                arguments,
                offset + 1,
                {**variables, parameter.name: bound},
                functions,
            )

    def invoke(
            self,
            context: JqEvalContext,
            value: JqResult,
            arguments: ta.Sequence[FilterArgument],
    ) -> ta.Iterator[JqResult]:
        context.enter_user_function()
        try:
            try:
                yield from self._invoke_bindings(
                    context,
                    value,
                    arguments,
                    0,
                    {},
                    {},
                )
            except JqRecursionError:
                raise
            except RecursionError as exc:
                if context.options.max_recursion_depth is None:
                    raise
                raise JqRecursionError('host recursion limit reached during jq function recursion') from exc
        finally:
            context.leave_user_function()


##


class Compiler:
    def compile(
            self,
            node: ast.Node,
            labels: ta.Mapping[str, object] | None = None,
    ) -> CompiledFilter:
        if labels is None:
            labels = {}

        if isinstance(node, ast.Identity):
            def identity(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                del context, environment
                yield value

            return identity

        if isinstance(node, ast.Empty):
            def empty(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                del context, value, environment
                yield from ()

            return empty

        if isinstance(node, ast.Literal):
            def literal(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                del context, value, environment
                yield JqResult(node.value)

            return literal

        if isinstance(node, ast.Variable):
            def variable(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                del value
                result = environment.find_variable(node.name)
                context.value_ops.type_name(result.value)
                yield result

            return variable

        if isinstance(node, ast.Call):
            arguments = tuple(
                self.compile(argument, labels)
                for argument in node.arguments
            )

            def call(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                filter_arguments = tuple(
                    FilterArgument(argument, environment)
                    for argument in arguments
                )
                yield from context.invoke(
                    environment,
                    node.name,
                    value,
                    filter_arguments,
                )

            return call

        if isinstance(node, ast.Comma):
            left = self.compile(node.left, labels)
            right = self.compile(node.right, labels)

            def comma(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                yield from left(context, value, environment)
                yield from right(context, value, environment)

            return comma

        if isinstance(node, ast.Pipe):
            left = self.compile(node.left, labels)
            right = self.compile(node.right, labels)

            def pipe(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                for intermediate in left(context, value, environment):
                    yield from right(context, intermediate, environment)

            return pipe

        if isinstance(node, ast.Array):
            child = self.compile(node.value, labels) if node.value is not None else None

            def array(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                if child is None:
                    yield JqResult([])
                else:
                    yield JqResult([item.value for item in child(context, value, environment)])

            return array

        if isinstance(node, ast.Object):
            members = tuple(
                (self.compile(member.key, labels), self.compile(member.value, labels))
                for member in node.members
            )

            def object_filter(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                def build(offset: int, current: dict[str, ta.Any]) -> ta.Iterator[dict[str, ta.Any]]:
                    if offset == len(members):
                        yield current
                        return
                    key_filter, value_filter = members[offset]
                    for key_result in key_filter(context, value, environment):
                        if not isinstance(key_result.value, str):
                            raise JqTypeError('object keys must be strings')
                        for member_value in value_filter(context, value, environment):
                            yield from build(offset + 1, {**current, key_result.value: member_value.value})

                for result in build(0, {}):
                    yield JqResult(result)

            return object_filter

        if isinstance(node, ast.Index):
            value_filter = self.compile(node.value, labels)
            key_filter = self.compile(node.key, labels)

            def index(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                for key in key_filter(context, value, environment):
                    for indexed in value_filter(context, value, environment):
                        result_path = None
                        if indexed.path is not None:
                            if isinstance(key.value, str):
                                result_path = (*indexed.path, key.value)
                            elif (array_index := context.value_ops.array_index(key.value)) is not None:
                                result_path = (*indexed.path, array_index)
                        result = context.value_ops.index(indexed.value, key.value)
                        context.value_ops.type_name(result)
                        yield JqResult(result, result_path)

            return index

        if isinstance(node, ast.Iterate):
            value_filter = self.compile(node.value, labels)

            def iterate(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                for iterable in value_filter(context, value, environment):
                    for component, item in context.value_ops.iterate(iterable.value):
                        context.value_ops.type_name(item)
                        path = (*iterable.path, component) if iterable.path is not None else None
                        yield JqResult(item, path)

            return iterate

        if isinstance(node, ast.Slice):
            value_filter = self.compile(node.value, labels)
            start_filter = self.compile(node.start, labels) if node.start is not None else None
            end_filter = self.compile(node.end, labels) if node.end is not None else None

            def slice_filter(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                starts = (
                    start_filter(context, value, environment)
                    if start_filter is not None else
                    iter((JqResult(None),))
                )
                for start in starts:
                    ends = (
                        end_filter(context, value, environment)
                        if end_filter is not None else
                        iter((JqResult(None),))
                    )
                    for end in ends:
                        for sliced in value_filter(context, value, environment):
                            yield JqResult(context.value_ops.slice(sliced.value, start.value, end.value))

            return slice_filter

        if isinstance(node, ast.Optional):
            optional_child = self.compile(node.value, labels)

            def optional(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                try:
                    yield from optional_child(context, value, environment)
                except JqRuntimeError:
                    return

            return optional

        if isinstance(node, ast.RecursiveDescent):
            def recursive(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                del environment
                yield value

                active: set[int] = set()

                def children(parent: JqResult) -> ta.Iterator[JqResult]:
                    parent_type = context.value_ops.type_name(parent.value)
                    if parent_type != 'array' and parent_type != 'object':
                        return
                    parent_id = id(parent.value)
                    if parent_id in active:
                        context.value_ops.validate(parent.value)
                    active.add(parent_id)
                    try:
                        for component, item in context.value_ops.iterate(parent.value):
                            path = (*parent.path, component) if parent.path is not None else None
                            yield JqResult(item, path)
                    finally:
                        active.remove(parent_id)

                stack: list[ta.Iterator[JqResult]] = [children(value)]
                while stack:
                    try:
                        child_value = next(stack[-1])
                    except StopIteration:
                        stack.pop()
                        continue
                    yield child_value
                    stack.append(children(child_value))

            return recursive

        if isinstance(node, ast.Unary):
            operand = self.compile(node.operand, labels)

            def unary(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                for item in operand(context, value, environment):
                    yield JqResult(context.value_ops.negate(item.value))

            return unary

        if isinstance(node, ast.Binary):
            return self._compile_binary(node, labels)

        if isinstance(node, ast.Alternative):
            left = self.compile(node.left, labels)
            right = self.compile(node.right, labels)

            def alternative(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                found = False
                for result in left(context, value, environment):
                    if context.value_ops.truthy(result.value):
                        found = True
                        yield result
                if not found:
                    yield from right(context, value, environment)

            return alternative

        if isinstance(node, ast.Assignment):
            return self._compile_assignment(node, labels)

        if isinstance(node, ast.Binding):
            source = self.compile(node.source, labels)
            body = self.compile(node.body, labels)

            def binding(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                for bound in source(context, value, environment):
                    yield from body(context, value, environment.with_variables({node.name: bound}))

            return binding

        if isinstance(node, ast.Conditional):
            branches = tuple(
                (self.compile(branch.condition, labels), self.compile(branch.body, labels))
                for branch in node.branches
            )
            otherwise = self.compile(node.otherwise, labels)

            def conditional(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                def choose(offset: int) -> ta.Iterator[JqResult]:
                    if offset == len(branches):
                        yield from otherwise(context, value, environment)
                        return
                    condition, body = branches[offset]
                    for condition_value in condition(context, value, environment):
                        if context.value_ops.truthy(condition_value.value):
                            yield from body(context, value, environment)
                        else:
                            yield from choose(offset + 1)

                yield from choose(0)

            return conditional

        if isinstance(node, ast.FunctionDefinition):
            body = self.compile(node.body, labels)
            next_filter = self.compile(node.next, labels)

            def definition(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                functions: dict[tuple[str, int], JqFunction] = {}
                definition_environment = JqEnvironment(parent=environment, functions=functions)
                function = UserFunction(node.name, node.parameters, body, definition_environment)
                functions[(node.name, len(node.parameters))] = function
                yield from next_filter(context, value, definition_environment)

            return definition

        if isinstance(node, ast.Reduce):
            source = self.compile(node.source, labels)
            initial = self.compile(node.initial, labels)
            update = self.compile(node.update, labels)

            def reduce_filter(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                for initial_value in initial(context, value, environment):
                    state = initial_value
                    for item in source(context, value, environment):
                        item_environment = environment.with_variables({node.variable: item})
                        previous = state
                        state = JqResult(None)
                        for updated in update(context, previous, item_environment):
                            state = updated
                    yield state

            return reduce_filter

        if isinstance(node, ast.Foreach):
            source = self.compile(node.source, labels)
            initial = self.compile(node.initial, labels)
            update = self.compile(node.update, labels)
            extract = self.compile(node.extract, labels)

            def foreach_filter(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                for initial_value in initial(context, value, environment):
                    state = initial_value
                    for item in source(context, value, environment):
                        item_environment = environment.with_variables({node.variable: item})
                        previous = state
                        state = JqResult(None)
                        for updated in update(context, previous, item_environment):
                            state = updated
                            yield from extract(context, updated, item_environment)

            return foreach_filter

        if isinstance(node, ast.Try):
            child = self.compile(node.value, labels)
            handler = self.compile(node.handler, labels) if node.handler is not None else None

            def try_filter(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                try:
                    yield from child(context, value, environment)
                except JqRuntimeError as exc:
                    if handler is not None:
                        yield from handler(context, JqResult(exc.payload), environment)

            return try_filter

        if isinstance(node, ast.Label):
            token = object()
            body = self.compile(node.body, {**labels, node.name: token})

            def label(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                try:
                    yield from body(context, value, environment)
                except BreakSignal as signal:
                    if signal.token is not token:
                        raise

            return label

        if isinstance(node, ast.Break):
            try:
                token = labels[node.name]
            except KeyError:
                raise JqNameError(f'break references out-of-scope label ${node.name}') from None

            def break_filter(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                del context, value, environment
                raise BreakSignal(token)

            return break_filter

        if isinstance(node, ast.String):
            parts = tuple(
                part if isinstance(part, str) else self.compile(part, labels)
                for part in node.parts
            )

            def string(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                def build(offset: int, current: str) -> ta.Iterator[str]:
                    if offset == len(parts):
                        yield current
                        return
                    part = parts[offset]
                    if isinstance(part, str):
                        yield from build(offset + 1, current + part)
                    else:
                        for interpolation in part(context, value, environment):
                            yield from build(offset + 1, current + context.value_ops.tostring(interpolation.value))

                for result in build(0, ''):
                    yield JqResult(result)

            return string

        raise TypeError(node)

    def _compile_binary(
            self,
            node: ast.Binary,
            labels: ta.Mapping[str, object],
    ) -> CompiledFilter:
        left = self.compile(node.left, labels)
        right = self.compile(node.right, labels)

        def binary(
                context: JqEvalContext,
                value: JqResult,
                environment: JqEnvironment,
        ) -> ta.Iterator[JqResult]:
            operator = node.operator
            if operator == 'and' or operator == 'or':
                for left_value in left(context, value, environment):
                    left_truth = context.value_ops.truthy(left_value.value)
                    if (operator == 'and' and not left_truth) or (operator == 'or' and left_truth):
                        yield JqResult(left_truth)
                        continue
                    for right_value in right(context, value, environment):
                        yield JqResult(context.value_ops.truthy(right_value.value))
                return

            for right_value in right(context, value, environment):
                for left_value in left(context, value, environment):
                    if operator == '+':
                        result = context.value_ops.add(left_value.value, right_value.value)
                    elif operator == '-':
                        result = context.value_ops.subtract(left_value.value, right_value.value)
                    elif operator == '*':
                        result = context.value_ops.multiply(left_value.value, right_value.value)
                    elif operator == '/':
                        result = context.value_ops.divide(left_value.value, right_value.value)
                    elif operator == '%':
                        result = context.value_ops.modulo(left_value.value, right_value.value)
                    elif operator == '==':
                        result = context.value_ops.equal(left_value.value, right_value.value)
                    elif operator == '!=':
                        result = not context.value_ops.equal(left_value.value, right_value.value)
                    elif operator == '<':
                        result = context.value_ops.compare(left_value.value, right_value.value) < 0
                    elif operator == '<=':
                        result = context.value_ops.compare(left_value.value, right_value.value) <= 0
                    elif operator == '>':
                        result = context.value_ops.compare(left_value.value, right_value.value) > 0
                    elif operator == '>=':
                        result = context.value_ops.compare(left_value.value, right_value.value) >= 0
                    else:
                        raise JqRuntimeError(f'unknown binary operator {operator}')
                    yield JqResult(result)

        return binary

    def _compile_assignment(
            self,
            node: ast.Assignment,
            labels: ta.Mapping[str, object],
    ) -> CompiledFilter:
        left = self.compile(node.left, labels)
        right = self.compile(node.right, labels)

        def paths(
                context: JqEvalContext,
                value: JqResult,
                environment: JqEnvironment,
        ) -> list[tuple[str | int, ...]]:
            result: list[tuple[str | int, ...]] = []
            for selected in left(context, JqResult(value.value, ()), environment):
                if selected.path is None:
                    raise JqPathError('assignment left-hand side does not produce a path')
                current = value.value
                resolved: list[str | int] = []
                for component in selected.path:
                    if isinstance(component, int) and component < 0 and context.value_ops.is_sequence(current):
                        component += len(current)
                    resolved.append(component)
                    current = context.value_ops.index(current, component)
                result.append(tuple(resolved))
            return result

        if node.operator == '=':
            def assign(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                for replacement in right(context, value, environment):
                    result = value.value
                    for path in paths(context, value, environment):
                        result = context.value_ops.setpath(result, path, replacement.value)
                    yield JqResult(result)

            return assign

        if node.operator != '|=':
            def compound(
                    context: JqEvalContext,
                    value: JqResult,
                    environment: JqEnvironment,
            ) -> ta.Iterator[JqResult]:
                for right_value in right(context, value, environment):
                    result = value.value
                    for path in paths(context, value, environment):
                        old = context.value_ops.getpath(result, path)
                        replacement = self._compound_value(
                            context,
                            old,
                            right_value.value,
                            node.operator,
                        )
                        result = context.value_ops.setpath(result, path, replacement)
                    yield JqResult(result)

            return compound

        def update(
                context: JqEvalContext,
                value: JqResult,
                environment: JqEnvironment,
        ) -> ta.Iterator[JqResult]:
            result = value.value
            selected_paths: list[tuple[str | int, ...] | None] = list(paths(context, value, environment))
            for offset, path in enumerate(selected_paths):
                if path is None:
                    continue
                old = context.value_ops.getpath(result, path)
                old_result = JqResult(old)

                outputs = right(context, old_result, environment)

                try:
                    replacement = next(outputs)
                except StopIteration:
                    result = context.value_ops.delpaths(result, [path])
                    for later in range(offset + 1, len(selected_paths)):
                        if (later_path := selected_paths[later]) is not None:
                            selected_paths[later] = self._rebase_after_delete(later_path, path)
                else:
                    result = context.value_ops.setpath(result, path, replacement.value)
                finally:
                    if isinstance(outputs, collections.abc.Generator):
                        outputs.close()
            yield JqResult(result)

        return update

    @staticmethod
    def _rebase_after_delete(
            path: tuple[str | int, ...],
            deleted: tuple[str | int, ...],
    ) -> tuple[str | int, ...] | None:
        if len(path) >= len(deleted) and path[:len(deleted)] == deleted:
            return None
        if not deleted or not isinstance(deleted[-1], int):
            return path
        parent = deleted[:-1]
        if len(path) <= len(parent) or path[:len(parent)] != parent:
            return path
        component = path[len(parent)]
        if not isinstance(component, int) or component < deleted[-1]:
            return path
        if component == deleted[-1]:
            return None
        return (*parent, component - 1, *path[len(parent) + 1:])

    @staticmethod
    def _compound_value(
            context: JqEvalContext,
            left: ta.Any,
            right: ta.Any,
            operator: str,
    ) -> ta.Any:
        if operator == '+=':
            return context.value_ops.add(left, right)
        if operator == '-=':
            return context.value_ops.subtract(left, right)
        if operator == '*=':
            return context.value_ops.multiply(left, right)
        if operator == '/=':
            return context.value_ops.divide(left, right)
        if operator == '%=':
            return context.value_ops.modulo(left, right)
        if operator == '//=':
            return left if context.value_ops.truthy(left) else right
        raise JqRuntimeError(f'unknown assignment operator {operator}')
