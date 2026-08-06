import collections.abc
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import reflect as rfl
from ..api.contexts import MarshalContext
from ..api.contexts import MarshalFactoryContext
from ..api.specs import Spec
from ..api.types import Marshaler
from ..api.types import MarshalerFactory
from ..api.values import Value
from ..api.vias import make_marshaler_via
from .api import ObjectSpecials
from .infos import FieldInfo
from .infos import FieldInfos
from .specs import ObjectSpec


##


@dc.dataclass(frozen=True)
class ObjectMarshaler(Marshaler):
    fields: ta.Sequence[tuple[FieldInfo, Marshaler]]

    _: dc.KW_ONLY

    specials: ObjectSpecials = ObjectSpecials()

    attr_getter: ta.Callable[[ta.Any, str], ta.Any] | None = None

    unwrap_if_single_field: FieldInfo | None = None

    @classmethod
    def make(
            cls,
            ctx: MarshalFactoryContext,
            fis: FieldInfos,
            **kwargs: ta.Any,
    ) -> Marshaler:
        fields = [
            (fi, ctx.make_marshaler(fi.type))
            for fi in fis
        ]

        return cls(
            fields,
            **kwargs,
        )

    #

    def marshal(self, ctx: MarshalContext, o: ta.Any) -> Value:
        if (attr_getter := self.attr_getter) is None:
            attr_getter = getattr

        ret: dict[str, ta.Any] = {}
        for fi, m in self.fields:
            v = attr_getter(o, fi.name)

            if fi.options.omit_if is not None and fi.options.omit_if(v):
                continue

            if fi.name in self.specials.set:
                continue

            mn = fi.marshal_name
            if mn is None:
                continue

            mv = m.marshal(ctx, v)

            if fi.options.embed:
                for ek, ev in check.isinstance(mv, collections.abc.Mapping).items():
                    ret[mn + check.non_empty_str(ek)] = ev

            else:
                ret[mn] = mv

        if self.specials.unknown is not None:
            if (ukf := attr_getter(o, self.specials.unknown)):
                if (dks := set(ret) & set(ukf)):
                    raise KeyError(f'Unknown field keys duplicate fields: {dks!r}')

                ret.update(ukf)  # FIXME: marshal?

        if (usf := self.unwrap_if_single_field) is not None and len(ret) == 1:
            skk, skv = next(iter(ret.items()))
            if skk == usf.marshal_name and (len(self.fields) < 2 or not isinstance(skv, collections.abc.Mapping)):
                ret = skv

        return ret


##


def _make_field_marshaler(ctx: MarshalFactoryContext, fi: FieldInfo) -> Marshaler:
    if (via := fi.options.marshal_via) is not None:
        return make_marshaler_via(ctx, fi.type, via)

    return ctx.make_marshaler(fi.type)


class ObjectMarshalerFactory(MarshalerFactory):
    """Consumes ObjectSpecs. Spec consumption is config-free - everything is baked into the spec."""

    def make_marshaler(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        if not isinstance(spec, ObjectSpec):
            return None

        def inner() -> Marshaler:
            fields = [
                (fi, _make_field_marshaler(ctx, fi))
                for fi in spec.fields
                if not fi.options.no_marshal
                and fi.name not in spec.specials.set
            ]

            unwrap_if_single_field: FieldInfo | None = None
            if spec.unwrap_if_single_field in ('marshal', True):
                unwrap_if_single_field = fields[0][0]

            return ObjectMarshaler(
                fields,
                specials=spec.specials,
                unwrap_if_single_field=unwrap_if_single_field,
            )

        return inner


##


@dc.dataclass(frozen=True)
class SimpleObjectMarshalerFactory(MarshalerFactory):
    dct: ta.Mapping[type, ta.Sequence[FieldInfo]]

    _: dc.KW_ONLY

    specials: ObjectSpecials = ObjectSpecials()

    def make_marshaler(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        if not isinstance(spec, rfl.Type):
            return None

        if (ty := rfl.get_runtime_type_or_none(spec)) is None or ty not in self.dct:
            return None

        osp = ObjectSpec(
            ty=check.not_none(ty),
            fields=FieldInfos(self.dct[ty]),
            specials=self.specials,
        )

        return lambda: ctx.make_marshaler(osp)
