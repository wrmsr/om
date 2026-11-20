import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import time
import typing as ta

from omcore import dataclasses as dc

from .landlock import LocalReadAccess
from .landlock import restrict_local_access


##


class CommandError(Exception):
    pass


@dc.dataclass(frozen=True)
class CommandResult:
    returncode: int
    seconds: float
    timed_out: bool = False
    stdout: bytes = b''


def write_json(path: str, value: ta.Any) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n')


def read_text(path: str) -> str:
    with open(path, encoding='utf-8') as f:
        return f.read()


def stop_process(process: subprocess.Popen) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass
    # A child can outlive its process-group leader.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=5)


def run_command(
        command: ta.Sequence[str],
        *,
        log_path: str,
        timeout: float,
        input_data: bytes | None = None,
        capture: bool = False,
        cwd: str | None = None,
        env: ta.Mapping[str, str] | None = None,
        local_write_paths: ta.Sequence[str] | None = None,
        local_read_access: LocalReadAccess | None = None,
        cleanup_group: bool = False,
) -> CommandResult:
    started = time.monotonic()
    timed_out = False
    with open(log_path, 'ab') as log:
        log.write(f'\n$ {shlex.join(command)}\n'.encode())
        log.flush()
        with subprocess.Popen(
                list(command),
                stdin=subprocess.PIPE if input_data is not None else subprocess.DEVNULL,
                stdout=subprocess.PIPE if capture else log,
                stderr=log,
                start_new_session=True,
                cwd=cwd,
                env=env,
                preexec_fn=(  # noqa: PLW1509
                    (lambda: restrict_local_access(local_write_paths, local_read_access))
                    if local_write_paths is not None else None
                ),
        ) as process:
            try:
                stdout, _ = process.communicate(input=input_data, timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                stop_process(process)
                stdout, _ = process.communicate(timeout=5)
            except BaseException:
                stop_process(process)
                raise
        if cleanup_group:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if capture and stdout:
            log.write(stdout)
    return CommandResult(process.returncode, time.monotonic() - started, timed_out, stdout or b'')


def checked(result: CommandResult, log_path: str) -> CommandResult:
    if result.timed_out:
        raise CommandError(f'Command timed out; see {log_path}')
    if result.returncode:
        raise CommandError(f'Command exited {result.returncode}; see {log_path}')
    return result


def replace_tokens(value: str, tokens: ta.Mapping[str, str]) -> str:
    return re.sub(r'\{([a-z_]+)\}', lambda match: tokens.get(match[1], match[0]), value)


def remove_path(path: str) -> None:
    if os.path.islink(path) or os.path.isfile(path):
        os.unlink(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
