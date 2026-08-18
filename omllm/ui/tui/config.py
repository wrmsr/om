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
    fs: bool | None = None
    allow_fs_reads: bool | None = None
    web: bool | None = None

    jsonl_storage: bool | None = None

    autoexec: lang.SequenceNotStr[str] | None = None

    stream: bool | None = None

    verbose: bool | None = None


##


def make_config_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument('-m', '--model')

    parser.add_argument('--eval', action='store_true')
    parser.add_argument('--exec', action='store_true')
    parser.add_argument('--fs', action='store_true')
    parser.add_argument('--allow-fs-reads', action='store_true')
    parser.add_argument('--web', action='store_true')

    parser.add_argument('-J', '--jsonl-storage', action='store_true')

    parser.add_argument('-X', '--autoexec', action='append')

    parser.add_argument('-S', '--stream', action='store_true')

    parser.add_argument('-v', '--verbose', action='store_true')

    return parser


def parse_config(argv: lang.SequenceNotStr[str] | None = None) -> Config:
    parser = make_config_parser()

    args = parser.parse_args(argv)

    return Config(
        model=args.model,

        eval=args.eval,
        exec=args.exec,
        fs=args.fs,
        allow_fs_reads=args.allow_fs_reads,
        web=args.web,

        jsonl_storage=args.jsonl_storage,

        autoexec=args.autoexec,

        stream=args.stream,

        verbose=args.verbose,
    )
