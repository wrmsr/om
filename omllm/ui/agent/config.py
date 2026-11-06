import typing as ta
import uuid

from omcore import dataclasses as dc
from omcore import lang

from ..configbase import ConfigBase


with lang.auto_proxy_import(globals()):
    import argparse


##


@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class AgentConfig(ConfigBase):
    cwd: str | None = None
    container: str | None = None

    eval: bool | None = None
    exec: bool | None = None
    fs: bool | None = None
    web: bool | None = None

    subagents: bool | None = None

    system_prompt: str | None = None
    extra_system_prompt: str | None = None

    in_memory: bool | None = None
    jsonl: bool | None = None
    resume: uuid.UUID | None = None

    ##

    @classmethod
    def configure_argument_parser(cls, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        parser = super().configure_argument_parser(parser)

        parser.add_argument('-C', '--cwd')
        parser.add_argument('--container')

        parser.add_argument('--eval', action='store_true')
        parser.add_argument('--exec', action='store_true')
        parser.add_argument('--fs', action='store_true')
        parser.add_argument('--web', action='store_true')

        parser.add_argument('--subagents', action='store_true')

        parser.add_argument('--system-prompt', metavar='TEXT')
        parser.add_argument('--extra-system-prompt', metavar='TEXT')

        parser.add_argument('--in-memory', action='store_true')
        parser.add_argument('--jsonl', action='store_true')
        parser.add_argument('--resume', type=uuid.UUID, metavar='SESSION_ID')

        return parser

    @classmethod
    def build_kwargs_from_parsed_arguments(cls, args: argparse.Namespace) -> dict[str, ta.Any]:
        return dict(
            **super().build_kwargs_from_parsed_arguments(args),

            cwd=args.cwd,
            container=args.container,

            eval=args.eval,
            exec=args.exec,
            fs=args.fs,
            web=args.web,

            subagents=args.subagents,

            system_prompt=args.system_prompt,
            extra_system_prompt=args.extra_system_prompt,

            in_memory=args.in_memory,
            jsonl=args.jsonl,
            resume=args.resume,
        )
