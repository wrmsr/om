import pathlib
import shutil
import sys
import typing as ta

from ... import lang
from ...argparse import all as ap
from ...term import styled as tst
from .parsing import parse_patch
from .types import ExtendedHeaderKind
from .types import FilePatch
from .types import PatchSet


with lang.auto_proxy_import(globals()):
    from . import term


##
# summary


def _display_path(fp: FilePatch) -> str:
    if fp.is_deleted_file:
        return fp.old_path or '<unknown>'
    if fp.is_new_file:
        return fp.new_path or '<unknown>'
    return fp.new_path or fp.old_path or '<unknown>'


def _is_rename(fp: FilePatch) -> bool:
    has_from = any(h.kind == ExtendedHeaderKind.RENAME_FROM for h in fp.extended_headers)
    has_to = any(h.kind == ExtendedHeaderKind.RENAME_TO for h in fp.extended_headers)
    return has_from and has_to


def _iter_modified_files(files: ta.Iterable[FilePatch]) -> ta.Iterator[FilePatch]:
    for fp in files:
        if not fp.is_new_file and not fp.is_deleted_file:
            yield fp


def _iter_added_files(files: ta.Iterable[FilePatch]) -> ta.Iterator[FilePatch]:
    for fp in files:
        if fp.is_new_file:
            yield fp


def _iter_removed_files(files: ta.Iterable[FilePatch]) -> ta.Iterator[FilePatch]:
    for fp in files:
        if fp.is_deleted_file:
            yield fp


def _print_summary(patch: PatchSet) -> None:
    print('Summary')
    print('-------')

    additions = 0
    deletions = 0
    renamed_files = 0

    modified_files = list(_iter_modified_files(patch.files))
    added_files = list(_iter_added_files(patch.files))
    removed_files = list(_iter_removed_files(patch.files))

    for fp in patch.files:
        path = _display_path(fp)

        if fp.binary:
            print(f'{path}:', '(binary file)')
        else:
            additions += fp.added_count
            deletions += fp.removed_count
            print(f'{path}:', f'+{fp.added_count:d} additions,', f'-{fp.removed_count:d} deletions')

        if _is_rename(fp):
            renamed_files += 1

    print()
    print(
        f'{len(modified_files):d} modified file(s), '
        f'{len(added_files):d} added file(s), '
        f'{len(removed_files):d} removed file(s)',
    )
    if renamed_files:
        print(f'{renamed_files:d} file(s) renamed')
    print(f'Total: {additions:d} addition(s), {deletions:d} deletion(s)')


##
# render


def find_git_root() -> pathlib.Path:
    cwd = pathlib.Path.cwd()
    if (cwd / '.git').exists():
        return cwd

    for directory in cwd.parents:
        if (directory / '.git').exists():
            return directory
    return cwd


##


class Cli(ap.Cli):
    @ap.cmd(
        ap.arg(
            'file',
            nargs='?',
            help='if not specified, read diff data from stdin',
        ),
        ap.arg(
            '--show-diff',
            action='store_true',
            default=False,
            help='output diff to stdout',
        ),
    )
    def summary(self) -> None:
        if self.args.file is not None:
            diff = pathlib.Path(self.args.file).read_text()
        else:
            diff = sys.stdin.read()

        patch = parse_patch(diff)

        if self.args.show_diff:
            sys.stdout.write(diff)
            if diff and not diff.endswith('\n'):
                sys.stdout.write('\n')
            print()

        _print_summary(patch)

    #

    @ap.cmd(
        ap.arg('file', nargs='?'),
        ap.arg('-r', '--root'),
        ap.arg('-w', '--width', type=int),
        ap.arg('--no-color', action='store_true'),
        ap.arg('--no-syntax', action='store_true'),
    )
    def render(self) -> None:
        project_root = pathlib.Path(self.args.root) if self.args.root else find_git_root()

        if self.args.file is not None:
            diff = pathlib.Path(self.args.file).read_text()
        else:
            diff = sys.stdin.read()

        width = self.args.width or shutil.get_terminal_size((80, 24)).columns
        color_depth = tst.ColorDepth.MONO if self.args.no_color else tst.detect_color_depth()
        sys.stdout.write(term.render_diff_ansi(
            parse_patch(diff),
            project_root,
            width=width,
            syntax_highlighting=not self.args.no_syntax,
            color_depth=color_depth,
        ))


# @om-manifest
_CLI_MODULE = {'!omdev.cli.types.CliModule': {
    'name': 'diff',
    'module': __name__,
}}


def _main(argv: ta.Sequence[str] | None = None) -> int:
    Cli(argv).cli_run_and_exit()


if __name__ == '__main__':
    raise SystemExit(_main())
