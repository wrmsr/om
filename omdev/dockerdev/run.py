"""
====

./om dockerdev run -CG \
    --user=0:0 \
    --env=EXTERNAL_UID=1000 \
    --env=EXTERNAL_GID=1000 \
    --env=INTERNAL_USER=om \
    --rm -it bash

====

INTERNAL_UID=$(id -u "$INTERNAL_USER")

if [ "$EXTERNAL_UID" != "$INTERNAL_UID" ]; then
  # 1. Evict any existing user squatting on our target UID
  CONFLICT_USER=$(getent passwd "$EXTERNAL_UID" | cut -d: -f1)
  if [ -n "$CONFLICT_USER" ] && [ "$CONFLICT_USER" != "$INTERNAL_USER" ]; then
      userdel "$CONFLICT_USER"
  fi

  # 2. Ensure the target group exists
  getent group "$EXTERNAL_GID" >/dev/null 2>&1 || groupadd -g "$EXTERNAL_GID" shift-uid

  # 3. DECOY: Temporarily point home dir away to bypass the automatic large chown
  INTERNAL_HOME=$(getent passwd "$INTERNAL_USER" | cut -d: -f6)
  usermod -d /tmp "$INTERNAL_USER"

  # 4. Shift user's primary UID and GID to match the host, keeping original group
  usermod -u "$EXTERNAL_UID" -g "$EXTERNAL_GID" -aG "$INTERNAL_UID" "$INTERNAL_USER"

  # 5. Point the home directory back
  usermod -d "$INTERNAL_HOME" "$INTERNAL_USER"
fi

unset EXTERNAL_UID
unset EXTERNAL_GID
unset INTERNAL_USER

unset INTERNAL_UID
unset INTERNAL_HOME

exec gosu om bash  # "$@"
"""
import abc
import os.path
import platform
import re
import shutil
import sys
import tempfile
import typing as ta
import uuid

from omcore import check
from omcore import dataclasses as dc
from omcore import lang
from omcore import marshal as msh
from omcore.secrets import all as sec
from omcore.shlex import shlex_maybe_quote

from .build import build_image
from .config import Config


with lang.auto_proxy_import(globals()):
    from . import db


##
# Args


@dc.dataclass(frozen=True, kw_only=True)
class RunArgs:
    verbose: bool = False

    mounts: ta.Sequence[str] | None = None
    mount_caches: bool = False
    mount_docker_sock: bool = False
    mount_git: bool = False
    clone_mount_git: bool = False

    privileged: bool = False

    offline: bool = False

    no_host_platform: bool = False

    autoexecs: ta.Sequence[str] | None = None

    x11: bool = False

    id: uuid.UUID | None = None
    no_id_label: bool = False

    # TODO: k=v? currently hardcodes env key as `sk.upper()`
    inject_secrets_pats: ta.Sequence[str | re.Pattern[str]] | None = dc.xfield(
        default=None,
    ) | msh.dc_field_options(
        omit_if=lang.is_none,
        marshal_via=msh.MarshalVia(str | None),
        unmarshal_via=msh.UnmarshalVia(str | None),
    )

    shift_uid: tuple[int, int] | None = None

    unknown_args: ta.Sequence[str] | None = None
    extra_args: ta.Sequence[str] | None = None


ID_LABEL = 'om.dockerdev'

CACHE_VOLUME = 'om-dockerdev-cache'


##
# Host


@dc.dataclass(frozen=True, kw_only=True)
class RunHost:
    """
    What a run reads from the machine it is launched from, gathered in one place so that a run can be planned - and
    tested - without that machine. `RunHost.current()` reads the real one.
    """

    # `platform.system()`.
    platform_system: str

    # `sys.platform`.
    sys_platform: str

    # The user's home directory, if known. Only an x11 run on linux needs it.
    home: str | None = None

    # The working directory, in which a git mount looks for `.git`.
    cwd: str

    # Where secrets to inject come from. Unset, a run which asks to inject any fails rather than reading them from
    # somewhere implicit.
    load_secrets: ta.Callable[[], sec.Secrets] | None = None

    # Makes the host directory staged files are written to. Unset, `tempfile.mkdtemp`.
    mkdtemp: ta.Callable[[], str] | None = None

    @classmethod
    def current(
            cls,
            *,
            load_secrets: ta.Callable[[], sec.Secrets] | None = None,
            mkdtemp: ta.Callable[[], str] | None = None,
    ) -> RunHost:
        return cls(
            platform_system=platform.system(),
            sys_platform=sys.platform,
            home=os.environ.get('HOME'),
            cwd=os.getcwd(),
            load_secrets=load_secrets,
            mkdtemp=mkdtemp,
        )


