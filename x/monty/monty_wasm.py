"""Direct Wasmtime host for the current pydantic/monty WIT component."""
import inspect
import math
import dataclasses as dc
import pathlib
import typing as ta

import wasmtime as wt
import wasmtime.component as wtc


##


type JsonScalar = type(None) | bool | int | float | str
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]

type HostFunction = ta.Callable[..., JsonValue]
type PrintHandler = ta.Callable[[ta.Literal['stdout', 'stderr'], str], None]


class _NotHandled:
    pass


class OsHandler(ta.Protocol):
    def __call__(
            self,
            function_name: str,
            args: ta.Sequence[JsonValue],
            kwargs: ta.Mapping[str, JsonValue],
    ) -> JsonValue | _NotHandled:
        ...


I64_MIN = -(1 << 63)
I64_MAX = (1 << 63) - 1
NOT_HANDLED = _NotHandled()


class MontyError(RuntimeError):
    pass


class MontyProtocolError(MontyError):
    pass


class MontyTypingError(MontyError):
    pass


class MontyWorkerError(MontyError):
    pass


class MontyExecutionError(MontyError):
    def __init__(self, exc_type: str, message: str, traceback: str) -> None:
        self.exc_type = exc_type
        self.message = message
        self.traceback = traceback

        super().__init__(traceback or f'{exc_type}: {message}')


@dc.dataclass(frozen=True)
class MontyLimits:
    max_duration_s: float | None = None
    max_memory_bytes: int | None = None
    gc_interval: int | None = None
    max_recursion_depth: int | None = None


class _Record:
    pass


def _record(**fields: ta.Any) -> _Record:
    value = _Record()
    for name, field_value in fields.items():
        # WIT names contain hyphens. Wasmtime lowers records with getattr(), so these are valid even though they cannot
        # be accessed with dot syntax.
        setattr(value, name.replace('_', '-'), field_value)
    return value


def _get(value: ta.Any, name: str) -> ta.Any:
    try:
        return getattr(value, name)
    except AttributeError as exc:
        raise MontyProtocolError(f'missing component field {name!r}') from exc


def _encode_limits(limits: MontyLimits | None) -> _Record | None:
    if limits is None:
        return None

    duration = limits.max_duration_s
    if duration is not None and (not math.isfinite(duration) or duration <= 0):
        raise ValueError('max_duration_s must be finite and positive')

    for name, value in (
        ('max_memory_bytes', limits.max_memory_bytes),
        ('gc_interval', limits.gc_interval),
        ('max_recursion_depth', limits.max_recursion_depth),
    ):
        if value is not None and value <= 0:
            raise ValueError(f'{name} must be positive')

    return _record(
        max_duration_micros=None if duration is None else max(1, round(duration * 1_000_000)),
        max_memory_bytes=limits.max_memory_bytes,
        gc_interval=limits.gc_interval,
        max_recursion_depth=limits.max_recursion_depth,
    )


def _encode_json(value: JsonValue) -> _Record:
    nodes: list[wtc.Variant] = []

    def push(item: JsonValue) -> int:
        if item is None:
            node = wtc.Variant('none')

        elif isinstance(item, bool):
            node = wtc.Variant('boolean', item)

        elif isinstance(item, int):
            node = wtc.Variant('integer', item) if I64_MIN <= item <= I64_MAX else wtc.Variant('bigint', str(item))

        elif isinstance(item, float):
            if not math.isfinite(item):
                raise TypeError('non-finite floats are not JSON values')
            node = wtc.Variant('float', item)

        elif isinstance(item, str):
            node = wtc.Variant('text', item)

        elif isinstance(item, list):
            node = wtc.Variant('list-value', [push(child) for child in item])

        elif isinstance(item, dict):
            pairs = []
            for key, child in item.items():
                if not isinstance(key, str):
                    raise TypeError('JSON object keys must be strings')
                pairs.append(_record(key=push(key), value=push(child)))
            node = wtc.Variant('dict', pairs)

        else:
            raise TypeError(f'cannot send {type(item).__name__} across the JSON boundary')

        index = len(nodes)
        nodes.append(node)
        return index

    return _record(root=(root := push(value)), nodes=nodes)


def _encode_function(name: str, fn: HostFunction) -> _Record:
    return _record(
        root=0,
        nodes=[wtc.Variant('function', _record(name=name, docstring=inspect.getdoc(fn)))],
    )


