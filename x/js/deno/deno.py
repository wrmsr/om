import abc
import asyncio
import dataclasses as dc
import json
import math
import os
import secrets
import shutil
import signal
import tempfile
import types
import typing as ta


##


type JsonValue = None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]


_PROTOCOL_VERSION = 1
_PROTOCOL_PREFIX = b'\x1escript-runner-result-v1:'

_DENO_CAPABILITY_NAMES: ta.Final[tuple[tuple[str, str], ...]] = (
    ('read', 'read'),
    ('write', 'write'),
    ('net', 'net'),
    ('env', 'env'),
    ('run', 'run'),
    ('sys', 'sys'),
    ('ffi', 'ffi'),
    ('imports', 'import'),
)

_RESERVED_ENVIRONMENT_KEYS: ta.Final[frozenset[str]] = frozenset({
    'DENO_DIR',
    'DENO_NO_PACKAGE_JSON',
    'DENO_NO_PROMPT',
    'DENO_NO_UPDATE_CHECK',
    'DENO_REPL_HISTORY',
    'HOME',
    'LD_LIBRARY_PATH',
    'LD_PRELOAD',
    'NODE_OPTIONS',
    'NO_COLOR',
    'TMPDIR',
    'V8_FLAGS',
    'XDG_CACHE_HOME',
    'XDG_CONFIG_HOME',
    'XDG_DATA_HOME',
    'XDG_RUNTIME_DIR',
})


##


@dc.dataclass(frozen=True)
class ScriptResult:
    value: JsonValue

    emitted: tuple[JsonValue, ...] = ()

    stdout: str = ''
    stderr: str = ''


class ScriptError(Exception):
    pass


class ScriptUnavailableError(ScriptError):
    pass


class ScriptRunError(ScriptError):
    def __init__(
            self,
            message: str,
            *,
            stdout: str = '',
            stderr: str = '',
    ) -> None:
        super().__init__(message)

        self.stdout = stdout
        self.stderr = stderr


class ScriptTimeoutError(ScriptRunError):
    def __init__(
            self,
            timeout_s: float,
            *,
            stdout: str = '',
            stderr: str = '',
    ) -> None:
        super().__init__(
            f'Script exceeded its {timeout_s:g} second timeout',
            stdout=stdout,
            stderr=stderr,
        )

        self.timeout_s = timeout_s


class ScriptOutputLimitError(ScriptRunError):
    def __init__(
            self,
            stream: str,
            limit: int,
            *,
            stdout: str = '',
            stderr: str = '',
    ) -> None:
        super().__init__(
            f'Script {stream} exceeded its {limit} byte limit',
            stdout=stdout,
            stderr=stderr,
        )

        self.stream = stream
        self.limit = limit


class ScriptProcessError(ScriptRunError):
    def __init__(
            self,
            returncode: int,
            *,
            stdout: str = '',
            stderr: str = '',
    ) -> None:
        super().__init__(
            f'Script process exited with status {returncode}',
            stdout=stdout,
            stderr=stderr,
        )

        self.returncode = returncode


class ScriptProtocolError(ScriptRunError):
    pass


class ScriptExecutionError(ScriptRunError):
    def __init__(
            self,
            name: str,
            message: str,
            stack: str | None,
            *,
            stdout: str = '',
            stderr: str = '',
    ) -> None:
        super().__init__(
            f'{name}: {message}',
            stdout=stdout,
            stderr=stderr,
        )

        self.name = name
        self.script_message = message
        self.stack = stack


##


class ScriptRunner(abc.ABC):
    @abc.abstractmethod
    async def run(
            self,
            source: str,
            input: JsonValue = None,
    ) -> ScriptResult:
        raise NotImplementedError


##


