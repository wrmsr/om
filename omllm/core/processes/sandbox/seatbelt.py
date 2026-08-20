# ruff: noqa: S108
"""
macOS `sandbox-exec` confinement backend. Renders a `SandboxPolicy` into a Scheme-ish sandbox profile that denies by
default and allows reads/writes only under the permitted subpaths. Cannot be exercised off macOS; kept structurally
simple.
"""
import io
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
            s = c.s.replace('\\', '\\\\').replace('"', '\\"').replace('\\n', '\\\\n')
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


def _sx_render(*xs: _Sx) -> str:
    out = io.StringIO()
    _sx_render_to(out, *xs)
    return out.getvalue()


##


def _quote(s: str) -> str:
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def build_seatbelt_profile(policy: SandboxPolicy) -> str:
    lines: list[_Sx] = [
        ['version', 1],
        ['deny', 'default'],
        ['allow', 'process-exec'],
        ['allow', 'process-fork'],
        ['allow', 'sysctl-read'],
        ['allow', 'mach-lookup'],
        ['allow', 'signal', ['target', 'self']],
        ['allow', 'file-read-metadata'],
    ]

    for d in (*policy.system_read_roots, *policy.read_roots):
        lines.append(['allow', 'file-read*', ['subpath', _sxq(d)]])
    for w in policy.write_roots:
        lines.append(['allow', 'file*', ['subpath', _sxq(w)]])

    if policy.tmpfs_tmp:
        lines.append(['allow', 'file*', ['subpath', _sxq('/tmp')]])
        lines.append(['allow', 'file*', ['subpath', _sxq('/private/tmp')]])
    if policy.allow_dev:
        lines.append(['allow', 'file*', ['subpath', _sxq('/dev')]])
    if policy.allow_network:
        lines.append(['allow', 'network*'])

    out = io.StringIO()
    _sx_render_to(out, *lines)
    out.write('\n')
    return out.getvalue()


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class SeatbeltSandbox(Sandbox, lang.Final):
    policy: SandboxPolicy

    sandbox_exec: str = '/usr/bin/sandbox-exec'

    def transform_spec(self, spec: ProcessSpec) -> ProcessSpec:
        profile = build_seatbelt_profile(self.policy)
        argv = [self.sandbox_exec, '-p', profile, *spec.argv]
        return dc.replace(spec, argv=argv)
