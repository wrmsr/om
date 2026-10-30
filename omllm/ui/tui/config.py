import typing as ta

from omcore import dataclasses as dc

from ..config import UiConfig


if ta.TYPE_CHECKING:
    import argparse


##


@dc.dataclass(frozen=True, kw_only=True)
class TuiConfig(UiConfig):
    verbose: bool | None = None

    ##

    @classmethod
    def configure_argument_parser(cls, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        parser = super().configure_argument_parser(parser)

        parser.add_argument('-v', '--verbose', action='store_true')

        return parser

    @classmethod
    def build_kwargs_from_parsed_arguments(cls, args: argparse.Namespace) -> dict[str, ta.Any]:
        return dict(
            **super().build_kwargs_from_parsed_arguments(args),

            verbose=args.verbose,
        )
