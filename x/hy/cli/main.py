"""The `hy` command."""
import enum
import io
import os
import platform
import runpy
import sys
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from .. import globalruntime
from ..errors import HyLanguageError
from ..reader import mangle
from ..repl import REPL
from ..runtime import HyRuntime
from .options import HyCliArgError
from .options import HyCliArgs
from .options import format_hy_cli_help
from .options import parse_hy_cli_args
from .running import filtered_exceptions
from .running import handle_exception
from .running import run_command
from .running import run_path
from .running import set_path


##


class _HyCliActionKind(enum.Enum):
    EVAL_STRING = enum.auto()
    RUN_MODULE = enum.auto()
    RUN_STDIN = enum.auto()
    RUN_FILE = enum.auto()
    REPL = enum.auto()


@dc.dataclass(frozen=True)
class _HyCliAction:
    kind: _HyCliActionKind
    arg: str | None = None

    @classmethod
    def of(cls, args: HyCliArgs) -> _HyCliAction:
        if isinstance(command := args.options.get('command'), str):
            return cls(_HyCliActionKind.EVAL_STRING, command)

        if isinstance(mod := args.options.get('mod'), str):
            return cls(_HyCliActionKind.RUN_MODULE, mod)

        # Otherwise, run any provided filename as a script (or standard input, if the filename is "-").
        if args.argv:
            if args.argv[0] == '-':
                return cls(_HyCliActionKind.RUN_STDIN)
            return cls(_HyCliActionKind.RUN_FILE, args.argv[0])

        # With none of those arguments, launch the REPL if standard input is a TTY, and otherwise run a script from it.
        if sys.stdin.isatty():
            return cls(_HyCliActionKind.REPL)
        return cls(_HyCliActionKind.RUN_STDIN)


def _remove_python_envs() -> None:
    """Remove `PYTHON*` environment variables, such as `PYTHONPATH`."""

    for key in list(os.environ.keys()):
        if key.startswith('PYTHON'):
            os.environ.pop(key)


def _unbuffer_stdio() -> None:
    for k in ['stdout', 'stderr']:
        setattr(
            sys,
            k,
            io.TextIOWrapper(
                io.FileIO(getattr(sys, k).fileno(), 'w', closefd=False),
                write_through=True,
            ),
        )


def _run_source_in_repl(
        repl: REPL,
        source: str,
        *,
        filename: str,
) -> None:
    """Run `source` in the REPL before it enters interactive mode."""

    with filtered_exceptions():
        incomplete = repl.runsource(source, filename=filename)

    # If the source ended prematurely, show an error (just like Python does).
    if incomplete:
        handle_exception()


def run_hy_cli(argv: ta.Sequence[str]) -> int:
    """Run the `hy` command with a full `sys.argv`-style argument list, returning an exit code."""

    args = parse_hy_cli_args(argv)
    opts = args.options

    if 'E' in opts:
        _remove_python_envs()

    if 'B' in opts:
        sys.dont_write_bytecode = True

    if 'unbuffered' in opts:
        _unbuffer_stdio()

    if 'help' in opts:
        print(format_hy_cli_help())
        return 0

    runtime: HyRuntime = globalruntime.install()

    action = _HyCliAction.of(args)

    repl: REPL | None = None
    if 'i' in opts or action.kind == _HyCliActionKind.REPL:
        output_fn = opts.get('repl_output_fn')
        repl = REPL(
            spy=bool(opts.get('spy')),
            output_fn=check.isinstance(output_fn, str) if output_fn is not None else None,
            runtime=runtime,
            startup=os.environ.get('HYSTARTUP'),
        )

    source: str | None = None
    filename = '<stdin>'

    match action.kind:
        case _HyCliActionKind.EVAL_STRING:
            sys.argv = ['-c', *args.argv]
            if repl is None:
                return run_command(runtime, check.not_none(action.arg), filename='<string>')
            source = check.not_none(action.arg)
            filename = '<string>'

        case _HyCliActionKind.RUN_MODULE:
            if repl is not None:
                raise HyCliArgError('hy: -i is not supported with -m')
            set_path('')
            sys.argv = [args.program, *args.argv]
            runpy.run_module(mangle(check.not_none(action.arg)), run_name='__main__', alter_sys=True)
            return 0

        case _HyCliActionKind.RUN_STDIN:
            sys.argv = list(args.argv)
            if repl is None:
                return run_command(runtime, sys.stdin.read(), filename='<stdin>')

        case _HyCliActionKind.RUN_FILE:
            sys.argv = list(args.argv)
            filename = check.not_none(action.arg)
            if not os.path.isabs(filename):
                filename = os.path.join(os.getcwd(), filename)
            set_path(filename)

            # Ensure `__file__` is set correctly in the code we're about to run.
            if platform.system() == 'Windows':
                filename = os.path.normpath(filename)

            if repl is not None:
                with open(filename, encoding='utf-8') as f:
                    source = f.read()
                repl.compile.compiler.skip_next_shebang = True

            else:
                try:
                    with filtered_exceptions():
                        run_path(filename)
                except FileNotFoundError as e:
                    print(
                        f"hy: Can't open file '{e.filename}': [Errno {e.errno}] {e.strerror}",
                        file=sys.stderr,
                    )
                    return e.errno or 1
                except HyLanguageError:
                    handle_exception()
                    return 1
                return 0

        case _HyCliActionKind.REPL:
            pass

    # If we didn't return earlier, we're using the REPL.
    repl = check.not_none(repl)
    if source:
        _run_source_in_repl(repl, source, filename=filename)
    return repl.run()


def hy_main() -> ta.NoReturn:
    sys.path.insert(0, '')

    try:
        sys.exit(run_hy_cli(sys.argv))

    except HyCliArgError as e:
        print(e)
        sys.exit(1)

    except Exception as e:  # noqa: BLE001  # Report exceptions raised by the user's program.
        handle_exception((type(e), e, e.__traceback__))
        sys.exit(1)
