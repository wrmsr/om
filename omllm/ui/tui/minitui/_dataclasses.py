# @om-generated
# type: ignore
# ruff: noqa
# flake8: noqa
import dataclasses
import reprlib
import types


##


REGISTRY = {}


def _register(**kwargs):
    def inner(fn):
        REGISTRY[kwargs['plan_repr']] = (kwargs, fn)
        return fn
    return inner


##


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('input', 'input_cached', 'output', 'reasoning')), EqPlan(fields=('input', 'input_c"
        "ached', 'output', 'reasoning')), FrozenPlan(fields=('input', 'input_cached', 'output', 'reasoning', '_SUFFIXES"
        "'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('input', 'input_cached', 'output', 'reas"
        "oning'), cache=False), InitPlan(fields=(InitPlan.Field(name='input', annotation=OpRef(name='init.fields.0.anno"
        "tation'), default=OpRef(name='init.fields.0.default'), default_factory=None, init=True, override=False, field_"
        "type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='input_cached', ann"
        "otation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=N"
        "one, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), I"
        "nitPlan.Field(name='output', annotation=OpRef(name='init.fields.2.annotation'), default=OpRef(name='init.field"
        "s.2.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, va"
        "lidate=None, check_type=None), InitPlan.Field(name='reasoning', annotation=OpRef(name='init.fields.3.annotatio"
        "n'), default=OpRef(name='init.fields.3.default'), default_factory=None, init=True, override=False, field_type="
        "FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='_SUFFIXES', annotation="
        "OpRef(name='init.fields.4.annotation'), default=OpRef(name='init.fields.4.default'), default_factory=None, ini"
        "t=True, override=False, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_type=None)), self_pa"
        "ram='self', std_params=(), kw_only_params=('input', 'input_cached', 'output', 'reasoning'), frozen=True, slots"
        "=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='input', kw"
        "_only=True, fn=None), ReprPlan.Field(name='input_cached', kw_only=True, fn=None), ReprPlan.Field(name='output'"
        ", kw_only=True, fn=None), ReprPlan.Field(name='reasoning', kw_only=True, fn=None)), id=False, terse=False, def"
        "ault_fn=None)))"
    ),
    plan_repr_sha1='cb783e8d0be2d3a68147e5991c73fe61f128969b',
    cls_names=(
        ('omllm.ui.tui.minitui.app', 'MinituiChatApp.Usage'),
    ),
)
def _process_dataclass__cb783e8d0be2d3a68147e5991c73fe61f128969b():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__default,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__3__default,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__object_setattr=object.__setattr__,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                input=self.input,
                input_cached=self.input_cached,
                output=self.output,
                reasoning=self.reasoning,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.input == other.input and
                self.input_cached == other.input_cached and
                self.output == other.output and
                self.reasoning == other.reasoning
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'input',
            'input_cached',
            'output',
            'reasoning',
            '_SUFFIXES',
        }

        def __setattr__(self, name, value):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot assign to field {name!r}")
            super(__class__, self).__setattr__(name, value)

        __dataclass__set_cls_attr(__class__, '__setattr__', __setattr__, 'raise', set_qualname=True)

        def __delattr__(self, name):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot delete field {name!r}")
            super(__class__, self).__delattr__(name)

        __dataclass__set_cls_attr(__class__, '__delattr__', __delattr__, 'raise', set_qualname=True)

        def __hash__(self):
            return hash((
                self.input,
                self.input_cached,
                self.output,
                self.reasoning,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            input: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            input_cached: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            output: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            reasoning: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'input', input)
            __dataclass__object_setattr(self, 'input_cached', input_cached)
            __dataclass__object_setattr(self, 'output', output)
            __dataclass__object_setattr(self, 'reasoning', reasoning)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"input={self.input!r}")
            parts.append(f"input_cached={self.input_cached!r}")
            parts.append(f"output={self.output!r}")
            parts.append(f"reasoning={self.reasoning!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('key', 'title', 'call_summary', 'detail', 'on_respond', 'on_cancel')), EqPlan(fiel"
        "ds=('key', 'title', 'call_summary', 'detail', 'on_respond', 'on_cancel')), FrozenPlan(fields=('key', 'title', "
        "'call_summary', 'detail', 'on_respond', 'on_cancel'), allow_dynamic_dunder_attrs=False), HashPlan(action='add'"
        ", fields=('key', 'title', 'call_summary', 'detail', 'on_respond', 'on_cancel'), cache=False), InitPlan(fields="
        "(InitPlan.Field(name='key', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=N"
        "one, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), I"
        "nitPlan.Field(name='title', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=N"
        "one, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), I"
        "nitPlan.Field(name='call_summary', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_fa"
        "ctory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=N"
        "one), InitPlan.Field(name='detail', annotation=OpRef(name='init.fields.3.annotation'), default=None, default_f"
        "actory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type="
        "None), InitPlan.Field(name='on_respond', annotation=OpRef(name='init.fields.4.annotation'), default=None, defa"
        "ult_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_"
        "type=None), InitPlan.Field(name='on_cancel', annotation=OpRef(name='init.fields.5.annotation'), default=OpRef("
        "name='init.fields.5.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE,"
        " coerce=None, validate=None, check_type=None)), self_param='self', std_params=('key', 'title', 'call_summary',"
        " 'detail', 'on_respond', 'on_cancel'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, ini"
        "t_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='key', kw_only=False, fn=None), ReprPlan.Fiel"
        "d(name='title', kw_only=False, fn=None), ReprPlan.Field(name='call_summary', kw_only=False, fn=None), ReprPlan"
        ".Field(name='detail', kw_only=False, fn=None), ReprPlan.Field(name='on_respond', kw_only=False, fn=None), Repr"
        "Plan.Field(name='on_cancel', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='2e87295db3f0cee81b20c79a1a6832fbcc6d0cc4',
    cls_names=(
        ('omllm.ui.tui.minitui.app', '_PermissionCardRequest'),
    ),
)
def _process_dataclass__2e87295db3f0cee81b20c79a1a6832fbcc6d0cc4():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__4__annotation,
        __dataclass__init__fields__5__annotation,
        __dataclass__init__fields__5__default,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__object_setattr=object.__setattr__,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                key=self.key,
                title=self.title,
                call_summary=self.call_summary,
                detail=self.detail,
                on_respond=self.on_respond,
                on_cancel=self.on_cancel,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.key == other.key and
                self.title == other.title and
                self.call_summary == other.call_summary and
                self.detail == other.detail and
                self.on_respond == other.on_respond and
                self.on_cancel == other.on_cancel
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'key',
            'title',
            'call_summary',
            'detail',
            'on_respond',
            'on_cancel',
        }

        def __setattr__(self, name, value):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot assign to field {name!r}")
            super(__class__, self).__setattr__(name, value)

        __dataclass__set_cls_attr(__class__, '__setattr__', __setattr__, 'raise', set_qualname=True)

        def __delattr__(self, name):
            if (
                type(self) is __class__
                or name in __dataclass___frozen_fields
            ):
                raise __dataclass__FrozenInstanceError(f"cannot delete field {name!r}")
            super(__class__, self).__delattr__(name)

        __dataclass__set_cls_attr(__class__, '__delattr__', __delattr__, 'raise', set_qualname=True)

        def __hash__(self):
            return hash((
                self.key,
                self.title,
                self.call_summary,
                self.detail,
                self.on_respond,
                self.on_cancel,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            key: __dataclass__init__fields__0__annotation,
            title: __dataclass__init__fields__1__annotation,
            call_summary: __dataclass__init__fields__2__annotation,
            detail: __dataclass__init__fields__3__annotation,
            on_respond: __dataclass__init__fields__4__annotation,
            on_cancel: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'title', title)
            __dataclass__object_setattr(self, 'call_summary', call_summary)
            __dataclass__object_setattr(self, 'detail', detail)
            __dataclass__object_setattr(self, 'on_respond', on_respond)
            __dataclass__object_setattr(self, 'on_cancel', on_cancel)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"key={self.key!r}")
            parts.append(f"title={self.title!r}")
            parts.append(f"call_summary={self.call_summary!r}")
            parts.append(f"detail={self.detail!r}")
            parts.append(f"on_respond={self.on_respond!r}")
            parts.append(f"on_cancel={self.on_cancel!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('title', 'call_summary', 'base_detail', 'card', 'ready_to_finalize', 'finalize_tim"
        "er')), EqPlan(fields=('title', 'call_summary', 'base_detail', 'card', 'ready_to_finalize', 'finalize_timer')),"
        " HashPlan(action='set_none', fields=None, cache=None), InitPlan(fields=(InitPlan.Field(name='title', annotatio"
        "n=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field"
        "_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='call_summary', an"
        "notation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override=False"
        ", field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='base_detai"
        "l', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override"
        "=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='card"
        "', annotation=OpRef(name='init.fields.3.annotation'), default=None, default_factory=None, init=True, override="
        "False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='ready"
        "_to_finalize', annotation=OpRef(name='init.fields.4.annotation'), default=OpRef(name='init.fields.4.default'),"
        " default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, c"
        "heck_type=None), InitPlan.Field(name='finalize_timer', annotation=OpRef(name='init.fields.5.annotation'), defa"
        "ult=OpRef(name='init.fields.5.default'), default_factory=None, init=True, override=False, field_type=FieldType"
        ".INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('title', 'call_summar"
        "y', 'base_detail', 'card', 'ready_to_finalize', 'finalize_timer'), kw_only_params=(), frozen=False, slots=Fals"
        "e, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='title', kw_only"
        "=False, fn=None), ReprPlan.Field(name='call_summary', kw_only=False, fn=None), ReprPlan.Field(name='base_detai"
        "l', kw_only=False, fn=None), ReprPlan.Field(name='card', kw_only=False, fn=None), ReprPlan.Field(name='ready_t"
        "o_finalize', kw_only=False, fn=None), ReprPlan.Field(name='finalize_timer', kw_only=False, fn=None)), id=False"
        ", terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='c06c191aa16baede8c0866b05bd1edf4dca7e072',
    cls_names=(
        ('omllm.ui.tui.minitui.app', '_ToolCardEntry'),
    ),
)
def _process_dataclass__c06c191aa16baede8c0866b05bd1edf4dca7e072():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__4__annotation,
        __dataclass__init__fields__4__default,
        __dataclass__init__fields__5__annotation,
        __dataclass__init__fields__5__default,
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                title=self.title,
                call_summary=self.call_summary,
                base_detail=self.base_detail,
                card=self.card,
                ready_to_finalize=self.ready_to_finalize,
                finalize_timer=self.finalize_timer,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.title == other.title and
                self.call_summary == other.call_summary and
                self.base_detail == other.base_detail and
                self.card == other.card and
                self.ready_to_finalize == other.ready_to_finalize and
                self.finalize_timer == other.finalize_timer
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            title: __dataclass__init__fields__0__annotation,
            call_summary: __dataclass__init__fields__1__annotation,
            base_detail: __dataclass__init__fields__2__annotation,
            card: __dataclass__init__fields__3__annotation,
            ready_to_finalize: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            finalize_timer: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            self.title = title
            self.call_summary = call_summary
            self.base_detail = base_detail
            self.card = card
            self.ready_to_finalize = ready_to_finalize
            self.finalize_timer = finalize_timer

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"title={self.title!r}")
            parts.append(f"call_summary={self.call_summary!r}")
            parts.append(f"base_detail={self.base_detail!r}")
            parts.append(f"card={self.card!r}")
            parts.append(f"ready_to_finalize={self.ready_to_finalize!r}")
            parts.append(f"finalize_timer={self.finalize_timer!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
