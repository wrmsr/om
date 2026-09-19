import enum
import typing as ta

from ... import dataclasses as dc


##


class ObjectKeyPolicy(enum.Enum):
    RAISE = 'raise'
    IGNORE = 'ignore'


@dc.dataclass(frozen=True, kw_only=True)
class JqValueOptions:
    object_key_policy: ObjectKeyPolicy = ObjectKeyPolicy.RAISE
    object_key_stringifier: ta.Callable[[object], str] | None = None


@dc.dataclass(frozen=True, kw_only=True)
class JqRuntimeOptions:
    max_recursion_depth: int | None = 1000
    stable_outputs: bool = True

    def __post_init__(self) -> None:
        if self.max_recursion_depth is not None and self.max_recursion_depth < 1:
            raise ValueError(self.max_recursion_depth)
