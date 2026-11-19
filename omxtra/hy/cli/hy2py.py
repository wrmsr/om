"""The `hy2py` command: converts Hy source to Python source."""
import argparse
import ast
import contextlib
import os
import sys
import typing as ta

from omcore import check

from .. import globalruntime
from ..compat import unparse
from ..compiler import hy_compile
from ..models import Lazy
from ..models import Object
from ..reader import read_many
from ..runtime import HyRuntime
from .running import filtered_exceptions
from .running import set_path


##


class Hy2pyOptions(argparse.Namespace):
    module: str | None
    FILE: str | None
    use_stdin: bool
    with_source: bool
    with_ast: bool
    without_python: bool
    output: str | None


def _printing_forms(forms: Lazy, *, file: ta.TextIO | None) -> Lazy:
    """Wrap `forms` such that each form is printed as it's read."""

    def gen() -> ta.Iterator[Object]:
        for form in forms:
            print(form, file=file)
            yield form

    ret = Lazy(gen())
    ret.source = forms.source
    ret.filename = forms.filename
    ret.reader = forms.reader
    return ret


def hy2py_convert(
        runtime: HyRuntime,
        source: str,
        options: Hy2pyOptions,
        *,
        filename: str | None = None,
        source_path: str | None = None,
        parent_module: str | None = None,
        output_path: str | None = None,
) -> None:
    """
    Convert Hy `source` - read from the file `source_path` if given - to Python, writing it to `output_path` (by
    default, `options.output` or else standard output).
    """

    if source_path is not None and parent_module is None:
        set_path(source_path)

    if not output_path and options.output:
        output_path = options.output

    with (
        open(output_path, 'w', encoding='utf-8')
        if output_path
        else contextlib.nullcontext()
    ) as output_file:
        forms = read_many(source, filename, skip_shebang=True)
        if options.with_source:
            forms = _printing_forms(forms, file=output_file)

        with filtered_exceptions():
            module_name = (
                os.path.splitext(os.path.basename(source_path))[0]
                if source_path is not None else
                os.path.basename(check.not_none(filename))
            )
            if parent_module:
                module_name = f'{parent_module}.{module_name}'

            module = runtime.new_module(module_name, filename=source_path)
            runtime.modules.add_module(module)
            try:
                tree = hy_compile(
                    forms,
                    module,
                    filename=filename,
                    source=source,
                    preamble=True,
                    runtime=runtime,
                )
            finally:
                runtime.modules.remove_module(module_name)

        if options.with_source:
            print('\n', file=output_file)

        if options.with_ast:
            print(ast.dump(tree, indent=2), file=output_file)
            print('\n', file=output_file)

        if not options.without_python:
            print(unparse(tree), file=output_file)


def hy2py_convert_file(
        runtime: HyRuntime,
        source_path: str,
        options: Hy2pyOptions,
        *,
        filename: str | None = None,
        parent_module: str | None = None,
        output_path: str | None = None,
) -> None:
    with open(source_path, encoding='utf-8') as f:
        source = f.read()

    hy2py_convert(
        runtime,
        source,
        options,
        filename=filename,
        source_path=source_path,
        parent_module=parent_module,
        output_path=output_path,
    )


def _convert_package(
        runtime: HyRuntime,
        package_dir: str,
        options: Hy2pyOptions,
) -> None:
    if not options.output:
        raise ValueError(
            f'{package_dir} is a directory but the output directory is not specified. Use --output or -o in command '
            f'line arguments to specify the output directory.',
        )

    os.makedirs(options.output, exist_ok=True)

    for path, _, files in os.walk(package_dir):
        for name in files:
            base, ext = os.path.splitext(name)
            if ext != '.hy':
                continue

            # Mirror the original file structure.
            output_dir = os.path.join(options.output, os.path.relpath(path, package_dir))
            os.makedirs(output_dir, exist_ok=True)

            hy2py_convert_file(
                runtime,
                os.path.join(path, name),
                options,
                parent_module=path.replace(os.sep, '.'),
                output_path=os.path.join(output_dir, base + '.py'),
            )


def hy2py_main() -> ta.NoReturn:
    parser = argparse.ArgumentParser(
        prog='hy2py',
        usage='%(prog)s [options] [-m MODULE | FILE | -]',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    gp = parser.add_argument_group().add_mutually_exclusive_group()
    gp.add_argument('-m', dest='module', help='convert Hy module (or all files in module)')
    gp.add_argument('FILE', type=str, nargs='?', help='convert Hy source file')
    gp.add_argument('-', dest='use_stdin', action='store_true', help='read Hy from stdin')

    parser.add_argument('--with-source', '-s', action='store_true', help='Show the parsed source structure')
    parser.add_argument('--with-ast', '-a', action='store_true', help='Show the generated AST')
    parser.add_argument('--without-python', '-np', action='store_true', help='Do not show the generated Python')
    parser.add_argument('--output', '-o', type=str, nargs='?', help='output file / directory')

    options = parser.parse_args(sys.argv[1:], namespace=Hy2pyOptions())

    runtime = globalruntime.install()

    if options.use_stdin or (options.FILE is None and options.module is None):
        sys.path.insert(0, '')
        hy2py_convert(runtime, sys.stdin.read(), options, filename='<stdin>')

    elif options.module:
        if options.module.startswith('.'):
            raise ValueError('Relative module names not supported')

        sys.path.insert(0, '')
        path = options.module.replace('.', os.sep)

        if os.path.isdir(path):
            _convert_package(runtime, path, options)
        else:
            hy2py_convert_file(
                runtime,
                path + '.hy',
                options,
                parent_module='.'.join(options.module.split('.')[:-1]),
            )

    else:
        hy2py_convert_file(runtime, check.not_none(options.FILE), options, filename=options.FILE)

    parser.exit(0)