@dc.dataclass(frozen=True)
class DenoCapability:
    """
    A single Deno permission class.

    ``allow=False`` denies the whole permission class. ``allow=True`` allows
    the whole class, while a tuple allows only the named resources. ``deny``
    can carve named resources out of an allowed class.
    """

    allow: bool | tuple[str, ...] = False
    deny: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.allow, bool) and not isinstance(self.allow, tuple):
            raise TypeError(self.allow)

        if isinstance(self.allow, tuple):
            _check_permission_values(self.allow)

        if not isinstance(self.deny, tuple):
            raise TypeError(self.deny)
        _check_permission_values(self.deny)

        if (self.allow is False or self.allow == ()) and self.deny:
            raise ValueError('deny scopes require an allowed permission scope')


@dc.dataclass(frozen=True)
class DenoPermissions:
    """
    Deno's eight permission classes.

    ``run`` and ``ffi`` are escape hatches: subprocesses and native libraries
    do not inherit Deno's sandbox.
    """

    read: DenoCapability = dc.field(default_factory=DenoCapability)
    write: DenoCapability = dc.field(default_factory=DenoCapability)
    net: DenoCapability = dc.field(default_factory=DenoCapability)
    env: DenoCapability = dc.field(default_factory=DenoCapability)
    run: DenoCapability = dc.field(default_factory=DenoCapability)
    sys: DenoCapability = dc.field(default_factory=DenoCapability)
    ffi: DenoCapability = dc.field(default_factory=DenoCapability)
    imports: DenoCapability = dc.field(default_factory=DenoCapability)

    def __post_init__(self) -> None:
        for field_name, _ in _DENO_CAPABILITY_NAMES:
            value = getattr(self, field_name)
            if not isinstance(value, DenoCapability):
                raise TypeError(value)


@dc.dataclass(frozen=True)
class DenoScriptRunnerConfig:
    """
    Configuration for one fresh Deno process per script execution.

    ``max_v8_old_space_mb`` constrains V8's old-space heap. It is not a hard
    operating-system limit on the process's total memory.
    """
    executable: str = 'deno'

    permissions: DenoPermissions = dc.field(default_factory=DenoPermissions)

    timeout_s: float = 5.

    max_source_bytes: int = 1 << 20
    max_input_bytes: int = 1 << 20
    max_request_bytes: int = 4 << 20
    max_result_bytes: int = 1 << 20
    max_stdout_bytes: int = 2 << 20
    max_stderr_bytes: int = 1 << 20
    max_emissions: int = 1_000

    max_v8_old_space_mb: int | None = 128
    seed: int | None = None

    no_prompt: bool = True
    no_config: bool = True
    no_lock: bool = True
    no_npm: bool = True
    no_remote: bool = True
    cached_only: bool = True
    no_code_cache: bool = True
    no_check: bool = True
    node_modules_dir: ta.Literal['none', 'auto', 'manual'] | None = 'none'

    working_directory: str | None = None
    deno_directory: str | None = None

    inherit_environment: bool = False
    environment: ta.Mapping[str, str] = dc.field(default_factory=dict)

    no_package_json: bool = True
    no_update_check: bool = True
    no_color: bool = True

    def __post_init__(self) -> None:
        if (
                not isinstance(self.executable, str) or
                not self.executable or
                '\x00' in self.executable
        ):
            raise ValueError(self.executable)
        if not isinstance(self.permissions, DenoPermissions):
            raise TypeError(self.permissions)

        for name in (
                'no_prompt',
                'no_config',
                'no_lock',
                'no_npm',
                'no_remote',
                'cached_only',
                'no_code_cache',
                'no_check',
                'inherit_environment',
                'no_package_json',
                'no_update_check',
                'no_color',
        ):
            value = getattr(self, name)
            if not isinstance(value, bool):
                raise TypeError(value)

        for path in (self.working_directory, self.deno_directory):
            if path is not None and (
                    not isinstance(path, str) or
                    not path or
                    '\x00' in path
            ):
                raise ValueError(path)

        _check_positive_number('timeout_s', self.timeout_s)

        for name in (
                'max_source_bytes',
                'max_input_bytes',
                'max_request_bytes',
                'max_result_bytes',
                'max_stdout_bytes',
                'max_stderr_bytes',
                'max_emissions',
        ):
            _check_positive_int(name, getattr(self, name))

        if self.max_v8_old_space_mb is not None:
            _check_positive_int('max_v8_old_space_mb', self.max_v8_old_space_mb)

        if self.seed is not None:
            if not isinstance(self.seed, int) or isinstance(self.seed, bool):
                raise TypeError(self.seed)
            if not 0 <= self.seed <= (2 ** 32 - 1):
                raise ValueError(self.seed)

        if self.node_modules_dir not in (None, 'none', 'auto', 'manual'):
            raise ValueError(self.node_modules_dir)

        environment = dict(self.environment)
        for key, value in environment.items():
            if not isinstance(key, str) or not key or '=' in key or '\x00' in key:
                raise ValueError(key)
            if not isinstance(value, str) or '\x00' in value:
                raise ValueError(value)
            if _is_reserved_environment_key(key):
                raise ValueError(f'Reserved environment key: {key}')

        object.__setattr__(self, 'environment', types.MappingProxyType(environment))


