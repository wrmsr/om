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


IMPLEMENTATION_KEY = 'ec0d825a77daf2010440f2135dbf8d063599428f1d09d40e22d60773f9be3250'


@_register(
    installer_sha1='a5e8f063c09b5fb8f17bb1974c1df163b510df3d',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('source', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('target', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False), (('source_max', True, True, None, True, True, False, None), 'instance', 'missi"
            "ng', None, False, False, False), (('target_max', True, True, None, True, True, False, None), 'instance', '"
            "missing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()"
            "), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.text.diffs.styled.layouts', 'DiffFileLines'),
    ),
)
def _process_dataclass__a5e8f063c09b5fb8f17bb1974c1df163b510df3d():
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
                source=self.source,
                target=self.target,
                source_max=self.source_max,
                target_max=self.target_max,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.source == other.source and
                self.target == other.target and
                self.source_max == other.source_max and
                self.target_max == other.target_max
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'source',
            'target',
            'source_max',
            'target_max',
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
                self.target,
                self.source_max,
                self.target_max,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            source: __dataclass__init__fields__0__annotation,
            target: __dataclass__init__fields__1__annotation,
            source_max: __dataclass__init__fields__2__annotation,
            target_max: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'source', source)
            __dataclass__object_setattr(self, 'target', target)
            __dataclass__object_setattr(self, 'source_max', source_max)
            __dataclass__object_setattr(self, 'target_max', target_max)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"source={self.source!r}")
            parts.append(f"target={self.target!r}")
            parts.append(f"source_max={self.source_max!r}")
            parts.append(f"target_max={self.target_max!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='da4547812146128c58f19616f3c5c1235d6db7a3',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('max_lines', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('max_bytes', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, True, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.text.diffs.styled.options', 'DiffContextLimits'),
    ),
)
def _process_dataclass__da4547812146128c58f19616f3c5c1235d6db7a3():
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
                max_lines=self.max_lines,
                max_bytes=self.max_bytes,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.max_lines == other.max_lines and
                self.max_bytes == other.max_bytes
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'max_lines',
            'max_bytes',
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
                self.max_lines,
                self.max_bytes,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            max_lines: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            max_bytes: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'max_lines', max_lines)
            __dataclass__object_setattr(self, 'max_bytes', max_bytes)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"max_lines={self.max_lines!r}")
            parts.append(f"max_bytes={self.max_bytes!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='6b1786cc711d9af712331d3be94b3a4cf7f5d346',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('width', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('tab_size', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('syntax_highlighting', True, True, None, True, False, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('layout', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('auto_split_width', True, True, None, True, True, False, None), "
            "'instance', 'value', None, False, False, False), (('context_limits', True, True, None, True, True, False, "
            "None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,),"
            " (False, True, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.text.diffs.styled.options', 'DiffStyledDocOptions'),
    ),
)
def _process_dataclass__6b1786cc711d9af712331d3be94b3a4cf7f5d346():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                width=self.width,
                tab_size=self.tab_size,
                syntax_highlighting=self.syntax_highlighting,
                layout=self.layout,
                auto_split_width=self.auto_split_width,
                context_limits=self.context_limits,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.width == other.width and
                self.tab_size == other.tab_size and
                self.syntax_highlighting == other.syntax_highlighting and
                self.layout == other.layout and
                self.auto_split_width == other.auto_split_width and
                self.context_limits == other.context_limits
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'width',
            'tab_size',
            'syntax_highlighting',
            'layout',
            'auto_split_width',
            'context_limits',
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
                self.width,
                self.tab_size,
                self.syntax_highlighting,
                self.layout,
                self.auto_split_width,
                self.context_limits,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            width: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            tab_size: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            syntax_highlighting: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            *,
            layout: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            auto_split_width: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            context_limits: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'width', width)
            __dataclass__object_setattr(self, 'tab_size', tab_size)
            __dataclass__object_setattr(self, 'syntax_highlighting', syntax_highlighting)
            __dataclass__object_setattr(self, 'layout', layout)
            __dataclass__object_setattr(self, 'auto_split_width', auto_split_width)
            __dataclass__object_setattr(self, 'context_limits', context_limits)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"width={self.width!r}")
            parts.append(f"tab_size={self.tab_size!r}")
            parts.append(f"syntax_highlighting={self.syntax_highlighting!r}")
            parts.append(f"layout={self.layout!r}")
            parts.append(f"auto_split_width={self.auto_split_width!r}")
            parts.append(f"context_limits={self.context_limits!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='74a97184cca4f4f6ea28ca57cc05bd847cfa7b00',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('source', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('target', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), "
            "(False,)))"
        ),
    ),
    cls_names=(
        ('omcore.text.diffs.styled.sources', 'DiffFileTexts'),
    ),
)
def _process_dataclass__74a97184cca4f4f6ea28ca57cc05bd847cfa7b00():
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
                source=self.source,
                target=self.target,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.source == other.source and
                self.target == other.target
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'source',
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
                self.source,
                self.target,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            source: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            target: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'source', source)
            __dataclass__object_setattr(self, 'target', target)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"source={self.source!r}")
            parts.append(f"target={self.target!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='5a3c9660bf07790cde2668ca5e63a9cee76247a1',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('source', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('target', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('intraline', True, True, None, True, False, False, None), 'instance', 'va"
            "lue', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ("
            "(),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.text.diffs.styled.split', '_AlignedRow'),
    ),
)
def _process_dataclass__5a3c9660bf07790cde2668ca5e63a9cee76247a1():
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
                source=self.source,
                target=self.target,
                intraline=self.intraline,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.source == other.source and
                self.target == other.target and
                self.intraline == other.intraline
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'source',
            'target',
            'intraline',
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
                self.target,
                self.intraline,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            source: __dataclass__init__fields__0__annotation,
            target: __dataclass__init__fields__1__annotation,
            intraline: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'source', source)
            __dataclass__object_setattr(self, 'target', target)
            __dataclass__object_setattr(self, 'intraline', intraline)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"source={self.source!r}")
            parts.append(f"target={self.target!r}")
            parts.append(f"intraline={self.intraline!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='82f6ffeb2d88cf99a0555ac2f435011a8cd69cff',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('number', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('text', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('changed', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (()"
            ",), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.text.diffs.styled.split', '_SideLine'),
    ),
)
def _process_dataclass__82f6ffeb2d88cf99a0555ac2f435011a8cd69cff():
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
                number=self.number,
                text=self.text,
                changed=self.changed,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.number == other.number and
                self.text == other.text and
                self.changed == other.changed
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'number',
            'text',
            'changed',
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
                self.number,
                self.text,
                self.changed,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            number: __dataclass__init__fields__0__annotation,
            text: __dataclass__init__fields__1__annotation,
            changed: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'number', number)
            __dataclass__object_setattr(self, 'text', text)
            __dataclass__object_setattr(self, 'changed', changed)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"number={self.number!r}")
            parts.append(f"text={self.text!r}")
            parts.append(f"changed={self.changed!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
