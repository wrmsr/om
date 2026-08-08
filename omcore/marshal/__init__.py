# ruff: noqa: I001
from .. import dataclasses as _dc  # noqa


_dc.init_package(
    globals(),
    codegen=True,
)


##


from .. import lang as _lang  # noqa


with _lang.auto_proxy_init(globals()):
    ##

    from .api.configs import (  # noqa
        Config,
        ConfigValues,
        ConfigsGetter,

        ConfigRegistrySealedError,
        ConfigRegistry,

        LazyInitFn,
        LazyInit,

        ModuleImport,
    )

    from .api.contexts import (  # noqa
        Context,
        BoundContext,
        FactoryContext,

        BaseContext,

        MarshalFactoryContext,
        UnmarshalFactoryContext,

        MarshalContext,
        UnmarshalContext,
    )

    from .api.errors import (  # noqa
        ForbiddenError,
        ForbiddenTypeError,
        MarshalError,
        UnhandledTypeError,
    )

    from .api.funcs import (  # noqa
        MarshalerFactoryFn,
        UnmarshalerFactoryFn,

        FuncMarshaler,
        FuncUnmarshaler,

        FuncMarshalerFactory,
        FuncUnmarshalerFactory,
    )

    from .api.marshaling import (  # noqa
        Marshaling,

        SimpleMarshaling,

        RuntimeMarshaling,
    )

    from .api.naming import (  # noqa
        Naming,
        translate_name,
    )

    from .api.options import (  # noqa
        Option,
        Options,

        DefaultOptions,
        IgnoreDefaultOptions,

        update_default_options,
        build_effective_options,
    )

    from .api.reflect import (  # noqa
        ReflectOverride,
    )

    from .api.runtime import (  # noqa
        Runtime,
    )

    from .api.specs import (  # noqa
        InternalSpec,
        Spec,
    )

    from .api.types import (  # noqa
        Handler,
        Factory,

        Marshaler,
        Unmarshaler,
        DuplexHandler,

        MarshalerFactory,
        UnmarshalerFactory,
        DuplexFactory,
    )

    from .api.values import (  # noqa
        Value,

        VALUE_TYPES,
    )

    from .api.vias import (  # noqa
        MarshalVia,
        UnmarshalVia,

        kw_marshal_via,
        kw_unmarshal_via,
        kw_marshal_unmarshal_via,

        make_marshaler_via,
        make_unmarshaler_via,

        set_marshal_via,
        set_unmarshal_via,
    )

    from .composite.api import (  # noqa
        DEFAULT_ITERABLE_CONCRETE_TYPES,
        DefaultIterableConstructors,

        DEFAULT_MAPPING_CONCRETE_TYPES,
        DefaultMappingConstructors,

        DefaultPersistentConstructors,
    )

    from .composite.iterables import (  # noqa
        IterableMarshaler,
        IterableUnmarshaler,
    )

    from .composite.optionals import (  # noqa
        OptionalMarshaler,
        OptionalUnmarshaler,
    )

    from .composite.persistent import (  # noqa
        PersistentSequenceMarshaler,
        PersistentSequenceUnmarshaler,

        PersistentMappingMarshaler,
        PersistentMappingUnmarshaler,
    )

    from .composite.unions.api import (  # noqa
        LITERAL_UNION_TYPES,

        PRIMITIVE_UNION_TYPES,
    )

    from .composite.unions.literals import (  # noqa
        LiteralUnionMarshaler,
        LiteralUnionMarshalerFactory,
        LiteralUnionUnmarshaler,
        LiteralUnionUnmarshalerFactory,
    )

    from .composite.unions.primitives import (  # noqa
        PrimitiveUnionMarshaler,
        PrimitiveUnionMarshalerFactory,
        PrimitiveUnionUnmarshaler,
        PrimitiveUnionUnmarshalerFactory,
    )

    from .composite.wrapped import (  # noqa
        WrappedMarshaler,
        WrappedUnmarshaler,
    )

    from .factories.method import (  # noqa
        MarshalerFactoryMethodClass,
        UnmarshalerFactoryMethodClass,
    )

    from .factories.filtered import (  # noqa
        FilteredMarshalerFactory,
        FilteredUnmarshalerFactory,
    )

    from .factories.lazy import (  # noqa
        LazyMarshalerFactory,
        LazyUnmarshalerFactory,
    )

    from .factories.multi import (  # noqa
        MultiMarshalerFactory,
        MultiUnmarshalerFactory,
    )

    from .factories.typemap import (  # noqa
        TypeMapMarshalerFactory,
        TypeMapUnmarshalerFactory,
    )

    from .factories.vias import (  # noqa
        ViaConfigMarshalerFactory,
        ViaConfigUnmarshalerFactory,

        ViaMetadataMarshalerFactory,
        ViaMetadataUnmarshalerFactory,
    )

    from .objects.dataclasses import (  # noqa
        DataclassFactory,
        DataclassMarshalerFactory,
        DataclassUnmarshalerFactory,

        get_dataclass_field_infos,
        get_dataclass_object_spec,
        get_dataclass_options,
    )

    from .objects.api import (  # noqa
        FieldOptions,
        ObjectOptions,
        ObjectSpecials,
    )

    from .objects.helpers import (  # noqa
        update_field_options,
        update_object_options,
        dc_field_options,
    )

    from .objects.infos import (  # noqa
        FieldInfo,
        FieldInfos,
    )

    from .objects.marshal import (  # noqa
        ObjectMarshaler,
        ObjectMarshalerFactory,
        SimpleObjectMarshalerFactory,
    )

    from .objects.namedtuples import (  # noqa
        NamedtupleFactory,
        NamedtupleMarshalerFactory,
        NamedtupleUnmarshalerFactory,

        get_namedtuple_field_infos,
    )

    from .objects.specs import (  # noqa
        ObjectSpec,
    )

    from .objects.unmarshal import (  # noqa
        ObjectUnmarshaler,
        ObjectUnmarshalerFactory,
        SimpleObjectUnmarshalerFactory,
    )

    from .polymorphism.api import (  # noqa
        PolymorphismTagError,
        PolymorphismSuffixError,
        PolymorphismSubtypeError,

        TypeTagging,
        WrapperTypeTagging,
        FieldTypeTagging,

        SuffixStripping,

        SubtypeInfo,
        SubtypeInfos,
        Polymorphism,

        polymorphism_from_subtypes,
        polymorphism_from_subclasses,

        SubtypeConfig,

        set_polymorphic_from_subclasses,
    )

    from .polymorphism.manifests import (  # noqa
        SubtypeManifest,
    )

    from .polymorphism.marshal import (  # noqa
        PolymorphismMarshaler,
        PolymorphismMarshalerFactory,
        PolymorphismSpecMarshalerFactory,
        make_polymorphism_marshaler,
    )

    from .polymorphism.metadata import (  # noqa
        PolymorphismMetadataFactory,
        PolymorphismMetadataUnionFactory,
    )

    from .polymorphism.resolving import (  # noqa
        resolve_polymorphism,
    )

    from .polymorphism.specs import (  # noqa
        SubtypeSource,
        ExplicitSubtypeSource,
        SubclassesSubtypeSource,
        ConfigSubtypeSource,
        ManifestSubtypeSource,

        PolymorphismSpec,
    )

    from .polymorphism.standard import (  # noqa
        standard_polymorphism_factories,
    )

    from .polymorphism.unmarshal import (  # noqa
        PolymorphismUnmarshaler,
        PolymorphismUnmarshalerFactory,
        PolymorphismSpecUnmarshalerFactory,
        make_polymorphism_unmarshaler,
    )

    from .singular.api import (  # noqa
        PRIMITIVE_TYPES,
    )

    from .singular.base64 import (  # noqa
        Base64MarshalerUnmarshaler,

        BASE64_MARSHALER_FACTORY,
        BASE64_UNMARSHALER_FACTORY,
    )

    from .singular.enums import (  # noqa
        EnumNameMarshaler,
        EnumNameUnmarshaler,

        EnumValueMarshaler,
        EnumValueUnmarshaler,

        EnumMode,
        EnumMarshalerFactory,
        EnumUnmarshalerFactory,
    )

    from .singular.primitives import (  # noqa
        PrimitiveMarshalerUnmarshaler,
        PRIMITIVE_MARSHALER_FACTORY,
        PRIMITIVE_UNMARSHALER_FACTORY,
    )

    from .standard.api import (  # noqa
        StandardMarshalerFactories,
        StandardUnmarshalerFactories,
    )

    from .standard.defaults import (  # noqa
        DEFAULT_STANDARD_FACTORIES,
    )

    from .standard.factories import (  # noqa
        StandardMarshalerFactory,
        StandardUnmarshalerFactory,

        new_standard_marshaler_factory,
        new_standard_unmarshaler_factory,
    )

    from .standard.install import (  # noqa
        install_standard_factories,
    )

    from .trivial.any import (  # noqa
        AnyMarshalerUnmarshaler,

        ANY_MARSHALER_UNMARSHALER,
        ANY_MARSHALER_FACTORY,
        ANY_UNMARSHALER_FACTORY,
    )

    from .trivial.const import (  # noqa
        ConstMarshaler,
        ConstUnmarshaler,
    )

    from .trivial.forbidden import (  # noqa
        ForbiddenMarshalerUnmarshaler,

        ForbiddenTypeMarshalerFactory,
        ForbiddenTypeMarshalerFactoryUnmarshalerFactory,
        ForbiddenTypeUnmarshalerFactory,
    )

    from .trivial.nop import (  # noqa
        NopMarshalerUnmarshaler,

        NOP_MARSHALER_UNMARSHALER,
    )

    from .typedvalues.collections import (  # noqa
        build_typed_values_marshaler,
        build_typed_values_unmarshaler,
    )

    from .globals import (  # noqa
        global_config_registry,
        global_runtime,

        global_marshaling,

        marshal,
        unmarshal,

        register_global_lazy_init,
        register_global_module_import,
    )
