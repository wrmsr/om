"""
The bash repl against a real bash, through a real process manager - the local one, and the remote agent's (its payload
in an interpreter of its own, as `--container` runs it). The same tests for both: nothing in the repl knows which it
has.
"""
import asyncio
import contextlib
import os
import shutil
import signal
import typing as ta

import pytest

from omcore import lang
from omdev import repl

from ......agent.remote.tests.support import remote_agent
from ......core import processes
from ..ptys import ProcessScopePtySpawner


##


pytestmark = [
    pytest.mark.skipif(shutil.which('bash') is None, reason='requires bash'),
    pytest.mark.asyncs('asyncio'),
]

both_managers = pytest.mark.parametrize('manager', ['local', 'remote'])


@contextlib.asynccontextmanager
async def root_process_scope(manager: str) -> ta.AsyncIterator[processes.ProcessScope]:
    if manager == 'local':
        async with processes.AsyncioProcessManager() as local:
            yield local.root
    else:
        async with remote_agent() as client:
            yield client.processes.root


@contextlib.asynccontextmanager
async def bash(manager: str, cwd, **config) -> ta.AsyncIterator[tuple[repl.BashInterpreter, processes.ProcessScope]]:
    async with root_process_scope(manager) as root:
        scope = root.child('repl')
        interpreter = repl.BashInterpreter(
            ProcessScopePtySpawner(scope, cwd=os.path.realpath(cwd)),
            # Not the startup files of whoever runs the tests.
            config=repl.BashInterpreter.Config(no_rc=True, **config),
        )
        try:
            yield interpreter, scope
        finally:
            await interpreter.aclose()
            assert not scope.processes


async def run(interpreter, source):
    sink = repl.ListOutputSink()
    result = await interpreter.execute(source, sink)
    return result, list(sink.outputs)


async def run_text(interpreter, source):
    return ''.join(repl.output_text(o) for o in (await run(interpreter, source))[1])


@contextlib.asynccontextmanager
async def fifo(path) -> ta.AsyncIterator[ta.Callable[[], ta.Awaitable[bytes]]]:
    """A fifo, open for reading: what a process which is not ours to wait on can say it got somewhere through."""

    os.mkfifo(path)
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    try:
        async def read() -> bytes:
            loop = asyncio.get_running_loop()
            readable = asyncio.Event()
            loop.add_reader(fd, readable.set)
            try:
                await asyncio.wait_for(readable.wait(), 10.)
            finally:
                loop.remove_reader(fd)
            return os.read(fd, 1024)

        yield read

    finally:
        os.close(fd)


async def start_and_cancel(interpreter, source):
    """
    Starts a command which says `started` and then does not finish, and cancels it once it has said so. It is the job
    itself which has to say it, not the shell ahead of starting one: an interrupt which finds the shell between the two
    is lost on it (as it is at any terminal), and found out only when the next command is.
    """

    started = asyncio.Event()
    task = asyncio.ensure_future(interpreter.execute(source, repl.CallbackOutputSink(lambda o: started.set())))
    await asyncio.wait_for(started.wait(), 10.)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


##


@both_managers
async def test_a_shell_which_keeps_its_state(manager, tmp_path):
    cwd = os.path.realpath(tmp_path)
    os.mkdir(os.path.join(cwd, 'sub'))

    async with bash(manager, cwd) as (interpreter, scope):
        assert not scope.processes

        result, outputs = await run(interpreter, 'pwd')
        assert result.ok
        assert outputs == [repl.TerminalOutput(f'{cwd}\n')]
        assert interpreter.cwd == cwd
        assert len(scope.processes) == 1

        assert (await run(interpreter, 'cd sub && export FOO=bar && greet() { echo "hi $1"; }'))[1] == []
        assert interpreter.cwd == os.path.join(cwd, 'sub')
        assert await run_text(interpreter, 'pwd; echo $FOO; greet there') == f'{cwd}/sub\nbar\nhi there\n'

        result, outputs = await run(interpreter, '(exit 3)')
        assert result.status is repl.ResultStatus.ERROR
        assert result.value == lang.just(3)
        assert outputs == [repl.NoteOutput('[exit 3]')]
        assert await run_text(interpreter, 'echo $?') == '3\n'
        assert await run_text(interpreter, 'echo $?') == '0\n'

        assert len(scope.processes) == 1


