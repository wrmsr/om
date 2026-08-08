"""
TODO:
 - use lang.metadata?
"""
import typing as ta

from ... import check
from ... import collections as col
from ... import dataclasses as dc
from ... import lang
from ... import metadata as md
from ... import reflect as rfl
from ...lite import marshal as lm
from ..api.configs import ConfigsGetter
from ..api.contexts import BaseFactoryContext
from ..api.contexts import MarshalFactoryContext
from ..api.contexts import UnmarshalFactoryContext
from ..api.naming import Naming
from ..api.naming import as_naming
from ..api.naming import translate_name
from ..api.specs import Spec
from ..api.types import DuplexFactory
from ..api.types import Marshaler
from ..api.types import Unmarshaler
from .api import DEFAULT_FIELD_OPTIONS
from .api import DEFAULT_OBJECT_OPTIONS
from .api import FieldOptions
from .api import ObjectOptions
from .api import _ObjectOptionsMetadata
from .infos import FieldInfo
from .infos import FieldInfos
from .specs import ObjectSpec


##


def get_dataclass_options(
        ty: type,
        cfgs: ConfigsGetter | None = None,
) -> ObjectOptions:
    opts = DEFAULT_OBJECT_OPTIONS

    if dc_md_opts := dc.reflect(ty).spec.metadata_by_type.get(ObjectOptions, []):
        opts = opts.merge(*dc_md_opts)

    if cfgs is not None and (cfg_opts := cfgs(ty).get(ObjectOptions)):
        opts = opts.merge(*cfg_opts)

    if md_opts := md.get_object_metadata(ty, type=_ObjectOptionsMetadata, mro_merge=True):
        opts = opts.merge(*[o.opts for o in md_opts])

    return opts


class _FieldInfoBuilder:
    def __init__(
            self,
            ty: type,
            configs: ConfigsGetter | None = None,
            *,
            dc_rfl: dc.ClassReflection | None = None,
            obj_opts: ObjectOptions | None = None,
    ) -> None:
        self.ty = ty
        self.configs = configs

        if obj_opts is None:
            obj_opts = get_dataclass_options(ty, configs)
        self.obj_opts = obj_opts

        fn: Naming | None = None
        if (oo_fn := self.obj_opts.field_naming) is not None:
            fn = as_naming(oo_fn)
        if fn is None and configs is not None:
            if (cn := configs(ty).get(Naming)) is None:
                cn = configs().get(Naming)
            if cn is not None:
                fn = cn
        self.class_naming = fn

        if dc_rfl is None:
            dc_rfl = dc.reflect(ty)
        self.dc_rfl = dc_rfl

    def build_field_options(self, field: dc.Field) -> FieldOptions:
        """
        Merges configuration from multiple sources in this order (later = higher precedence):
        1. Empty baseline
        2. Class-level field_defaults (from ObjectMetadata)
        3. Field-level FieldMetadata (from field.metadata)
        4. Lite marshal compatibility overrides (OBJ_MARSHALER_FIELD_KEY, etc.)
        5. ObjectOptions.fields
        """

        ##
        # Start with baseline (empty) and merge class-level defaults

        merged_opts = DEFAULT_FIELD_OPTIONS.merge(self.obj_opts.field_defaults)

        ##
        # Merge field-level FieldMetadata if present

        field_opts = field.metadata.get(FieldOptions)
        if field_opts is not None:
            merged_opts = merged_opts.merge(field_opts)

        ##
        # Lite marshal compatibility - build override metadata

        lite_override_kw: dict[str, ta.Any] = {}

        # Handle OBJ_MARSHALER_FIELD_KEY
        if lm.OBJ_MARSHALER_FIELD_KEY in field.metadata:
            lfk = field.metadata[lm.OBJ_MARSHALER_FIELD_KEY]
            if lfk is not None:
                check.non_empty_str(lfk)
                lite_override_kw['name'] = lfk
            else:
                lite_override_kw['no_marshal'] = True
                lite_override_kw['no_unmarshal'] = True

        # Handle OBJ_MARSHALER_OMIT_IF_NONE
        if (lon := field.metadata.get(lm.OBJ_MARSHALER_OMIT_IF_NONE)) is not None:
            if check.isinstance(lon, bool):
                lite_override_kw['omit_if'] = lang.is_none

        # Merge lite overrides if any
        if lite_override_kw:
            merged_opts = merged_opts.merge(FieldOptions(**lite_override_kw))

        ##
        # ObjectOptions

        if oo_fields := self.obj_opts.fields:
            if (oo_opts := oo_fields.get(field.name)) is None:
                oo_opts = oo_fields.get(None)
            if oo_opts is not None:
                merged_opts = merged_opts.merge(oo_opts)

        ##
        # Done

        return merged_opts

    def build_field_info(self, field: dc.Field) -> FieldInfo:
        merged_opts = self.build_field_options(field)

        ##
        # Determine field type (with generic replacement if needed)

        if self.dc_rfl.spec.generic_init or merged_opts.generic_replace:
            f_ty = self.dc_rfl.fields_inspection.generic_replaced_field_annotations[field.name]
        else:
            f_ty = self.dc_rfl.type_hints[field.name]

        ##
        # Compute marshal/unmarshal names based on merged metadata

        has_explicit_name = merged_opts.name is not None

        marshal_name: str | None
        unmarshal_names: ta.Sequence[str]

        if has_explicit_name:
            # Explicitly set name takes precedence
            # Type narrow: we know merged_opts.name is not None here
            explicit_name = check.not_none(merged_opts.name)
            marshal_name = explicit_name
            unmarshal_names = col.unique([explicit_name, *(merged_opts.alts or ())])
        else:
            # Use naming convention if available, otherwise field name
            field_naming = field.metadata.get(Naming, self.class_naming)
            if field_naming is not None:
                base_name = translate_name(field.name, field_naming)
            else:
                base_name = field.name

            marshal_name = base_name
            unmarshal_names = [base_name]

        ##
        # Handle embed suffix (only if name wasn't explicitly set)

        if merged_opts.embed and not has_explicit_name:
            # At this point marshal_name is guaranteed to be str (not None)
            marshal_name = check.not_none(marshal_name) + '_'
            unmarshal_names = [n + '_' for n in unmarshal_names]

        ##
        # Handle no_marshal/no_unmarshal

        if merged_opts.no_marshal:
            marshal_name = None
        if merged_opts.no_unmarshal:
            unmarshal_names = []

        ##
        # Create FieldInfo with computed values

        return FieldInfo(
            name=field.name,
            type=f_ty,
            marshal_name=marshal_name,
            unmarshal_names=unmarshal_names,
            options=merged_opts,
        )

    def build_field_infos(self) -> FieldInfos:
        ret: list[FieldInfo] = []

        for field in self.dc_rfl.instance_fields:
            ret.append(self.build_field_info(field))

        return FieldInfos(ret)


