"""
Option parsing for the `hy` command.

This can't use `argparse`, as - like Python's own command line - interpretation of options must end at certain options
(such as `-c`), with everything after them passed through to the program being run.
"""
import typing as ta

from omcore import dataclasses as dc


HyCliOptionValue: ta.TypeAlias = str | bool


##


@dc.dataclass(frozen=True)
class HyCliOption:
    names: ta.Sequence[str]
    help: str

    _: dc.KW_ONLY

    # If set, the option takes an argument, which is stored under this key.
    dest: str | None = None

    # If set, no further options are interpreted after this one.
    terminates: bool = False

    @property
    def key(self) -> str:
        return self.dest if self.dest is not None else self.names[-1].lstrip('-')


HY_CLI_OPTIONS: ta.Sequence[HyCliOption] = [
    HyCliOption(
        ['-B'],
        "don't write .py[co] files on import; also PYTHONDONTWRITEBYTECODE=x",
    ),
    HyCliOption(
        ['-c'],
        'program passed in as string',
        dest='command',
        terminates=True,
    ),
    HyCliOption(
        ['-E'],
        'ignore PYTHON* environment variables (such as PYTHONPATH)',
    ),
    HyCliOption(
        ['-h', '--help'],
        'print this help message and exit',
    ),
    HyCliOption(
        ['-i'],
        'launch REPL after running script; forces a prompt even if stdin does not appear to be a terminal',
    ),
    HyCliOption(
        ['-m'],
        'run library module as a script',
        dest='mod',
        terminates=True,
    ),
    HyCliOption(
        ['--repl-output-fn'],
        'function for printing REPL output (e.g., repr)',
        dest='repl_output_fn',
    ),
    HyCliOption(
        ['--spy'],
        'print equivalent Python code before executing',
    ),
    HyCliOption(
        ['-u', '--unbuffered'],
        (
            'force the stdout and stderr streams to be unbuffered; this option has no effect on stdin; also '
            'PYTHONUNBUFFERED=x'
        ),
    ),
]


HY_CLI_USAGE = 'hy [-h | -i | -c CMD | -m MODULE | FILE | -] [ARG]...'

HY_CLI_EPILOG = """
FILE
  program read from script
-
  program read from stdin
[ARG]...
  arguments passed to program in (cut sys.argv 1)
"""


def format_hy_cli_help(options: ta.Sequence[HyCliOption] = HY_CLI_OPTIONS) -> str:
    lines = [
        f'usage: {HY_CLI_USAGE}',
        '',
        'optional arguments:',
    ]

    for o in options:
        lines.append(', '.join(o.names) + (f'={o.dest.upper()}' if o.dest is not None else ''))
        lines.append('    ' + o.help + (' (terminates option list)' if o.terminates else ''))

    lines.append(HY_CLI_EPILOG)
    return '\n'.join(lines)


##


class HyCliArgError(Exception):
    pass


@dc.dataclass(frozen=True)
class HyCliArgs:
    program: str
    options: ta.Mapping[str, HyCliOptionValue]

    # The arguments remaining after the options.
    argv: ta.Sequence[str]


class _HyCliArgParser:
    def __init__(self, argv: ta.Sequence[str], options: ta.Sequence[HyCliOption]) -> None:
        super().__init__()

        self._argv = list(argv)
        self._options = options

        self._values: dict[str, HyCliOptionValue] = {}

    def _error(self, msg: str) -> ta.NoReturn:
        raise HyCliArgError(f'hy: {msg}')

    def _process(
            self,
            name: str,
            *,
            arg: str | None = None,
            rest: str = '',
    ) -> tuple[bool, bool]:
        """
        Process the option `name`, given either with an explicit `arg` (as in `--foo=bar`), or as one of a group of
        single-hyphen options (as in `-ic foo`) followed by the characters `rest`. Returns whether the rest of the
        group was consumed (as an argument), and whether option processing should stop.
        """

        matches = [o for o in self._options if name in o.names]
        if not matches:
            self._error(f'unrecognized option: {name}')
        [opt] = matches

        if opt.dest is None:
            self._values[opt.key] = True
            return False, opt.terminates

        if arg:
            pass
        elif rest:
            arg = rest[1:] if rest[0] == '=' else rest
        elif self._argv:
            arg = self._argv.pop(0)
        else:
            self._error(f'option {name}: expected one argument')

        self._values[opt.key] = arg
        return True, opt.terminates

    def parse(self) -> HyCliArgs:
        program, *self._argv = self._argv

        while self._argv:
            item = self._argv.pop(0)

            if item == '--':
                break

            elif item.startswith('--'):
                # One double-hyphen option.
                name, _, arg = item.partition('=')
                if self._process(name, arg=arg)[1]:
                    break

            elif item.startswith('-') and item != '-':
                # One or more single-hyphen options.
                terminated = False
                for i in range(1, len(item)):
                    consumed, terminated = self._process('-' + item[i], rest=item[i + 1:])
                    if consumed or terminated:
                        break
                if terminated:
                    break

            else:
                # We're done with options. Put the item back.
                self._argv.insert(0, item)
                break

        return HyCliArgs(
            program=program,
            options=self._values,
            argv=self._argv,
        )


def parse_hy_cli_args(
        argv: ta.Sequence[str],
        options: ta.Sequence[HyCliOption] = HY_CLI_OPTIONS,
) -> HyCliArgs:
    """Parse a full `sys.argv`-style argument list, including the program name."""

    return _HyCliArgParser(argv, options).parse()
