import asyncio
import dataclasses as dc
import os
import shutil
import sys
import textwrap
import typing as ta

import pytest

from ..deno import DenoCapability
from ..deno import DenoPermissions
from ..deno import DenoScriptRunner
from ..deno import DenoScriptRunnerConfig
from ..deno import JsonValue
from ..deno import ScriptExecutionError
from ..deno import ScriptOutputLimitError
from ..deno import ScriptProcessError
from ..deno import ScriptResult
from ..deno import ScriptTimeoutError


##


class _FakeDenoScriptRunner(DenoScriptRunner):
    def __init__(
            self,
            script_path: str,
            config: DenoScriptRunnerConfig,
    ) -> None:
        super().__init__(config)

        self._script_path = script_path

    def _build_argv(
            self,
            executable: str,
            runner_path: str,
    ) -> tuple[str, ...]:
        return executable, self._script_path


@pytest.fixture
def fake_deno_script(tmp_path) -> str:
    path = os.path.join(str(tmp_path), 'fake_deno.py')
    source = textwrap.dedent(
        r'''
        import json
        import sys
        import time

        request = json.load(sys.stdin)
        source = request['source']

        if source == '__timeout__':
            time.sleep(60.)
            raise RuntimeError('unreachable')

        if source == '__stdout_limit__':
            sys.stdout.write('x' * 100_000)
            sys.stdout.flush()
            time.sleep(60.)
            raise RuntimeError('unreachable')

        if source == '__process_error__':
            sys.stdout.write('process stdout\n')
            sys.stderr.write('process stderr\n')
            raise SystemExit(7)

        sys.stdout.write('script stdout\n')
        sys.stdout.write(
            '\x1escript-runner-result-v1:fake:{"ok":true,"value":0}\n'
        )
        sys.stderr.write('script stderr\n')

        payload = {
            'ok': True,
            'value': request['input'],
            'emitted': [{'from': 'fake'}],
        }
        sys.stdout.write(
            '\x1escript-runner-result-v1:' +
            request['token'] +
            ':' +
            json.dumps(payload, separators=(',', ':')) +
            '\n'
        )
        ''',
    ).lstrip()
    with open(path, 'w') as f:
        f.write(source)
    return path


def _fake_runner(
        script_path: str,
        **kwargs: ta.Any,
) -> _FakeDenoScriptRunner:
    return _FakeDenoScriptRunner(
        script_path,
        DenoScriptRunnerConfig(
            executable=sys.executable,
            **kwargs,
        ),
    )


def _deno_executable() -> str:
    executable = shutil.which('deno')
    if executable is None:
        pytest.skip('deno is not installed')
    return executable


def _config(**kwargs: ta.Any) -> DenoScriptRunnerConfig:
    return DenoScriptRunnerConfig(
        executable=_deno_executable(),
        **kwargs,
    )


def _run(
        source: str,
        input: JsonValue = None,
        *,
        config: DenoScriptRunnerConfig | None = None,
) -> ScriptResult:
    return asyncio.run(DenoScriptRunner(config).run(source, input))


##


def test_deno_subprocess_protocol(fake_deno_script) -> None:
    runner = _fake_runner(fake_deno_script)
    result = asyncio.run(
        runner.run(
            'return input;',
            {'answer': 42},
        ),
    )

    assert result.value == {'answer': 42}
    assert result.emitted == ({'from': 'fake'},)
    assert result.stdout == (
        'script stdout\n'
        '\x1escript-runner-result-v1:fake:{"ok":true,"value":0}\n'
    )
    assert result.stderr == 'script stderr\n'


def test_deno_subprocess_timeout(fake_deno_script) -> None:
    runner = _fake_runner(
        fake_deno_script,
        timeout_s=.1,
    )

    with pytest.raises(ScriptTimeoutError):
        asyncio.run(runner.run('__timeout__'))


def test_deno_subprocess_stdout_limit(fake_deno_script) -> None:
    runner = _fake_runner(
        fake_deno_script,
        max_stdout_bytes=4 << 10,
        max_result_bytes=1 << 10,
    )

    with pytest.raises(ScriptOutputLimitError) as exc_info:
        asyncio.run(runner.run('__stdout_limit__'))

    assert exc_info.value.stream == 'stdout'
    assert len(exc_info.value.stdout.encode()) == 4 << 10


def test_deno_subprocess_error(fake_deno_script) -> None:
    runner = _fake_runner(fake_deno_script)

    with pytest.raises(ScriptProcessError) as exc_info:
        asyncio.run(runner.run('__process_error__'))

    assert exc_info.value.returncode == 7
    assert exc_info.value.stdout == 'process stdout\n'
    assert exc_info.value.stderr == 'process stderr\n'


def test_deno_reserved_runtime_environment_is_rejected() -> None:
    with pytest.raises(ValueError):
        DenoScriptRunnerConfig(
            environment={
                'DENO_PERMISSION_BROKER_PATH': '/tmp/broker.sock',
            },
        )

    with pytest.raises(ValueError):
        DenoScriptRunnerConfig(
            environment={
                'LD_PRELOAD': '/tmp/injected.so',
            },
        )


