import typing as ta

from .... import dataclasses as dc


##


@dc.dataclass(frozen=True)
class GroupInfo:
    """What a compiled pattern knows about its capturing groups, which it and its matches both work from."""

    num_groups: int
    index: ta.Mapping[str, int]
    names: ta.Mapping[int, str]

    # See TranslatedPattern.
    close_ranks: ta.Sequence[int]
