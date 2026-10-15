import pytest

from omcore import lang

from ...interpreters import ResultStatus
from ...outputs import ListOutputSink
from ...outputs import NoteOutput
from ...outputs import TerminalOutput
from ..interpreter import BashInterpreter
from ..interpreter import BashStartError
from ..interpreter import BashVersionError
from ..protocol import BashProtocol
from .support import QUIET
from .support import Cancelled
from .support import Reply
from .support import ScriptedSpawner


##


def make(handler=lambda source: Reply(), *, config=None, **kwargs):
    spawner = ScriptedSpawner(handler, **kwargs)
    return BashInterpreter(spawner, config=config, clock=spawner.clock), spawner


def execute(interpreter, source):
    sink = ListOutputSink()
    result = lang.sync_await(interpreter.execute(source, sink))
    return result, list(sink.outputs)


def test_nothing_is_started_until_used():
    interpreter, spawner = make()
    assert not interpreter.is_started
    assert interpreter.cwd is None

    result, outputs = execute(interpreter, '  \n')
    assert result.ok
    assert outputs == []
    assert spawner.shells == []


def test_execution():
    interpreter, spawner = make(lambda source: Reply(output=[b'one\r\ntwo\r\n'], cwd='/work'))

    result, outputs = execute(interpreter, 'echo one; echo two')
    assert result.status is ResultStatus.OK
    assert result.value == lang.just(0)
    assert outputs == [TerminalOutput('one\ntwo\n')]

    assert interpreter.is_started
    assert interpreter.cwd == '/work'
    assert spawner.shell.argv == ('bash', '--noediting', '-i')
    assert spawner.shell.size == (50, 120)
    assert spawner.shell.sources == ['echo one; echo two']
    assert spawner.shell.commands == [BashProtocol.VERSION]


def test_the_shell_is_kept():
    interpreter, spawner = make()
    execute(interpreter, 'cd /tmp')
    execute(interpreter, 'pwd')
    assert len(spawner.shells) == 1
    assert spawner.shell.sources == ['cd /tmp', 'pwd']


def test_source_crosses_as_it_is():
    source = 'echo \'quoted\' "$x" \\ \t\x15\x7f é \u65e5\u672c\nsecond line ' + 'x' * 5000
    interpreter, spawner = make()
    execute(interpreter, source)
    assert spawner.shell.sources == [source]


def test_a_failing_command():
    interpreter, _ = make(lambda source: Reply(output=[b'nope\r\n'], returncode=3))
    result, outputs = execute(interpreter, 'false')
    assert result.status is ResultStatus.ERROR
    assert result.value == lang.just(3)
    assert outputs == [TerminalOutput('nope\n'), NoteOutput('[exit 3]')]


def test_output_arrives_in_pieces():
    # A line split mid-escape and mid-character, and a prompt mark split from what precedes it.
    red = '\x1b[31mré\x1b[0m\r\n'.encode()
    interpreter, _ = make(lambda source: Reply(output=[red[:3], red[3:8], red[8:], b'plain']))
    _, outputs = execute(interpreter, 'x')
    assert outputs == [TerminalOutput('\x1b[0;31mré\x1b[0m\n'), TerminalOutput('plain')]


def test_a_quiet_spell_shows_the_line_so_far():
    interpreter, _ = make(lambda source: Reply(output=[b'password: ', QUIET, b'thanks\r\n']))
    _, outputs = execute(interpreter, 'x')
    assert outputs == [TerminalOutput('password: '), TerminalOutput('thanks\n')]


def test_a_quiet_spell_is_waited_out_without_a_line_to_show():
    interpreter, _ = make(
        lambda source: Reply(output=[b'partial', QUIET, b' line\r\n']),
        config=BashInterpreter.Config(partial_line_s=None),
    )
    _, outputs = execute(interpreter, 'x')
    assert outputs == [TerminalOutput('partial line\n')]


