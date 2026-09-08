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


class _Helpers:
    def __init__(
            self,
            *,
            raise_direct: bool = False,
    ) -> None:
        super().__init__()

        self._raise_direct = raise_direct

    def _raise_from(self, e: BaseException, fe: BaseException) -> ta.NoReturn:
        if self._raise_direct:
            raise  # noqa

        raise e from fe

    def _record(self, **fields: ta.Any) -> _Record:
        value = _Record()
        for name, field_value in fields.items():
            # WIT names contain hyphens. Wasmtime lowers records with getattr(), so these are valid even though they
            # cannot be accessed with dot syntax.
            setattr(value, name.replace('_', '-'), field_value)
        return value

    def _get(self, value: ta.Any, name: str) -> ta.Any:
        try:
            return getattr(value, name)
        except AttributeError as exc:
            self._raise_from(MontyProtocolError(f'missing component field {name!r}'), exc)

    def _encode_limits(self, limits: MontyLimits | None) -> _Record | None:
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

        return self._record(
            max_duration_micros=None if duration is None else max(1, round(duration * 1_000_000)),
            max_memory_bytes=limits.max_memory_bytes,
            gc_interval=limits.gc_interval,
            max_recursion_depth=limits.max_recursion_depth,
        )

    def _encode_json(self, value: JsonValue) -> _Record:
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
                    pairs.append(self._record(key=push(key), value=push(child)))
                node = wtc.Variant('dict', pairs)

            else:
                raise TypeError(f'cannot send {type(item).__name__} across the JSON boundary')

            index = len(nodes)
            nodes.append(node)
            return index

        return self._record(root=(root := push(value)), nodes=nodes)

    def _encode_function(self, name: str, fn: HostFunction) -> _Record:
        return self._record(
            root=0,
            nodes=[wtc.Variant('function', self._record(name=name, docstring=inspect.getdoc(fn)))],
        )

    def _decode_json(self, value: ta.Any) -> JsonValue:
        root = self._get(value, 'root')
        nodes = self._get(value, 'nodes')
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
                    names = self._get(payload, 'field-names')
                    items = self._get(payload, 'items')
                    if len(names) != len(items):
                        raise MontyProtocolError('named tuple metadata is malformed')
                    return {name: read(child) for name, child in zip(names, items)}

                if tag == 'dict':
                    result: dict[str, JsonValue] = {}
                    for pair in payload:
                        key = read(self._get(pair, 'key'))
                        if not isinstance(key, str):
                            raise MontyProtocolError('Monty returned a dict with a non-string key')
                        result[key] = read(self._get(pair, 'value'))
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

    def _decode_args(self, values: list[ta.Any]) -> list[JsonValue]:
        return [self._decode_json(value) for value in values]

    def _decode_kwargs(self, values: list[ta.Any]) -> dict[str, JsonValue]:
        kwargs: dict[str, JsonValue] = {}
        for pair in values:
            key = self._decode_json(self._get(pair, 'key'))
            if not isinstance(key, str):
                raise MontyProtocolError('host-call keyword names must be strings')
            kwargs[key] = self._decode_json(self._get(pair, 'value'))
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

    def _error_outcome(self, exc: Exception) -> wtc.Variant:
        exc_type = type(exc).__name__
        if exc_type not in self._KNOWN_EXCEPTIONS:
            exc_type = 'RuntimeError'
        return wtc.Variant('error', self._record(exc_type=exc_type, message=str(exc)))

    def _return_outcome(self, value: ta.Any) -> wtc.Variant:
        if inspect.isawaitable(value):
            return self._error_outcome(TypeError('async host functions are not supported'))
        try:
            return wtc.Variant('return-value', self._encode_json(value))
        except Exception as exc:
            return self._error_outcome(TypeError(str(exc)))