##


class DenoScriptRunner(ScriptRunner):
    """
    Run a JavaScript function body in a fresh, restricted Deno process.

    The body receives ``input`` and a synchronous ``emit(value)`` helper. It
    may use top-level ``await``; module imports must use dynamic ``import()``.
    """

    def __init__(
            self,
            config: DenoScriptRunnerConfig | None = None,
    ) -> None:
        super().__init__()

        if config is None:
            config = DenoScriptRunnerConfig()
        self._config = config

    @property
    def config(self) -> DenoScriptRunnerConfig:
        return self._config

    async def run(
            self,
            source: str,
            input: JsonValue = None,
    ) -> ScriptResult:
        if not isinstance(source, str):
            raise TypeError(source)

        source_bytes = source.encode('utf-8')
        if len(source_bytes) > self._config.max_source_bytes:
            raise ValueError(
                f'Script source exceeds its {self._config.max_source_bytes} byte limit',
            )

        input_bytes = _json_dump_bytes(input)
        if len(input_bytes) > self._config.max_input_bytes:
            raise ValueError(
                f'Script input exceeds its {self._config.max_input_bytes} byte limit',
            )

        executable = shutil.which(self._config.executable)
        if executable is None:
            raise ScriptUnavailableError(
                f'Deno executable not found: {self._config.executable!r}',
            )
        executable = os.path.abspath(executable)

        runner_path = os.path.join(os.path.dirname(__file__), 'runner.mjs')
        runner_path = os.path.abspath(runner_path)
        if not os.path.isfile(runner_path):
            raise ScriptUnavailableError(f'Deno runner not found: {runner_path}')

        token = secrets.token_hex(16)
        request = {
            'version': _PROTOCOL_VERSION,
            'token': token,
            'source': source,
            'input': input,
            'maxEmissions': self._config.max_emissions,
            'maxResultBytes': self._config.max_result_bytes,
        }
        request_bytes = _json_dump_bytes(request)
        if len(request_bytes) > self._config.max_request_bytes:
            raise ValueError(
                f'Script request exceeds its {self._config.max_request_bytes} byte limit',
            )

        with tempfile.TemporaryDirectory(prefix='deno-script-runner-') as temp_directory:
            environment = self._build_environment(temp_directory)
            working_directory = self._build_working_directory(temp_directory)
            argv = self._build_argv(executable, runner_path)

            try:
                process = await asyncio.create_subprocess_exec(
                    *argv,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=working_directory,
                    env=environment,
                    start_new_session=True,
                )
            except OSError as exc:
                raise ScriptUnavailableError(
                    f'Failed to execute Deno: {exc}',
                ) from exc

            stdout_bytes, stderr_bytes = await _communicate_limited(
                process,
                request_bytes,
                timeout_s=self._config.timeout_s,
                max_stdout_bytes=self._config.max_stdout_bytes,
                max_stderr_bytes=self._config.max_stderr_bytes,
            )

        stdout = stdout_bytes.decode('utf-8', errors='replace')
        stderr = stderr_bytes.decode('utf-8', errors='replace')

        if process.returncode != 0:
            raise ScriptProcessError(
                ta.cast(int, process.returncode),
                stdout=stdout,
                stderr=stderr,
            )

        payload, script_stdout = _extract_protocol_payload(
            stdout_bytes,
            token,
            stderr=stderr,
        )
        script_stdout_string = script_stdout.decode('utf-8', errors='replace')

        if payload.get('ok') is True:
            if 'value' not in payload:
                raise ScriptProtocolError(
                    'Deno runner omitted its result value',
                    stdout=script_stdout_string,
                    stderr=stderr,
                )

            emitted = payload.get('emitted', [])
            if not isinstance(emitted, list):
                raise ScriptProtocolError(
                    'Deno runner returned an invalid emitted value',
                    stdout=script_stdout_string,
                    stderr=stderr,
                )

            return ScriptResult(
                value=ta.cast(JsonValue, payload['value']),
                emitted=tuple(ta.cast(list[JsonValue], emitted)),
                stdout=script_stdout_string,
                stderr=stderr,
            )

        if payload.get('ok') is False:
            error = payload.get('error')
            if not isinstance(error, dict):
                raise ScriptProtocolError(
                    'Deno runner returned an invalid error value',
                    stdout=script_stdout_string,
                    stderr=stderr,
                )

            name = error.get('name')
            message = error.get('message')
            stack = error.get('stack')
            if not isinstance(name, str) or not isinstance(message, str):
                raise ScriptProtocolError(
                    'Deno runner returned an incomplete error value',
                    stdout=script_stdout_string,
                    stderr=stderr,
                )
            if stack is not None and not isinstance(stack, str):
                raise ScriptProtocolError(
                    'Deno runner returned an invalid error stack',
                    stdout=script_stdout_string,
                    stderr=stderr,
                )

            raise ScriptExecutionError(
                name,
                message,
                stack,
                stdout=script_stdout_string,
                stderr=stderr,
            )

        raise ScriptProtocolError(
            'Deno runner returned an invalid result envelope',
            stdout=script_stdout_string,
            stderr=stderr,
        )

    def _build_argv(
            self,
            executable: str,
            runner_path: str,
    ) -> tuple[str, ...]:
        argv = [
            executable,
            'run',
        ]

        if self._config.no_prompt:
            argv.append('--no-prompt')
        if self._config.no_config:
            argv.append('--no-config')
        if self._config.no_lock:
            argv.append('--no-lock')
        if self._config.no_npm:
            argv.append('--no-npm')
        if self._config.no_remote:
            argv.append('--no-remote')
        if self._config.cached_only:
            argv.append('--cached-only')
        if self._config.no_code_cache:
            argv.append('--no-code-cache')
        if self._config.no_check:
            argv.append('--no-check')
        if self._config.node_modules_dir is not None:
            argv.append(f'--node-modules-dir={self._config.node_modules_dir}')

        if self._config.max_v8_old_space_mb is not None:
            argv.append(
                '--v8-flags='
                f'--max-old-space-size={self._config.max_v8_old_space_mb}',
            )
        if self._config.seed is not None:
            argv.append(f'--seed={self._config.seed}')

        for field_name, cli_name in _DENO_CAPABILITY_NAMES:
            capability = getattr(self._config.permissions, field_name)
            argv.extend(_build_capability_argv(cli_name, capability))

        argv.append(runner_path)
        return tuple(argv)

    def _build_environment(self, temp_directory: str) -> dict[str, str]:
        if self._config.inherit_environment:
            environment = {
                key: value
                for key, value in os.environ.items()
                if not _is_reserved_environment_key(key)
            }
        else:
            environment = {}

        environment.update(self._config.environment)

        home_directory = os.path.join(temp_directory, 'home')
        temp_path = os.path.join(temp_directory, 'tmp')
        xdg_cache_directory = os.path.join(temp_directory, 'xdg-cache')
        xdg_config_directory = os.path.join(temp_directory, 'xdg-config')
        xdg_data_directory = os.path.join(temp_directory, 'xdg-data')
        xdg_runtime_directory = os.path.join(temp_directory, 'xdg-runtime')

        if self._config.deno_directory is None:
            deno_directory = os.path.join(temp_directory, 'deno')
        else:
            deno_directory = os.path.abspath(self._config.deno_directory)

        for directory in (
                home_directory,
                temp_path,
                xdg_cache_directory,
                xdg_config_directory,
                xdg_data_directory,
                xdg_runtime_directory,
                deno_directory,
        ):
            os.makedirs(directory, exist_ok=True)

        environment.update({
            'DENO_DIR': deno_directory,
            'DENO_REPL_HISTORY': '',
            'HOME': home_directory,
            'TMPDIR': temp_path,
            'XDG_CACHE_HOME': xdg_cache_directory,
            'XDG_CONFIG_HOME': xdg_config_directory,
            'XDG_DATA_HOME': xdg_data_directory,
            'XDG_RUNTIME_DIR': xdg_runtime_directory,
        })

        if self._config.no_package_json:
            environment['DENO_NO_PACKAGE_JSON'] = '1'
        if self._config.no_prompt:
            environment['DENO_NO_PROMPT'] = '1'
        if self._config.no_update_check:
            environment['DENO_NO_UPDATE_CHECK'] = '1'
        if self._config.no_color:
            environment['NO_COLOR'] = '1'

        return environment

    def _build_working_directory(self, temp_directory: str) -> str:
        if self._config.working_directory is None:
            working_directory = os.path.join(temp_directory, 'work')
            os.makedirs(working_directory)
            return working_directory

        working_directory = os.path.abspath(self._config.working_directory)
        if not os.path.isdir(working_directory):
            raise ValueError(f'Working directory does not exist: {working_directory}')
        return working_directory


