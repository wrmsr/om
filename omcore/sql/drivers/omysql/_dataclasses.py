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
        "Plans(tup=(CopyPlan(fields=('payload',)), EqPlan(fields=('payload',)), FrozenPlan(fields=('payload',), allow_d"
        "ynamic_dunder_attrs=False), HashPlan(action='add', fields=('payload',), cache=False), InitPlan(fields=(InitPla"
        "n.Field(name='payload', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None,"
        " init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), sel"
        "f_param='self', std_params=('payload',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, i"
        "nit_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='payload', kw_only=False, fn=None),), id=Fa"
        "lse, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='a8307fd0ee10cd563d5a4729551ee6543baad69d',
    cls_names=(
        ('omcore.sql.drivers.omysql.core.handlers', 'ServerPacket'),
    ),
)
def _process_dataclass__a8307fd0ee10cd563d5a4729551ee6543baad69d():
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
                payload=self.payload,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.payload == other.payload
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
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
                self.payload,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            payload: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'payload', payload)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
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
        ('omcore.sql.drivers.omysql.protocol.messages', 'AuthMoreData'),
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
        "Plans(tup=(CopyPlan(fields=('plugin_name', 'data')), EqPlan(fields=('plugin_name', 'data')), FrozenPlan(fields"
        "=('plugin_name', 'data'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('plugin_name', 'da"
        "ta'), cache=False), InitPlan(fields=(InitPlan.Field(name='plugin_name', annotation=OpRef(name='init.fields.0.a"
        "nnotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coe"
        "rce=None, validate=None, check_type=None), InitPlan.Field(name='data', annotation=OpRef(name='init.fields.1.an"
        "notation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coer"
        "ce=None, validate=None, check_type=None)), self_param='self', std_params=('plugin_name', 'data'), kw_only_para"
        "ms=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPl"
        "an.Field(name='plugin_name', kw_only=False, fn=None), ReprPlan.Field(name='data', kw_only=False, fn=None)), id"
        "=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='3a097468a320bb8ba18c8822ac2dd5f9af0b62b6',
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.messages', 'AuthSwitchRequest'),
    ),
)
def _process_dataclass__3a097468a320bb8ba18c8822ac2dd5f9af0b62b6():
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
                plugin_name=self.plugin_name,
                data=self.data,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.plugin_name == other.plugin_name and
                self.data == other.data
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'plugin_name',
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
                self.plugin_name,
                self.data,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            plugin_name: __dataclass__init__fields__0__annotation,
            data: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'plugin_name', plugin_name)
            __dataclass__object_setattr(self, 'data', data)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"plugin_name={self.plugin_name!r}")
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
        "Plans(tup=(CopyPlan(fields=('catalog', 'db', 'table_name', 'org_table', 'name', 'org_name', 'charsetnr', 'leng"
        "th', 'type_code', 'flags', 'scale')), EqPlan(fields=('catalog', 'db', 'table_name', 'org_table', 'name', 'org_"
        "name', 'charsetnr', 'length', 'type_code', 'flags', 'scale')), FrozenPlan(fields=('catalog', 'db', 'table_name"
        "', 'org_table', 'name', 'org_name', 'charsetnr', 'length', 'type_code', 'flags', 'scale'), allow_dynamic_dunde"
        "r_attrs=False), HashPlan(action='add', fields=('catalog', 'db', 'table_name', 'org_table', 'name', 'org_name',"
        " 'charsetnr', 'length', 'type_code', 'flags', 'scale'), cache=False), InitPlan(fields=(InitPlan.Field(name='ca"
        "talog', annotation=OpRef(name='init.fields.00.annotation'), default=None, default_factory=None, init=True, ove"
        "rride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name="
        "'db', annotation=OpRef(name='init.fields.01.annotation'), default=None, default_factory=None, init=True, overr"
        "ide=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='t"
        "able_name', annotation=OpRef(name='init.fields.02.annotation'), default=None, default_factory=None, init=True,"
        " override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(n"
        "ame='org_table', annotation=OpRef(name='init.fields.03.annotation'), default=None, default_factory=None, init="
        "True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Fi"
        "eld(name='name', annotation=OpRef(name='init.fields.04.annotation'), default=None, default_factory=None, init="
        "True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Fi"
        "eld(name='org_name', annotation=OpRef(name='init.fields.05.annotation'), default=None, default_factory=None, i"
        "nit=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPla"
        "n.Field(name='charsetnr', annotation=OpRef(name='init.fields.06.annotation'), default=None, default_factory=No"
        "ne, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), In"
        "itPlan.Field(name='length', annotation=OpRef(name='init.fields.07.annotation'), default=None, default_factory="
        "None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), "
        "InitPlan.Field(name='type_code', annotation=OpRef(name='init.fields.08.annotation'), default=None, default_fac"
        "tory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=No"
        "ne), InitPlan.Field(name='flags', annotation=OpRef(name='init.fields.09.annotation'), default=None, default_fa"
        "ctory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=N"
        "one), InitPlan.Field(name='scale', annotation=OpRef(name='init.fields.10.annotation'), default=None, default_f"
        "actory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type="
        "None)), self_param='self', std_params=('catalog', 'db', 'table_name', 'org_table', 'name', 'org_name', 'charse"
        "tnr', 'length', 'type_code', 'flags', 'scale'), kw_only_params=(), frozen=True, slots=False, post_init_params="
        "None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='catalog', kw_only=False, fn=None), "
        "ReprPlan.Field(name='db', kw_only=False, fn=None), ReprPlan.Field(name='table_name', kw_only=False, fn=None), "
        "ReprPlan.Field(name='org_table', kw_only=False, fn=None), ReprPlan.Field(name='name', kw_only=False, fn=None),"
        " ReprPlan.Field(name='org_name', kw_only=False, fn=None), ReprPlan.Field(name='charsetnr', kw_only=False, fn=N"
        "one), ReprPlan.Field(name='length', kw_only=False, fn=None), ReprPlan.Field(name='type_code', kw_only=False, f"
        "n=None), ReprPlan.Field(name='flags', kw_only=False, fn=None), ReprPlan.Field(name='scale', kw_only=False, fn="
        "None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='0a03aae566b4bced2756dee22243dba484a8513c',
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.messages', 'ColumnDefinition'),
    ),
)
def _process_dataclass__0a03aae566b4bced2756dee22243dba484a8513c():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__00__annotation,
        __dataclass__init__fields__01__annotation,
        __dataclass__init__fields__02__annotation,
        __dataclass__init__fields__03__annotation,
        __dataclass__init__fields__04__annotation,
        __dataclass__init__fields__05__annotation,
        __dataclass__init__fields__06__annotation,
        __dataclass__init__fields__07__annotation,
        __dataclass__init__fields__08__annotation,
        __dataclass__init__fields__09__annotation,
        __dataclass__init__fields__10__annotation,
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
                catalog=self.catalog,
                db=self.db,
                table_name=self.table_name,
                org_table=self.org_table,
                name=self.name,
                org_name=self.org_name,
                charsetnr=self.charsetnr,
                length=self.length,
                type_code=self.type_code,
                flags=self.flags,
                scale=self.scale,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.catalog == other.catalog and
                self.db == other.db and
                self.table_name == other.table_name and
                self.org_table == other.org_table and
                self.name == other.name and
                self.org_name == other.org_name and
                self.charsetnr == other.charsetnr and
                self.length == other.length and
                self.type_code == other.type_code and
                self.flags == other.flags and
                self.scale == other.scale
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'catalog',
            'db',
            'table_name',
            'org_table',
            'name',
            'org_name',
            'charsetnr',
            'length',
            'type_code',
            'flags',
            'scale',
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
                self.catalog,
                self.db,
                self.table_name,
                self.org_table,
                self.name,
                self.org_name,
                self.charsetnr,
                self.length,
                self.type_code,
                self.flags,
                self.scale,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            catalog: __dataclass__init__fields__00__annotation,
            db: __dataclass__init__fields__01__annotation,
            table_name: __dataclass__init__fields__02__annotation,
            org_table: __dataclass__init__fields__03__annotation,
            name: __dataclass__init__fields__04__annotation,
            org_name: __dataclass__init__fields__05__annotation,
            charsetnr: __dataclass__init__fields__06__annotation,
            length: __dataclass__init__fields__07__annotation,
            type_code: __dataclass__init__fields__08__annotation,
            flags: __dataclass__init__fields__09__annotation,
            scale: __dataclass__init__fields__10__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'catalog', catalog)
            __dataclass__object_setattr(self, 'db', db)
            __dataclass__object_setattr(self, 'table_name', table_name)
            __dataclass__object_setattr(self, 'org_table', org_table)
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'org_name', org_name)
            __dataclass__object_setattr(self, 'charsetnr', charsetnr)
            __dataclass__object_setattr(self, 'length', length)
            __dataclass__object_setattr(self, 'type_code', type_code)
            __dataclass__object_setattr(self, 'flags', flags)
            __dataclass__object_setattr(self, 'scale', scale)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"catalog={self.catalog!r}")
            parts.append(f"db={self.db!r}")
            parts.append(f"table_name={self.table_name!r}")
            parts.append(f"org_table={self.org_table!r}")
            parts.append(f"name={self.name!r}")
            parts.append(f"org_name={self.org_name!r}")
            parts.append(f"charsetnr={self.charsetnr!r}")
            parts.append(f"length={self.length!r}")
            parts.append(f"type_code={self.type_code!r}")
            parts.append(f"flags={self.flags!r}")
            parts.append(f"scale={self.scale!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('warning_count', 'status_flags')), EqPlan(fields=('warning_count', 'status_flags')"
        "), FrozenPlan(fields=('warning_count', 'status_flags'), allow_dynamic_dunder_attrs=False), HashPlan(action='ad"
        "d', fields=('warning_count', 'status_flags'), cache=False), InitPlan(fields=(InitPlan.Field(name='warning_coun"
        "t', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override"
        "=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='stat"
        "us_flags', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, o"
        "verride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self'"
        ", std_params=('warning_count', 'status_flags'), kw_only_params=(), frozen=True, slots=False, post_init_params="
        "None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='warning_count', kw_only=False, fn=N"
        "one), ReprPlan.Field(name='status_flags', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='aa26a203f1ac92f6a67ee2135a10aa2d77ed9b1b',
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.messages', 'EofPacket'),
    ),
)
def _process_dataclass__aa26a203f1ac92f6a67ee2135a10aa2d77ed9b1b():
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
                warning_count=self.warning_count,
                status_flags=self.status_flags,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.warning_count == other.warning_count and
                self.status_flags == other.status_flags
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'warning_count',
            'status_flags',
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
                self.warning_count,
                self.status_flags,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            warning_count: __dataclass__init__fields__0__annotation,
            status_flags: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'warning_count', warning_count)
            __dataclass__object_setattr(self, 'status_flags', status_flags)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"warning_count={self.warning_count!r}")
            parts.append(f"status_flags={self.status_flags!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('errno', 'sqlstate', 'message')), EqPlan(fields=('errno', 'sqlstate', 'message')),"
        " FrozenPlan(fields=('errno', 'sqlstate', 'message'), allow_dynamic_dunder_attrs=False), HashPlan(action='add',"
        " fields=('errno', 'sqlstate', 'message'), cache=False), InitPlan(fields=(InitPlan.Field(name='errno', annotati"
        "on=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, fiel"
        "d_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='sqlstate', annot"
        "ation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, f"
        "ield_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='message', ann"
        "otation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=False,"
        " field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=("
        "'errno', 'sqlstate', 'message'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns="
        "(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='errno', kw_only=False, fn=None), ReprPlan.Field(na"
        "me='sqlstate', kw_only=False, fn=None), ReprPlan.Field(name='message', kw_only=False, fn=None)), id=False, ter"
        "se=False, default_fn=None)))"
    ),
    plan_repr_sha1='634c3034870e64f9d0ec82984d1b73e576dde4e0',
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.messages', 'ErrPacket'),
    ),
)
def _process_dataclass__634c3034870e64f9d0ec82984d1b73e576dde4e0():
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
                errno=self.errno,
                sqlstate=self.sqlstate,
                message=self.message,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.errno == other.errno and
                self.sqlstate == other.sqlstate and
                self.message == other.message
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'errno',
            'sqlstate',
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
                self.errno,
                self.sqlstate,
                self.message,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            errno: __dataclass__init__fields__0__annotation,
            sqlstate: __dataclass__init__fields__1__annotation,
            message: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'errno', errno)
            __dataclass__object_setattr(self, 'sqlstate', sqlstate)
            __dataclass__object_setattr(self, 'message', message)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"errno={self.errno!r}")
            parts.append(f"sqlstate={self.sqlstate!r}")
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
        "Plans(tup=(CopyPlan(fields=('protocol_version', 'server_version', 'thread_id', 'auth_plugin_data', 'capabiliti"
        "es', 'charset_id', 'status_flags', 'auth_plugin_name')), EqPlan(fields=('protocol_version', 'server_version', "
        "'thread_id', 'auth_plugin_data', 'capabilities', 'charset_id', 'status_flags', 'auth_plugin_name')), FrozenPla"
        "n(fields=('protocol_version', 'server_version', 'thread_id', 'auth_plugin_data', 'capabilities', 'charset_id',"
        " 'status_flags', 'auth_plugin_name'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('proto"
        "col_version', 'server_version', 'thread_id', 'auth_plugin_data', 'capabilities', 'charset_id', 'status_flags',"
        " 'auth_plugin_name'), cache=False), InitPlan(fields=(InitPlan.Field(name='protocol_version', annotation=OpRef("
        "name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=Fi"
        "eldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='server_version', annotati"
        "on=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, fiel"
        "d_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='thread_id', anno"
        "tation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=False, "
        "field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='auth_plugin_"
        "data', annotation=OpRef(name='init.fields.3.annotation'), default=None, default_factory=None, init=True, overr"
        "ide=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='c"
        "apabilities', annotation=OpRef(name='init.fields.4.annotation'), default=None, default_factory=None, init=True"
        ", override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field("
        "name='charset_id', annotation=OpRef(name='init.fields.5.annotation'), default=None, default_factory=None, init"
        "=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.F"
        "ield(name='status_flags', annotation=OpRef(name='init.fields.6.annotation'), default=None, default_factory=Non"
        "e, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), Ini"
        "tPlan.Field(name='auth_plugin_name', annotation=OpRef(name='init.fields.7.annotation'), default=None, default_"
        "factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type"
        "=None)), self_param='self', std_params=('protocol_version', 'server_version', 'thread_id', 'auth_plugin_data',"
        " 'capabilities', 'charset_id', 'status_flags', 'auth_plugin_name'), kw_only_params=(), frozen=True, slots=Fals"
        "e, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='protocol_versio"
        "n', kw_only=False, fn=None), ReprPlan.Field(name='server_version', kw_only=False, fn=None), ReprPlan.Field(nam"
        "e='thread_id', kw_only=False, fn=None), ReprPlan.Field(name='auth_plugin_data', kw_only=False, fn=None), ReprP"
        "lan.Field(name='capabilities', kw_only=False, fn=None), ReprPlan.Field(name='charset_id', kw_only=False, fn=No"
        "ne), ReprPlan.Field(name='status_flags', kw_only=False, fn=None), ReprPlan.Field(name='auth_plugin_name', kw_o"
        "nly=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='4f4110d72a293f6e3595b704e272ec7ad7fef561',
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.messages', 'Handshake'),
    ),
)
def _process_dataclass__4f4110d72a293f6e3595b704e272ec7ad7fef561():
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
        __dataclass__init__fields__7__annotation,
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
                protocol_version=self.protocol_version,
                server_version=self.server_version,
                thread_id=self.thread_id,
                auth_plugin_data=self.auth_plugin_data,
                capabilities=self.capabilities,
                charset_id=self.charset_id,
                status_flags=self.status_flags,
                auth_plugin_name=self.auth_plugin_name,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.protocol_version == other.protocol_version and
                self.server_version == other.server_version and
                self.thread_id == other.thread_id and
                self.auth_plugin_data == other.auth_plugin_data and
                self.capabilities == other.capabilities and
                self.charset_id == other.charset_id and
                self.status_flags == other.status_flags and
                self.auth_plugin_name == other.auth_plugin_name
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'protocol_version',
            'server_version',
            'thread_id',
            'auth_plugin_data',
            'capabilities',
            'charset_id',
            'status_flags',
            'auth_plugin_name',
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
                self.protocol_version,
                self.server_version,
                self.thread_id,
                self.auth_plugin_data,
                self.capabilities,
                self.charset_id,
                self.status_flags,
                self.auth_plugin_name,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            protocol_version: __dataclass__init__fields__0__annotation,
            server_version: __dataclass__init__fields__1__annotation,
            thread_id: __dataclass__init__fields__2__annotation,
            auth_plugin_data: __dataclass__init__fields__3__annotation,
            capabilities: __dataclass__init__fields__4__annotation,
            charset_id: __dataclass__init__fields__5__annotation,
            status_flags: __dataclass__init__fields__6__annotation,
            auth_plugin_name: __dataclass__init__fields__7__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'protocol_version', protocol_version)
            __dataclass__object_setattr(self, 'server_version', server_version)
            __dataclass__object_setattr(self, 'thread_id', thread_id)
            __dataclass__object_setattr(self, 'auth_plugin_data', auth_plugin_data)
            __dataclass__object_setattr(self, 'capabilities', capabilities)
            __dataclass__object_setattr(self, 'charset_id', charset_id)
            __dataclass__object_setattr(self, 'status_flags', status_flags)
            __dataclass__object_setattr(self, 'auth_plugin_name', auth_plugin_name)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"protocol_version={self.protocol_version!r}")
            parts.append(f"server_version={self.server_version!r}")
            parts.append(f"thread_id={self.thread_id!r}")
            parts.append(f"auth_plugin_data={self.auth_plugin_data!r}")
            parts.append(f"capabilities={self.capabilities!r}")
            parts.append(f"charset_id={self.charset_id!r}")
            parts.append(f"status_flags={self.status_flags!r}")
            parts.append(f"auth_plugin_name={self.auth_plugin_name!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('filename',)), EqPlan(fields=('filename',)), FrozenPlan(fields=('filename',), allo"
        "w_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('filename',), cache=False), InitPlan(fields=(Ini"
        "tPlan.Field(name='filename', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory="
        "None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),)"
        ", self_param='self', std_params=('filename',), kw_only_params=(), frozen=True, slots=False, post_init_params=N"
        "one, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='filename', kw_only=False, fn=None),)"
        ", id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='b16fc0d5b43453ad164b8d2c892b6255cc8f2ac9',
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.messages', 'LocalInfileRequest'),
    ),
)
def _process_dataclass__b16fc0d5b43453ad164b8d2c892b6255cc8f2ac9():
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
                filename=self.filename,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.filename == other.filename
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'filename',
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
                self.filename,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            filename: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'filename', filename)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"filename={self.filename!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('affected_rows', 'insert_id', 'status_flags', 'warning_count', 'message')), EqPlan"
        "(fields=('affected_rows', 'insert_id', 'status_flags', 'warning_count', 'message')), FrozenPlan(fields=('affec"
        "ted_rows', 'insert_id', 'status_flags', 'warning_count', 'message'), allow_dynamic_dunder_attrs=False), HashPl"
        "an(action='add', fields=('affected_rows', 'insert_id', 'status_flags', 'warning_count', 'message'), cache=Fals"
        "e), InitPlan(fields=(InitPlan.Field(name='affected_rows', annotation=OpRef(name='init.fields.0.annotation'), d"
        "efault=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, vali"
        "date=None, check_type=None), InitPlan.Field(name='insert_id', annotation=OpRef(name='init.fields.1.annotation'"
        "), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, "
        "validate=None, check_type=None), InitPlan.Field(name='status_flags', annotation=OpRef(name='init.fields.2.anno"
        "tation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce"
        "=None, validate=None, check_type=None), InitPlan.Field(name='warning_count', annotation=OpRef(name='init.field"
        "s.3.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE"
        ", coerce=None, validate=None, check_type=None), InitPlan.Field(name='message', annotation=OpRef(name='init.fie"
        "lds.4.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTAN"
        "CE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('affected_rows', 'insert_id'"
        ", 'status_flags', 'warning_count', 'message'), kw_only_params=(), frozen=True, slots=False, post_init_params=N"
        "one, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='affected_rows', kw_only=False, fn=No"
        "ne), ReprPlan.Field(name='insert_id', kw_only=False, fn=None), ReprPlan.Field(name='status_flags', kw_only=Fal"
        "se, fn=None), ReprPlan.Field(name='warning_count', kw_only=False, fn=None), ReprPlan.Field(name='message', kw_"
        "only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='9b1ca1a85cebef0d7799a8478acbce4c63bf3049',
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.messages', 'OkPacket'),
    ),
)
def _process_dataclass__9b1ca1a85cebef0d7799a8478acbce4c63bf3049():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__4__annotation,
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
                affected_rows=self.affected_rows,
                insert_id=self.insert_id,
                status_flags=self.status_flags,
                warning_count=self.warning_count,
                message=self.message,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.affected_rows == other.affected_rows and
                self.insert_id == other.insert_id and
                self.status_flags == other.status_flags and
                self.warning_count == other.warning_count and
                self.message == other.message
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'affected_rows',
            'insert_id',
            'status_flags',
            'warning_count',
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
                self.affected_rows,
                self.insert_id,
                self.status_flags,
                self.warning_count,
                self.message,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            affected_rows: __dataclass__init__fields__0__annotation,
            insert_id: __dataclass__init__fields__1__annotation,
            status_flags: __dataclass__init__fields__2__annotation,
            warning_count: __dataclass__init__fields__3__annotation,
            message: __dataclass__init__fields__4__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'affected_rows', affected_rows)
            __dataclass__object_setattr(self, 'insert_id', insert_id)
            __dataclass__object_setattr(self, 'status_flags', status_flags)
            __dataclass__object_setattr(self, 'warning_count', warning_count)
            __dataclass__object_setattr(self, 'message', message)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"affected_rows={self.affected_rows!r}")
            parts.append(f"insert_id={self.insert_id!r}")
            parts.append(f"status_flags={self.status_flags!r}")
            parts.append(f"warning_count={self.warning_count!r}")
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
        "Plans(tup=(CopyPlan(fields=('seq', 'payload')), EqPlan(fields=('seq', 'payload')), FrozenPlan(fields=('seq', '"
        "payload'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('seq', 'payload'), cache=False), "
        "InitPlan(fields=(InitPlan.Field(name='seq', annotation=OpRef(name='init.fields.0.annotation'), default=None, d"
        "efault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, che"
        "ck_type=None), InitPlan.Field(name='payload', annotation=OpRef(name='init.fields.1.annotation'), default=None,"
        " default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, c"
        "heck_type=None)), self_param='self', std_params=('seq', 'payload'), kw_only_params=(), frozen=True, slots=Fals"
        "e, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='seq', kw_only=F"
        "alse, fn=None), ReprPlan.Field(name='payload', kw_only=False, fn=None)), id=False, terse=False, default_fn=Non"
        "e)))"
    ),
    plan_repr_sha1='ca3b6bbac9428021ad8b2dc18f53057981bd0c15',
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.packets', 'Packet'),
    ),
)
def _process_dataclass__ca3b6bbac9428021ad8b2dc18f53057981bd0c15():
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
                seq=self.seq,
                payload=self.payload,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.seq == other.seq and
                self.payload == other.payload
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'seq',
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
                self.seq,
                self.payload,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            seq: __dataclass__init__fields__0__annotation,
            payload: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'seq', seq)
            __dataclass__object_setattr(self, 'payload', payload)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"seq={self.seq!r}")
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
        "Plans(tup=(CopyPlan(fields=('fields', 'coders')), EqPlan(fields=('fields', 'coders')), FrozenPlan(fields=('fie"
        "lds', 'coders'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('fields', 'coders'), cache="
        "False), InitPlan(fields=(InitPlan.Field(name='fields', annotation=OpRef(name='init.fields.0.annotation'), defa"
        "ult=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validat"
        "e=None, check_type=None), InitPlan.Field(name='coders', annotation=OpRef(name='init.fields.1.annotation'), def"
        "ault=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, valida"
        "te=None, check_type=None)), self_param='self', std_params=('fields', 'coders'), kw_only_params=(), frozen=True"
        ", slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='fie"
        "lds', kw_only=False, fn=None), ReprPlan.Field(name='coders', kw_only=False, fn=None)), id=False, terse=False, "
        "default_fn=None)))"
    ),
    plan_repr_sha1='16a38ef783bae7a3ab00afe61c265e121a0e3076',
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.results', 'ResultSchema'),
    ),
)
def _process_dataclass__16a38ef783bae7a3ab00afe61c265e121a0e3076():
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
                fields=self.fields,
                coders=self.coders,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.fields == other.fields and
                self.coders == other.coders
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'fields',
            'coders',
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
                self.coders,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            fields: __dataclass__init__fields__0__annotation,
            coders: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'fields', fields)
            __dataclass__object_setattr(self, 'coders', coders)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"fields={self.fields!r}")
            parts.append(f"coders={self.coders!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('payload', 'starts_command')), EqPlan(fields=('payload', 'starts_command')), Froze"
        "nPlan(fields=('payload', 'starts_command'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=("
        "'payload', 'starts_command'), cache=False), InitPlan(fields=(InitPlan.Field(name='payload', annotation=OpRef(n"
        "ame='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=Fie"
        "ldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='starts_command', annotatio"
        "n=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, i"
        "nit=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_p"
        "aram='self', std_params=('payload', 'starts_command'), kw_only_params=(), frozen=True, slots=False, post_init_"
        "params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='payload', kw_only=False, fn="
        "None), ReprPlan.Field(name='starts_command', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)"
        "))"
    ),
    plan_repr_sha1='a1c6a8eab7d1cf71ee7b1aebba7dab57232d7814',
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.session', 'OutPacket'),
    ),
)
def _process_dataclass__a1c6a8eab7d1cf71ee7b1aebba7dab57232d7814():
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
                payload=self.payload,
                starts_command=self.starts_command,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.payload == other.payload and
                self.starts_command == other.starts_command
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'payload',
            'starts_command',
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
                self.payload,
                self.starts_command,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            payload: __dataclass__init__fields__0__annotation,
            starts_command: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'payload', payload)
            __dataclass__object_setattr(self, 'starts_command', starts_command)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"payload={self.payload!r}")
            parts.append(f"starts_command={self.starts_command!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('affected_rows', 'insert_id', 'server_status', 'warning_count', 'message', 'descri"
        "ption', 'fields', 'rows', 'has_next')), EqPlan(fields=('affected_rows', 'insert_id', 'server_status', 'warning"
        "_count', 'message', 'description', 'fields', 'rows', 'has_next')), FrozenPlan(fields=('affected_rows', 'insert"
        "_id', 'server_status', 'warning_count', 'message', 'description', 'fields', 'rows', 'has_next'), allow_dynamic"
        "_dunder_attrs=False), HashPlan(action='add', fields=('affected_rows', 'insert_id', 'server_status', 'warning_c"
        "ount', 'message', 'description', 'fields', 'rows', 'has_next'), cache=False), InitPlan(fields=(InitPlan.Field("
        "name='affected_rows', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, i"
        "nit=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPla"
        "n.Field(name='insert_id', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=Non"
        "e, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), Ini"
        "tPlan.Field(name='server_status', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_fac"
        "tory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=No"
        "ne), InitPlan.Field(name='warning_count', annotation=OpRef(name='init.fields.3.annotation'), default=None, def"
        "ault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check"
        "_type=None), InitPlan.Field(name='message', annotation=OpRef(name='init.fields.4.annotation'), default=None, d"
        "efault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, che"
        "ck_type=None), InitPlan.Field(name='description', annotation=OpRef(name='init.fields.5.annotation'), default=N"
        "one, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=Non"
        "e, check_type=None), InitPlan.Field(name='fields', annotation=OpRef(name='init.fields.6.annotation'), default="
        "None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=No"
        "ne, check_type=None), InitPlan.Field(name='rows', annotation=OpRef(name='init.fields.7.annotation'), default=N"
        "one, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=Non"
        "e, check_type=None), InitPlan.Field(name='has_next', annotation=OpRef(name='init.fields.8.annotation'), defaul"
        "t=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate="
        "None, check_type=None)), self_param='self', std_params=('affected_rows', 'insert_id', 'server_status', 'warnin"
        "g_count', 'message', 'description', 'fields', 'rows', 'has_next'), kw_only_params=(), frozen=True, slots=False"
        ", post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='affected_rows', "
        "kw_only=False, fn=None), ReprPlan.Field(name='insert_id', kw_only=False, fn=None), ReprPlan.Field(name='server"
        "_status', kw_only=False, fn=None), ReprPlan.Field(name='warning_count', kw_only=False, fn=None), ReprPlan.Fiel"
        "d(name='message', kw_only=False, fn=None), ReprPlan.Field(name='description', kw_only=False, fn=None), ReprPla"
        "n.Field(name='fields', kw_only=False, fn=None), ReprPlan.Field(name='rows', kw_only=False, fn=None), ReprPlan."
        "Field(name='has_next', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='19a356201416e01f911a60b66caad8662c66839b',
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.session', 'QueryResult'),
    ),
)
def _process_dataclass__19a356201416e01f911a60b66caad8662c66839b():
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
        __dataclass__init__fields__7__annotation,
        __dataclass__init__fields__8__annotation,
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
                affected_rows=self.affected_rows,
                insert_id=self.insert_id,
                server_status=self.server_status,
                warning_count=self.warning_count,
                message=self.message,
                description=self.description,
                fields=self.fields,
                rows=self.rows,
                has_next=self.has_next,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.affected_rows == other.affected_rows and
                self.insert_id == other.insert_id and
                self.server_status == other.server_status and
                self.warning_count == other.warning_count and
                self.message == other.message and
                self.description == other.description and
                self.fields == other.fields and
                self.rows == other.rows and
                self.has_next == other.has_next
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'affected_rows',
            'insert_id',
            'server_status',
            'warning_count',
            'message',
            'description',
            'fields',
            'rows',
            'has_next',
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
                self.affected_rows,
                self.insert_id,
                self.server_status,
                self.warning_count,
                self.message,
                self.description,
                self.fields,
                self.rows,
                self.has_next,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            affected_rows: __dataclass__init__fields__0__annotation,
            insert_id: __dataclass__init__fields__1__annotation,
            server_status: __dataclass__init__fields__2__annotation,
            warning_count: __dataclass__init__fields__3__annotation,
            message: __dataclass__init__fields__4__annotation,
            description: __dataclass__init__fields__5__annotation,
            fields: __dataclass__init__fields__6__annotation,
            rows: __dataclass__init__fields__7__annotation,
            has_next: __dataclass__init__fields__8__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'affected_rows', affected_rows)
            __dataclass__object_setattr(self, 'insert_id', insert_id)
            __dataclass__object_setattr(self, 'server_status', server_status)
            __dataclass__object_setattr(self, 'warning_count', warning_count)
            __dataclass__object_setattr(self, 'message', message)
            __dataclass__object_setattr(self, 'description', description)
            __dataclass__object_setattr(self, 'fields', fields)
            __dataclass__object_setattr(self, 'rows', rows)
            __dataclass__object_setattr(self, 'has_next', has_next)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"affected_rows={self.affected_rows!r}")
            parts.append(f"insert_id={self.insert_id!r}")
            parts.append(f"server_status={self.server_status!r}")
            parts.append(f"warning_count={self.warning_count!r}")
            parts.append(f"message={self.message!r}")
            parts.append(f"description={self.description!r}")
            parts.append(f"fields={self.fields!r}")
            parts.append(f"rows={self.rows!r}")
            parts.append(f"has_next={self.has_next!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('packets', 'more')), EqPlan(fields=('packets', 'more')), FrozenPlan(fields=('packe"
        "ts', 'more'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('packets', 'more'), cache=Fals"
        "e), InitPlan(fields=(InitPlan.Field(name='packets', annotation=OpRef(name='init.fields.0.annotation'), default"
        "=OpRef(name='init.fields.0.default'), default_factory=None, init=True, override=False, field_type=FieldType.IN"
        "STANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='more', annotation=OpRef(name='init."
        "fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override="
        "False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_pa"
        "rams=('packets', 'more'), kw_only_params=(), frozen=True, slots=False, post_init_params=(), init_fns=(), valid"
        "ate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='packets', kw_only=False, fn=None), ReprPlan.Field(name='mor"
        "e', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='0c7763b043d6033d10ed6f3c42c82856e45ad472',
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.session', 'Step'),
    ),
)
def _process_dataclass__0c7763b043d6033d10ed6f3c42c82856e45ad472():
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
                packets=self.packets,
                more=self.more,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.packets == other.packets and
                self.more == other.more
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'packets',
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
                self.packets,
                self.more,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            packets: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            more: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'packets', packets)
            __dataclass__object_setattr(self, 'more', more)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"packets={self.packets!r}")
            parts.append(f"more={self.more!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('schema', 'server_status', 'warning_count', 'has_next', 'active', 'affected_rows',"
        " 'insert_id', 'rows')), EqPlan(fields=('schema', 'server_status', 'warning_count', 'has_next', 'active', 'affe"
        "cted_rows', 'insert_id', 'rows')), HashPlan(action='set_none', fields=None, cache=None), InitPlan(fields=(Init"
        "Plan.Field(name='schema', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=Non"
        "e, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), Ini"
        "tPlan.Field(name='server_status', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init."
        "fields.1.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=Non"
        "e, validate=None, check_type=None), InitPlan.Field(name='warning_count', annotation=OpRef(name='init.fields.2."
        "annotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, override=False, fi"
        "eld_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='has_next', ann"
        "otation=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default'), default_factory=N"
        "one, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), I"
        "nitPlan.Field(name='active', annotation=OpRef(name='init.fields.4.annotation'), default=OpRef(name='init.field"
        "s.4.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, va"
        "lidate=None, check_type=None), InitPlan.Field(name='affected_rows', annotation=OpRef(name='init.fields.5.annot"
        "ation'), default=OpRef(name='init.fields.5.default'), default_factory=None, init=True, override=False, field_t"
        "ype=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='insert_id', annotat"
        "ion=OpRef(name='init.fields.6.annotation'), default=OpRef(name='init.fields.6.default'), default_factory=None,"
        " init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitP"
        "lan.Field(name='rows', annotation=OpRef(name='init.fields.7.annotation'), default=OpRef(name='init.fields.7.de"
        "fault'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate"
        "=None, check_type=None)), self_param='self', std_params=('schema', 'server_status', 'warning_count', 'has_next"
        "', 'active', 'affected_rows', 'insert_id', 'rows'), kw_only_params=(), frozen=False, slots=False, post_init_pa"
        "rams=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='schema', kw_only=False, fn=Non"
        "e), ReprPlan.Field(name='server_status', kw_only=False, fn=None), ReprPlan.Field(name='warning_count', kw_only"
        "=False, fn=None), ReprPlan.Field(name='has_next', kw_only=False, fn=None), ReprPlan.Field(name='active', kw_on"
        "ly=False, fn=None), ReprPlan.Field(name='affected_rows', kw_only=False, fn=None), ReprPlan.Field(name='insert_"
        "id', kw_only=False, fn=None), ReprPlan.Field(name='rows', kw_only=False, fn=None)), id=False, terse=False, def"
        "ault_fn=None)))"
    ),
    plan_repr_sha1='727fae313a49f1bd3586c417a69d51e2fefa8f3a',
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.session', 'UnbufferedResult'),
    ),
)
def _process_dataclass__727fae313a49f1bd3586c417a69d51e2fefa8f3a():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__3__default,
        __dataclass__init__fields__4__annotation,
        __dataclass__init__fields__4__default,
        __dataclass__init__fields__5__annotation,
        __dataclass__init__fields__5__default,
        __dataclass__init__fields__6__annotation,
        __dataclass__init__fields__6__default,
        __dataclass__init__fields__7__annotation,
        __dataclass__init__fields__7__default,
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                schema=self.schema,
                server_status=self.server_status,
                warning_count=self.warning_count,
                has_next=self.has_next,
                active=self.active,
                affected_rows=self.affected_rows,
                insert_id=self.insert_id,
                rows=self.rows,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.schema == other.schema and
                self.server_status == other.server_status and
                self.warning_count == other.warning_count and
                self.has_next == other.has_next and
                self.active == other.active and
                self.affected_rows == other.affected_rows and
                self.insert_id == other.insert_id and
                self.rows == other.rows
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            schema: __dataclass__init__fields__0__annotation,
            server_status: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            warning_count: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            has_next: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            active: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            affected_rows: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            insert_id: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
            rows: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
        ) -> __dataclass__None:
            self.schema = schema
            self.server_status = server_status
            self.warning_count = warning_count
            self.has_next = has_next
            self.active = active
            self.affected_rows = affected_rows
            self.insert_id = insert_id
            self.rows = rows

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"schema={self.schema!r}")
            parts.append(f"server_status={self.server_status!r}")
            parts.append(f"warning_count={self.warning_count!r}")
            parts.append(f"has_next={self.has_next!r}")
            parts.append(f"active={self.active!r}")
            parts.append(f"affected_rows={self.affected_rows!r}")
            parts.append(f"insert_id={self.insert_id!r}")
            parts.append(f"rows={self.rows!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
