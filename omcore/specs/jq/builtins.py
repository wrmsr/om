import functools
import json
import math
import typing as ta

from ... import dataclasses as dc
from .errors import JqRegexUnavailableError
from .errors import JqThrownError
from .errors import JqTypeError
from .errors import JqValueError
from .regex import RegexEngine
from .regex import regex_capture_object
from .regex import regex_match_object
from .runtime import FilterArgument
from .runtime import JqEvalContext
from .runtime import JqFunction
from .runtime import JqResult
from .streaming import tostream


type NativeFunctionImpl = ta.Callable[
    [JqEvalContext, JqResult, ta.Sequence[FilterArgument]],
    ta.Iterator[JqResult],
]


##


@dc.dataclass(frozen=True)
class NativeFunction(JqFunction):
    name: str
    arity: int
    implementation: NativeFunctionImpl

    def invoke(
            self,
            context: JqEvalContext,
            value: JqResult,
            arguments: ta.Sequence[FilterArgument],
    ) -> ta.Iterator[JqResult]:
        yield from self.implementation(context, value, arguments)


def _argument_values(
        context: JqEvalContext,
        value: JqResult,
        arguments: ta.Sequence[FilterArgument],
        offset: int = 0,
        values: tuple[JqResult, ...] = (),
) -> ta.Iterator[tuple[JqResult, ...]]:
    if offset == len(arguments):
        yield values
        return
    for argument_value in arguments[offset].evaluate(context, value):
        yield from _argument_values(context, value, arguments, offset + 1, (*values, argument_value))


