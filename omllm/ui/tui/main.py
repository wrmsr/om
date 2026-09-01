import argparse
import typing as ta

from omcore import lang


##


def _main(argv: lang.SequenceNotStr[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        add_help=False,
        allow_abbrev=False,
    )
    parser.add_argument('--bare', action='store_true')

    ns, args = parser.parse_known_args(argv)

    #

    main: ta.Any

    if ns.bare:
        from .bare import main
    else:
        from .minitui import main

    main._main(args)  # noqa


if __name__ == '__main__':
    _main()
