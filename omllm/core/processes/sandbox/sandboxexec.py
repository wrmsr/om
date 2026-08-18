"""
macOS `sandbox-exec` confinement backend. Renders a `SandboxPolicy` into a Scheme-ish sandbox profile that denies by
default and allows reads/writes only under the permitted subpaths. Cannot be exercised off macOS; kept structurally
simple.

TODO:
 - rename
 - bring back sexp lol
"""
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ..types.options import Sandbox
from ..types.specs import ProcessSpec
from .policy import SandboxPolicy


##


def _quote(s: str) -> str:
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def build_sandbox_exec_profile(policy: SandboxPolicy) -> str:
    lines: list[str] = [
        '(version 1)',
        '(deny default)',
        '(allow process-exec)',
        '(allow process-fork)',
        '(allow sysctl-read)',
        '(allow mach-lookup)',
        '(allow signal (target self))',
        '(allow file-read-metadata)',
    ]

    for d in (*policy.system_read_roots, *policy.read_roots):
        lines.append(f'(allow file-read* (subpath {_quote(d)}))')
    for w in policy.write_roots:
        lines.append(f'(allow file* (subpath {_quote(w)}))')

    if policy.tmpfs_tmp:
        lines.append('(allow file* (subpath "/tmp"))')
        lines.append('(allow file* (subpath "/private/tmp"))')
    if policy.allow_dev:
        lines.append('(allow file* (subpath "/dev"))')
    if policy.allow_network:
        lines.append('(allow network*)')

    return '\n'.join(lines) + '\n'


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class SandboxExecSandbox(Sandbox, lang.Final):
    policy: SandboxPolicy

    sandbox_exec: str = '/usr/bin/sandbox-exec'

    def transform_spec(self, spec: ProcessSpec) -> ProcessSpec:
        profile = build_sandbox_exec_profile(self.policy)
        argv = [self.sandbox_exec, '-p', profile, *spec.argv]
        return dc.replace(spec, argv=argv)