def _type(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    del arguments
    yield JqResult(context.value_ops.type_name(value.value))


def _length(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    del arguments
    yield JqResult(context.value_ops.length(value.value))


def _keys(
        context: JqEvalContext,
        value: JqResult,
        arguments: ta.Sequence[FilterArgument],
        *,
        sorted_: bool,
) -> ta.Iterator[JqResult]:
    del arguments
    yield JqResult(context.value_ops.keys(value.value, sorted_=sorted_))


def _has(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    for values in _argument_values(context, value, arguments):
        yield JqResult(context.value_ops.has(value.value, values[0].value))


def _tostring(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    del arguments
    yield JqResult(context.value_ops.tostring(value.value))


def _tojson(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    del arguments
    yield JqResult(context.value_ops.tojson(value.value))


def _fromjson(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    del arguments
    yield JqResult(context.value_ops.fromjson(value.value))


def _tonumber(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    del arguments
    value_type = context.value_ops.type_name(value.value)
    if value_type == 'number':
        yield JqResult(value.value)
        return
    if value_type != 'string':
        raise JqTypeError('tonumber requires a string or number')
    try:
        number = json.loads(value.value)
    except (json.JSONDecodeError, ValueError) as exc:
        raise JqValueError(str(exc)) from exc
    if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number):
        raise JqValueError('string does not contain a finite number')
    yield JqResult(number)


def _not(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    del arguments
    yield JqResult(not context.value_ops.truthy(value.value))


def _error(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    if not arguments:
        raise JqThrownError(value.value)
    for values in _argument_values(context, value, arguments):
        raise JqThrownError(values[0].value)
    yield from ()


def _input(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    del value, arguments
    input_value = context.input_source.take()
    context.value_ops.type_name(input_value)
    yield JqResult(input_value)


def _range(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    for values in _argument_values(context, value, arguments):
        numbers = [item.value for item in values]
        if any(context.value_ops.type_name(number) != 'number' for number in numbers):
            raise JqTypeError('range arguments must be numbers')
        if len(numbers) == 1:
            start, stop, step = 0, numbers[0], 1
        elif len(numbers) == 2:
            start, stop = numbers
            step = 1
        else:
            start, stop, step = numbers
        if step == 0:
            continue
        current = start
        if step > 0:
            while current < stop:
                yield JqResult(current)
                current += step
        else:
            while current > stop:
                yield JqResult(current)
                current += step


def _path(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    root = JqResult(value.value, ())
    for result in arguments[0].evaluate(context, root):
        if result.path is None:
            raise JqValueError('path expression does not produce a path')
        yield JqResult(list(result.path))


def _getpath(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    for values in _argument_values(context, value, arguments):
        yield JqResult(context.value_ops.getpath(value.value, values[0].value))


def _setpath(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    for values in _argument_values(context, value, arguments):
        yield JqResult(context.value_ops.setpath(value.value, values[0].value, values[1].value))


def _delpaths(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    for values in _argument_values(context, value, arguments):
        paths = values[0].value
        if not context.value_ops.is_sequence(paths):
            raise JqTypeError('delpaths requires an array of paths')
        yield JqResult(context.value_ops.delpaths(value.value, paths))


def _contains(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    for values in _argument_values(context, value, arguments):
        yield JqResult(context.value_ops.contains(value.value, values[0].value))


def _inside(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    for values in _argument_values(context, value, arguments):
        yield JqResult(context.value_ops.contains(values[0].value, value.value))


def _string_predicate(
        context: JqEvalContext,
        value: JqResult,
        arguments: ta.Sequence[FilterArgument],
        predicate: ta.Callable[[str, str], bool],
) -> ta.Iterator[JqResult]:
    if not isinstance(value.value, str):
        raise JqTypeError('string operation requires a string input')
    for values in _argument_values(context, value, arguments):
        argument = values[0].value
        if not isinstance(argument, str):
            raise JqTypeError('string operation requires a string argument')
        yield JqResult(predicate(value.value, argument))


def _split(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    if not isinstance(value.value, str):
        raise JqTypeError('split requires a string input')
    for values in _argument_values(context, value, arguments):
        separator = values[0].value
        if not isinstance(separator, str):
            raise JqTypeError('split requires a string separator')
        if not separator:
            yield JqResult(list(value.value))
        else:
            yield JqResult(value.value.split(separator))


def _reverse(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    del arguments
    if not context.value_ops.is_sequence(value.value):
        raise JqTypeError('reverse requires an array')
    yield JqResult(list(reversed(value.value)))


def _sort(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    del arguments
    if not context.value_ops.is_sequence(value.value):
        raise JqTypeError('sort requires an array')
    yield JqResult(context.value_ops.sort(value.value))


def _keyed_values(
        context: JqEvalContext,
        value: JqResult,
        arguments: ta.Sequence[FilterArgument],
) -> ta.Iterator[list[tuple[ta.Any, ta.Any]]]:
    if not context.value_ops.is_sequence(value.value):
        raise JqTypeError('keyed collection operation requires an array')
    for values in _argument_values(context, value, arguments):
        keys = values[0].value
        if not context.value_ops.is_sequence(keys) or len(keys) != len(value.value):
            raise JqValueError('key array does not match input array')
        yield list(zip(keys, value.value))


def _sort_by_impl(
        context: JqEvalContext,
        value: JqResult,
        arguments: ta.Sequence[FilterArgument],
) -> ta.Iterator[JqResult]:
    compare = lambda left, right: context.value_ops.compare(left[0], right[0])
    for pairs in _keyed_values(context, value, arguments):
        pairs.sort(key=functools.cmp_to_key(compare))
        yield JqResult([item for _, item in pairs])


def _group_by_impl(
        context: JqEvalContext,
        value: JqResult,
        arguments: ta.Sequence[FilterArgument],
) -> ta.Iterator[JqResult]:
    compare = lambda left, right: context.value_ops.compare(left[0], right[0])
    for pairs in _keyed_values(context, value, arguments):
        pairs.sort(key=functools.cmp_to_key(compare))
        groups: list[list[ta.Any]] = []
        previous: ta.Any = _NOT_SET
        for key, item in pairs:
            if previous is _NOT_SET or not context.value_ops.equal(previous, key):
                groups.append([])
                previous = key
            groups[-1].append(item)
        yield JqResult(groups)


def _unique_by_impl(
        context: JqEvalContext,
        value: JqResult,
        arguments: ta.Sequence[FilterArgument],
) -> ta.Iterator[JqResult]:
    compare = lambda left, right: context.value_ops.compare(left[0], right[0])
    for pairs in _keyed_values(context, value, arguments):
        pairs.sort(key=functools.cmp_to_key(compare))
        result: list[ta.Any] = []
        previous: ta.Any = _NOT_SET
        for key, item in pairs:
            if previous is _NOT_SET or not context.value_ops.equal(previous, key):
                result.append(item)
                previous = key
        yield JqResult(result)


def _extreme_by_impl(
        context: JqEvalContext,
        value: JqResult,
        arguments: ta.Sequence[FilterArgument],
        *,
        maximum: bool,
) -> ta.Iterator[JqResult]:
    compare = lambda left, right: context.value_ops.compare(left[0], right[0])
    for pairs in _keyed_values(context, value, arguments):
        if not pairs:
            yield JqResult(None)
            continue
        pairs.sort(key=functools.cmp_to_key(compare))
        yield JqResult(pairs[-1 if maximum else 0][1])


def _indices(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    for values in _argument_values(context, value, arguments):
        needle = values[0].value
        value_type = context.value_ops.type_name(value.value)
        result: list[int] = []
        if value_type == 'string':
            if not isinstance(needle, str):
                raise JqTypeError('string indices require a string')
            if not needle:
                yield JqResult([])
                continue
            start = 0
            while True:
                index = value.value.find(needle, start)
                if index < 0:
                    break
                result.append(index)
                start = index + 1
        elif value_type == 'array':
            if context.value_ops.is_sequence(needle):
                width = len(needle)
                if not width:
                    yield JqResult([])
                    continue
                for index in range(len(value.value) - width + 1):
                    if context.value_ops.equal(value.value[index:index + width], needle):
                        result.append(index)
            else:
                for index, item in enumerate(value.value):
                    if context.value_ops.equal(item, needle):
                        result.append(index)
        else:
            raise JqTypeError('indices requires an array or string')
        yield JqResult(result)


def _extreme(
        context: JqEvalContext,
        value: JqResult,
        arguments: ta.Sequence[FilterArgument],
        *,
        maximum: bool,
) -> ta.Iterator[JqResult]:
    del arguments
    if not context.value_ops.is_sequence(value.value):
        raise JqTypeError('min/max requires an array')
    if not value.value:
        yield JqResult(None)
        return
    key = functools.cmp_to_key(context.value_ops.compare)
    function = max if maximum else min
    yield JqResult(function(value.value, key=key))


def _explode(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    del context, arguments
    if not isinstance(value.value, str):
        raise JqTypeError('explode requires a string')
    yield JqResult([ord(character) for character in value.value])


def _implode(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    del arguments
    if not context.value_ops.is_sequence(value.value):
        raise JqTypeError('implode requires an array')
    characters: list[str] = []
    for number in value.value:
        if context.value_ops.type_name(number) != 'number':
            raise JqTypeError('implode requires numeric Unicode codepoints')
        codepoint = int(number)
        if codepoint < 0 or codepoint > 0x10ffff or 0xd800 <= codepoint <= 0xdfff:
            codepoint = 0xfffd
        characters.append(chr(codepoint))
    yield JqResult(''.join(characters))


def _tostream(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    del arguments
    for stream_value in tostream(value.value, value_ops=context.value_ops):
        yield JqResult(stream_value)


def _regex_engine(context: JqEvalContext) -> RegexEngine:
    if context.regex_engine is None:
        raise JqRegexUnavailableError('regex support is disabled')
    if not isinstance(context.regex_engine, RegexEngine):
        raise TypeError(context.regex_engine)
    return context.regex_engine


def _regex_mode(value: ta.Any) -> str:
    if value is None:
        return ''
    if not isinstance(value, str):
        raise JqTypeError('regex flags must be a string or null')
    return value


def _match_impl(
        context: JqEvalContext,
        value: JqResult,
        arguments: ta.Sequence[FilterArgument],
) -> ta.Iterator[JqResult]:
    if not isinstance(value.value, str):
        raise JqTypeError('regex matching requires a string input')
    engine = _regex_engine(context)
    for values in _argument_values(context, value, arguments):
        pattern, mode, test = (item.value for item in values)
        if not isinstance(pattern, str):
            raise JqTypeError('regex pattern must be a string')
        if not isinstance(test, bool):
            raise JqTypeError('regex test mode must be a boolean')
        matches = engine.find(value.value, pattern, _regex_mode(mode))
        if test:
            yield JqResult(next(matches, None) is not None)
        else:
            yield JqResult([regex_match_object(match) for match in matches])


def _regex_splits(
        context: JqEvalContext,
        value: JqResult,
        arguments: ta.Sequence[FilterArgument],
        *,
        collect: bool,
) -> ta.Iterator[JqResult]:
    if not isinstance(value.value, str):
        raise JqTypeError('regex splitting requires a string input')
    engine = _regex_engine(context)
    for values in _argument_values(context, value, arguments):
        pattern = values[0].value
        mode = values[1].value if len(values) > 1 else ''
        if not isinstance(pattern, str):
            raise JqTypeError('regex pattern must be a string')
        flags = _regex_mode(mode)
        if 'g' not in flags:
            flags += 'g'
        offset = 0
        parts: list[str] = []
        for match in engine.find(value.value, pattern, flags):
            parts.append(value.value[offset:match.offset])
            offset = match.offset + match.length
        parts.append(value.value[offset:])
        if collect:
            yield JqResult(parts)
        else:
            for part in parts:
                yield JqResult(part)


def _substitute(
        context: JqEvalContext,
        value: JqResult,
        arguments: ta.Sequence[FilterArgument],
        *,
        global_: bool,
) -> ta.Iterator[JqResult]:
    if not isinstance(value.value, str):
        raise JqTypeError('regex substitution requires a string input')
    engine = _regex_engine(context)
    pattern_argument = arguments[0]
    replacement_argument = arguments[1]
    mode_argument = arguments[2] if len(arguments) > 2 else None

    for pattern_result in pattern_argument.evaluate(context, value):
        if not isinstance(pattern_result.value, str):
            raise JqTypeError('regex pattern must be a string')
        modes = (
            mode_argument.evaluate(context, value)
            if mode_argument is not None else
            iter((JqResult(''),))
        )
        for mode_result in modes:
            mode = _regex_mode(mode_result.value)
            if global_ and 'g' not in mode:
                mode += 'g'
            matches = list(engine.find(value.value, pattern_result.value, mode))
            if not matches:
                yield value
                continue

            states: list[tuple[str, int]] = [('', 0)]
            for match in matches:
                capture_value = JqResult(regex_capture_object(match))
                replacements = list(replacement_argument.evaluate(context, capture_value))
                next_states: list[tuple[str, int]] = []
                for prefix, previous in states:
                    gap = value.value[previous:match.offset]
                    for replacement in replacements:
                        if not isinstance(replacement.value, str):
                            raise JqTypeError('regex replacement must produce strings')
                        next_states.append((
                            prefix + gap + replacement.value,
                            match.offset + match.length,
                        ))
                states = next_states
            for prefix, previous in states:
                yield JqResult(prefix + value.value[previous:])


def _repeat(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    while True:
        yield from arguments[0].evaluate(context, value)


def _iterative_control(
        context: JqEvalContext,
        value: JqResult,
        condition: FilterArgument,
        update: FilterArgument,
        *,
        until: bool,
) -> ta.Iterator[JqResult]:
    type Task = tuple[ta.Literal['node', 'emit'], JqResult]

    def node_tasks(node: JqResult) -> ta.Iterator[Task]:
        for condition_value in condition.evaluate(context, node):
            matched = context.value_ops.truthy(condition_value.value)
            if matched:
                yield 'emit', node
                if until:
                    continue
            if matched or until:
                for updated in update.evaluate(context, node):
                    yield 'node', updated

    stack: list[ta.Iterator[Task]] = [iter((('node', value),))]
    while stack:
        try:
            kind, current = next(stack[-1])
        except StopIteration:
            stack.pop()
            continue
        if kind == 'emit':
            yield current
        else:
            stack.append(node_tasks(current))


def _while(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    yield from _iterative_control(context, value, arguments[0], arguments[1], until=False)


def _until(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    yield from _iterative_control(context, value, arguments[0], arguments[1], until=True)


def _recurse(context: JqEvalContext, value: JqResult, arguments: ta.Sequence[FilterArgument]) -> ta.Iterator[JqResult]:
    if arguments:
        child_filter = arguments[0]
        condition_filter = arguments[1] if len(arguments) > 1 else None
    else:
        active: set[int] = set()

        def children(child_context: JqEvalContext, child: JqResult) -> ta.Iterator[JqResult]:
            child_type = child_context.value_ops.type_name(child.value)
            if child_type != 'array' and child_type != 'object':
                return
            child_id = id(child.value)
            if child_id in active:
                child_context.value_ops.validate(child.value)
            active.add(child_id)
            try:
                for component, item in child_context.value_ops.iterate(child.value):
                    path = (*child.path, component) if child.path is not None else None
                    yield JqResult(item, path)
            finally:
                active.remove(child_id)

        child_filter = None
        condition_filter = None

    def filtered_children(parent: JqResult) -> ta.Iterator[JqResult]:
        if child_filter is None:
            yield from children(context, parent)
            return
        for child in child_filter.evaluate(context, parent):
            if condition_filter is None:
                yield child
            else:
                for condition in condition_filter.evaluate(context, child):
                    if context.value_ops.truthy(condition.value):
                        yield child

    yield value
    stack: list[ta.Iterator[JqResult]] = [filtered_children(value)]
    while stack:
        try:
            child = next(stack[-1])
        except StopIteration:
            stack.pop()
            continue
        yield child
        stack.append(filtered_children(child))


def build_native_functions() -> ta.Mapping[tuple[str, int], JqFunction]:
    functions = [
        NativeFunction('type', 0, _type),
        NativeFunction('length', 0, _length),
        NativeFunction('keys', 0, functools.partial(_keys, sorted_=True)),
        NativeFunction('keys_unsorted', 0, functools.partial(_keys, sorted_=False)),
        NativeFunction('has', 1, _has),
        NativeFunction('tostring', 0, _tostring),
        NativeFunction('tojson', 0, _tojson),
        NativeFunction('fromjson', 0, _fromjson),
        NativeFunction('tonumber', 0, _tonumber),
        NativeFunction('not', 0, _not),
        NativeFunction('error', 0, _error),
        NativeFunction('error', 1, _error),
        NativeFunction('input', 0, _input),
        NativeFunction('range', 1, _range),
        NativeFunction('range', 2, _range),
        NativeFunction('range', 3, _range),
        NativeFunction('path', 1, _path),
        NativeFunction('getpath', 1, _getpath),
        NativeFunction('setpath', 2, _setpath),
        NativeFunction('delpaths', 1, _delpaths),
        NativeFunction('contains', 1, _contains),
        NativeFunction('inside', 1, _inside),
        NativeFunction('startswith', 1, functools.partial(_string_predicate, predicate=str.startswith)),
        NativeFunction('endswith', 1, functools.partial(_string_predicate, predicate=str.endswith)),
        NativeFunction('split', 1, _split),
        NativeFunction('reverse', 0, _reverse),
        NativeFunction('sort', 0, _sort),
        NativeFunction('_sort_by_impl', 1, _sort_by_impl),
        NativeFunction('_group_by_impl', 1, _group_by_impl),
        NativeFunction('_unique_by_impl', 1, _unique_by_impl),
        NativeFunction('_min_by_impl', 1, functools.partial(_extreme_by_impl, maximum=False)),
        NativeFunction('_max_by_impl', 1, functools.partial(_extreme_by_impl, maximum=True)),
        NativeFunction('min', 0, functools.partial(_extreme, maximum=False)),
        NativeFunction('max', 0, functools.partial(_extreme, maximum=True)),
        NativeFunction('indices', 1, _indices),
        NativeFunction('explode', 0, _explode),
        NativeFunction('implode', 0, _implode),
        NativeFunction('tostream', 0, _tostream),
        NativeFunction('_match_impl', 3, _match_impl),
        NativeFunction('splits', 1, functools.partial(_regex_splits, collect=False)),
        NativeFunction('splits', 2, functools.partial(_regex_splits, collect=False)),
        NativeFunction('split', 2, functools.partial(_regex_splits, collect=True)),
        NativeFunction('sub', 2, functools.partial(_substitute, global_=False)),
        NativeFunction('sub', 3, functools.partial(_substitute, global_=False)),
        NativeFunction('gsub', 2, functools.partial(_substitute, global_=True)),
        NativeFunction('gsub', 3, functools.partial(_substitute, global_=True)),
        NativeFunction('repeat', 1, _repeat),
        NativeFunction('while', 2, _while),
        NativeFunction('until', 2, _until),
        NativeFunction('recurse', 0, _recurse),
        NativeFunction('recurse', 1, _recurse),
        NativeFunction('recurse', 2, _recurse),
    ]
    return {(function.name, function.arity): function for function in functions}


_NOT_SET = object()
