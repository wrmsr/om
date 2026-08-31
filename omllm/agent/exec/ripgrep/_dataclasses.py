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
        "Plans(tup=(CopyPlan(fields=('long', 'is_switch', 'short', 'aliases', 'negated')), EqPlan(fields=('long', 'is_s"
        "witch', 'short', 'aliases', 'negated')), FrozenPlan(fields=('long', 'is_switch', 'short', 'aliases', 'negated'"
        "), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('long', 'is_switch', 'short', 'aliases', "
        "'negated'), cache=False), InitPlan(fields=(InitPlan.Field(name='long', annotation=OpRef(name='init.fields.0.an"
        "notation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coer"
        "ce=None, validate=None, check_type=None), InitPlan.Field(name='is_switch', annotation=OpRef(name='init.fields."
        "1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, "
        "coerce=None, validate=None, check_type=None), InitPlan.Field(name='short', annotation=OpRef(name='init.fields."
        "2.annotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, override=False, "
        "field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='aliases', an"
        "notation=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default'), default_factory="
        "None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), "
        "InitPlan.Field(name='negated', annotation=OpRef(name='init.fields.4.annotation'), default=OpRef(name='init.fie"
        "lds.4.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, "
        "validate=None, check_type=None)), self_param='self', std_params=('long', 'is_switch', 'short', 'aliases', 'neg"
        "ated'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), Rep"
        "rPlan(fields=(ReprPlan.Field(name='long', kw_only=False, fn=None), ReprPlan.Field(name='is_switch', kw_only=Fa"
        "lse, fn=None), ReprPlan.Field(name='short', kw_only=False, fn=None), ReprPlan.Field(name='aliases', kw_only=Fa"
        "lse, fn=None), ReprPlan.Field(name='negated', kw_only=False, fn=None)), id=False, terse=False, default_fn=None"
        ")))"
    ),
    plan_repr_sha1='8c34479354bba359d40bf9327b7a9cb50660e2e6',
    cls_names=(
        ('omllm.agent.exec.ripgrep.args.parsing', 'RgFlagSpec'),
    ),
)
def _process_dataclass__8c34479354bba359d40bf9327b7a9cb50660e2e6():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__3__default,
        __dataclass__init__fields__4__annotation,
        __dataclass__init__fields__4__default,
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
                long=self.long,
                is_switch=self.is_switch,
                short=self.short,
                aliases=self.aliases,
                negated=self.negated,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.long == other.long and
                self.is_switch == other.is_switch and
                self.short == other.short and
                self.aliases == other.aliases and
                self.negated == other.negated
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'long',
            'is_switch',
            'short',
            'aliases',
            'negated',
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
                self.long,
                self.is_switch,
                self.short,
                self.aliases,
                self.negated,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            long: __dataclass__init__fields__0__annotation,
            is_switch: __dataclass__init__fields__1__annotation,
            short: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            aliases: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            negated: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'long', long)
            __dataclass__object_setattr(self, 'is_switch', is_switch)
            __dataclass__object_setattr(self, 'short', short)
            __dataclass__object_setattr(self, 'aliases', aliases)
            __dataclass__object_setattr(self, 'negated', negated)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"long={self.long!r}")
            parts.append(f"is_switch={self.is_switch!r}")
            parts.append(f"short={self.short!r}")
            parts.append(f"aliases={self.aliases!r}")
            parts.append(f"negated={self.negated!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('flag', 'spelling', 'form', 'value', 'argv_index', 'value_argv_index', 'attached')"
        "), EqPlan(fields=('flag', 'spelling', 'form', 'value', 'argv_index', 'value_argv_index', 'attached')), FrozenP"
        "lan(fields=('flag', 'spelling', 'form', 'value', 'argv_index', 'value_argv_index', 'attached'), allow_dynamic_"
        "dunder_attrs=False), HashPlan(action='add', fields=('flag', 'spelling', 'form', 'value', 'argv_index', 'value_"
        "argv_index', 'attached'), cache=False), InitPlan(fields=(InitPlan.Field(name='flag', annotation=OpRef(name='in"
        "it.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType."
        "INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='spelling', annotation=OpRef(name="
        "'init.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldTy"
        "pe.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='form', annotation=OpRef(name='"
        "init.fields.2.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldTyp"
        "e.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='value', annotation=OpRef(name='"
        "init.fields.3.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldTyp"
        "e.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='argv_index', annotation=OpRef(n"
        "ame='init.fields.4.annotation'), default=None, default_factory=None, init=True, override=False, field_type=Fie"
        "ldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='value_argv_index', annotat"
        "ion=OpRef(name='init.fields.5.annotation'), default=None, default_factory=None, init=True, override=False, fie"
        "ld_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='attached', anno"
        "tation=OpRef(name='init.fields.6.annotation'), default=None, default_factory=None, init=True, override=False, "
        "field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('"
        "flag', 'spelling', 'form', 'value', 'argv_index', 'value_argv_index', 'attached'), kw_only_params=(), frozen=T"
        "rue, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='"
        "flag', kw_only=False, fn=None), ReprPlan.Field(name='spelling', kw_only=False, fn=None), ReprPlan.Field(name='"
        "form', kw_only=False, fn=None), ReprPlan.Field(name='value', kw_only=False, fn=None), ReprPlan.Field(name='arg"
        "v_index', kw_only=False, fn=None), ReprPlan.Field(name='value_argv_index', kw_only=False, fn=None), ReprPlan.F"
        "ield(name='attached', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='83c9a635d71aeaf233490a5aef2a633260bfd998',
    cls_names=(
        ('omllm.agent.exec.ripgrep.args.parsing', 'RgOption'),
    ),
)
def _process_dataclass__83c9a635d71aeaf233490a5aef2a633260bfd998():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__4__annotation,
        __dataclass__init__fields__5__annotation,
        __dataclass__init__fields__6__annotation,
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
                flag=self.flag,
                spelling=self.spelling,
                form=self.form,
                value=self.value,
                argv_index=self.argv_index,
                value_argv_index=self.value_argv_index,
                attached=self.attached,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.flag == other.flag and
                self.spelling == other.spelling and
                self.form == other.form and
                self.value == other.value and
                self.argv_index == other.argv_index and
                self.value_argv_index == other.value_argv_index and
                self.attached == other.attached
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'flag',
            'spelling',
            'form',
            'value',
            'argv_index',
            'value_argv_index',
            'attached',
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
                self.flag,
                self.spelling,
                self.form,
                self.value,
                self.argv_index,
                self.value_argv_index,
                self.attached,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            flag: __dataclass__init__fields__0__annotation,
            spelling: __dataclass__init__fields__1__annotation,
            form: __dataclass__init__fields__2__annotation,
            value: __dataclass__init__fields__3__annotation,
            argv_index: __dataclass__init__fields__4__annotation,
            value_argv_index: __dataclass__init__fields__5__annotation,
            attached: __dataclass__init__fields__6__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'flag', flag)
            __dataclass__object_setattr(self, 'spelling', spelling)
            __dataclass__object_setattr(self, 'form', form)
            __dataclass__object_setattr(self, 'value', value)
            __dataclass__object_setattr(self, 'argv_index', argv_index)
            __dataclass__object_setattr(self, 'value_argv_index', value_argv_index)
            __dataclass__object_setattr(self, 'attached', attached)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"flag={self.flag!r}")
            parts.append(f"spelling={self.spelling!r}")
            parts.append(f"form={self.form!r}")
            parts.append(f"value={self.value!r}")
            parts.append(f"argv_index={self.argv_index!r}")
            parts.append(f"value_argv_index={self.value_argv_index!r}")
            parts.append(f"attached={self.attached!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('value', 'argv_index')), EqPlan(fields=('value', 'argv_index')), FrozenPlan(fields"
        "=('value', 'argv_index'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('value', 'argv_ind"
        "ex'), cache=False), InitPlan(fields=(InitPlan.Field(name='value', annotation=OpRef(name='init.fields.0.annotat"
        "ion'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=No"
        "ne, validate=None, check_type=None), InitPlan.Field(name='argv_index', annotation=OpRef(name='init.fields.1.an"
        "notation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coer"
        "ce=None, validate=None, check_type=None)), self_param='self', std_params=('value', 'argv_index'), kw_only_para"
        "ms=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPl"
        "an.Field(name='value', kw_only=False, fn=None), ReprPlan.Field(name='argv_index', kw_only=False, fn=None)), id"
        "=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='09b6463293df552988e5dd4ed8d333c458054c3e',
    cls_names=(
        ('omllm.agent.exec.ripgrep.args.parsing', 'RgPositional'),
    ),
)
def _process_dataclass__09b6463293df552988e5dd4ed8d333c458054c3e():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
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
                value=self.value,
                argv_index=self.argv_index,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.value == other.value and
                self.argv_index == other.argv_index
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'value',
            'argv_index',
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
                self.value,
                self.argv_index,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            value: __dataclass__init__fields__0__annotation,
            argv_index: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'value', value)
            __dataclass__object_setattr(self, 'argv_index', argv_index)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"value={self.value!r}")
            parts.append(f"argv_index={self.argv_index!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('args', 'timeout_s')), EqPlan(fields=('args', 'timeout_s')), FrozenPlan(fields=('a"
        "rgs', 'timeout_s'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('args', 'timeout_s'), ca"
        "che=False), InitPlan(fields=(InitPlan.Field(name='args', annotation=OpRef(name='init.fields.0.annotation'), de"
        "fault=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, valid"
        "ate=None, check_type=None), InitPlan.Field(name='timeout_s', annotation=OpRef(name='init.fields.1.annotation')"
        ", default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False, field_type=Fie"
        "ldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('args',), kw_on"
        "ly_params=('timeout_s',), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), Repr"
        "Plan(fields=(ReprPlan.Field(name='args', kw_only=False, fn=None), ReprPlan.Field(name='timeout_s', kw_only=Tru"
        "e, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='d90876b1b65e9f406ac36b571296b6c423eb256c',
    cls_names=(
        ('omllm.agent.exec.ripgrep.tools.ripgrep', 'RipgrepToolParams'),
    ),
)
def _process_dataclass__d90876b1b65e9f406ac36b571296b6c423eb256c():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
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
                args=self.args,
                timeout_s=self.timeout_s,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.args == other.args and
                self.timeout_s == other.timeout_s
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'args',
            'timeout_s',
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
                self.args,
                self.timeout_s,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            args: __dataclass__init__fields__0__annotation,
            *,
            timeout_s: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'args', args)
            __dataclass__object_setattr(self, 'timeout_s', timeout_s)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"args={self.args!r}")
            parts.append(f"timeout_s={self.timeout_s!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
