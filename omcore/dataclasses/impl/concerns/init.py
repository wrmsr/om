"""
TODO:
 - ensure all 'init' fields work - non-instance
 - special case 'None' default, most common
"""
import dataclasses as dc
import itertools
import typing as ta

from .... import check
from ..._internals import STD_POST_INIT_NAME
from ...inspect import FieldsInspection
from ...specs import CoerceFn
from ...specs import DefaultFactory
from ...specs import FieldSpec
from ...specs import FieldType
from ...specs import InitFn
from ...specs import ValidateFn
from ..generation.base import Generation
from ..generation.base import Generator
from ..generation.globals import FIELD_FN_VALIDATION_ERROR_GLOBAL
from ..generation.globals import FIELD_TYPE_VALIDATION_ERROR_GLOBAL
from ..generation.globals import FN_VALIDATION_ERROR_GLOBAL
from ..generation.globals import HAS_DEFAULT_FACTORY_GLOBAL
from ..generation.globals import ISINSTANCE_GLOBAL
from ..generation.globals import NONE_GLOBAL
from ..generation.idents import SELF_IDENT
from ..generation.ops import AddMethodOp
from ..generation.ops import OpRef
from ..generation.ops import Ref
from ..generation.ops import add_ref
from ..generation.registry import register_generator_type
from ..generation.utils import SetattrSrcBuilder
from ..generation.values import ContextVal
from ..generation.values import Item
from ..generation.values import SpecVal
from ..generation.values import Val
from ..generation.values import ValOp
from ..processing.base import ProcessingContext
from ..processing.registry import register_processing_context_item_factory
from .fields import InitFields
from .mro import MroDict


##


InitGenericAnnotations = ta.NewType('InitGenericAnnotations', ta.Mapping[str, ta.Any])


@register_processing_context_item_factory(InitGenericAnnotations)
def _init_generic_annotations(ctx: ProcessingContext) -> InitGenericAnnotations:
    return InitGenericAnnotations(ctx[FieldsInspection].generic_replaced_field_annotations)


InitCheckTypes = ta.NewType('InitCheckTypes', tuple[ta.Any, ...])


@register_processing_context_item_factory(InitCheckTypes)
def _init_check_types(ctx: ProcessingContext) -> InitCheckTypes:
    values: list[ta.Any] = []
    for f in ctx.cs.fields:
        ct = f.check_type
        value: ta.Any
        if ct is None or ct is False:
            value = None
        elif isinstance(ct, tuple):
            value = tuple(type(None) if e is None else check.isinstance(e, type) for e in ct)
        elif isinstance(ct, type):
            value = ct
        elif ct is True:
            value = f.annotation
        else:
            raise TypeError(ct)
        values.append(value)
    return InitCheckTypes(tuple(values))


@dc.dataclass(frozen=True)
class InitFunctions:
    values: tuple[ta.Any, ...]
    kinds: tuple[str, ...]


@register_processing_context_item_factory(InitFunctions)
def _init_functions(ctx: ProcessingContext) -> InitFunctions:
    init_fns = ctx.cs.init_fns or ()
    if not init_fns:
        return InitFunctions((), ())

    mro_v_ids = set(map(id, ctx[MroDict].values()))
    props_by_fget_id = {
        id(v.fget): v
        for v in ctx[MroDict].values()
        if isinstance(v, property) and v.fget is not None
    }
    values: list[ta.Any] = []
    kinds = []
    for fn in init_fns:
        if (obj_id := id(fn)) not in mro_v_ids and obj_id in props_by_fget_id:
            values.append(props_by_fget_id[obj_id].__get__)
            kinds.append('getter')
        elif isinstance(fn, property):
            values.append(fn.__get__)
            kinds.append('property')
        else:
            values.append(fn)
            kinds.append('callable')
    return InitFunctions(tuple(values), tuple(kinds))


##


@dc.dataclass(frozen=True)
class _InitField:
    name: str
    annotation: OpRef[ta.Any]

    default: OpRef[ta.Any] | None
    default_factory: OpRef[ta.Any] | None

    init: bool
    override: bool
    field_type: FieldType

    coerce: bool | OpRef[CoerceFn] | None
    validate: OpRef[ValidateFn] | None
    check_type: OpRef[type | tuple[type, ...]] | None


@dc.dataclass(frozen=True)
class _InitCacheKey:
    has_own_init: bool
    has_post_init: bool
    init_func_kinds: tuple[str, ...]


