import re
import typing as ta

from omcore import dataclasses as dc
from omcore.subprocesses.wrap import subprocess_maybe_shell_wrap_exec

from ..types.options import ProcessOptions
from ..types.specs import ProcessSpec
from .launcher import SpecTransform


##


class ShellWrapTransform(SpecTransform):
    """
    Wraps argv in `sh -c` when a debugger is attached (or forced), so IDE debuggers don't attach to python-looking
    children. See `omcore.subprocesses.wrap`.
    """

    def transform(self, spec: ProcessSpec, options: ProcessOptions) -> ProcessSpec:
        argv = subprocess_maybe_shell_wrap_exec(*spec.argv)
        if tuple(argv) == tuple(spec.argv):
            return spec
        return dc.replace(spec, argv=argv)


##


@dc.dataclass(frozen=True, kw_only=True)
class EnvScrubTransform(SpecTransform):
    """Removes env vars matching any of `remove` (regexes on the name), or keeps only those matching `keep`."""

    remove: ta.Sequence[str] = ()
    keep: ta.Sequence[str] | None = None

    def transform(self, spec: ProcessSpec, options: ProcessOptions) -> ProcessSpec:
        env = spec.resolve_env()
        rm = [re.compile(p) for p in self.remove]
        kp = [re.compile(p) for p in self.keep] if self.keep is not None else None
        out = {
            k: v
            for k, v in env.items()
            if not any(p.fullmatch(k) for p in rm)
            and (kp is None or any(p.fullmatch(k) for p in kp))
        }
        return dc.replace(spec, env=out)
