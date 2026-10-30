import abc
import os.path
import typing as ta

from omcore import check
from omcore import lang
from omcore.secrets import all as sec
from omcore.shlex import shlex_maybe_quote

from .consts import CACHE_DIR
from .consts import CACHE_VOLUME
from .consts import CONTAINER_STAGING_DIR
from .consts import ID_LABEL
from .consts import PERSIST_DIR
from .consts import PERSIST_VOLUME
from .plans import RunPlan


##


class RunStep(lang.Abstract):
    """
    One concern of a run. Steps are applied to a plan in order, and a later one may build on what an earlier one
    planned: the autoexec entrypoint runs the lines other steps added, shift-uid wraps the entrypoint planned before it,
    and the staging mount follows every step which may stage a file.
    """

    @abc.abstractmethod
    def apply(self, plan: RunPlan) -> None:
        raise NotImplementedError


class NameRunStep(RunStep):
    def apply(self, plan: RunPlan) -> None:
        for name in plan.args.names or []:
            plan.add_options(f'--name={name}')


class BaseOptionsRunStep(RunStep):
    """
    `--rm`, `-i` and `-t` unless each is disabled, `-d` if asked for, and the options passed through unrecognized from
    the command line. Detaching disables neither of the others: a tty is what keeps a detached `bash` waiting rather
    than exiting at the end of an empty stdin, and `-i` is what lets a later `docker attach` type into it.
    """

    def apply(self, plan: RunPlan) -> None:
        if not plan.args.no_rm:
            plan.add_options('--rm')
        if not plan.args.no_interactive:
            plan.add_options('-i')
        if not plan.args.no_tty:
            plan.add_options('-t')

        if plan.args.detach:
            plan.add_options('-d')

        if plan.args.unknown_args:
            plan.add_options(*plan.args.unknown_args)


class PrivilegedRunStep(RunStep):
    def apply(self, plan: RunPlan) -> None:
        if plan.args.privileged:
            plan.add_options('--privileged')


class CudaRunStep(RunStep):
    """Every host gpu, through the nvidia container runtime."""

    def apply(self, plan: RunPlan) -> None:
        if plan.args.cuda:
            plan.add_options('--runtime=nvidia', '--gpus=all')


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


class CacheMountRunStep(RunStep):
    """
    Mounts the shared cache volume, and has the entrypoint replace each configured cache directory with a symlink into
    it.
    """

    def apply(self, plan: RunPlan) -> None:
        if not (plan.args.mount_cache and (cache_mounts := plan.cfg.cache_mounts)):
            return

        plan.add_options(f'--mount=type=volume,src={CACHE_VOLUME},dst={CACHE_DIR}')
        plan.add_autoexec_lines(f'sudo chown om:om {CACHE_DIR}')

        for cl, cr in cache_mounts.items():
            plan.add_autoexec_lines(
                f'if ! [ -d {CACHE_DIR}/{cl} ] ; then mkdir -p {CACHE_DIR}/{cl} ; fi',
                f'rm -rf {cr} || true',
                f'ln -s {CACHE_DIR}/{cl} {cr}',
            )

            if cr == '/om/.cache/uv':
                # uv cannot hardlink across the volume boundary.
                plan.add_options(f'--env=UV_LINK_MODE=symlink')


class PersistMountRunStep(RunStep):
    def apply(self, plan: RunPlan) -> None:
        if not plan.args.mount_persist:
            pass

        plan.add_setup_run([
            '-it',
            '--rm',
            f'--mount=type=volume,src={PERSIST_VOLUME},dst={PERSIST_DIR}',
            check.not_none(plan.cfg.base_image_id),  # FIXME: :|
            'bash', '-c', f'mkdir -p /persist/runs/{str(plan.run_id)}',
        ])

        plan.add_options((
            f'--mount='
            f'type=volume,'
            f'src={PERSIST_VOLUME},'
            f'dst={PERSIST_DIR},'
            f'volume-subpath=runs/{str(plan.run_id)}'
        ))
        plan.add_autoexec_lines(f'sudo chown om:om {PERSIST_DIR}')


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
            return

        script = '\n'.join([
            '#!/bin/sh',
            'set -e',
            *lines,
            ' '.join([
                *[
                    f'{shlex_maybe_quote(k)}={shlex_maybe_quote(v)}'
                    for k, v in plan.autoexec_env.items()
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

        script_src = lang.get_relative_resources('..build.resources', globals=globals())['shift-uid.sh'].read_text()
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
    Adds every host secret whose name matches any of the patterns, under its name uppercased. The values go into the
    docker client's environment, and `--env=KEY` passes each through by name, so that none appears in its argv.
    """

    def apply(self, plan: RunPlan) -> None:
        env_secrets = plan.args.env_secrets
        env_secret_pats = plan.args.env_secret_pats
        if not (env_secrets or env_secret_pats):
            return

        #

        if (load_secrets := plan.host.load_secrets) is None:
            raise RunSecretsUnavailableError('Secrets to inject were requested, but no source of secrets was given')

        secrets = check.isinstance(load_secrets(), sec.IterableSecrets)

        #

        env_keys: dict[str, None] = {}

        def add(ek: str, sv: sec.Secret) -> None:
            plan.set_client_env(ek, sv)
            if ek not in env_keys:
                plan.add_options(f'--env={ek}')
                env_keys[ek] = None

        if env_secret_pats:
            for sk in secrets:
                if any(p.fullmatch(sk) for p in env_secret_pats):
                    add(sk.upper(), secrets.get(sk))

        for es in env_secrets or []:
            if isinstance(es, tuple):
                ek, sk = es
            else:
                ek, sk = es.upper(), es.lower()
            if (sv := secrets.try_get(sk)) is not None:
                add(ek, sv)
            elif not plan.args.non_strict_env_secrets:
                raise RunSecretsUnavailableError(sk)


DEFAULT_RUN_STEPS: ta.Sequence[RunStep] = (
    NameRunStep(),
    BaseOptionsRunStep(),
    PrivilegedRunStep(),
    CudaRunStep(),
    OfflineRunStep(),
    MountsRunStep(),
    CacheMountRunStep(),
    PersistMountRunStep(),
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
