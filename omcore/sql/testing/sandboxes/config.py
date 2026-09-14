import re

from .... import check
from .... import dataclasses as dc
from .... import lang


##


_PREFIX_PAT = re.compile(r'^[a-z_][a-z0-9_]*_$')


@dc.dataclass(frozen=True, kw_only=True)
class SandboxesConfig(lang.Final):
    """
    Everything the sandbox machinery manages is named under `prefix`; its own internal objects (the test database, the
    role, the registry schema) sit under the doubled-underscore `internal_prefix`, leaving plain-prefix names for the
    sandboxes themselves. The prefix invariant is what makes a run safe to point at a shared server: nothing outside
    the prefix is ever named in a destructive statement.
    """

    prefix: str = '_osbx_'

    database: str = '_osbx__db'
    role: str = '_osbx__role'
    registry_schema: str = '_osbx__registry'

    # A lease is renewed by every allocation its run makes, so this only needs to outlast a run's idle stretches. A
    # run that dies with its lease unexpired is still reaped once it expires, provided none of its sessions linger.
    lease_ttl_s: float = 60. * 60.

    # How many times the reaper tries to drop a given orphan before giving up on it for this pass.
    reap_attempts: int = 3

    def __post_init__(self) -> None:
        check.arg(_PREFIX_PAT.fullmatch(self.prefix) is not None, self.prefix)
        for n in (self.database, self.role, self.registry_schema):
            check.arg(n.startswith(self.internal_prefix), n)
        check.arg(self.lease_ttl_s >= 0)
        check.arg(self.reap_attempts >= 1)

    @property
    def internal_prefix(self) -> str:
        return self.prefix + '_'
