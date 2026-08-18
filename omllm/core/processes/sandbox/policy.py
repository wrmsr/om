"""
A backend-neutral confinement policy: which paths the process may read and write, and whether it gets network. The
bubblewrap and sandbox-exec backends each render this into their own form.
"""
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang


##


# Read-only system locations a typical dynamically-linked command needs to find its executable and libraries.
# Non-existent ones are skipped at render time.
DEFAULT_SYSTEM_READ_ROOTS: ta.Final[ta.Sequence[str]] = (
    '/usr',
    '/bin',
    '/sbin',
    '/lib',
    '/lib64',
    '/etc',
    '/opt',
    '/System/Library',  # macOS
    '/private/var/select',  # macOS
)


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class SandboxPolicy:
    # Directories the process may read (recursively). System roots are added separately.
    read_roots: ta.Sequence[str] = dc.xfield(default=(), coerce=tuple)

    # Directories the process may read and write (recursively).
    write_roots: ta.Sequence[str] = dc.xfield(default=(), coerce=tuple)

    # Read-only system locations (libs / binaries). Missing paths are skipped.
    system_read_roots: ta.Sequence[str] = dc.xfield(default=DEFAULT_SYSTEM_READ_ROOTS, coerce=tuple)

    allow_network: bool = False

    # Expose a minimal /dev (null, zero, urandom, tty, ...) and /proc.
    allow_dev: bool = True
    allow_proc: bool = True

    # Mount a fresh tmpfs at /tmp (writable scratch that vanishes with the sandbox).
    tmpfs_tmp: bool = True

    def __post_init__(self) -> None:
        for r in (*self.read_roots, *self.write_roots, *self.system_read_roots):
            check.non_empty_str(r)
