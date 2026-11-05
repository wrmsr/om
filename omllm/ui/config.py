import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from .agent.config import AgentConfig
from .backends.config import BackendsConfig
from .configbase import ConfigBase


with lang.auto_proxy_import(globals()):
    import argparse


##


@dc.dataclass(frozen=True, kw_only=True)
class UiConfig(
    AgentConfig,
    BackendsConfig,
    ConfigBase,
):
    autoexec: lang.SequenceNotStr[str] | None = None

    yolo: bool | None = None
    diet_yolo: bool | None = None

    ##

    @classmethod
    def configure_argument_parser(cls, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        parser = super().configure_argument_parser(parser)

        parser.add_argument('-X', '--autoexec', action='append')

        parser.add_argument('--yolo', action='store_true')
        parser.add_argument('--diet-yolo', action='store_true')

        return parser

    @classmethod
    def build_kwargs_from_parsed_arguments(cls, args: argparse.Namespace) -> dict[str, ta.Any]:
        return dict(
            **super().build_kwargs_from_parsed_arguments(args),

            autoexec=args.autoexec,

            yolo=args.yolo,
            diet_yolo=args.diet_yolo,
        )