def test_output_is_limited_to_its_head_and_tail():
    lines = b''.join(b'%d\r\n' % (i,) for i in range(100))
    interpreter, _ = make(
        lambda source: Reply(output=[lines[:150], lines[150:]]),
        config=BashInterpreter.Config(max_output_lines=7, max_tail_lines=3),
    )
    _, outputs = execute(interpreter, 'seq')
    assert outputs == [
        TerminalOutput(''.join(f'{i}\n' for i in range(7))),
        NoteOutput('[more output follows: only its last 3 lines will be shown, once the command has ended]'),
        NoteOutput('[... 90 lines not shown ...]'),
        TerminalOutput('97\n98\n99\n'),
    ]


def test_output_within_its_limit_is_untouched():
    interpreter, _ = make(
        lambda source: Reply(output=[b'1\r\n2\r\n', b'3\r\n']),
        config=BashInterpreter.Config(max_output_lines=3, max_tail_lines=1),
    )
    _, outputs = execute(interpreter, 'seq')
    assert outputs == [TerminalOutput('1\n2\n'), TerminalOutput('3\n')]


def test_output_just_past_its_limit_loses_nothing():
    interpreter, _ = make(
        lambda source: Reply(output=[b'1\r\n2\r\n3\r\n4\r\n']),
        config=BashInterpreter.Config(max_output_lines=2, max_tail_lines=5),
    )
    _, outputs = execute(interpreter, 'seq')
    assert outputs == [
        TerminalOutput('1\n2\n'),
        NoteOutput('[more output follows: only its last 5 lines will be shown, once the command has ended]'),
        TerminalOutput('3\n4\n'),
    ]


def test_output_past_its_limit_with_no_tail_kept():
    interpreter, _ = make(
        lambda source: Reply(output=[b'1\r\n2\r\n3\r\n']),
        config=BashInterpreter.Config(max_output_lines=1, max_tail_lines=0),
    )
    _, outputs = execute(interpreter, 'seq')
    assert outputs == [
        TerminalOutput('1\n'),
        NoteOutput('[more output follows: it will not be shown]'),
        NoteOutput('[... 2 lines not shown ...]'),
    ]


def test_the_terminal_follows_the_host_size():
    size = [(40, 100)]
    spawner = ScriptedSpawner()
    interpreter = BashInterpreter(spawner, size=lambda: size[0], clock=spawner.clock)

    execute(interpreter, 'x')
    assert spawner.shell.size == (40, 100)
    size[0] = (40, 72)
    execute(interpreter, 'x')
    assert spawner.shell.size == (40, 72)


##
# Versions


def test_an_old_bash_is_refused():
    interpreter, spawner = make(version='3.0')

    with pytest.raises(BashVersionError, match=r"bash is not bash 3\.2 or later: '3\.0'"):
        execute(interpreter, 'echo hi')
    assert not interpreter.is_started
    assert spawner.shell.is_closed
    assert spawner.shell.sources == []


def test_a_shell_which_is_not_a_bash_is_refused():
    interpreter, spawner = make(version='sh: 1: Bad substitution')

    with pytest.raises(BashVersionError, match='Bad substitution'):
        execute(interpreter, 'echo hi')
    assert spawner.shell.is_closed


def test_the_version_check_can_be_skipped():
    interpreter, spawner = make(version='3.0', config=BashInterpreter.Config(no_version_check=True))

    assert execute(interpreter, 'echo hi')[0].ok
    assert spawner.shell.commands == []


##
# Abandoned commands


def test_a_cancelled_command_is_interrupted_and_the_shell_kept():
    replies = iter([
        Reply(output=[b'before\r\n', Cancelled()], is_running=True),
        Reply(output=[b'after\r\n']),
    ])
    interpreter, spawner = make(lambda source: next(replies))

    sink = ListOutputSink()
    with pytest.raises(Cancelled):
        lang.sync_await(interpreter.execute('sleep 100', sink))
    assert list(sink.outputs) == [TerminalOutput('before\n')]
    assert (spawner.shell.num_shell_interrupts, spawner.shell.num_interrupts) == (1, 1)
    # The shell had the interrupt in hand before its job died of it: the rest of the submission was abandoned, not gone
    # on to.
    assert spawner.shell.num_went_on == 0

    # The interrupt ended it: the shell is found at its prompt, and nothing of the old command leaks into the new.
    result, outputs = execute(interpreter, 'echo after')
    assert result.ok
    assert outputs == [TerminalOutput('after\n')]
    assert len(spawner.shells) == 1
    assert (spawner.shell.num_interrupts, spawner.shell.num_suspends) == (1, 0)
    assert spawner.shell.commands == [BashProtocol.VERSION, BashProtocol.SYNC]


