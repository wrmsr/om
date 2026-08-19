import typing as ta

from omcore import check
from omcore import dataclasses as dc


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ScopeClosePolicy:
    # Backstop over the concurrent close of all of a scope's processes (each of which is already bounded by its own
    # TerminationPolicy). On expiry, remaining handles are SIGKILLed and abandoned (reaped later by their lingering
    # watchers) - or, if they had already exited, reaped right away.
    overall_timeout_s: float | None = 60.

    def __post_init__(self) -> None:
        check.arg(self.overall_timeout_s is None or self.overall_timeout_s > 0)


DEFAULT_SCOPE_CLOSE_POLICY: ta.Final = ScopeClosePolicy()
