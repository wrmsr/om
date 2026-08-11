import typing as ta

from ... import lang
from ... import reflect as rfl
from .api import DisjointPolymorphism
from .api import Polymorphism
from .api import SubtypeInfo
from .api import SubtypeInfos


##


def _root_matches(rty: rfl.Type, key: ta.Any) -> bool:
    if isinstance(key, rfl.Type):
        return rty.type_key_or_none() == key.type_key_or_none() if rty.type_key_or_none() is not None else rty is key

    return rfl.get_runtime_object_or_none(rty) is key


def _covered_subtypes(p: Polymorphism, cls: type) -> ta.Sequence[SubtypeInfo] | None:
    """
    The subtypes an abstract intermediate covers - computed on demand rather than recorded at scan time. Covers
    concrete entries only: lazy entries cannot be subclass-tested without importing.
    """

    if not (isinstance(p.root, type) and lang.is_abstract(cls) and issubclass(cls, p.root)):
        return None

    if not (covered := [i for i in p.subtypes if (c := i.cls) is not None and issubclass(c, cls)]):
        return None

    return covered


def _member_subtypes(p: Polymorphism, t: type) -> ta.Sequence[SubtypeInfo] | None:
    """
    The subtypes a single union member claims of a polymorphism - the member may be the root, a concrete subtype, or
    a covering abstract intermediate.
    """

    if t is p.root:
        return list(p.subtypes)

    if (i := p.subtypes.by_ty.get(t)) is not None:
        return [i]

    # A loaded member class may have been resolved as a lazy declaration - unify by fqcn.
    if (
            (tf := lang.get_cls_fqcn(t, optional=True)) is not None and
            (i := p.subtypes.lazy_by_fqcn.get(tf)) is not None
    ):
        return [i]

    return _covered_subtypes(p, t)


##


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

    out: dict[int, SubtypeInfo] = {}
    for t in ta.cast('set[type]', set(tys)):
        if (ms := _member_subtypes(p, t)) is None:
            return None
        out.update({id(i): i for i in ms})

    return SubtypeInfos(list(out.values()))


##


def get_disjoint_polymorphism_subtypes(
        rty: rfl.Type,
        dp: DisjointPolymorphism,
) -> SubtypeInfos | None:
    if not isinstance(rty, rfl.UnionType):
        for p in dp.polymorphisms:
            if (sts := get_polymorphism_subtypes(rty, p)) is not None:
                return sts
        return None

    tys = [rfl.get_runtime_type_or_none(it) for it in rty.items]
    if any(t is None for t in tys):
        return None

    out: dict[int, SubtypeInfo] = {}
    for t in ta.cast('set[type]', set(tys)):
        for p in dp.polymorphisms:
            if (m_sts := _member_subtypes(p, t)) is not None:
                out.update({id(i): i for i in m_sts})
                break
        else:
            return None

    sts = SubtypeInfos(list(out.values()))
    sts.by_tag  # noqa  # A recognized-but-conflicting merger is a real error, not a pass.
    return sts
