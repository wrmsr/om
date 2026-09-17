"""Conservative structural keys. Opaque runtime bindings never participate in comparison or serialization."""
import dataclasses as dc
import hashlib
import operator
import types
import typing as ta

from .... import lang
from ....lite import reflect as lrf
from ...specs import ClassSpec
from ...specs import DefaultFactory
from ...specs import FieldSpec
from ..processing.base import ProcessingContext
from ..processing.registry import all_processing_context_item_factories
from ..processing.registry import ordered_processor_types
from .registry import all_generator_types


##


FORMAT_VERSION = 3


class UncacheableSpecError(Exception):
    pass


def literal_key(value: ta.Any) -> ta.Any:
    if type(value) in (str, int, bool, type(None)):
        return value
    if type(value) in (tuple, list):
        return tuple(literal_key(v) for v in value)
    if dc.is_dataclass(value):
        return tuple(getattr(value, f.name) for f in dc.fields(value))
    raise UncacheableSpecError(type(value))


@lang.cached_function
def _spec_getters() -> tuple[ta.Callable, ta.Callable]:
    # Everything not explicitly treated as opaque or projected below participates automatically. New unsupported
    # structural values disable fast caching instead of silently disappearing from the key.

    return tuple(  # type: ignore[return-value]
        operator.attrgetter(*[
            f.name
            for f in dc.fields(ty)
            if f.name not in special
        ])
        for ty, special in [
            (
                ClassSpec,
                {
                    'fields',
                    'metadata',
                    'default_repr_fn',
                    'init_fns',
                    'validate_fns',
                },
            ),
            (
                FieldSpec,
                {
                    'annotation',
                    'default',
                    'metadata',
                    'doc',
                    'coerce',
                    'validate',
                    'check_type',
                    'repr_fn',
                    'field_type',
                },
            ),
        ]
    )


def spec_key(cs: ClassSpec) -> tuple:
    get_class, get_field = _spec_getters()
    return (
        literal_key(get_class(cs)),
        tuple(
            (
                literal_key(get_field(f)),
                f.field_type.value,
                'missing' if not f.default.present else
                'factory' if isinstance(f.default.must(), DefaultFactory) else
                'value',
                f.coerce if isinstance(f.coerce, bool) or f.coerce is None else 'callable',
                f.validate is not None,
                f.check_type is not None and f.check_type is not False,
                f.repr_fn is not None,
            )
            for f in cs.fields
        ),
        cs.default_repr_fn is not None,
        len(cs.init_fns or ()),
        tuple(literal_key(v.params) for v in cs.validate_fns or ()),
    )


def _type_schema_repr(ty: ta.Any) -> str:
    if isinstance(ty, type):
        return f'{ty.__module__}.{ty.__qualname__}'

    elif ty is ta.Any:
        return 'typing.Any'

    elif lrf.is_optional_alias(ty):
        ety = lrf.get_optional_alias_arg(ty)
        return _type_schema_repr(ety) + ' | None'

    elif lrf.is_union_alias(ty):
        args = ta.get_args(ty)
        return ' | '.join(sorted(_type_schema_repr(a) for a in args))

    elif lrf.is_callable_alias(ty):
        ptys, rty = ta.get_args(ty)
        return (
            f'typing.Callable[['
            f'{"..." if isinstance(ptys, types.EllipsisType) else ", ".join(_type_schema_repr(a) for a in ptys)}], '
            f'{_type_schema_repr(rty)}]'
        )

    elif lrf.is_literal_type(ty):
        args = ta.get_args(ty)
        return f'typing.Literal[{", ".join(sorted(repr(a) for a in args))}]'

    elif lrf.is_new_type(ty):
        raise NotImplementedError

    elif lrf.is_generic_alias(ty):
        origin = ta.get_origin(ty)
        args = ta.get_args(ty)
        if origin is tuple and args and isinstance(args[-1], types.EllipsisType):
            return (
                f'{_type_schema_repr(origin)}['
                f'{", ".join(_type_schema_repr(a) for a in args[:-1])}, ...]'
            )
        else:
            return (
                f'{_type_schema_repr(origin)}['
                f'{", ".join(_type_schema_repr(a) for a in args)}]'
            )

    else:
        raise TypeError(ty)


def _schema(ty: type) -> tuple:
    return (
        f'{ty.__module__}.{ty.__qualname__}',
        tuple(
            (f.name, _type_schema_repr(f.type))
            for f in dc.fields(ty)
        ),
        tuple(
            _schema(v)
            for v in vars(ty).values()
            if isinstance(v, type) and dc.is_dataclass(v)
        ),
    )


@lang.cached_function
def implementation_key() -> str:
    stamp = (
        FORMAT_VERSION,
        _schema(ClassSpec),
        _schema(FieldSpec),
        tuple(
            (
                f'{g.__module__}.{g.__qualname__}',
                g.__dict__.get('cache_version'),
                tuple(_schema(t) for t in g.cache_schema),
            )
            for g in all_generator_types()
        ),
        tuple(
            f'{p.__module__}.{p.__qualname__}'
            for p in ordered_processor_types()
        ),
        tuple(sorted(
            k
            for k in all_processing_context_item_factories()
            if isinstance(k, str)
        )),
    )
    return hashlib.sha256(repr(stamp).encode()).hexdigest()


def processing_key(ctx: ProcessingContext) -> str | None:
    generators = all_generator_types()
    if any(g.__dict__.get('cache_version') is None for g in generators):
        return None
    try:
        spec = spec_key(ctx.cs)
        concerns = tuple(literal_key(g().cache_key(ctx)) for g in generators)
    except UncacheableSpecError:
        return None
    return repr((spec, concerns))