##


def _check_positive_number(name: str, value: float) -> None:
    if (
            isinstance(value, bool) or
            not isinstance(value, (int, float)) or
            not math.isfinite(value) or
            value <= 0
    ):
        raise ValueError(f'{name} must be positive and finite: {value!r}')


def _check_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f'{name} must be a positive integer: {value!r}')


def _check_permission_values(values: tuple[str, ...]) -> None:
    for value in values:
        if not isinstance(value, str) or not value or '\x00' in value:
            raise ValueError(value)


def _escape_permission_value(value: str) -> str:
    return value.replace(',', ',,')


def _build_capability_argv(
        name: str,
        capability: DenoCapability,
) -> tuple[str, ...]:
    argv = []

    if capability.allow is True:
        argv.append(f'--allow-{name}')
    elif capability.allow:
        argv.append(
            f'--allow-{name}=' + ','.join(
                _escape_permission_value(value)
                for value in capability.allow
            ),
        )
    else:
        argv.append(f'--deny-{name}')

    if capability.deny:
        argv.append(
            f'--deny-{name}=' + ','.join(
                _escape_permission_value(value)
                for value in capability.deny
            ),
        )

    return tuple(argv)


def _is_reserved_environment_key(key: str) -> bool:
    return (
        key in _RESERVED_ENVIRONMENT_KEYS or
        key.startswith('DENO_') or
        key.startswith('DYLD_') or
        key.startswith('LD_')
    )


