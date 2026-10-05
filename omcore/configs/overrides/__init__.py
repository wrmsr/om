"""
Overrides for structured configs: small `PATH OP VALUE` statements (plus jq filters, for anything they can't express)
applied to the plain tree form of a config, bridging nested config dataclasses and flat commandline arguments.

  cfg = override_config(Config(), ['model.opt.lr=3e-4', 'layers[name=enc].dim=3', '/model.dropout'])

See the README for the grammar and its semantics.
"""
from ... import lang as _lang


with _lang.auto_proxy_init(globals()):
    ##

    from .applying import (  # noqa
        OverrideApplier,

        apply_overrides,
        load_override_file,
        own_tree,
    )

    from .args import (  # noqa
        OVERRIDE_DUMP_FORMATS,

        add_override_arguments,
    )

    from .dumping import (  # noqa
        OverrideDumpFormat,

        dump_overrides,
        dump_tree,
    )

    from .errors import (  # noqa
        OverrideError,
        OverrideFileError,
        OverrideJqError,
        OverrideOpError,
        OverridePathError,
        OverrideSyntaxError,
        OverrideValueError,
        UnhandledOverrideShapeError,
    )

    from .literals import (  # noqa
        RawList,
        RawMap,
        RawNode,
        RawScalar,

        guess_raw,
        guess_scalar,
        parse_raw_value,
    )

    from .marshal import (  # noqa
        ConfigOverrider,

        get_unmarshaler_shape,
        override_config,
    )

    from .ops import (  # noqa
        ConstOpValue,
        FileOpValue,
        OpValue,
        RawOpValue,

        JqOp,
        MergeOp,
        OverrideOp,
        RemoveOp,
        SetOp,
    )

    from .parsing import (  # noqa
        parse_override,
        parse_path,
    )

    from .paths import (  # noqa
        AppendSegment,
        IndexSegment,
        KeySegment,
        OverridePath,
        PathSegment,
        SelectSegment,

        render_path,
    )

    from .resolving import (  # noqa
        ValueResolver,
    )

    from .shapes import (  # noqa
        AnyShape,
        ChoiceShape,
        LazyShape,
        ListShape,
        MapShape,
        ObjectShape,
        OptionalShape,
        ScalarShape,
        Shape,
        TaggedShape,
        TupleShape,
        UnionShape,
        UnknownShape,
    )

    from .stepping import (  # noqa
        ShapeStep,

        step_shape,
    )
