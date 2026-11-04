import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from .. import llm
from .agent.config import AgentConfig
from .configbase import ConfigBase


with lang.auto_proxy_import(globals()):
    import argparse


##


@dc.dataclass(frozen=True, kw_only=True)
class UiConfig(AgentConfig, ConfigBase):
    model: str | None = None

    effort: llm.ReasoningEffort | None = None
    thinking: bool | None = None

    url: str | None = None
    backend_model_id: str | None = None

    autoexec: lang.SequenceNotStr[str] | None = None

    immediate: bool | None = None

    yolo: bool | None = None
    diet_yolo: bool | None = None

    ##

    @classmethod
    def configure_argument_parser(cls, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        parser = super().configure_argument_parser(parser)

        parser.add_argument('-m', '--model')

        parser.add_argument('--effort', type=llm.ReasoningEffort, choices=list(llm.ReasoningEffort))
        parser.add_argument('--thinking', action=argparse.BooleanOptionalAction, default=None)

        parser.add_argument('--url')
        parser.add_argument('--backend-model-id')

        parser.add_argument('-X', '--autoexec', action='append')

        parser.add_argument('-I', '--immediate', action='store_true')

        parser.add_argument('--yolo', action='store_true')
        parser.add_argument('--diet-yolo', action='store_true')

        return parser

    @classmethod
    def build_kwargs_from_parsed_arguments(cls, args: argparse.Namespace) -> dict[str, ta.Any]:
        return dict(
            **super().build_kwargs_from_parsed_arguments(args),

            model=args.model,

            effort=args.effort,
            thinking=args.thinking,

            url=args.url,
            backend_model_id=args.backend_model_id,

            autoexec=args.autoexec,

            immediate=args.immediate,

            yolo=args.yolo,
            diet_yolo=args.diet_yolo,
        )
