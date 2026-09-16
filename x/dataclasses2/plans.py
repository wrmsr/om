import dataclasses as dc
import typing as ta

from omcore import check
from omcore.dataclasses._internals import STD_POST_INIT_NAME
from omcore.dataclasses.impl.concerns.copy import CopyPlan
from omcore.dataclasses.impl.concerns.eq import EqPlan
from omcore.dataclasses.impl.concerns.fields import InitFields
from omcore.dataclasses.impl.concerns.fields import InstanceFields
from omcore.dataclasses.impl.concerns.frozen import FrozenPlan
from omcore.dataclasses.impl.concerns.frozen import check_frozen_bases
from omcore.dataclasses.impl.concerns.hash import HASH_ACTIONS
from omcore.dataclasses.impl.concerns.hash import HashPlan
from omcore.dataclasses.impl.concerns.hash import _raise_hash_action_exception
from omcore.dataclasses.impl.concerns.init import InitPlan
from omcore.dataclasses.impl.concerns.mro import MroDict
from omcore.dataclasses.impl.concerns.order import ORDER_NAME_OP_PAIRS
from omcore.dataclasses.impl.concerns.order import OrderPlan
from omcore.dataclasses.impl.concerns.override import OverridePlan
from omcore.dataclasses.impl.concerns.repr import ReprPlan
from omcore.dataclasses.impl.generation.base import Generator
from omcore.dataclasses.impl.generation.base import PlanResult
from omcore.dataclasses.impl.generation.idents import SELF_IDENT
from omcore.dataclasses.impl.generation.ops import OpRef
from omcore.dataclasses.impl.processing.base import ProcessingContext
from omcore.dataclasses.inspect import FieldsInspection
from omcore.dataclasses.specs import CoerceFn
from omcore.dataclasses.specs import DefaultFactory
from omcore.dataclasses.specs import FieldSpec
from omcore.dataclasses.specs import FieldType
from omcore.dataclasses.specs import InitFn
from omcore.dataclasses.specs import ValidateFn


##


class CopyGenerator(Generator[CopyPlan]):
    def plan(self, ctx: ProcessingContext) -> PlanResult[CopyPlan] | None:
        if '__copy__' in ctx.cls.__dict__:
            return None

        return PlanResult(CopyPlan(
            tuple(f.name for f in ctx.cs.fields if f.field_type is not FieldType.CLASS_VAR),
        ))


class EqGenerator(Generator[EqPlan]):
    def plan(self, ctx: ProcessingContext) -> PlanResult[EqPlan] | None:
        if not ctx.cs.eq or '__eq__' in ctx.cls.__dict__:
            return None

        return PlanResult(EqPlan(
            tuple(f.name for f in ctx[InstanceFields] if f.compare),
        ))


class FrozenGenerator(Generator[FrozenPlan]):
    def plan(self, ctx: ProcessingContext) -> PlanResult[FrozenPlan] | None:
        check_frozen_bases(ctx.cls, ctx.cs.frozen)

        if not ctx.cs.frozen:
            return None

        if issubclass(ctx.cls, BaseException):
            raise TypeError('cannot use frozen=True with subclass of BaseException')

        return PlanResult(FrozenPlan(
            fields=tuple(f.name for f in ctx.cs.fields),
            allow_dynamic_dunder_attrs=ctx.cs.allow_dynamic_dunder_attrs,
        ))


class HashGenerator(Generator[HashPlan]):
    def plan(self, ctx: ProcessingContext) -> PlanResult[HashPlan] | None:
        class_hash = ctx.cls.__dict__.get('__hash__', dc.MISSING)
        has_explicit_hash = not (class_hash is dc.MISSING or (class_hash is None and '__eq__' in ctx.cls.__dict__))

        action = HASH_ACTIONS[(
            bool(ctx.cs.unsafe_hash),
            bool(ctx.cs.eq),
            bool(ctx.cs.frozen),
            has_explicit_hash,
        )]

        if action == 'set_none':
            return PlanResult(HashPlan(action))  # noqa

        elif action == 'exception':
            _raise_hash_action_exception(ctx.cls)

        elif action == 'add':
            fields = tuple(
                f.name
                for f in ctx[InstanceFields]
                if (f.compare if f.hash is None else f.hash)
            )

            return PlanResult(HashPlan(
                'add',
                fields=fields,
                cache=ctx.cs.cache_hash,
            ))

        elif action is None:
            return None

        else:
            raise ValueError(action)


