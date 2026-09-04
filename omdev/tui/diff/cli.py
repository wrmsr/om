import os
import pathlib
import shutil
import sys

from omcore.term import styled as tst
from omcore.text import diffs

from .terminal import render_diff_ansi


##


def find_git_root() -> pathlib.Path:
    cwd = pathlib.Path.cwd()
    if (cwd / '.git').exists():
        return cwd

    for directory in cwd.parents:
        if (directory / '.git').exists():
            return directory
    return cwd


def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('file', nargs='?')
    parser.add_argument('-r', '--root')
    parser.add_argument('-w', '--width', type=int)
    parser.add_argument('--no-color', action='store_true')
    parser.add_argument('--no-syntax', action='store_true')
    args = parser.parse_args()

    try:
        project_root = pathlib.Path(args.root) if args.root else find_git_root()
        if args.file is not None:
            diff = pathlib.Path(args.file).read_text()
        else:
            diff = sys.stdin.read()

        width = args.width or shutil.get_terminal_size((80, 24)).columns
        color_depth = tst.ColorDepth.MONO if args.no_color else tst.detect_color_depth()
        sys.stdout.write(render_diff_ansi(
            diffs.parse_patch(diff),
            project_root,
            width=width,
            syntax_highlighting=not args.no_syntax,
            color_depth=color_depth,
        ))

    except BrokenPipeError:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)

    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == '__main__':
    _main()