def _decode_json(value: ta.Any) -> JsonValue:
    root = _get(value, 'root')
    nodes = _get(value, 'nodes')
    visiting: set[int] = set()
    used: set[int] = set()

    def read(index: int) -> JsonValue:
        if not isinstance(index, int) or not 0 <= index < len(nodes):
            raise MontyProtocolError(f'value-node index {index!r} is out of bounds')
        if index in visiting:
            raise MontyProtocolError('value arena contains a cycle')
        if index in used:
            raise MontyProtocolError('value arena reuses a node')

        visiting.add(index)
        used.add(index)
        try:
            node = nodes[index]
            tag = node.tag
            payload = node.payload

            if tag == 'none':
                return None

            if tag in ('boolean', 'integer', 'text'):
                return payload

            if tag == 'bigint':
                return int(payload, 10)

            if tag == 'float':
                if not math.isfinite(payload):
                    raise MontyProtocolError('Monty returned a non-finite float')
                return payload

            if tag in ('list-value', 'tuple-value'):
                return [read(child) for child in payload]

            if tag == 'named-tuple':
                names = _get(payload, 'field-names')
                items = _get(payload, 'items')
                if len(names) != len(items):
                    raise MontyProtocolError('named tuple metadata is malformed')
                return {name: read(child) for name, child in zip(names, items)}

            if tag == 'dict':
                result: dict[str, JsonValue] = {}
                for pair in payload:
                    key = read(_get(pair, 'key'))
                    if not isinstance(key, str):
                        raise MontyProtocolError('Monty returned a dict with a non-string key')
                    result[key] = read(_get(pair, 'value'))
                return result

            if tag in ('path', 'repr'):
                return payload

            raise MontyProtocolError(f'Monty returned non-JSON value-node tag {tag!r}')

        finally:
            visiting.remove(index)

    result = read(root)
    if len(used) != len(nodes):
        raise MontyProtocolError('value arena contains unreachable nodes')
    return result


def _decode_args(values: list[ta.Any]) -> list[JsonValue]:
    return [_decode_json(value) for value in values]


def _decode_kwargs(values: list[ta.Any]) -> dict[str, JsonValue]:
    kwargs: dict[str, JsonValue] = {}
    for pair in values:
        key = _decode_json(_get(pair, 'key'))
        if not isinstance(key, str):
            raise MontyProtocolError('host-call keyword names must be strings')
        kwargs[key] = _decode_json(_get(pair, 'value'))
    return kwargs


_KNOWN_EXCEPTIONS = frozenset([
    'AssertionError',
    'AttributeError',
    'ImportError',
    'IndexError',
    'KeyError',
    'MemoryError',
    'NameError',
    'NotImplementedError',
    'OSError',
    'OverflowError',
    'RuntimeError',
    'TypeError',
    'ValueError',
    'ZeroDivisionError',
])


def _error_outcome(exc: Exception) -> wtc.Variant:
    exc_type = type(exc).__name__
    if exc_type not in _KNOWN_EXCEPTIONS:
        exc_type = 'RuntimeError'
    return wtc.Variant('error', _record(exc_type=exc_type, message=str(exc)))


def _return_outcome(value: ta.Any) -> wtc.Variant:
    if inspect.isawaitable(value):
        return _error_outcome(TypeError('async host functions are not supported'))
    try:
        return wtc.Variant('return-value', _encode_json(value))
    except Exception as exc:
        return _error_outcome(TypeError(str(exc)))