class InitGenerator(Generator[InitPlan]):
    def _plan_field(
            self,
            ctx: ProcessingContext,
            i: int,
            f: FieldSpec,
            ann: ta.Any,
            orm: dict,
    ) -> InitPlan.Field:
        ref_gen = OpRef.numbered(len(ctx.cs.fields))

        ann_ref: OpRef = ref_gen('init.fields.{i}.annotation', i)
        orm[ann_ref] = ann

        default_ref: OpRef[ta.Any] | None = None
        default_factory_ref: OpRef[ta.Any] | None = None
        if f.default.present:
            dfl = f.default.must()
            if isinstance(dfl, DefaultFactory):
                default_factory_ref = ref_gen('init.fields.{i}.default_factory', i)
                orm[default_factory_ref] = dfl.fn
            else:
                default_ref = ref_gen('init.fields.{i}.default', i)
                orm[default_ref] = dfl

        coerce: bool | OpRef[CoerceFn] | None = None
        if isinstance(f.coerce, bool):
            coerce = f.coerce
        elif f.coerce is not None:
            coerce = ref_gen('init.fields.{i}.coerce', i)
            orm[coerce] = f.coerce

        validate_ref: OpRef[ValidateFn] | None = None
        if f.validate is not None:
            validate_ref = ref_gen('init.fields.{i}.validate', i)
            orm[validate_ref] = f.validate

        check_type_ref: OpRef[type | tuple[type, ...]] | None = None
        if f.check_type is not None and f.check_type is not False:
            check_type_arg: ta.Any
            if isinstance(f.check_type, tuple):
                check_type_arg = tuple(type(None) if e is None else check.isinstance(e, type) for e in f.check_type)
            elif isinstance(f.check_type, type):
                check_type_arg = f.check_type
            elif f.check_type is True:
                check_type_arg = f.annotation
            else:
                raise TypeError(f.check_type)
            check_type_ref = ref_gen('init.fields.{i}.check_type', i)
            orm[check_type_ref] = check_type_arg

        return InitPlan.Field(
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

    def plan(self, ctx: ProcessingContext) -> PlanResult[InitPlan] | None:
        if '__init__' in ctx.cls.__dict__ or not ctx.cs.init:
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

        if ctx.cs.generic_init:
            gr_field_anns = ctx[FieldsInspection].generic_replaced_field_annotations
            get_field_ann = lambda f: gr_field_anns[f.name]
        else:
            get_field_ann = lambda f: f.annotation

        orm: dict = {}

        plan_fields: list[InitPlan.Field] = []
        for i, f in enumerate(ctx.cs.fields):
            plan_fields.append(self._plan_field(
                ctx,
                i,
                f,
                get_field_ann(f),
                orm,
            ))

        mro_v_ids = set(map(id, ctx[MroDict].values()))
        props_by_fget_id = {
            id(v.fget): v
            for v in ctx[MroDict].values()
            if isinstance(v, property)
               and v.fget is not None
        }

        init_fns = ctx.cs.init_fns or []
        init_fn_refs: list[OpRef[InitFn]] = []
        init_fn_ref_gen = OpRef.numbered(len(init_fns))
        for i, init_fn in enumerate(init_fns):
            if (obj_id := id(init_fn)) not in mro_v_ids and obj_id in props_by_fget_id:
                init_fn = props_by_fget_id[obj_id].__get__
            elif isinstance(init_fn, property):
                init_fn = init_fn.__get__
            init_fn_ref: OpRef = init_fn_ref_gen('init.init_fns.{i}', i)
            orm[init_fn_ref] = init_fn
            init_fn_refs.append(init_fn_ref)

        validate_fns = ctx.cs.validate_fns or []
        validate_fn_refs: list[InitPlan.ValidateFnWithParams] = []
        validate_fn_ref_gen = OpRef.numbered(len(validate_fns))
        for i, validate_fn in enumerate(validate_fns):
            validate_fn_ref: OpRef = validate_fn_ref_gen('init.validate_fns.{i}', i)
            orm[validate_fn_ref] = validate_fn.fn
            validate_fn_refs.append(InitPlan.ValidateFnWithParams(
                fn=validate_fn_ref,
                params=tuple(validate_fn.params),
            ))

        post_init_params: tuple[str, ...] | None = None
        if hasattr(ctx.cls, STD_POST_INIT_NAME):
            post_init_params = tuple(f.name for f in init_fields.all if f.field_type is FieldType.INIT_VAR)

        return PlanResult(
            InitPlan(
                fields=tuple(plan_fields),

                self_param=SELF_IDENT if 'self' in ctx.cs.fields_by_name else 'self',
                std_params=tuple(f.name for f in init_fields.std),
                kw_only_params=tuple(f.name for f in init_fields.kw_only),

                frozen=ctx.cs.frozen,

                slots=ctx.cs.slots,

                post_init_params=post_init_params,

                init_fns=tuple(init_fn_refs),

                validate_fns=tuple(validate_fn_refs),
            ),
            orm,
        )


class OrderGenerator(Generator[OrderPlan]):
    def plan(self, ctx: ProcessingContext) -> PlanResult[OrderPlan] | None:
        if not ctx.cs.order:
            return None

        for name, _ in ORDER_NAME_OP_PAIRS:
            if name in ctx.cls.__dict__:
                raise TypeError(
                    f'Cannot overwrite attribute {name} in class {ctx.cls.__name__}. '
                    f'Consider using functools.total_ordering',
                )

        return PlanResult(OrderPlan(
            tuple(f.name for f in ctx[InstanceFields] if f.compare),
        ))


class OverrideGenerator(Generator[OverridePlan]):
    def plan(self, ctx: ProcessingContext) -> PlanResult[OverridePlan] | None:
        orm = {}

        flds: list[OverridePlan.Field] = []
        ifs = ctx[InstanceFields]
        r_g = OpRef.numbered(len(ifs))
        for i, f in enumerate(ifs):
            if not (f.override or ctx.cs.override):
                continue
            r: OpRef = r_g('override.fields.{i}.annotation', i)
            orm[r] = f.annotation
            flds.append(OverridePlan.Field(
                f.name,
                r,
            ))

        if not flds:
            return None

        return PlanResult(
            OverridePlan(
                tuple(flds),
                ctx.cs.frozen,
            ),
            orm,
        )


class ReprGenerator(Generator[ReprPlan]):
    def plan(self, ctx: ProcessingContext) -> PlanResult[ReprPlan] | None:
        if not ctx.cs.repr or '__repr__' in ctx.cls.__dict__:
            return None

        ifs = ctx[InitFields]
        fs: ta.Sequence[FieldSpec]
        if ctx.cs.terse_repr:
            # If terse repr will match init param order
            fs = [
                *[f for f in ifs.all if not f.kw_only],
                *[f for f in ifs.all if f.kw_only],
            ]
        else:
            # Otherwise default to dc.fields() order
            fs = sorted(ctx.cs.fields, key=lambda f: f.repr_priority or 0)

        orm = {}
        rfs: list[ReprPlan.Field] = []
        fnr_g = OpRef.numbered(len(fs))
        for i, f in enumerate(fs):
            if not (f.field_type is FieldType.INSTANCE and f.repr):
                continue

            fnr: OpRef | None = None
            if f.repr_fn is not None:
                fnr = fnr_g('repr.fns.{i}.fn', i)
                orm[fnr] = f.repr_fn

            rfs.append(ReprPlan.Field(
                name=f.name,
                kw_only=f in ifs.kw_only,
                fn=fnr,
            ))

        drf: OpRef | None = None
        if ctx.cs.default_repr_fn is not None:
            drf = OpRef(f'repr.default_fn')
            orm[drf] = ctx.cs.default_repr_fn

        return PlanResult(
            ReprPlan(
                fields=tuple(rfs),
                id=ctx.cs.repr_id,
                terse=ctx.cs.terse_repr,
                default_fn=drf,
            ),
            orm,
        )