class MontyWasm(_Helpers):
    """Owns Wasmtime and a compiled Monty component; creates a fresh instance per execute()."""

    def __init__(
            self,
            component_path: str | pathlib.Path,
            *,
            raise_direct: bool = False,
    ) -> None:
        super().__init__(
            raise_direct=raise_direct,
        )

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
                self._raise_from(MontyWorkerError('Monty component trapped or failed'), exc)

            status = self._get(result, 'status')
            if status == 'shutdown':
                dead = True
            elif status != 'continue':
                dead = True
                raise MontyProtocolError(f'unknown dispatch status {status!r}')

            terminal: wtc.Variant | None = None
            for event in self._get(result, 'events'):
                if event.tag == 'print':
                    if on_print is not None:
                        printed = event.payload
                        on_print(
                            'stderr' if self._get(printed, 'stderr') else 'stdout',
                            self._get(printed, 'text'),
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
            return turn(wtc.Variant('resume-call', self._record(call_id=call_id, outcome=outcome)))

        configured = turn(wtc.Variant('configure', self._record(
            script_name=script_name,
            limits=self._encode_limits(limits),
            type_check=type_check,
            type_check_stubs=type_check_stubs,
            assert_message_annotations=None,
            type_check_format='full',
            type_check_color=False,
        )))
        if configured.tag != 'ok':
            raise MontyProtocolError(f'configure returned {configured.tag!r}')

        event = turn(wtc.Variant('feed', self._record(
            code=code,
            inputs=[self._record(name=name, value=self._encode_json(value)) for name, value in (inputs or {}).items()],
            skip_type_check=skip_type_check,
        )))

        while True:
            if event.tag == 'complete':
                return self._decode_json(event.payload)

            if event.tag == 'error':
                error = event.payload
                raise MontyExecutionError(
                    self._get(error, 'exc-type'),
                    self._get(error, 'message'),
                    self._get(error, 'traceback'),
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
                    answer = wtc.Variant('value', self._encode_function(name, functions[name]))
                elif name in external_values:
                    answer = wtc.Variant('value', self._encode_json(external_values[name]))
                else:
                    answer = wtc.Variant('undefined')
                event = turn(wtc.Variant('resume-name-lookup', answer))
                continue

            if event.tag == 'function-call':
                call = event.payload
                name = self._get(call, 'function-name')
                call_id = self._get(call, 'call-id')
                fn = functions.get(name)

                if self._get(call, 'method-call'):
                    outcome = self._error_outcome(
                        RuntimeError(f'method calls on host objects are not supported: {name}'),
                    )

                elif fn is None:
                    outcome = wtc.Variant('not-found', name)

                else:
                    try:
                        outcome = self._return_outcome(fn(
                            *self._decode_args(self._get(call, 'args')),
                            **self._decode_kwargs(self._get(call, 'kwargs')),
                        ))
                    except Exception as exc:
                        outcome = self._error_outcome(exc)

                event = resume(call_id, outcome)
                continue

            if event.tag == 'os-call':
                call = event.payload
                call_id = self._get(call, 'call-id')

                if os_handler is None:
                    outcome = wtc.Variant('not-handled')

                else:
                    try:
                        value = os_handler(
                            self._get(call, 'function-name'),
                            self._decode_args(self._get(call, 'args')),
                            self._decode_kwargs(self._get(call, 'kwargs')),
                        )
                        outcome = wtc.Variant('not-handled') if value is NOT_HANDLED else self._return_outcome(value)
                    except Exception as exc:
                        outcome = self._error_outcome(exc)

                event = resume(call_id, outcome)
                continue

            if event.tag == 'resolve-futures':
                raise MontyProtocolError('this synchronous bridge does not implement external futures')

            raise MontyProtocolError(f'unexpected Monty event {event.tag!r}')


##


def _main(argv=None) -> None:
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('component_path', metavar='component-path')
    parser.add_argument('--raise_direct', metavar='raise-direct', action='store_true')

    args = parser.parse_args(argv)

    #

    runtime = MontyWasm(
        args.component_path,
        raise_direct=bool(args.raise_direct),
    )

    result = runtime.execute(
        'x * 2',
        inputs={
            'x': 21,
        },
        limits=MontyLimits(
            max_duration_s=0.5,
            max_memory_bytes=8 * 1024 * 1024,
        ),
    )

    print(result)


if __name__ == '__main__':
    _main()