def get_dataclass_field_infos(
        ty: type,
        configs: ConfigsGetter | None = None,
) -> FieldInfos:
    return _FieldInfoBuilder(ty, configs).build_field_infos()


##


def _type_or_generic_base(rty: rfl.Type) -> type | None:
    if not isinstance(rty, rfl.Instance):
        return None
    return rfl.get_runtime_type_or_none(rty)


##


def get_dataclass_object_spec(
        ty: type,
        cfgs: ConfigsGetter | None = None,
) -> ObjectSpec:
    check.state(dc.is_dataclass(ty))
    check.state(not lang.is_abstract_class(ty))

    obj_opts = get_dataclass_options(ty, cfgs)
    dc_rfl = dc.reflect(ty)
    fib = _FieldInfoBuilder(ty, cfgs, dc_rfl=dc_rfl, obj_opts=obj_opts)
    fis = fib.build_field_infos()

    # Embedded fields' specs are pre-resolved here so spec consumption stays config-free.
    embeds: dict[str, ObjectSpec] = {}
    for fi in fis:
        if not fi.options.embed:
            continue

        e_ty = check.isinstance(fi.type, type)
        check.state(dc.is_dataclass(e_ty))
        e_spec = get_dataclass_object_spec(e_ty, cfgs)
        if e_spec.specials.set:
            raise Exception(f'Embedded fields cannot have specials: {e_ty}')

        embeds[fi.name] = e_spec

    return ObjectSpec(
        ty=ty,
        fields=fis,
        specials=obj_opts.specials,
        ignore_unknown=bool(obj_opts.ignore_unknown),
        unwrap_if_single_field=obj_opts.unwrap_if_single_field,
        embeds=embeds,
    )


class DataclassFactory(DuplexFactory):
    """
    Derives ObjectSpecs from concrete dataclass types (reading any registered configs - the reads land in this reflected
    type's cache footprint).
    """

    def _derive_spec(self, ctx: BaseFactoryContext, spec: Spec) -> ObjectSpec | None:
        if not isinstance(spec, rfl.Type):
            return None

        if not (
            (ty := _type_or_generic_base(spec)) is not None and
            dc.is_dataclass(ty) and
            not lang.is_abstract_class(ty)
        ):
            return None

        return get_dataclass_object_spec(ty, ctx.get_configs)

    def make_marshaler(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        if (osp := self._derive_spec(ctx, spec)) is None:
            return None

        return lambda: ctx.make_marshaler(osp)

    def make_unmarshaler(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        if (osp := self._derive_spec(ctx, spec)) is None:
            return None

        return lambda: ctx.make_unmarshaler(osp)


DataclassMarshalerFactory = DataclassFactory
DataclassUnmarshalerFactory = DataclassFactory
