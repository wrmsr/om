"""The `hyc` command: byte-compiles Hy source files."""
import argparse
import importlib.util
import sys
import typing as ta

from .. import globalruntime
from ..errors import HyLanguageError
from .running import set_path


##


def hyc_main() -> ta.NoReturn:
    parser = argparse.ArgumentParser(
        prog='hyc',
        description='Compile Hy source files to Python bytecode (.pyc).',
    )
    parser.add_argument('files', metavar='FILE', nargs='+', help='File(s) to compile')
    parser.add_argument(
        '-q',
        '--quiet',
        action='store_true',
        default=False,
        help="Suppress the 'Compiling … --> …' progress messages.",
    )

    options = parser.parse_args(sys.argv[1:])

    globalruntime.install()

    rv = 0
    for filename in options.files:
        set_path(filename)
        try:
            if not options.quiet:
                print(
                    f'Compiling {filename!r} --> {importlib.util.cache_from_source(filename)!r}',
                    file=sys.stderr,
                )
            globalruntime.compile_hy_file(filename)
        except (OSError, SyntaxError, HyLanguageError) as error:
            rv = 1
            print(f'{type(error).__name__}: {error}', file=sys.stderr)
        sys.path.pop(0)

    sys.exit(rv)
