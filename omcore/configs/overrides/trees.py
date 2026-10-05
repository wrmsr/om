import collections.abc
import typing as ta


##


def own_tree(v: ta.Any) -> ta.Any:
    """Deep-copies a tree into plain, unaliased dicts and lists."""

    if isinstance(v, collections.abc.Mapping):
        return {k: own_tree(e) for k, e in v.items()}
    elif isinstance(v, (str, bytes, bytearray)):
        return v
    elif isinstance(v, collections.abc.Sequence):
        return [own_tree(e) for e in v]
    else:
        return v
