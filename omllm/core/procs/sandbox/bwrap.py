"""
Bubblewrap (`bwrap`) confinement backend for Linux. Renders a `SandboxPolicy` into a `bwrap ... -- <cmd>` invocation
that binds only the permitted paths, drops network unless allowed, and dies with its parent. Requires unprivileged
user namespaces to actually run (kernels that disable them will reject the spawn).
"""
import os.path
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ..types.options import Sandbox
from ..types.specs import ProcessSpec
from .policy import SandboxPolicy


##


def build_bwrap_argv(
        bwrap: str,
        policy: SandboxPolicy,
        *,
        cwd: str | None = None,
) -> list[str]:
    a: list[str] = [
        bwrap,
        '--die-with-parent',
        '--unshare-ipc',
        '--unshare-uts',
        '--unshare-cgroup-try',
        '--unshare-pid',
        '--new-session',
    ]

    if not policy.allow_network:
        a += ['--unshare-net']

    def _ro(path: str) -> None:
        rp = os.path.realpath(path)
        if os.path.exists(rp):
            a.extend(['--ro-bind', rp, rp])

    def _rw(path: str) -> None:
        rp = os.path.realpath(path)
        if os.path.exists(rp):
            a.extend(['--bind', rp, rp])

    for d in policy.system_read_roots:
        _ro(d)
    for r in policy.read_roots:
        _ro(r)
    for w in policy.write_roots:
        _rw(w)

    if policy.allow_dev:
        a += ['--dev', '/dev']
    if policy.allow_proc:
        a += ['--proc', '/proc']
    if policy.tmpfs_tmp:
        a += ['--tmpfs', '/tmp']  # noqa: S108

    if cwd is not None:
        a += ['--chdir', os.path.realpath(cwd)]

    a.append('--')
    return a


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class BwrapSandbox(Sandbox, lang.Final):
    policy: SandboxPolicy

    bwrap: str = 'bwrap'

    def transform_spec(self, spec: ProcessSpec) -> ProcessSpec:
        argv = build_bwrap_argv(self.bwrap, self.policy, cwd=spec.cwd)
        # cwd is applied inside the sandbox via --chdir; the bwrap process itself runs from our cwd.
        return dc.replace(spec, argv=[*argv, *spec.argv], cwd=None)
