import typing as ta

from omcore import dataclasses as dc
from omcore import lang


with lang.auto_proxy_import(globals()):
    import argparse


##


@dc.dataclass(frozen=True, kw_only=True)
class ConfigBase:
    @classmethod
    def configure_argument_parser(cls, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        return parser

    @classmethod
    def build_kwargs_from_parsed_arguments(cls, args: argparse.Namespace) -> dict[str, ta.Any]:  # noqa
        return {}

    #

    @classmethod
    def parse_from_arguments_(
            cls,
            argv: lang.SequenceNotStr[str] | None = None,
            *,
            parser: argparse.ArgumentParser | None = None,
    ) -> tuple[ta.Self, argparse.Namespace]:
        if parser is None:
            parser = argparse.ArgumentParser()
        cls.configure_argument_parser(parser)
        args = parser.parse_args(argv)
        kwargs = cls.build_kwargs_from_parsed_arguments(args)
        return cls(**kwargs), args

    @classmethod
    def parse_from_arguments(
            cls,
            argv: lang.SequenceNotStr[str] | None = None,
            *,
            parser: argparse.ArgumentParser | None = None,
    ) -> ta.Self:
        return cls.parse_from_arguments_(
            argv,
            parser=parser,
        )[0]