@both_managers
async def test_commands_see_a_terminal_and_nothing_to_read(manager, tmp_path):
    async with bash(manager, tmp_path) as (interpreter, _):
        assert await run_text(interpreter, '[ -t 1 ] && [ -t 2 ] && echo tty; echo $TERM') == 'tty\nxterm-256color\n'

        _, outputs = await run(interpreter, r"printf 'plain \033[1;31mred\033[0m\n'; printf 'working\rdone   \n'")
        assert outputs == [repl.TerminalOutput('plain \x1b[0;1;31mred\x1b[0m\ndone\n')]

        # Nothing can be typed to a command, so one which reads finds the end of its input rather than waiting.
        assert await run_text(interpreter, 'cat; echo "rc=$?"; [ -t 0 ] || echo "no tty in"') == 'rc=0\nno tty in\n'

        # A pipeline's writer dies quietly of its SIGPIPE, as on any terminal.
        assert await run_text(interpreter, 'yes | head -n 1') == 'y\n'

        assert await run_text(interpreter, 'echo $PAGER; shopt -qo history || echo unrecorded; echo "[$HISTFILE]"') == (
            'cat\nunrecorded\n[]\n'
        )


@both_managers
async def test_source_which_a_terminal_would_mangle(manager, tmp_path):
    async with bash(manager, tmp_path) as (interpreter, _):
        # Longer than a terminal's line, and full of what its line discipline acts on.
        assert await run_text(interpreter, 'x=' + 'a' * 20_000 + '; echo ${#x}') == '20000\n'
        assert await run_text(interpreter, "printf '%s' 'a\x03b\x15c\x7fd' | od -An -c") == (
            '   a 003   b 025   c 177   d\n'
        )
        assert await run_text(interpreter, "echo 'héllo → \u65e5\u672c'") == 'héllo → \u65e5\u672c\n'
        assert await run_text(interpreter, "cat <<'EOF'\nheredoc $HOME\n  second\nEOF") == 'heredoc $HOME\n  second\n'
        assert await run_text(interpreter, 'for i in 1 2; do\n  echo "n=$i"\ndone') == 'n=1\nn=2\n'

        # An unfinished quote is the shell's to report, not a continuation prompt to wait at.
        result, outputs = await run(interpreter, 'echo "unfinished')
        assert result.value == lang.just(2)
        assert 'unexpected EOF' in outputs[0].text
        assert await run_text(interpreter, 'echo fine') == 'fine\n'


@both_managers
async def test_the_terminal_follows_the_host_size(manager, tmp_path):
    size = [(30, 100)]
    async with root_process_scope(manager) as root:
        interpreter = repl.BashInterpreter(
            ProcessScopePtySpawner(root.child('repl'), cwd=os.path.realpath(tmp_path)),
            config=repl.BashInterpreter.Config(no_rc=True),
            size=lambda: size[0],
        )
        try:
            assert await run_text(interpreter, 'stty size </dev/tty') == '30 100\n'
            size[0] = (30, 64)
            assert await run_text(interpreter, 'stty size </dev/tty') == '30 64\n'
        finally:
            await interpreter.aclose()


@both_managers
async def test_a_cancelled_command_is_interrupted(manager, tmp_path):
    marker = os.path.join(os.path.realpath(tmp_path), 'finished')

    async with bash(manager, tmp_path) as (interpreter, scope):
        await run(interpreter, 'FOO=kept')
        await start_and_cancel(interpreter, f'sh -c "echo started; exec sleep 60"; touch {marker}')

        assert await run_text(interpreter, 'echo "$FOO"; jobs') == 'kept\n'
        assert not os.path.exists(marker)
        assert len(scope.processes) == 1


