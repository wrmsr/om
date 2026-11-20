import argparse
import sys
import typing as ta

from omcore import lang


##


def _build_frontend_parser() -> argparse.ArgumentParser:
    """
    Takes the choice of frontend and nothing else: every other argument is left for the chosen frontend's own parser.
    A flag taken here never reaches that parser, so none of these may be one of its own.
    """

    parser = argparse.ArgumentParser(
        add_help=False,
        allow_abbrev=False,
    )

    frontends = parser.add_mutually_exclusive_group()
    frontends.add_argument('--bare', action='store_true')
    frontends.add_argument('--web', action='store_true')

    return parser


def _main(argv: lang.SequenceNotStr[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == 'evals':
        from .evals import minieval

        minieval._main(list(argv[1:]))  # noqa: SLF001
        return

    if argv and argv[0] == 'jobs':
        from .jobs.cli import run_jobs_cli

        run_jobs_cli(list(argv[1:]))
        return

    ns, args = _build_frontend_parser().parse_known_args(argv)

    #

    main: ta.Any

    if ns.bare:
        from .tui.bare import main
    elif ns.web:
        from .web import main
    else:
        from .tui.minitui import main

    main._main(args)  # noqa


if __name__ == '__main__':
    _main()
