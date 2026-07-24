"""
NOTE: This cannot be auto-imported as @om-lite usage of other modules in this package requires it be importable on
8.
"""
import dataclasses as dc
import typing as ta

from omcore import lang
from omcore import marshal as msh
from omcore import reflect as rfl

from .requirements import ParsedRequirement
from .requirements import RequirementMarkerItem
from .requirements import RequirementMarkerList
from .requirements import RequirementNode
from .requirements import RequirementOp
from .requirements import RequirementValue
from .requirements import RequirementVariable


##


class MarshalRequirementMarkerList(lang.NotInstantiable, lang.Final):
    pass


@dc.dataclass(frozen=True)
class RequirementMarkerListMarshaler(msh.Marshaler):
    item_m: msh.Marshaler
    node_m: msh.Marshaler

    def marshal(self, ctx: msh.MarshalContext, o: ta.Any) -> msh.Value:
        def inner(c: ta.Any) -> ta.Any:
            if isinstance(c, str):
                return c
            elif isinstance(c, RequirementMarkerItem):
                return self.item_m.marshal(ctx, c)
            elif isinstance(c, ta.Iterable):
                return [inner(e) for e in c]
            else:
                raise TypeError(c)
        return [inner(e) for e in o]


class RequirementMarkerListMarshalerFactory(msh.MarshalerFactory):
    def make_marshaler(self, ctx: msh.MarshalFactoryContext, rty: rfl.Type) -> ta.Callable[[], msh.Marshaler] | None:
        if rty.runtime_object is not MarshalRequirementMarkerList:
            return None
        return lambda: RequirementMarkerListMarshaler(
            ctx.make_marshaler(RequirementMarkerItem),
            ctx.make_marshaler(RequirementNode),
        )


##


@msh.register_global_lazy_init
def _install_standard_marshaling(cfgs: msh.ConfigRegistry) -> None:
    requires_node_poly = msh.Polymorphism(
        RequirementNode,
        [
            msh.Impl(RequirementVariable, 'variable'),
            msh.Impl(RequirementValue, 'value'),
            msh.Impl(RequirementOp, 'op'),
        ],
    )
    msh.install_standard_factories(
        cfgs,
        msh.PolymorphismMarshalerFactory(requires_node_poly),
        msh.PolymorphismUnmarshalerFactory(requires_node_poly),
    )

    msh.install_standard_factories(
        cfgs,
        RequirementMarkerListMarshalerFactory(),
    )

    cfgs.update(
        RequirementMarkerList,
        msh.ReflectOverride(MarshalRequirementMarkerList),
        identity=True,
    )

    cfgs.update(
        ParsedRequirement,
        msh.ObjectOptions(
            fields=dict(
                marker=msh.FieldOptions(
                    marshal_via=msh.MarshalVia(RequirementMarkerList | None),
                    unmarshal_via=msh.UnmarshalVia(RequirementMarkerList | None),
                ),
            ),
        ),
    )
