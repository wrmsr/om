"""
====

if [ -t 1 ] ; then TTY_ENV_ARGS="-e LINES=$(tput lines) -e COLUMNS=$(tput cols)" ; fi
--detach-keys 'ctrl-o,ctrl-d' \

====

tag = f'om-dockerdev--{time.time_ns()}--{os.getpid()}'
subprocess.check_call(['docker', 'tag', obi, tag])
try:
    cfg = dc.replace(cfg, base_image=tag)  # noqa
    ...
finally:
    subprocess.check_call(['docker', 'image', 'rm', tag], stdout=subprocess.DEVNULL)
"""
import os
import re
import subprocess
import sys
import tomllib
import typing as ta

from omcore import check
from omcore import lang
from omcore import marshal as msh
from omcore.argparse import all as ap
from omcore.docker.ps import DEFAULT_PS_FORMAT_STR
from omcore.formats.json import all as json

from ..home.secrets import load_secrets
from .build.build import build_image
from .build.config import Config
from .build.gen import gen_src
from .run.run import ID_LABEL
from .run.run import RunArgs
from .run.run import RunHost
from .run.run import run_image


##


class Cli(ap.Cli):
    def _load_config(self) -> Config:
        cfg_src = lang.get_relative_resources('build', globals=globals())['config.toml'].read_text()
        cfg_dct = tomllib.loads(cfg_src)
        return msh.unmarshal(cfg_dct, Config)

    @ap.cmd()
    def gen(self) -> None:
        cfg = self._load_config()
        src = gen_src(cfg)
        print(src)

    #

    _SHIFT_UID_ARGS: ta.ClassVar = (
        ap.arg('--shift-uid'),
        ap.arg('-U', '--auto-shift-uid', action='store_true'),
    )

    class _ShiftUid(ta.NamedTuple):
        uid: int
        gid: int

    def _get_args_shift_uid(self) -> _ShiftUid | None:
        if (su := self.args.shift_uid) is not None:
            check.arg(not self.args.auto_shift_uid)
            return Cli._ShiftUid(*map(int, su.split(':')))

        if self.args.auto_shift_uid:
            if sys.platform == 'linux':
                return Cli._ShiftUid(os.getuid(), os.getgid())

        return None

    #

    @ap.cmd(
        ap.arg('-v', '--verbose', action='store_true'),

        ap.arg('-O', '--offline', action='store_true'),
    )
    def build(self) -> None:
        sha = build_image(
            self._load_config(),

            offline=bool(self.args.offline),

            verbose=bool(self.args.verbose),
        )

        print(sha)

    def _build_run_args(self) -> RunArgs:
        # The command starts at the first argument which is not an option, or after a `--` ending the options - which
        # argparse leaves at the head of the remainder, and is dropped here. A later `--` belongs to the command.
        extra_args = list(self.args.args or [])
        if extra_args[:1] == ['--']:
            extra_args = extra_args[1:]

        return RunArgs(
            names=self.args.name,

            verbose=bool(self.args.verbose),

            no_rm=bool(self.args.no_rm),
            no_interactive=bool(self.args.no_interactive),
            no_tty=bool(self.args.no_tty),

            detach=bool(self.args.detach),

            mounts=self.args.mount,
            mount_caches=bool(self.args.mount_caches),
            mount_docker_sock=bool(self.args.mount_docker_sock),
            mount_git=bool(self.args.mount_git),
            clone_mount_git=bool(self.args.clone_mount_git),

            privileged=bool(self.args.privileged),

            cuda=bool(self.args.cuda),

            offline=bool(self.args.offline),

            no_host_platform=bool(self.args.no_host_platform),

            autoexecs=self.args.autoexec,

            x11=bool(self.args.x11),

            env_secrets=[s.split('=') if '=' in s else s for s in self.args.env_secret or []],
            env_secret_pats=[re.compile(p) for p in self.args.env_secret_pat or []],

            shift_uid=self._get_args_shift_uid(),

            unknown_args=self.unknown_args or None,
            extra_args=extra_args or None,
        )

    @ap.cmd(
        ap.arg('-n', '--name', action='append'),

        ap.arg('-v', '--verbose', action='store_true'),

        ap.arg('--no-rm', action='store_true'),
        ap.arg('--no-interactive', action='store_true'),
        ap.arg('--no-tty', action='store_true'),

        ap.arg('-d', '--detach', action='store_true'),

        ap.arg('--mount', action='append'),
        ap.arg('-C', '--mount-caches', action='store_true'),
        ap.arg('-D', '--mount-docker-sock', action='store_true'),
        ap.arg('--mount-git', action='store_true'),
        ap.arg('-G', '--clone-mount-git', action='store_true'),

        ap.arg('-P', '--privileged', action='store_true'),

        ap.arg('--cuda', action='store_true'),

        ap.arg('-O', '--offline', action='store_true'),

        ap.arg('--no-host-platform', action='store_true'),

        ap.arg('-x', '--autoexec', action='append'),

        ap.arg('-X', '--x11', action='store_true'),

        ap.arg('--env-secret', action='append'),
        ap.arg('--env-secret-pat', action='append'),

        *_SHIFT_UID_ARGS,

        ap.arg('--no-db', action='store_true'),

        ap.arg('args', nargs=ap.REMAINDER),
        accepts_unknown=True,
    )
    def run(self) -> None:
        container_id = run_image(
            self._load_config(),

            self._build_run_args(),

            host=RunHost.current(
                load_secrets=load_secrets,
            ),

            no_db=bool(self.args.no_db),
        )

        print(container_id)

    #

    @ap.cmd(
        ap.arg('-j', '--json', action='store_true'),
        ap.arg('-H', '--no-header', action='store_true'),
        ap.arg('-I', '--id-only', action='store_true'),

        ap.arg('args', nargs=ap.REMAINDER),
        accepts_unknown=True,
    )
    def ps(self) -> None:
        out = subprocess.check_output([
            'docker',
            'ps',
            *(self.unknown_args or []),
            f'--filter=label={ID_LABEL}',
            *(
                ['--format={{.ID}}'] if self.args.id_only else
                ['--format=json'] if self.args.json else
                [f'--format={DEFAULT_PS_FORMAT_STR}'] if self.args.no_header else
                []
            ),
            *(self.args.args or []),
        ]).decode().strip()

        if self.args.id_only and self.args.json:
            out = json.dumps_compact([sl for l in out.splitlines() if (sl := l.strip())])

        print(out)

    #

    @ap.cmd(
        ap.arg('container-id'),
        ap.arg('secret', nargs='+'),
        ap.arg('-f', '--secrets-file'),

        *_SHIFT_UID_ARGS,
    )
    def inject_secret(self) -> None:
        secrets: list[str | tuple[str, str]] = []
        for s in self.args.secret:
            if '=' in s:
                k, v = s.split('=')
                secrets.append((k, v))
            else:
                secrets.append(s)

        #

        from .run.secrets import inject_dockerdev_secrets

        inject_dockerdev_secrets(
            self.args.container_id,
            secrets,
            secrets_file=self.args.secrets_file,
            shift_uid=self._get_args_shift_uid(),
        )


def _main() -> None:
    Cli().cli_run_and_exit()


if __name__ == '__main__':
    _main()
