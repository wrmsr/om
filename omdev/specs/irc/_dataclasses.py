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
        "Plans(tup=(CopyPlan(fields=()), EqPlan(fields=()), FrozenPlan(fields=('FORMAT', 'REPLIES'), allow_dynamic_dund"
        "er_attrs=False), HashPlan(action='add', fields=(), cache=False), InitPlan(fields=(InitPlan.Field(name='FORMAT'"
        ", annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=T"
        "rue, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='REPLIE"
        "S', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_fa"
        "ctory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_type=N"
        "one)), self_param='self', std_params=(), kw_only_params=(), frozen=True, slots=False, post_init_params=None, i"
        "nit_fns=(), validate_fns=()), ReprPlan(fields=(), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='10e6634f8b4566f3738ee30728050f10b166e612',
    cls_names=(
        ('omdev.specs.irc.messages.base', 'Message'),
        ('omdev.specs.irc.messages.messages', 'AuthenticateMessage'),
        ('omdev.specs.irc.messages.messages', 'InfoMessage'),
        ('omdev.specs.irc.messages.messages', 'LeaveAllJoinMessage'),
        ('omdev.specs.irc.messages.messages', 'LinksMessage'),
        ('omdev.specs.irc.messages.messages', 'LusersMessage'),
        ('omdev.specs.irc.messages.messages', 'RehashMessage'),
        ('omdev.specs.irc.messages.messages', 'RestartMessage'),
    ),
)
def _process_dataclass__10e6634f8b4566f3738ee30728050f10b166e612():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__()  # noqa

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return True

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
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
            return hash(())

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
        ) -> __dataclass__None:
            pass

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            return f"{self.__class__.__qualname__}()"

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('name', 'params', 'unpack_params')), EqPlan(fields=('name', 'params', 'unpack_para"
        "ms')), FrozenPlan(fields=('name', 'params', 'unpack_params'), allow_dynamic_dunder_attrs=False), HashPlan(acti"
        "on='add', fields=('name', 'params', 'unpack_params'), cache=False), InitPlan(fields=(InitPlan.Field(name='name"
        "', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override="
        "False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='param"
        "s', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override"
        "=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='unpa"
        "ck_params', annotation=OpRef(name='init.fields.2.annotation'), default=OpRef(name='init.fields.2.default'), de"
        "fault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, chec"
        "k_type=None)), self_param='self', std_params=('name', 'params'), kw_only_params=('unpack_params',), frozen=Tru"
        "e, slots=False, post_init_params=None, init_fns=(OpRef(name='init.init_fns.0'),), validate_fns=()), ReprPlan(f"
        "ields=(ReprPlan.Field(name='name', kw_only=False, fn=None), ReprPlan.Field(name='params', kw_only=False, fn=No"
        "ne), ReprPlan.Field(name='unpack_params', kw_only=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='da94bfca5f0c76678ad107d9b800d7f934eade4b',
    cls_names=(
        ('omdev.specs.irc.messages.formats', 'MessageFormat'),
    ),
)
def _process_dataclass__da94bfca5f0c76678ad107d9b800d7f934eade4b():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default,
        __dataclass__init__init_fns__0,
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
                name=self.name,
                params=self.params,
                unpack_params=self.unpack_params,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.params == other.params and
                self.unpack_params == other.unpack_params
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'params',
            'unpack_params',
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
                self.name,
                self.params,
                self.unpack_params,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
            params: __dataclass__init__fields__1__annotation,
            *,
            unpack_params: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'params', params)
            __dataclass__object_setattr(self, 'unpack_params', unpack_params)
            __dataclass__init__init_fns__0(self)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"params={self.params!r}")
            parts.append(f"unpack_params={self.unpack_params!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('name', 'optional', 'arity')), EqPlan(fields=('name', 'optional', 'arity')), Froze"
        "nPlan(fields=('name', 'optional', 'arity'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=("
        "'name', 'optional', 'arity'), cache=False), InitPlan(fields=(InitPlan.Field(name='name', annotation=OpRef(name"
        "='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=True, field_type=FieldTy"
        "pe.INSTANCE, coerce=None, validate=OpRef(name='init.fields.0.validate'), check_type=None), InitPlan.Field(name"
        "='optional', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), d"
        "efault_factory=None, init=True, override=True, field_type=FieldType.INSTANCE, coerce=None, validate=None, chec"
        "k_type=None), InitPlan.Field(name='arity', annotation=OpRef(name='init.fields.2.annotation'), default=OpRef(na"
        "me='init.fields.2.default'), default_factory=None, init=True, override=True, field_type=FieldType.INSTANCE, co"
        "erce=None, validate=None, check_type=None)), self_param='self', std_params=('name', 'optional', 'arity'), kw_o"
        "nly_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), OverridePlan(fi"
        "elds=(OverridePlan.Field(name='name', annotation=OpRef(name='override.fields.0.annotation')), OverridePlan.Fie"
        "ld(name='optional', annotation=OpRef(name='override.fields.1.annotation')), OverridePlan.Field(name='arity', a"
        "nnotation=OpRef(name='override.fields.2.annotation'))), frozen=True), ReprPlan(fields=(ReprPlan.Field(name='na"
        "me', kw_only=False, fn=None), ReprPlan.Field(name='optional', kw_only=False, fn=None), ReprPlan.Field(name='ar"
        "ity', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='bd569b6a7bd869a1af0ec27be9b79b5c834e340f',
    cls_names=(
        ('omdev.specs.irc.messages.formats', 'MessageFormat.KwargParam'),
    ),
)
def _process_dataclass__bd569b6a7bd869a1af0ec27be9b79b5c834e340f():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__validate,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default,
        __dataclass__override__fields__0__annotation,
        __dataclass__override__fields__1__annotation,
        __dataclass__override__fields__2__annotation,
        __dataclass__FieldFnValidationError,  # noqa
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                name=self.name,
                optional=self.optional,
                arity=self.arity,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.optional == other.optional and
                self.arity == other.arity
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'optional',
            'arity',
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
                self.name,
                self.optional,
                self.arity,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
            optional: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            arity: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            if not __dataclass__init__fields__0__validate(name): 
                raise __dataclass__FieldFnValidationError(
                    obj=self,
                    fn=__dataclass__init__fields__0__validate,
                    field='name',
                    value=name,
                )
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['name'] = name
            __dataclass__self_dict['optional'] = optional
            __dataclass__self_dict['arity'] = arity

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__name():
            @__dataclass__property
            def name(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['name']

            return name

        setattr(__class__, 'name', __dataclass__property__name())

        def __dataclass__property__optional():
            @__dataclass__property
            def optional(__dataclass__self) -> __dataclass__override__fields__1__annotation:
                return __dataclass__self.__dict__['optional']

            return optional

        setattr(__class__, 'optional', __dataclass__property__optional())

        def __dataclass__property__arity():
            @__dataclass__property
            def arity(__dataclass__self) -> __dataclass__override__fields__2__annotation:
                return __dataclass__self.__dict__['arity']

            return arity

        setattr(__class__, 'arity', __dataclass__property__arity())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"optional={self.optional!r}")
            parts.append(f"arity={self.arity!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('text',)), EqPlan(fields=('text',)), FrozenPlan(fields=('text',), allow_dynamic_du"
        "nder_attrs=False), HashPlan(action='add', fields=('text',), cache=False), InitPlan(fields=(InitPlan.Field(name"
        "='text', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, ove"
        "rride=True, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='self', "
        "std_params=('text',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validat"
        "e_fns=()), OverridePlan(fields=(OverridePlan.Field(name='text', annotation=OpRef(name='override.fields.0.annot"
        "ation')),), frozen=True), ReprPlan(fields=(ReprPlan.Field(name='text', kw_only=False, fn=None),), id=False, te"
        "rse=False, default_fn=None)))"
    ),
    plan_repr_sha1='a329242462ab29a834510db46c94b1b088b539f7',
    cls_names=(
        ('omdev.specs.irc.messages.formats', 'MessageFormat.LiteralParam'),
    ),
)
def _process_dataclass__a329242462ab29a834510db46c94b1b088b539f7():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__override__fields__0__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                text=self.text,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.text == other.text
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'text',
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
                self.text,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            text: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['text'] = text

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__text():
            @__dataclass__property
            def text(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['text']

            return text

        setattr(__class__, 'text', __dataclass__property__text())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"text={self.text!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=()), EqPlan(fields=()), FrozenPlan(fields=(), allow_dynamic_dunder_attrs=False), Ha"
        "shPlan(action='add', fields=(), cache=False), InitPlan(fields=(), self_param='self', std_params=(), kw_only_pa"
        "rams=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(), i"
        "d=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='e1f7edfe11f2b721d6a656c46e698fedc95461bb',
    cls_names=(
        ('omdev.specs.irc.messages.formats', 'MessageFormat.Param'),
    ),
)
def _process_dataclass__e1f7edfe11f2b721d6a656c46e698fedc95461bb():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__()  # noqa

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return True

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        def __setattr__(self, name, value):
            if (
                type(self) is __class__
            ):
                raise __dataclass__FrozenInstanceError(f"cannot assign to field {name!r}")
            super(__class__, self).__setattr__(name, value)

        __dataclass__set_cls_attr(__class__, '__setattr__', __setattr__, 'raise', set_qualname=True)

        def __delattr__(self, name):
            if (
                type(self) is __class__
            ):
                raise __dataclass__FrozenInstanceError(f"cannot delete field {name!r}")
            super(__class__, self).__delattr__(name)

        __dataclass__set_cls_attr(__class__, '__delattr__', __delattr__, 'raise', set_qualname=True)

        def __hash__(self):
            return hash(())

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
        ) -> __dataclass__None:
            pass

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            return f"{self.__class__.__qualname__}()"

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('target',)), EqPlan(fields=('target',)), FrozenPlan(fields=('FORMAT', 'REPLIES', '"
        "target'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('target',), cache=False), InitPlan"
        "(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields.0.annotation'), default=None, defaul"
        "t_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_ty"
        "pe=None), InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name"
        "='init.fields.1.default'), default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coe"
        "rce=None, validate=None, check_type=None), InitPlan.Field(name='target', annotation=OpRef(name='init.fields.2."
        "annotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, override=True, fie"
        "ld_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('tar"
        "get',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), Ove"
        "rridePlan(fields=(OverridePlan.Field(name='target', annotation=OpRef(name='override.fields.0.annotation')),), "
        "frozen=True), ReprPlan(fields=(ReprPlan.Field(name='target', kw_only=False, fn=None),), id=False, terse=False,"
        " default_fn=None)))"
    ),
    plan_repr_sha1='37a36c791bfeb4ff6a400b95aba6b729d87c7dfa',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'AdminMessage'),
        ('omdev.specs.irc.messages.messages', 'MotdMessage'),
        ('omdev.specs.irc.messages.messages', 'VersionMessage'),
    ),
)
def _process_dataclass__37a36c791bfeb4ff6a400b95aba6b729d87c7dfa():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default,
        __dataclass__override__fields__0__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                target=self.target,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.target == other.target
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'target',
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
                self.target,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            target: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['target'] = target

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__target():
            @__dataclass__property
            def target(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['target']

            return target

        setattr(__class__, 'target', __dataclass__property__target())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"target={self.target!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('text',)), EqPlan(fields=('text',)), FrozenPlan(fields=('FORMAT', 'REPLIES', 'text"
        "'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('text',), cache=False), InitPlan(fields="
        "(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factor"
        "y=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_type=None)"
        ", InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.f"
        "ields.1.default'), default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None"
        ", validate=None, check_type=None), InitPlan.Field(name='text', annotation=OpRef(name='init.fields.2.annotation"
        "'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, override=True, field_type=Fi"
        "eldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('text',), kw_o"
        "nly_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), OverridePlan(fi"
        "elds=(OverridePlan.Field(name='text', annotation=OpRef(name='override.fields.0.annotation')),), frozen=True), "
        "ReprPlan(fields=(ReprPlan.Field(name='text', kw_only=False, fn=None),), id=False, terse=False, default_fn=None"
        ")))"
    ),
    plan_repr_sha1='a50fd29ff8190377436f259ba08228ac40dfe8d5',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'AwayMessage'),
    ),
)
def _process_dataclass__a50fd29ff8190377436f259ba08228ac40dfe8d5():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default,
        __dataclass__override__fields__0__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                text=self.text,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.text == other.text
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'text',
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
                self.text,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            text: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['text'] = text

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__text():
            @__dataclass__property
            def text(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['text']

            return text

        setattr(__class__, 'text', __dataclass__property__text())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"text={self.text!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('subcommand', 'capabilities')), EqPlan(fields=('subcommand', 'capabilities')), Fro"
        "zenPlan(fields=('FORMAT', 'REPLIES', 'subcommand', 'capabilities'), allow_dynamic_dunder_attrs=False), HashPla"
        "n(action='add', fields=('subcommand', 'capabilities'), cache=False), InitPlan(fields=(InitPlan.Field(name='FOR"
        "MAT', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, overri"
        "de=True, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='RE"
        "PLIES', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), defaul"
        "t_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_ty"
        "pe=None), InitPlan.Field(name='subcommand', annotation=OpRef(name='init.fields.2.annotation'), default=None, d"
        "efault_factory=None, init=True, override=True, field_type=FieldType.INSTANCE, coerce=None, validate=None, chec"
        "k_type=None), InitPlan.Field(name='capabilities', annotation=OpRef(name='init.fields.3.annotation'), default=N"
        "one, default_factory=None, init=True, override=True, field_type=FieldType.INSTANCE, coerce=None, validate=None"
        ", check_type=None)), self_param='self', std_params=('subcommand', 'capabilities'), kw_only_params=(), frozen=T"
        "rue, slots=False, post_init_params=None, init_fns=(), validate_fns=()), OverridePlan(fields=(OverridePlan.Fiel"
        "d(name='subcommand', annotation=OpRef(name='override.fields.0.annotation')), OverridePlan.Field(name='capabili"
        "ties', annotation=OpRef(name='override.fields.1.annotation'))), frozen=True), ReprPlan(fields=(ReprPlan.Field("
        "name='subcommand', kw_only=False, fn=None), ReprPlan.Field(name='capabilities', kw_only=False, fn=None)), id=F"
        "alse, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='ca392f075b0a4bf94fc3b61b96c601e6f4018e48',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'CapMessage'),
    ),
)
def _process_dataclass__ca392f075b0a4bf94fc3b61b96c601e6f4018e48():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__override__fields__0__annotation,
        __dataclass__override__fields__1__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                subcommand=self.subcommand,
                capabilities=self.capabilities,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.subcommand == other.subcommand and
                self.capabilities == other.capabilities
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'subcommand',
            'capabilities',
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
                self.subcommand,
                self.capabilities,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            subcommand: __dataclass__init__fields__2__annotation,
            capabilities: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['subcommand'] = subcommand
            __dataclass__self_dict['capabilities'] = capabilities

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__subcommand():
            @__dataclass__property
            def subcommand(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['subcommand']

            return subcommand

        setattr(__class__, 'subcommand', __dataclass__property__subcommand())

        def __dataclass__property__capabilities():
            @__dataclass__property
            def capabilities(__dataclass__self) -> __dataclass__override__fields__1__annotation:
                return __dataclass__self.__dict__['capabilities']

            return capabilities

        setattr(__class__, 'capabilities', __dataclass__property__capabilities())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"subcommand={self.subcommand!r}")
            parts.append(f"capabilities={self.capabilities!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('target_server', 'port', 'remote_server')), EqPlan(fields=('target_server', 'port'"
        ", 'remote_server')), FrozenPlan(fields=('FORMAT', 'REPLIES', 'target_server', 'port', 'remote_server'), allow_"
        "dynamic_dunder_attrs=False), HashPlan(action='add', fields=('target_server', 'port', 'remote_server'), cache=F"
        "alse), InitPlan(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields.0.annotation'), defau"
        "lt=None, default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None, validate"
        "=None, check_type=None), InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fields.1.annotation'), def"
        "ault=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=True, field_type=FieldType"
        ".CLASS_VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='target_server', annotation=OpRe"
        "f(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=True, field_type=F"
        "ieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='port', annotation=OpRef("
        "name='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default'), default_factory=None, init=True"
        ", override=True, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(n"
        "ame='remote_server', annotation=OpRef(name='init.fields.4.annotation'), default=OpRef(name='init.fields.4.defa"
        "ult'), default_factory=None, init=True, override=True, field_type=FieldType.INSTANCE, coerce=None, validate=No"
        "ne, check_type=None)), self_param='self', std_params=('target_server', 'port', 'remote_server'), kw_only_param"
        "s=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), OverridePlan(fields=(Ove"
        "rridePlan.Field(name='target_server', annotation=OpRef(name='override.fields.0.annotation')), OverridePlan.Fie"
        "ld(name='port', annotation=OpRef(name='override.fields.1.annotation')), OverridePlan.Field(name='remote_server"
        "', annotation=OpRef(name='override.fields.2.annotation'))), frozen=True), ReprPlan(fields=(ReprPlan.Field(name"
        "='target_server', kw_only=False, fn=None), ReprPlan.Field(name='port', kw_only=False, fn=None), ReprPlan.Field"
        "(name='remote_server', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='8811fba3b5d672526d571123253aedbb9c2280e7',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'ConnectMessage'),
    ),
)
def _process_dataclass__8811fba3b5d672526d571123253aedbb9c2280e7():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__3__default,
        __dataclass__init__fields__4__annotation,
        __dataclass__init__fields__4__default,
        __dataclass__override__fields__0__annotation,
        __dataclass__override__fields__1__annotation,
        __dataclass__override__fields__2__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                target_server=self.target_server,
                port=self.port,
                remote_server=self.remote_server,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.target_server == other.target_server and
                self.port == other.port and
                self.remote_server == other.remote_server
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'target_server',
            'port',
            'remote_server',
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
                self.target_server,
                self.port,
                self.remote_server,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            target_server: __dataclass__init__fields__2__annotation,
            port: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            remote_server: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['target_server'] = target_server
            __dataclass__self_dict['port'] = port
            __dataclass__self_dict['remote_server'] = remote_server

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__target_server():
            @__dataclass__property
            def target_server(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['target_server']

            return target_server

        setattr(__class__, 'target_server', __dataclass__property__target_server())

        def __dataclass__property__port():
            @__dataclass__property
            def port(__dataclass__self) -> __dataclass__override__fields__1__annotation:
                return __dataclass__self.__dict__['port']

            return port

        setattr(__class__, 'port', __dataclass__property__port())

        def __dataclass__property__remote_server():
            @__dataclass__property
            def remote_server(__dataclass__self) -> __dataclass__override__fields__2__annotation:
                return __dataclass__self.__dict__['remote_server']

            return remote_server

        setattr(__class__, 'remote_server', __dataclass__property__remote_server())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"target_server={self.target_server!r}")
            parts.append(f"port={self.port!r}")
            parts.append(f"remote_server={self.remote_server!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('reason',)), EqPlan(fields=('reason',)), FrozenPlan(fields=('FORMAT', 'REPLIES', '"
        "reason'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('reason',), cache=False), InitPlan"
        "(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields.0.annotation'), default=None, defaul"
        "t_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_ty"
        "pe=None), InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name"
        "='init.fields.1.default'), default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coe"
        "rce=None, validate=None, check_type=None), InitPlan.Field(name='reason', annotation=OpRef(name='init.fields.2."
        "annotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, override=True, fie"
        "ld_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('rea"
        "son',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), Ove"
        "rridePlan(fields=(OverridePlan.Field(name='reason', annotation=OpRef(name='override.fields.0.annotation')),), "
        "frozen=True), ReprPlan(fields=(ReprPlan.Field(name='reason', kw_only=False, fn=None),), id=False, terse=False,"
        " default_fn=None)))"
    ),
    plan_repr_sha1='7623cc8f9f94ad80790b66a93f99b4f376be7421',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'ErrorMessage'),
        ('omdev.specs.irc.messages.messages', 'QuitMessage'),
    ),
)
def _process_dataclass__7623cc8f9f94ad80790b66a93f99b4f376be7421():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default,
        __dataclass__override__fields__0__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                reason=self.reason,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.reason == other.reason
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'reason',
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
                self.reason,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            reason: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['reason'] = reason

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__reason():
            @__dataclass__property
            def reason(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['reason']

            return reason

        setattr(__class__, 'reason', __dataclass__property__reason())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"reason={self.reason!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('subject',)), EqPlan(fields=('subject',)), FrozenPlan(fields=('FORMAT', 'REPLIES',"
        " 'subject'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('subject',), cache=False), Init"
        "Plan(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields.0.annotation'), default=None, de"
        "fault_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, chec"
        "k_type=None), InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef("
        "name='init.fields.1.default'), default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR,"
        " coerce=None, validate=None, check_type=None), InitPlan.Field(name='subject', annotation=OpRef(name='init.fiel"
        "ds.2.annotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, override=True"
        ", field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params="
        "('subject',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()"
        "), OverridePlan(fields=(OverridePlan.Field(name='subject', annotation=OpRef(name='override.fields.0.annotation"
        "')),), frozen=True), ReprPlan(fields=(ReprPlan.Field(name='subject', kw_only=False, fn=None),), id=False, ters"
        "e=False, default_fn=None)))"
    ),
    plan_repr_sha1='791265d73b5c748eaaa4ed2aeb925c4555b68bcd',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'HelpMessage'),
    ),
)
def _process_dataclass__791265d73b5c748eaaa4ed2aeb925c4555b68bcd():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default,
        __dataclass__override__fields__0__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                subject=self.subject,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.subject == other.subject
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'subject',
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
                self.subject,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            subject: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['subject'] = subject

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__subject():
            @__dataclass__property
            def subject(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['subject']

            return subject

        setattr(__class__, 'subject', __dataclass__property__subject())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"subject={self.subject!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('nickname', 'channel')), EqPlan(fields=('nickname', 'channel')), FrozenPlan(fields"
        "=('FORMAT', 'REPLIES', 'nickname', 'channel'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', field"
        "s=('nickname', 'channel'), cache=False), InitPlan(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name="
        "'init.fields.0.annotation'), default=None, default_factory=None, init=True, override=True, field_type=FieldTyp"
        "e.CLASS_VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='REPLIES', annotation=OpRef(nam"
        "e='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, o"
        "verride=True, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(nam"
        "e='nickname', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True"
        ", override=True, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(n"
        "ame='channel', annotation=OpRef(name='init.fields.3.annotation'), default=None, default_factory=None, init=Tru"
        "e, override=True, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='se"
        "lf', std_params=('nickname', 'channel'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, i"
        "nit_fns=(), validate_fns=()), OverridePlan(fields=(OverridePlan.Field(name='nickname', annotation=OpRef(name='"
        "override.fields.0.annotation')), OverridePlan.Field(name='channel', annotation=OpRef(name='override.fields.1.a"
        "nnotation'))), frozen=True), ReprPlan(fields=(ReprPlan.Field(name='nickname', kw_only=False, fn=None), ReprPla"
        "n.Field(name='channel', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='5ec5e6b22f0e498014c7c5da721a3723508c9c06',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'InviteMessage'),
    ),
)
def _process_dataclass__5ec5e6b22f0e498014c7c5da721a3723508c9c06():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__override__fields__0__annotation,
        __dataclass__override__fields__1__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                nickname=self.nickname,
                channel=self.channel,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.nickname == other.nickname and
                self.channel == other.channel
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'nickname',
            'channel',
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
                self.nickname,
                self.channel,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            nickname: __dataclass__init__fields__2__annotation,
            channel: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['nickname'] = nickname
            __dataclass__self_dict['channel'] = channel

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__nickname():
            @__dataclass__property
            def nickname(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['nickname']

            return nickname

        setattr(__class__, 'nickname', __dataclass__property__nickname())

        def __dataclass__property__channel():
            @__dataclass__property
            def channel(__dataclass__self) -> __dataclass__override__fields__1__annotation:
                return __dataclass__self.__dict__['channel']

            return channel

        setattr(__class__, 'channel', __dataclass__property__channel())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"nickname={self.nickname!r}")
            parts.append(f"channel={self.channel!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('channels',)), EqPlan(fields=('channels',)), FrozenPlan(fields=('FORMAT', 'REPLIES"
        "', 'channels'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('channels',), cache=False), "
        "InitPlan(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields.0.annotation'), default=None"
        ", default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, "
        "check_type=None), InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fields.1.annotation'), default=Op"
        "Ref(name='init.fields.1.default'), default_factory=None, init=True, override=True, field_type=FieldType.CLASS_"
        "VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='channels', annotation=OpRef(name='init"
        ".fields.2.annotation'), default=None, default_factory=None, init=True, override=True, field_type=FieldType.INS"
        "TANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('channels',), kw_only_par"
        "ams=(), frozen=True, slots=False, post_init_params=None, init_fns=(OpRef(name='init.init_fns.0'),), validate_f"
        "ns=()), OverridePlan(fields=(OverridePlan.Field(name='channels', annotation=OpRef(name='override.fields.0.anno"
        "tation')),), frozen=True), ReprPlan(fields=(ReprPlan.Field(name='channels', kw_only=False, fn=None),), id=Fals"
        "e, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='1a70b14638ff334f563f97b1f401f8213e9554a2',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'JoinMessage'),
    ),
)
def _process_dataclass__1a70b14638ff334f563f97b1f401f8213e9554a2():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__init_fns__0,
        __dataclass__override__fields__0__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                channels=self.channels,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.channels == other.channels
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'channels',
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
                self.channels,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            channels: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['channels'] = channels
            __dataclass__init__init_fns__0(self)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__channels():
            @__dataclass__property
            def channels(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['channels']

            return channels

        setattr(__class__, 'channels', __dataclass__property__channels())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"channels={self.channels!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('channel', 'users', 'comment')), EqPlan(fields=('channel', 'users', 'comment')), F"
        "rozenPlan(fields=('FORMAT', 'REPLIES', 'channel', 'users', 'comment'), allow_dynamic_dunder_attrs=False), Hash"
        "Plan(action='add', fields=('channel', 'users', 'comment'), cache=False), InitPlan(fields=(InitPlan.Field(name="
        "'FORMAT', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, ov"
        "erride=True, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name"
        "='REPLIES', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), de"
        "fault_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, chec"
        "k_type=None), InitPlan.Field(name='channel', annotation=OpRef(name='init.fields.2.annotation'), default=None, "
        "default_factory=None, init=True, override=True, field_type=FieldType.INSTANCE, coerce=None, validate=None, che"
        "ck_type=None), InitPlan.Field(name='users', annotation=OpRef(name='init.fields.3.annotation'), default=None, d"
        "efault_factory=None, init=True, override=True, field_type=FieldType.INSTANCE, coerce=None, validate=None, chec"
        "k_type=None), InitPlan.Field(name='comment', annotation=OpRef(name='init.fields.4.annotation'), default=OpRef("
        "name='init.fields.4.default'), default_factory=None, init=True, override=True, field_type=FieldType.INSTANCE, "
        "coerce=None, validate=None, check_type=None)), self_param='self', std_params=('channel', 'users', 'comment'), "
        "kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), OverridePla"
        "n(fields=(OverridePlan.Field(name='channel', annotation=OpRef(name='override.fields.0.annotation')), OverrideP"
        "lan.Field(name='users', annotation=OpRef(name='override.fields.1.annotation')), OverridePlan.Field(name='comme"
        "nt', annotation=OpRef(name='override.fields.2.annotation'))), frozen=True), ReprPlan(fields=(ReprPlan.Field(na"
        "me='channel', kw_only=False, fn=None), ReprPlan.Field(name='users', kw_only=False, fn=None), ReprPlan.Field(na"
        "me='comment', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='5792a5887896028004187d042d1ec934392cfc65',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'KickMessage'),
    ),
)
def _process_dataclass__5792a5887896028004187d042d1ec934392cfc65():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__4__annotation,
        __dataclass__init__fields__4__default,
        __dataclass__override__fields__0__annotation,
        __dataclass__override__fields__1__annotation,
        __dataclass__override__fields__2__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                channel=self.channel,
                users=self.users,
                comment=self.comment,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.channel == other.channel and
                self.users == other.users and
                self.comment == other.comment
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'channel',
            'users',
            'comment',
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
                self.channel,
                self.users,
                self.comment,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            channel: __dataclass__init__fields__2__annotation,
            users: __dataclass__init__fields__3__annotation,
            comment: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['channel'] = channel
            __dataclass__self_dict['users'] = users
            __dataclass__self_dict['comment'] = comment

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__channel():
            @__dataclass__property
            def channel(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['channel']

            return channel

        setattr(__class__, 'channel', __dataclass__property__channel())

        def __dataclass__property__users():
            @__dataclass__property
            def users(__dataclass__self) -> __dataclass__override__fields__1__annotation:
                return __dataclass__self.__dict__['users']

            return users

        setattr(__class__, 'users', __dataclass__property__users())

        def __dataclass__property__comment():
            @__dataclass__property
            def comment(__dataclass__self) -> __dataclass__override__fields__2__annotation:
                return __dataclass__self.__dict__['comment']

            return comment

        setattr(__class__, 'comment', __dataclass__property__comment())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"channel={self.channel!r}")
            parts.append(f"users={self.users!r}")
            parts.append(f"comment={self.comment!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('nickname', 'comment')), EqPlan(fields=('nickname', 'comment')), FrozenPlan(fields"
        "=('FORMAT', 'REPLIES', 'nickname', 'comment'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', field"
        "s=('nickname', 'comment'), cache=False), InitPlan(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name="
        "'init.fields.0.annotation'), default=None, default_factory=None, init=True, override=True, field_type=FieldTyp"
        "e.CLASS_VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='REPLIES', annotation=OpRef(nam"
        "e='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, o"
        "verride=True, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(nam"
        "e='nickname', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True"
        ", override=True, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(n"
        "ame='comment', annotation=OpRef(name='init.fields.3.annotation'), default=None, default_factory=None, init=Tru"
        "e, override=True, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='se"
        "lf', std_params=('nickname', 'comment'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, i"
        "nit_fns=(), validate_fns=()), OverridePlan(fields=(OverridePlan.Field(name='nickname', annotation=OpRef(name='"
        "override.fields.0.annotation')), OverridePlan.Field(name='comment', annotation=OpRef(name='override.fields.1.a"
        "nnotation'))), frozen=True), ReprPlan(fields=(ReprPlan.Field(name='nickname', kw_only=False, fn=None), ReprPla"
        "n.Field(name='comment', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='0970330452192ce75282795ac855e7b531d4bbe0',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'KillMessage'),
    ),
)
def _process_dataclass__0970330452192ce75282795ac855e7b531d4bbe0():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__override__fields__0__annotation,
        __dataclass__override__fields__1__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                nickname=self.nickname,
                comment=self.comment,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.nickname == other.nickname and
                self.comment == other.comment
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'nickname',
            'comment',
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
                self.nickname,
                self.comment,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            nickname: __dataclass__init__fields__2__annotation,
            comment: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['nickname'] = nickname
            __dataclass__self_dict['comment'] = comment

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__nickname():
            @__dataclass__property
            def nickname(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['nickname']

            return nickname

        setattr(__class__, 'nickname', __dataclass__property__nickname())

        def __dataclass__property__comment():
            @__dataclass__property
            def comment(__dataclass__self) -> __dataclass__override__fields__1__annotation:
                return __dataclass__self.__dict__['comment']

            return comment

        setattr(__class__, 'comment', __dataclass__property__comment())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"nickname={self.nickname!r}")
            parts.append(f"comment={self.comment!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('channels', 'elistconds')), EqPlan(fields=('channels', 'elistconds')), FrozenPlan("
        "fields=('FORMAT', 'REPLIES', 'channels', 'elistconds'), allow_dynamic_dunder_attrs=False), HashPlan(action='ad"
        "d', fields=('channels', 'elistconds'), cache=False), InitPlan(fields=(InitPlan.Field(name='FORMAT', annotation"
        "=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=True, field_t"
        "ype=FieldType.CLASS_VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='REPLIES', annotati"
        "on=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, "
        "init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_type=None), InitPl"
        "an.Field(name='channels', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=Non"
        "e, init=True, override=True, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), Init"
        "Plan.Field(name='elistconds', annotation=OpRef(name='init.fields.3.annotation'), default=None, default_factory"
        "=None, init=True, override=True, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)),"
        " self_param='self', std_params=('channels', 'elistconds'), kw_only_params=(), frozen=True, slots=False, post_i"
        "nit_params=None, init_fns=(), validate_fns=()), OverridePlan(fields=(OverridePlan.Field(name='channels', annot"
        "ation=OpRef(name='override.fields.0.annotation')), OverridePlan.Field(name='elistconds', annotation=OpRef(name"
        "='override.fields.1.annotation'))), frozen=True), ReprPlan(fields=(ReprPlan.Field(name='channels', kw_only=Fal"
        "se, fn=None), ReprPlan.Field(name='elistconds', kw_only=False, fn=None)), id=False, terse=False, default_fn=No"
        "ne)))"
    ),
    plan_repr_sha1='1106d0edab01af7e48cb754591d1b026b7ba58b7',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'ListMessage'),
    ),
)
def _process_dataclass__1106d0edab01af7e48cb754591d1b026b7ba58b7():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__override__fields__0__annotation,
        __dataclass__override__fields__1__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                channels=self.channels,
                elistconds=self.elistconds,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.channels == other.channels and
                self.elistconds == other.elistconds
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'channels',
            'elistconds',
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
                self.channels,
                self.elistconds,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            channels: __dataclass__init__fields__2__annotation,
            elistconds: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['channels'] = channels
            __dataclass__self_dict['elistconds'] = elistconds

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__channels():
            @__dataclass__property
            def channels(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['channels']

            return channels

        setattr(__class__, 'channels', __dataclass__property__channels())

        def __dataclass__property__elistconds():
            @__dataclass__property
            def elistconds(__dataclass__self) -> __dataclass__override__fields__1__annotation:
                return __dataclass__self.__dict__['elistconds']

            return elistconds

        setattr(__class__, 'elistconds', __dataclass__property__elistconds())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"channels={self.channels!r}")
            parts.append(f"elistconds={self.elistconds!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('target', 'modestring', 'mode_arguments')), EqPlan(fields=('target', 'modestring',"
        " 'mode_arguments')), FrozenPlan(fields=('FORMAT', 'REPLIES', 'target', 'modestring', 'mode_arguments'), allow_"
        "dynamic_dunder_attrs=False), HashPlan(action='add', fields=('target', 'modestring', 'mode_arguments'), cache=F"
        "alse), InitPlan(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields.0.annotation'), defau"
        "lt=None, default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None, validate"
        "=None, check_type=None), InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fields.1.annotation'), def"
        "ault=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=True, field_type=FieldType"
        ".CLASS_VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='target', annotation=OpRef(name="
        "'init.fields.2.annotation'), default=None, default_factory=None, init=True, override=True, field_type=FieldTyp"
        "e.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='modestring', annotation=OpRef(n"
        "ame='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default'), default_factory=None, init=True,"
        " override=True, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(na"
        "me='mode_arguments', annotation=OpRef(name='init.fields.4.annotation'), default=OpRef(name='init.fields.4.defa"
        "ult'), default_factory=None, init=True, override=True, field_type=FieldType.INSTANCE, coerce=None, validate=No"
        "ne, check_type=None)), self_param='self', std_params=('target', 'modestring', 'mode_arguments'), kw_only_param"
        "s=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), OverridePlan(fields=(Ove"
        "rridePlan.Field(name='target', annotation=OpRef(name='override.fields.0.annotation')), OverridePlan.Field(name"
        "='modestring', annotation=OpRef(name='override.fields.1.annotation')), OverridePlan.Field(name='mode_arguments"
        "', annotation=OpRef(name='override.fields.2.annotation'))), frozen=True), ReprPlan(fields=(ReprPlan.Field(name"
        "='target', kw_only=False, fn=None), ReprPlan.Field(name='modestring', kw_only=False, fn=None), ReprPlan.Field("
        "name='mode_arguments', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='284ad27444ea2bf1cb4dca89baba0914c98f216d',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'ModeMessage'),
    ),
)
def _process_dataclass__284ad27444ea2bf1cb4dca89baba0914c98f216d():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__3__default,
        __dataclass__init__fields__4__annotation,
        __dataclass__init__fields__4__default,
        __dataclass__override__fields__0__annotation,
        __dataclass__override__fields__1__annotation,
        __dataclass__override__fields__2__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                target=self.target,
                modestring=self.modestring,
                mode_arguments=self.mode_arguments,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.target == other.target and
                self.modestring == other.modestring and
                self.mode_arguments == other.mode_arguments
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'target',
            'modestring',
            'mode_arguments',
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
                self.target,
                self.modestring,
                self.mode_arguments,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            target: __dataclass__init__fields__2__annotation,
            modestring: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            mode_arguments: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['target'] = target
            __dataclass__self_dict['modestring'] = modestring
            __dataclass__self_dict['mode_arguments'] = mode_arguments

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__target():
            @__dataclass__property
            def target(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['target']

            return target

        setattr(__class__, 'target', __dataclass__property__target())

        def __dataclass__property__modestring():
            @__dataclass__property
            def modestring(__dataclass__self) -> __dataclass__override__fields__1__annotation:
                return __dataclass__self.__dict__['modestring']

            return modestring

        setattr(__class__, 'modestring', __dataclass__property__modestring())

        def __dataclass__property__mode_arguments():
            @__dataclass__property
            def mode_arguments(__dataclass__self) -> __dataclass__override__fields__2__annotation:
                return __dataclass__self.__dict__['mode_arguments']

            return mode_arguments

        setattr(__class__, 'mode_arguments', __dataclass__property__mode_arguments())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"target={self.target!r}")
            parts.append(f"modestring={self.modestring!r}")
            parts.append(f"mode_arguments={self.mode_arguments!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('channels',)), EqPlan(fields=('channels',)), FrozenPlan(fields=('FORMAT', 'REPLIES"
        "', 'channels'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('channels',), cache=False), "
        "InitPlan(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields.0.annotation'), default=None"
        ", default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, "
        "check_type=None), InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fields.1.annotation'), default=Op"
        "Ref(name='init.fields.1.default'), default_factory=None, init=True, override=True, field_type=FieldType.CLASS_"
        "VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='channels', annotation=OpRef(name='init"
        ".fields.2.annotation'), default=None, default_factory=None, init=True, override=True, field_type=FieldType.INS"
        "TANCE, coerce=None, validate=OpRef(name='init.fields.2.validate'), check_type=None)), self_param='self', std_p"
        "arams=('channels',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate"
        "_fns=()), OverridePlan(fields=(OverridePlan.Field(name='channels', annotation=OpRef(name='override.fields.0.an"
        "notation')),), frozen=True), ReprPlan(fields=(ReprPlan.Field(name='channels', kw_only=False, fn=None),), id=Fa"
        "lse, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='2d4fe92ac829033676777150c5c262e348d32396',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'NamesMessage'),
    ),
)
def _process_dataclass__2d4fe92ac829033676777150c5c262e348d32396():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__validate,
        __dataclass__override__fields__0__annotation,
        __dataclass__FieldFnValidationError,  # noqa
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                channels=self.channels,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.channels == other.channels
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'channels',
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
                self.channels,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            channels: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            if not __dataclass__init__fields__2__validate(channels): 
                raise __dataclass__FieldFnValidationError(
                    obj=self,
                    fn=__dataclass__init__fields__2__validate,
                    field='channels',
                    value=channels,
                )
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['channels'] = channels

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__channels():
            @__dataclass__property
            def channels(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['channels']

            return channels

        setattr(__class__, 'channels', __dataclass__property__channels())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"channels={self.channels!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('nickname',)), EqPlan(fields=('nickname',)), FrozenPlan(fields=('FORMAT', 'REPLIES"
        "', 'nickname'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('nickname',), cache=False), "
        "InitPlan(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields.0.annotation'), default=None"
        ", default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, "
        "check_type=None), InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fields.1.annotation'), default=Op"
        "Ref(name='init.fields.1.default'), default_factory=None, init=True, override=True, field_type=FieldType.CLASS_"
        "VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='nickname', annotation=OpRef(name='init"
        ".fields.2.annotation'), default=None, default_factory=None, init=True, override=True, field_type=FieldType.INS"
        "TANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('nickname',), kw_only_par"
        "ams=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), OverridePlan(fields=(O"
        "verridePlan.Field(name='nickname', annotation=OpRef(name='override.fields.0.annotation')),), frozen=True), Rep"
        "rPlan(fields=(ReprPlan.Field(name='nickname', kw_only=False, fn=None),), id=False, terse=False, default_fn=Non"
        "e)))"
    ),
    plan_repr_sha1='54111260e4b0641f0f7894cbbcf4ad31e9e7759d',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'NickMessage'),
    ),
)
def _process_dataclass__54111260e4b0641f0f7894cbbcf4ad31e9e7759d():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__override__fields__0__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                nickname=self.nickname,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.nickname == other.nickname
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'nickname',
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
                self.nickname,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            nickname: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['nickname'] = nickname

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__nickname():
            @__dataclass__property
            def nickname(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['nickname']

            return nickname

        setattr(__class__, 'nickname', __dataclass__property__nickname())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"nickname={self.nickname!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('targets', 'text')), EqPlan(fields=('targets', 'text')), FrozenPlan(fields=('FORMA"
        "T', 'REPLIES', 'targets', 'text'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('targets'"
        ", 'text'), cache=False), InitPlan(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields.0.a"
        "nnotation'), default=None, default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coe"
        "rce=None, validate=None, check_type=None), InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fields.1"
        ".annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=True, fi"
        "eld_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='targets', ann"
        "otation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=True, "
        "field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='text', annot"
        "ation=OpRef(name='init.fields.3.annotation'), default=None, default_factory=None, init=True, override=True, fi"
        "eld_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('ta"
        "rgets', 'text'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns"
        "=()), OverridePlan(fields=(OverridePlan.Field(name='targets', annotation=OpRef(name='override.fields.0.annotat"
        "ion')), OverridePlan.Field(name='text', annotation=OpRef(name='override.fields.1.annotation'))), frozen=True),"
        " ReprPlan(fields=(ReprPlan.Field(name='targets', kw_only=False, fn=None), ReprPlan.Field(name='text', kw_only="
        "False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='87ce9704ce48dd27c205a13d86219933c174a018',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'NoticeMessage'),
        ('omdev.specs.irc.messages.messages', 'PrivmsgMessage'),
    ),
)
def _process_dataclass__87ce9704ce48dd27c205a13d86219933c174a018():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__override__fields__0__annotation,
        __dataclass__override__fields__1__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                targets=self.targets,
                text=self.text,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.targets == other.targets and
                self.text == other.text
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'targets',
            'text',
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
                self.targets,
                self.text,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            targets: __dataclass__init__fields__2__annotation,
            text: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['targets'] = targets
            __dataclass__self_dict['text'] = text

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__targets():
            @__dataclass__property
            def targets(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['targets']

            return targets

        setattr(__class__, 'targets', __dataclass__property__targets())

        def __dataclass__property__text():
            @__dataclass__property
            def text(__dataclass__self) -> __dataclass__override__fields__1__annotation:
                return __dataclass__self.__dict__['text']

            return text

        setattr(__class__, 'text', __dataclass__property__text())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"targets={self.targets!r}")
            parts.append(f"text={self.text!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('name', 'password')), EqPlan(fields=('name', 'password')), FrozenPlan(fields=('FOR"
        "MAT', 'REPLIES', 'name', 'password'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('name'"
        ", 'password'), cache=False), InitPlan(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields"
        ".0.annotation'), default=None, default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR,"
        " coerce=None, validate=None, check_type=None), InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fiel"
        "ds.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=True"
        ", field_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='name', an"
        "notation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=True,"
        " field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='password', "
        "annotation=OpRef(name='init.fields.3.annotation'), default=None, default_factory=None, init=True, override=Tru"
        "e, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params"
        "=('name', 'password'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), valida"
        "te_fns=()), OverridePlan(fields=(OverridePlan.Field(name='name', annotation=OpRef(name='override.fields.0.anno"
        "tation')), OverridePlan.Field(name='password', annotation=OpRef(name='override.fields.1.annotation'))), frozen"
        "=True), ReprPlan(fields=(ReprPlan.Field(name='name', kw_only=False, fn=None), ReprPlan.Field(name='password', "
        "kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='9ae99947272306a0f51f4e19f60b04591df8cf76',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'OperMessage'),
    ),
)
def _process_dataclass__9ae99947272306a0f51f4e19f60b04591df8cf76():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__override__fields__0__annotation,
        __dataclass__override__fields__1__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                name=self.name,
                password=self.password,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.password == other.password
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'name',
            'password',
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
                self.name,
                self.password,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__2__annotation,
            password: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['name'] = name
            __dataclass__self_dict['password'] = password

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__name():
            @__dataclass__property
            def name(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['name']

            return name

        setattr(__class__, 'name', __dataclass__property__name())

        def __dataclass__property__password():
            @__dataclass__property
            def password(__dataclass__self) -> __dataclass__override__fields__1__annotation:
                return __dataclass__self.__dict__['password']

            return password

        setattr(__class__, 'password', __dataclass__property__password())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"password={self.password!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('channels', 'reason')), EqPlan(fields=('channels', 'reason')), FrozenPlan(fields=("
        "'FORMAT', 'REPLIES', 'channels', 'reason'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=("
        "'channels', 'reason'), cache=False), InitPlan(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name='ini"
        "t.fields.0.annotation'), default=None, default_factory=None, init=True, override=True, field_type=FieldType.CL"
        "ASS_VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='REPLIES', annotation=OpRef(name='i"
        "nit.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, overr"
        "ide=True, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='c"
        "hannels', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, ov"
        "erride=True, field_type=FieldType.INSTANCE, coerce=None, validate=OpRef(name='init.fields.2.validate'), check_"
        "type=None), InitPlan.Field(name='reason', annotation=OpRef(name='init.fields.3.annotation'), default=OpRef(nam"
        "e='init.fields.3.default'), default_factory=None, init=True, override=True, field_type=FieldType.INSTANCE, coe"
        "rce=None, validate=None, check_type=None)), self_param='self', std_params=('channels', 'reason'), kw_only_para"
        "ms=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), OverridePlan(fields=(Ov"
        "erridePlan.Field(name='channels', annotation=OpRef(name='override.fields.0.annotation')), OverridePlan.Field(n"
        "ame='reason', annotation=OpRef(name='override.fields.1.annotation'))), frozen=True), ReprPlan(fields=(ReprPlan"
        ".Field(name='channels', kw_only=False, fn=None), ReprPlan.Field(name='reason', kw_only=False, fn=None)), id=Fa"
        "lse, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='cfaa1afd0d730c2063d603b4891d6e9795d99a8b',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'PartMessage'),
    ),
)
def _process_dataclass__cfaa1afd0d730c2063d603b4891d6e9795d99a8b():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__validate,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__3__default,
        __dataclass__override__fields__0__annotation,
        __dataclass__override__fields__1__annotation,
        __dataclass__FieldFnValidationError,  # noqa
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                channels=self.channels,
                reason=self.reason,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.channels == other.channels and
                self.reason == other.reason
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'channels',
            'reason',
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
                self.channels,
                self.reason,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            channels: __dataclass__init__fields__2__annotation,
            reason: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            if not __dataclass__init__fields__2__validate(channels): 
                raise __dataclass__FieldFnValidationError(
                    obj=self,
                    fn=__dataclass__init__fields__2__validate,
                    field='channels',
                    value=channels,
                )
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['channels'] = channels
            __dataclass__self_dict['reason'] = reason

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__channels():
            @__dataclass__property
            def channels(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['channels']

            return channels

        setattr(__class__, 'channels', __dataclass__property__channels())

        def __dataclass__property__reason():
            @__dataclass__property
            def reason(__dataclass__self) -> __dataclass__override__fields__1__annotation:
                return __dataclass__self.__dict__['reason']

            return reason

        setattr(__class__, 'reason', __dataclass__property__reason())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"channels={self.channels!r}")
            parts.append(f"reason={self.reason!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('password',)), EqPlan(fields=('password',)), FrozenPlan(fields=('FORMAT', 'REPLIES"
        "', 'password'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('password',), cache=False), "
        "InitPlan(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields.0.annotation'), default=None"
        ", default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, "
        "check_type=None), InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fields.1.annotation'), default=Op"
        "Ref(name='init.fields.1.default'), default_factory=None, init=True, override=True, field_type=FieldType.CLASS_"
        "VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='password', annotation=OpRef(name='init"
        ".fields.2.annotation'), default=None, default_factory=None, init=True, override=True, field_type=FieldType.INS"
        "TANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('password',), kw_only_par"
        "ams=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), OverridePlan(fields=(O"
        "verridePlan.Field(name='password', annotation=OpRef(name='override.fields.0.annotation')),), frozen=True), Rep"
        "rPlan(fields=(ReprPlan.Field(name='password', kw_only=False, fn=None),), id=False, terse=False, default_fn=Non"
        "e)))"
    ),
    plan_repr_sha1='b41feddc6cb4288b4138cddf6b323c30913b2511',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'PassMessage'),
    ),
)
def _process_dataclass__b41feddc6cb4288b4138cddf6b323c30913b2511():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__override__fields__0__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                password=self.password,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.password == other.password
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'password',
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
                self.password,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            password: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['password'] = password

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__password():
            @__dataclass__property
            def password(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['password']

            return password

        setattr(__class__, 'password', __dataclass__property__password())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"password={self.password!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('token',)), EqPlan(fields=('token',)), FrozenPlan(fields=('FORMAT', 'REPLIES', 'to"
        "ken'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('token',), cache=False), InitPlan(fie"
        "lds=(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_fa"
        "ctory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_type=N"
        "one), InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='in"
        "it.fields.1.default'), default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce="
        "None, validate=None, check_type=None), InitPlan.Field(name='token', annotation=OpRef(name='init.fields.2.annot"
        "ation'), default=None, default_factory=None, init=True, override=True, field_type=FieldType.INSTANCE, coerce=N"
        "one, validate=None, check_type=None)), self_param='self', std_params=('token',), kw_only_params=(), frozen=Tru"
        "e, slots=False, post_init_params=None, init_fns=(), validate_fns=()), OverridePlan(fields=(OverridePlan.Field("
        "name='token', annotation=OpRef(name='override.fields.0.annotation')),), frozen=True), ReprPlan(fields=(ReprPla"
        "n.Field(name='token', kw_only=False, fn=None),), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='e04839ab6deccb9b310f949d0518c0127c9b6ee6',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'PingMessage'),
    ),
)
def _process_dataclass__e04839ab6deccb9b310f949d0518c0127c9b6ee6():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__override__fields__0__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                token=self.token,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.token == other.token
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'token',
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
                self.token,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            token: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['token'] = token

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__token():
            @__dataclass__property
            def token(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['token']

            return token

        setattr(__class__, 'token', __dataclass__property__token())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"token={self.token!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('token', 'server')), EqPlan(fields=('token', 'server')), FrozenPlan(fields=('FORMA"
        "T', 'REPLIES', 'token', 'server'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('token', "
        "'server'), cache=False), InitPlan(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields.0.a"
        "nnotation'), default=None, default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coe"
        "rce=None, validate=None, check_type=None), InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fields.1"
        ".annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=True, fi"
        "eld_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='token', annot"
        "ation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=True, fi"
        "eld_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='server', annot"
        "ation=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default'), default_factory=Non"
        "e, init=True, override=True, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), sel"
        "f_param='self', std_params=('token', 'server'), kw_only_params=(), frozen=True, slots=False, post_init_params="
        "None, init_fns=(), validate_fns=()), OverridePlan(fields=(OverridePlan.Field(name='token', annotation=OpRef(na"
        "me='override.fields.0.annotation')), OverridePlan.Field(name='server', annotation=OpRef(name='override.fields."
        "1.annotation'))), frozen=True), ReprPlan(fields=(ReprPlan.Field(name='token', kw_only=False, fn=None), ReprPla"
        "n.Field(name='server', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='f12fa05398ee3eb719c5f6fadff847a13d2a0b70',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'PongMessage'),
    ),
)
def _process_dataclass__f12fa05398ee3eb719c5f6fadff847a13d2a0b70():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__3__default,
        __dataclass__override__fields__0__annotation,
        __dataclass__override__fields__1__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                token=self.token,
                server=self.server,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.token == other.token and
                self.server == other.server
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'token',
            'server',
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
                self.token,
                self.server,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            token: __dataclass__init__fields__2__annotation,
            server: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['token'] = token
            __dataclass__self_dict['server'] = server

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__token():
            @__dataclass__property
            def token(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['token']

            return token

        setattr(__class__, 'token', __dataclass__property__token())

        def __dataclass__property__server():
            @__dataclass__property
            def server(__dataclass__self) -> __dataclass__override__fields__1__annotation:
                return __dataclass__self.__dict__['server']

            return server

        setattr(__class__, 'server', __dataclass__property__server())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"token={self.token!r}")
            parts.append(f"server={self.server!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('server', 'comment')), EqPlan(fields=('server', 'comment')), FrozenPlan(fields=('F"
        "ORMAT', 'REPLIES', 'server', 'comment'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('se"
        "rver', 'comment'), cache=False), InitPlan(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fi"
        "elds.0.annotation'), default=None, default_factory=None, init=True, override=True, field_type=FieldType.CLASS_"
        "VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='REPLIES', annotation=OpRef(name='init."
        "fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override="
        "True, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='serve"
        "r', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override"
        "=True, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='comme"
        "nt', annotation=OpRef(name='init.fields.3.annotation'), default=None, default_factory=None, init=True, overrid"
        "e=True, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_p"
        "arams=('server', 'comment'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), "
        "validate_fns=()), OverridePlan(fields=(OverridePlan.Field(name='server', annotation=OpRef(name='override.field"
        "s.0.annotation')), OverridePlan.Field(name='comment', annotation=OpRef(name='override.fields.1.annotation'))),"
        " frozen=True), ReprPlan(fields=(ReprPlan.Field(name='server', kw_only=False, fn=None), ReprPlan.Field(name='co"
        "mment', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='0c13e8ddfbb89482b2db1fe2b572f22ad5f55534',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'SquitMessage'),
    ),
)
def _process_dataclass__0c13e8ddfbb89482b2db1fe2b572f22ad5f55534():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__override__fields__0__annotation,
        __dataclass__override__fields__1__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                server=self.server,
                comment=self.comment,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.server == other.server and
                self.comment == other.comment
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'server',
            'comment',
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
                self.server,
                self.comment,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            server: __dataclass__init__fields__2__annotation,
            comment: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['server'] = server
            __dataclass__self_dict['comment'] = comment

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__server():
            @__dataclass__property
            def server(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['server']

            return server

        setattr(__class__, 'server', __dataclass__property__server())

        def __dataclass__property__comment():
            @__dataclass__property
            def comment(__dataclass__self) -> __dataclass__override__fields__1__annotation:
                return __dataclass__self.__dict__['comment']

            return comment

        setattr(__class__, 'comment', __dataclass__property__comment())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"server={self.server!r}")
            parts.append(f"comment={self.comment!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('query', 'server')), EqPlan(fields=('query', 'server')), FrozenPlan(fields=('FORMA"
        "T', 'REPLIES', 'query', 'server'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('query', "
        "'server'), cache=False), InitPlan(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields.0.a"
        "nnotation'), default=None, default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coe"
        "rce=None, validate=None, check_type=None), InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fields.1"
        ".annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=True, fi"
        "eld_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='query', annot"
        "ation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=True, fi"
        "eld_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='server', annot"
        "ation=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default'), default_factory=Non"
        "e, init=True, override=True, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), sel"
        "f_param='self', std_params=('query', 'server'), kw_only_params=(), frozen=True, slots=False, post_init_params="
        "None, init_fns=(), validate_fns=()), OverridePlan(fields=(OverridePlan.Field(name='query', annotation=OpRef(na"
        "me='override.fields.0.annotation')), OverridePlan.Field(name='server', annotation=OpRef(name='override.fields."
        "1.annotation'))), frozen=True), ReprPlan(fields=(ReprPlan.Field(name='query', kw_only=False, fn=None), ReprPla"
        "n.Field(name='server', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='4476390b3addd000ea364a5387b80dff9d487b5f',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'StatsMessage'),
    ),
)
def _process_dataclass__4476390b3addd000ea364a5387b80dff9d487b5f():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__3__default,
        __dataclass__override__fields__0__annotation,
        __dataclass__override__fields__1__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                query=self.query,
                server=self.server,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.query == other.query and
                self.server == other.server
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'query',
            'server',
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
                self.query,
                self.server,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            query: __dataclass__init__fields__2__annotation,
            server: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['query'] = query
            __dataclass__self_dict['server'] = server

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__query():
            @__dataclass__property
            def query(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['query']

            return query

        setattr(__class__, 'query', __dataclass__property__query())

        def __dataclass__property__server():
            @__dataclass__property
            def server(__dataclass__self) -> __dataclass__override__fields__1__annotation:
                return __dataclass__self.__dict__['server']

            return server

        setattr(__class__, 'server', __dataclass__property__server())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"query={self.query!r}")
            parts.append(f"server={self.server!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('server',)), EqPlan(fields=('server',)), FrozenPlan(fields=('FORMAT', 'REPLIES', '"
        "server'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('server',), cache=False), InitPlan"
        "(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields.0.annotation'), default=None, defaul"
        "t_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_ty"
        "pe=None), InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name"
        "='init.fields.1.default'), default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coe"
        "rce=None, validate=None, check_type=None), InitPlan.Field(name='server', annotation=OpRef(name='init.fields.2."
        "annotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, override=True, fie"
        "ld_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('ser"
        "ver',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), Ove"
        "rridePlan(fields=(OverridePlan.Field(name='server', annotation=OpRef(name='override.fields.0.annotation')),), "
        "frozen=True), ReprPlan(fields=(ReprPlan.Field(name='server', kw_only=False, fn=None),), id=False, terse=False,"
        " default_fn=None)))"
    ),
    plan_repr_sha1='44db07aa12830bbc79072d98d0fdb6a70ff7e380',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'TimeMessage'),
    ),
)
def _process_dataclass__44db07aa12830bbc79072d98d0fdb6a70ff7e380():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default,
        __dataclass__override__fields__0__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                server=self.server,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.server == other.server
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'server',
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
                self.server,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            server: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['server'] = server

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__server():
            @__dataclass__property
            def server(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['server']

            return server

        setattr(__class__, 'server', __dataclass__property__server())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"server={self.server!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('channel', 'topic')), EqPlan(fields=('channel', 'topic')), FrozenPlan(fields=('FOR"
        "MAT', 'REPLIES', 'channel', 'topic'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('chann"
        "el', 'topic'), cache=False), InitPlan(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields"
        ".0.annotation'), default=None, default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR,"
        " coerce=None, validate=None, check_type=None), InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fiel"
        "ds.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=True"
        ", field_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='channel',"
        " annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=Tr"
        "ue, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='topic', "
        "annotation=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default'), default_factor"
        "y=None, init=True, override=True, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None))"
        ", self_param='self', std_params=('channel', 'topic'), kw_only_params=(), frozen=True, slots=False, post_init_p"
        "arams=None, init_fns=(), validate_fns=()), OverridePlan(fields=(OverridePlan.Field(name='channel', annotation="
        "OpRef(name='override.fields.0.annotation')), OverridePlan.Field(name='topic', annotation=OpRef(name='override."
        "fields.1.annotation'))), frozen=True), ReprPlan(fields=(ReprPlan.Field(name='channel', kw_only=False, fn=None)"
        ", ReprPlan.Field(name='topic', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='6ff3a3b378ac74e192f51cef7ef115b9bf45d028',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'TopicMessage'),
    ),
)
def _process_dataclass__6ff3a3b378ac74e192f51cef7ef115b9bf45d028():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__3__default,
        __dataclass__override__fields__0__annotation,
        __dataclass__override__fields__1__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                channel=self.channel,
                topic=self.topic,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.channel == other.channel and
                self.topic == other.topic
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'channel',
            'topic',
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
                self.channel,
                self.topic,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            channel: __dataclass__init__fields__2__annotation,
            topic: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['channel'] = channel
            __dataclass__self_dict['topic'] = topic

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__channel():
            @__dataclass__property
            def channel(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['channel']

            return channel

        setattr(__class__, 'channel', __dataclass__property__channel())

        def __dataclass__property__topic():
            @__dataclass__property
            def topic(__dataclass__self) -> __dataclass__override__fields__1__annotation:
                return __dataclass__self.__dict__['topic']

            return topic

        setattr(__class__, 'topic', __dataclass__property__topic())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"channel={self.channel!r}")
            parts.append(f"topic={self.topic!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('username', 'realname', 'param1', 'param2')), EqPlan(fields=('username', 'realname"
        "', 'param1', 'param2')), FrozenPlan(fields=('FORMAT', 'REPLIES', 'username', 'realname', 'param1', 'param2'), "
        "allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('username', 'realname', 'param1', 'param2'),"
        " cache=False), InitPlan(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields.0.annotation'"
        "), default=None, default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None, "
        "validate=None, check_type=None), InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fields.1.annotatio"
        "n'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=True, field_type=F"
        "ieldType.CLASS_VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='username', annotation=O"
        "pRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=True, field_typ"
        "e=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='realname', annotation"
        "=OpRef(name='init.fields.3.annotation'), default=None, default_factory=None, init=True, override=True, field_t"
        "ype=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='param1', annotation"
        "=OpRef(name='init.fields.4.annotation'), default=OpRef(name='init.fields.4.default'), default_factory=None, in"
        "it=True, override=True, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan."
        "Field(name='param2', annotation=OpRef(name='init.fields.5.annotation'), default=OpRef(name='init.fields.5.defa"
        "ult'), default_factory=None, init=True, override=True, field_type=FieldType.INSTANCE, coerce=None, validate=No"
        "ne, check_type=None)), self_param='self', std_params=('username', 'realname', 'param1', 'param2'), kw_only_par"
        "ams=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), OverridePlan(fields=(O"
        "verridePlan.Field(name='username', annotation=OpRef(name='override.fields.0.annotation')), OverridePlan.Field("
        "name='realname', annotation=OpRef(name='override.fields.1.annotation')), OverridePlan.Field(name='param1', ann"
        "otation=OpRef(name='override.fields.2.annotation')), OverridePlan.Field(name='param2', annotation=OpRef(name='"
        "override.fields.3.annotation'))), frozen=True), ReprPlan(fields=(ReprPlan.Field(name='username', kw_only=False"
        ", fn=None), ReprPlan.Field(name='realname', kw_only=False, fn=None), ReprPlan.Field(name='param1', kw_only=Fal"
        "se, fn=None), ReprPlan.Field(name='param2', kw_only=False, fn=None)), id=False, terse=False, default_fn=None))"
        ")"
    ),
    plan_repr_sha1='38a9ae90eea475011dacaad96621bf817d7e09c3',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'UserMessage'),
    ),
)
def _process_dataclass__38a9ae90eea475011dacaad96621bf817d7e09c3():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__4__annotation,
        __dataclass__init__fields__4__default,
        __dataclass__init__fields__5__annotation,
        __dataclass__init__fields__5__default,
        __dataclass__override__fields__0__annotation,
        __dataclass__override__fields__1__annotation,
        __dataclass__override__fields__2__annotation,
        __dataclass__override__fields__3__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                username=self.username,
                realname=self.realname,
                param1=self.param1,
                param2=self.param2,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.username == other.username and
                self.realname == other.realname and
                self.param1 == other.param1 and
                self.param2 == other.param2
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'username',
            'realname',
            'param1',
            'param2',
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
                self.username,
                self.realname,
                self.param1,
                self.param2,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            username: __dataclass__init__fields__2__annotation,
            realname: __dataclass__init__fields__3__annotation,
            param1: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            param2: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['username'] = username
            __dataclass__self_dict['realname'] = realname
            __dataclass__self_dict['param1'] = param1
            __dataclass__self_dict['param2'] = param2

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__username():
            @__dataclass__property
            def username(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['username']

            return username

        setattr(__class__, 'username', __dataclass__property__username())

        def __dataclass__property__realname():
            @__dataclass__property
            def realname(__dataclass__self) -> __dataclass__override__fields__1__annotation:
                return __dataclass__self.__dict__['realname']

            return realname

        setattr(__class__, 'realname', __dataclass__property__realname())

        def __dataclass__property__param1():
            @__dataclass__property
            def param1(__dataclass__self) -> __dataclass__override__fields__2__annotation:
                return __dataclass__self.__dict__['param1']

            return param1

        setattr(__class__, 'param1', __dataclass__property__param1())

        def __dataclass__property__param2():
            @__dataclass__property
            def param2(__dataclass__self) -> __dataclass__override__fields__3__annotation:
                return __dataclass__self.__dict__['param2']

            return param2

        setattr(__class__, 'param2', __dataclass__property__param2())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"username={self.username!r}")
            parts.append(f"realname={self.realname!r}")
            parts.append(f"param1={self.param1!r}")
            parts.append(f"param2={self.param2!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('nicknames',)), EqPlan(fields=('nicknames',)), FrozenPlan(fields=('FORMAT', 'REPLI"
        "ES', 'nicknames'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('nicknames',), cache=Fals"
        "e), InitPlan(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields.0.annotation'), default="
        "None, default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None, validate=No"
        "ne, check_type=None), InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fields.1.annotation'), defaul"
        "t=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=True, field_type=FieldType.CL"
        "ASS_VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='nicknames', annotation=OpRef(name="
        "'init.fields.2.annotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, ove"
        "rride=True, field_type=FieldType.INSTANCE, coerce=None, validate=OpRef(name='init.fields.2.validate'), check_t"
        "ype=None)), self_param='self', std_params=('nicknames',), kw_only_params=(), frozen=True, slots=False, post_in"
        "it_params=None, init_fns=(), validate_fns=()), OverridePlan(fields=(OverridePlan.Field(name='nicknames', annot"
        "ation=OpRef(name='override.fields.0.annotation')),), frozen=True), ReprPlan(fields=(ReprPlan.Field(name='nickn"
        "ames', kw_only=False, fn=None),), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='081b371138ece934e9f4e2847c25e2b31b32a8f9',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'UserhostMessage'),
    ),
)
def _process_dataclass__081b371138ece934e9f4e2847c25e2b31b32a8f9():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default,
        __dataclass__init__fields__2__validate,
        __dataclass__override__fields__0__annotation,
        __dataclass__FieldFnValidationError,  # noqa
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                nicknames=self.nicknames,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.nicknames == other.nicknames
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'nicknames',
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
                self.nicknames,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            nicknames: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            if not __dataclass__init__fields__2__validate(nicknames): 
                raise __dataclass__FieldFnValidationError(
                    obj=self,
                    fn=__dataclass__init__fields__2__validate,
                    field='nicknames',
                    value=nicknames,
                )
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['nicknames'] = nicknames

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__nicknames():
            @__dataclass__property
            def nicknames(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['nicknames']

            return nicknames

        setattr(__class__, 'nicknames', __dataclass__property__nicknames())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"nicknames={self.nicknames!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('text',)), EqPlan(fields=('text',)), FrozenPlan(fields=('FORMAT', 'REPLIES', 'text"
        "'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('text',), cache=False), InitPlan(fields="
        "(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factor"
        "y=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_type=None)"
        ", InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.f"
        "ields.1.default'), default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None"
        ", validate=None, check_type=None), InitPlan.Field(name='text', annotation=OpRef(name='init.fields.2.annotation"
        "'), default=None, default_factory=None, init=True, override=True, field_type=FieldType.INSTANCE, coerce=None, "
        "validate=None, check_type=None)), self_param='self', std_params=('text',), kw_only_params=(), frozen=True, slo"
        "ts=False, post_init_params=None, init_fns=(), validate_fns=()), OverridePlan(fields=(OverridePlan.Field(name='"
        "text', annotation=OpRef(name='override.fields.0.annotation')),), frozen=True), ReprPlan(fields=(ReprPlan.Field"
        "(name='text', kw_only=False, fn=None),), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='e15608040bc440e7383ee21984cedb343657d450',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'WallopsMessage'),
    ),
)
def _process_dataclass__e15608040bc440e7383ee21984cedb343657d450():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__override__fields__0__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                text=self.text,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.text == other.text
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'text',
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
                self.text,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            text: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['text'] = text

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__text():
            @__dataclass__property
            def text(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['text']

            return text

        setattr(__class__, 'text', __dataclass__property__text())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"text={self.text!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('mask',)), EqPlan(fields=('mask',)), FrozenPlan(fields=('FORMAT', 'REPLIES', 'mask"
        "'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('mask',), cache=False), InitPlan(fields="
        "(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factor"
        "y=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None, validate=None, check_type=None)"
        ", InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.f"
        "ields.1.default'), default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None"
        ", validate=None, check_type=None), InitPlan.Field(name='mask', annotation=OpRef(name='init.fields.2.annotation"
        "'), default=None, default_factory=None, init=True, override=True, field_type=FieldType.INSTANCE, coerce=None, "
        "validate=None, check_type=None)), self_param='self', std_params=('mask',), kw_only_params=(), frozen=True, slo"
        "ts=False, post_init_params=None, init_fns=(), validate_fns=()), OverridePlan(fields=(OverridePlan.Field(name='"
        "mask', annotation=OpRef(name='override.fields.0.annotation')),), frozen=True), ReprPlan(fields=(ReprPlan.Field"
        "(name='mask', kw_only=False, fn=None),), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='e4fc02392bfb6f8abb932a7deeb8f313a410f966',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'WhoMessage'),
    ),
)
def _process_dataclass__e4fc02392bfb6f8abb932a7deeb8f313a410f966():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__override__fields__0__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                mask=self.mask,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.mask == other.mask
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'mask',
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
                self.mask,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            mask: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['mask'] = mask

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__mask():
            @__dataclass__property
            def mask(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['mask']

            return mask

        setattr(__class__, 'mask', __dataclass__property__mask())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"mask={self.mask!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('nick', 'target')), EqPlan(fields=('nick', 'target')), FrozenPlan(fields=('FORMAT'"
        ", 'REPLIES', 'nick', 'target'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('nick', 'tar"
        "get'), cache=False), InitPlan(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields.0.annot"
        "ation'), default=None, default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce="
        "None, validate=None, check_type=None), InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fields.1.ann"
        "otation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=True, field_"
        "type=FieldType.CLASS_VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='nick', annotation"
        "=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=True, field_t"
        "ype=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='target', annotation"
        "=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default'), default_factory=None, in"
        "it=True, override=True, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_par"
        "am='self', std_params=('nick', 'target'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, "
        "init_fns=(), validate_fns=()), OverridePlan(fields=(OverridePlan.Field(name='nick', annotation=OpRef(name='ove"
        "rride.fields.0.annotation')), OverridePlan.Field(name='target', annotation=OpRef(name='override.fields.1.annot"
        "ation'))), frozen=True), ReprPlan(fields=(ReprPlan.Field(name='nick', kw_only=False, fn=None), ReprPlan.Field("
        "name='target', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='6b3809ef5387c79e1d6041ef7886947d80e3f048',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'WhoisMessage'),
    ),
)
def _process_dataclass__6b3809ef5387c79e1d6041ef7886947d80e3f048():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__3__default,
        __dataclass__override__fields__0__annotation,
        __dataclass__override__fields__1__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                nick=self.nick,
                target=self.target,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.nick == other.nick and
                self.target == other.target
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'nick',
            'target',
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
                self.nick,
                self.target,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            nick: __dataclass__init__fields__2__annotation,
            target: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['nick'] = nick
            __dataclass__self_dict['target'] = target

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__nick():
            @__dataclass__property
            def nick(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['nick']

            return nick

        setattr(__class__, 'nick', __dataclass__property__nick())

        def __dataclass__property__target():
            @__dataclass__property
            def target(__dataclass__self) -> __dataclass__override__fields__1__annotation:
                return __dataclass__self.__dict__['target']

            return target

        setattr(__class__, 'target', __dataclass__property__target())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"nick={self.nick!r}")
            parts.append(f"target={self.target!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('nick', 'count')), EqPlan(fields=('nick', 'count')), FrozenPlan(fields=('FORMAT', "
        "'REPLIES', 'nick', 'count'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('nick', 'count'"
        "), cache=False), InitPlan(fields=(InitPlan.Field(name='FORMAT', annotation=OpRef(name='init.fields.0.annotatio"
        "n'), default=None, default_factory=None, init=True, override=True, field_type=FieldType.CLASS_VAR, coerce=None"
        ", validate=None, check_type=None), InitPlan.Field(name='REPLIES', annotation=OpRef(name='init.fields.1.annotat"
        "ion'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=True, field_type"
        "=FieldType.CLASS_VAR, coerce=None, validate=None, check_type=None), InitPlan.Field(name='nick', annotation=OpR"
        "ef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=True, field_type="
        "FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='count', annotation=OpRe"
        "f(name='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default'), default_factory=None, init=Tr"
        "ue, override=True, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='s"
        "elf', std_params=('nick', 'count'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_f"
        "ns=(), validate_fns=()), OverridePlan(fields=(OverridePlan.Field(name='nick', annotation=OpRef(name='override."
        "fields.0.annotation')), OverridePlan.Field(name='count', annotation=OpRef(name='override.fields.1.annotation')"
        ")), frozen=True), ReprPlan(fields=(ReprPlan.Field(name='nick', kw_only=False, fn=None), ReprPlan.Field(name='c"
        "ount', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='09188aa2d40abb428c0e7b290dbf45a4b94d54e6',
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'WhowasMessage'),
    ),
)
def _process_dataclass__09188aa2d40abb428c0e7b290dbf45a4b94d54e6():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__3__default,
        __dataclass__override__fields__0__annotation,
        __dataclass__override__fields__1__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__property=property,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                nick=self.nick,
                count=self.count,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.nick == other.nick and
                self.count == other.count
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'FORMAT',
            'REPLIES',
            'nick',
            'count',
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
                self.nick,
                self.count,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            nick: __dataclass__init__fields__2__annotation,
            count: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__self_dict = self.__dict__
            __dataclass__self_dict['nick'] = nick
            __dataclass__self_dict['count'] = count

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __dataclass__property__nick():
            @__dataclass__property
            def nick(__dataclass__self) -> __dataclass__override__fields__0__annotation:
                return __dataclass__self.__dict__['nick']

            return nick

        setattr(__class__, 'nick', __dataclass__property__nick())

        def __dataclass__property__count():
            @__dataclass__property
            def count(__dataclass__self) -> __dataclass__override__fields__1__annotation:
                return __dataclass__self.__dict__['count']

            return count

        setattr(__class__, 'count', __dataclass__property__count())

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"nick={self.nick!r}")
            parts.append(f"count={self.count!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('name',)), EqPlan(fields=('name',)), FrozenPlan(fields=('name',), allow_dynamic_du"
        "nder_attrs=False), HashPlan(action='add', fields=('name',), cache=False), InitPlan(fields=(InitPlan.Field(name"
        "='name', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, ove"
        "rride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='self',"
        " std_params=('name',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), valida"
        "te_fns=()), ReprPlan(fields=(ReprPlan.Field(name='name', kw_only=False, fn=None),), id=False, terse=False, def"
        "ault_fn=None)))"
    ),
    plan_repr_sha1='a8c678a92ec79b6aa505feedefe70ee7fef92ccd',
    cls_names=(
        ('omdev.specs.irc.numerics.formats', 'Formats.Name'),
    ),
)
def _process_dataclass__a8c678a92ec79b6aa505feedefe70ee7fef92ccd():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
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
                name=self.name,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
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
                self.name,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('body',)), EqPlan(fields=('body',)), FrozenPlan(fields=('body',), allow_dynamic_du"
        "nder_attrs=False), HashPlan(action='add', fields=('body',), cache=False), InitPlan(fields=(InitPlan.Field(name"
        "='body', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, ove"
        "rride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='self',"
        " std_params=('body',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), valida"
        "te_fns=()), ReprPlan(fields=(ReprPlan.Field(name='body', kw_only=False, fn=None),), id=False, terse=False, def"
        "ault_fn=None)))"
    ),
    plan_repr_sha1='f1ebecfd7b16c38a215b1abc7348bff27ceb4fbf',
    cls_names=(
        ('omdev.specs.irc.numerics.formats', 'Formats.Optional'),
        ('omdev.specs.irc.numerics.formats', 'Formats.Variadic'),
    ),
)
def _process_dataclass__f1ebecfd7b16c38a215b1abc7348bff27ceb4fbf():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
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
                body=self.body,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.body == other.body
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'body',
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
                self.body,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            body: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'body', body)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"body={self.body!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('name', 'num', 'formats')), EqPlan(fields=('name', 'num', 'formats')), FrozenPlan("
        "fields=('name', 'num', 'formats'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('name', '"
        "num', 'formats'), cache=False), InitPlan(fields=(InitPlan.Field(name='name', annotation=OpRef(name='init.field"
        "s.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE"
        ", coerce=None, validate=None, check_type=None), InitPlan.Field(name='num', annotation=OpRef(name='init.fields."
        "1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, "
        "coerce=None, validate=None, check_type=None), InitPlan.Field(name='formats', annotation=OpRef(name='init.field"
        "s.2.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE"
        ", coerce=None, validate=None, check_type=None)), self_param='self', std_params=('name', 'num', 'formats'), kw_"
        "only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(field"
        "s=(ReprPlan.Field(name='name', kw_only=False, fn=None), ReprPlan.Field(name='num', kw_only=False, fn=None), Re"
        "prPlan.Field(name='formats', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='c47995a925cc7ceecc5e19bd212269169a944d0d',
    cls_names=(
        ('omdev.specs.irc.numerics.types', 'NumericReply'),
    ),
)
def _process_dataclass__c47995a925cc7ceecc5e19bd212269169a944d0d():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
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
                name=self.name,
                num=self.num,
                formats=self.formats,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.num == other.num and
                self.formats == other.formats
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'num',
            'formats',
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
                self.name,
                self.num,
                self.formats,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
            num: __dataclass__init__fields__1__annotation,
            formats: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'num', num)
            __dataclass__object_setattr(self, 'formats', formats)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"num={self.num!r}")
            parts.append(f"formats={self.formats!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('source', 'command', 'params', 'force_trailing', 'tags', 'client_only_tags')), EqP"
        "lan(fields=('source', 'command', 'params', 'force_trailing', 'tags', 'client_only_tags')), FrozenPlan(fields=("
        "'source', 'command', 'params', 'force_trailing', 'tags', 'client_only_tags'), allow_dynamic_dunder_attrs=False"
        "), HashPlan(action='add', fields=('source', 'command', 'params', 'force_trailing', 'tags', 'client_only_tags')"
        ", cache=False), InitPlan(fields=(InitPlan.Field(name='source', annotation=OpRef(name='init.fields.0.annotation"
        "'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None,"
        " validate=None, check_type=None), InitPlan.Field(name='command', annotation=OpRef(name='init.fields.1.annotati"
        "on'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=Non"
        "e, validate=None, check_type=None), InitPlan.Field(name='params', annotation=OpRef(name='init.fields.2.annotat"
        "ion'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=No"
        "ne, validate=None, check_type=None), InitPlan.Field(name='force_trailing', annotation=OpRef(name='init.fields."
        "3.annotation'), default=OpRef(name='init.fields.3.default'), default_factory=None, init=True, override=False, "
        "field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='tags', annot"
        "ation=OpRef(name='init.fields.4.annotation'), default=OpRef(name='init.fields.4.default'), default_factory=Non"
        "e, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), Ini"
        "tPlan.Field(name='client_only_tags', annotation=OpRef(name='init.fields.5.annotation'), default=OpRef(name='in"
        "it.fields.5.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce="
        "None, validate=None, check_type=None)), self_param='self', std_params=('source', 'command', 'params', 'force_t"
        "railing', 'tags', 'client_only_tags'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, ini"
        "t_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='source', kw_only=False, fn=None), ReprPlan.F"
        "ield(name='command', kw_only=False, fn=None), ReprPlan.Field(name='params', kw_only=False, fn=None), ReprPlan."
        "Field(name='force_trailing', kw_only=False, fn=None), ReprPlan.Field(name='tags', kw_only=False, fn=None), Rep"
        "rPlan.Field(name='client_only_tags', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='b3c30b0ed6d1c426e0a02a08a25e6f55b9dedff1',
    cls_names=(
        ('omdev.specs.irc.protocol.message', 'Message'),
    ),
)
def _process_dataclass__b3c30b0ed6d1c426e0a02a08a25e6f55b9dedff1():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__3__default,
        __dataclass__init__fields__4__annotation,
        __dataclass__init__fields__4__default,
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
                source=self.source,
                command=self.command,
                params=self.params,
                force_trailing=self.force_trailing,
                tags=self.tags,
                client_only_tags=self.client_only_tags,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.source == other.source and
                self.command == other.command and
                self.params == other.params and
                self.force_trailing == other.force_trailing and
                self.tags == other.tags and
                self.client_only_tags == other.client_only_tags
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'source',
            'command',
            'params',
            'force_trailing',
            'tags',
            'client_only_tags',
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
                self.source,
                self.command,
                self.params,
                self.force_trailing,
                self.tags,
                self.client_only_tags,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            source: __dataclass__init__fields__0__annotation,
            command: __dataclass__init__fields__1__annotation,
            params: __dataclass__init__fields__2__annotation,
            force_trailing: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            tags: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            client_only_tags: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'source', source)
            __dataclass__object_setattr(self, 'command', command)
            __dataclass__object_setattr(self, 'params', params)
            __dataclass__object_setattr(self, 'force_trailing', force_trailing)
            __dataclass__object_setattr(self, 'tags', tags)
            __dataclass__object_setattr(self, 'client_only_tags', client_only_tags)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"source={self.source!r}")
            parts.append(f"command={self.command!r}")
            parts.append(f"params={self.params!r}")
            parts.append(f"force_trailing={self.force_trailing!r}")
            parts.append(f"tags={self.tags!r}")
            parts.append(f"client_only_tags={self.client_only_tags!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('name', 'user', 'host')), EqPlan(fields=('name', 'user', 'host')), FrozenPlan(fiel"
        "ds=('name', 'user', 'host'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('name', 'user',"
        " 'host'), cache=False), InitPlan(fields=(InitPlan.Field(name='name', annotation=OpRef(name='init.fields.0.anno"
        "tation'), default=OpRef(name='init.fields.0.default'), default_factory=None, init=True, override=False, field_"
        "type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='user', annotation="
        "OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, ini"
        "t=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan."
        "Field(name='host', annotation=OpRef(name='init.fields.2.annotation'), default=OpRef(name='init.fields.2.defaul"
        "t'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=Non"
        "e, check_type=None)), self_param='self', std_params=('name', 'user', 'host'), kw_only_params=(), frozen=True, "
        "slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='name'"
        ", kw_only=False, fn=None), ReprPlan.Field(name='user', kw_only=False, fn=None), ReprPlan.Field(name='host', kw"
        "_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='39f37672c909d1e41aacfe4005cd76534720c50d',
    cls_names=(
        ('omdev.specs.irc.protocol.nuh', 'Nuh'),
    ),
)
def _process_dataclass__39f37672c909d1e41aacfe4005cd76534720c50d():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__default,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default,
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
                name=self.name,
                user=self.user,
                host=self.host,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.user == other.user and
                self.host == other.host
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'user',
            'host',
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
                self.name,
                self.user,
                self.host,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            user: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            host: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'user', user)
            __dataclass__object_setattr(self, 'host', host)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"user={self.user!r}")
            parts.append(f"host={self.host!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
