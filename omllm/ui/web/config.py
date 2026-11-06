import typing as ta

from omcore import dataclasses as dc

from ..config import UiConfig


if ta.TYPE_CHECKING:
    import argparse


##


DEFAULT_WEB_HOST = '127.0.0.1'
DEFAULT_WEB_PORT = 8077


@dc.dataclass(frozen=True, kw_only=True)
class WebConfig(UiConfig):
    host: str | None = None

    # Zero binds an ephemeral port, which is then logged.
    port: int | None = None

    verbose: bool | None = None

    ##

    @classmethod
    def configure_argument_parser(cls, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        parser = super().configure_argument_parser(parser)

        parser.add_argument('--host')
        parser.add_argument('-p', '--port', type=int)

        parser.add_argument('-v', '--verbose', action='store_true')

        return parser

    @classmethod
    def build_kwargs_from_parsed_arguments(cls, args: argparse.Namespace) -> dict[str, ta.Any]:
        return dict(
            **super().build_kwargs_from_parsed_arguments(args),

            host=args.host,
            port=args.port,

            verbose=args.verbose,
        )