##
# Plan


# Where the container sees the files a run stages for it.
CONTAINER_STAGING_DIR: ta.Final = '/dockerdev'


class RunPlan:
    """
    What one `docker run` will be, accumulated by the run steps in order: the options before the image, the shell lines
    the autoexec entrypoint runs ahead of the command (and the environment it execs the command with), the entrypoint,
    the files staged for the container, and the environment of the docker client process itself.
    """

    def __init__(
            self,
            *,
            cfg: Config,
            args: RunArgs,
            run_id: uuid.UUID,
            host: RunHost,
    ) -> None:
        super().__init__()

        self._cfg = cfg
        self._args = args
        self._run_id = run_id
        self._host = host

        self._options: list[str] = []
        self._autoexec_lines: list[str] = []
        self._exec_env: dict[str, str] = {}
        self._entrypoint: str | None = None
        self._client_env: dict[str, str | sec.Secret] = {}
        self._staging_dir: str | None = None

    #

    @property
    def cfg(self) -> Config:
        return self._cfg

    @property
    def args(self) -> RunArgs:
        return self._args

    @property
    def run_id(self) -> uuid.UUID:
        return self._run_id

    @property
    def host(self) -> RunHost:
        return self._host

    #

    @property
    def options(self) -> ta.Sequence[str]:
        """The `docker run` options planned so far - everything before the image."""

        return self._options

    def add_options(self, *options: str) -> None:
        self._options.extend(options)

    @property
    def autoexec_lines(self) -> ta.Sequence[str]:
        return self._autoexec_lines

    def add_autoexec_lines(self, *lines: str) -> None:
        self._autoexec_lines.extend(lines)

    @property
    def exec_env(self) -> ta.Mapping[str, str]:
        """Environment the autoexec entrypoint sets for the command alone, once its lines have run."""

        return self._exec_env

    def set_exec_env(self, key: str, value: str) -> None:
        self._exec_env[key] = value

    @property
    def entrypoint(self) -> str | None:
        return self._entrypoint

    def set_entrypoint(self, entrypoint: str) -> None:
        self._entrypoint = entrypoint

    @property
    def client_env(self) -> ta.Mapping[str, str | sec.Secret]:
        """Environment for the docker client process, from which `--env=KEY` options pass values without naming them."""

        return self._client_env

    def set_client_env(self, key: str, value: str | sec.Secret) -> None:
        self._client_env[key] = value

    #

    @property
    def staging_dir(self) -> str | None:
        """The host directory files have been staged in, if any have."""

        return self._staging_dir

    def stage_file(self, name: str, content: str, *, mode: int = 0o755) -> str:
        """Writes a file for the container to see in its staging dir, returning its path there."""

        check.non_empty_str(name)
        check.arg(os.sep not in name and name not in ('.', '..'), name)

        if (staging_dir := self._staging_dir) is None:
            if (mkdtemp := self._host.mkdtemp) is None:
                mkdtemp = tempfile.mkdtemp
            staging_dir = self._staging_dir = mkdtemp()

        path = os.path.join(staging_dir, name)
        with open(path, 'x') as f:
            f.write(content)
        os.chmod(path, mode)  # noqa

        return f'{CONTAINER_STAGING_DIR}/{name}'


##
# Steps


class RunStep(lang.Abstract):
    """
    One concern of a run. Steps are applied to a plan in order, and a later one may build on what an earlier one
    planned: the autoexec entrypoint runs the lines other steps added, shift-uid wraps the entrypoint planned before it,
    and the staging mount follows every step which may stage a file.
    """

    @abc.abstractmethod
    def apply(self, plan: RunPlan) -> None:
        raise NotImplementedError


class BaseOptionsRunStep(RunStep):
    """The options passed through unrecognized from the command line, or else `--rm -it`."""

    # FIXME: any unrecognized option at all drops the defaults, rather than only one which conflicts with them.

    def apply(self, plan: RunPlan) -> None:
        if plan.args.unknown_args:
            plan.add_options(*plan.args.unknown_args)
        else:
            plan.add_options('--rm', '-it')