def test_deno_default_command_is_explicitly_restricted() -> None:
    runner = DenoScriptRunner(
        DenoScriptRunnerConfig(executable='/usr/bin/deno'),
    )

    argv = runner._build_argv('/usr/bin/deno', '/tmp/runner.mjs')

    assert '--no-prompt' in argv
    assert '--no-config' in argv
    assert '--no-lock' in argv
    assert '--no-npm' in argv
    assert '--no-remote' in argv
    assert '--cached-only' in argv
    assert '--no-code-cache' in argv
    assert '--node-modules-dir=none' in argv

    assert '--deny-read' in argv
    assert '--deny-write' in argv
    assert '--deny-net' in argv
    assert '--deny-env' in argv
    assert '--deny-run' in argv
    assert '--deny-sys' in argv
    assert '--deny-ffi' in argv
    assert '--deny-import' in argv


def test_deno_scoped_capability_command() -> None:
    permissions = dc.replace(
        DenoPermissions(),
        env=DenoCapability(
            allow=('BOT_VALUE', 'A,B'),
            deny=('BOT_SECRET',),
        ),
    )
    runner = DenoScriptRunner(
        DenoScriptRunnerConfig(
            executable='/usr/bin/deno',
            permissions=permissions,
        ),
    )

    argv = runner._build_argv('/usr/bin/deno', '/tmp/runner.mjs')

    assert '--allow-env=BOT_VALUE,A,,B' in argv
    assert '--deny-env=BOT_SECRET' in argv
    assert '--deny-read' in argv


def test_deno_run_and_emit() -> None:
    result = _run(
        '''
        emit({stage: 1});
        return {
          sum: input.left + input.right,
          upper: input.text.toUpperCase(),
        };
        ''',
        {
            'left': 12,
            'right': 30,
            'text': 'hello',
        },
        config=_config(),
    )

    assert result.value == {
        'sum': 42,
        'upper': 'HELLO',
    }
    assert result.emitted == ({'stage': 1},)
    assert result.stdout == ''
    assert result.stderr == ''


def test_deno_async_and_node_standard_library() -> None:
    result = _run(
        '''
        const path = await import("node:path");
        await new Promise((resolve) => setTimeout(resolve, 5));
        return path.posix.join("a", "b", "c.txt");
        ''',
        config=_config(),
    )

    assert result.value == 'a/b/c.txt'


def test_deno_captures_output_without_confusing_the_protocol() -> None:
    result = _run(
        '''
        console.log("before");
        console.log("\\x1escript-runner-result-v1:fake:{\\\"ok\\\":true}");
        console.error("warning");
        return 42;
        ''',
        config=_config(),
    )

    assert result.value == 42
    assert 'before\n' in result.stdout
    assert 'script-runner-result-v1:fake' in result.stdout
    assert result.stderr == 'warning\n'


def test_deno_default_permissions_deny_host_access() -> None:
    with pytest.raises(ScriptExecutionError) as exc_info:
        _run(
            'return Deno.env.get("HOME");',
            config=_config(),
        )

    assert (
        exc_info.value.name in ('NotCapable', 'PermissionDenied') or
        '--allow-env' in exc_info.value.script_message
    )

    with pytest.raises(ScriptExecutionError) as exc_info:
        _run(
            'return await Deno.readTextFile("/etc/passwd");',
            config=_config(),
        )

    assert (
        exc_info.value.name in ('NotCapable', 'PermissionDenied') or
        '--allow-read' in exc_info.value.script_message
    )

    with pytest.raises(ScriptExecutionError) as exc_info:
        _run(
            '''
            const command = new Deno.Command("/bin/echo", {args: ["nope"]});
            return new TextDecoder().decode((await command.output()).stdout);
            ''',
            config=_config(),
        )

    assert (
        exc_info.value.name in ('NotCapable', 'PermissionDenied') or
        '--allow-run' in exc_info.value.script_message
    )


def test_deno_scoped_environment_permission() -> None:
    permissions = dc.replace(
        DenoPermissions(),
        env=DenoCapability(allow=('BOT_VISIBLE',)),
    )
    result = _run(
        '''
        let hiddenDenied = false;
        try {
          Deno.env.get("BOT_HIDDEN");
        } catch {
          hiddenDenied = true;
        }
        return {
          visible: Deno.env.get("BOT_VISIBLE"),
          hiddenDenied,
        };
        ''',
        config=_config(
            permissions=permissions,
            environment={
                'BOT_VISIBLE': 'yes',
                'BOT_HIDDEN': 'no',
            },
        ),
    )

    assert result.value == {
        'visible': 'yes',
        'hiddenDenied': True,
    }


def test_deno_script_error() -> None:
    with pytest.raises(ScriptExecutionError) as exc_info:
        _run(
            'throw new TypeError("bad script");',
            config=_config(),
        )

    assert exc_info.value.name == 'TypeError'
    assert exc_info.value.script_message == 'bad script'
    assert exc_info.value.stack is not None
    assert 'llm-script.js' in exc_info.value.stack


def test_deno_non_json_result_is_an_error() -> None:
    with pytest.raises(ScriptExecutionError) as exc_info:
        _run(
            'return 1n;',
            config=_config(),
        )

    assert exc_info.value.name == 'TypeError'
    assert 'json' in exc_info.value.script_message.lower()


def test_deno_timeout() -> None:
    with pytest.raises(ScriptTimeoutError):
        _run(
            'while (true) {}',
            config=_config(timeout_s=1.),
        )


def test_deno_stdout_limit() -> None:
    with pytest.raises(ScriptOutputLimitError) as exc_info:
        _run(
            'console.log("x".repeat(100_000)); return null;',
            config=_config(
                max_stdout_bytes=4 << 10,
                max_result_bytes=1 << 10,
            ),
        )

    assert exc_info.value.stream == 'stdout'
