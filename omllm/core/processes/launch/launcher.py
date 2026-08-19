"""
A `Launcher` turns a `ProcessSpec` (+ options) into what `subprocess.Popen` is actually asked to run. The only launcher
today is the `ShimLauncher`; remote targets will be further launchers/transforms layered on the same seam.
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
    Everything the spawner needs. Owns `owned_fds` (created for this launch, e.g. the payload file) - the spawner must
    close them in the parent after the spawn, whether or not it succeeded, via `close()`. (No cwd: the launched program
    - the shim - changes directory itself.)
    """

    # The spec after transforms - what the target will actually be.
    spec: ProcessSpec

    argv: ta.Sequence[str]
    env: ta.Mapping[str, str]

    # Extra fds the spawner must pass through (owned fds plus caller `PassFd`s and the status fd).
    pass_fds: ta.Sequence[int] = ()

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
            status_fd: int,
    ) -> LaunchPlan:
        """`status_fd` is the write end of the exec-status pipe, already created by the caller."""

        raise NotImplementedError
