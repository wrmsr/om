import argparse
import ast
import contextlib
import importlib
import importlib.machinery
import importlib.util
import io
import os
import platform
import runpy
import sys
import types
import typing as ta
import zipfile

from omcore import check

from . import globalruntime
from .compiler import hy_compile
from .compiler import hy_eval
from .errors import HyLanguageError
from .errors import filtered_hy_exceptions
from .errors import hy_exc_handler
from .models import Lazy
from .models import Object
from .reader import mangle
from .reader import read_many
from .repl import REPL
from .runtime import HyRuntime


##


class _OptionDef(ta.TypedDict):
    name: list[str]
    help: str
    dest: ta.NotRequired[str]
    action: ta.NotRequired[str]
    terminate: ta.NotRequired[bool]


class _Hy2pyOptions(argparse.Namespace):
    module: str | None
    FILE: str | None
    use_stdin: bool
    with_source: bool
    with_ast: bool
    without_python: bool
    output: str | None


def set_path(filename: str | os.PathLike[str]) -> None:
    """Emulate Python cmdline behavior by setting `sys.path` relative to the executed file's location."""

    if sys.path[0] == '':
        sys.path.pop(0)
    sys.path.insert(0, os.path.realpath(os.path.dirname(os.path.normpath(filename))))


def _show_internal_errors() -> bool:
    return bool(os.environ.get('HY_SHOW_INTERNAL_ERRORS', ''))


def _filtered_hy_exceptions() -> ta.ContextManager[None]:
    return filtered_hy_exceptions(show_internal_errors=_show_internal_errors())


def _handle_exc(exc_info: tuple[ta.Any, ta.Any, ta.Any] | None = None) -> None:
    hy_exc_handler(*(exc_info or sys.exc_info()), show_internal_errors=_show_internal_errors())


def run_command(runtime: HyRuntime, source: str, filename: str | None = None) -> int:
    __main__ = importlib.import_module('__main__')

    with _filtered_hy_exceptions():
        try:
            hy_eval(
                read_many(source, filename=filename),
                __main__.__dict__,
                __main__,
                filename=filename,
                source=source,
                runtime=runtime,
            )
        except HyLanguageError:
            _handle_exc()
            return 1
    return 0


_PYTHON_FILE_SUFFIXES: ta.AbstractSet[str] = frozenset([
    *importlib.machinery.SOURCE_SUFFIXES,
    *importlib.machinery.BYTECODE_SUFFIXES,
])


def run_path(filename: str) -> None:
    """
    Run a file, directory, or zip archive as `__main__`. Files are treated as Hy source unless they have a Python
    extension. Requires the global runtime to be installed.
    """

    check.state(globalruntime.is_installed())

    if (
            os.path.isdir(filename) or
            zipfile.is_zipfile(filename) or
            os.path.splitext(filename)[1] in _PYTHON_FILE_SUFFIXES
    ):
        # With the global runtime installed, Python's machinery handles everything else - including finding a
        # `__main__.hy` in a directory or archive.
        runpy.run_path(filename, run_name='__main__')
        return

    # Load Hy source files with a `HyLoader` (meaning they're bytecode-cached, as imported modules are) into a fresh
    # `__main__` module.
    loader = globalruntime.HyLoader('__main__', filename)
    main = types.ModuleType('__main__')
    main.__file__ = filename
    main.__loader__ = loader

    # Give the main module a spec naming the script as a module - as Python itself does for `-m` - so that
    # `multiprocessing`'s `spawn` and `forkserver` children (which can't run Hy files by path) re-import it by name.
    base, ext = os.path.splitext(os.path.basename(filename))
    if ext == '.hy':
        main.__spec__ = importlib.util.spec_from_file_location(
            base,
            filename,
            loader=globalruntime.HyLoader(base, filename),
        )

    prev_main = sys.modules.get('__main__')
    sys.modules['__main__'] = main
    try:
        loader.exec_module(main)
    finally:
        if prev_main is not None:
            sys.modules['__main__'] = prev_main


USAGE = 'hy [-h | -v | -i | -c CMD | -m MODULE | FILE | -] [ARG]...'
EPILOG = """
FILE
  program read from script
-
  program read from stdin
[ARG]...
  arguments passed to program in (cut sys.argv 1)
"""


