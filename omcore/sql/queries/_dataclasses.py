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
    installer_sha1='530fb51e28f71c6bd0f28c436e453627a540780f',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('ty', True, True, None, True, False, False, None), 'instance', 'missing', Non"
            "e, False, False, False),), False, 1, ()), (False, False, (), False, (False, False, ('getter',)), (), (), F"
            "alse))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries._marshal', 'LowerEnumMarshaler'),
    ),
)
def _process_dataclass__530fb51e28f71c6bd0f28c436e453627a540780f():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__init_fns__0 = __dataclass__ctx['omcore.dataclasses.impl.concerns.init.InitFunctions'].values[0]
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                ty=self.ty,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.ty == other.ty
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'ty',
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
                self.ty,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            ty: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'ty', ty)
            __dataclass__init__init_fns__0(self)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"ty={self.ty!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='cd712472773ca4eba8b80083f8630c78bf828f5c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('ty', True, True, None, True, False, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('ns', True, True, None, True, False, False, None), 'instance', 'missing', None,"
            " False, False, False)), False, 1, ()), (False, False, (), False, (False, False, ('getter',)), (), (), Fals"
            "e))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries._marshal', 'OpMarshalerUnmarshaler'),
    ),
)
def _process_dataclass__cd712472773ca4eba8b80083f8630c78bf828f5c():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__init_fns__0 = __dataclass__ctx['omcore.dataclasses.impl.concerns.init.InitFunctions'].values[0]
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                ty=self.ty,
                ns=self.ns,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.ty == other.ty and
                self.ns == other.ns
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'ty',
            'ns',
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
                self.ty,
                self.ns,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            ty: __dataclass__init__fields__0__annotation,
            ns: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'ty', ty)
            __dataclass__object_setattr(self, 'ns', ns)
            __dataclass__init__init_fns__0(self)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"ty={self.ty!r}")
            parts.append(f"ns={self.ns!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d7e6b591db6f7823c8b898b24559750f88bc966e',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('param_style', True, True, None, True, False, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('quote_style', True, True, None, True, False, False, None), 'instance', "
            "'value', None, False, False, False), (('literal_style', True, True, None, True, False, False, None), 'inst"
            "ance', 'value', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), "
            "(), (), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.adapters', 'Adapter'),
    ),
)
def _process_dataclass__d7e6b591db6f7823c8b898b24559750f88bc966e():
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
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                param_style=self.param_style,
                quote_style=self.quote_style,
                literal_style=self.literal_style,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.param_style == other.param_style and
                self.quote_style == other.quote_style and
                self.literal_style == other.literal_style
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'param_style',
            'quote_style',
            'literal_style',
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
                self.param_style,
                self.quote_style,
                self.literal_style,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            param_style: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            quote_style: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            literal_style: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'param_style', param_style)
            __dataclass__object_setattr(self, 'quote_style', quote_style)
            __dataclass__object_setattr(self, 'literal_style', literal_style)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"param_style={self.param_style!r}")
            parts.append(f"quote_style={self.quote_style!r}")
            parts.append(f"literal_style={self.literal_style!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c7e7ad4391709d3fedb9acc0695129737240ebf3',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), ("
            "), False))"
        ),
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False)), False, 0, ()), (False, True, (), True, (False, False, ()), (), (),"
            " False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.base', 'Node'),
        ('omcore.sql.queries.exprs', 'Expr'),
        ('omcore.sql.queries.keywords', 'Keyword'),
        ('omcore.sql.queries.keywords', 'Star'),
        ('omcore.sql.queries.relations', 'Relation'),
        ('omcore.sql.queries.selects', 'AllSelectItem'),
        ('omcore.sql.queries.selects', 'SelectItem'),
        ('omcore.sql.queries.stmts', 'ExprStmt'),
        ('omcore.sql.queries.stmts', 'Stmt'),
    ),
)
def _process_dataclass__c7e7ad4391709d3fedb9acc0695129737240ebf3():
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
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__()  # noqa

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
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
    installer_sha1='c820707994443eb3ebd4fb2e288496fcc47e85b8',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('cmp_fields', True, True, None, True, False, False, None), 'instance', 'missi"
            "ng', None, False, False, False), (('hash_fields', True, True, None, True, False, False, None), 'instance',"
            " 'missing', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), "
            "(), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.base', 'Node._Fields'),
    ),
)
def _process_dataclass__c820707994443eb3ebd4fb2e288496fcc47e85b8():
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
                cmp_fields=self.cmp_fields,
                hash_fields=self.hash_fields,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.cmp_fields == other.cmp_fields and
                self.hash_fields == other.hash_fields
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'cmp_fields',
            'hash_fields',
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
                self.cmp_fields,
                self.hash_fields,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            cmp_fields: __dataclass__init__fields__0__annotation,
            hash_fields: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'cmp_fields', cmp_fields)
            __dataclass__object_setattr(self, 'hash_fields', hash_fields)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"cmp_fields={self.cmp_fields!r}")
            parts.append(f"hash_fields={self.hash_fields!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='300bbdf5cf71ccbe518718ce04ca7023d2d00bbd',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('op', True, True, None, True, False, False, None), 'instance', 'm"
            "issing', None, False, False, False), (('l', True, True, None, True, False, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('r', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), False"
            "))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.binary', 'Binary'),
    ),
)
def _process_dataclass__300bbdf5cf71ccbe518718ce04ca7023d2d00bbd():
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
                op=self.op,
                l=self.l,
                r=self.r,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
            'op',
            'l',
            'r',
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

        def __init__(
            self,
            op: __dataclass__init__fields__2__annotation,
            l: __dataclass__init__fields__3__annotation,
            r: __dataclass__init__fields__4__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'op', op)
            __dataclass__object_setattr(self, 'l', l)
            __dataclass__object_setattr(self, 'r', r)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"op={self.op!r}")
            parts.append(f"l={self.l!r}")
            parts.append(f"r={self.r!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='ea6586803cf7343e82b7cfb9cc15d0dc77cf3c8e',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('name', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('kind', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.binary', 'BinaryOp'),
        ('omcore.sql.queries.unary', 'UnaryOp'),
    ),
)
def _process_dataclass__ea6586803cf7343e82b7cfb9cc15d0dc77cf3c8e():
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
                name=self.name,
                kind=self.kind,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'kind',
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

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
            kind: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'kind', kind)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"kind={self.kind!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='9e823e808b3009586a7def922b698b7dcd6ddd58',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('from_', True, True, None, True, False, False, None), 'instance',"
            " 'missing', None, False, False, False), (('where', True, True, None, True, False, False, None), 'instance'"
            ", 'value', None, False, False, True)), False, 0, ()), (False, False, (), False, (False, False, ()), (), ()"
            ", False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.deletes', 'Delete'),
    ),
)
def _process_dataclass__9e823e808b3009586a7def922b698b7dcd6ddd58():
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
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__repr__fns__3__fn = __dataclass__spec.fields[3].repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                from_=self.from_,
                where=self.where,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
            'from_',
            'where',
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

        def __init__(
            self,
            from_: __dataclass__init__fields__2__annotation,
            where: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'from_', from_)
            __dataclass__object_setattr(self, 'where', where)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"from_={self.from_!r}")
            if (s := __dataclass__repr__fns__3__fn(self.where)) is not None:
                parts.append(f"where={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='6ed390bde8a29f37d6d53dea3ceb84c6a8918e51',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('v', True, True, None, True, False, False, None), 'instance', 'mi"
            "ssing', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), "
            "False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.exprs', 'Literal'),
    ),
)
def _process_dataclass__6ed390bde8a29f37d6d53dea3ceb84c6a8918e51():
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
                v=self.v,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
            'v',
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

        def __init__(
            self,
            v: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'v', v)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"v={self.v!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='140c01688f8a8560a33e12f4c3c160cb3f0bfc2d',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('n', True, True, None, True, False, False, None), 'instance', 'mi"
            "ssing', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), "
            "False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.exprs', 'NameExpr'),
    ),
)
def _process_dataclass__140c01688f8a8560a33e12f4c3c160cb3f0bfc2d():
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
                n=self.n,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
            'n',
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

        def __init__(
            self,
            n: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'n', n)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"n={self.n!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='32bd9532fec1f5b63f0c547879a6df818534917c',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('p', True, True, None, True, False, False, None), 'instance', 'mi"
            "ssing', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), "
            "False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.exprs', 'ParamExpr'),
    ),
)
def _process_dataclass__32bd9532fec1f5b63f0c547879a6df818534917c():
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
                p=self.p,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
            'p',
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

        def __init__(
            self,
            p: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'p', p)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"p={self.p!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='f0be7972883b0a773095bc8af9a3493a862de384',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('name', True, True, None, True, False, False, None), 'instance', "
            "'missing', None, False, False, False), (('args', True, True, None, True, False, False, None), 'instance', "
            "'value', 'callable', False, False, True)), False, 0, ()), (False, False, (), False, (False, False, ()), ()"
            ", (), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.funcs', 'Func'),
    ),
)
def _process_dataclass__f0be7972883b0a773095bc8af9a3493a862de384():
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
        __dataclass__init__fields__3__coerce = __dataclass__spec.fields[3].coerce
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__repr__fns__3__fn = __dataclass__spec.fields[3].repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                name=self.name,
                args=self.args,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
            'name',
            'args',
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

        def __init__(
            self,
            name: __dataclass__init__fields__2__annotation,
            args: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            args = __dataclass__init__fields__3__coerce(args)
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'args', args)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            if (s := __dataclass__repr__fns__3__fn(self.args)) is not None:
                parts.append(f"args={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='6d3ffb9c08414773b94d4dffb8f0174eec250e5e',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('s', True, True, None, True, False, False, None), 'instance', 'mi"
            "ssing', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), "
            "False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.idents', 'Ident'),
        ('omcore.sql.queries.selects', 'SelectExpr'),
        ('omcore.sql.queries.selects', 'SelectRelation'),
    ),
)
def _process_dataclass__6d3ffb9c08414773b94d4dffb8f0174eec250e5e():
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
                s=self.s,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
            's',
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

        def __init__(
            self,
            s: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 's', s)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"s={self.s!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='45225e34ab176cee05c1520e2957c559e22cf19b',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('v', True, True, None, True, False, False, None), 'instance', 'mi"
            "ssing', None, False, False, False), (('vs', True, True, None, True, False, False, None), 'instance', 'miss"
            "ing', 'callable', False, False, False), (('not_', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, True)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), "
            "False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.in_', 'In'),
    ),
)
def _process_dataclass__45225e34ab176cee05c1520e2957c559e22cf19b():
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
        __dataclass__init__fields__3__coerce = __dataclass__spec.fields[3].coerce
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__repr__fns__4__fn = __dataclass__spec.fields[4].repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                v=self.v,
                vs=self.vs,
                not_=self.not_,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
            'v',
            'vs',
            'not_',
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

        def __init__(
            self,
            v: __dataclass__init__fields__2__annotation,
            vs: __dataclass__init__fields__3__annotation,
            *,
            not_: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            vs = __dataclass__init__fields__3__coerce(vs)
            __dataclass__object_setattr(self, 'v', v)
            __dataclass__object_setattr(self, 'vs', vs)
            __dataclass__object_setattr(self, 'not_', not_)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"v={self.v!r}")
            parts.append(f"vs={self.vs!r}")
            if (s := __dataclass__repr__fns__4__fn(self.not_)) is not None:
                parts.append(f"not_={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='8ea9ca8836a28c427038e697af6e58a5e6767b8d',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('columns', True, True, None, True, False, False, None), 'instance"
            "', 'missing', 'callable', False, False, False), (('into', True, True, None, True, False, False, None), 'in"
            "stance', 'missing', None, False, False, False), (('data', True, True, None, True, False, False, None), 'in"
            "stance', 'missing', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ("
            ")), (), (), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.inserts', 'Insert'),
    ),
)
def _process_dataclass__8ea9ca8836a28c427038e697af6e58a5e6767b8d():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__coerce = __dataclass__spec.fields[2].coerce
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
                columns=self.columns,
                into=self.into,
                data=self.data,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
            'columns',
            'into',
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

        def __init__(
            self,
            columns: __dataclass__init__fields__2__annotation,
            into: __dataclass__init__fields__3__annotation,
            data: __dataclass__init__fields__4__annotation,
        ) -> __dataclass__None:
            columns = __dataclass__init__fields__2__coerce(columns)
            __dataclass__object_setattr(self, 'columns', columns)
            __dataclass__object_setattr(self, 'into', into)
            __dataclass__object_setattr(self, 'data', data)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"columns={self.columns!r}")
            parts.append(f"into={self.into!r}")
            parts.append(f"data={self.data!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='fc694312fccdd56ce9a6f264d28df0f1235af983',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('vs', True, True, None, True, False, False, None), 'instance', 'm"
            "issing', 'callable', False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), ("
            "), (), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.inserts', 'Values'),
    ),
)
def _process_dataclass__fc694312fccdd56ce9a6f264d28df0f1235af983():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__coerce = __dataclass__spec.fields[2].coerce
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                vs=self.vs,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
            'vs',
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

        def __init__(
            self,
            vs: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            vs = __dataclass__init__fields__2__coerce(vs)
            __dataclass__object_setattr(self, 'vs', vs)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"vs={self.vs!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='cf2ad194aae880c5fe4b864dadc5d62654b9e1f6',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('s', True, True, None, True, False, False, None), 'instance', 'mi"
            "ssing', 'callable', False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), ()"
            ", (), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.keywords', 'LiteralKeyword'),
    ),
)
def _process_dataclass__cf2ad194aae880c5fe4b864dadc5d62654b9e1f6():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__coerce = __dataclass__spec.fields[2].coerce
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                s=self.s,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
            's',
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

        def __init__(
            self,
            s: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            s = __dataclass__init__fields__2__coerce(s)
            __dataclass__object_setattr(self, 's', s)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"s={self.s!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='14a487f8518002ed8004bf3b8ce2c49ec58df500',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('k', True, True, None, True, False, False, None), 'instance', 'mi"
            "ssing', None, False, False, False), (('es', True, True, None, True, False, False, None), 'instance', 'miss"
            "ing', 'callable', True, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), ("
            "), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.multi', 'Multi'),
    ),
)
def _process_dataclass__14a487f8518002ed8004bf3b8ce2c49ec58df500():
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
        __dataclass__init__fields__3__coerce = __dataclass__spec.fields[3].coerce
        __dataclass__init__fields__3__validate = __dataclass__spec.fields[3].validate
        __dataclass__FieldFnValidationError = __dataclass__globals['__dataclass__FieldFnValidationError']
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                k=self.k,
                es=self.es,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
            'k',
            'es',
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

        def __init__(
            self,
            k: __dataclass__init__fields__2__annotation,
            es: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            es = __dataclass__init__fields__3__coerce(es)
            if not __dataclass__init__fields__3__validate(es): 
                raise __dataclass__FieldFnValidationError(
                    obj=self,
                    fn=__dataclass__init__fields__3__validate,
                    field='es',
                    value=es,
                )
            __dataclass__object_setattr(self, 'k', k)
            __dataclass__object_setattr(self, 'es', es)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"k={self.k!r}")
            parts.append(f"es={self.es!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c3d52d68b056caf8b1a0248598a907fe06a93e39',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('ps', True, True, None, True, False, False, None), 'instance', 'm"
            "issing', 'callable', False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), ("
            "), (), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.names', 'Name'),
    ),
)
def _process_dataclass__c3d52d68b056caf8b1a0248598a907fe06a93e39():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__coerce = __dataclass__spec.fields[2].coerce
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                ps=self.ps,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
            'ps',
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

        def __init__(
            self,
            ps: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            ps = __dataclass__init__fields__2__coerce(ps)
            __dataclass__object_setattr(self, 'ps', ps)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"ps={self.ps!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='038a8d9b3b78ed580aecb93613c4d27a1b19bbad',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('v', True, True, None, True, False, False, None), 'instance', 'mi"
            "ssing', None, False, False, False), (('direction', True, True, None, True, True, False, None), 'instance',"
            " 'value', None, False, False, True), (('nulls', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, True)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), Fa"
            "lse))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.ordering', 'OrderByItem'),
    ),
)
def _process_dataclass__038a8d9b3b78ed580aecb93613c4d27a1b19bbad():
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
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__repr__fns__3__fn = __dataclass__spec.fields[3].repr_fn
        __dataclass__repr__fns__4__fn = __dataclass__spec.fields[4].repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                v=self.v,
                direction=self.direction,
                nulls=self.nulls,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
            'v',
            'direction',
            'nulls',
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

        def __init__(
            self,
            v: __dataclass__init__fields__2__annotation,
            *,
            direction: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            nulls: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'v', v)
            __dataclass__object_setattr(self, 'direction', direction)
            __dataclass__object_setattr(self, 'nulls', nulls)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"v={self.v!r}")
            if (s := __dataclass__repr__fns__3__fn(self.direction)) is not None:
                parts.append(f"direction={s}")
            if (s := __dataclass__repr__fns__4__fn(self.nulls)) is not None:
                parts.append(f"nulls={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='ffa12e85eba40cc8d287aba80f242e997cdea667',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('n', True, True, None, True, False, False, None), 'instance', 'value', None, "
            "True, False, False),), False, 0, ()), (False, True, (), True, (False, False, ()), (), (), True))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.params', 'Param'),
    ),
)
def _process_dataclass__ffa12e85eba40cc8d287aba80f242e997cdea667():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default = __dataclass__spec.fields[0].default.must()
        __dataclass__init__fields__0__validate = __dataclass__spec.fields[0].validate
        __dataclass__FieldFnValidationError = __dataclass__globals['__dataclass__FieldFnValidationError']
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                n=self.n,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'n',
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

        def __init__(
            self,
            n: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
        ) -> __dataclass__None:
            if not __dataclass__init__fields__0__validate(n): 
                raise __dataclass__FieldFnValidationError(
                    obj=self,
                    fn=__dataclass__init__fields__0__validate,
                    field='n',
                    value=n,
                )
            __dataclass__object_setattr(self, 'n', n)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='580f1be47ac1c16acd252778aaacf3be1ec96d45',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('k', True, True, None, True, False, False, None), 'instance', 'mi"
            "ssing', None, False, False, False), (('l', True, True, None, True, False, False, None), 'instance', 'missi"
            "ng', None, False, False, False), (('r', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('c', True, True, None, True, False, False, None), 'instance', 'value', Non"
            "e, False, False, True)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.relations', 'Join'),
    ),
)
def _process_dataclass__580f1be47ac1c16acd252778aaacf3be1ec96d45():
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
        __dataclass__init__fields__5__default = __dataclass__spec.fields[5].default.must()
        __dataclass__repr__fns__5__fn = __dataclass__spec.fields[5].repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                k=self.k,
                l=self.l,
                r=self.r,
                c=self.c,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
            'k',
            'l',
            'r',
            'c',
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

        def __init__(
            self,
            k: __dataclass__init__fields__2__annotation,
            l: __dataclass__init__fields__3__annotation,
            r: __dataclass__init__fields__4__annotation,
            c: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'k', k)
            __dataclass__object_setattr(self, 'l', l)
            __dataclass__object_setattr(self, 'r', r)
            __dataclass__object_setattr(self, 'c', c)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"k={self.k!r}")
            parts.append(f"l={self.l!r}")
            parts.append(f"r={self.r!r}")
            if (s := __dataclass__repr__fns__5__fn(self.c)) is not None:
                parts.append(f"c={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c953fb2914f1bd3d55100c2affec2a39881f45d7',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('n', True, True, None, True, False, False, None), 'instance', 'mi"
            "ssing', None, False, False, False), (('a', True, True, None, True, False, False, None), 'instance', 'value"
            "', None, False, False, True)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), False)"
            ")"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.relations', 'Table'),
    ),
)
def _process_dataclass__c953fb2914f1bd3d55100c2affec2a39881f45d7():
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
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__repr__fns__3__fn = __dataclass__spec.fields[3].repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                n=self.n,
                a=self.a,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
            'n',
            'a',
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

        def __init__(
            self,
            n: __dataclass__init__fields__2__annotation,
            a: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'n', n)
            __dataclass__object_setattr(self, 'a', a)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"n={self.n!r}")
            if (s := __dataclass__repr__fns__3__fn(self.a)) is not None:
                parts.append(f"a={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='96fa4fdb56e4885db6b27e8d081ac97aa563ac70',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('s', True, True, None, True, False, False, None), 'instance', 'missing', None"
            ", False, False, False), (('params', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('literals', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.rendering', 'RenderedQuery'),
    ),
)
def _process_dataclass__96fa4fdb56e4885db6b27e8d081ac97aa563ac70():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                s=self.s,
                params=self.params,
                literals=self.literals,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.s == other.s and
                self.params == other.params and
                self.literals == other.literals
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            's',
            'params',
            'literals',
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
                self.s,
                self.params,
                self.literals,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            s: __dataclass__init__fields__0__annotation,
            params: __dataclass__init__fields__1__annotation,
            literals: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 's', s)
            __dataclass__object_setattr(self, 'params', params)
            __dataclass__object_setattr(self, 'literals', literals)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"s={self.s!r}")
            parts.append(f"params={self.params!r}")
            parts.append(f"literals={self.literals!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='8d34696e040cadd67efd9c78b89535e76adc0aad',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('p', True, True, None, True, False, False, None), 'instance', 'missing', None"
            ", False, False, False), (('params', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('literals', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.rendering', 'RenderedQueryParts'),
    ),
)
def _process_dataclass__8d34696e040cadd67efd9c78b89535e76adc0aad():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                p=self.p,
                params=self.params,
                literals=self.literals,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.p == other.p and
                self.params == other.params and
                self.literals == other.literals
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'p',
            'params',
            'literals',
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
                self.p,
                self.params,
                self.literals,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            p: __dataclass__init__fields__0__annotation,
            params: __dataclass__init__fields__1__annotation,
            literals: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'p', p)
            __dataclass__object_setattr(self, 'params', params)
            __dataclass__object_setattr(self, 'literals', literals)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"p={self.p!r}")
            parts.append(f"params={self.params!r}")
            parts.append(f"literals={self.literals!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='a067f497b44273781e23bf17858045e12b47b602',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('v', True, True, None, True, False, False, None), 'instance', 'mi"
            "ssing', None, False, False, False), (('a', True, True, None, True, False, False, None), 'instance', 'value"
            "', None, False, False, True)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), False)"
            ")"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.selects', 'ExprSelectItem'),
    ),
)
def _process_dataclass__a067f497b44273781e23bf17858045e12b47b602():
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
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__repr__fns__3__fn = __dataclass__spec.fields[3].repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                v=self.v,
                a=self.a,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
            'v',
            'a',
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

        def __init__(
            self,
            v: __dataclass__init__fields__2__annotation,
            a: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'v', v)
            __dataclass__object_setattr(self, 'a', a)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"v={self.v!r}")
            if (s := __dataclass__repr__fns__3__fn(self.a)) is not None:
                parts.append(f"a={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c55b83e53653d0725fb4636e8607fc0764c18842',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('items', True, True, None, True, False, False, None), 'instance',"
            " 'missing', 'callable', False, False, False), (('from_', True, True, None, True, False, False, None), 'ins"
            "tance', 'value', None, False, False, True), (('where', True, True, None, True, False, False, None), 'insta"
            "nce', 'value', None, False, False, True), (('order_by', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', 'callable', False, False, False), (('limit', True, True, None, True, True, False, None), 'i"
            "nstance', 'value', None, False, False, True), (('offset', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, True)), False, 0, ()), (False, False, (), False, (False, False, ()), "
            "(), (), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.selects', 'Select'),
    ),
)
def _process_dataclass__c55b83e53653d0725fb4636e8607fc0764c18842():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__coerce = __dataclass__spec.fields[2].coerce
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__coerce = __dataclass__spec.fields[5].coerce
        __dataclass__init__fields__5__default = __dataclass__spec.fields[5].default.must()
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__6__default = __dataclass__spec.fields[6].default.must()
        __dataclass__init__fields__7__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__7__default = __dataclass__spec.fields[7].default.must()
        __dataclass__repr__fns__3__fn = __dataclass__spec.fields[3].repr_fn
        __dataclass__repr__fns__4__fn = __dataclass__spec.fields[4].repr_fn
        __dataclass__repr__fns__6__fn = __dataclass__spec.fields[6].repr_fn
        __dataclass__repr__fns__7__fn = __dataclass__spec.fields[7].repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                items=self.items,
                from_=self.from_,
                where=self.where,
                order_by=self.order_by,
                limit=self.limit,
                offset=self.offset,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
            'items',
            'from_',
            'where',
            'order_by',
            'limit',
            'offset',
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

        def __init__(
            self,
            items: __dataclass__init__fields__2__annotation,
            from_: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            where: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            *,
            order_by: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            limit: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
            offset: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
        ) -> __dataclass__None:
            items = __dataclass__init__fields__2__coerce(items)
            order_by = __dataclass__init__fields__5__coerce(order_by)
            __dataclass__object_setattr(self, 'items', items)
            __dataclass__object_setattr(self, 'from_', from_)
            __dataclass__object_setattr(self, 'where', where)
            __dataclass__object_setattr(self, 'order_by', order_by)
            __dataclass__object_setattr(self, 'limit', limit)
            __dataclass__object_setattr(self, 'offset', offset)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"items={self.items!r}")
            if (s := __dataclass__repr__fns__3__fn(self.from_)) is not None:
                parts.append(f"from_={s}")
            if (s := __dataclass__repr__fns__4__fn(self.where)) is not None:
                parts.append(f"where={s}")
            parts.append(f"order_by={self.order_by!r}")
            if (s := __dataclass__repr__fns__6__fn(self.limit)) is not None:
                parts.append(f"limit={s}")
            if (s := __dataclass__repr__fns__7__fn(self.offset)) is not None:
                parts.append(f"offset={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='fae5bf722f324cfe0f32dd455ca3f55397ca783e',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('op', True, True, None, True, False, False, None), 'instance', 'm"
            "issing', None, False, False, False), (('v', True, True, None, True, False, False, None), 'instance', 'miss"
            "ing', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), Fa"
            "lse))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.unary', 'Unary'),
    ),
)
def _process_dataclass__fae5bf722f324cfe0f32dd455ca3f55397ca783e():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                op=self.op,
                v=self.v,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
            'op',
            'v',
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

        def __init__(
            self,
            op: __dataclass__init__fields__2__annotation,
            v: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'op', op)
            __dataclass__object_setattr(self, 'v', v)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"op={self.op!r}")
            parts.append(f"v={self.v!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e1ef64011fb90579f5d0a38833303a664abb440c',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('selects', True, True, None, True, False, False, None), 'instance"
            "', 'missing', 'callable', False, False, False), (('all', True, True, None, True, True, False, None), 'inst"
            "ance', 'value', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), "
            "(), (), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.unions', 'Union'),
    ),
)
def _process_dataclass__e1ef64011fb90579f5d0a38833303a664abb440c():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__coerce = __dataclass__spec.fields[2].coerce
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                selects=self.selects,
                all=self.all,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
            'selects',
            'all',
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

        def __init__(
            self,
            selects: __dataclass__init__fields__2__annotation,
            *,
            all: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            selects = __dataclass__init__fields__2__coerce(selects)
            __dataclass__object_setattr(self, 'selects', selects)
            __dataclass__object_setattr(self, 'all', all)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"selects={self.selects!r}")
            parts.append(f"all={self.all!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='ac55343b5d12a348a6e6bead12d4504885f47e3e',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('c', True, True, None, True, False, False, None), 'instance', 'mi"
            "ssing', None, False, False, False), (('v', True, True, None, True, False, False, None), 'instance', 'missi"
            "ng', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), Fal"
            "se))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.updates', 'Field'),
    ),
)
def _process_dataclass__ac55343b5d12a348a6e6bead12d4504885f47e3e():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                c=self.c,
                v=self.v,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
            'c',
            'v',
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

        def __init__(
            self,
            c: __dataclass__init__fields__2__annotation,
            v: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'c', c)
            __dataclass__object_setattr(self, 'v', v)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"c={self.c!r}")
            parts.append(f"v={self.v!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c8fcef17b4e8296bcb715565bba9d892fed1f601',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('fields', True, True, None, True, False, False, None), 'instance'"
            ", 'missing', 'callable', False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()"
            "), (), (), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.updates', 'Fields'),
    ),
)
def _process_dataclass__c8fcef17b4e8296bcb715565bba9d892fed1f601():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__coerce = __dataclass__spec.fields[2].coerce
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
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
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

        def __init__(
            self,
            fields: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            fields = __dataclass__init__fields__2__coerce(fields)
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
    installer_sha1='a91ee8c3ecb630b70c3929706f4f77aca73505f3',
    spec_keys=(
        (
            "(((True, True, False, False, False, True, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, True), ((('__node_fields__', True, True, None, True, None, False, None), 'class_var', '"
            "missing', None, False, False, False), (('_hash', True, True, None, True, None, False, None), 'class_var', "
            "'missing', None, False, False, False), (('into', True, True, None, True, False, False, None), 'instance', "
            "'missing', None, False, False, False), (('fields', True, True, None, True, False, False, None), 'instance'"
            ", 'missing', None, False, False, False), (('where', True, True, None, True, False, False, None), 'instance"
            "', 'value', None, False, False, True)), False, 0, ()), (False, False, (), False, (False, False, ()), (), ("
            "), False))"
        ),
    ),
    cls_names=(
        ('omcore.sql.queries.updates', 'Update'),
    ),
)
def _process_dataclass__a91ee8c3ecb630b70c3929706f4f77aca73505f3():
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
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__repr__fns__4__fn = __dataclass__spec.fields[4].repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                into=self.into,
                fields=self.fields,
                where=self.where,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            '__node_fields__',
            '_hash',
            'into',
            'fields',
            'where',
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

        def __init__(
            self,
            into: __dataclass__init__fields__2__annotation,
            fields: __dataclass__init__fields__3__annotation,
            where: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'into', into)
            __dataclass__object_setattr(self, 'fields', fields)
            __dataclass__object_setattr(self, 'where', where)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"into={self.into!r}")
            parts.append(f"fields={self.fields!r}")
            if (s := __dataclass__repr__fns__4__fn(self.where)) is not None:
                parts.append(f"where={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
