"""
How parameters are held: the quantized width, the group, the error-minimising search and the per-tensor precision
policy. Each choice that changes the stored bytes contributes to the parameter cache's key, so recipes for one source
coexist on disk.
"""
import typing as ta

from omcore import dataclasses as dc

from ..ops.quant import QUANT_BITS
from .policies import POLICIES


PolicyFn: ta.TypeAlias = ta.Callable[[str, ta.Any], int | None]  # (canonical name, config) -> bits override | None


##


@dc.dataclass(frozen=True)
class LoadRecipe:
    """
    quant: None (dense), 'int8' or 'int4' -- weight-only affine, group-wise (see ops/quant.py).
    policy: per-tensor precision, a name in `POLICIES` or a callable (name, config) -> bits override | None.
    search: the error-minimising scale search when quantizing; off is plain min/max.
    """

    quant: str | None = None
    group: int = 64
    search: bool = True
    policy: str | PolicyFn = 'uniform'

    def __post_init__(self) -> None:
        if self.quant is not None and self.quant not in QUANT_BITS:
            raise ValueError(f'quant must be one of {list(QUANT_BITS)}, got {self.quant!r}')

    @property
    def bits(self) -> int | None:
        return QUANT_BITS[self.quant] if self.quant else None

    @property
    def policy_name(self) -> str:
        if isinstance(self.policy, str):
            return self.policy
        return getattr(self.policy, '__name__', 'custom')

    @property
    def policy_fn(self) -> PolicyFn:
        return POLICIES[self.policy] if isinstance(self.policy, str) else self.policy

    def width(self, name: str, cfg: ta.Any) -> int | None:
        """The width the policy gives a source tensor (None for a dense model)."""

        if (bits := self.bits) is None:
            return None
        return self.policy_fn(name, cfg) or bits

    def cache_variant(self) -> str:
        """
        The recipe's contribution to the parameter cache's key beyond the width and group: the policy (when not
        'uniform') and the search ('s'), in that order.
        """

        tags = (
            self.policy_name if self.policy_name != 'uniform' else '',
            's' if self.search else '',
        )
        return '-'.join(t for t in tags if t)

    def describe(self) -> str:
        return f'{self.policy_name}, search' if self.search else self.policy_name
