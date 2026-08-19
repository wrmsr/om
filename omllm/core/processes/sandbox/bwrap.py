"""
Bubblewrap (`bwrap`) confinement backend for Linux. Renders a `SandboxPolicy` into a `bwrap ... -- <cmd>` invocation
that binds only the permitted paths, drops network unless allowed, and dies with its parent. Requires unprivileged user
namespaces to actually run (kernels that disable them will reject the spawn).

Merged-/usr systems: `/bin`, `/sbin`, `/lib`, `/lib64` are symlinks into `/usr` on most current distros. Every path is
bound at its *real* location, and each symlink on the way to it is recreated inside the sandbox (`--symlink`), so that
`/bin/sh` and the ELF interpreter `/lib64/ld-linux-*.so` resolve exactly as on the host. Without that, nothing
dynamically linked can even exec.

Termination: bwrap does not forward signals. Our TERM to the process group reaches the sandboxed command *and* the
outer bwrap, which dies of it - and `--die-with-parent` then SIGKILLs the whole sandbox - so a sandboxed command gets no
real grace period; the manager's escalation still guarantees the sandbox is gone. (A graceful remote stop would need
the in-sandbox pid, the same open item as the docker / ssh targets.)
"""
import os.path
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ..types.options import Sandbox
from ..types.specs import ProcessSpec
from .policy import SandboxPolicy


##


def iter_symlink_prefixes(path: str) -> ta.Iterator[tuple[str, str]]:
    """
    Yields `(link_target, link_path)` for every symlink encountered walking `path` component by component (including
    `path` itself), so a caller can recreate them and have `path` resolve inside a tree that only holds real paths.
    """

    path = os.path.abspath(path)
    cur = ''
    for part in path.split(os.sep):
        if not part:
            continue
        cur = os.path.join(cur or os.sep, part)
        if os.path.islink(cur):
            yield os.readlink(cur), cur


def build_bwrap_argv(
        bwrap: str,
        policy: SandboxPolicy,
        *,
        cwd: str | None = None,
        new_session: bool = False,
) -> list[str]:
    a: list[str] = [
        bwrap,
        '--die-with-parent',
        '--unshare-ipc',
        '--unshare-uts',
        '--unshare-cgroup-try',
        '--unshare-pid',
    ]

    if new_session:
        a.append('--new-session')

    if not policy.allow_network:
        a.append('--unshare-net')

    # Fresh /dev, /proc and /tmp go first: a later mount at a path shadows everything already mounted beneath it, so
    # binds of roots under /tmp must land *inside* the tmpfs, not under it.
    if policy.allow_dev:
        a.extend(['--dev', '/dev'])
    if policy.allow_proc:
        a.extend(['--proc', '/proc'])
    if policy.tmpfs_tmp:
        a.extend(['--tmpfs', '/tmp'])  # noqa: S108

    seen_binds: set[tuple[str, str]] = set()
    seen_links: set[str] = set()

    def _links(path: str) -> None:
        for target, link in iter_symlink_prefixes(path):
            if link not in seen_links:
                seen_links.add(link)
                a.extend(['--symlink', target, link])

    def _bind(flag: str, path: str) -> None:
        rp = os.path.realpath(path)
        if not os.path.exists(rp):
            return
        _links(path)
        if (flag, rp) not in seen_binds:
            seen_binds.add((flag, rp))
            a.extend([flag, rp, rp])

    for d in policy.system_read_roots:
        _bind('--ro-bind', d)
    for r in policy.read_roots:
        _bind('--ro-bind', r)
    for w in policy.write_roots:
        _bind('--bind', w)

    if cwd is not None:
        # The cwd is reachable by its given name once its symlink prefixes exist in the sandbox.
        _links(cwd)
        a.extend(['--chdir', os.path.abspath(cwd)])

    a.append('--')
    return a


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class BwrapSandbox(Sandbox, lang.Final):
    policy: SandboxPolicy

    bwrap: str = 'bwrap'

    # `--new-session`: setsid() inside the sandbox. Off by default: the manager already makes every child a session
    # leader with no controlling terminal (or with our own pty as one, under PtyStdio - which a setsid would detach,
    # breaking job control / `tty`), so there is no user terminal for the sandbox to TIOCSTI into. Turn it on if a
    # sandboxed process is deliberately given the manager's own terminal (SessionMode 'group' + inherited stdio).
    new_session: bool = False

    def transform_spec(self, spec: ProcessSpec) -> ProcessSpec:
        argv = build_bwrap_argv(self.bwrap, self.policy, cwd=spec.cwd, new_session=self.new_session)
        # cwd is applied inside the sandbox via --chdir; the bwrap process itself runs from our cwd.
        return dc.replace(spec, argv=[*argv, *spec.argv], cwd=None)
