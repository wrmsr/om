"""
Run a process inside an already-running docker container via `docker exec`. This is a `Target`: it rewrites the spec
into the local `docker exec ...` command, which the manager then spawns and streams as an ordinary local process.

The spec's `cwd` and `env` are interpreted container-side (`-w` / `-e`); the local docker client itself inherits the
host environment (it needs PATH / DOCKER_HOST to reach the daemon). A `PtyStdio` spec adds `-t` so the container
process gets a real tty.

Caveat: terminating the process handle kills the local `docker exec` *client*; depending on the daemon the process
inside the container may keep running. A reliable remote stop needs the in-container pid (a `docker exec <c> kill`,
or the future in-container agent) - not yet implemented here.
"""
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang

from ..types.options import Target
from ..types.specs import ProcessSpec
from ..types.specs import PtyStdio


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class DockerExecTarget(Target, lang.Final):
    # Container name or id to exec into.
    container: str = dc.xfield(coerce=check.non_empty_str)

    # User (or user:group / uid) to run as inside the container.
    user: str | None = None

    # Extra raw flags inserted after `docker exec` (e.g. ('--privileged',)).
    extra_flags: ta.Sequence[str] = ()

    # The docker executable (name resolved on PATH, or an absolute path).
    docker: str = 'docker'

    def transform_spec(self, spec: ProcessSpec) -> ProcessSpec:
        argv: list[str] = [self.docker, 'exec', '-i']

        if isinstance(spec.stdio, PtyStdio):
            argv.append('-t')

        argv.extend(self.extra_flags)

        if spec.cwd is not None:
            argv += ['-w', spec.cwd]

        if self.user is not None:
            argv += ['-u', self.user]

        # Only explicitly-set container env is forwarded (spec.env is None -> inherit the container's own env).
        for k, v in (spec.env or {}).items():
            argv += ['-e', f'{k}={v}']

        argv += [self.container, '--', *spec.argv]

        # The local docker client runs anywhere and inherits the host env (env=None); the container-side cwd/env were
        # consumed into flags above.
        return dc.replace(spec, argv=argv, cwd=None, env=None)
