"""
TODO:
 - just injectify this thing already
 - async (and/or injectable subproc runner)
"""
import os.path
import shutil
import subprocess
import typing as ta
import uuid

from omcore import check
from omcore import dataclasses as dc
from omcore import lang
from omcore.secrets import all as sec
from omcore.subprocesses.wrap import subprocess_maybe_shell_wrap_exec

from ..build.build import build_image
from ..build.config import Config
from ..utils import BARE_SHA256_PAT
from .args import RunArgs
from .plans import RunHost
from .plans import RunPlan
from .steps import DEFAULT_RUN_STEPS
from .steps import RunStep


with lang.auto_proxy_import(globals()):
    from . import db


##


##
# Processing


@dc.dataclass(frozen=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class ProcessedRunArgs:
    id: uuid.UUID

    args: list[str]

    _: dc.KW_ONLY

    env: dict[str, str | sec.Secret] | None = None

    setup_runs: list[ta.Sequence[str]] | None = None


def process_run_args(
        cfg: Config,
        args: RunArgs,
        sha: str,
        *,
        host: RunHost | None = None,
        steps: ta.Sequence[RunStep] = DEFAULT_RUN_STEPS,
) -> ProcessedRunArgs:
    if host is None:
        host = RunHost.current()

    if (run_id := args.id) is None:
        run_id = uuid.uuid7()

    plan = RunPlan(
        cfg=cfg,
        args=args,
        run_id=run_id,
        host=host,
    )

    for step in steps:
        step.apply(plan)

    return ProcessedRunArgs(
        run_id,
        [
            *plan.options,
            sha,
            *(args.extra_args or ['bash']),
        ],
        env=dict(plan.client_env) or None,
        setup_runs=plan.setup_runs,
    )


def run_image(
        cfg: Config,
        args: RunArgs = RunArgs(),
        sha: str | None = None,
        *,
        host: RunHost | None = None,
        no_db: bool = False,
) -> str:  # | ta.NoReturn
    if sha is None:
        sha = build_image(
            cfg,
            offline=bool(args.offline),
            verbose=bool(args.verbose),
        )

    #

    p_args = process_run_args(
        cfg,
        args,
        sha,
        host=host,
    )

    #

    if not no_db:
        db.write_run_to_db(
            id=p_args.id,

            cfg=cfg,
            sha=sha,
            args=args,
        )

    #

    docker = check.not_none(shutil.which('docker'))

    env = {
        **os.environ,
        **({
            ek: ev.reveal() if isinstance(ev, sec.Secret) else ev
            for ek, ev in p_args.env.items()
        } if p_args.env else {}),
    }

    for setup_run in p_args.setup_runs or []:
        raise NotImplementedError  # noqa

    exec_args = [
        docker,
        'run',
        *p_args.args,
    ]

    if not args.detach:
        os.execle(
            docker,
            *exec_args,
            env,
        )

        raise RuntimeError('unreachable')  # noqa

    out = subprocess.check_output(
        subprocess_maybe_shell_wrap_exec(*exec_args),
        stderr=subprocess.PIPE,
    )

    container_id = out.decode().strip()
    check.not_none(BARE_SHA256_PAT.fullmatch(container_id))
    return container_id
