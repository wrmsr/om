import collections.abc
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import reflect as rfl
from ..api.contexts import UnmarshalContext
from ..api.contexts import UnmarshalFactoryContext
from ..api.specs import Spec
from ..api.types import Unmarshaler
from ..api.types import UnmarshalerFactory
from ..api.values import Value
from ..api.vias import make_unmarshaler_via
from .api import ObjectSpecials
from .infos import FieldInfo
from .infos import FieldInfos
from .specs import ObjectSpec


##


@dc.dataclass(frozen=True)
class ObjectUnmarshaler(Unmarshaler):
    factory: ta.Callable
    fields_by_unmarshal_name: ta.Mapping[str, tuple[FieldInfo, Unmarshaler]]

    _: dc.KW_ONLY

    specials: ObjectSpecials = ObjectSpecials()

    defaults: ta.Mapping[str, ta.Any] | None = None

    embeds: ta.Mapping[str, type] | None = None
    embeds_by_unmarshal_name: ta.Mapping[str, tuple[str, str]] | None = None

    ignore_unknown: bool = False

    unwrap_if_single_field: FieldInfo | None = None
    is_single_field: bool | None = None

    @classmethod
    def make(
            cls,
            ctx: UnmarshalFactoryContext,
            factory: ta.Callable,
            fis: FieldInfos,
            **kwargs: ta.Any,
    ) -> Unmarshaler:
        fields_by_unmarshal_name = {
            n: (fi, ctx.make_unmarshaler(fi.type))
            for fi in fis
            for n in fi.unmarshal_names
        }

        defaults = {
            fi.name: dfl.must()
            for fi in fis
            if (dfl := fi.options.default) is not None and dfl.present
        }

        return cls(
            factory,
            fields_by_unmarshal_name,
            defaults=defaults,
            **kwargs,
        )

    #

    def unmarshal(self, ctx: UnmarshalContext, v: Value) -> ta.Any:
        ma: collections.abc.Mapping

        is_map = isinstance(v, collections.abc.Mapping)

        if (usf := self.unwrap_if_single_field) is not None and (not is_map or self.is_single_field):
            ma = {usf.unmarshal_names[0]: v}

        elif is_map:
            ma = v  # type: ignore[assignment]  # noqa

        elif (usf := self.unwrap_if_single_field) is not None:
            ma = {usf.unmarshal_names[0]: v}

        else:
            raise TypeError(v)

        u: ta.Any
        kw: dict[str, ta.Any] = {}
        ukf: dict[str, ta.Any] | None = None

        ekws: dict[str, dict[str, ta.Any]] = {en: {} for en in self.embeds or ()}

        if self.specials.source is not None:
            kw[self.specials.source] = v

        if self.specials.unknown is not None:
            kw[self.specials.unknown] = ukf = {}

        for k, mv in ma.items():
            ks = check.isinstance(k, str)

            try:
                fi, u = self.fields_by_unmarshal_name[ks]

            except KeyError:
                if ukf is not None:
                    ukf[ks] = mv  # FIXME: unmarshal?
                    continue

                if self.ignore_unknown:
                    continue

                raise

            if self.embeds_by_unmarshal_name and (en := self.embeds_by_unmarshal_name.get(ks)):
                tkw, tk = ekws[en[0]], en[1]
            else:
                tkw, tk = kw, fi.name

            if tk in tkw:
                raise KeyError(f'Duplicate keys for field {tk!r}: {ks!r}')

            tkw[tk] = u.unmarshal(ctx, mv)

        for em, ecls in self.embeds.items() if self.embeds else ():
            ekw = ekws[em]
            ev = ecls(**ekw)
            kw[em] = ev

        if self.defaults:
            for dk, dv in self.defaults.items():
                kw.setdefault(dk, dv)

        return self.factory(**kw)


##


