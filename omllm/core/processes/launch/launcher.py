"""
A `Launcher` turns a `ProcessSpec` (+ options) into what the process spawner is actually asked to run. The only launcher
today is the `ShimLauncher`; remote targets are transforms layered on the same seam.
"""
import abc
import os
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ..types.options import ProcessOptions
from ..types.specs import ProcessSpec


##


class SpecTransform(lang.Abstract):
    """
    A pure `ProcessSpec -> ProcessSpec` rewrite applied before launch (shell wrapping, env scrubbing, sandboxing,
    docker/ssh wrapping, ...).
    """

    @abc.abstractmethod
    def transform(self, spec: ProcessSpec, options: ProcessOptions) -> ProcessSpec:
        raise NotImplementedError


def apply_transforms(
        transforms: ta.Iterable[SpecTransform],
        spec: ProcessSpec,
        options: ProcessOptions,
) -> ProcessSpec:
    for t in transforms:
        spec = t.transform(spec, options)
    return spec


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class LaunchPlan:
    """
    Everything the spawner needs. The contract: the spawner creates an AF_UNIX stream socket pair, queues `send_fds` on
    it (`managers/spawn.py::send_control_fds`), delivers the child end at fd `control_fd` in the child (a dup2 at spawn
    - nothing is made inheritable in the parent), and reads exec status from the parent end until EOF. Owns `owned_fds`
    (created for this launch, e.g. the payload file) - the spawner must close them in the parent after the spawn,
    whether or not it succeeded, via `close()`. (No cwd: the launched program - the shim - changes directory itself.)
    """

    # The spec after transforms - what the target will actually be.
    spec: ProcessSpec

    argv: ta.Sequence[str]
    env: ta.Mapping[str, str]

    # Where the child expects the control socket.
    control_fd: int

    # Fds to send over the control socket before the child runs, in order (owned fds such as the payload blob, then the
    # caller's `PassFd`s).
    send_fds: ta.Sequence[int] = ()

    owned_fds: ta.Sequence[int] = ()

    def close(self) -> None:
        for fd in self.owned_fds:
            try:
                os.close(fd)
            except OSError:
                pass


class Launcher(lang.Abstract):
    @abc.abstractmethod
    def plan(
            self,
            spec: ProcessSpec,
            options: ProcessOptions,
            *,
            child_setsid: bool = False,
    ) -> LaunchPlan:
        """Builds a launch plan; `child_setsid` asks the launched child to create its own session before target exec."""

        raise NotImplementedError