def test_a_cancellation_which_races_the_commands_end():
    # The command had already finished: the interrupts find an idle shell, which answers each with a prompt of its own.
    replies = iter([
        Reply(output=[b'done\r\n', Cancelled()]),
        Reply(output=[b'next\r\n']),
    ])
    interpreter, spawner = make(lambda source: next(replies))

    with pytest.raises(Cancelled):
        lang.sync_await(interpreter.execute('true', ListOutputSink()))

    result, outputs = execute(interpreter, 'echo next')
    assert result.ok
    assert outputs == [TerminalOutput('next\n')]


def test_a_stale_prompt_is_not_taken_for_the_commands():
    interpreter, spawner = make()
    execute(interpreter, 'first')

    spawner.handler = lambda source: Reply(output=[spawner.shell.mark(1, 130) + b'real\r\n'], returncode=7)
    result, outputs = execute(interpreter, 'second')
    assert result.value == lang.just(7)
    assert outputs == [TerminalOutput('real\n'), NoteOutput('[exit 7]')]


def test_a_lost_interrupt_is_sent_again():
    # An interrupt which finds the shell between a command's builtins and the job it is about to start is lost on it.
    replies = iter([
        Reply(output=[Cancelled()], is_running=True, num_interrupts_lost=1),
        Reply(output=[b'after\r\n']),
    ])
    interpreter, spawner = make(lambda source: next(replies))

    with pytest.raises(Cancelled):
        lang.sync_await(interpreter.execute('echo started; sleep 100', ListOutputSink()))

    result, outputs = execute(interpreter, 'echo after')
    assert result.ok
    assert outputs == [TerminalOutput('after\n')]
    assert (spawner.shell.num_interrupts, spawner.shell.num_suspends) == (2, 0)
    assert spawner.shell.num_shell_interrupts == 2
    assert spawner.shell.num_went_on == 0
    assert spawner.shell.commands == [BashProtocol.VERSION, BashProtocol.SYNC]
    assert spawner.clock.now == pytest.approx(interpreter.config.interrupt_timeout_s)


def test_a_command_deaf_to_interrupts_is_stopped_and_killed():
    replies = iter([
        Reply(output=[Cancelled()], is_running=True, is_deaf=True),
        Reply(output=[b'after\r\n']),
    ])
    interpreter, spawner = make(lambda source: next(replies))

    with pytest.raises(Cancelled):
        lang.sync_await(interpreter.execute('trap "" INT; sleep 100', ListOutputSink()))

    result, outputs = execute(interpreter, 'echo after')
    assert result.ok
    assert outputs == [TerminalOutput('after\n')]
    assert len(spawner.shells) == 1
    assert (spawner.shell.num_interrupts, spawner.shell.num_suspends) == (2, 1)
    assert spawner.shell.num_shell_interrupts == 2
    assert spawner.shell.commands == [BashProtocol.VERSION, BashProtocol.KILL_STOPPED_JOBS]
    assert spawner.shell.num_stopped_jobs == 0
    # One timeout for the interrupt sent with the cancellation, one for the second.
    assert spawner.clock.now == pytest.approx(2 * interpreter.config.interrupt_timeout_s)


def test_a_stuck_shell_is_replaced():
    replies = iter([
        Reply(output=[Cancelled()], is_running=True, is_stuck=True),
        Reply(output=[b'after\r\n']),
    ])
    interpreter, spawner = make(lambda source: next(replies))

    with pytest.raises(Cancelled):
        lang.sync_await(interpreter.execute('stuck', ListOutputSink()))
    old = spawner.shell

    result, outputs = execute(interpreter, 'echo after')
    assert result.ok
    assert outputs == [
        NoteOutput('[the shell did not come back from an interrupt: starting a new one]'),
        TerminalOutput('after\n'),
    ]
    assert old.is_closed
    assert len(spawner.shells) == 2
    assert spawner.shell.sources == ['echo after']


