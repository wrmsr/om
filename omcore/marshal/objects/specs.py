"""
The direction-agnostic 'what' of object marshaling: a resolved set of field infos plus the object-level behaviors,
divorced from how it was discovered (dataclass reflection, namedtuple inspection, hand construction). Sniffing factories
(dataclasses, namedtuples) resolve reflected types to ObjectSpecs and re-enter; the ObjectMarshalerFactory /
ObjectUnmarshalerFactory pair consumes them.

Per the InternalSpec contract these are values - hashable and compared by value, serving as their own handler cache
keys. All contained collections are coerced to hashable forms at construction.
"""
import typing as ta

from ... import check
from ... import collections as col
from ... import dataclasses as dc
from ... import lang
from ..api.specs import InternalSpec
from .api import ObjectSpecials
from .infos import FieldInfos


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ObjectSpec(InternalSpec, lang.Final):
    ty: type
    fields: FieldInfos

    specials: ObjectSpecials = ObjectSpecials()

    ignore_unknown: bool = False

    unwrap_if_single_field: ta.Literal['marshal', 'unmarshal', True, None] = None

    # Pre-resolved specs for embedded fields, keyed by field name - present iff the corresponding FieldInfo has
    # `options.embed` set. Resolved at sniff time so spec consumption stays config-free. Coerced to a (hashable)
    # FrozenDict.
    embeds: ta.Mapping[str, ObjectSpec] = dc.xfield(
        default=col.frozendict(),
        coerce=col.frozendict,
    )

    def __post_init__(self) -> None:
        for fi in self.fields:
            if fi.options.embed:
                check.in_(fi.name, self.embeds)
        for en in self.embeds:
            check.state(self.fields.by_name[en].options.embed is True)
