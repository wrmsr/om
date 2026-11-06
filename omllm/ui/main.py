import argparse
import typing as ta

from omcore import lang


##


def _main(argv: lang.SequenceNotStr[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        add_help=False,
        allow_abbrev=False,
    )
    frontends = parser.add_mutually_exclusive_group()
    frontends.add_argument('--bare', action='store_true')
    frontends.add_argument('--web', action='store_true')

    ns, args = parser.parse_known_args(argv)

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