##
# Full-screen programs


def test_a_program_taking_the_screen_over_is_stopped_and_killed():
    interpreter, spawner = make(
        lambda source: Reply(output=[b'\x1b[?1049h\x1b[2J\x1b[Hdrawn all over'], is_running=True),
    )

    result, outputs = execute(interpreter, 'vi')
    assert result.value == lang.just(148)
    assert outputs == [NoteOutput('[full-screen programs are not supported here: stopping it]')]
    assert (spawner.shell.num_interrupts, spawner.shell.num_suspends) == (0, 1)
    assert spawner.shell.num_shell_interrupts == 0
    assert spawner.shell.commands == [BashProtocol.VERSION, BashProtocol.KILL_STOPPED_JOBS]
    assert spawner.shell.num_stopped_jobs == 0

    spawner.handler = lambda source: Reply(output=[b'fine\r\n'])
    assert execute(interpreter, 'echo fine')[1] == [TerminalOutput('fine\n')]


##
# The shell's own life


def test_exit_ends_the_shell_and_the_next_use_starts_another():
    replies = iter([
        Reply(output=[b'exit\r\n'], exits_shell=True),
        Reply(output=[b'again\r\n']),
    ])
    interpreter, spawner = make(lambda source: next(replies))

    result, outputs = execute(interpreter, 'exit')
    assert result.status is ResultStatus.EXIT
    assert outputs == [TerminalOutput('exit\n'), NoteOutput('[the shell exited]')]
    assert spawner.shell.is_closed
    assert not interpreter.is_started

    result, outputs = execute(interpreter, 'echo again')
    assert result.ok
    assert outputs == [TerminalOutput('again\n')]
    assert len(spawner.shells) == 2


def test_a_shell_which_went_while_idle_is_replaced_and_the_command_run():
    interpreter, spawner = make(lambda source: Reply(output=[b'ran\r\n']))
    execute(interpreter, 'first')
    spawner.shell.die()

    result, outputs = execute(interpreter, 'second')
    assert result.ok
    assert outputs == [NoteOutput('[the shell was gone: starting a new one]'), TerminalOutput('ran\n')]
    assert [s.sources for s in spawner.shells] == [['first'], ['second']]
    assert spawner.shells[0].is_closed


def test_a_shell_which_does_not_come_up_with_its_startup_files_is_started_without():
    interpreter, spawner = make(
        lambda source: Reply(output=[b'ok\r\n']),
        comes_up=lambda argv: '--norc' in argv,
    )

    result, outputs = execute(interpreter, 'echo ok')
    assert result.ok
    assert outputs == [
        NoteOutput('[the shell did not reach its prompt with its startup files: starting without them]'),
        TerminalOutput('ok\n'),
    ]
    assert [s.argv for s in spawner.shells] == [
        ('bash', '--noediting', '-i'),
        ('bash', '--noprofile', '--norc', '--noediting', '-i'),
    ]
    assert spawner.shells[0].is_closed
    assert spawner.clock.now == pytest.approx(interpreter.config.start_timeout_s)


def test_a_shell_which_never_comes_up():
    interpreter, spawner = make(comes_up=lambda argv: False)
    with pytest.raises(BashStartError):
        execute(interpreter, 'echo ok')
    assert all(s.is_closed for s in spawner.shells)
    assert not interpreter.is_started


def test_a_shell_which_cannot_be_started():
    interpreter, _ = make(error=FileNotFoundError('bash'))
    with pytest.raises(BashStartError, match='bash'):
        execute(interpreter, 'echo ok')


def test_without_startup_files():
    interpreter, spawner = make(config=BashInterpreter.Config(no_rc=True))
    execute(interpreter, 'x')
    assert spawner.shell.argv == ('bash', '--noprofile', '--norc', '--noediting', '-i')


def test_aclose():
    interpreter, spawner = make()
    lang.sync_await(interpreter.aclose())
    execute(interpreter, 'x')
    lang.sync_await(interpreter.aclose())
    assert spawner.shell.is_closed
    assert not interpreter.is_started
