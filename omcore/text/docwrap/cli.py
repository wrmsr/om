"""
Usable as a jetbrains external tool:
  `om docwrap -i "$FilePath$" -s "$SelectionStartLine$" -S "$SelectionStartColumn$" -e "$SelectionEndLine$" -E "$SelectionEndColumn$"`

TODO:
 - fix 'stealing trailing line'
 - -> omdev.tools
 - at least file extension awareness, preserve say # prefixes in py comment blocks
  - maybe treesitter? or just special case py
"""  # noqa
import argparse
import json
import os.path
import sys
import typing as ta

from .api import docwrap
from .rendering import render


##


def wrap_cli_text(
        in_txt: str,
        *,
        width: int = 120,
        # All 1-based, exclusive ends
        start_line: int | None = None,
        start_col: int | None = None,
        end_line: int | None = None,
        end_col: int | None = None,
) -> str:
    in_lines = in_txt.splitlines()

    #

    if start_line is not None and end_line is not None:
        if start_line > end_line:
            raise ValueError('Start line cannot be greater than end line')
    if start_col not in (None, 1):
        raise ValueError('Start column not supported')

    if start_line is not None:
        if start_line < 1:
            raise ValueError('Start line cannot be less than 1')
        start_line = start_line - 1
    else:
        start_line = 0

    if end_line is not None:
        if end_line < 1:
            raise ValueError('End line cannot be less than 1')
        end_line = end_line - 1
    else:
        end_line = len(in_lines) - 1

    if end_col == 1:
        end_line -= 1

    #

    in_part_lines = in_lines[start_line:end_line + 1]

    if end_col not in (None, 1) and end_col != len(in_part_lines[-1]) + 1:
        raise ValueError('End column not supported')

    in_part = '\n'.join(in_part_lines)

    #

    root = docwrap(
        in_part,
        width=width,
    )

    out_part = render(root)

    out_txt = '\n'.join([
        *in_lines[:start_line],
        out_part,
        *in_lines[end_line + 1:],
        '',
    ])

    return out_txt


def _main(argv: ta.Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('file', nargs='?')

    parser.add_argument('-w', '--width', type=int, default=120)

    # All 1-based, exclusive ends
    parser.add_argument('-s', '--start-line', type=int)
    parser.add_argument('-S', '--start-col', type=int)
    parser.add_argument('-e', '--end-line', type=int)
    parser.add_argument('-E', '--end-col', type=int)

    parser.add_argument('-i', '--in-place', action='store_true')

    parser.add_argument('--log-args', action='store_true')

    args = parser.parse_args(argv)

    #

    if args.log_args:
        with open(os.path.join(os.path.dirname(__file__), 'cli.log'), 'a') as f:  # noqa
            f.write(json.dumps(args.__dict__, indent=None) + '\n')

    #

    if args.file:
        with open(args.file) as f:
            in_txt = f.read()
    else:
        if args.in_place:
            raise ValueError('Cannot use --in-place without specifying a file')
        in_txt = sys.stdin.read()

    #

    out_txt = wrap_cli_text(
        in_txt,
        width=args.width,
        start_line=args.start_line,
        start_col=args.start_col,
        end_line=args.end_line,
        end_col=args.end_col,
    )

    #

    if args.in_place:
        with open(args.file, 'w') as f:
            f.write(out_txt)
    else:
        print(out_txt)


if __name__ == '__main__':
    _main()