class HyArgError(Exception):
    pass


def cmdline_handler(argv: ta.Sequence[str]) -> int:
    # We need to terminate interpretation of options after certain options, such as `-c`. So, we can't use `argparse`.

    defs: list[_OptionDef] = [  # noqa
        dict(
            name=['-B'],
            action='store_true',
            help="don't write .py[co] files on import; also PYTHONDONTWRITEBYTECODE=x",
        ),
        dict(
            name=['-c'],
            dest='command',
            terminate=True,
            help='program passed in as string',
        ),
        dict(
            name=['-E'],
            action='store_true',
            help='ignore PYTHON* environment variables (such as PYTHONPATH)',
        ),
        dict(
            name=['-h', '--help'],
            action='help',
            help='print this help message and exit',
        ),
        dict(
            name=['-i'],
            action='store_true',
            help='launch REPL after running script; forces a prompt even if stdin does not appear to be a terminal',
        ),
        dict(
            name=['-m'],
            dest='mod',
            terminate=True,
            help='run library module as a script',
        ),
        dict(
            name=['--repl-output-fn'],
            dest='repl_output_fn',
            help='function for printing REPL output (e.g., repr)',
        ),
        dict(
            name=['--spy'],
            action='store_true',
            help='print equivalent Python code before executing',
        ),
        dict(
            name=['-u', '--unbuffered'],
            action='store_true',
            help=(
                'force the stdout and stderr streams to be unbuffered; '
                'this option has no effect on stdin; also PYTHONUNBUFFERED=x'
            ),
        ),
        dict(
            name=['-v', '--version'],
            action='version',
            help='print the Hy version number and exit',
        ),
    ]

    runtime = globalruntime.install()

    program = argv[0]
    argv = list(argv[1:])
    options: dict[str, str | bool] = {}

    def err(fmt: str, *args: object) -> ta.NoReturn:
        raise HyArgError('hy: ' + fmt.format(*args))

    def proc_opt(
            opt: str,
            arg: str | None = None,
            item: str | None = None,
            i: int | None = None,
    ) -> bool | ta.Literal['terminate']:
        matches = [o for o in defs if opt in o['name']]
        if not matches:
            err('unrecognized option: {}', opt)
        [match] = matches
        if 'dest' in match:
            if arg:
                pass
            elif i is not None and item is not None and i + 1 < len(item):
                arg = item[i + 1 + (item[i + 1] == '='):]
            elif argv:
                arg = argv.pop(0)
            else:
                err('option {}: expected one argument', opt)
            options[match['dest']] = check.not_none(arg)
        else:
            options[match['name'][-1].lstrip('-')] = True
        if 'terminate' in match:
            return 'terminate'
        return 'dest' in match

    # Collect options.
    while argv:
        item = argv.pop(0)
        if item == '--':
            break
        elif item.startswith('--'):
            # One double-hyphen option.
            opt, _, arg = item.partition('=')
            if proc_opt(opt, arg=arg) == 'terminate':
                break
        elif item.startswith('-') and item != '-':
            # One or more single-hyphen options.
            for i in range(1, len(item)):
                x = proc_opt('-' + item[i], item=item, i=i)
                if x:
                    break
            if x == 'terminate':
                break
        else:
            # We're done with options. Add the item back.
            argv.insert(0, item)
            break

    if 'E' in options:
        _remove_python_envs()

    if 'B' in options:
        sys.dont_write_bytecode = True

    if 'unbuffered' in options:
        for k in 'stdout', 'stderr':
            setattr(
                sys,
                k,
                io.TextIOWrapper(
                    io.FileIO(getattr(sys, k).fileno(), 'w', closefd=False), write_through=True,
                ),
            )

    if 'help' in options:
        print('usage:', USAGE)
        print()
        print('optional arguments:')
        for o in defs:
            print(
                ', '.join(o['name']) + ('=' + o['dest'].upper() if 'dest' in o else ''),
            )
            print(
                '    '
                + o['help']
                + (' (terminates option list)' if o.get('terminate') else ''),
            )
        print(EPILOG)
        return 0

    action, action_arg = (
        # If the `command` or `mod` options were provided, we'll run the corresponding code.
        ('eval_string', check.isinstance(options['command'], str)) if 'command' in options else
        ('run_module', check.isinstance(options['mod'], str)) if 'mod' in options else
        # Otherwise, we'll run any provided filename as a script (or standard input, if the filename is "-").
        ('run_script_stdin', None) if argv and argv[0] == '-' else
        ('run_script_file', argv[0]) if argv else
        # With none of those arguments, we'll launch the REPL (if standard input is a TTY) or run a script from standard
        # input (otherwise).
        ('just_repl', None) if sys.stdin.isatty() else
        ('run_script_stdin', None))
    repl = (
        REPL(
            spy=bool(options.get('spy')),
            output_fn=check.isinstance(options['repl_output_fn'], str) if 'repl_output_fn' in options else None,
            runtime=runtime,
            startup=os.environ.get('HYSTARTUP'),
        )
        if 'i' in options or action == 'just_repl'
        else None
    )
    source = ''
    filename = '<stdin>'

    if action == 'eval_string':
        sys.argv = ['-c', *argv]
        if repl:
            source = check.not_none(action_arg)
            filename = '<string>'
        else:
            return run_command(runtime, check.not_none(action_arg), filename='<string>')
    elif action == 'run_module':
        if repl:
            raise ValueError
        set_path('')
        sys.argv = [program, *argv]
        runpy.run_module(mangle(action_arg), run_name='__main__', alter_sys=True)
        return 0
    elif action == 'run_script_stdin':
        sys.argv = argv
        if not repl:
            return run_command(runtime, sys.stdin.read(), filename='<stdin>')
    elif action == 'run_script_file':
        sys.argv = argv
        filename = check.not_none(action_arg)
        if not os.path.isabs(filename):
            filename = os.path.join(os.getcwd(), filename)
        set_path(filename)
        # Ensure __file__ is set correctly in the code we're about to run.
        if platform.system() == 'Windows':
            filename = os.path.normpath(filename)
        if repl:
            with open(filename, encoding='utf-8') as source_file:
                source = source_file.read()
            repl.compile.compiler.skip_next_shebang = True
        else:
            try:
                with _filtered_hy_exceptions():
                    run_path(str(filename))
                return 0
            except FileNotFoundError as e:
                print(
                    f"hy: Can't open file '{e.filename}': [Errno {e.errno}] {e.strerror}",
                    file=sys.stderr,
                )
                sys.exit(e.errno)
            except HyLanguageError:
                _handle_exc()
                sys.exit(1)
    else:
        check.state(action == 'just_repl')

    # If we didn't return earlier, we'll be using the REPL.
    repl = check.not_none(repl)
    if source:
        # Execute `source` in the REPL before entering interactive mode.
        res = None
        filename = str(filename)
        with _filtered_hy_exceptions():
            accum = ''
            for chunk in ([source] if isinstance(source, str) else source):
                accum += chunk
                res = repl.runsource(accum, filename=filename)
                if not res:
                    accum = ''
        # If the command was prematurely ended, show an error (just like Python does).
        if res:
            _handle_exc()
    return repl.run()


