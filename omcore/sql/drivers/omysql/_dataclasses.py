# @om-generated
# type: ignore
# ruff: noqa
# flake8: noqa
import dataclasses
import reprlib
import types


##


REGISTRY_BY_SPEC_KEY = {}
REGISTRY_BY_CLS_NAME = {}


def _register(**kwargs):
    def inner(fn):
        for key in kwargs['spec_keys']:
            if key in REGISTRY_BY_SPEC_KEY:
                raise RuntimeError('Conflicting dataclass cache key')
            REGISTRY_BY_SPEC_KEY[key] = (kwargs, fn)
        REGISTRY_BY_CLS_NAME.update({cn: (kwargs, fn) for cn in kwargs['cls_names']})
        return fn
    return inner


##


IMPLEMENTATION_KEY = '0b058e19e67cdb26e91b1c38203523e9cefe1242a3d73dbb76cc5c75c41df941'


@_register(
    installer_sha1='5b282c1791597dfbc4b7f532f939d3f8c7943f91',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('payload', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False),), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), False"
            "))"
        ),
    ),
    cls_names=(
        ('omcore.sql.drivers.omysql.core.handlers', 'ServerPacket'),
    ),
)
def _process_dataclass__5b282c1791597dfbc4b7f532f939d3f8c7943f91():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='df151e2262141f4f7c26168c0ada271a6cfd8b1b',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('data', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False),), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.messages', 'AuthMoreData'),
    ),
)
def _process_dataclass__df151e2262141f4f7c26168c0ada271a6cfd8b1b():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='a0ae6ea9bd42a105ad1822a9164a8fc2f7047414',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('plugin_name', True, True, None, True, False, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('data', True, True, None, True, False, False, None), 'instance', 'miss"
            "ing', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), Fa"
            "lse))"
        ),
    ),
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.messages', 'AuthSwitchRequest'),
    ),
)
def _process_dataclass__a0ae6ea9bd42a105ad1822a9164a8fc2f7047414():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='39021b27af2db0991b012117f50b27ffc02fbbb0',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('catalog', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('db', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('table_name', True, True, None, True, False, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('org_table', True, True, None, True, False, False, None), 'instance', "
            "'missing', None, False, False, False), (('name', True, True, None, True, False, False, None), 'instance', "
            "'missing', None, False, False, False), (('org_name', True, True, None, True, False, False, None), 'instanc"
            "e', 'missing', None, False, False, False), (('charsetnr', True, True, None, True, False, False, None), 'in"
            "stance', 'missing', None, False, False, False), (('length', True, True, None, True, False, False, None), '"
            "instance', 'missing', None, False, False, False), (('type_code', True, True, None, True, False, False, Non"
            "e), 'instance', 'missing', None, False, False, False), (('flags', True, True, None, True, False, False, No"
            "ne), 'instance', 'missing', None, False, False, False), (('scale', True, True, None, True, False, False, N"
            "one), 'instance', 'missing', None, False, False, False)), False, 0, ()), (False, False, (), False, (False,"
            " False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.messages', 'ColumnDefinition'),
    ),
)
def _process_dataclass__39021b27af2db0991b012117f50b27ffc02fbbb0():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__01__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__02__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__03__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__04__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__05__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__06__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__07__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__08__annotation = __dataclass__spec.fields[8].annotation
        __dataclass__init__fields__09__annotation = __dataclass__spec.fields[9].annotation
        __dataclass__init__fields__10__annotation = __dataclass__spec.fields[10].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='697f6cdb44d59c172beee390839c7902034ffae5',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('warning_count', True, True, None, True, False, False, None), 'instance', 'mi"
            "ssing', None, False, False, False), (('status_flags', True, True, None, True, False, False, None), 'instan"
            "ce', 'missing', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), "
            "(), (), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.messages', 'EofPacket'),
    ),
)
def _process_dataclass__697f6cdb44d59c172beee390839c7902034ffae5():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='539f79f02d9aa33c43d71781e641d6b9531a4748',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('errno', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('sqlstate', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('message', True, True, None, True, False, False, None), 'instance', 'mis"
            "sing', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), F"
            "alse))"
        ),
    ),
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.messages', 'ErrPacket'),
    ),
)
def _process_dataclass__539f79f02d9aa33c43d71781e641d6b9531a4748():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='2031b20663173c87ce357b42c9781a26e152514d',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('protocol_version', True, True, None, True, False, False, None), 'instance', "
            "'missing', None, False, False, False), (('server_version', True, True, None, True, False, False, None), 'i"
            "nstance', 'missing', None, False, False, False), (('thread_id', True, True, None, True, False, False, None"
            "), 'instance', 'missing', None, False, False, False), (('auth_plugin_data', True, True, None, True, False,"
            " False, None), 'instance', 'missing', None, False, False, False), (('capabilities', True, True, None, True"
            ", False, False, None), 'instance', 'missing', None, False, False, False), (('charset_id', True, True, None"
            ", True, False, False, None), 'instance', 'missing', None, False, False, False), (('status_flags', True, Tr"
            "ue, None, True, False, False, None), 'instance', 'missing', None, False, False, False), (('auth_plugin_nam"
            "e', True, True, None, True, False, False, None), 'instance', 'missing', None, False, False, False)), False"
            ", 0, ()), (False, False, (), False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.messages', 'Handshake'),
    ),
)
def _process_dataclass__2031b20663173c87ce357b42c9781a26e152514d():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__7__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='b88c39a3a9d236843d6b7bcd0aba04c7cce85193',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('filename', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False),), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), Fals"
            "e))"
        ),
    ),
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.messages', 'LocalInfileRequest'),
    ),
)
def _process_dataclass__b88c39a3a9d236843d6b7bcd0aba04c7cce85193():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='b6ee319c0b94a6138d90f9a78838b10a08af81c7',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('affected_rows', True, True, None, True, False, False, None), 'instance', 'mi"
            "ssing', None, False, False, False), (('insert_id', True, True, None, True, False, False, None), 'instance'"
            ", 'missing', None, False, False, False), (('status_flags', True, True, None, True, False, False, None), 'i"
            "nstance', 'missing', None, False, False, False), (('warning_count', True, True, None, True, False, False, "
            "None), 'instance', 'missing', None, False, False, False), (('message', True, True, None, True, False, Fals"
            "e, None), 'instance', 'missing', None, False, False, False)), False, 0, ()), (False, False, (), False, (Fa"
            "lse, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.messages', 'OkPacket'),
    ),
)
def _process_dataclass__b6ee319c0b94a6138d90f9a78838b10a08af81c7():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='555000a2d01b182387a4777e9e4fc5ab7e829822',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('seq', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('payload', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.packets', 'Packet'),
    ),
)
def _process_dataclass__555000a2d01b182387a4777e9e4fc5ab7e829822():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='2e75ca22514d790652efa03f55901529309784e6',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('fields', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('coders', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), False"
            "))"
        ),
    ),
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.results', 'ResultSchema'),
    ),
)
def _process_dataclass__2e75ca22514d790652efa03f55901529309784e6():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='570e4eec388c13115b6d1524877c819193e28e86',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('payload', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('starts_command', True, True, None, True, False, False, None), 'instance',"
            " 'value', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), ()"
            ", False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.session', 'OutPacket'),
    ),
)
def _process_dataclass__570e4eec388c13115b6d1524877c819193e28e86():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='92091271013a8ad7d6b13e79147afc2a73a32344',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('affected_rows', True, True, None, True, False, False, None), 'instance', 'mi"
            "ssing', None, False, False, False), (('insert_id', True, True, None, True, False, False, None), 'instance'"
            ", 'missing', None, False, False, False), (('server_status', True, True, None, True, False, False, None), '"
            "instance', 'missing', None, False, False, False), (('warning_count', True, True, None, True, False, False,"
            " None), 'instance', 'missing', None, False, False, False), (('message', True, True, None, True, False, Fal"
            "se, None), 'instance', 'missing', None, False, False, False), (('description', True, True, None, True, Fal"
            "se, False, None), 'instance', 'missing', None, False, False, False), (('fields', True, True, None, True, F"
            "alse, False, None), 'instance', 'missing', None, False, False, False), (('rows', True, True, None, True, F"
            "alse, False, None), 'instance', 'missing', None, False, False, False), (('has_next', True, True, None, Tru"
            "e, False, False, None), 'instance', 'missing', None, False, False, False)), False, 0, ()), (False, False, "
            "(), False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.session', 'QueryResult'),
    ),
)
def _process_dataclass__92091271013a8ad7d6b13e79147afc2a73a32344():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__7__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__8__annotation = __dataclass__spec.fields[8].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='39710759b74741f236b7349986dc22a46bac9ca5',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('packets', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('more', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False)), False, 0, ()), (False, False, (), False, (False, True, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.session', 'Step'),
    ),
)
def _process_dataclass__39710759b74741f236b7349986dc22a46bac9ca5():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default = __dataclass__spec.fields[0].default.must()
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='ae5e6ee5b7b3e0ffceceece7023ce1434a8f8ca5',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('schema', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('server_status', True, True, None, True, False, False, None), 'instance', "
            "'value', None, False, False, False), (('warning_count', True, True, None, True, False, False, None), 'inst"
            "ance', 'value', None, False, False, False), (('has_next', True, True, None, True, False, False, None), 'in"
            "stance', 'value', None, False, False, False), (('active', True, True, None, True, False, False, None), 'in"
            "stance', 'value', None, False, False, False), (('affected_rows', True, True, None, True, False, False, Non"
            "e), 'instance', 'value', None, False, False, False), (('insert_id', True, True, None, True, False, False, "
            "None), 'instance', 'value', None, False, False, False), (('rows', True, True, None, True, False, False, No"
            "ne), 'instance', 'value', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, Fa"
            "lse, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.drivers.omysql.protocol.session', 'UnbufferedResult'),
    ),
)
def _process_dataclass__ae5e6ee5b7b3e0ffceceece7023ce1434a8f8ca5():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__default = __dataclass__spec.fields[5].default.must()
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__6__default = __dataclass__spec.fields[6].default.must()
        __dataclass__init__fields__7__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__7__default = __dataclass__spec.fields[7].default.must()
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