def _json_dump_bytes(value: ta.Any) -> bytes:
    try:
        string = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(',', ':'),
        )
    except (TypeError, ValueError) as exc:
        raise TypeError('Value must be JSON-serializable') from exc

    return string.encode('utf-8')


def _extract_protocol_payload(
        stdout: bytes,
        token: str,
        *,
        stderr: str = '',
) -> tuple[dict[str, ta.Any], bytes]:
    marker = _PROTOCOL_PREFIX + token.encode('ascii') + b':'
    marker_offset = stdout.rfind(marker)
    if marker_offset < 0:
        raise ScriptProtocolError(
            'Deno runner did not return a result envelope',
            stdout=stdout.decode('utf-8', errors='replace'),
            stderr=stderr,
        )

    payload_offset = marker_offset + len(marker)
    line_end = stdout.find(b'\n', payload_offset)
    if line_end < 0:
        line_end = len(stdout)
        suffix_offset = line_end
    else:
        suffix_offset = line_end + 1

    payload_bytes = stdout[payload_offset:line_end]
    script_stdout = stdout[:marker_offset] + stdout[suffix_offset:]

    try:
        payload = json.loads(payload_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ScriptProtocolError(
            'Deno runner returned malformed result JSON',
            stdout=script_stdout.decode('utf-8', errors='replace'),
            stderr=stderr,
        ) from exc

    if not isinstance(payload, dict):
        raise ScriptProtocolError(
            'Deno runner returned a non-object result envelope',
            stdout=script_stdout.decode('utf-8', errors='replace'),
            stderr=stderr,
        )

    return payload, script_stdout


##


class _StreamLimitError(Exception):
    def __init__(self, stream: str, limit: int) -> None:
        super().__init__(stream, limit)

        self.stream = stream
        self.limit = limit


async def _read_stream_limited(
        reader: asyncio.StreamReader,
        stream: str,
        limit: int,
        output: bytearray,
) -> None:
    while True:
        chunk = await reader.read(64 << 10)
        if not chunk:
            return

        remaining = limit - len(output)
        if len(chunk) > remaining:
            output.extend(chunk[:remaining])
            raise _StreamLimitError(stream, limit)

        output.extend(chunk)


async def _write_stdin(
        writer: asyncio.StreamWriter,
        data: bytes,
) -> None:
    try:
        writer.write(data)
        await writer.drain()
    except (BrokenPipeError, ConnectionResetError):
        pass
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except (BrokenPipeError, ConnectionResetError):
            pass


async def _communicate_limited(
        process: asyncio.subprocess.Process,
        input_bytes: bytes,
        *,
        timeout_s: float,
        max_stdout_bytes: int,
        max_stderr_bytes: int,
) -> tuple[bytes, bytes]:
    if process.stdin is None or process.stdout is None or process.stderr is None:
        raise RuntimeError('Subprocess pipes were not created')

    stdout = bytearray()
    stderr = bytearray()

    tasks = (
        asyncio.create_task(_write_stdin(process.stdin, input_bytes)),
        asyncio.create_task(
            _read_stream_limited(
                process.stdout,
                'stdout',
                max_stdout_bytes,
                stdout,
            ),
        ),
        asyncio.create_task(
            _read_stream_limited(
                process.stderr,
                'stderr',
                max_stderr_bytes,
                stderr,
            ),
        ),
        asyncio.create_task(process.wait()),
    )

    try:
        async with asyncio.timeout(timeout_s):
            await asyncio.gather(*tasks)

    except TimeoutError as exc:
        await _abort_process(process, tasks)
        raise ScriptTimeoutError(
            timeout_s,
            stdout=stdout.decode('utf-8', errors='replace'),
            stderr=stderr.decode('utf-8', errors='replace'),
        ) from exc

    except _StreamLimitError as exc:
        await _abort_process(process, tasks)
        raise ScriptOutputLimitError(
            exc.stream,
            exc.limit,
            stdout=stdout.decode('utf-8', errors='replace'),
            stderr=stderr.decode('utf-8', errors='replace'),
        ) from exc

    except BaseException:
        await _abort_process(process, tasks)
        raise

    return bytes(stdout), bytes(stderr)


def _kill_process_group(process: asyncio.subprocess.Process) -> None:
    if process.returncode is not None:
        return

    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError:
        if process.returncode is None:
            try:
                process.kill()
            except ProcessLookupError:
                pass


async def _abort_process(
        process: asyncio.subprocess.Process,
        tasks: tuple[asyncio.Task[ta.Any], ...],
) -> None:
    _kill_process_group(process)

    for task in tasks:
        if not task.done():
            task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)

    if process.returncode is None:
        try:
            await process.wait()
        except ProcessLookupError:
            pass
