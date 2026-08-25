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
        "Plans(tup=(CopyPlan(fields=()), EqPlan(fields=()), FrozenPlan(fields=(), allow_dynamic_dunder_attrs=False), Ha"
        "shPlan(action='add', fields=(), cache=False), InitPlan(fields=(), self_param='self', std_params=(), kw_only_pa"
        "rams=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(), i"
        "d=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='e1f7edfe11f2b721d6a656c46e698fedc95461bb',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'AuthenticationCleartextPassword'),
        ('omcore.sql.drivers.og8000.protocol.messages', 'AuthenticationOk'),
        ('omcore.sql.drivers.og8000.protocol.messages', 'BindComplete'),
        ('omcore.sql.drivers.og8000.protocol.messages', 'CloseComplete'),
        ('omcore.sql.drivers.og8000.protocol.messages', 'CopyDone'),
        ('omcore.sql.drivers.og8000.protocol.messages', 'EmptyQueryResponse'),
        ('omcore.sql.drivers.og8000.protocol.messages', 'Flush'),
        ('omcore.sql.drivers.og8000.protocol.messages', 'NoData'),
        ('omcore.sql.drivers.og8000.protocol.messages', 'ParseComplete'),
        ('omcore.sql.drivers.og8000.protocol.messages', 'PortalSuspended'),
        ('omcore.sql.drivers.og8000.protocol.messages', 'SslRequest'),
        ('omcore.sql.drivers.og8000.protocol.messages', 'Sync'),
        ('omcore.sql.drivers.og8000.protocol.messages', 'Terminate'),
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
        "Plans(tup=(CopyPlan(fields=('salt',)), EqPlan(fields=('salt',)), FrozenPlan(fields=('salt',), allow_dynamic_du"
        "nder_attrs=False), HashPlan(action='add', fields=('salt',), cache=False), InitPlan(fields=(InitPlan.Field(name"
        "='salt', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, ove"
        "rride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='self',"
        " std_params=('salt',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), valida"
        "te_fns=()), ReprPlan(fields=(ReprPlan.Field(name='salt', kw_only=False, fn=None),), id=False, terse=False, def"
        "ault_fn=None)))"
    ),
    plan_repr_sha1='791ba72d691b7ed01fb80e78c02c525bd925017a',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'AuthenticationMd5Password'),
    ),
)
def _process_dataclass__791ba72d691b7ed01fb80e78c02c525bd925017a():
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
                salt=self.salt,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.salt == other.salt
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'salt',
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
                self.salt,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            salt: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'salt', salt)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"salt={self.salt!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('code', 'data')), EqPlan(fields=('code', 'data')), FrozenPlan(fields=('code', 'dat"
        "a'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('code', 'data'), cache=False), InitPlan"
        "(fields=(InitPlan.Field(name='code', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_"
        "factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type"
        "=None), InitPlan.Field(name='data', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_f"
        "actory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type="
        "None)), self_param='self', std_params=('code', 'data'), kw_only_params=(), frozen=True, slots=False, post_init"
        "_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='code', kw_only=False, fn=No"
        "ne), ReprPlan.Field(name='data', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='0527a8b9c62be65307ec7e0465b1720419b6dade',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'AuthenticationOther'),
    ),
)
def _process_dataclass__0527a8b9c62be65307ec7e0465b1720419b6dade():
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
                code=self.code,
                data=self.data,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.code == other.code and
                self.data == other.data
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'code',
            'data',
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
                self.code,
                self.data,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            code: __dataclass__init__fields__0__annotation,
            data: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'code', code)
            __dataclass__object_setattr(self, 'data', data)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"code={self.code!r}")
            parts.append(f"data={self.data!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('mechanisms',)), EqPlan(fields=('mechanisms',)), FrozenPlan(fields=('mechanisms',)"
        ", allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('mechanisms',), cache=False), InitPlan(fie"
        "lds=(InitPlan.Field(name='mechanisms', annotation=OpRef(name='init.fields.0.annotation'), default=None, defaul"
        "t_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_ty"
        "pe=None),), self_param='self', std_params=('mechanisms',), kw_only_params=(), frozen=True, slots=False, post_i"
        "nit_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='mechanisms', kw_only=Fal"
        "se, fn=None),), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='7ad04be65d14fe8798f6efef3fb9ac676a1af389',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'AuthenticationSasl'),
    ),
)
def _process_dataclass__7ad04be65d14fe8798f6efef3fb9ac676a1af389():
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
                mechanisms=self.mechanisms,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.mechanisms == other.mechanisms
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'mechanisms',
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
                self.mechanisms,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            mechanisms: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'mechanisms', mechanisms)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"mechanisms={self.mechanisms!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('data',)), EqPlan(fields=('data',)), FrozenPlan(fields=('data',), allow_dynamic_du"
        "nder_attrs=False), HashPlan(action='add', fields=('data',), cache=False), InitPlan(fields=(InitPlan.Field(name"
        "='data', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, ove"
        "rride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='self',"
        " std_params=('data',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), valida"
        "te_fns=()), ReprPlan(fields=(ReprPlan.Field(name='data', kw_only=False, fn=None),), id=False, terse=False, def"
        "ault_fn=None)))"
    ),
    plan_repr_sha1='3931abcab6561a093f5364a7941c35ea26f7f722',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'AuthenticationSaslContinue'),
        ('omcore.sql.drivers.og8000.protocol.messages', 'AuthenticationSaslFinal'),
        ('omcore.sql.drivers.og8000.protocol.messages', 'CopyData'),
        ('omcore.sql.drivers.og8000.protocol.messages', 'SaslResponse'),
    ),
)
def _process_dataclass__3931abcab6561a093f5364a7941c35ea26f7f722():
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
                data=self.data,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.data == other.data
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'data',
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
                self.data,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            data: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'data', data)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"data={self.data!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('process_id', 'secret_key')), EqPlan(fields=('process_id', 'secret_key')), FrozenP"
        "lan(fields=('process_id', 'secret_key'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('pr"
        "ocess_id', 'secret_key'), cache=False), InitPlan(fields=(InitPlan.Field(name='process_id', annotation=OpRef(na"
        "me='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=Fiel"
        "dType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='secret_key', annotation=OpR"
        "ef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, field_type"
        "=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('process_id"
        "', 'secret_key'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fn"
        "s=()), ReprPlan(fields=(ReprPlan.Field(name='process_id', kw_only=False, fn=None), ReprPlan.Field(name='secret"
        "_key', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='b92f6667cca0c711393df4bbb6f42929a0e52a23',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'BackendKeyData'),
    ),
)
def _process_dataclass__b92f6667cca0c711393df4bbb6f42929a0e52a23():
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
                process_id=self.process_id,
                secret_key=self.secret_key,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.process_id == other.process_id and
                self.secret_key == other.secret_key
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'process_id',
            'secret_key',
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
                self.process_id,
                self.secret_key,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            process_id: __dataclass__init__fields__0__annotation,
            secret_key: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'process_id', process_id)
            __dataclass__object_setattr(self, 'secret_key', secret_key)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"process_id={self.process_id!r}")
            parts.append(f"secret_key={self.secret_key!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('portal', 'statement', 'params')), EqPlan(fields=('portal', 'statement', 'params')"
        "), FrozenPlan(fields=('portal', 'statement', 'params'), allow_dynamic_dunder_attrs=False), HashPlan(action='ad"
        "d', fields=('portal', 'statement', 'params'), cache=False), InitPlan(fields=(InitPlan.Field(name='portal', ann"
        "otation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False,"
        " field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='statement',"
        " annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override=Fa"
        "lse, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='params'"
        ", annotation=OpRef(name='init.fields.2.annotation'), default=OpRef(name='init.fields.2.default'), default_fact"
        "ory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=Non"
        "e)), self_param='self', std_params=('portal', 'statement', 'params'), kw_only_params=(), frozen=True, slots=Fa"
        "lse, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='portal', kw_o"
        "nly=False, fn=None), ReprPlan.Field(name='statement', kw_only=False, fn=None), ReprPlan.Field(name='params', k"
        "w_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='677d5839f0d1668611b84d406aa03da796e0d545',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'Bind'),
    ),
)
def _process_dataclass__677d5839f0d1668611b84d406aa03da796e0d545():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
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
                portal=self.portal,
                statement=self.statement,
                params=self.params,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.portal == other.portal and
                self.statement == other.statement and
                self.params == other.params
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'portal',
            'statement',
            'params',
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
                self.portal,
                self.statement,
                self.params,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            portal: __dataclass__init__fields__0__annotation,
            statement: __dataclass__init__fields__1__annotation,
            params: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'portal', portal)
            __dataclass__object_setattr(self, 'statement', statement)
            __dataclass__object_setattr(self, 'params', params)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"portal={self.portal!r}")
            parts.append(f"statement={self.statement!r}")
            parts.append(f"params={self.params!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('kind', 'name')), EqPlan(fields=('kind', 'name')), FrozenPlan(fields=('kind', 'nam"
        "e'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('kind', 'name'), cache=False), InitPlan"
        "(fields=(InitPlan.Field(name='kind', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_"
        "factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type"
        "=None), InitPlan.Field(name='name', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_f"
        "actory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type="
        "None)), self_param='self', std_params=('kind', 'name'), kw_only_params=(), frozen=True, slots=False, post_init"
        "_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='kind', kw_only=False, fn=No"
        "ne), ReprPlan.Field(name='name', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='310fe3cbd6f71a15ddffacb9a6f1a4e345bcfa0c',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'Close'),
        ('omcore.sql.drivers.og8000.protocol.messages', 'Describe'),
    ),
)
def _process_dataclass__310fe3cbd6f71a15ddffacb9a6f1a4e345bcfa0c():
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
                kind=self.kind,
                name=self.name,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.kind == other.kind and
                self.name == other.name
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'kind',
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
                self.kind,
                self.name,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            kind: __dataclass__init__fields__0__annotation,
            name: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'kind', kind)
            __dataclass__object_setattr(self, 'name', name)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"kind={self.kind!r}")
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
        "Plans(tup=(CopyPlan(fields=('tag',)), EqPlan(fields=('tag',)), FrozenPlan(fields=('tag',), allow_dynamic_dunde"
        "r_attrs=False), HashPlan(action='add', fields=('tag',), cache=False), InitPlan(fields=(InitPlan.Field(name='ta"
        "g', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override"
        "=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='self', std_"
        "params=('tag',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns"
        "=()), ReprPlan(fields=(ReprPlan.Field(name='tag', kw_only=False, fn=None),), id=False, terse=False, default_fn"
        "=None)))"
    ),
    plan_repr_sha1='74a1bdcc3cd4338d1bb04cdc435bf6d82caf7517',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'CommandComplete'),
    ),
)
def _process_dataclass__74a1bdcc3cd4338d1bb04cdc435bf6d82caf7517():
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
                tag=self.tag,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.tag == other.tag
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'tag',
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
                self.tag,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            tag: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'tag', tag)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"tag={self.tag!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('message',)), EqPlan(fields=('message',)), FrozenPlan(fields=('message',), allow_d"
        "ynamic_dunder_attrs=False), HashPlan(action='add', fields=('message',), cache=False), InitPlan(fields=(InitPla"
        "n.Field(name='message', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None,"
        " init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), sel"
        "f_param='self', std_params=('message',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, i"
        "nit_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='message', kw_only=False, fn=None),), id=Fa"
        "lse, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='824edbf0c69a77060c728451cc009c800d8bc247',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'CopyFail'),
    ),
)
def _process_dataclass__824edbf0c69a77060c728451cc009c800d8bc247():
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
                message=self.message,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.message == other.message
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'message',
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
                self.message,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            message: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'message', message)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"message={self.message!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('is_binary', 'column_formats')), EqPlan(fields=('is_binary', 'column_formats')), F"
        "rozenPlan(fields=('is_binary', 'column_formats'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fi"
        "elds=('is_binary', 'column_formats'), cache=False), InitPlan(fields=(InitPlan.Field(name='is_binary', annotati"
        "on=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, fiel"
        "d_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='column_formats',"
        " annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override=Fa"
        "lse, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_para"
        "ms=('is_binary', 'column_formats'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_f"
        "ns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='is_binary', kw_only=False, fn=None), ReprPlan.F"
        "ield(name='column_formats', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='bb0ffcc83d7c43710d102c3cd52f6efa1faa1097',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'CopyInResponse'),
        ('omcore.sql.drivers.og8000.protocol.messages', 'CopyOutResponse'),
    ),
)
def _process_dataclass__bb0ffcc83d7c43710d102c3cd52f6efa1faa1097():
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
                is_binary=self.is_binary,
                column_formats=self.column_formats,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.is_binary == other.is_binary and
                self.column_formats == other.column_formats
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'is_binary',
            'column_formats',
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
                self.is_binary,
                self.column_formats,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            is_binary: __dataclass__init__fields__0__annotation,
            column_formats: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'is_binary', is_binary)
            __dataclass__object_setattr(self, 'column_formats', column_formats)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"is_binary={self.is_binary!r}")
            parts.append(f"column_formats={self.column_formats!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('values',)), EqPlan(fields=('values',)), FrozenPlan(fields=('values',), allow_dyna"
        "mic_dunder_attrs=False), HashPlan(action='add', fields=('values',), cache=False), InitPlan(fields=(InitPlan.Fi"
        "eld(name='values', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init"
        "=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_par"
        "am='self', std_params=('values',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fn"
        "s=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='values', kw_only=False, fn=None),), id=False, te"
        "rse=False, default_fn=None)))"
    ),
    plan_repr_sha1='a7abe5eeac180c2c591f3d3a53805368068716bd',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'DataRow'),
    ),
)
def _process_dataclass__a7abe5eeac180c2c591f3d3a53805368068716bd():
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
                values=self.values,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.values == other.values
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'values',
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
                self.values,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            values: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'values', values)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"values={self.values!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('fields',)), EqPlan(fields=('fields',)), FrozenPlan(fields=('fields',), allow_dyna"
        "mic_dunder_attrs=False), HashPlan(action='add', fields=('fields',), cache=False), InitPlan(fields=(InitPlan.Fi"
        "eld(name='fields', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init"
        "=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_par"
        "am='self', std_params=('fields',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fn"
        "s=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='fields', kw_only=False, fn=None),), id=False, te"
        "rse=False, default_fn=None)))"
    ),
    plan_repr_sha1='ccb42473f47d1af901c59888f92592a2ab833a98',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'ErrorResponse'),
        ('omcore.sql.drivers.og8000.protocol.messages', 'NoticeResponse'),
        ('omcore.sql.drivers.og8000.protocol.messages', 'RowDescription'),
    ),
)
def _process_dataclass__ccb42473f47d1af901c59888f92592a2ab833a98():
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
                fields=self.fields,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.fields == other.fields
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'fields',
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
                self.fields,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            fields: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'fields', fields)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"fields={self.fields!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('portal', 'max_rows')), EqPlan(fields=('portal', 'max_rows')), FrozenPlan(fields=("
        "'portal', 'max_rows'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('portal', 'max_rows')"
        ", cache=False), InitPlan(fields=(InitPlan.Field(name='portal', annotation=OpRef(name='init.fields.0.annotation"
        "'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None,"
        " validate=None, check_type=None), InitPlan.Field(name='max_rows', annotation=OpRef(name='init.fields.1.annotat"
        "ion'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False, field_typ"
        "e=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('portal', "
        "'max_rows'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=())"
        ", ReprPlan(fields=(ReprPlan.Field(name='portal', kw_only=False, fn=None), ReprPlan.Field(name='max_rows', kw_o"
        "nly=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='c0a83733421c4a65ec03f135c18ab2e8c697cc72',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'Execute'),
    ),
)
def _process_dataclass__c0a83733421c4a65ec03f135c18ab2e8c697cc72():
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
                portal=self.portal,
                max_rows=self.max_rows,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.portal == other.portal and
                self.max_rows == other.max_rows
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'portal',
            'max_rows',
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
                self.portal,
                self.max_rows,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            portal: __dataclass__init__fields__0__annotation,
            max_rows: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'portal', portal)
            __dataclass__object_setattr(self, 'max_rows', max_rows)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"portal={self.portal!r}")
            parts.append(f"max_rows={self.max_rows!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('name', 'table_oid', 'column_attrnum', 'type_oid', 'type_size', 'type_modifier', '"
        "format_code')), EqPlan(fields=('name', 'table_oid', 'column_attrnum', 'type_oid', 'type_size', 'type_modifier'"
        ", 'format_code')), FrozenPlan(fields=('name', 'table_oid', 'column_attrnum', 'type_oid', 'type_size', 'type_mo"
        "difier', 'format_code'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('name', 'table_oid'"
        ", 'column_attrnum', 'type_oid', 'type_size', 'type_modifier', 'format_code'), cache=False), InitPlan(fields=(I"
        "nitPlan.Field(name='name', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=No"
        "ne, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), In"
        "itPlan.Field(name='table_oid', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factor"
        "y=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)"
        ", InitPlan.Field(name='column_attrnum', annotation=OpRef(name='init.fields.2.annotation'), default=None, defau"
        "lt_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_t"
        "ype=None), InitPlan.Field(name='type_oid', annotation=OpRef(name='init.fields.3.annotation'), default=None, de"
        "fault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, chec"
        "k_type=None), InitPlan.Field(name='type_size', annotation=OpRef(name='init.fields.4.annotation'), default=None"
        ", default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, "
        "check_type=None), InitPlan.Field(name='type_modifier', annotation=OpRef(name='init.fields.5.annotation'), defa"
        "ult=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validat"
        "e=None, check_type=None), InitPlan.Field(name='format_code', annotation=OpRef(name='init.fields.6.annotation')"
        ", default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, v"
        "alidate=None, check_type=None)), self_param='self', std_params=('name', 'table_oid', 'column_attrnum', 'type_o"
        "id', 'type_size', 'type_modifier', 'format_code'), kw_only_params=(), frozen=True, slots=False, post_init_para"
        "ms=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='name', kw_only=False, fn=None), "
        "ReprPlan.Field(name='table_oid', kw_only=False, fn=None), ReprPlan.Field(name='column_attrnum', kw_only=False,"
        " fn=None), ReprPlan.Field(name='type_oid', kw_only=False, fn=None), ReprPlan.Field(name='type_size', kw_only=F"
        "alse, fn=None), ReprPlan.Field(name='type_modifier', kw_only=False, fn=None), ReprPlan.Field(name='format_code"
        "', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='01d8691af70e493b0aa0e2fabeffe79688d0b504',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'FieldDescription'),
    ),
)
def _process_dataclass__01d8691af70e493b0aa0e2fabeffe79688d0b504():
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
                name=self.name,
                table_oid=self.table_oid,
                column_attrnum=self.column_attrnum,
                type_oid=self.type_oid,
                type_size=self.type_size,
                type_modifier=self.type_modifier,
                format_code=self.format_code,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.table_oid == other.table_oid and
                self.column_attrnum == other.column_attrnum and
                self.type_oid == other.type_oid and
                self.type_size == other.type_size and
                self.type_modifier == other.type_modifier and
                self.format_code == other.format_code
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'table_oid',
            'column_attrnum',
            'type_oid',
            'type_size',
            'type_modifier',
            'format_code',
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
                self.table_oid,
                self.column_attrnum,
                self.type_oid,
                self.type_size,
                self.type_modifier,
                self.format_code,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
            table_oid: __dataclass__init__fields__1__annotation,
            column_attrnum: __dataclass__init__fields__2__annotation,
            type_oid: __dataclass__init__fields__3__annotation,
            type_size: __dataclass__init__fields__4__annotation,
            type_modifier: __dataclass__init__fields__5__annotation,
            format_code: __dataclass__init__fields__6__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'table_oid', table_oid)
            __dataclass__object_setattr(self, 'column_attrnum', column_attrnum)
            __dataclass__object_setattr(self, 'type_oid', type_oid)
            __dataclass__object_setattr(self, 'type_size', type_size)
            __dataclass__object_setattr(self, 'type_modifier', type_modifier)
            __dataclass__object_setattr(self, 'format_code', format_code)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"table_oid={self.table_oid!r}")
            parts.append(f"column_attrnum={self.column_attrnum!r}")
            parts.append(f"type_oid={self.type_oid!r}")
            parts.append(f"type_size={self.type_size!r}")
            parts.append(f"type_modifier={self.type_modifier!r}")
            parts.append(f"format_code={self.format_code!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('process_id', 'channel', 'payload')), EqPlan(fields=('process_id', 'channel', 'pay"
        "load')), FrozenPlan(fields=('process_id', 'channel', 'payload'), allow_dynamic_dunder_attrs=False), HashPlan(a"
        "ction='add', fields=('process_id', 'channel', 'payload'), cache=False), InitPlan(fields=(InitPlan.Field(name='"
        "process_id', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True,"
        " override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(n"
        "ame='channel', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=Tru"
        "e, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field"
        "(name='payload', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=T"
        "rue, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param="
        "'self', std_params=('process_id', 'channel', 'payload'), kw_only_params=(), frozen=True, slots=False, post_ini"
        "t_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='process_id', kw_only=False"
        ", fn=None), ReprPlan.Field(name='channel', kw_only=False, fn=None), ReprPlan.Field(name='payload', kw_only=Fal"
        "se, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='19d9f9fe2d6cea593db18941f663b2c5633f8454',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'NotificationResponse'),
    ),
)
def _process_dataclass__19d9f9fe2d6cea593db18941f663b2c5633f8454():
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
                process_id=self.process_id,
                channel=self.channel,
                payload=self.payload,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.process_id == other.process_id and
                self.channel == other.channel and
                self.payload == other.payload
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'process_id',
            'channel',
            'payload',
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
                self.process_id,
                self.channel,
                self.payload,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            process_id: __dataclass__init__fields__0__annotation,
            channel: __dataclass__init__fields__1__annotation,
            payload: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'process_id', process_id)
            __dataclass__object_setattr(self, 'channel', channel)
            __dataclass__object_setattr(self, 'payload', payload)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"process_id={self.process_id!r}")
            parts.append(f"channel={self.channel!r}")
            parts.append(f"payload={self.payload!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('type_oids',)), EqPlan(fields=('type_oids',)), FrozenPlan(fields=('type_oids',), a"
        "llow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('type_oids',), cache=False), InitPlan(fields="
        "(InitPlan.Field(name='type_oids', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_fac"
        "tory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=No"
        "ne),), self_param='self', std_params=('type_oids',), kw_only_params=(), frozen=True, slots=False, post_init_pa"
        "rams=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='type_oids', kw_only=False, fn="
        "None),), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='532df4d4c4ee853048b2d4cee3c2c898b9191a5e',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'ParameterDescription'),
    ),
)
def _process_dataclass__532df4d4c4ee853048b2d4cee3c2c898b9191a5e():
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
                type_oids=self.type_oids,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type_oids == other.type_oids
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'type_oids',
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
                self.type_oids,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            type_oids: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'type_oids', type_oids)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"type_oids={self.type_oids!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('name', 'value')), EqPlan(fields=('name', 'value')), FrozenPlan(fields=('name', 'v"
        "alue'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('name', 'value'), cache=False), Init"
        "Plan(fields=(InitPlan.Field(name='name', annotation=OpRef(name='init.fields.0.annotation'), default=None, defa"
        "ult_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_"
        "type=None), InitPlan.Field(name='value', annotation=OpRef(name='init.fields.1.annotation'), default=None, defa"
        "ult_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_"
        "type=None)), self_param='self', std_params=('name', 'value'), kw_only_params=(), frozen=True, slots=False, pos"
        "t_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='name', kw_only=False,"
        " fn=None), ReprPlan.Field(name='value', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='3e40309e2b73f8abf9df2dea7473d3ea0bbbfad7',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'ParameterStatus'),
    ),
)
def _process_dataclass__3e40309e2b73f8abf9df2dea7473d3ea0bbbfad7():
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
                name=self.name,
                value=self.value,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.value == other.value
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'value',
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
                self.value,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
            value: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'value', value)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"value={self.value!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('name', 'sql', 'type_oids')), EqPlan(fields=('name', 'sql', 'type_oids')), FrozenP"
        "lan(fields=('name', 'sql', 'type_oids'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('na"
        "me', 'sql', 'type_oids'), cache=False), InitPlan(fields=(InitPlan.Field(name='name', annotation=OpRef(name='in"
        "it.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType."
        "INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='sql', annotation=OpRef(name='init"
        ".fields.1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.IN"
        "STANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='type_oids', annotation=OpRef(name='"
        "init.fields.2.annotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, over"
        "ride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', s"
        "td_params=('name', 'sql', 'type_oids'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, in"
        "it_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='name', kw_only=False, fn=None), ReprPlan.Fi"
        "eld(name='sql', kw_only=False, fn=None), ReprPlan.Field(name='type_oids', kw_only=False, fn=None)), id=False, "
        "terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='e0646bc6ab243d7da23ce41e667e81fe72ac134d',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'Parse'),
    ),
)
def _process_dataclass__e0646bc6ab243d7da23ce41e667e81fe72ac134d():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
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
                sql=self.sql,
                type_oids=self.type_oids,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.sql == other.sql and
                self.type_oids == other.type_oids
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'sql',
            'type_oids',
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
                self.sql,
                self.type_oids,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
            sql: __dataclass__init__fields__1__annotation,
            type_oids: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'sql', sql)
            __dataclass__object_setattr(self, 'type_oids', type_oids)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"sql={self.sql!r}")
            parts.append(f"type_oids={self.type_oids!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('password',)), EqPlan(fields=('password',)), FrozenPlan(fields=('password',), allo"
        "w_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('password',), cache=False), InitPlan(fields=(Ini"
        "tPlan.Field(name='password', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory="
        "None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),)"
        ", self_param='self', std_params=('password',), kw_only_params=(), frozen=True, slots=False, post_init_params=N"
        "one, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='password', kw_only=False, fn=None),)"
        ", id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='84d35def3afabfbe44653787c70f18a3fc7dc8c4',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'PasswordMessage'),
    ),
)
def _process_dataclass__84d35def3afabfbe44653787c70f18a3fc7dc8c4():
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
            password: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'password', password)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

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
        "Plans(tup=(CopyPlan(fields=('sql',)), EqPlan(fields=('sql',)), FrozenPlan(fields=('sql',), allow_dynamic_dunde"
        "r_attrs=False), HashPlan(action='add', fields=('sql',), cache=False), InitPlan(fields=(InitPlan.Field(name='sq"
        "l', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override"
        "=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='self', std_"
        "params=('sql',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns"
        "=()), ReprPlan(fields=(ReprPlan.Field(name='sql', kw_only=False, fn=None),), id=False, terse=False, default_fn"
        "=None)))"
    ),
    plan_repr_sha1='3d9d52b377500f3e09ac6ce01e26fb1e8fab1975',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'Query'),
    ),
)
def _process_dataclass__3d9d52b377500f3e09ac6ce01e26fb1e8fab1975():
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
                sql=self.sql,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.sql == other.sql
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'sql',
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
                self.sql,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            sql: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'sql', sql)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"sql={self.sql!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('status',)), EqPlan(fields=('status',)), FrozenPlan(fields=('status',), allow_dyna"
        "mic_dunder_attrs=False), HashPlan(action='add', fields=('status',), cache=False), InitPlan(fields=(InitPlan.Fi"
        "eld(name='status', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init"
        "=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_par"
        "am='self', std_params=('status',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fn"
        "s=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='status', kw_only=False, fn=None),), id=False, te"
        "rse=False, default_fn=None)))"
    ),
    plan_repr_sha1='685f84a91290bd1a2994d81cf15cdc2231a889e3',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'ReadyForQuery'),
    ),
)
def _process_dataclass__685f84a91290bd1a2994d81cf15cdc2231a889e3():
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
                status=self.status,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.status == other.status
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'status',
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
                self.status,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            status: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'status', status)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"status={self.status!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('mechanism', 'data')), EqPlan(fields=('mechanism', 'data')), FrozenPlan(fields=('m"
        "echanism', 'data'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('mechanism', 'data'), ca"
        "che=False), InitPlan(fields=(InitPlan.Field(name='mechanism', annotation=OpRef(name='init.fields.0.annotation'"
        "), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, "
        "validate=None, check_type=None), InitPlan.Field(name='data', annotation=OpRef(name='init.fields.1.annotation')"
        ", default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, v"
        "alidate=None, check_type=None)), self_param='self', std_params=('mechanism', 'data'), kw_only_params=(), froze"
        "n=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(nam"
        "e='mechanism', kw_only=False, fn=None), ReprPlan.Field(name='data', kw_only=False, fn=None)), id=False, terse="
        "False, default_fn=None)))"
    ),
    plan_repr_sha1='b57cc0dc5df850ca2e99b1409d1f3d5ac1155ac9',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'SaslInitialResponse'),
    ),
)
def _process_dataclass__b57cc0dc5df850ca2e99b1409d1f3d5ac1155ac9():
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
                mechanism=self.mechanism,
                data=self.data,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.mechanism == other.mechanism and
                self.data == other.data
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'mechanism',
            'data',
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
                self.mechanism,
                self.data,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            mechanism: __dataclass__init__fields__0__annotation,
            data: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'mechanism', mechanism)
            __dataclass__object_setattr(self, 'data', data)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"mechanism={self.mechanism!r}")
            parts.append(f"data={self.data!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('accepted',)), EqPlan(fields=('accepted',)), FrozenPlan(fields=('accepted',), allo"
        "w_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('accepted',), cache=False), InitPlan(fields=(Ini"
        "tPlan.Field(name='accepted', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory="
        "None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),)"
        ", self_param='self', std_params=('accepted',), kw_only_params=(), frozen=True, slots=False, post_init_params=N"
        "one, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='accepted', kw_only=False, fn=None),)"
        ", id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='21fc7dc37d1774d17b39d935727283e97d52d5f1',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'SslResponse'),
    ),
)
def _process_dataclass__21fc7dc37d1774d17b39d935727283e97d52d5f1():
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
                accepted=self.accepted,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.accepted == other.accepted
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'accepted',
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
                self.accepted,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            accepted: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'accepted', accepted)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"accepted={self.accepted!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('params',)), EqPlan(fields=('params',)), FrozenPlan(fields=('params',), allow_dyna"
        "mic_dunder_attrs=False), HashPlan(action='add', fields=('params',), cache=False), InitPlan(fields=(InitPlan.Fi"
        "eld(name='params', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init"
        "=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_par"
        "am='self', std_params=('params',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fn"
        "s=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='params', kw_only=False, fn=None),), id=False, te"
        "rse=False, default_fn=None)))"
    ),
    plan_repr_sha1='9abd7c34aef7de188f3668b5cbddb1a7daaf8022',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.messages', 'StartupMessage'),
    ),
)
def _process_dataclass__9abd7c34aef7de188f3668b5cbddb1a7daaf8022():
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
                params=self.params,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.params == other.params
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'params',
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
                self.params,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            params: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'params', params)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"params={self.params!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('messages', 'more')), EqPlan(fields=('messages', 'more')), FrozenPlan(fields=('mes"
        "sages', 'more'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('messages', 'more'), cache="
        "False), InitPlan(fields=(InitPlan.Field(name='messages', annotation=OpRef(name='init.fields.0.annotation'), de"
        "fault=OpRef(name='init.fields.0.default'), default_factory=None, init=True, override=False, field_type=FieldTy"
        "pe.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='more', annotation=OpRef(name='"
        "init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, over"
        "ride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', s"
        "td_params=('messages', 'more'), kw_only_params=(), frozen=True, slots=False, post_init_params=(), init_fns=(),"
        " validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='messages', kw_only=False, fn=None), ReprPlan.Field(na"
        "me='more', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='93f9d7f890f99b379589caafb0ed5ed91edc7ec5',
    cls_names=(
        ('omcore.sql.drivers.og8000.protocol.session', 'Step'),
    ),
)
def _process_dataclass__93f9d7f890f99b379589caafb0ed5ed91edc7ec5():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__default,
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
                messages=self.messages,
                more=self.more,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.messages == other.messages and
                self.more == other.more
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'messages',
            'more',
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
                self.messages,
                self.more,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            messages: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            more: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'messages', messages)
            __dataclass__object_setattr(self, 'more', more)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"messages={self.messages!r}")
            parts.append(f"more={self.more!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