class _ObjectUnmarshalerBuilder:
    def __init__(self, ctx: UnmarshalFactoryContext, spec: ObjectSpec) -> None:
        super().__init__()

        self.ctx = ctx
        self.spec = spec

        self._fields_dct: dict[str, tuple[FieldInfo, Unmarshaler]] = {}

        self._defaults: dict[str, ta.Any] = {}
        self._embeds: dict[str, type] = {}
        self._embeds_by_unmarshal_name: dict[str, tuple[str, str]] = {}

    def _make_field_unmarshaler(self, fi: FieldInfo) -> Unmarshaler:
        if (via := fi.options.unmarshal_via) is not None:
            return make_unmarshaler_via(self.ctx, fi.type, via)

        return self.ctx.make_unmarshaler(fi.type)

    def _add_field(
            self,
            spec: ObjectSpec,
            fi: FieldInfo,
            *,
            prefixes: ta.Iterable[str] = ('',),
    ) -> ta.Iterable[str]:
        if fi.options.no_unmarshal:
            return []

        ret: list[str] = []

        if fi.options.embed:
            e_spec = spec.embeds[fi.name]
            if e_spec.specials.set:
                raise Exception(f'Embedded fields cannot have specials: {e_spec.ty}')

            self._embeds[fi.name] = e_spec.ty
            for e_fi in e_spec.fields:
                e_ns = self._add_field(e_spec, e_fi, prefixes=[p + ep for p in prefixes for ep in fi.unmarshal_names])
                self._embeds_by_unmarshal_name.update({e_f: (fi.name, e_fi.name) for e_f in e_ns})
                ret.extend(e_ns)

        else:
            tup = (fi, self._make_field_unmarshaler(fi))

            for pfx in prefixes:
                for un in fi.unmarshal_names:
                    un = pfx + un
                    if un in self._fields_dct:
                        raise KeyError(f'Duplicate fields for name {un!r}: {fi.name!r}, {self._fields_dct[un][0].name!r}')  # noqa
                    self._fields_dct[un] = tup
                    ret.append(un)

            if (dfl := fi.options.default) is not None and dfl.present:
                self._defaults[fi.name] = dfl.must()

        return ret

    def build(self) -> Unmarshaler:
        spec = self.spec

        for fi in spec.fields:
            if fi.name in spec.specials.set:
                continue
            self._add_field(spec, fi)

        unwrap_if_single_field: FieldInfo | None = None
        if spec.unwrap_if_single_field in ('unmarshal', True):
            unwrap_if_single_field = next(iter(self._fields_dct.values()))[0]

        return ObjectUnmarshaler(
            spec.ty,
            self._fields_dct,
            specials=spec.specials,
            defaults=self._defaults,
            embeds=self._embeds,
            embeds_by_unmarshal_name=self._embeds_by_unmarshal_name,
            ignore_unknown=spec.ignore_unknown,
            unwrap_if_single_field=unwrap_if_single_field,
            # Must mirror the marshaler's participating-field count (which excludes no_marshal fields and specials) or
            # unwrapped output won't roundtrip.
            is_single_field=len([
                fi
                for fi in spec.fields
                if not fi.options.no_unmarshal
                and fi.name not in spec.specials.set
            ]) < 2,
        )


class ObjectUnmarshalerFactory(UnmarshalerFactory):
    """Consumes ObjectSpecs. Spec consumption is config-free - everything is baked into the spec."""

    def make_unmarshaler(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        if not isinstance(spec, ObjectSpec):
            return None

        return lambda: _ObjectUnmarshalerBuilder(ctx, spec).build()


##


@dc.dataclass(frozen=True)
class SimpleObjectUnmarshalerFactory(UnmarshalerFactory):
    dct: ta.Mapping[type, ta.Sequence[FieldInfo]]

    _: dc.KW_ONLY

    specials: ObjectSpecials = ObjectSpecials()

    def make_unmarshaler(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        if not isinstance(spec, rfl.Type):
            return None

        if (ty := rfl.get_runtime_type_or_none(spec)) is None or ty not in self.dct:
            return None

        osp = ObjectSpec(
            ty=check.not_none(ty),
            fields=FieldInfos(self.dct[ty]),
            specials=self.specials,
        )

        return lambda: ctx.make_unmarshaler(osp)
