import json
import subprocess
import sys

from ....subprocesses.wrap import subprocess_maybe_shell_wrap_exec


##


def run_cli(*arguments, input_value=''):
    return subprocess.run(
        subprocess_maybe_shell_wrap_exec(sys.executable, '-m', 'omcore.specs.jq', *arguments),
        input=input_value,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_json_and_arguments():
    result = run_cli('-c', '--arg', 'suffix', '!', '.items[] | . + $suffix', input_value='{"items":["a","b"]}')
    assert result.returncode == 0
    assert result.stdout.splitlines() == ['"a!"', '"b!"']
    assert not result.stderr


def test_cli_multiple_inputs_raw_and_slurp():
    result = run_cli('-c', '[inputs]', input_value='1 2 3')
    assert result.returncode == 0
    assert json.loads(result.stdout) == [2, 3]

    result = run_cli('-Rr', '.', input_value='a\nb\n')
    assert result.returncode == 0
    assert result.stdout == 'a\nb\n'

    result = run_cli('-Rrs', '.', input_value='a\nb\n')
    assert result.returncode == 0
    assert result.stdout == 'a\nb\n\n'

    result = run_cli('-sc', 'add', input_value='1 2 3')
    assert result.returncode == 0
    assert result.stdout == '6\n'


def test_cli_null_input_and_json_argument():
    result = run_cli('-nc', '--argjson', 'value', '{"a":1}', '$value.a')
    assert result.returncode == 0
    assert result.stdout == '1\n'


def test_cli_stream_does_not_materialize_document():
    result = run_cli('--stream', '-c', '.', input_value='["a",["b"]]')
    assert result.returncode == 0
    assert [json.loads(line) for line in result.stdout.splitlines()] == [
        [[0], 'a'],
        [[1, 0], 'b'],
        [[1, 0]],
        [[1]],
    ]
