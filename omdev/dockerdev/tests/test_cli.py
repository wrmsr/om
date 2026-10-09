"""
How a `dockerdev run` command line splits: `dockerdev run [OPTIONS] [--] [COMMAND [ARG...]]`. Options are dockerdev's
own or else forwarded to `docker run`, which requires a forwarded option to be one argument (`--name=foo`, not
`--name foo`). The command starts at the first argument which is not an option, or after a `--` ending the options, and
from there on is passed to the container verbatim.
"""
import shlex

from ..cli import Cli
from ..config import Config
from ..run import RunArgs
from ..run import RunHost
from ..run import process_run_args


##


def _run_args(cmdline: str) -> RunArgs:
    return Cli(['run', *shlex.split(cmdline)])._build_run_args()  # noqa: SLF001


def _split(cmdline: str) -> tuple[list[str], list[str]]:
    args = _run_args(cmdline)
    return list(args.unknown_args or []), list(args.extra_args or [])


##


def test_the_command_starts_at_the_first_non_option():
    assert _split('') == ([], [])
    assert _split('bash') == ([], ['bash'])
    assert _split('bash -c "echo hi"') == ([], ['bash', '-c', 'echo hi'])

    # Once the command has started, nothing is read as an option - not even one of dockerdev's own.
    args = _run_args('-C python3 -v -X dev')
    assert args.mount_caches
    assert not args.verbose
    assert not args.x11
    assert args.extra_args == ['python3', '-v', '-X', 'dev']

    assert _split('bash --name=foo') == ([], ['bash', '--name=foo'])


def test_unknown_options_are_forwarded():
    assert _split('--name=foo --init bash') == (['--name=foo', '--init'], ['bash'])
    assert _split('--rm -it') == (['--rm', '-it'], [])

    # A forwarded option must be one argument: its separate value would be taken for the command.
    assert _split('--name foo bash') == (['--name'], ['foo', 'bash'])


def test_a_double_dash_ends_the_options():
    args = _run_args('-C -- bash -v')
    assert args.mount_caches
    assert not args.verbose
    assert args.extra_args == ['bash', '-v']

    assert _split('-- -v') == ([], ['-v'])
    assert _split('--name=foo --') == (['--name=foo'], [])

    # Only the first: a later one belongs to the command.
    assert _split('bash -- x') == ([], ['bash', '--', 'x'])
    assert _split('-- -- x') == ([], ['--', 'x'])


def test_a_double_dash_does_not_reach_docker(tmp_path):
    p = process_run_args(
        Config('ubuntu:24.04'),
        _run_args('-- bash -v'),
        'sha',
        host=RunHost(platform_system='Linux', sys_platform='linux', cwd=str(tmp_path)),
    )
    assert p.args[p.args.index('sha'):] == ['sha', 'bash', '-v']

    # With no command at all, the default one.
    p = process_run_args(
        Config('ubuntu:24.04'),
        _run_args('--'),
        'sha',
        host=RunHost(platform_system='Linux', sys_platform='linux', cwd=str(tmp_path)),
    )
    assert p.args[p.args.index('sha'):] == ['sha', 'bash']


def test_the_defaults_can_be_disabled():
    args = _run_args('--no-rm --no-interactive --no-tty bash')
    assert args.no_rm
    assert args.no_interactive
    assert args.no_tty
    assert args.extra_args == ['bash']

    args = _run_args('--name=foo bash')
    assert not args.no_rm
    assert not args.no_interactive
    assert not args.no_tty


def test_detach():
    for cmdline in ['-d bash', '--detach bash']:
        args = _run_args(cmdline)
        assert args.detach
        assert not args.no_interactive
        assert not args.no_tty
        assert args.extra_args == ['bash']

    assert not _run_args('bash').detach

    # dockerdev's `-d` means what docker's does, and docker's `--detach-keys` is not taken for it.
    args = _run_args('--detach-keys=ctrl-o,ctrl-d -d bash')
    assert args.detach
    assert args.unknown_args == ['--detach-keys=ctrl-o,ctrl-d']

    # Docker's clustered `-dit` still works: dockerdev takes the `-d`, and forwards the rest - harmlessly, as `-i` and
    # `-t` are on by default.
    args = _run_args('-dit bash')
    assert args.detach
    assert args.unknown_args == ['-it']


def test_cuda():
    assert _run_args('--cuda bash').cuda
    assert not _run_args('bash').cuda


def test_dockerdev_short_options_shadow_dockers():
    # dockerdev's `-v` (verbose) and `-P` (privileged) take docker's `-v` (volume) and `-P` (publish-all): spell those
    # `--volume=` and `--publish-all`.
    args = _run_args('-v /a:/b bash')
    assert args.verbose
    assert args.extra_args == ['/a:/b', 'bash']

    assert _split('--volume=/a:/b --publish-all bash') == (['--volume=/a:/b', '--publish-all'], ['bash'])
