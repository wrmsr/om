"""
macOS `sandbox-exec` confinement backend. Renders a `SandboxPolicy` into a Scheme-ish sandbox profile that denies by
default and allows only what the policy names: reads / writes under the permitted subpaths, exec of only the permitted
binaries, and narrowly scoped metadata / sysctl / dev access. Cannot be exercised off macOS; kept structurally simple.

How seatbelt actually evaluates things, which shapes this renderer:

- Matching is against *resolved* vnode paths, so every granted path is emitted realpath'd (alongside its as-given
  spelling when that differs - the `/tmp` vs `/private/tmp` family). This is also what makes symlink escapes a
  non-issue: an open through a symlink pointing outside the granted roots resolves outside them and is denied.

- Caller-supplied path values travel as `-D` profile parameters referenced via `(param ...)`, never spliced into the
  profile text, so they never touch the SBPL parser and quoting / injection is structurally moot. Only fixed constants
  are inlined.

- `file-read-metadata` is granted only on the *ancestor* directories of granted paths, as literals: enough for path
  resolution and getcwd, without turning the sandbox into a filesystem-wide stat / existence / size oracle.

Deliberately absent relative to the obvious "just allow it" profile: `mach-lookup` (the classic seatbelt escape surface
- plain CLI tools degrade fine without it), unscoped `sysctl-read` (KERN_PROCARGS2 answers other same-uid processes'
argv and env), `process-fork` and unscoped `process-exec`, and any grant on the shared host /tmp or /dev.
`policy.private_tmp` instead makes a fresh per-spawn directory and exports it as TMPDIR.

`sandbox-exec` has carried a deprecation banner for years but remains the substrate under Chromium's, Bazel's, and
various agent harnesses' macOS sandboxes; profiles are best iterated empirically against `log stream --style compact
--predicate 'sender == "Sandbox" OR process == "sandboxd"'`, which shows the exact denied operation and path.

====

To debug:
  - log stream --style compact --predicate 'sender == "Sandbox" OR process == "sandboxd"'
"""
import io
import os.path
import pathlib
import tempfile
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ..types.options import Sandbox
from ..types.specs import ProcessSpec
from .policy import SandboxPolicy


##


@dc.dataclass(frozen=True)
class _SxQuote:
    s: str


_SxConst: ta.TypeAlias = ta.Union[  # noqa: UP007
    int,
    float,
    _SxQuote,
]


type _Sx = ta.Union[  # noqa: UP007
    str,
    _SxConst,
    list[_Sx],
]


def _sxq(s: str) -> _SxQuote:
    return _SxQuote(s)


def _sx_render_to(out: lang.SupportsWrite[str], *xs: _Sx) -> None:
    def rec(c: _Sx) -> None:
        if isinstance(c, _SxQuote):
            s = c.s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            out.write(f'"{s}"')

        elif isinstance(c, _SxConst):  # type: ignore[arg-type]
            out.write(str(c))

        elif isinstance(c, str):
            out.write(c)

        elif isinstance(c, list):
            out.write('(')
            for j, n in enumerate(c):
                if j:
                    out.write(' ')
                rec(n)
            out.write(')')

        else:
            raise TypeError(c)

    for i, x in enumerate(xs):
        if i:
            out.write('\n')
        rec(x)


##


def _ancestor_dirs(path: str) -> list[str]:
    # '/a/b/c' -> ['/', '/a', '/a/b']
    return [str(x) for x in reversed(pathlib.PurePosixPath(path).parents)]


def _path_forms(p: str) -> list[str]:
    # The realpath'd form - what seatbelt actually matches - plus the as-given spelling when it differs.
    ap = os.path.abspath(p)
    return list(dict.fromkeys((os.path.realpath(ap), ap)))


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class SeatbeltProfile(lang.Final):
    profile: str

    # Ordered `-D` parameter definitions, referenced from the profile via `(param ...)`.
    params: ta.Mapping[str, str]