class PrivilegedRunStep(RunStep):
    def apply(self, plan: RunPlan) -> None:
        if plan.args.privileged:
            plan.add_options('--privileged')


class OfflineRunStep(RunStep):
    def apply(self, plan: RunPlan) -> None:
        if plan.args.offline:
            plan.add_options('--pull=never')


class MountsRunStep(RunStep):
    """The mounts asked for by spec, and the host's docker socket."""

    def apply(self, plan: RunPlan) -> None:
        if plan.args.mounts:
            plan.add_options(*[f'--mount={m}' for m in plan.args.mounts])

        if plan.args.mount_docker_sock:
            plan.add_options('--mount=type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock')


class CacheMountsRunStep(RunStep):
    """
    Mounts the shared cache volume, and has the entrypoint replace each configured cache directory with a symlink into
    it.
    """

    def apply(self, plan: RunPlan) -> None:
        if not (plan.args.mount_caches and (cache_mounts := plan.cfg.cache_mounts)):
            return

        plan.add_options(f'--mount=type=volume,src={CACHE_VOLUME},dst=/cache')
        plan.add_autoexec_lines('sudo chown om:om /cache')

        for cl, cr in cache_mounts.items():
            plan.add_autoexec_lines(
                f'if ! [ -d /cache/{cl} ] ; then mkdir -p /cache/{cl} ; fi',
                f'rm -rf {cr} || true',
                f'ln -s /cache/{cl} {cr}',
            )

            if cr == '/om/.cache/uv':
                # uv cannot hardlink across the volume boundary.
                plan.set_exec_env('UV_LINK_MODE', 'symlink')


class GitMountRunStep(RunStep):
    """Mounts the working directory's `.git` read-only, and optionally has the entrypoint clone a checkout from it."""

    def apply(self, plan: RunPlan) -> None:
        if not (plan.args.mount_git or plan.args.clone_mount_git):
            return

        git_path = os.path.join(plan.host.cwd, '.git')
        check.state(os.path.isdir(git_path))
        plan.add_options(f'--mount=type=bind,src={git_path},dst=/git,ro')

        if plan.args.clone_mount_git:
            plan.add_autoexec_lines(
                'git config --global --add safe.directory /git',
                'git clone -q /git /work/git',
            )


class HostPlatformRunStep(RunStep):
    def apply(self, plan: RunPlan) -> None:
        if not plan.args.no_host_platform:
            plan.add_options(f'--env=DOCKER_HOST_PLATFORM={plan.host.platform_system.lower()}')


class AutoexecRunStep(RunStep):
    """
    Collects the shell lines earlier steps planned, followed by the ones asked for directly, into a staged entrypoint
    script which runs them and then execs the command with the planned exec environment.
    """

    def apply(self, plan: RunPlan) -> None:
        lines = [
            *plan.autoexec_lines,
            *(plan.args.autoexecs or []),
        ]

        if not lines:
            # The exec environment is only ever applied by this script.
            check.empty(plan.exec_env)
            return

        script = '\n'.join([
            '#!/bin/sh',
            'set -e',
            *lines,
            ' '.join([
                *[
                    f'{shlex_maybe_quote(k)}={shlex_maybe_quote(v)}'
                    for k, v in plan.exec_env.items()
                ],
                'exec "$@"',
            ]),
        ])

        plan.set_entrypoint(plan.stage_file('autoexec.sh', script))


class ShiftUidRunStep(RunStep):
    """
    Starts the container as root, in a staged entrypoint script which moves the image's user onto the given host uid
    and gid - so that what it writes to bind mounts belongs to the host user - and then runs the entrypoint planned
    before it as that user.
    """

    def apply(self, plan: RunPlan) -> None:
        if (shift_uid := plan.args.shift_uid) is None:
            return

        uid, gid = shift_uid
        inner_entrypoint = plan.entrypoint

        script_src = lang.get_relative_resources('.resources', globals=globals())['shift-uid.sh'].read_text()
        script = plan.stage_file('shift-uid.sh', script_src)

        plan.add_options('--user=0:0')
        plan.add_options(*[
            f'--env={k}={v}'
            for k, v in {
                'SHIFTUID_EXTERNAL_UID': str(uid),
                'SHIFTUID_EXTERNAL_GID': str(gid),
                'SHIFTUID_INTERNAL_USER': 'om',
                'SHIFTUID_INTERNAL_ENTRYPOINT': inner_entrypoint or '',
            }.items()
        ])

        plan.set_entrypoint(script)


