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


IMPLEMENTATION_KEY = '9435723149cde3211bedb6c2958a590435b02c76608192a2caf2a7c46f2eb4b2'


@_register(
    installer_sha1='8825d38c1e7b9232d0d33c9a194d6de70b4fd1cb',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('yield_object_lists', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()"
            "), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.formats.json.stream.building', 'JsonValueBuilder.Config'),
    ),
)
def _process_dataclass__8825d38c1e7b9232d0d33c9a194d6de70b4fd1cb():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default = __dataclass__spec.fields[0].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                yield_object_lists=self.yield_object_lists,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.yield_object_lists == other.yield_object_lists
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'yield_object_lists',
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
                self.yield_object_lists,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            yield_object_lists: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'yield_object_lists', yield_object_lists)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"yield_object_lists={self.yield_object_lists!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='cb3a01fe9490f5d99cc4225caa616a3b33788cc1',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('message', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('pos', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.formats.json.stream.lexing', 'JsonStreamLexError'),
    ),
)
def _process_dataclass__cb3a01fe9490f5d99cc4225caa616a3b33788cc1():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                message=self.message,
                pos=self.pos,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.message == other.message and
                self.pos == other.pos
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            message: __dataclass__init__fields__0__annotation,
            pos: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            self.message = message
            self.pos = pos

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"message={self.message!r}")
            parts.append(f"pos={self.pos!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='85ce61e2676d7f450fb758cb0dc057fd00d75fb9',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('include_raw', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('allow_extended_space', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('include_space', True, True, None, True, True, False, None), "
            "'instance', 'value', None, False, False, False), (('allow_comments', True, True, None, True, True, False, "
            "None), 'instance', 'value', None, False, False, False), (('include_comments', True, True, None, True, True"
            ", False, None), 'instance', 'value', None, False, False, False), (('allow_single_quotes', True, True, None"
            ", True, True, False, None), 'instance', 'value', None, False, False, False), (('string_literal_parser', Tr"
            "ue, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('allow_extend"
            "ed_number_literals', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, "
            "False), (('number_literal_parser', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False), (('allow_extended_idents', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()),"
            " ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.formats.json.stream.lexing', 'JsonStreamLexer.Config'),
    ),
)
def _process_dataclass__85ce61e2676d7f450fb758cb0dc057fd00d75fb9():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                include_raw=self.include_raw,
                allow_extended_space=self.allow_extended_space,
                include_space=self.include_space,
                allow_comments=self.allow_comments,
                include_comments=self.include_comments,
                allow_single_quotes=self.allow_single_quotes,
                string_literal_parser=self.string_literal_parser,
                allow_extended_number_literals=self.allow_extended_number_literals,
                number_literal_parser=self.number_literal_parser,
                allow_extended_idents=self.allow_extended_idents,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.include_raw == other.include_raw and
                self.allow_extended_space == other.allow_extended_space and
                self.include_space == other.include_space and
                self.allow_comments == other.allow_comments and
                self.include_comments == other.include_comments and
                self.allow_single_quotes == other.allow_single_quotes and
                self.string_literal_parser == other.string_literal_parser and
                self.allow_extended_number_literals == other.allow_extended_number_literals and
                self.number_literal_parser == other.number_literal_parser and
                self.allow_extended_idents == other.allow_extended_idents
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'include_raw',
            'allow_extended_space',
            'include_space',
            'allow_comments',
            'include_comments',
            'allow_single_quotes',
            'string_literal_parser',
            'allow_extended_number_literals',
            'number_literal_parser',
            'allow_extended_idents',
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
                self.include_raw,
                self.allow_extended_space,
                self.include_space,
                self.allow_comments,
                self.include_comments,
                self.allow_single_quotes,
                self.string_literal_parser,
                self.allow_extended_number_literals,
                self.number_literal_parser,
                self.allow_extended_idents,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            include_raw: __dataclass__init__fields__00__annotation = __dataclass__init__fields__00__default,
            allow_extended_space: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            include_space: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            allow_comments: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            include_comments: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            allow_single_quotes: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            string_literal_parser: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            allow_extended_number_literals: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            number_literal_parser: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            allow_extended_idents: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'include_raw', include_raw)
            __dataclass__object_setattr(self, 'allow_extended_space', allow_extended_space)
            __dataclass__object_setattr(self, 'include_space', include_space)
            __dataclass__object_setattr(self, 'allow_comments', allow_comments)
            __dataclass__object_setattr(self, 'include_comments', include_comments)
            __dataclass__object_setattr(self, 'allow_single_quotes', allow_single_quotes)
            __dataclass__object_setattr(self, 'string_literal_parser', string_literal_parser)
            __dataclass__object_setattr(self, 'allow_extended_number_literals', allow_extended_number_literals)
            __dataclass__object_setattr(self, 'number_literal_parser', number_literal_parser)
            __dataclass__object_setattr(self, 'allow_extended_idents', allow_extended_idents)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"include_raw={self.include_raw!r}")
            parts.append(f"allow_extended_space={self.allow_extended_space!r}")
            parts.append(f"include_space={self.include_space!r}")
            parts.append(f"allow_comments={self.allow_comments!r}")
            parts.append(f"include_comments={self.include_comments!r}")
            parts.append(f"allow_single_quotes={self.allow_single_quotes!r}")
            parts.append(f"string_literal_parser={self.string_literal_parser!r}")
            parts.append(f"allow_extended_number_literals={self.allow_extended_number_literals!r}")
            parts.append(f"number_literal_parser={self.number_literal_parser!r}")
            parts.append(f"allow_extended_idents={self.allow_extended_idents!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='92bf50d48942893ede3d5020c33ad83774c16997',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('message', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('pos', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.formats.json.stream.parsing', 'JsonStreamParseError'),
    ),
)
def _process_dataclass__92bf50d48942893ede3d5020c33ad83774c16997():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                message=self.message,
                pos=self.pos,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.message == other.message and
                self.pos == other.pos
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            message: __dataclass__init__fields__0__annotation,
            pos: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            self.message = message
            self.pos = pos

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"message={self.message!r}")
            parts.append(f"pos={self.pos!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='858476e8034f6c195b071f626f2c4ac91f809acb',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('allow_trailing_commas', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('allow_ident_values', True, True, None, True, True, False, None)"
            ", 'instance', 'value', None, False, False, False), (('allow_extended_idents', True, True, None, True, True"
            ", False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), "
            "(False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.formats.json.stream.parsing', 'JsonStreamParser.Config'),
    ),
)
def _process_dataclass__858476e8034f6c195b071f626f2c4ac91f809acb():
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
                allow_trailing_commas=self.allow_trailing_commas,
                allow_ident_values=self.allow_ident_values,
                allow_extended_idents=self.allow_extended_idents,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.allow_trailing_commas == other.allow_trailing_commas and
                self.allow_ident_values == other.allow_ident_values and
                self.allow_extended_idents == other.allow_extended_idents
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'allow_trailing_commas',
            'allow_ident_values',
            'allow_extended_idents',
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
                self.allow_trailing_commas,
                self.allow_ident_values,
                self.allow_extended_idents,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            allow_trailing_commas: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            allow_ident_values: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            allow_extended_idents: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'allow_trailing_commas', allow_trailing_commas)
            __dataclass__object_setattr(self, 'allow_ident_values', allow_ident_values)
            __dataclass__object_setattr(self, 'allow_extended_idents', allow_extended_idents)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"allow_trailing_commas={self.allow_trailing_commas!r}")
            parts.append(f"allow_ident_values={self.allow_ident_values!r}")
            parts.append(f"allow_extended_idents={self.allow_extended_idents!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='fc85d9ec2f6ac4a083467799b594eb85955cd9e7',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('indent', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('separators', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('sort_keys', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('ensure_ascii', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('style', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('delimiter', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ("
            "(),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.formats.json.stream.rendering', 'StreamJsonRenderer.Config'),
    ),
)
def _process_dataclass__fc85d9ec2f6ac4a083467799b594eb85955cd9e7():
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
                indent=self.indent,
                separators=self.separators,
                sort_keys=self.sort_keys,
                ensure_ascii=self.ensure_ascii,
                style=self.style,
                delimiter=self.delimiter,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.indent == other.indent and
                self.separators == other.separators and
                self.sort_keys == other.sort_keys and
                self.ensure_ascii == other.ensure_ascii and
                self.style == other.style and
                self.delimiter == other.delimiter
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'indent',
            'separators',
            'sort_keys',
            'ensure_ascii',
            'style',
            'delimiter',
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
                self.indent,
                self.separators,
                self.sort_keys,
                self.ensure_ascii,
                self.style,
                self.delimiter,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            indent: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            separators: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            sort_keys: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            ensure_ascii: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            style: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            delimiter: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'indent', indent)
            __dataclass__object_setattr(self, 'separators', separators)
            __dataclass__object_setattr(self, 'sort_keys', sort_keys)
            __dataclass__object_setattr(self, 'ensure_ascii', ensure_ascii)
            __dataclass__object_setattr(self, 'style', style)
            __dataclass__object_setattr(self, 'delimiter', delimiter)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.indent)) is not None:
                parts.append(f"indent={s}")
            if (s := __dataclass__repr__default_fn(self.separators)) is not None:
                parts.append(f"separators={s}")
            if (s := __dataclass__repr__default_fn(self.sort_keys)) is not None:
                parts.append(f"sort_keys={s}")
            if (s := __dataclass__repr__default_fn(self.ensure_ascii)) is not None:
                parts.append(f"ensure_ascii={s}")
            if (s := __dataclass__repr__default_fn(self.style)) is not None:
                parts.append(f"style={s}")
            if (s := __dataclass__repr__default_fn(self.delimiter)) is not None:
                parts.append(f"delimiter={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
