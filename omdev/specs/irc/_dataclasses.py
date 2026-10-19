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
    installer_sha1='60382027b1fa30f68941d60600e39d09b9ce6b13',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
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
def _process_dataclass__60382027b1fa30f68941d60600e39d09b9ce6b13():
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
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='0436f9b5e64141f4dfc12f63d638508fd5fd6192',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, True), ((('name', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('params', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('unpack_params', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False)), False, 1, ()), ((False,), (False,), (), (False,), (False, False, ('call"
            "able',)), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.formats', 'MessageFormat'),
    ),
)
def _process_dataclass__0436f9b5e64141f4dfc12f63d638508fd5fd6192():
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
    installer_sha1='82f1fb8ec85d4f8c1e9bc6527e636e3771779a7c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('name', True, True, None, True, False, False, None), 'instance', 'missing', Non"
            "e, True, False, False), (('optional', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('arity', True, True, None, True, False, False, None), 'instance', 'value', Non"
            "e, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (),"
            " (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.formats', 'MessageFormat.KwargParam'),
    ),
)
def _process_dataclass__82f1fb8ec85d4f8c1e9bc6527e636e3771779a7c():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__validate = __dataclass__spec.fields[0].validate
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__override__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__override__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__FieldFnValidationError = __dataclass__globals['__dataclass__FieldFnValidationError']
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='ecaebfce768a42320555a328d623f23af96ff96a',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('text', True, True, None, True, False, False, None), 'instance', 'missing', Non"
            "e, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.formats', 'MessageFormat.LiteralParam'),
    ),
)
def _process_dataclass__ecaebfce768a42320555a328d623f23af96ff96a():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='2e9c2c8314bdc172df0c232bdc5c95c17700fd22',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), (), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.formats', 'MessageFormat.Param'),
    ),
)
def _process_dataclass__2e9c2c8314bdc172df0c232bdc5c95c17700fd22():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='9b795c0760f94abced4ad6300eb7ce6021189fb6',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('target', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'AdminMessage'),
        ('omdev.specs.irc.messages.messages', 'MotdMessage'),
        ('omdev.specs.irc.messages.messages', 'VersionMessage'),
    ),
)
def _process_dataclass__9b795c0760f94abced4ad6300eb7ce6021189fb6():
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
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='9f72a88cc440e6e56efb147a25959e1ba8188344',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('text', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'AwayMessage'),
    ),
)
def _process_dataclass__9f72a88cc440e6e56efb147a25959e1ba8188344():
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
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='301e9951d6c2a1f4b3609c992086d0aaf3337e85',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('subcommand', True, True, None, True, False, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('capabilities', True, True, None, True, False, False, None), 'instance"
            "', 'missing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False"
            ", ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'CapMessage'),
    ),
)
def _process_dataclass__301e9951d6c2a1f4b3609c992086d0aaf3337e85():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__override__fields__1__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='ab974bfebfa45427aed03869cc1b5c2ca6ee5f03',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('target_server', True, True, None, True, False, False, None), 'instance', 'm"
            "issing', None, False, False, False), (('port', True, True, None, True, False, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('remote_server', True, True, None, True, False, False, None), 'instan"
            "ce', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False"
            ", ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'ConnectMessage'),
    ),
)
def _process_dataclass__ab974bfebfa45427aed03869cc1b5c2ca6ee5f03():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__override__fields__1__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__override__fields__2__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='943bb04f76952eb1d84ebbee0671159b4a36a4f2',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('reason', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'ErrorMessage'),
        ('omdev.specs.irc.messages.messages', 'QuitMessage'),
    ),
)
def _process_dataclass__943bb04f76952eb1d84ebbee0671159b4a36a4f2():
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
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='ae53f655803ff31b986116a61734164c7c3b43b4',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('subject', True, True, None, True, False, False, None), 'instance', 'value',"
            " None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'HelpMessage'),
    ),
)
def _process_dataclass__ae53f655803ff31b986116a61734164c7c3b43b4():
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
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='25c3d9818d881d7f66537608d2f1c1cfd362ba7c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('nickname', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('channel', True, True, None, True, False, False, None), 'instance', 'mis"
            "sing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), "
            "((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'InviteMessage'),
    ),
)
def _process_dataclass__25c3d9818d881d7f66537608d2f1c1cfd362ba7c():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__override__fields__1__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='33f5cea30e545684f4db0353123dbb6ade5f3198',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('channels', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, False, False, False)), False, 1, ()), ((False,), (False,), (), (False,), (False, False, ('callab"
            "le',)), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'JoinMessage'),
    ),
)
def _process_dataclass__33f5cea30e545684f4db0353123dbb6ade5f3198():
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
        __dataclass__init__init_fns__0 = __dataclass__ctx['omcore.dataclasses.impl.concerns.init.InitFunctions'].values[0]
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='16fa967564f81cea75c80c8664036e8e35e62c8b',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('channel', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('users', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('comment', True, True, None, True, False, False, None), 'instance', 'val"
            "ue', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (("
            "),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'KickMessage'),
    ),
)
def _process_dataclass__16fa967564f81cea75c80c8664036e8e35e62c8b():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__override__fields__1__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__override__fields__2__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='0c2977abdaea373d7aa32715ad09f4f271b15ece',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('nickname', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('comment', True, True, None, True, False, False, None), 'instance', 'mis"
            "sing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), "
            "((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'KillMessage'),
    ),
)
def _process_dataclass__0c2977abdaea373d7aa32715ad09f4f271b15ece():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__override__fields__1__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='2efc8023542d05678e66555fdf23e1c5a1946cb4',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('channels', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('elistconds', True, True, None, True, False, False, None), 'instance', '"
            "missing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()"
            "), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'ListMessage'),
    ),
)
def _process_dataclass__2efc8023542d05678e66555fdf23e1c5a1946cb4():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__override__fields__1__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='ab3074af1ee9aa9b6842ec571085b1d186833162',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('target', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('modestring', True, True, None, True, False, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('mode_arguments', True, True, None, True, False, False, None), 'instan"
            "ce', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False"
            ", ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'ModeMessage'),
    ),
)
def _process_dataclass__ab3074af1ee9aa9b6842ec571085b1d186833162():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__override__fields__1__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__override__fields__2__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='7db92e357640058df6755f4f66b9d09a0e909fd4',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('channels', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, True, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'NamesMessage'),
    ),
)
def _process_dataclass__7db92e357640058df6755f4f66b9d09a0e909fd4():
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
        __dataclass__init__fields__2__validate = __dataclass__spec.fields[2].validate
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__FieldFnValidationError = __dataclass__globals['__dataclass__FieldFnValidationError']
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='d34208c989941a87da2a47900422df8b57d9e8fa',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('nickname', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (()"
            ",), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'NickMessage'),
    ),
)
def _process_dataclass__d34208c989941a87da2a47900422df8b57d9e8fa():
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
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='9f78263be6ab7019468c2aa06cb4fc0e4f3e7b35',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('targets', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('text', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'NoticeMessage'),
        ('omdev.specs.irc.messages.messages', 'PrivmsgMessage'),
    ),
)
def _process_dataclass__9f78263be6ab7019468c2aa06cb4fc0e4f3e7b35():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__override__fields__1__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='8fe5024418938960d143a6f897b2aeb1d025d09f',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('name', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('password', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (()"
            ",), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'OperMessage'),
    ),
)
def _process_dataclass__8fe5024418938960d143a6f897b2aeb1d025d09f():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__override__fields__1__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='c65a6356b1efda9e8fed456ad2e12bd009196240',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('channels', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, True, False, False), (('reason', True, True, None, True, False, False, None), 'instance', 'value"
            "', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'PartMessage'),
    ),
)
def _process_dataclass__c65a6356b1efda9e8fed456ad2e12bd009196240():
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
        __dataclass__init__fields__2__validate = __dataclass__spec.fields[2].validate
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__override__fields__1__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__FieldFnValidationError = __dataclass__globals['__dataclass__FieldFnValidationError']
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='025c1e815ee2501eb12051c935d0cc6b549bc686',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('password', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (()"
            ",), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'PassMessage'),
    ),
)
def _process_dataclass__025c1e815ee2501eb12051c935d0cc6b549bc686():
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
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='87386a08c5ab595f7f7becabd8b326045973d43c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('token', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'PingMessage'),
    ),
)
def _process_dataclass__87386a08c5ab595f7f7becabd8b326045973d43c():
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
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='2d288b9b31008c4144c83be27e47647fb9cf2e51',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('token', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('server', True, True, None, True, False, False, None), 'instance', 'value',"
            " None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'PongMessage'),
    ),
)
def _process_dataclass__2d288b9b31008c4144c83be27e47647fb9cf2e51():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__override__fields__1__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='ec3f775d9f60117f7416b4451915fe13ed038843',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('server', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('comment', True, True, None, True, False, False, None), 'instance', 'missi"
            "ng', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (("
            "),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'SquitMessage'),
    ),
)
def _process_dataclass__ec3f775d9f60117f7416b4451915fe13ed038843():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__override__fields__1__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='99c6c7c28b3a801f17bc32f466da221e7b27efd8',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('query', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('server', True, True, None, True, False, False, None), 'instance', 'value',"
            " None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'StatsMessage'),
    ),
)
def _process_dataclass__99c6c7c28b3a801f17bc32f466da221e7b27efd8():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__override__fields__1__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='7dec5f6fd5b4e8d95deb6a7c419b8588780da4eb',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('server', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'TimeMessage'),
    ),
)
def _process_dataclass__7dec5f6fd5b4e8d95deb6a7c419b8588780da4eb():
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
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='698e8394d3e6d8b3be61321a2393f525a267dee6',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('channel', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('topic', True, True, None, True, False, False, None), 'instance', 'value'"
            ", None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'TopicMessage'),
    ),
)
def _process_dataclass__698e8394d3e6d8b3be61321a2393f525a267dee6():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__override__fields__1__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='a64ab5575951f1c17d7b81a5f9709bfcd6724929',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('username', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('realname', True, True, None, True, False, False, None), 'instance', 'mi"
            "ssing', None, False, False, False), (('param1', True, True, None, True, False, False, None), 'instance', '"
            "value', None, False, False, False), (('param2', True, True, None, True, False, False, None), 'instance', '"
            "value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()),"
            " ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'UserMessage'),
    ),
)
def _process_dataclass__a64ab5575951f1c17d7b81a5f9709bfcd6724929():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__default = __dataclass__spec.fields[5].default.must()
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__override__fields__1__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__override__fields__2__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__override__fields__3__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='a64e2a0f9d44ef62cfd88c88931c3dbf63407b47',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('nicknames', True, True, None, True, False, False, None), 'instance', 'value"
            "', None, True, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'UserhostMessage'),
    ),
)
def _process_dataclass__a64e2a0f9d44ef62cfd88c88931c3dbf63407b47():
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
        __dataclass__init__fields__2__validate = __dataclass__spec.fields[2].validate
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__FieldFnValidationError = __dataclass__globals['__dataclass__FieldFnValidationError']
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='34b771a561cb9045f4879f65ce39e6c3b0518e2a',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('text', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'WallopsMessage'),
    ),
)
def _process_dataclass__34b771a561cb9045f4879f65ce39e6c3b0518e2a():
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
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='4b1fc278e14c63a6492f1e4265663f0feedab198',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('mask', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'WhoMessage'),
    ),
)
def _process_dataclass__4b1fc278e14c63a6492f1e4265663f0feedab198():
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
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='be93e36b8f2a109662e0db4c35f42aa6c7d70655',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('nick', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('target', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'WhoisMessage'),
    ),
)
def _process_dataclass__be93e36b8f2a109662e0db4c35f42aa6c7d70655():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__override__fields__1__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='a4e1e20ebeb6a995488c5b341a5fc26b8fd339e0',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, True, False, Fals"
            "e, False, False, True), ((('FORMAT', True, True, None, True, None, False, None), 'class_var', 'missing', N"
            "one, False, False, False), (('REPLIES', True, True, None, True, None, False, None), 'class_var', 'value', "
            "None, False, False, False), (('nick', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('count', True, True, None, True, False, False, None), 'instance', 'value', N"
            "one, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.messages.messages', 'WhowasMessage'),
    ),
)
def _process_dataclass__a4e1e20ebeb6a995488c5b341a5fc26b8fd339e0():
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
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__override__fields__0__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__override__fields__1__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__property = __dataclass__globals['__dataclass__property']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='a7362c742da9b0702fbafcbaf971e36ed37f17dc',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('name', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.numerics.formats', 'Formats.Name'),
    ),
)
def _process_dataclass__a7362c742da9b0702fbafcbaf971e36ed37f17dc():
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
    installer_sha1='d2e556cffd35c8ef16a83ebe9fa8962562f94f68',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('body', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.numerics.formats', 'Formats.Optional'),
        ('omdev.specs.irc.numerics.formats', 'Formats.Variadic'),
    ),
)
def _process_dataclass__d2e556cffd35c8ef16a83ebe9fa8962562f94f68():
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
    installer_sha1='348274680fff3bfd35dfa52f7858b60399a7df02',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('name', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('num', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('formats', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.numerics.types', 'NumericReply'),
    ),
)
def _process_dataclass__348274680fff3bfd35dfa52f7858b60399a7df02():
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
    installer_sha1='56d32f7446f630f6f2f751cb7a88badbc3527196',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('source', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('command', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('params', True, True, None, True, False, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('force_trailing', True, True, None, True, False, False, None), 'instan"
            "ce', 'value', None, False, False, False), (('tags', True, True, None, True, False, False, None), 'instance"
            "', 'value', None, False, False, False), (('client_only_tags', True, True, None, True, False, False, None),"
            " 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (Fals"
            "e, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.protocol.message', 'Message'),
    ),
)
def _process_dataclass__56d32f7446f630f6f2f751cb7a88badbc3527196():
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
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__default = __dataclass__spec.fields[5].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='7c24abce9d19666ef75be7ea938bb52f4dc73fb3',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('name', True, True, None, True, False, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('user', True, True, None, True, False, False, None), 'instance', 'value', None,"
            " False, False, False), (('host', True, True, None, True, False, False, None), 'instance', 'value', None, F"
            "alse, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (Fa"
            "lse,)))"
        ),
    ),
    cls_names=(
        ('omdev.specs.irc.protocol.nuh', 'Nuh'),
    ),
)
def _process_dataclass__7c24abce9d19666ef75be7ea938bb52f4dc73fb3():
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