class StagingMountRunStep(RunStep):
    """Mounts the staging dir read-only, if any step staged a file. Applied after every step which may."""

    def apply(self, plan: RunPlan) -> None:
        if (staging_dir := plan.staging_dir) is not None:
            plan.add_options(f'--mount=type=bind,src={staging_dir},dst={CONTAINER_STAGING_DIR},readonly')


class EntrypointRunStep(RunStep):
    """The entrypoint as it stands once every step which may set or wrap it has."""

    def apply(self, plan: RunPlan) -> None:
        if (entrypoint := plan.entrypoint) is not None:
            plan.add_options(f'--entrypoint={entrypoint}')


class X11RunStep(RunStep):
    """Gives the container the host's X display: its socket and auth on linux, Docker Desktop's forwarding on macOS."""

    def apply(self, plan: RunPlan) -> None:
        if not plan.args.x11:
            return

        sys_platform = plan.host.sys_platform

        if sys_platform.startswith('linux'):
            plan.add_options(
                '--env=DISPLAY',
                '--volume=/tmp/.X11-unix:/tmp/.X11-unix:rw',
                f'--volume={check.not_none(plan.host.home)}/.Xauthority:/tmp/.Xauthority:ro',
                '--env=XAUTHORITY=/tmp/.Xauthority',
            )

        elif sys_platform == 'darwin':
            plan.add_options('--env=DISPLAY=host.docker.internal:0')

        else:
            raise OSError(sys_platform)


class IdLabelRunStep(RunStep):
    """Labels the container as a dockerdev one, with its run id - which is how it is found again."""

    def apply(self, plan: RunPlan) -> None:
        if not plan.args.no_id_label:
            plan.add_options(f'--label={ID_LABEL}={plan.run_id}')


class RunSecretsUnavailableError(RuntimeError):
    pass


class SecretsRunStep(RunStep):
    """
    Injects every host secret whose name matches any of the patterns, under its name uppercased. The values go into the
    docker client's environment, and `--env=KEY` passes each through by name, so that none appears in its argv.
    """

    def apply(self, plan: RunPlan) -> None:
        if not (pats := plan.args.inject_secrets_pats):
            return

        if (load_secrets := plan.host.load_secrets) is None:
            raise RunSecretsUnavailableError('Secrets to inject were requested, but no source of secrets was given')

        secrets = check.isinstance(load_secrets(), sec.IterableSecrets)

        compiled = [p if isinstance(p, re.Pattern) else re.compile(p) for p in pats]

        for sk in secrets:
            if any(p.fullmatch(sk) for p in compiled):
                ek = sk.upper()
                plan.set_client_env(ek, secrets.get(sk))
                plan.add_options(f'--env={ek}')


DEFAULT_RUN_STEPS: ta.Sequence[RunStep] = (
    BaseOptionsRunStep(),
    PrivilegedRunStep(),
    OfflineRunStep(),
    MountsRunStep(),
    CacheMountsRunStep(),
    GitMountRunStep(),
    HostPlatformRunStep(),
    AutoexecRunStep(),
    ShiftUidRunStep(),
    StagingMountRunStep(),
    EntrypointRunStep(),
    X11RunStep(),
    IdLabelRunStep(),
    SecretsRunStep(),
)


##
# Processing


@dc.dataclass(frozen=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class ProcessedRunArgs:
    id: uuid.UUID

    args: list[str]

    _: dc.KW_ONLY

    env: dict[str, str | sec.Secret] | None = None


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
    )


def run_image(
        cfg: Config,
        args: RunArgs = RunArgs(),
        sha: str | None = None,
        *,
        host: RunHost | None = None,
        write_to_db: bool = False,
) -> None:
    if sha is None:
        sha = build_image(
            cfg,
            offline=args.offline,
            verbose=args.verbose,
        )

    #

    p_args = process_run_args(
        cfg,
        args,
        sha,
        host=host,
    )

    #

    if write_to_db:
        db.write_run_to_db(
            id=p_args.id,

            cfg=cfg,
            sha=sha,
            args=args,
        )

    #

    os.execle(
        docker := check.not_none(shutil.which('docker')),
        docker,
        'run',
        *p_args.args,
        {
            **os.environ,
            **({
                ek: ev.reveal() if isinstance(ev, sec.Secret) else ev
                for ek, ev in p_args.env.items()
            } if p_args.env else {}),
        },
    )
