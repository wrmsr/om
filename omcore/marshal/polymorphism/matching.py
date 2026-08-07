import typing as ta

from ... import lang
from ... import reflect as rfl
from .api import Polymorphism
from .api import SubtypeInfo
from .api import SubtypeInfos


##


def _root_matches(rty: rfl.Type, key: ta.Any) -> bool:
    if isinstance(key, rfl.Type):
        return rty.type_key_or_none() == key.type_key_or_none() if rty.type_key_or_none() is not None else rty is key

    return rfl.get_runtime_object_or_none(rty) is key


def _covered_subtypes(p: Polymorphism, cls: type) -> ta.Sequence[SubtypeInfo] | None:
    """The subtypes an abstract intermediate covers - computed on demand rather than recorded at scan time."""

    if not (isinstance(p.root, type) and lang.is_abstract(cls) and issubclass(cls, p.root)):
        return None

    if not (covered := [i for i in p.subtypes if issubclass(i.ty, cls)]):
        return None

    return covered


def get_polymorphism_subtypes(
        rty: rfl.Type,
        p: Polymorphism,
) -> SubtypeInfos | None:
    if _root_matches(rty, p.root):
        return p.subtypes

    if (
            (cls := rfl.get_runtime_type_or_none(rty)) is not None and
            (covered := _covered_subtypes(p, cls)) is not None
    ):
        return SubtypeInfos(covered)

    if (
            isinstance(rty, rfl.UnionType) and
            (u_is := get_polymorphism_union_subtypes(rty, p)) is not None
    ):
        return u_is

    return None


def get_polymorphism_union_subtypes(
        rty: rfl.UnionType,
        p: Polymorphism,
) -> SubtypeInfos | None:
    tys = [rfl.get_runtime_type_or_none(it) for it in rty.items]
    if any(t is None for t in tys):
        return None

    out: dict[type, SubtypeInfo] = {}
    for t in ta.cast('set[type]', set(tys)):
        if (i := p.subtypes.by_ty.get(t)) is not None:
            out[t] = i
        elif (covered := _covered_subtypes(p, t)) is not None:
            out.update({c.ty: c for c in covered})
        else:
            return None

    return SubtypeInfos(list(out.values()))
