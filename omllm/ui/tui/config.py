from omcore import dataclasses as dc
from omcore import lang


with lang.auto_proxy_import(globals()):
    import argparse


##


@dc.dataclass(frozen=True, kw_only=True)
class Config:
    model: str | None = None

    cwd: str | None = None

    eval: bool | None = None
    exec: bool | None = None
    allow_ripgrep_execs: bool | None = None
    fs: bool | None = None
    allow_fs_reads: bool | None = None
    web: bool | None = None

    jsonl_storage: bool | None = None

    autoexec: lang.SequenceNotStr[str] | None = None

    immediate: bool | None = None

    verbose: bool | None = None


##


def configure_argument_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument('-m', '--model')

    parser.add_argument('--eval', action='store_true')
    parser.add_argument('--exec', action='store_true')
    parser.add_argument('--allow-ripgrep-execs', action='store_true')
    parser.add_argument('--fs', action='store_true')
    parser.add_argument('--allow-fs-reads', action='store_true')
    parser.add_argument('--web', action='store_true')

    parser.add_argument('-J', '--jsonl-storage', action='store_true')

    parser.add_argument('-X', '--autoexec', action='append')

    parser.add_argument('-I', '--immediate', action='store_true')

    parser.add_argument('-v', '--verbose', action='store_true')

    return parser


def build_config_from_args(args: argparse.Namespace) -> Config:
    return Config(
        model=args.model,

        eval=args.eval,
        exec=args.exec,
        allow_ripgrep_execs=args.allow_ripgrep_execs,
        fs=args.fs,
        allow_fs_reads=args.allow_fs_reads,
        web=args.web,

        jsonl_storage=args.jsonl_storage,

        autoexec=args.autoexec,

        immediate=args.immediate,

        verbose=args.verbose,
    )


##


def parse_config(argv: lang.SequenceNotStr[str] | None = None) -> Config:
    parser = argparse.ArgumentParser()
    configure_argument_parser(parser)
    args = parser.parse_args(argv)
    return build_config_from_args(args)
