# @om-generated
# type: ignore
# ruff: noqa
# flake8: noqa


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


IMPLEMENTATION_KEY = 'ec0d825a77daf2010440f2135dbf8d063599428f1d09d40e22d60773f9be3250'


@_register(
    installer_sha1='5300d62a4416f5aa4af512e263d9b885d5c61d36',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('m', True, True, None, True, False, False, None), 'instance', 'missing', None"
            ", False, False, False), (('r', True, True, None, True, False, False, None), 'instance', 'missing', None, F"
            "alse, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (Fa"
            "lse,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi._marshal', '_ReferenceUnionMarshaler'),
    ),
)
def _process_dataclass__5300d62a4416f5aa4af512e263d9b885d5c61d36():
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
                m=self.m,
                r=self.r,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.m == other.m and
                self.r == other.r
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'm',
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

        def __hash__(self):
            return hash((
                self.m,
                self.r,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            m: __dataclass__init__fields__0__annotation,
            r: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'm', m)
            __dataclass__object_setattr(self, 'r', r)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"m={self.m!r}")
            parts.append(f"r={self.r!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d4faac3dca3ac9fe07002ff9810bbfeff66965a9',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('u', True, True, None, True, False, False, None), 'instance', 'missing', None"
            ", False, False, False), (('r', True, True, None, True, False, False, None), 'instance', 'missing', None, F"
            "alse, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (Fa"
            "lse,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi._marshal', '_ReferenceUnionUnmarshaler'),
    ),
)
def _process_dataclass__d4faac3dca3ac9fe07002ff9810bbfeff66965a9():
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
                u=self.u,
                r=self.r,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.u == other.u and
                self.r == other.r
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'u',
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

        def __hash__(self):
            return hash((
                self.u,
                self.r,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            u: __dataclass__init__fields__0__annotation,
            r: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'u', u)
            __dataclass__object_setattr(self, 'r', r)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"u={self.u!r}")
            parts.append(f"r={self.r!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='f508263caf1723da5ac06f79189061cb5629225c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('m_dct', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('kw_m', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi._marshal', '_SchemaMarshaler'),
    ),
)
def _process_dataclass__f508263caf1723da5ac06f79189061cb5629225c():
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
                m_dct=self.m_dct,
                kw_m=self.kw_m,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.m_dct == other.m_dct and
                self.kw_m == other.kw_m
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'm_dct',
            'kw_m',
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
                self.m_dct,
                self.kw_m,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            m_dct: __dataclass__init__fields__0__annotation,
            kw_m: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'm_dct', m_dct)
            __dataclass__object_setattr(self, 'kw_m', kw_m)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"m_dct={self.m_dct!r}")
            parts.append(f"kw_m={self.kw_m!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='8c352cabd7d3db0df76a7b662f322ee508ed3606',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('u_dct', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('kw_u', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi._marshal', '_SchemaUnmarshaler'),
    ),
)
def _process_dataclass__8c352cabd7d3db0df76a7b662f322ee508ed3606():
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
                u_dct=self.u_dct,
                kw_u=self.kw_u,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.u_dct == other.u_dct and
                self.kw_u == other.kw_u
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'u_dct',
            'kw_u',
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
                self.u_dct,
                self.kw_u,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            u_dct: __dataclass__init__fields__0__annotation,
            kw_u: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'u_dct', u_dct)
            __dataclass__object_setattr(self, 'kw_u', kw_u)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"u_dct={self.u_dct!r}")
            parts.append(f"kw_u={self.kw_u!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='f1cc91dfacb69fc3f8891a27a543b1ac65cd248c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('schemas', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('responses', True, True, None, True, False, False, None), 'instance', 'value"
            "', None, False, False, False), (('parameters', True, True, None, True, False, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('examples', True, True, None, True, False, False, None), 'instance', "
            "'value', None, False, False, False), (('request_bodies', True, True, None, True, False, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('headers', True, True, None, True, False, False, None), 'in"
            "stance', 'value', None, False, False, False), (('security_schemes', True, True, None, True, False, False, "
            "None), 'instance', 'value', None, False, False, False), (('links', True, True, None, True, False, False, N"
            "one), 'instance', 'value', None, False, False, False), (('callbacks', True, True, None, True, False, False"
            ", None), 'instance', 'value', None, False, False, False), (('path_items', True, True, None, True, False, F"
            "alse, None), 'instance', 'value', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (Fal"
            "se,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'Components'),
    ),
)
def _process_dataclass__f1cc91dfacb69fc3f8891a27a543b1ac65cd248c():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__00__default = __dataclass__spec.fields[0].default.must()
        __dataclass__init__fields__01__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__01__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__02__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__02__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__03__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__03__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__04__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__04__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__05__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__05__default = __dataclass__spec.fields[5].default.must()
        __dataclass__init__fields__06__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__06__default = __dataclass__spec.fields[6].default.must()
        __dataclass__init__fields__07__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__07__default = __dataclass__spec.fields[7].default.must()
        __dataclass__init__fields__08__annotation = __dataclass__spec.fields[8].annotation
        __dataclass__init__fields__08__default = __dataclass__spec.fields[8].default.must()
        __dataclass__init__fields__09__annotation = __dataclass__spec.fields[9].annotation
        __dataclass__init__fields__09__default = __dataclass__spec.fields[9].default.must()
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                schemas=self.schemas,
                responses=self.responses,
                parameters=self.parameters,
                examples=self.examples,
                request_bodies=self.request_bodies,
                headers=self.headers,
                security_schemes=self.security_schemes,
                links=self.links,
                callbacks=self.callbacks,
                path_items=self.path_items,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.schemas == other.schemas and
                self.responses == other.responses and
                self.parameters == other.parameters and
                self.examples == other.examples and
                self.request_bodies == other.request_bodies and
                self.headers == other.headers and
                self.security_schemes == other.security_schemes and
                self.links == other.links and
                self.callbacks == other.callbacks and
                self.path_items == other.path_items
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'schemas',
            'responses',
            'parameters',
            'examples',
            'request_bodies',
            'headers',
            'security_schemes',
            'links',
            'callbacks',
            'path_items',
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
                self.schemas,
                self.responses,
                self.parameters,
                self.examples,
                self.request_bodies,
                self.headers,
                self.security_schemes,
                self.links,
                self.callbacks,
                self.path_items,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            schemas: __dataclass__init__fields__00__annotation = __dataclass__init__fields__00__default,
            responses: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            parameters: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            examples: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            request_bodies: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            headers: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            security_schemes: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            links: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            callbacks: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            path_items: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'schemas', schemas)
            __dataclass__object_setattr(self, 'responses', responses)
            __dataclass__object_setattr(self, 'parameters', parameters)
            __dataclass__object_setattr(self, 'examples', examples)
            __dataclass__object_setattr(self, 'request_bodies', request_bodies)
            __dataclass__object_setattr(self, 'headers', headers)
            __dataclass__object_setattr(self, 'security_schemes', security_schemes)
            __dataclass__object_setattr(self, 'links', links)
            __dataclass__object_setattr(self, 'callbacks', callbacks)
            __dataclass__object_setattr(self, 'path_items', path_items)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.schemas)) is not None:
                parts.append(f"schemas={s}")
            if (s := __dataclass__repr__default_fn(self.responses)) is not None:
                parts.append(f"responses={s}")
            if (s := __dataclass__repr__default_fn(self.parameters)) is not None:
                parts.append(f"parameters={s}")
            if (s := __dataclass__repr__default_fn(self.examples)) is not None:
                parts.append(f"examples={s}")
            if (s := __dataclass__repr__default_fn(self.request_bodies)) is not None:
                parts.append(f"request_bodies={s}")
            if (s := __dataclass__repr__default_fn(self.headers)) is not None:
                parts.append(f"headers={s}")
            if (s := __dataclass__repr__default_fn(self.security_schemes)) is not None:
                parts.append(f"security_schemes={s}")
            if (s := __dataclass__repr__default_fn(self.links)) is not None:
                parts.append(f"links={s}")
            if (s := __dataclass__repr__default_fn(self.callbacks)) is not None:
                parts.append(f"callbacks={s}")
            if (s := __dataclass__repr__default_fn(self.path_items)) is not None:
                parts.append(f"path_items={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='81690b6b55bd379ebd8d49c8ed4847ee386451ba',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('name', True, True, None, True, False, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('url', True, True, None, True, False, False, None), 'instance', 'value', None, "
            "False, False, False), (('email', True, True, None, True, False, False, None), 'instance', 'value', None, F"
            "alse, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (Fal"
            "se,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'Contact'),
    ),
)
def _process_dataclass__81690b6b55bd379ebd8d49c8ed4847ee386451ba():
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
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
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
                url=self.url,
                email=self.email,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.url == other.url and
                self.email == other.email
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'url',
            'email',
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
                self.url,
                self.email,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            url: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            email: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'url', url)
            __dataclass__object_setattr(self, 'email', email)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.name)) is not None:
                parts.append(f"name={s}")
            if (s := __dataclass__repr__default_fn(self.url)) is not None:
                parts.append(f"url={s}")
            if (s := __dataclass__repr__default_fn(self.email)) is not None:
                parts.append(f"email={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='0e45bb3eb688795306c8d3cd0328c880d011f955',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('property_name', True, True, None, True, False, False, None), 'instance', 'mi"
            "ssing', None, False, False, False), (('mapping', True, True, None, True, False, False, None), 'instance', "
            "'value', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()),"
            " ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'Discriminator'),
    ),
)
def _process_dataclass__0e45bb3eb688795306c8d3cd0328c880d011f955():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                property_name=self.property_name,
                mapping=self.mapping,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.property_name == other.property_name and
                self.mapping == other.mapping
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'property_name',
            'mapping',
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
                self.property_name,
                self.mapping,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            property_name: __dataclass__init__fields__0__annotation,
            mapping: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'property_name', property_name)
            __dataclass__object_setattr(self, 'mapping', mapping)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.property_name)) is not None:
                parts.append(f"property_name={s}")
            if (s := __dataclass__repr__default_fn(self.mapping)) is not None:
                parts.append(f"mapping={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c459016646919dd38ea44c0f7acfc58c14e1ef96',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('content_type', True, True, None, True, False, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('headers', True, True, None, True, False, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('style', True, True, None, True, False, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('explode', True, True, None, True, False, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('allow_reserved', True, True, None, True, False, False, None), 'instan"
            "ce', 'value', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False,"
            " ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'Encoding'),
    ),
)
def _process_dataclass__c459016646919dd38ea44c0f7acfc58c14e1ef96():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                content_type=self.content_type,
                headers=self.headers,
                style=self.style,
                explode=self.explode,
                allow_reserved=self.allow_reserved,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.content_type == other.content_type and
                self.headers == other.headers and
                self.style == other.style and
                self.explode == other.explode and
                self.allow_reserved == other.allow_reserved
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'content_type',
            'headers',
            'style',
            'explode',
            'allow_reserved',
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
                self.content_type,
                self.headers,
                self.style,
                self.explode,
                self.allow_reserved,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            content_type: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            headers: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            style: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            explode: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            allow_reserved: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'content_type', content_type)
            __dataclass__object_setattr(self, 'headers', headers)
            __dataclass__object_setattr(self, 'style', style)
            __dataclass__object_setattr(self, 'explode', explode)
            __dataclass__object_setattr(self, 'allow_reserved', allow_reserved)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.content_type)) is not None:
                parts.append(f"content_type={s}")
            if (s := __dataclass__repr__default_fn(self.headers)) is not None:
                parts.append(f"headers={s}")
            if (s := __dataclass__repr__default_fn(self.style)) is not None:
                parts.append(f"style={s}")
            if (s := __dataclass__repr__default_fn(self.explode)) is not None:
                parts.append(f"explode={s}")
            if (s := __dataclass__repr__default_fn(self.allow_reserved)) is not None:
                parts.append(f"allow_reserved={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e1dfcd4b333a0d8757bd73a5108c4522cca48e83',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('summary', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('description', True, True, None, True, False, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('value', True, True, None, True, False, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('external_value', True, True, None, True, False, False, None), 'instance"
            "', 'value', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ("
            ")), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'Example'),
    ),
)
def _process_dataclass__e1dfcd4b333a0d8757bd73a5108c4522cca48e83():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                summary=self.summary,
                description=self.description,
                value=self.value,
                external_value=self.external_value,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.summary == other.summary and
                self.description == other.description and
                self.value == other.value and
                self.external_value == other.external_value
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'summary',
            'description',
            'value',
            'external_value',
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
                self.summary,
                self.description,
                self.value,
                self.external_value,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            summary: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            description: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            value: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            external_value: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'summary', summary)
            __dataclass__object_setattr(self, 'description', description)
            __dataclass__object_setattr(self, 'value', value)
            __dataclass__object_setattr(self, 'external_value', external_value)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.summary)) is not None:
                parts.append(f"summary={s}")
            if (s := __dataclass__repr__default_fn(self.description)) is not None:
                parts.append(f"description={s}")
            if (s := __dataclass__repr__default_fn(self.value)) is not None:
                parts.append(f"value={s}")
            if (s := __dataclass__repr__default_fn(self.external_value)) is not None:
                parts.append(f"external_value={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='19e80c02a64b17baffc8864e541893a972b6c74b',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('url', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('description', True, True, None, True, False, False, None), 'instance', 'value"
            "', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'ExternalDocumentation'),
    ),
)
def _process_dataclass__19e80c02a64b17baffc8864e541893a972b6c74b():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                url=self.url,
                description=self.description,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.url == other.url and
                self.description == other.description
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'url',
            'description',
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
                self.url,
                self.description,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            url: __dataclass__init__fields__0__annotation,
            description: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'url', url)
            __dataclass__object_setattr(self, 'description', description)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.url)) is not None:
                parts.append(f"url={s}")
            if (s := __dataclass__repr__default_fn(self.description)) is not None:
                parts.append(f"description={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='6484bba7bed29055f4f9d7c1b5c3ed0d495f5550',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('common', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False),), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'Header'),
    ),
)
def _process_dataclass__6484bba7bed29055f4f9d7c1b5c3ed0d495f5550():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                common=self.common,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.common == other.common
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'common',
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
                self.common,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            common: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'common', common)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.common)) is not None:
                parts.append(f"common={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d068e2c359d3759f7e36931230488889b39ac0b6',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('title', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('version', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('summary', True, True, None, True, False, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('description', True, True, None, True, False, False, None), 'instance', "
            "'value', None, False, False, False), (('terms_of_service', True, True, None, True, False, False, None), 'i"
            "nstance', 'value', None, False, False, False), (('contact', True, True, None, True, False, False, None), '"
            "instance', 'value', None, False, False, False), (('license', True, True, None, True, False, False, None), "
            "'instance', 'value', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False,"
            " False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'Info'),
    ),
)
def _process_dataclass__d068e2c359d3759f7e36931230488889b39ac0b6():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__default = __dataclass__spec.fields[5].default.must()
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__6__default = __dataclass__spec.fields[6].default.must()
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                title=self.title,
                version=self.version,
                summary=self.summary,
                description=self.description,
                terms_of_service=self.terms_of_service,
                contact=self.contact,
                license=self.license,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.title == other.title and
                self.version == other.version and
                self.summary == other.summary and
                self.description == other.description and
                self.terms_of_service == other.terms_of_service and
                self.contact == other.contact and
                self.license == other.license
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'title',
            'version',
            'summary',
            'description',
            'terms_of_service',
            'contact',
            'license',
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
                self.title,
                self.version,
                self.summary,
                self.description,
                self.terms_of_service,
                self.contact,
                self.license,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            title: __dataclass__init__fields__0__annotation,
            version: __dataclass__init__fields__1__annotation,
            summary: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            description: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            terms_of_service: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            contact: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            license: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'title', title)
            __dataclass__object_setattr(self, 'version', version)
            __dataclass__object_setattr(self, 'summary', summary)
            __dataclass__object_setattr(self, 'description', description)
            __dataclass__object_setattr(self, 'terms_of_service', terms_of_service)
            __dataclass__object_setattr(self, 'contact', contact)
            __dataclass__object_setattr(self, 'license', license)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.title)) is not None:
                parts.append(f"title={s}")
            if (s := __dataclass__repr__default_fn(self.version)) is not None:
                parts.append(f"version={s}")
            if (s := __dataclass__repr__default_fn(self.summary)) is not None:
                parts.append(f"summary={s}")
            if (s := __dataclass__repr__default_fn(self.description)) is not None:
                parts.append(f"description={s}")
            if (s := __dataclass__repr__default_fn(self.terms_of_service)) is not None:
                parts.append(f"terms_of_service={s}")
            if (s := __dataclass__repr__default_fn(self.contact)) is not None:
                parts.append(f"contact={s}")
            if (s := __dataclass__repr__default_fn(self.license)) is not None:
                parts.append(f"license={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='a97fd9a3f321f9616b8bcf5cb4863311689cda59',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('name', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('identifier', True, True, None, True, False, False, None), 'instance', 'value"
            "', None, False, False, False), (('url', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'License'),
    ),
)
def _process_dataclass__a97fd9a3f321f9616b8bcf5cb4863311689cda59():
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
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
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
                identifier=self.identifier,
                url=self.url,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.identifier == other.identifier and
                self.url == other.url
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'identifier',
            'url',
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
                self.identifier,
                self.url,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
            identifier: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            url: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'identifier', identifier)
            __dataclass__object_setattr(self, 'url', url)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.name)) is not None:
                parts.append(f"name={s}")
            if (s := __dataclass__repr__default_fn(self.identifier)) is not None:
                parts.append(f"identifier={s}")
            if (s := __dataclass__repr__default_fn(self.url)) is not None:
                parts.append(f"url={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='fe7aa2ee5e21b3ee3e745e679d8f9a2f43c4def7',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('operation_ref', True, True, None, True, False, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('operation_id', True, True, None, True, False, False, None), 'instance"
            "', 'value', None, False, False, False), (('parameters', True, True, None, True, False, False, None), 'inst"
            "ance', 'value', None, False, False, False), (('request_body', True, True, None, True, False, False, None),"
            " 'instance', 'value', None, False, False, False), (('description', True, True, None, True, False, False, N"
            "one), 'instance', 'value', None, False, False, False), (('server', True, True, None, True, False, False, N"
            "one), 'instance', 'value', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), ("
            "False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'Link'),
    ),
)
def _process_dataclass__fe7aa2ee5e21b3ee3e745e679d8f9a2f43c4def7():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__default = __dataclass__spec.fields[5].default.must()
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                operation_ref=self.operation_ref,
                operation_id=self.operation_id,
                parameters=self.parameters,
                request_body=self.request_body,
                description=self.description,
                server=self.server,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.operation_ref == other.operation_ref and
                self.operation_id == other.operation_id and
                self.parameters == other.parameters and
                self.request_body == other.request_body and
                self.description == other.description and
                self.server == other.server
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'operation_ref',
            'operation_id',
            'parameters',
            'request_body',
            'description',
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
                self.operation_ref,
                self.operation_id,
                self.parameters,
                self.request_body,
                self.description,
                self.server,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            operation_ref: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            operation_id: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            parameters: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            request_body: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            description: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            server: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'operation_ref', operation_ref)
            __dataclass__object_setattr(self, 'operation_id', operation_id)
            __dataclass__object_setattr(self, 'parameters', parameters)
            __dataclass__object_setattr(self, 'request_body', request_body)
            __dataclass__object_setattr(self, 'description', description)
            __dataclass__object_setattr(self, 'server', server)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.operation_ref)) is not None:
                parts.append(f"operation_ref={s}")
            if (s := __dataclass__repr__default_fn(self.operation_id)) is not None:
                parts.append(f"operation_id={s}")
            if (s := __dataclass__repr__default_fn(self.parameters)) is not None:
                parts.append(f"parameters={s}")
            if (s := __dataclass__repr__default_fn(self.request_body)) is not None:
                parts.append(f"request_body={s}")
            if (s := __dataclass__repr__default_fn(self.description)) is not None:
                parts.append(f"description={s}")
            if (s := __dataclass__repr__default_fn(self.server)) is not None:
                parts.append(f"server={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='5efd9c9b3c5e8c4c79ce1c3be09161390e995ccc',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('schema', True, True, None, True, False, False, None), 'instance', 'value', N"
            "one, False, False, False), (('example', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('examples', True, True, None, True, False, False, None), 'instance', 'value'"
            ", None, False, False, False), (('encoding', True, True, None, True, False, False, None), 'instance', 'valu"
            "e', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'MediaType'),
    ),
)
def _process_dataclass__5efd9c9b3c5e8c4c79ce1c3be09161390e995ccc():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                schema=self.schema,
                example=self.example,
                examples=self.examples,
                encoding=self.encoding,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.schema == other.schema and
                self.example == other.example and
                self.examples == other.examples and
                self.encoding == other.encoding
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'schema',
            'example',
            'examples',
            'encoding',
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
                self.schema,
                self.example,
                self.examples,
                self.encoding,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            schema: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            example: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            examples: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            encoding: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'schema', schema)
            __dataclass__object_setattr(self, 'example', example)
            __dataclass__object_setattr(self, 'examples', examples)
            __dataclass__object_setattr(self, 'encoding', encoding)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.schema)) is not None:
                parts.append(f"schema={s}")
            if (s := __dataclass__repr__default_fn(self.example)) is not None:
                parts.append(f"example={s}")
            if (s := __dataclass__repr__default_fn(self.examples)) is not None:
                parts.append(f"examples={s}")
            if (s := __dataclass__repr__default_fn(self.encoding)) is not None:
                parts.append(f"encoding={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='f0cf8a6c1964188fae9bbe6bcda47b725cebc9da',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('authorization_url', True, True, None, True, False, False, None), 'instance',"
            " 'missing', None, False, False, False), (('token_url', True, True, None, True, False, False, None), 'insta"
            "nce', 'missing', None, False, False, False), (('scopes', True, True, None, True, False, False, None), 'ins"
            "tance', 'missing', None, False, False, False), (('refresh_ur', True, True, None, True, False, False, None)"
            ", 'instance', 'value', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (Fals"
            "e, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'OauthFlow'),
    ),
)
def _process_dataclass__f0cf8a6c1964188fae9bbe6bcda47b725cebc9da():
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
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                authorization_url=self.authorization_url,
                token_url=self.token_url,
                scopes=self.scopes,
                refresh_ur=self.refresh_ur,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.authorization_url == other.authorization_url and
                self.token_url == other.token_url and
                self.scopes == other.scopes and
                self.refresh_ur == other.refresh_ur
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'authorization_url',
            'token_url',
            'scopes',
            'refresh_ur',
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
                self.authorization_url,
                self.token_url,
                self.scopes,
                self.refresh_ur,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            authorization_url: __dataclass__init__fields__0__annotation,
            token_url: __dataclass__init__fields__1__annotation,
            scopes: __dataclass__init__fields__2__annotation,
            refresh_ur: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'authorization_url', authorization_url)
            __dataclass__object_setattr(self, 'token_url', token_url)
            __dataclass__object_setattr(self, 'scopes', scopes)
            __dataclass__object_setattr(self, 'refresh_ur', refresh_ur)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.authorization_url)) is not None:
                parts.append(f"authorization_url={s}")
            if (s := __dataclass__repr__default_fn(self.token_url)) is not None:
                parts.append(f"token_url={s}")
            if (s := __dataclass__repr__default_fn(self.scopes)) is not None:
                parts.append(f"scopes={s}")
            if (s := __dataclass__repr__default_fn(self.refresh_ur)) is not None:
                parts.append(f"refresh_ur={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='603ce066e42888d5d9836606880c55da18463b8f',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('implicit', True, True, None, True, False, False, None), 'instance', 'value',"
            " None, False, False, False), (('password', True, True, None, True, False, False, None), 'instance', 'value"
            "', None, False, False, False), (('client_credentials', True, True, None, True, False, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('authorization_code', True, True, None, True, False, False, N"
            "one), 'instance', 'value', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), ("
            "False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'OauthFlows'),
    ),
)
def _process_dataclass__603ce066e42888d5d9836606880c55da18463b8f():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                implicit=self.implicit,
                password=self.password,
                client_credentials=self.client_credentials,
                authorization_code=self.authorization_code,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.implicit == other.implicit and
                self.password == other.password and
                self.client_credentials == other.client_credentials and
                self.authorization_code == other.authorization_code
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'implicit',
            'password',
            'client_credentials',
            'authorization_code',
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
                self.implicit,
                self.password,
                self.client_credentials,
                self.authorization_code,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            implicit: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            password: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            client_credentials: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            authorization_code: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'implicit', implicit)
            __dataclass__object_setattr(self, 'password', password)
            __dataclass__object_setattr(self, 'client_credentials', client_credentials)
            __dataclass__object_setattr(self, 'authorization_code', authorization_code)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.implicit)) is not None:
                parts.append(f"implicit={s}")
            if (s := __dataclass__repr__default_fn(self.password)) is not None:
                parts.append(f"password={s}")
            if (s := __dataclass__repr__default_fn(self.client_credentials)) is not None:
                parts.append(f"client_credentials={s}")
            if (s := __dataclass__repr__default_fn(self.authorization_code)) is not None:
                parts.append(f"authorization_code={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b4740fe5df20f4b16e4560e9e19dd9d8b9f62d49',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('openapi', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('info', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('json_schema_dialect', True, True, None, True, False, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('servers', True, True, None, True, False, False, None), 'inst"
            "ance', 'value', None, False, False, False), (('paths', True, True, None, True, False, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('webhooks', True, True, None, True, False, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('components', True, True, None, True, False, False, None), "
            "'instance', 'value', None, False, False, False), (('security', True, True, None, True, False, False, None)"
            ", 'instance', 'value', None, False, False, False), (('tags', True, True, None, True, False, False, None), "
            "'instance', 'value', None, False, False, False), (('external_docs', True, True, None, True, False, False, "
            "None), 'instance', 'value', None, False, False, False), (('x', True, True, None, True, False, False, None)"
            ", 'instance', 'value', None, False, False, False)), True, 1, ()), ((False,), (False,), (), (False,), (Fals"
            "e, False, ('callable',)), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'Openapi'),
    ),
)
def _process_dataclass__b4740fe5df20f4b16e4560e9e19dd9d8b9f62d49():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__01__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__02__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__02__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__03__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__03__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__04__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__04__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__05__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__05__default = __dataclass__spec.fields[5].default.must()
        __dataclass__init__fields__06__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__06__default = __dataclass__spec.fields[6].default.must()
        __dataclass__init__fields__07__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__07__default = __dataclass__spec.fields[7].default.must()
        __dataclass__init__fields__08__annotation = __dataclass__spec.fields[8].annotation
        __dataclass__init__fields__08__default = __dataclass__spec.fields[8].default.must()
        __dataclass__init__fields__09__annotation = __dataclass__spec.fields[9].annotation
        __dataclass__init__fields__09__default = __dataclass__spec.fields[9].default.must()
        __dataclass__init__fields__10__annotation = __dataclass__spec.fields[10].annotation
        __dataclass__init__fields__10__default = __dataclass__spec.fields[10].default.must()
        __dataclass__init__init_fns__0 = __dataclass__ctx['omcore.dataclasses.impl.concerns.init.InitFunctions'].values[0]
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                openapi=self.openapi,
                info=self.info,
                json_schema_dialect=self.json_schema_dialect,
                servers=self.servers,
                paths=self.paths,
                webhooks=self.webhooks,
                components=self.components,
                security=self.security,
                tags=self.tags,
                external_docs=self.external_docs,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.openapi == other.openapi and
                self.info == other.info and
                self.json_schema_dialect == other.json_schema_dialect and
                self.servers == other.servers and
                self.paths == other.paths and
                self.webhooks == other.webhooks and
                self.components == other.components and
                self.security == other.security and
                self.tags == other.tags and
                self.external_docs == other.external_docs and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'openapi',
            'info',
            'json_schema_dialect',
            'servers',
            'paths',
            'webhooks',
            'components',
            'security',
            'tags',
            'external_docs',
            'x',
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
                self.openapi,
                self.info,
                self.json_schema_dialect,
                self.servers,
                self.paths,
                self.webhooks,
                self.components,
                self.security,
                self.tags,
                self.external_docs,
                self.x,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            openapi: __dataclass__init__fields__00__annotation,
            info: __dataclass__init__fields__01__annotation,
            json_schema_dialect: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            servers: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            paths: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            webhooks: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            components: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            security: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            tags: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            external_docs: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            x: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'openapi', openapi)
            __dataclass__object_setattr(self, 'info', info)
            __dataclass__object_setattr(self, 'json_schema_dialect', json_schema_dialect)
            __dataclass__object_setattr(self, 'servers', servers)
            __dataclass__object_setattr(self, 'paths', paths)
            __dataclass__object_setattr(self, 'webhooks', webhooks)
            __dataclass__object_setattr(self, 'components', components)
            __dataclass__object_setattr(self, 'security', security)
            __dataclass__object_setattr(self, 'tags', tags)
            __dataclass__object_setattr(self, 'external_docs', external_docs)
            __dataclass__object_setattr(self, 'x', x)
            __dataclass__init__init_fns__0(self)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.openapi)) is not None:
                parts.append(f"openapi={s}")
            if (s := __dataclass__repr__default_fn(self.info)) is not None:
                parts.append(f"info={s}")
            if (s := __dataclass__repr__default_fn(self.json_schema_dialect)) is not None:
                parts.append(f"json_schema_dialect={s}")
            if (s := __dataclass__repr__default_fn(self.servers)) is not None:
                parts.append(f"servers={s}")
            if (s := __dataclass__repr__default_fn(self.paths)) is not None:
                parts.append(f"paths={s}")
            if (s := __dataclass__repr__default_fn(self.webhooks)) is not None:
                parts.append(f"webhooks={s}")
            if (s := __dataclass__repr__default_fn(self.components)) is not None:
                parts.append(f"components={s}")
            if (s := __dataclass__repr__default_fn(self.security)) is not None:
                parts.append(f"security={s}")
            if (s := __dataclass__repr__default_fn(self.tags)) is not None:
                parts.append(f"tags={s}")
            if (s := __dataclass__repr__default_fn(self.external_docs)) is not None:
                parts.append(f"external_docs={s}")
            if (s := __dataclass__repr__default_fn(self.x)) is not None:
                parts.append(f"x={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='fb0d4de44967999106c39603ac1aab5b06774b53',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('tags', True, True, None, True, False, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('summary', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('description', True, True, None, True, False, False, None), 'instance', 'value"
            "', None, False, False, False), (('external_docs', True, True, None, True, False, False, None), 'instance',"
            " 'value', None, False, False, False), (('operation_id', True, True, None, True, False, False, None), 'inst"
            "ance', 'value', None, False, False, False), (('parameters', True, True, None, True, False, False, None), '"
            "instance', 'value', None, False, False, False), (('request_body', True, True, None, True, False, False, No"
            "ne), 'instance', 'value', None, False, False, False), (('responses', True, True, None, True, False, False,"
            " None), 'instance', 'value', None, False, False, False), (('callbacks', True, True, None, True, False, Fal"
            "se, None), 'instance', 'value', None, False, False, False), (('deprecated', True, True, None, True, False,"
            " False, None), 'instance', 'value', None, False, False, False), (('security', True, True, None, True, Fals"
            "e, False, None), 'instance', 'value', None, False, False, False), (('servers', True, True, None, True, Fal"
            "se, False, None), 'instance', 'value', None, False, False, False), (('x', True, True, None, True, False, F"
            "alse, None), 'instance', 'value', None, False, False, False)), True, 1, ()), ((False,), (False,), (), (Fal"
            "se,), (False, False, ('callable',)), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'Operation'),
    ),
)
def _process_dataclass__fb0d4de44967999106c39603ac1aab5b06774b53():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__00__default = __dataclass__spec.fields[0].default.must()
        __dataclass__init__fields__01__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__01__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__02__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__02__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__03__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__03__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__04__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__04__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__05__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__05__default = __dataclass__spec.fields[5].default.must()
        __dataclass__init__fields__06__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__06__default = __dataclass__spec.fields[6].default.must()
        __dataclass__init__fields__07__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__07__default = __dataclass__spec.fields[7].default.must()
        __dataclass__init__fields__08__annotation = __dataclass__spec.fields[8].annotation
        __dataclass__init__fields__08__default = __dataclass__spec.fields[8].default.must()
        __dataclass__init__fields__09__annotation = __dataclass__spec.fields[9].annotation
        __dataclass__init__fields__09__default = __dataclass__spec.fields[9].default.must()
        __dataclass__init__fields__10__annotation = __dataclass__spec.fields[10].annotation
        __dataclass__init__fields__10__default = __dataclass__spec.fields[10].default.must()
        __dataclass__init__fields__11__annotation = __dataclass__spec.fields[11].annotation
        __dataclass__init__fields__11__default = __dataclass__spec.fields[11].default.must()
        __dataclass__init__fields__12__annotation = __dataclass__spec.fields[12].annotation
        __dataclass__init__fields__12__default = __dataclass__spec.fields[12].default.must()
        __dataclass__init__init_fns__0 = __dataclass__ctx['omcore.dataclasses.impl.concerns.init.InitFunctions'].values[0]
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                tags=self.tags,
                summary=self.summary,
                description=self.description,
                external_docs=self.external_docs,
                operation_id=self.operation_id,
                parameters=self.parameters,
                request_body=self.request_body,
                responses=self.responses,
                callbacks=self.callbacks,
                deprecated=self.deprecated,
                security=self.security,
                servers=self.servers,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.tags == other.tags and
                self.summary == other.summary and
                self.description == other.description and
                self.external_docs == other.external_docs and
                self.operation_id == other.operation_id and
                self.parameters == other.parameters and
                self.request_body == other.request_body and
                self.responses == other.responses and
                self.callbacks == other.callbacks and
                self.deprecated == other.deprecated and
                self.security == other.security and
                self.servers == other.servers and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'tags',
            'summary',
            'description',
            'external_docs',
            'operation_id',
            'parameters',
            'request_body',
            'responses',
            'callbacks',
            'deprecated',
            'security',
            'servers',
            'x',
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
                self.tags,
                self.summary,
                self.description,
                self.external_docs,
                self.operation_id,
                self.parameters,
                self.request_body,
                self.responses,
                self.callbacks,
                self.deprecated,
                self.security,
                self.servers,
                self.x,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            tags: __dataclass__init__fields__00__annotation = __dataclass__init__fields__00__default,
            summary: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            description: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            external_docs: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            operation_id: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            parameters: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            request_body: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            responses: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            callbacks: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            deprecated: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            security: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            servers: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            x: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'tags', tags)
            __dataclass__object_setattr(self, 'summary', summary)
            __dataclass__object_setattr(self, 'description', description)
            __dataclass__object_setattr(self, 'external_docs', external_docs)
            __dataclass__object_setattr(self, 'operation_id', operation_id)
            __dataclass__object_setattr(self, 'parameters', parameters)
            __dataclass__object_setattr(self, 'request_body', request_body)
            __dataclass__object_setattr(self, 'responses', responses)
            __dataclass__object_setattr(self, 'callbacks', callbacks)
            __dataclass__object_setattr(self, 'deprecated', deprecated)
            __dataclass__object_setattr(self, 'security', security)
            __dataclass__object_setattr(self, 'servers', servers)
            __dataclass__object_setattr(self, 'x', x)
            __dataclass__init__init_fns__0(self)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.tags)) is not None:
                parts.append(f"tags={s}")
            if (s := __dataclass__repr__default_fn(self.summary)) is not None:
                parts.append(f"summary={s}")
            if (s := __dataclass__repr__default_fn(self.description)) is not None:
                parts.append(f"description={s}")
            if (s := __dataclass__repr__default_fn(self.external_docs)) is not None:
                parts.append(f"external_docs={s}")
            if (s := __dataclass__repr__default_fn(self.operation_id)) is not None:
                parts.append(f"operation_id={s}")
            if (s := __dataclass__repr__default_fn(self.parameters)) is not None:
                parts.append(f"parameters={s}")
            if (s := __dataclass__repr__default_fn(self.request_body)) is not None:
                parts.append(f"request_body={s}")
            if (s := __dataclass__repr__default_fn(self.responses)) is not None:
                parts.append(f"responses={s}")
            if (s := __dataclass__repr__default_fn(self.callbacks)) is not None:
                parts.append(f"callbacks={s}")
            if (s := __dataclass__repr__default_fn(self.deprecated)) is not None:
                parts.append(f"deprecated={s}")
            if (s := __dataclass__repr__default_fn(self.security)) is not None:
                parts.append(f"security={s}")
            if (s := __dataclass__repr__default_fn(self.servers)) is not None:
                parts.append(f"servers={s}")
            if (s := __dataclass__repr__default_fn(self.x)) is not None:
                parts.append(f"x={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='5432fc1b2dca4e077be50eeb0172869f2ffd81e6',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('name', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('in_', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('common', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'Parameter'),
    ),
)
def _process_dataclass__5432fc1b2dca4e077be50eeb0172869f2ffd81e6():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
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
                in_=self.in_,
                common=self.common,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.in_ == other.in_ and
                self.common == other.common
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'in_',
            'common',
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
                self.in_,
                self.common,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
            in_: __dataclass__init__fields__1__annotation,
            common: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'in_', in_)
            __dataclass__object_setattr(self, 'common', common)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.name)) is not None:
                parts.append(f"name={s}")
            if (s := __dataclass__repr__default_fn(self.in_)) is not None:
                parts.append(f"in_={s}")
            if (s := __dataclass__repr__default_fn(self.common)) is not None:
                parts.append(f"common={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='5c208f7d34682c05ec1144d1694eecb4f8126766',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('description', True, True, None, True, False, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('required', True, True, None, True, False, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('deprecated', True, True, None, True, False, False, None), 'instance',"
            " 'value', None, False, False, False), (('allow_empty_value', True, True, None, True, False, False, None), "
            "'instance', 'value', None, False, False, False), (('style', True, True, None, True, False, False, None), '"
            "instance', 'value', None, False, False, False), (('explode', True, True, None, True, False, False, None), "
            "'instance', 'value', None, False, False, False), (('allow_reserved', True, True, None, True, False, False,"
            " None), 'instance', 'value', None, False, False, False), (('schema', True, True, None, True, False, False,"
            " None), 'instance', 'value', None, False, False, False), (('example', True, True, None, True, False, False"
            ", None), 'instance', 'value', None, False, False, False), (('examples', True, True, None, True, False, Fal"
            "se, None), 'instance', 'value', None, False, False, False), (('content', True, True, None, True, False, Fa"
            "lse, None), 'instance', 'value', None, False, False, False), (('matrix', True, True, None, True, False, Fa"
            "lse, None), 'instance', 'value', None, False, False, False), (('label', True, True, None, True, False, Fal"
            "se, None), 'instance', 'value', None, False, False, False), (('form', True, True, None, True, False, False"
            ", None), 'instance', 'value', None, False, False, False), (('simple', True, True, None, True, False, False"
            ", None), 'instance', 'value', None, False, False, False), (('space_delimited', True, True, None, True, Fal"
            "se, False, None), 'instance', 'value', None, False, False, False), (('pipe_delimited', True, True, None, T"
            "rue, False, False, None), 'instance', 'value', None, False, False, False), (('deep_object', True, True, No"
            "ne, True, False, False, None), 'instance', 'value', None, False, False, False)), True, 0, ()), ((False,), "
            "(False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'ParameterCommon'),
    ),
)
def _process_dataclass__5c208f7d34682c05ec1144d1694eecb4f8126766():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__00__default = __dataclass__spec.fields[0].default.must()
        __dataclass__init__fields__01__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__01__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__02__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__02__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__03__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__03__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__04__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__04__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__05__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__05__default = __dataclass__spec.fields[5].default.must()
        __dataclass__init__fields__06__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__06__default = __dataclass__spec.fields[6].default.must()
        __dataclass__init__fields__07__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__07__default = __dataclass__spec.fields[7].default.must()
        __dataclass__init__fields__08__annotation = __dataclass__spec.fields[8].annotation
        __dataclass__init__fields__08__default = __dataclass__spec.fields[8].default.must()
        __dataclass__init__fields__09__annotation = __dataclass__spec.fields[9].annotation
        __dataclass__init__fields__09__default = __dataclass__spec.fields[9].default.must()
        __dataclass__init__fields__10__annotation = __dataclass__spec.fields[10].annotation
        __dataclass__init__fields__10__default = __dataclass__spec.fields[10].default.must()
        __dataclass__init__fields__11__annotation = __dataclass__spec.fields[11].annotation
        __dataclass__init__fields__11__default = __dataclass__spec.fields[11].default.must()
        __dataclass__init__fields__12__annotation = __dataclass__spec.fields[12].annotation
        __dataclass__init__fields__12__default = __dataclass__spec.fields[12].default.must()
        __dataclass__init__fields__13__annotation = __dataclass__spec.fields[13].annotation
        __dataclass__init__fields__13__default = __dataclass__spec.fields[13].default.must()
        __dataclass__init__fields__14__annotation = __dataclass__spec.fields[14].annotation
        __dataclass__init__fields__14__default = __dataclass__spec.fields[14].default.must()
        __dataclass__init__fields__15__annotation = __dataclass__spec.fields[15].annotation
        __dataclass__init__fields__15__default = __dataclass__spec.fields[15].default.must()
        __dataclass__init__fields__16__annotation = __dataclass__spec.fields[16].annotation
        __dataclass__init__fields__16__default = __dataclass__spec.fields[16].default.must()
        __dataclass__init__fields__17__annotation = __dataclass__spec.fields[17].annotation
        __dataclass__init__fields__17__default = __dataclass__spec.fields[17].default.must()
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                description=self.description,
                required=self.required,
                deprecated=self.deprecated,
                allow_empty_value=self.allow_empty_value,
                style=self.style,
                explode=self.explode,
                allow_reserved=self.allow_reserved,
                schema=self.schema,
                example=self.example,
                examples=self.examples,
                content=self.content,
                matrix=self.matrix,
                label=self.label,
                form=self.form,
                simple=self.simple,
                space_delimited=self.space_delimited,
                pipe_delimited=self.pipe_delimited,
                deep_object=self.deep_object,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.description == other.description and
                self.required == other.required and
                self.deprecated == other.deprecated and
                self.allow_empty_value == other.allow_empty_value and
                self.style == other.style and
                self.explode == other.explode and
                self.allow_reserved == other.allow_reserved and
                self.schema == other.schema and
                self.example == other.example and
                self.examples == other.examples and
                self.content == other.content and
                self.matrix == other.matrix and
                self.label == other.label and
                self.form == other.form and
                self.simple == other.simple and
                self.space_delimited == other.space_delimited and
                self.pipe_delimited == other.pipe_delimited and
                self.deep_object == other.deep_object
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'description',
            'required',
            'deprecated',
            'allow_empty_value',
            'style',
            'explode',
            'allow_reserved',
            'schema',
            'example',
            'examples',
            'content',
            'matrix',
            'label',
            'form',
            'simple',
            'space_delimited',
            'pipe_delimited',
            'deep_object',
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
                self.description,
                self.required,
                self.deprecated,
                self.allow_empty_value,
                self.style,
                self.explode,
                self.allow_reserved,
                self.schema,
                self.example,
                self.examples,
                self.content,
                self.matrix,
                self.label,
                self.form,
                self.simple,
                self.space_delimited,
                self.pipe_delimited,
                self.deep_object,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            description: __dataclass__init__fields__00__annotation = __dataclass__init__fields__00__default,
            required: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            deprecated: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            allow_empty_value: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            style: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            explode: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            allow_reserved: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            schema: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            example: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            examples: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            content: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            matrix: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            label: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            form: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            simple: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            space_delimited: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            pipe_delimited: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            deep_object: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'description', description)
            __dataclass__object_setattr(self, 'required', required)
            __dataclass__object_setattr(self, 'deprecated', deprecated)
            __dataclass__object_setattr(self, 'allow_empty_value', allow_empty_value)
            __dataclass__object_setattr(self, 'style', style)
            __dataclass__object_setattr(self, 'explode', explode)
            __dataclass__object_setattr(self, 'allow_reserved', allow_reserved)
            __dataclass__object_setattr(self, 'schema', schema)
            __dataclass__object_setattr(self, 'example', example)
            __dataclass__object_setattr(self, 'examples', examples)
            __dataclass__object_setattr(self, 'content', content)
            __dataclass__object_setattr(self, 'matrix', matrix)
            __dataclass__object_setattr(self, 'label', label)
            __dataclass__object_setattr(self, 'form', form)
            __dataclass__object_setattr(self, 'simple', simple)
            __dataclass__object_setattr(self, 'space_delimited', space_delimited)
            __dataclass__object_setattr(self, 'pipe_delimited', pipe_delimited)
            __dataclass__object_setattr(self, 'deep_object', deep_object)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.description)) is not None:
                parts.append(f"description={s}")
            if (s := __dataclass__repr__default_fn(self.required)) is not None:
                parts.append(f"required={s}")
            if (s := __dataclass__repr__default_fn(self.deprecated)) is not None:
                parts.append(f"deprecated={s}")
            if (s := __dataclass__repr__default_fn(self.allow_empty_value)) is not None:
                parts.append(f"allow_empty_value={s}")
            if (s := __dataclass__repr__default_fn(self.style)) is not None:
                parts.append(f"style={s}")
            if (s := __dataclass__repr__default_fn(self.explode)) is not None:
                parts.append(f"explode={s}")
            if (s := __dataclass__repr__default_fn(self.allow_reserved)) is not None:
                parts.append(f"allow_reserved={s}")
            if (s := __dataclass__repr__default_fn(self.schema)) is not None:
                parts.append(f"schema={s}")
            if (s := __dataclass__repr__default_fn(self.example)) is not None:
                parts.append(f"example={s}")
            if (s := __dataclass__repr__default_fn(self.examples)) is not None:
                parts.append(f"examples={s}")
            if (s := __dataclass__repr__default_fn(self.content)) is not None:
                parts.append(f"content={s}")
            if (s := __dataclass__repr__default_fn(self.matrix)) is not None:
                parts.append(f"matrix={s}")
            if (s := __dataclass__repr__default_fn(self.label)) is not None:
                parts.append(f"label={s}")
            if (s := __dataclass__repr__default_fn(self.form)) is not None:
                parts.append(f"form={s}")
            if (s := __dataclass__repr__default_fn(self.simple)) is not None:
                parts.append(f"simple={s}")
            if (s := __dataclass__repr__default_fn(self.space_delimited)) is not None:
                parts.append(f"space_delimited={s}")
            if (s := __dataclass__repr__default_fn(self.pipe_delimited)) is not None:
                parts.append(f"pipe_delimited={s}")
            if (s := __dataclass__repr__default_fn(self.deep_object)) is not None:
                parts.append(f"deep_object={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d368581a71c52678cc1448f58a466b0f74813b58',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('ref', True, True, None, True, False, False, None), 'instance', 'value', None"
            ", False, False, False), (('summary', True, True, None, True, False, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('description', True, True, None, True, False, False, None), 'instance', 'value'"
            ", None, False, False, False), (('get', True, True, None, True, False, False, None), 'instance', 'value', N"
            "one, False, False, False), (('put', True, True, None, True, False, False, None), 'instance', 'value', None"
            ", False, False, False), (('post', True, True, None, True, False, False, None), 'instance', 'value', None, "
            "False, False, False), (('delete', True, True, None, True, False, False, None), 'instance', 'value', None, "
            "False, False, False), (('options', True, True, None, True, False, False, None), 'instance', 'value', None,"
            " False, False, False), (('head', True, True, None, True, False, False, None), 'instance', 'value', None, F"
            "alse, False, False), (('patch', True, True, None, True, False, False, None), 'instance', 'value', None, Fa"
            "lse, False, False), (('trace', True, True, None, True, False, False, None), 'instance', 'value', None, Fal"
            "se, False, False), (('servers', True, True, None, True, False, False, None), 'instance', 'value', None, Fa"
            "lse, False, False), (('parameters', True, True, None, True, False, False, None), 'instance', 'value', None"
            ", False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), ("
            "False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'PathItem'),
    ),
)
def _process_dataclass__d368581a71c52678cc1448f58a466b0f74813b58():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__00__default = __dataclass__spec.fields[0].default.must()
        __dataclass__init__fields__01__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__01__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__02__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__02__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__03__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__03__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__04__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__04__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__05__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__05__default = __dataclass__spec.fields[5].default.must()
        __dataclass__init__fields__06__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__06__default = __dataclass__spec.fields[6].default.must()
        __dataclass__init__fields__07__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__07__default = __dataclass__spec.fields[7].default.must()
        __dataclass__init__fields__08__annotation = __dataclass__spec.fields[8].annotation
        __dataclass__init__fields__08__default = __dataclass__spec.fields[8].default.must()
        __dataclass__init__fields__09__annotation = __dataclass__spec.fields[9].annotation
        __dataclass__init__fields__09__default = __dataclass__spec.fields[9].default.must()
        __dataclass__init__fields__10__annotation = __dataclass__spec.fields[10].annotation
        __dataclass__init__fields__10__default = __dataclass__spec.fields[10].default.must()
        __dataclass__init__fields__11__annotation = __dataclass__spec.fields[11].annotation
        __dataclass__init__fields__11__default = __dataclass__spec.fields[11].default.must()
        __dataclass__init__fields__12__annotation = __dataclass__spec.fields[12].annotation
        __dataclass__init__fields__12__default = __dataclass__spec.fields[12].default.must()
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                ref=self.ref,
                summary=self.summary,
                description=self.description,
                get=self.get,
                put=self.put,
                post=self.post,
                delete=self.delete,
                options=self.options,
                head=self.head,
                patch=self.patch,
                trace=self.trace,
                servers=self.servers,
                parameters=self.parameters,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.ref == other.ref and
                self.summary == other.summary and
                self.description == other.description and
                self.get == other.get and
                self.put == other.put and
                self.post == other.post and
                self.delete == other.delete and
                self.options == other.options and
                self.head == other.head and
                self.patch == other.patch and
                self.trace == other.trace and
                self.servers == other.servers and
                self.parameters == other.parameters
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'ref',
            'summary',
            'description',
            'get',
            'put',
            'post',
            'delete',
            'options',
            'head',
            'patch',
            'trace',
            'servers',
            'parameters',
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
                self.ref,
                self.summary,
                self.description,
                self.get,
                self.put,
                self.post,
                self.delete,
                self.options,
                self.head,
                self.patch,
                self.trace,
                self.servers,
                self.parameters,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            ref: __dataclass__init__fields__00__annotation = __dataclass__init__fields__00__default,
            summary: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            description: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            get: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            put: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            post: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            delete: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            options: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            head: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            patch: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            trace: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            servers: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            parameters: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'ref', ref)
            __dataclass__object_setattr(self, 'summary', summary)
            __dataclass__object_setattr(self, 'description', description)
            __dataclass__object_setattr(self, 'get', get)
            __dataclass__object_setattr(self, 'put', put)
            __dataclass__object_setattr(self, 'post', post)
            __dataclass__object_setattr(self, 'delete', delete)
            __dataclass__object_setattr(self, 'options', options)
            __dataclass__object_setattr(self, 'head', head)
            __dataclass__object_setattr(self, 'patch', patch)
            __dataclass__object_setattr(self, 'trace', trace)
            __dataclass__object_setattr(self, 'servers', servers)
            __dataclass__object_setattr(self, 'parameters', parameters)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.ref)) is not None:
                parts.append(f"ref={s}")
            if (s := __dataclass__repr__default_fn(self.summary)) is not None:
                parts.append(f"summary={s}")
            if (s := __dataclass__repr__default_fn(self.description)) is not None:
                parts.append(f"description={s}")
            if (s := __dataclass__repr__default_fn(self.get)) is not None:
                parts.append(f"get={s}")
            if (s := __dataclass__repr__default_fn(self.put)) is not None:
                parts.append(f"put={s}")
            if (s := __dataclass__repr__default_fn(self.post)) is not None:
                parts.append(f"post={s}")
            if (s := __dataclass__repr__default_fn(self.delete)) is not None:
                parts.append(f"delete={s}")
            if (s := __dataclass__repr__default_fn(self.options)) is not None:
                parts.append(f"options={s}")
            if (s := __dataclass__repr__default_fn(self.head)) is not None:
                parts.append(f"head={s}")
            if (s := __dataclass__repr__default_fn(self.patch)) is not None:
                parts.append(f"patch={s}")
            if (s := __dataclass__repr__default_fn(self.trace)) is not None:
                parts.append(f"trace={s}")
            if (s := __dataclass__repr__default_fn(self.servers)) is not None:
                parts.append(f"servers={s}")
            if (s := __dataclass__repr__default_fn(self.parameters)) is not None:
                parts.append(f"parameters={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='ca2baaedf883af7acfc6c4c233e110b8a19bdb91',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('ref', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('summary', True, True, None, True, False, False, None), 'instance', 'value', N"
            "one, False, False, False), (('description', True, True, None, True, False, False, None), 'instance', 'valu"
            "e', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'Reference'),
    ),
)
def _process_dataclass__ca2baaedf883af7acfc6c4c233e110b8a19bdb91():
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
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                ref=self.ref,
                summary=self.summary,
                description=self.description,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.ref == other.ref and
                self.summary == other.summary and
                self.description == other.description
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'ref',
            'summary',
            'description',
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
                self.ref,
                self.summary,
                self.description,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            ref: __dataclass__init__fields__0__annotation,
            summary: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            description: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'ref', ref)
            __dataclass__object_setattr(self, 'summary', summary)
            __dataclass__object_setattr(self, 'description', description)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.ref)) is not None:
                parts.append(f"ref={s}")
            if (s := __dataclass__repr__default_fn(self.summary)) is not None:
                parts.append(f"summary={s}")
            if (s := __dataclass__repr__default_fn(self.description)) is not None:
                parts.append(f"description={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b75fd83c530c89e8d35eefc94c3f8b3b32c68198',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('content', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('description', True, True, None, True, False, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('required', True, True, None, True, False, False, None), 'instance', "
            "'value', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()),"
            " ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'RequestBody'),
    ),
)
def _process_dataclass__b75fd83c530c89e8d35eefc94c3f8b3b32c68198():
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
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                content=self.content,
                description=self.description,
                required=self.required,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.content == other.content and
                self.description == other.description and
                self.required == other.required
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'content',
            'description',
            'required',
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
                self.content,
                self.description,
                self.required,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            content: __dataclass__init__fields__0__annotation,
            description: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            required: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'content', content)
            __dataclass__object_setattr(self, 'description', description)
            __dataclass__object_setattr(self, 'required', required)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.content)) is not None:
                parts.append(f"content={s}")
            if (s := __dataclass__repr__default_fn(self.description)) is not None:
                parts.append(f"description={s}")
            if (s := __dataclass__repr__default_fn(self.required)) is not None:
                parts.append(f"required={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e05c09f817ffc631b829f77dadde62e31806e537',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('description', True, True, None, True, False, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('headers', True, True, None, True, False, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('content', True, True, None, True, False, False, None), 'instance', '"
            "value', None, False, False, False), (('links', True, True, None, True, False, False, None), 'instance', 'v"
            "alue', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ("
            "(),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'Response'),
    ),
)
def _process_dataclass__e05c09f817ffc631b829f77dadde62e31806e537():
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
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                description=self.description,
                headers=self.headers,
                content=self.content,
                links=self.links,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.description == other.description and
                self.headers == other.headers and
                self.content == other.content and
                self.links == other.links
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'description',
            'headers',
            'content',
            'links',
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
                self.description,
                self.headers,
                self.content,
                self.links,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            description: __dataclass__init__fields__0__annotation,
            headers: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            content: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            links: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'description', description)
            __dataclass__object_setattr(self, 'headers', headers)
            __dataclass__object_setattr(self, 'content', content)
            __dataclass__object_setattr(self, 'links', links)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.description)) is not None:
                parts.append(f"description={s}")
            if (s := __dataclass__repr__default_fn(self.headers)) is not None:
                parts.append(f"headers={s}")
            if (s := __dataclass__repr__default_fn(self.content)) is not None:
                parts.append(f"content={s}")
            if (s := __dataclass__repr__default_fn(self.links)) is not None:
                parts.append(f"links={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='2bb5f8a3872a7a100cd9d40d9ea8b76a4f89144e',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('discriminator', True, True, None, True, False, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('xml', True, True, None, True, False, False, None), 'instance', 'value"
            "', None, False, False, False), (('external_docs', True, True, None, True, False, False, None), 'instance',"
            " 'value', None, False, False, False), (('example', True, True, None, True, False, False, None), 'instance'"
            ", 'value', None, False, False, False), (('keywords', True, True, None, True, False, False, None), 'instanc"
            "e', 'value', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, "
            "()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'Schema'),
    ),
)
def _process_dataclass__2bb5f8a3872a7a100cd9d40d9ea8b76a4f89144e():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                discriminator=self.discriminator,
                xml=self.xml,
                external_docs=self.external_docs,
                example=self.example,
                keywords=self.keywords,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.discriminator == other.discriminator and
                self.xml == other.xml and
                self.external_docs == other.external_docs and
                self.example == other.example and
                self.keywords == other.keywords
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'discriminator',
            'xml',
            'external_docs',
            'example',
            'keywords',
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
                self.discriminator,
                self.xml,
                self.external_docs,
                self.example,
                self.keywords,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            discriminator: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            xml: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            external_docs: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            example: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            keywords: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'discriminator', discriminator)
            __dataclass__object_setattr(self, 'xml', xml)
            __dataclass__object_setattr(self, 'external_docs', external_docs)
            __dataclass__object_setattr(self, 'example', example)
            __dataclass__object_setattr(self, 'keywords', keywords)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.discriminator)) is not None:
                parts.append(f"discriminator={s}")
            if (s := __dataclass__repr__default_fn(self.xml)) is not None:
                parts.append(f"xml={s}")
            if (s := __dataclass__repr__default_fn(self.external_docs)) is not None:
                parts.append(f"external_docs={s}")
            if (s := __dataclass__repr__default_fn(self.example)) is not None:
                parts.append(f"example={s}")
            if (s := __dataclass__repr__default_fn(self.keywords)) is not None:
                parts.append(f"keywords={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='471a3ab0b1b54c9628e968f33271de7f048da23a',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('type', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('scheme', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('name', True, True, None, True, False, False, None), 'instance', 'value', N"
            "one, False, False, False), (('in_', True, True, None, True, False, False, None), 'instance', 'value', None"
            ", False, False, False), (('description', True, True, None, True, False, False, None), 'instance', 'value',"
            " None, False, False, False), (('bearer_format', True, True, None, True, False, False, None), 'instance', '"
            "value', None, False, False, False), (('flows', True, True, None, True, False, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('open_id_connect_url', True, True, None, True, False, False, None), '"
            "instance', 'value', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, "
            "False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'SecurityScheme'),
    ),
)
def _process_dataclass__471a3ab0b1b54c9628e968f33271de7f048da23a():
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
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                type=self.type,
                scheme=self.scheme,
                name=self.name,
                in_=self.in_,
                description=self.description,
                bearer_format=self.bearer_format,
                flows=self.flows,
                open_id_connect_url=self.open_id_connect_url,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type and
                self.scheme == other.scheme and
                self.name == other.name and
                self.in_ == other.in_ and
                self.description == other.description and
                self.bearer_format == other.bearer_format and
                self.flows == other.flows and
                self.open_id_connect_url == other.open_id_connect_url
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'type',
            'scheme',
            'name',
            'in_',
            'description',
            'bearer_format',
            'flows',
            'open_id_connect_url',
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
                self.type,
                self.scheme,
                self.name,
                self.in_,
                self.description,
                self.bearer_format,
                self.flows,
                self.open_id_connect_url,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            type: __dataclass__init__fields__0__annotation,
            scheme: __dataclass__init__fields__1__annotation,
            name: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            in_: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            description: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            bearer_format: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            flows: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
            open_id_connect_url: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'type', type)
            __dataclass__object_setattr(self, 'scheme', scheme)
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'in_', in_)
            __dataclass__object_setattr(self, 'description', description)
            __dataclass__object_setattr(self, 'bearer_format', bearer_format)
            __dataclass__object_setattr(self, 'flows', flows)
            __dataclass__object_setattr(self, 'open_id_connect_url', open_id_connect_url)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.type)) is not None:
                parts.append(f"type={s}")
            if (s := __dataclass__repr__default_fn(self.scheme)) is not None:
                parts.append(f"scheme={s}")
            if (s := __dataclass__repr__default_fn(self.name)) is not None:
                parts.append(f"name={s}")
            if (s := __dataclass__repr__default_fn(self.in_)) is not None:
                parts.append(f"in_={s}")
            if (s := __dataclass__repr__default_fn(self.description)) is not None:
                parts.append(f"description={s}")
            if (s := __dataclass__repr__default_fn(self.bearer_format)) is not None:
                parts.append(f"bearer_format={s}")
            if (s := __dataclass__repr__default_fn(self.flows)) is not None:
                parts.append(f"flows={s}")
            if (s := __dataclass__repr__default_fn(self.open_id_connect_url)) is not None:
                parts.append(f"open_id_connect_url={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b37cc21f4673d8549580d9ec3258a5327e96e8e6',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('url', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('description', True, True, None, True, False, False, None), 'instance', 'value"
            "', None, False, False, False), (('variables', True, True, None, True, False, False, None), 'instance', 'va"
            "lue', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (("
            "),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'Server'),
    ),
)
def _process_dataclass__b37cc21f4673d8549580d9ec3258a5327e96e8e6():
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
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                url=self.url,
                description=self.description,
                variables=self.variables,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.url == other.url and
                self.description == other.description and
                self.variables == other.variables
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'url',
            'description',
            'variables',
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
                self.url,
                self.description,
                self.variables,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            url: __dataclass__init__fields__0__annotation,
            description: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            variables: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'url', url)
            __dataclass__object_setattr(self, 'description', description)
            __dataclass__object_setattr(self, 'variables', variables)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.url)) is not None:
                parts.append(f"url={s}")
            if (s := __dataclass__repr__default_fn(self.description)) is not None:
                parts.append(f"description={s}")
            if (s := __dataclass__repr__default_fn(self.variables)) is not None:
                parts.append(f"variables={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b59acf57df6cc10037f0579c3cda6197a0c519e5',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('default', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('enum', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('description', True, True, None, True, False, False, None), 'instance', 'val"
            "ue', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (()"
            ",), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'ServerVariable'),
    ),
)
def _process_dataclass__b59acf57df6cc10037f0579c3cda6197a0c519e5():
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
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                default=self.default,
                enum=self.enum,
                description=self.description,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.default == other.default and
                self.enum == other.enum and
                self.description == other.description
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'default',
            'enum',
            'description',
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
                self.default,
                self.enum,
                self.description,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            default: __dataclass__init__fields__0__annotation,
            enum: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            description: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'default', default)
            __dataclass__object_setattr(self, 'enum', enum)
            __dataclass__object_setattr(self, 'description', description)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.default)) is not None:
                parts.append(f"default={s}")
            if (s := __dataclass__repr__default_fn(self.enum)) is not None:
                parts.append(f"enum={s}")
            if (s := __dataclass__repr__default_fn(self.description)) is not None:
                parts.append(f"description={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='ff2d957c7e02e994b60c810df5e2fc5fcc936db7',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('name', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('description', True, True, None, True, False, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('external_docs', True, True, None, True, False, False, None), 'instance'"
            ", 'value', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()"
            "), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'Tag'),
    ),
)
def _process_dataclass__ff2d957c7e02e994b60c810df5e2fc5fcc936db7():
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
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
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
                description=self.description,
                external_docs=self.external_docs,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.description == other.description and
                self.external_docs == other.external_docs
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'description',
            'external_docs',
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
                self.description,
                self.external_docs,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
            description: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            external_docs: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'description', description)
            __dataclass__object_setattr(self, 'external_docs', external_docs)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.name)) is not None:
                parts.append(f"name={s}")
            if (s := __dataclass__repr__default_fn(self.description)) is not None:
                parts.append(f"description={s}")
            if (s := __dataclass__repr__default_fn(self.external_docs)) is not None:
                parts.append(f"external_docs={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='50ab3264f76b5872f04dee2993b5634f3b696fef',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('name', True, True, None, True, False, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('namespace', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('prefix', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('attribute', True, True, None, True, False, False, None), 'instance', 'value"
            "', None, False, False, False), (('wrapped', True, True, None, True, False, False, None), 'instance', 'valu"
            "e', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.openapi', 'Xml'),
    ),
)
def _process_dataclass__50ab3264f76b5872f04dee2993b5634f3b696fef():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
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
                namespace=self.namespace,
                prefix=self.prefix,
                attribute=self.attribute,
                wrapped=self.wrapped,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.namespace == other.namespace and
                self.prefix == other.prefix and
                self.attribute == other.attribute and
                self.wrapped == other.wrapped
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'namespace',
            'prefix',
            'attribute',
            'wrapped',
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
                self.namespace,
                self.prefix,
                self.attribute,
                self.wrapped,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            namespace: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            prefix: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            attribute: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            wrapped: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'namespace', namespace)
            __dataclass__object_setattr(self, 'prefix', prefix)
            __dataclass__object_setattr(self, 'attribute', attribute)
            __dataclass__object_setattr(self, 'wrapped', wrapped)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.name)) is not None:
                parts.append(f"name={s}")
            if (s := __dataclass__repr__default_fn(self.namespace)) is not None:
                parts.append(f"namespace={s}")
            if (s := __dataclass__repr__default_fn(self.prefix)) is not None:
                parts.append(f"prefix={s}")
            if (s := __dataclass__repr__default_fn(self.attribute)) is not None:
                parts.append(f"attribute={s}")
            if (s := __dataclass__repr__default_fn(self.wrapped)) is not None:
                parts.append(f"wrapped={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='5b40eb558df58420862911137ee815099799d794',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('schema', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('names', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.tools.jsonschema', 'OpenapiJsonschema'),
    ),
)
def _process_dataclass__5b40eb558df58420862911137ee815099799d794():
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
                schema=self.schema,
                names=self.names,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.schema == other.schema and
                self.names == other.names
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'schema',
            'names',
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
                self.schema,
                self.names,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            schema: __dataclass__init__fields__0__annotation,
            names: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'schema', schema)
            __dataclass__object_setattr(self, 'names', names)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"schema={self.schema!r}")
            parts.append(f"names={self.names!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c7aa662ba66b65730c245b75025a5272386c1f41',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('name', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('schema', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.specs.openapi.tools.jsonschema', '_NamedSchema'),
    ),
)
def _process_dataclass__c7aa662ba66b65730c245b75025a5272386c1f41():
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
                schema=self.schema,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.schema == other.schema
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'schema',
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
                self.schema,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
            schema: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'schema', schema)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"schema={self.schema!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
