"""
Run a process on a remote host via `ssh`. Like `DockerExecTarget`, this is a `Target`: it rewrites the spec into the
local `ssh ... host <remote-command>` invocation, which the manager spawns and streams as an ordinary local process.

Unlike `docker exec` (which takes an argv vector after `--`), ssh runs a *command string* through the remote login
shell, so the remote argv (and its cwd/env) are shell-quoted into a single string here. `ControlMaster` connection
sharing is enabled when `control_path` is set, so many execs to the same host reuse one connection.

Same caveat as docker: terminating the handle kills the local `ssh` client; without a remote tty (`PtyStdio` -> `-tt`)
the remote command may outlive it. A robust remote stop is future work on the Target.
"""
import shlex
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang

from ..types.options import Target
from ..types.specs import ProcessSpec
from ..types.specs import PtyStdio


##


def build_remote_command(spec: ProcessSpec) -> str:
    """The single shell command string ssh runs on the remote host: optional `cd`, optional `env`, then `exec`."""

    prefix = ''
    if spec.cwd is not None:
        prefix = f'cd {shlex.quote(spec.cwd)} && '

    cmd_parts: list[str] = []
    if spec.env:
        cmd_parts.append('env')
        cmd_parts.extend(f'{k}={shlex.quote(v)}' for k, v in spec.env.items())
    cmd_parts.extend(shlex.quote(a) for a in spec.argv)

    return f'{prefix}exec {" ".join(cmd_parts)}'


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class SshTarget(Target, lang.Final):
    host: str = dc.xfield(coerce=check.non_empty_str)

    user: str | None = None
    port: int | None = None
    identity_file: str | None = None

    # When set, enables ControlMaster connection sharing over this socket path (many execs reuse one connection).
    control_path: str | None = None
    control_persist: str = '60s'

    # Disable host-key checking (for ephemeral / throwaway hosts). None leaves ssh defaults.
    no_host_key_checking: bool = False

    # Raw extra ssh args (e.g. ('-o', 'ServerAliveInterval=15')).
    extra_options: ta.Sequence[str] = ()

    ssh: str = 'ssh'

    def transform_spec(self, spec: ProcessSpec) -> ProcessSpec:
        argv: list[str] = [self.ssh]

        if self.port is not None:
            argv.extend(['-p', str(self.port)])
        if self.identity_file is not None:
            argv.extend(['-i', self.identity_file])

        if isinstance(spec.stdio, PtyStdio):
            # -tt forces a remote tty even though our stdin is a (pty) device rather than the user's terminal.
            argv.append('-tt')

        if self.control_path is not None:
            argv.extend([
                '-o', 'ControlMaster=auto',
                '-o', f'ControlPath={self.control_path}',
                '-o', f'ControlPersist={self.control_persist}',
            ])

        if self.no_host_key_checking:
            argv.extend([
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
            ])

        argv.extend(self.extra_options)

        argv.append(f'{self.user}@{self.host}' if self.user is not None else self.host)
        argv.append(build_remote_command(spec))

        # cwd/env were folded into the remote command; the local ssh client runs anywhere and inherits the host env (ssh
        # config, agent, ...).
        return dc.replace(spec, argv=argv, cwd=None, env=None)