# entry point for cmd line script "hy"
def hy_main() -> ta.NoReturn:
    sys.path.insert(0, '')
    try:
        sys.exit(cmdline_handler(sys.argv))
    except HyArgError as e:
        print(e)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001  # Report exceptions raised by the user's program.
        _handle_exc((type(e), e, e.__traceback__))
        sys.exit(1)


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


def hy2py_worker(
        runtime: HyRuntime,
        source: str | os.PathLike[str],
        options: _Hy2pyOptions,
        filename: str | None = None,
        parent_module: str | None = None,
        output_filepath: str | None = None,
        *,
        source_is_file: bool = False,
) -> None:
    source_path = None
    if source_is_file or isinstance(source, os.PathLike):
        source_path = os.fspath(source)
        with open(source_path, encoding='utf-8') as source_file:
            source = source_file.read()
        if parent_module is None:
            set_path(source_path)

    if not output_filepath and options.output:
        output_filepath = options.output

    with (
        open(output_filepath, 'w', encoding='utf-8')
        if output_filepath
        else contextlib.nullcontext()
    ) as output_file:

        def printing_source(hst: Lazy) -> Lazy:
            def _printing_gen(hst: Lazy) -> ta.Iterator[Object]:
                for node in hst:
                    if options.with_source:
                        print(node, file=output_file)
                    yield node
            printing_hst = Lazy(_printing_gen(hst))
            printing_hst.source = hst.source
            printing_hst.filename = hst.filename
            printing_hst.reader = hst.reader
            return printing_hst

        hst = printing_source(read_many(source, filename, skip_shebang=True))

        with _filtered_hy_exceptions():
            module_name = (
                os.path.splitext(os.path.basename(source_path))[0]
                if source_path else
                os.path.basename(check.not_none(filename)))
            if parent_module:
                module_name = f'{parent_module}.{module_name}'
            module = runtime.new_module(module_name, filename=source_path)
            runtime.modules.add_module(module)
            try:
                _ast = hy_compile(
                    hst,
                    module,
                    filename=filename,
                    source=source,
                    preamble=True,
                    runtime=runtime,
                )
            finally:
                runtime.modules.remove_module(module_name)

        if options.with_source:
            print()
            print()

        if options.with_ast:
            print(ast.dump(_ast, indent=2), file=output_file)
            print()
            print()

        if not options.without_python:
            print(ast.unparse(_ast), file=output_file)


