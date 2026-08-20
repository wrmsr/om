"""
A backend-neutral confinement policy: which paths the process may read and write, whether it gets network, and what it
may exec and spawn. The bubblewrap and sandbox-exec backends each render this into their own form; capabilities a
backend cannot express are documented per-field and ignored there rather than silently approximated.

The defaults are meant to be safe for a single-purpose tool: exec of only its own binary, no children, no mach services,
a narrow sysctl set, a minimal /dev, a private tmp, no network. Anything looser is an explicit opt-in at the call site,
where the reviewer can see it.
"""
import os.path
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang


# What the confined process may exec: only its own argv[0] ('self', the default), an explicit set of binaries, or
# anything it can read ('any').
type SandboxExecPaths = ta.Literal['self', 'any'] | ta.Sequence[str]

# What of /dev is exposed. 'minimal': null (rw) and zero / random / urandom (ro) - under bwrap this is its own fresh
# minimal /dev. 'all': the host's /dev, read-write - almost never right: among much else it holds every other same-uid
# session's ttys. 'none': nothing.
type SandboxDevAccess = ta.Literal['none', 'minimal', 'all']


##


class SandboxDefaults(lang.Namespace):
    # Read-only system locations a typical dynamically-linked command needs to find its executable and libraries.
    # Non-existent ones are skipped at render time.
    SYSTEM_READ_ROOTS: ta.Final[ta.Sequence[str]] = (
        '/usr',
        '/bin',
        '/sbin',
        '/lib',
        '/lib64',
        '/etc',
        '/opt',
        '/System/Library',  # macOS
        '/System/Volumes/Preboot/Cryptexes/OS',  # macOS: home of the dyld shared cache on current versions
        '/private/var/select',  # macOS: /var/select/sh &c
    )

    # A much smaller set for tools that only need to load their own dynamic libraries: no shells, no /etc, no
    # package-manager prefixes. Missing paths are skipped at render time, so the union covers both platforms. Callers
    # add their binary's own prefix (eg its homebrew keg's lib trees) themselves.
    MINIMAL_SYSTEM_READ_ROOTS: ta.Final[ta.Sequence[str]] = (
        # Linux
        '/lib',
        '/lib64',
        '/usr/lib',
        '/usr/lib64',

        # macOS
        '/System/Library',
        '/System/Volumes/Preboot/Cryptexes/OS',
        '/private/var/db/dyld',  # dyld caches on older versions
    )

    # Sysctl names (and '.'-terminated prefixes) that common runtimes read at startup: cpu counts and feature flags,
    # page and memory sizes, os version. Deliberately narrow - unscoped sysctl-read also answers KERN_PROCARGS2, ie the
    # argv *and environment* of every other same-uid process on the machine.
    SYSCTL_READ_NAMES: ta.Final[ta.Sequence[str]] = (
        'hw.activecpu',
        'hw.cpufamily',
        'hw.cpusubtype',
        'hw.cputype',
        'hw.logicalcpu',
        'hw.logicalcpu_max',
        'hw.memsize',
        'hw.ncpu',
        'hw.optional.',  # arm feature flags (hw.optional.neon, ...)
        'hw.pagesize',
        'hw.pagesize_compat',
        'hw.physicalcpu',
        'hw.physicalcpu_max',
        'kern.osproductversion',
        'kern.osrelease',
        'kern.osvariant_status',
        'kern.osversion',
        'kern.version',
        'machdep.cpu.',  # x86 feature flags
        'sysctl.proc_translated',  # rosetta check
    )


##


def _coerce_exec_paths(v: SandboxExecPaths) -> SandboxExecPaths:
    return v if isinstance(v, str) else tuple(v)


def _coerce_opt_names(v: ta.Literal['any'] | ta.Sequence[str] | None) -> ta.Literal['any'] | ta.Sequence[str] | None:
    return v if v is None or isinstance(v, str) else tuple(v)


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class SandboxPolicy:
    # Directories the process may read (recursively). System roots are added separately.
    read_roots: ta.Sequence[str] = dc.xfield(default=(), coerce=tuple)

    # Directories the process may read and write (recursively).
    write_roots: ta.Sequence[str] = dc.xfield(default=(), coerce=tuple)

    # Read-only system locations (libs / binaries). Missing paths are skipped.
    system_read_roots: ta.Sequence[str] = dc.xfield(default=SandboxDefaults.SYSTEM_READ_ROOTS, coerce=tuple)

    #

    # Binaries the process may exec. Seatbelt enforces this exactly ('self' resolves to the spawned argv[0], which must
    # then be absolute); bubblewrap can only approximate it through what happens to be bound, which with any
    # system_read_roots is far looser - real parity there needs seccomp, an open item.
    exec_paths: SandboxExecPaths = dc.xfield(default='self', coerce=_coerce_exec_paths)

    # Whether the process may fork / posix_spawn children at all. Most single-purpose tools never do (threads are not
    # forks). Seatbelt-enforced; inexpressible in bubblewrap.
    allow_fork: bool = False

    # macOS only: mach services reachable by name. None (the default) denies all lookups - unscoped mach-lookup is the
    # classic seatbelt escape surface, and plain CLI tools degrade gracefully without it. A sequence allows exactly
    # those global names; 'any' is unrestricted.
    mach_lookup: ta.Literal['any'] | ta.Sequence[str] | None = dc.xfield(default=None, coerce=_coerce_opt_names)

    # macOS only: readable sysctls, as exact names or '.'-terminated prefixes. 'any' is unrestricted - which includes
    # other same-uid processes' argv / env via KERN_PROCARGS2, so keep it scoped.
    sysctl_names: ta.Literal['any'] | ta.Sequence[str] = dc.xfield(
        default=SandboxDefaults.SYSCTL_READ_NAMES,
        coerce=_coerce_opt_names,
    )

    #

    allow_network: bool = False

    # See SandboxDevAccess.
    dev: SandboxDevAccess = 'minimal'

    # Expose /proc (bwrap only; pid-namespaced, so it shows only the sandbox's own processes).
    allow_proc: bool = True

    # Private writable scratch that dies with the sandbox: a fresh tmpfs at /tmp under bwrap; under seatbelt a fresh
    # per-spawn directory exported as TMPDIR (macOS's periodic per-user temp cleanup reaps it - scope-tied removal is an
    # open item). Never the shared host /tmp, on either backend.
    private_tmp: bool = True

    def __post_init__(self) -> None:
        for r in (*self.read_roots, *self.write_roots, *self.system_read_roots):
            check.non_empty_str(r)
            check.arg(os.path.isabs(r), f'sandbox roots must be absolute: {r!r}')

        if isinstance(self.exec_paths, str):
            check.arg(self.exec_paths in ('self', 'any'))
        else:
            for p in self.exec_paths:
                check.non_empty_str(p)
                check.arg(os.path.isabs(p), f'exec paths must be absolute: {p!r}')

        if isinstance(self.mach_lookup, str):
            check.arg(self.mach_lookup == 'any')
        elif self.mach_lookup is not None:
            for n in self.mach_lookup:
                check.non_empty_str(n)

        if isinstance(self.sysctl_names, str):
            check.arg(self.sysctl_names == 'any')
        else:
            for n in self.sysctl_names:
                check.non_empty_str(n)

        check.arg(self.dev in ('none', 'minimal', 'all'))