@both_managers
async def test_a_command_deaf_to_interrupts_is_killed_and_the_shell_kept(manager, tmp_path):
    async with bash(manager, tmp_path, interrupt_timeout_s=.5) as (interpreter, scope):
        await run(interpreter, 'FOO=kept')
        (shell,) = scope.processes.values()

        await start_and_cancel(interpreter, """sh -c "trap '' INT; echo started; exec sleep 60" """)

        assert await run_text(interpreter, 'echo "$FOO"; jobs') == 'kept\n'
        assert list(scope.processes.values()) == [shell]


@both_managers
async def test_a_program_taking_the_screen_over_is_stopped(manager, tmp_path):
    async with bash(manager, tmp_path) as (interpreter, _):
        result, outputs = await run(interpreter, r'''sh -c "printf '\033[?1049h\033[2Jdrawn'; exec sleep 60"''')
        assert not result.ok
        assert outputs == [repl.NoteOutput('[full-screen programs are not supported here: stopping it]')]

        assert await run_text(interpreter, 'echo fine; jobs') == 'fine\n'


@both_managers
async def test_exit_ends_the_shell_and_hangs_up_its_jobs(manager, tmp_path):
    cwd = os.path.realpath(tmp_path)
    hung_up = os.path.join(cwd, 'hung-up')

    async with bash(manager, cwd) as (interpreter, scope), fifo(hung_up) as read_hung_up:
        await run(interpreter, f"cd /; (trap 'echo hup > {hung_up}; exit' HUP; sleep 60 & wait) &")
        result, outputs = await run(interpreter, 'exit 3')
        assert result.status is repl.ResultStatus.EXIT
        assert outputs[-1] == repl.NoteOutput('[the shell exited]')
        assert not interpreter.is_started
        assert not scope.processes

        assert await read_hung_up() == b'hup\n'

        assert await run_text(interpreter, 'pwd; jobs') == f'{cwd}\n'
        assert len(scope.processes) == 1


@both_managers
async def test_exit_ends_the_shell_whatever_it_leaves_behind(manager, tmp_path):
    async with bash(manager, tmp_path) as (interpreter, scope):
        # A job the shell was told to forget outlives it, with the terminal still in hand: the shell is over all the
        # same, without waiting for an end of output which is not coming.
        # The shell announces the job (`[1] <pid>`) ahead of the echoed pid, the two as likely as not in one output.
        pid = int((await run_text(interpreter, 'sleep 5 & disown; echo $!')).splitlines()[-1])
        try:
            result, _ = await run(interpreter, 'exit')
            assert result.status is repl.ResultStatus.EXIT
            assert not scope.processes
        finally:
            os.kill(pid, signal.SIGKILL)


@both_managers
async def test_a_shell_killed_behind_its_back_is_replaced(manager, tmp_path):
    cwd = os.path.realpath(tmp_path)

    async with bash(manager, cwd) as (interpreter, scope):
        await run(interpreter, 'cd /')
        (shell,) = scope.processes.values()
        await shell.kill()
        await shell.wait(10.)

        _, outputs = await run(interpreter, 'pwd')
        assert outputs == [
            repl.NoteOutput('[the shell was gone: starting a new one]'),
            repl.TerminalOutput(f'{cwd}\n'),
        ]
        assert shell not in scope.processes.values()
        assert len(scope.processes) == 1


@both_managers
async def test_no_bash_to_start(manager, tmp_path):
    async with bash(manager, tmp_path, executable='no-such-bash') as (interpreter, scope):
        with pytest.raises(repl.BashStartError, match='no-such-bash'):
            await run(interpreter, 'echo hi')
        assert not interpreter.is_started
        assert not scope.processes


@both_managers
async def test_long_output_is_limited(manager, tmp_path):
    async with bash(manager, tmp_path, max_output_lines=5, max_tail_lines=2) as (interpreter, _):
        _, outputs = await run(interpreter, 'seq 1 50000')
        assert ''.join(repl.output_text(o) for o in outputs) == (
            '1\n2\n3\n4\n5\n'
            '[more output follows: only its last 2 lines will be shown, once the command has ended]\n'
            '[... 49993 lines not shown ...]\n'
            '49999\n50000\n'
        )
