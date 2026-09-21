import typing as ta

from ..dtypes import Dtype
from ..tabledefs.elements import Column
from ..tabledefs.elements import Element
from ..tabledefs.elements import Elements
from ..tabledefs.elements import Index
from ..tabledefs.elements import OpaqueTrigger
from ..tabledefs.elements import PrimaryKey
from ..tabledefs.tabledefs import TableDef
from .reflected import ReflectedColumn
from .reflected import ReflectedTable


##


def lift_reflected_table(
        reflected: ReflectedTable,
        lift_dtype: ta.Callable[[ReflectedColumn], Dtype],
) -> TableDef:
    """
    The dialect-independent part of lifting a reflected snapshot into a diffable tabledef: only the mapping of a raw
    column type to a dtype differs per backend, and that is injected. Reflected triggers become opaque, name-only
    elements - present so the differ can see them, but never creatable.
    """

    els: list[Element] = []

    for rc in reflected.columns:
        els.append(Column(rc.name, lift_dtype(rc), nullable=rc.nullable))
    if reflected.primary_key:
        els.append(PrimaryKey(reflected.primary_key))

    for ri in reflected.indexes:
        els.append(Index(ri.columns, name=ri.name, unique=ri.unique))

    for rt in reflected.triggers:
        els.append(OpaqueTrigger(rt.name))

    return TableDef(reflected.name, Elements(*els))