# entry point for cmd line script "hy2py"
def hy2py_main() -> ta.NoReturn:
    parser = argparse.ArgumentParser(
        prog='hy2py',
        usage='%(prog)s [options] [-m MODULE | FILE | -]',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    gp = parser.add_argument_group().add_mutually_exclusive_group()
    gp.add_argument('-m', dest='module', help='convert Hy module (or all files in module)')
    gp.add_argument(
        'FILE',
        type=str,
        nargs='?',
        help='convert Hy source file',
    )
    gp.add_argument('-', dest='use_stdin', action='store_true', help='read Hy from stdin')
    parser.add_argument(
        '--with-source',
        '-s',
        action='store_true',
        help='Show the parsed source structure',
    )
    parser.add_argument(
        '--with-ast', '-a', action='store_true', help='Show the generated AST',
    )
    parser.add_argument(
        '--without-python',
        '-np',
        action='store_true',
        help=('Do not show the Python code generated from the AST'),
    )
    parser.add_argument(
        '--output',
        '-o',
        type=str,
        nargs='?',
        help='output file / directory',
    )

    options = parser.parse_args(sys.argv[1:], namespace=_Hy2pyOptions())

    runtime = globalruntime.install()

    if options.use_stdin or (options.FILE is None and options.module is None):
        sys.path.insert(0, '')
        filename = '<stdin>'
        hy2py_worker(runtime, sys.stdin.read(), options, filename)
    elif options.module:
        if options.module[:1] == '.':
            raise ValueError('Relative module names not supported')
        sys.path.insert(0, '')
        filename = options.module.replace('.', os.sep)
        if os.path.isdir(filename):
            # handle recursively if --output is specified
            if not options.output:
                raise ValueError(
                    f'{filename} is a directory but the output directory is not specified. Use --output or -o in '
                    f'command line arguments to specify the output directory.',
                )
            os.makedirs(options.output, exist_ok=True)
            for path, _, files in os.walk(filename):
                for name in files:
                    filename_raw, filename_ext = os.path.splitext(name)
                    if filename_ext == '.hy':
                        filepath = os.path.join(path, name)
                        # make sure to follow original file structure
                        subdirectory = os.path.relpath(path, filename)
                        output_directory_path = os.path.join(
                            options.output, subdirectory,
                        )
                        os.makedirs(output_directory_path, exist_ok=True)
                        hy2py_worker(
                            runtime,
                            filepath,
                            options,
                            parent_module=path.replace(os.sep, '.'),
                            output_filepath=os.path.join(
                                output_directory_path, filename_raw + '.py',
                            ),
                            source_is_file=True,
                        )
        else:
            filename += '.hy'
            parent_module = '.'.join(options.module.split('.')[:-1])
            hy2py_worker(runtime, filename, options, parent_module=parent_module, source_is_file=True)
    else:
        hy2py_worker(runtime, check.not_none(options.FILE), options, options.FILE, source_is_file=True)
    parser.exit(0)


# remove PYTHON* environment variables, such as "PYTHONPATH"
def _remove_python_envs() -> None:
    for key in list(os.environ.keys()):
        if key.startswith('PYTHON'):
            os.environ.pop(key)