@register_generator_type
class InitGenerator(Generator):
    cache_version = 2
    cache_schema = (_InitCacheKey, _InitField)

    def cache_key(self, ctx: ProcessingContext) -> _InitCacheKey:
        has_own_init = '__init__' in ctx.cls.__dict__
        return _InitCacheKey(
            has_own_init,
            hasattr(ctx.cls, STD_POST_INIT_NAME),
            ctx[InitFunctions].kinds if ctx.cs.init and not has_own_init else (),
        )

    def _prepare_field(
            self,
            ctx: ProcessingContext,
            i: int,
            f: FieldSpec,
            ann: Val,
            orm: dict,
    ) -> _InitField:
        ref_gen = OpRef.numbered(len(ctx.cs.fields))

        ann_ref: OpRef = ref_gen('init.fields.{i}.annotation', i)
        orm[ann_ref] = ann

        default_ref: OpRef[ta.Any] | None = None
        default_factory_ref: OpRef[ta.Any] | None = None
        if f.default.present:
            dfl = f.default.must()
            if isinstance(dfl, DefaultFactory):
                default_factory_ref = ref_gen('init.fields.{i}.default_factory', i)
                orm[default_factory_ref] = SpecVal(('fields', i, 'default', ValOp.MUST, 'fn'))
            else:
                default_ref = ref_gen('init.fields.{i}.default', i)
                orm[default_ref] = SpecVal(('fields', i, 'default', ValOp.MUST))

        coerce: bool | OpRef[CoerceFn] | None = None
        if isinstance(f.coerce, bool):
            coerce = f.coerce
        elif f.coerce is not None:
            coerce = ref_gen('init.fields.{i}.coerce', i)
            orm[coerce] = SpecVal(('fields', i, 'coerce'))

        validate_ref: OpRef[ValidateFn] | None = None
        if f.validate is not None:
            validate_ref = ref_gen('init.fields.{i}.validate', i)
            orm[validate_ref] = SpecVal(('fields', i, 'validate'))

        check_type_ref: OpRef[type | tuple[type, ...]] | None = None
        if f.check_type is not None and f.check_type is not False:
            ctx[InitCheckTypes]  # noqa
            check_type_ref = ref_gen('init.fields.{i}.check_type', i)
            orm[check_type_ref] = ContextVal.of(InitCheckTypes, (i,))

        return _InitField(
            name=f.name,
            annotation=ann_ref,

            default=default_ref,
            default_factory=default_factory_ref,

            init=f.init,

            override=f.override or ctx.cs.override,

            field_type=f.field_type,

            coerce=coerce,
            validate=validate_ref,

            check_type=check_type_ref,
        )

    def generate(self, ctx: ProcessingContext) -> Generation | None:
        cache_key = self.cache_key(ctx)
        if cache_key.has_own_init or not ctx.cs.init:
            return None

        init_fields = ctx[InitFields]
        seen_default = None
        for f in init_fields.std:
            if not f.init:
                continue
            if f.default.present:
                seen_default = f
            elif seen_default:
                raise TypeError(f'non-default argument {f.name!r} follows default argument {seen_default.name!r}')

        get_field_ann: ta.Callable[[FieldSpec], Val]
        if ctx.cs.generic_init:
            ctx[InitGenericAnnotations]  # noqa
            get_field_ann = lambda f: ContextVal.of(InitGenericAnnotations, (Item(f.name),))
        else:
            get_field_ann = lambda f: SpecVal(('fields', ctx.cs.field_indexes_by_name[f.name], 'annotation'))

        orm: dict = {}

        fields: list[_InitField] = []
        for i, f in enumerate(ctx.cs.fields):
            fields.append(self._prepare_field(
                ctx,
                i,
                f,
                get_field_ann(f),
                orm,
            ))

        init_fns = ctx.cs.init_fns or []
        init_fn_refs: list[OpRef[InitFn]] = []
        init_fn_ref_gen = OpRef.numbered(len(init_fns))
        for i in range(len(init_fns)):
            init_fn_ref: OpRef = init_fn_ref_gen('init.init_fns.{i}', i)
            orm[init_fn_ref] = ContextVal.of(InitFunctions, ('values', i))
            init_fn_refs.append(init_fn_ref)

        validate_fns = ctx.cs.validate_fns or []
        validate_fn_refs: list[tuple[OpRef[ValidateFn], tuple[str, ...]]] = []
        validate_fn_ref_gen = OpRef.numbered(len(validate_fns))
        for i, validate_fn in enumerate(validate_fns):
            validate_fn_ref: OpRef = validate_fn_ref_gen('init.validate_fns.{i}', i)
            orm[validate_fn_ref] = SpecVal(('validate_fns', i, 'fn'))
            validate_fn_refs.append((validate_fn_ref, tuple(validate_fn.params)))

        post_init_params: tuple[str, ...] | None = None
        if cache_key.has_post_init:
            post_init_params = tuple(f.name for f in init_fields.all if f.field_type is FieldType.INIT_VAR)

        self_param = SELF_IDENT if 'self' in ctx.cs.fields_by_name else 'self'
        refs: set[Ref] = set()

        fields_by_name = {f.name: f for f in fields}

        # proto

        params: list[str] = []
        seen_kw_only = False
        for fn, kw_only in itertools.chain(
            [(f.name, False) for f in init_fields.std],
            [(f.name, True) for f in init_fields.kw_only],
        ):
            pf = fields_by_name[fn]
            if kw_only:
                if not seen_kw_only:
                    params.append('*')
                    seen_kw_only = True
            elif seen_kw_only:
                raise TypeError(f'non-keyword-only argument {pf.name!r} follows keyword-only argument(s)')

            p = f'{pf.name}: {add_ref(pf.annotation, refs).ident()}'

            if pf.default_factory is not None:
                check.none(pf.default)
                p += f' = {add_ref(HAS_DEFAULT_FACTORY_GLOBAL, refs).ident}'
            elif pf.default is not None:
                check.none(pf.default_factory)
                p += f' = {add_ref(pf.default, refs).ident()}'

            params.append(p)

        proto_lines = [
            f'def __init__(',
            f'    {self_param},',
            *[
                f'    {p},'
                for p in params
            ],
            f') -> {add_ref(NONE_GLOBAL, refs).ident}:',
        ]

        # body

        lines = []

        # defaults

        values: dict[str, str] = {
            self_param: self_param,
        }

        for pf in fields:
            if pf.default_factory is not None:
                check.none(pf.default)
                refs.add(pf.default_factory)
                if pf.init:
                    lines.extend([
                        f'    if {pf.name} is {add_ref(HAS_DEFAULT_FACTORY_GLOBAL, refs).ident}:',
                        f'        {pf.name} = {pf.default_factory.ident()}()',
                    ])
                else:
                    lines.append(
                        f'    {pf.name} = {pf.default_factory.ident()}()',
                    )
                values[pf.name] = pf.name

            elif pf.init:
                if pf.default is not None:
                    check.none(pf.default_factory)
                    values[pf.name] = pf.name

                else:
                    values[pf.name] = pf.name

            elif ctx.cs.slots and pf.default is not None:
                lines.append(
                    f'    {pf.name} = {add_ref(pf.default, refs).ident()}',
                )
                values[pf.name] = pf.name

        # coercion

        for pf in fields:
            if isinstance(pf.coerce, bool) and pf.coerce:
                lines.append(
                    f'    {pf.name} = {pf.annotation.ident()}({values[pf.name]})',
                )
                values[pf.name] = pf.name
            elif isinstance(pf.coerce, OpRef):
                lines.append(
                    f'    {pf.name} = {add_ref(pf.coerce, refs).ident()}({values[pf.name]})',
                )
                values[pf.name] = pf.name

        # field validation

        for pf in fields:
            if pf.check_type is None:
                continue
            refs.add(pf.check_type)
            lines.extend([
                f'    if not {add_ref(ISINSTANCE_GLOBAL, refs).ident}({values[pf.name]}, {pf.check_type.ident()}): ',
                f'        raise {add_ref(FIELD_TYPE_VALIDATION_ERROR_GLOBAL, refs).ident}(',
                f'            obj={self_param},',
                f'            type={pf.check_type.ident()},',
                f'            field={pf.name!r},',
                f'            value={values[pf.name]},',
                f'        )',
            ])

        for pf in fields:
            if pf.validate is None:
                continue
            refs.add(pf.validate)
            lines.extend([
                f'    if not {pf.validate.ident()}({values[pf.name]}): ',
                f'        raise {add_ref(FIELD_FN_VALIDATION_ERROR_GLOBAL, refs).ident}(',
                f'            obj={self_param},',
                f'            fn={pf.validate.ident()},',
                f'            field={pf.name!r},',
                f'            value={values[pf.name]},',
                f'        )',
            ])

        # setattr

        sab = SetattrSrcBuilder(
            object_ident=self_param,
        )
        for pf in fields:
            if pf.name not in values or pf.field_type != FieldType.INSTANCE:
                continue
            lines.extend([
                f'    {l}'
                for l in sab(
                    pf.name,
                    values[pf.name],
                    frozen=ctx.cs.frozen,
                    override=pf.override,
                )
            ])
        refs.update(sab.refs)

        # fn validation

        for vfn, vparams in validate_fn_refs:
            refs.add(vfn)
            if vparams:
                lines.extend([
                    f'    if not {vfn.ident()}(',
                    *[
                        f'        {values[p]},'
                        for p in vparams
                    ],
                    f'    ):',
                ])
            else:
                lines.append(
                    f'    if not {vfn.ident()}():',
                )
            lines.extend([
                f'        raise {add_ref(FN_VALIDATION_ERROR_GLOBAL, refs).ident}(',
                f'            obj={self_param},',
                f'            fn={vfn.ident()},',
                f'        )',
            ])

        # post-init

        if (pia := post_init_params) is not None:
            if pia:
                lines.extend([
                    f'    {self_param}.{STD_POST_INIT_NAME}(',
                    *[
                        f'        {values[p]},'
                        for p in pia
                    ],
                    f'    )',
                ])
            else:
                lines.append(
                    f'    {self_param}.{STD_POST_INIT_NAME}()',
                )

        for init_fn in init_fn_refs:
            lines.append(
                f'    {add_ref(init_fn, refs).ident()}({self_param})',
            )

        #

        if not lines:
            lines.append(
                '    pass',
            )

        return Generation([
            AddMethodOp(
                '__init__',
                '\n'.join([*proto_lines, *lines]),
                frozenset(refs),
            ),
        ], bindings=orm)