def build_seatbelt_profile(
        policy: SandboxPolicy,
        *,
        argv0: str | None = None,
        tmp_dir: str | None = None,
) -> SeatbeltProfile:
    params: dict[str, str] = {}
    counts: dict[str, int] = {}

    def param(prefix: str, value: str) -> _Sx:
        for ek, ev in params.items():
            if ev == value:
                return ['param', _sxq(ek)]
        n = counts.get(prefix, 0)
        counts[prefix] = n + 1
        k = f'{prefix}_{n}'
        params[k] = value
        return ['param', _sxq(k)]

    meta_dirs: dict[str, None] = {}

    def note_meta(forms: ta.Iterable[str]) -> None:
        for f in forms:
            for a in _ancestor_dirs(f):
                meta_dirs.setdefault(a)

    lines: list[_Sx] = [
        ['version', 1],
        ['deny', 'default'],
    ]

    # Exec. sandbox-exec compiles the profile and then execs the target *inside* it, so at minimum the target binary
    # itself must be exec- and read-allowed - hence 'self'.
    if policy.exec_paths == 'any':
        lines.append(['allow', 'process-exec'])
    else:
        if policy.exec_paths == 'self':
            if not argv0:
                raise ValueError("exec_paths='self' requires an argv0")
            if not os.path.isabs(argv0):
                raise ValueError(f"exec_paths='self' requires an absolute argv[0]: {argv0!r}")
            exec_paths: ta.Sequence[str] = (argv0,)
        else:
            exec_paths = policy.exec_paths

        exec_forms = list(dict.fromkeys(f for p in exec_paths for f in _path_forms(p)))
        note_meta(exec_forms)
        lines.append(['allow', 'process-exec', *[['literal', param('EXEC', f)] for f in exec_forms]])
        lines.append(['allow', 'file-read*', *[['literal', param('EXEC', f)] for f in exec_forms]])

    if policy.allow_fork:
        lines.append(['allow', 'process-fork'])

    lines.append(['allow', 'signal', ['target', 'self']])

    if policy.sysctl_names == 'any':
        lines.append(['allow', 'sysctl-read'])
    elif policy.sysctl_names:
        lines.append(['allow', 'sysctl-read', *[
            ['sysctl-name-prefix' if n.endswith('.') else 'sysctl-name', _sxq(n)]
            for n in policy.sysctl_names
        ]])

    if policy.mach_lookup == 'any':
        lines.append(['allow', 'mach-lookup'])
    elif policy.mach_lookup:
        lines.append(['allow', 'mach-lookup', *[['global-name', _sxq(n)] for n in policy.mach_lookup]])

    # Reads.
    read_forms: list[str] = []
    for d in policy.system_read_roots:
        if not os.path.exists(os.path.realpath(d)):
            continue
        read_forms.extend(_path_forms(d))
    for d in policy.read_roots:
        read_forms.extend(_path_forms(d))
    read_forms = list(dict.fromkeys(read_forms))
    note_meta(read_forms)
    for f in read_forms:
        lines.append(['allow', 'file-read*', ['subpath', param('RD', f)]])

    # Writes. file-read* + file-write* rather than file*: the wildcard would also grant file-ioctl, file-mount, &c.
    write_forms: list[str] = []
    for w in policy.write_roots:
        write_forms.extend(_path_forms(w))
    if tmp_dir is not None:
        write_forms.extend(_path_forms(tmp_dir))
    write_forms = list(dict.fromkeys(write_forms))
    note_meta(write_forms)
    for f in write_forms:
        lines.append(['allow', 'file-read*', 'file-write*', ['subpath', param('WR', f)]])

    # Dev.
    if policy.dev == 'all':
        lines.append(['allow', 'file*', ['subpath', _sxq('/dev')]])
        note_meta(['/dev'])
    elif policy.dev == 'minimal':
        lines.append(['allow', 'file-read*', 'file-write-data', ['literal', _sxq('/dev/null')]])
        lines.append(['allow', 'file-read*', *[
            ['literal', _sxq(d)] for d in ('/dev/zero', '/dev/random', '/dev/urandom')
        ]])
        note_meta(['/dev/null'])

    # Ancestor metadata for path resolution: literal dirs only - existence / stat, never contents.
    if meta_dirs:
        lines.append(['allow', 'file-read-metadata', 'file-test-existence', *[
            ['literal', param('META', a)] for a in meta_dirs
        ]])

    if policy.allow_network:
        lines.append(['allow', 'network*'])

    out = io.StringIO()
    _sx_render_to(out, *lines)
    out.write('\n')

    return SeatbeltProfile(
        profile=out.getvalue(),
        params=params,
    )


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class SeatbeltSandbox(Sandbox, lang.Final):
    policy: SandboxPolicy

    sandbox_exec: str = '/usr/bin/sandbox-exec'

    def transform_spec(self, spec: ProcessSpec) -> ProcessSpec:
        tmp_dir: str | None = None
        if self.policy.private_tmp:
            # A fresh dir under the user's per-user temp root (/var/folders/..., already mode-0700), exported as TMPDIR.
            # Not removed here: the OS's periodic per-user temp cleanup reaps it; scope-tied removal is an open item.
            tmp_dir = os.path.realpath(tempfile.mkdtemp(prefix='om-sandbox-'))

        prof = build_seatbelt_profile(
            self.policy,
            argv0=spec.argv[0],
            tmp_dir=tmp_dir,
        )

        defs: list[str] = []
        for k, v in prof.params.items():
            defs.extend(['-D', f'{k}={v}'])

        spec = dc.replace(spec, argv=[self.sandbox_exec, *defs, '-p', prof.profile, *spec.argv])

        if tmp_dir is not None:
            spec = spec.with_env(TMPDIR=tmp_dir)

        return spec