class MontyWasm:
    """Owns Wasmtime and a compiled Monty component; creates a fresh instance per execute()."""

    def __init__(self, component_path: str | pathlib.Path) -> None:
        super().__init__()

        config = wt.Config()
        config.wasm_component_model = True

        self._engine = wt.Engine(config)
        self._component = wtc.Component.from_file(self._engine, component_path)

        exports = self._component.type.exports(self._engine)

        worker_name = next(
            (name for name in exports if name == 'pydantic:monty/worker' or name.endswith(':monty/worker')),
            None,
        )
        if worker_name is None:
            raise MontyProtocolError(f'no Monty worker export; found {sorted(exports)!r}')

        self._worker_index = self._component.get_export_index(worker_name)
        if self._worker_index is None:
            raise MontyProtocolError(f'could not resolve Monty worker export {worker_name!r}')

        self._dispatch_index = self._component.get_export_index('dispatch', self._worker_index)
        if self._dispatch_index is None:
            raise MontyProtocolError('Monty worker has no dispatch export')

    def execute(
        self,
        code: str,
        inputs: ta.Mapping[str, JsonValue] | None = None,
        *,
        functions: ta.Mapping[str, HostFunction] | None = None,
        external_values: ta.Mapping[str, JsonValue] | None = None,
        os_handler: OsHandler | None = None,
        on_print: PrintHandler | None = None,
        limits: MontyLimits | None = None,
        max_wasm_memory_bytes: int | None = None,
        script_name: str = 'main.py',
        type_check: bool = False,
        type_check_stubs: str | None = None,
        skip_type_check: bool = False,
    ) -> JsonValue:
        functions = dict(functions or {})
        external_values = dict(external_values or {})
        overlap = functions.keys() & external_values.keys()
        if overlap:
            raise ValueError(f'names registered as both functions and values: {sorted(overlap)!r}')

        store = wt.Store(self._engine)
        # Empty: no inherited argv, environment, stdio, or preopened directories.
        store.set_wasi(wt.WasiConfig())
        if max_wasm_memory_bytes is not None:
            if max_wasm_memory_bytes <= 0:
                raise ValueError('max_wasm_memory_bytes must be positive')
            store.set_limits(memory_size=max_wasm_memory_bytes)

        # Linkers are cheap and mutable; keeping one per execution also avoids making concurrent execute() calls contend
        # on a shared linker object.
        linker = wtc.Linker(self._engine)
        linker.add_wasip2()

        instance = linker.instantiate(store, self._component)

        dispatch = instance.get_func(store, self._dispatch_index)
        if dispatch is None:
            raise MontyProtocolError('could not resolve Monty dispatch function')

        dead = False

        def turn(request: wtc.Variant) -> wtc.Variant:
            nonlocal dead
            if dead:
                raise MontyWorkerError('Monty component instance is no longer usable')

            try:
                result = dispatch(store, request)
                dispatch.post_return(store)
            except Exception as exc:
                dead = True
                raise MontyWorkerError('Monty component trapped or failed') from exc

            status = _get(result, 'status')
            if status == 'shutdown':
                dead = True
            elif status != 'continue':
                dead = True
                raise MontyProtocolError(f'unknown dispatch status {status!r}')

            terminal: wtc.Variant | None = None
            for event in _get(result, 'events'):
                if event.tag == 'print':
                    if on_print is not None:
                        printed = event.payload
                        on_print(
                            'stderr' if _get(printed, 'stderr') else 'stdout',
                            _get(printed, 'text'),
                        )

                elif terminal is None:
                    terminal = event

                else:
                    dead = True
                    raise MontyProtocolError('turn returned multiple terminating events')

            if terminal is None:
                dead = True
                raise MontyWorkerError('turn returned no terminating event')

            return terminal

        def resume(call_id: int, outcome: wtc.Variant) -> wtc.Variant:
            return turn(wtc.Variant('resume-call', _record(call_id=call_id, outcome=outcome)))

        configured = turn(wtc.Variant('configure', _record(
            script_name=script_name,
            limits=_encode_limits(limits),
            type_check=type_check,
            type_check_stubs=type_check_stubs,
            assert_message_annotations=None,
            type_check_format='full',
            type_check_color=False,
        )))
        if configured.tag != 'ok':
            raise MontyProtocolError(f'configure returned {configured.tag!r}')

        event = turn(wtc.Variant('feed', _record(
            code=code,
            inputs=[_record(name=name, value=_encode_json(value)) for name, value in (inputs or {}).items()],
            skip_type_check=skip_type_check,
        )))

        while True:
            if event.tag == 'complete':
                return _decode_json(event.payload)

            if event.tag == 'error':
                error = event.payload
                raise MontyExecutionError(
                    _get(error, 'exc-type'),
                    _get(error, 'message'),
                    _get(error, 'traceback'),
                )

            if event.tag == 'typing-error':
                raise MontyTypingError(str(event.payload))

            if event.tag == 'fatal-error':
                raise MontyWorkerError(str(event.payload))

            if event.tag == 'shutdown':
                raise MontyWorkerError('Monty worker shut down')

            if event.tag == 'name-lookup':
                name = event.payload
                if name in functions:
                    answer = wtc.Variant('value', _encode_function(name, functions[name]))
                elif name in external_values:
                    answer = wtc.Variant('value', _encode_json(external_values[name]))
                else:
                    answer = wtc.Variant('undefined')
                event = turn(wtc.Variant('resume-name-lookup', answer))
                continue

            if event.tag == 'function-call':
                call = event.payload
                name = _get(call, 'function-name')
                call_id = _get(call, 'call-id')
                fn = functions.get(name)

                if _get(call, 'method-call'):
                    outcome = _error_outcome(
                        RuntimeError(f'method calls on host objects are not supported: {name}'),
                    )

                elif fn is None:
                    outcome = wtc.Variant('not-found', name)

                else:
                    try:
                        outcome = _return_outcome(fn(
                            *_decode_args(_get(call, 'args')),
                            **_decode_kwargs(_get(call, 'kwargs')),
                        ))
                    except Exception as exc:
                        outcome = _error_outcome(exc)

                event = resume(call_id, outcome)
                continue

            if event.tag == 'os-call':
                call = event.payload
                call_id = _get(call, 'call-id')

                if os_handler is None:
                    outcome = wtc.Variant('not-handled')

                else:
                    try:
                        value = os_handler(
                            _get(call, 'function-name'),
                            _decode_args(_get(call, 'args')),
                            _decode_kwargs(_get(call, 'kwargs')),
                        )
                        outcome = wtc.Variant('not-handled') if value is NOT_HANDLED else _return_outcome(value)
                    except Exception as exc:
                        outcome = _error_outcome(exc)

                event = resume(call_id, outcome)
                continue

            if event.tag == 'resolve-futures':
                raise MontyProtocolError('this synchronous bridge does not implement external futures')

            raise MontyProtocolError(f'unexpected Monty event {event.tag!r}')
