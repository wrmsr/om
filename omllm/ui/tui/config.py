import os.path
import typing as ta
import uuid

from omcore import check
from omcore import dataclasses as dc
from omcore import lang
from omcore import typedvalues as tv


with lang.auto_proxy_import(globals()):
    import argparse


##


class TargetCwd(tv.UniqueScalarTypedValue[str], final=True):
    def __post_init__(self) -> None:
        check.non_empty_str(self.v)
        check.arg(os.path.isabs(self.v))


@dc.dataclass(frozen=True, kw_only=True)
class Config:
    model: str | None = None

    cwd: str | None = None
    container: str | None = None

    eval: bool | None = None
    exec: bool | None = None
    allow_ripgrep_execs: bool | None = None
    fs: bool | None = None
    allow_fs_reads: bool | None = None
    web: bool | None = None

    url: str | None = None
    backend_model_id: str | None = None

    in_memory: bool | None = None
    jsonl: bool | None = None
    resume: uuid.UUID | None = None

    autoexec: lang.SequenceNotStr[str] | None = None

    immediate: bool | None = None

    verbose: bool | None = None
    yolo: bool | None = None

    ##

    @classmethod
    def configure_argument_parser(cls, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        parser.add_argument('-m', '--model')

        parser.add_argument('-C', '--cwd')
        parser.add_argument('--container')

        parser.add_argument('--eval', action='store_true')
        parser.add_argument('--exec', action='store_true')
        parser.add_argument('--allow-ripgrep-execs', action='store_true')
        parser.add_argument('--fs', action='store_true')
        parser.add_argument('--allow-fs-reads', action='store_true')
        parser.add_argument('--web', action='store_true')

        parser.add_argument('--url')
        parser.add_argument('--backend-model-id')

        parser.add_argument('--in-memory', action='store_true')
        parser.add_argument('--jsonl', action='store_true')
        parser.add_argument('--resume', type=uuid.UUID, metavar='SESSION_ID')

        parser.add_argument('-X', '--autoexec', action='append')

        parser.add_argument('-I', '--immediate', action='store_true')

        parser.add_argument('-v', '--verbose', action='store_true')
        parser.add_argument('--yolo', action='store_true')

        return parser

    @classmethod
    def build_kwargs_from_parsed_arguments(cls, args: argparse.Namespace) -> dict[str, ta.Any]:
        return dict(
            model=args.model,

            cwd=args.cwd,
            container=args.container,

            eval=args.eval,
            exec=args.exec,
            allow_ripgrep_execs=args.allow_ripgrep_execs,
            fs=args.fs,
            allow_fs_reads=args.allow_fs_reads,
            web=args.web,

            url=args.url,
            backend_model_id=args.backend_model_id,

            in_memory=args.in_memory,
            jsonl=args.jsonl,
            resume=args.resume,

            autoexec=args.autoexec,

            immediate=args.immediate,

            verbose=args.verbose,
            yolo=args.yolo,
        )

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
