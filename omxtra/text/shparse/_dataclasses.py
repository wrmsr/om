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
    installer_sha1='3a67adf2531fe1e9306f34279d749ebfc2bd2b08',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('s', True, True, None, True, False, False, None), 'instance', 'missing', Non"
            "e, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.errors', 'GenericError'),
    ),
)
def _process_dataclass__3a67adf2531fe1e9306f34279d749ebfc2bd2b08():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                s=self.s,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.s == other.s
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            s: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            self.s = s

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
    installer_sha1='a261af455ddffde2c89930232b9201763e49722d',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('left', True, True, None, True, False, False, None), 'instance', 'factory', "
            "None, False, False, False), (('right', True, True, None, True, False, False, None), 'instance', 'factory',"
            " None, False, False, False), (('unsigned', True, True, None, True, False, False, None), 'instance', 'value"
            "', None, False, False, False), (('x', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'ArithmCmd'),
    ),
)
def _process_dataclass__a261af455ddffde2c89930232b9201763e49722d():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                left=self.left,
                right=self.right,
                unsigned=self.unsigned,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.left == other.left and
                self.right == other.right and
                self.unsigned == other.unsigned and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            left: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            right: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            unsigned: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            x: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            if left is __dataclass__HAS_DEFAULT_FACTORY:
                left = __dataclass__init__fields__0__default_factory()
            if right is __dataclass__HAS_DEFAULT_FACTORY:
                right = __dataclass__init__fields__1__default_factory()
            self.left = left
            self.right = right
            self.unsigned = unsigned
            self.x = x

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"left={self.left!r}")
            parts.append(f"right={self.right!r}")
            parts.append(f"unsigned={self.unsigned!r}")
            parts.append(f"x={self.x!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='932e07d884939a4fb129fa6a755baab2a2d256e9',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('left', True, True, None, True, False, False, None), 'instance', 'factory', "
            "None, False, False, False), (('right', True, True, None, True, False, False, None), 'instance', 'factory',"
            " None, False, False, False), (('bracket', True, True, None, True, False, False, None), 'instance', 'value'"
            ", None, False, False, False), (('unsigned', True, True, None, True, False, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('x', True, True, None, True, False, False, None), 'instance', 'value', N"
            "one, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'ArithmExp'),
    ),
)
def _process_dataclass__932e07d884939a4fb129fa6a755baab2a2d256e9():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                left=self.left,
                right=self.right,
                bracket=self.bracket,
                unsigned=self.unsigned,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.left == other.left and
                self.right == other.right and
                self.bracket == other.bracket and
                self.unsigned == other.unsigned and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            left: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            right: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            bracket: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            unsigned: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            x: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            if left is __dataclass__HAS_DEFAULT_FACTORY:
                left = __dataclass__init__fields__0__default_factory()
            if right is __dataclass__HAS_DEFAULT_FACTORY:
                right = __dataclass__init__fields__1__default_factory()
            self.left = left
            self.right = right
            self.bracket = bracket
            self.unsigned = unsigned
            self.x = x

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"left={self.left!r}")
            parts.append(f"right={self.right!r}")
            parts.append(f"bracket={self.bracket!r}")
            parts.append(f"unsigned={self.unsigned!r}")
            parts.append(f"x={self.x!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d201643447ff40013c7b75e8d4ff39d2dc23b076',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), (), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'ArithmExpr'),
        ('omxtra.text.shparse.nodes', 'Command'),
        ('omxtra.text.shparse.nodes', 'Loop'),
        ('omxtra.text.shparse.nodes', 'Node'),
        ('omxtra.text.shparse.nodes', 'TestExpr'),
        ('omxtra.text.shparse.nodes', 'WordPart'),
    ),
)
def _process_dataclass__d201643447ff40013c7b75e8d4ff39d2dc23b076():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
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

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

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
    installer_sha1='aae9854f7387036b544d816946a1578c8daf5b1c',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('index', True, True, None, True, False, False, None), 'instance', 'value', N"
            "one, False, False, False), (('value', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('comments', True, True, None, True, False, False, None), 'instance', 'factory'"
            ", None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'ArrayElem'),
    ),
)
def _process_dataclass__aae9854f7387036b544d816946a1578c8daf5b1c():
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
        __dataclass__init__fields__2__default_factory = __dataclass__spec.fields[2].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                index=self.index,
                value=self.value,
                comments=self.comments,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.index == other.index and
                self.value == other.value and
                self.comments == other.comments
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            index: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            value: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            comments: __dataclass__init__fields__2__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if comments is __dataclass__HAS_DEFAULT_FACTORY:
                comments = __dataclass__init__fields__2__default_factory()
            self.index = index
            self.value = value
            self.comments = comments

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"index={self.index!r}")
            parts.append(f"value={self.value!r}")
            parts.append(f"comments={self.comments!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='3e82d0c8777c0a66349a4448ca29a82f5929e9df',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('lparen', True, True, None, True, False, False, None), 'instance', 'factory'"
            ", None, False, False, False), (('rparen', True, True, None, True, False, False, None), 'instance', 'factor"
            "y', None, False, False, False), (('elems', True, True, None, True, False, False, None), 'instance', 'facto"
            "ry', None, False, False, False), (('last', True, True, None, True, False, False, None), 'instance', 'facto"
            "ry', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (("
            "),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'ArrayExpr'),
    ),
)
def _process_dataclass__3e82d0c8777c0a66349a4448ca29a82f5929e9df():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default_factory = __dataclass__spec.fields[2].default.must().fn
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default_factory = __dataclass__spec.fields[3].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                lparen=self.lparen,
                rparen=self.rparen,
                elems=self.elems,
                last=self.last,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.lparen == other.lparen and
                self.rparen == other.rparen and
                self.elems == other.elems and
                self.last == other.last
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            lparen: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            rparen: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            elems: __dataclass__init__fields__2__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            last: __dataclass__init__fields__3__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if lparen is __dataclass__HAS_DEFAULT_FACTORY:
                lparen = __dataclass__init__fields__0__default_factory()
            if rparen is __dataclass__HAS_DEFAULT_FACTORY:
                rparen = __dataclass__init__fields__1__default_factory()
            if elems is __dataclass__HAS_DEFAULT_FACTORY:
                elems = __dataclass__init__fields__2__default_factory()
            if last is __dataclass__HAS_DEFAULT_FACTORY:
                last = __dataclass__init__fields__3__default_factory()
            self.lparen = lparen
            self.rparen = rparen
            self.elems = elems
            self.last = last

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"lparen={self.lparen!r}")
            parts.append(f"rparen={self.rparen!r}")
            parts.append(f"elems={self.elems!r}")
            parts.append(f"last={self.last!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='7313cf512f2a14142ba47ec1a2af9c0eab7c6ed0',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('append', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('naked', True, True, None, True, False, False, None), 'instance', 'value', N"
            "one, False, False, False), (('name', True, True, None, True, False, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('index', True, True, None, True, False, False, None), 'instance', 'value', None"
            ", False, False, False), (('value', True, True, None, True, False, False, None), 'instance', 'value', None,"
            " False, False, False), (('array', True, True, None, True, False, False, None), 'instance', 'value', None, "
            "False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (F"
            "alse,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'Assign'),
    ),
)
def _process_dataclass__7313cf512f2a14142ba47ec1a2af9c0eab7c6ed0():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                append=self.append,
                naked=self.naked,
                name=self.name,
                index=self.index,
                value=self.value,
                array=self.array,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.append == other.append and
                self.naked == other.naked and
                self.name == other.name and
                self.index == other.index and
                self.value == other.value and
                self.array == other.array
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            append: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            naked: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            name: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            index: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            value: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            array: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            self.append = append
            self.naked = naked
            self.name = name
            self.index = index
            self.value = value
            self.array = array

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"append={self.append!r}")
            parts.append(f"naked={self.naked!r}")
            parts.append(f"name={self.name!r}")
            parts.append(f"index={self.index!r}")
            parts.append(f"value={self.value!r}")
            parts.append(f"array={self.array!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='dd277911e2fcabc73f099d40ed9e303687e3cb10',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('op_pos', True, True, None, True, False, False, None), 'instance', 'factory'"
            ", None, False, False, False), (('op', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('x', True, True, None, True, False, False, None), 'instance', 'value', None, F"
            "alse, False, False), (('y', True, True, None, True, False, False, None), 'instance', 'value', None, False,"
            " False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)"
            "))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'BinaryArithm'),
        ('omxtra.text.shparse.nodes', 'BinaryCmd'),
        ('omxtra.text.shparse.nodes', 'BinaryTest'),
    ),
)
def _process_dataclass__dd277911e2fcabc73f099d40ed9e303687e3cb10():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                op_pos=self.op_pos,
                op=self.op,
                x=self.x,
                y=self.y,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.op_pos == other.op_pos and
                self.op == other.op and
                self.x == other.x and
                self.y == other.y
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            op_pos: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            op: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            x: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            y: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            if op_pos is __dataclass__HAS_DEFAULT_FACTORY:
                op_pos = __dataclass__init__fields__0__default_factory()
            self.op_pos = op_pos
            self.op = op
            self.x = x
            self.y = y

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"op_pos={self.op_pos!r}")
            parts.append(f"op={self.op!r}")
            parts.append(f"x={self.x!r}")
            parts.append(f"y={self.y!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='43e72fe944f777e90f2464a71cc8d1761e5eab11',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('lbrace', True, True, None, True, False, False, None), 'instance', 'factory'"
            ", None, False, False, False), (('rbrace', True, True, None, True, False, False, None), 'instance', 'factor"
            "y', None, False, False, False), (('stmts', True, True, None, True, False, False, None), 'instance', 'facto"
            "ry', None, False, False, False), (('last', True, True, None, True, False, False, None), 'instance', 'facto"
            "ry', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (("
            "),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'Block'),
    ),
)
def _process_dataclass__43e72fe944f777e90f2464a71cc8d1761e5eab11():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default_factory = __dataclass__spec.fields[2].default.must().fn
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default_factory = __dataclass__spec.fields[3].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                lbrace=self.lbrace,
                rbrace=self.rbrace,
                stmts=self.stmts,
                last=self.last,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.lbrace == other.lbrace and
                self.rbrace == other.rbrace and
                self.stmts == other.stmts and
                self.last == other.last
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            lbrace: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            rbrace: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            stmts: __dataclass__init__fields__2__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            last: __dataclass__init__fields__3__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if lbrace is __dataclass__HAS_DEFAULT_FACTORY:
                lbrace = __dataclass__init__fields__0__default_factory()
            if rbrace is __dataclass__HAS_DEFAULT_FACTORY:
                rbrace = __dataclass__init__fields__1__default_factory()
            if stmts is __dataclass__HAS_DEFAULT_FACTORY:
                stmts = __dataclass__init__fields__2__default_factory()
            if last is __dataclass__HAS_DEFAULT_FACTORY:
                last = __dataclass__init__fields__3__default_factory()
            self.lbrace = lbrace
            self.rbrace = rbrace
            self.stmts = stmts
            self.last = last

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"lbrace={self.lbrace!r}")
            parts.append(f"rbrace={self.rbrace!r}")
            parts.append(f"stmts={self.stmts!r}")
            parts.append(f"last={self.last!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='427d1000e1ed62cbe0ec4cea6ae1d1081121f855',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('sequence', True, True, None, True, False, False, None), 'instance', 'value'"
            ", None, False, False, False), (('elems', True, True, None, True, False, False, None), 'instance', 'factory"
            "', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'BraceExp'),
    ),
)
def _process_dataclass__427d1000e1ed62cbe0ec4cea6ae1d1081121f855():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default = __dataclass__spec.fields[0].default.must()
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                sequence=self.sequence,
                elems=self.elems,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.sequence == other.sequence and
                self.elems == other.elems
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            sequence: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            elems: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if elems is __dataclass__HAS_DEFAULT_FACTORY:
                elems = __dataclass__init__fields__1__default_factory()
            self.sequence = sequence
            self.elems = elems

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"sequence={self.sequence!r}")
            parts.append(f"elems={self.elems!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='14b2c3f481a82be1485432e6726696d1cd8f9224',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('lparen', True, True, None, True, False, False, None), 'instance', 'factory'"
            ", None, False, False, False), (('rparen', True, True, None, True, False, False, None), 'instance', 'factor"
            "y', None, False, False, False), (('init', True, True, None, True, False, False, None), 'instance', 'value'"
            ", None, False, False, False), (('cond', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('post', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'CStyleLoop'),
    ),
)
def _process_dataclass__14b2c3f481a82be1485432e6726696d1cd8f9224():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                lparen=self.lparen,
                rparen=self.rparen,
                init=self.init,
                cond=self.cond,
                post=self.post,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.lparen == other.lparen and
                self.rparen == other.rparen and
                self.init == other.init and
                self.cond == other.cond and
                self.post == other.post
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            lparen: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            rparen: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            init: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            cond: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            post: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            if lparen is __dataclass__HAS_DEFAULT_FACTORY:
                lparen = __dataclass__init__fields__0__default_factory()
            if rparen is __dataclass__HAS_DEFAULT_FACTORY:
                rparen = __dataclass__init__fields__1__default_factory()
            self.lparen = lparen
            self.rparen = rparen
            self.init = init
            self.cond = cond
            self.post = post

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"lparen={self.lparen!r}")
            parts.append(f"rparen={self.rparen!r}")
            parts.append(f"init={self.init!r}")
            parts.append(f"cond={self.cond!r}")
            parts.append(f"post={self.post!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='f33cc651957cfc20056d96f4875090ec0b6e736a',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('assigns', True, True, None, True, False, False, None), 'instance', 'factory"
            "', None, False, False, False), (('args', True, True, None, True, False, False, None), 'instance', 'factory"
            "', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'CallExpr'),
    ),
)
def _process_dataclass__f33cc651957cfc20056d96f4875090ec0b6e736a():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                assigns=self.assigns,
                args=self.args,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.assigns == other.assigns and
                self.args == other.args
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            assigns: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            args: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if assigns is __dataclass__HAS_DEFAULT_FACTORY:
                assigns = __dataclass__init__fields__0__default_factory()
            if args is __dataclass__HAS_DEFAULT_FACTORY:
                args = __dataclass__init__fields__1__default_factory()
            self.assigns = assigns
            self.args = args

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"assigns={self.assigns!r}")
            parts.append(f"args={self.args!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='198ccc3f88745c63101cee5c32461599b30ea136',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('case', True, True, None, True, False, False, None), 'instance', 'factory', "
            "None, False, False, False), (('in_', True, True, None, True, False, False, None), 'instance', 'factory', N"
            "one, False, False, False), (('esac', True, True, None, True, False, False, None), 'instance', 'factory', N"
            "one, False, False, False), (('braces', True, True, None, True, False, False, None), 'instance', 'value', N"
            "one, False, False, False), (('word', True, True, None, True, False, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('items', True, True, None, True, False, False, None), 'instance', 'factory', No"
            "ne, False, False, False), (('last', True, True, None, True, False, False, None), 'instance', 'factory', No"
            "ne, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'CaseClause'),
    ),
)
def _process_dataclass__198ccc3f88745c63101cee5c32461599b30ea136():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default_factory = __dataclass__spec.fields[2].default.must().fn
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__default_factory = __dataclass__spec.fields[5].default.must().fn
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__6__default_factory = __dataclass__spec.fields[6].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                case=self.case,
                in_=self.in_,
                esac=self.esac,
                braces=self.braces,
                word=self.word,
                items=self.items,
                last=self.last,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.case == other.case and
                self.in_ == other.in_ and
                self.esac == other.esac and
                self.braces == other.braces and
                self.word == other.word and
                self.items == other.items and
                self.last == other.last
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            case: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            in_: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            esac: __dataclass__init__fields__2__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            braces: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            word: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            items: __dataclass__init__fields__5__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            last: __dataclass__init__fields__6__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if case is __dataclass__HAS_DEFAULT_FACTORY:
                case = __dataclass__init__fields__0__default_factory()
            if in_ is __dataclass__HAS_DEFAULT_FACTORY:
                in_ = __dataclass__init__fields__1__default_factory()
            if esac is __dataclass__HAS_DEFAULT_FACTORY:
                esac = __dataclass__init__fields__2__default_factory()
            if items is __dataclass__HAS_DEFAULT_FACTORY:
                items = __dataclass__init__fields__5__default_factory()
            if last is __dataclass__HAS_DEFAULT_FACTORY:
                last = __dataclass__init__fields__6__default_factory()
            self.case = case
            self.in_ = in_
            self.esac = esac
            self.braces = braces
            self.word = word
            self.items = items
            self.last = last

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"case={self.case!r}")
            parts.append(f"in_={self.in_!r}")
            parts.append(f"esac={self.esac!r}")
            parts.append(f"braces={self.braces!r}")
            parts.append(f"word={self.word!r}")
            parts.append(f"items={self.items!r}")
            parts.append(f"last={self.last!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='a8252bee9b2cff74b0bbd238233d1585aaee1d90',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('op', True, True, None, True, False, False, None), 'instance', 'value', None"
            ", False, False, False), (('op_pos', True, True, None, True, False, False, None), 'instance', 'factory', No"
            "ne, False, False, False), (('comments', True, True, None, True, False, False, None), 'instance', 'factory'"
            ", None, False, False, False), (('patterns', True, True, None, True, False, False, None), 'instance', 'fact"
            "ory', None, False, False, False), (('stmts', True, True, None, True, False, False, None), 'instance', 'fac"
            "tory', None, False, False, False), (('last', True, True, None, True, False, False, None), 'instance', 'fac"
            "tory', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), "
            "((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'CaseItem'),
    ),
)
def _process_dataclass__a8252bee9b2cff74b0bbd238233d1585aaee1d90():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default = __dataclass__spec.fields[0].default.must()
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default_factory = __dataclass__spec.fields[2].default.must().fn
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default_factory = __dataclass__spec.fields[3].default.must().fn
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default_factory = __dataclass__spec.fields[4].default.must().fn
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__default_factory = __dataclass__spec.fields[5].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                op=self.op,
                op_pos=self.op_pos,
                comments=self.comments,
                patterns=self.patterns,
                stmts=self.stmts,
                last=self.last,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.op == other.op and
                self.op_pos == other.op_pos and
                self.comments == other.comments and
                self.patterns == other.patterns and
                self.stmts == other.stmts and
                self.last == other.last
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            op: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            op_pos: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            comments: __dataclass__init__fields__2__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            patterns: __dataclass__init__fields__3__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            stmts: __dataclass__init__fields__4__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            last: __dataclass__init__fields__5__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if op_pos is __dataclass__HAS_DEFAULT_FACTORY:
                op_pos = __dataclass__init__fields__1__default_factory()
            if comments is __dataclass__HAS_DEFAULT_FACTORY:
                comments = __dataclass__init__fields__2__default_factory()
            if patterns is __dataclass__HAS_DEFAULT_FACTORY:
                patterns = __dataclass__init__fields__3__default_factory()
            if stmts is __dataclass__HAS_DEFAULT_FACTORY:
                stmts = __dataclass__init__fields__4__default_factory()
            if last is __dataclass__HAS_DEFAULT_FACTORY:
                last = __dataclass__init__fields__5__default_factory()
            self.op = op
            self.op_pos = op_pos
            self.comments = comments
            self.patterns = patterns
            self.stmts = stmts
            self.last = last

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"op={self.op!r}")
            parts.append(f"op_pos={self.op_pos!r}")
            parts.append(f"comments={self.comments!r}")
            parts.append(f"patterns={self.patterns!r}")
            parts.append(f"stmts={self.stmts!r}")
            parts.append(f"last={self.last!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='a4d51bf25b346d2cbe11b6106e98656fea9377ff',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('left', True, True, None, True, False, False, None), 'instance', 'factory', "
            "None, False, False, False), (('right', True, True, None, True, False, False, None), 'instance', 'factory',"
            " None, False, False, False), (('stmts', True, True, None, True, False, False, None), 'instance', 'factory'"
            ", None, False, False, False), (('last', True, True, None, True, False, False, None), 'instance', 'factory'"
            ", None, False, False, False), (('backquotes', True, True, None, True, False, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('temp_file', True, True, None, True, False, False, None), 'instance', "
            "'value', None, False, False, False), (('reply_var', True, True, None, True, False, False, None), 'instance"
            "', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, "
            "()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'CmdSubst'),
    ),
)
def _process_dataclass__a4d51bf25b346d2cbe11b6106e98656fea9377ff():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default_factory = __dataclass__spec.fields[2].default.must().fn
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default_factory = __dataclass__spec.fields[3].default.must().fn
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__default = __dataclass__spec.fields[5].default.must()
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__6__default = __dataclass__spec.fields[6].default.must()
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                left=self.left,
                right=self.right,
                stmts=self.stmts,
                last=self.last,
                backquotes=self.backquotes,
                temp_file=self.temp_file,
                reply_var=self.reply_var,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.left == other.left and
                self.right == other.right and
                self.stmts == other.stmts and
                self.last == other.last and
                self.backquotes == other.backquotes and
                self.temp_file == other.temp_file and
                self.reply_var == other.reply_var
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            left: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            right: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            stmts: __dataclass__init__fields__2__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            last: __dataclass__init__fields__3__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            backquotes: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            temp_file: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            reply_var: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
        ) -> __dataclass__None:
            if left is __dataclass__HAS_DEFAULT_FACTORY:
                left = __dataclass__init__fields__0__default_factory()
            if right is __dataclass__HAS_DEFAULT_FACTORY:
                right = __dataclass__init__fields__1__default_factory()
            if stmts is __dataclass__HAS_DEFAULT_FACTORY:
                stmts = __dataclass__init__fields__2__default_factory()
            if last is __dataclass__HAS_DEFAULT_FACTORY:
                last = __dataclass__init__fields__3__default_factory()
            self.left = left
            self.right = right
            self.stmts = stmts
            self.last = last
            self.backquotes = backquotes
            self.temp_file = temp_file
            self.reply_var = reply_var

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"left={self.left!r}")
            parts.append(f"right={self.right!r}")
            parts.append(f"stmts={self.stmts!r}")
            parts.append(f"last={self.last!r}")
            parts.append(f"backquotes={self.backquotes!r}")
            parts.append(f"temp_file={self.temp_file!r}")
            parts.append(f"reply_var={self.reply_var!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='385a38d6b95a6ba96c0f90e063fb53f5a7bb5de5',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('hash', True, True, None, True, False, False, None), 'instance', 'factory', "
            "None, False, False, False), (('text', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'Comment'),
    ),
)
def _process_dataclass__385a38d6b95a6ba96c0f90e063fb53f5a7bb5de5():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                hash=self.hash,
                text=self.text,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.hash == other.hash and
                self.text == other.text
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            hash: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            text: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            if hash is __dataclass__HAS_DEFAULT_FACTORY:
                hash = __dataclass__init__fields__0__default_factory()
            self.hash = hash
            self.text = text

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"hash={self.hash!r}")
            parts.append(f"text={self.text!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='48922b1a8626c47ed9b7ece728274b19a743ddb4',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('coproc', True, True, None, True, False, False, None), 'instance', 'factory'"
            ", None, False, False, False), (('name', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('stmt', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'CoprocClause'),
    ),
)
def _process_dataclass__48922b1a8626c47ed9b7ece728274b19a743ddb4():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                coproc=self.coproc,
                name=self.name,
                stmt=self.stmt,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.coproc == other.coproc and
                self.name == other.name and
                self.stmt == other.stmt
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            coproc: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            name: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            stmt: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            if coproc is __dataclass__HAS_DEFAULT_FACTORY:
                coproc = __dataclass__init__fields__0__default_factory()
            self.coproc = coproc
            self.name = name
            self.stmt = stmt

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"coproc={self.coproc!r}")
            parts.append(f"name={self.name!r}")
            parts.append(f"stmt={self.stmt!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='ae7f5fee7ddc303cd3484eca7cbf18a37341bfd5',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('left', True, True, None, True, False, False, None), 'instance', 'factory', "
            "None, False, False, False), (('right', True, True, None, True, False, False, None), 'instance', 'factory',"
            " None, False, False, False), (('dollar', True, True, None, True, False, False, None), 'instance', 'value',"
            " None, False, False, False), (('parts', True, True, None, True, False, False, None), 'instance', 'factory'"
            ", None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'DblQuoted'),
    ),
)
def _process_dataclass__ae7f5fee7ddc303cd3484eca7cbf18a37341bfd5():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default_factory = __dataclass__spec.fields[3].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                left=self.left,
                right=self.right,
                dollar=self.dollar,
                parts=self.parts,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.left == other.left and
                self.right == other.right and
                self.dollar == other.dollar and
                self.parts == other.parts
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            left: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            right: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            dollar: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            parts: __dataclass__init__fields__3__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if left is __dataclass__HAS_DEFAULT_FACTORY:
                left = __dataclass__init__fields__0__default_factory()
            if right is __dataclass__HAS_DEFAULT_FACTORY:
                right = __dataclass__init__fields__1__default_factory()
            if parts is __dataclass__HAS_DEFAULT_FACTORY:
                parts = __dataclass__init__fields__3__default_factory()
            self.left = left
            self.right = right
            self.dollar = dollar
            self.parts = parts

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"left={self.left!r}")
            parts.append(f"right={self.right!r}")
            parts.append(f"dollar={self.dollar!r}")
            parts.append(f"parts={self.parts!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='1410745696b59c190cc0e7cf7563dc737bdba329',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('variant', True, True, None, True, False, False, None), 'instance', 'value',"
            " None, False, False, False), (('args', True, True, None, True, False, False, None), 'instance', 'factory',"
            " None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'DeclClause'),
    ),
)
def _process_dataclass__1410745696b59c190cc0e7cf7563dc737bdba329():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default = __dataclass__spec.fields[0].default.must()
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                variant=self.variant,
                args=self.args,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.variant == other.variant and
                self.args == other.args
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            variant: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            args: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if args is __dataclass__HAS_DEFAULT_FACTORY:
                args = __dataclass__init__fields__1__default_factory()
            self.variant = variant
            self.args = args

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"variant={self.variant!r}")
            parts.append(f"args={self.args!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='6c94db94724fc44df6dc39c7f0082dea082d06c9',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('op', True, True, None, True, False, False, None), 'instance', 'value', None"
            ", False, False, False), (('word', True, True, None, True, False, False, None), 'instance', 'value', None, "
            "False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (F"
            "alse,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'Expansion'),
    ),
)
def _process_dataclass__6c94db94724fc44df6dc39c7f0082dea082d06c9():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                op=self.op,
                word=self.word,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.op == other.op and
                self.word == other.word
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            op: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            word: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            self.op = op
            self.word = word

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"op={self.op!r}")
            parts.append(f"word={self.word!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='0e6f56ff155557f5916da14ca513e529b0813560',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('op_pos', True, True, None, True, False, False, None), 'instance', 'factory'"
            ", None, False, False, False), (('op', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('pattern', True, True, None, True, False, False, None), 'instance', 'value', N"
            "one, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'ExtGlob'),
    ),
)
def _process_dataclass__0e6f56ff155557f5916da14ca513e529b0813560():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                op_pos=self.op_pos,
                op=self.op,
                pattern=self.pattern,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.op_pos == other.op_pos and
                self.op == other.op and
                self.pattern == other.pattern
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            op_pos: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            op: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            pattern: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            if op_pos is __dataclass__HAS_DEFAULT_FACTORY:
                op_pos = __dataclass__init__fields__0__default_factory()
            self.op_pos = op_pos
            self.op = op
            self.pattern = pattern

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"op_pos={self.op_pos!r}")
            parts.append(f"op={self.op!r}")
            parts.append(f"pattern={self.pattern!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='bfa4829e8c74b1850850246b4401bd604822e3d8',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('name', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('stmts', True, True, None, True, False, False, None), 'instance', 'factory', N"
            "one, False, False, False), (('last', True, True, None, True, False, False, None), 'instance', 'factory', N"
            "one, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'File'),
    ),
)
def _process_dataclass__bfa4829e8c74b1850850246b4401bd604822e3d8():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default = __dataclass__spec.fields[0].default.must()
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default_factory = __dataclass__spec.fields[2].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                name=self.name,
                stmts=self.stmts,
                last=self.last,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.stmts == other.stmts and
                self.last == other.last
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            stmts: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            last: __dataclass__init__fields__2__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if stmts is __dataclass__HAS_DEFAULT_FACTORY:
                stmts = __dataclass__init__fields__1__default_factory()
            if last is __dataclass__HAS_DEFAULT_FACTORY:
                last = __dataclass__init__fields__2__default_factory()
            self.name = name
            self.stmts = stmts
            self.last = last

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"stmts={self.stmts!r}")
            parts.append(f"last={self.last!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='4c0490e7c3ff92e77ccf0daf84b87db37b5269ad',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('flags', True, True, None, True, False, False, None), 'instance', 'value', N"
            "one, False, False, False), (('x', True, True, None, True, False, False, None), 'instance', 'value', None, "
            "False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (F"
            "alse,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'FlagsArithm'),
    ),
)
def _process_dataclass__4c0490e7c3ff92e77ccf0daf84b87db37b5269ad():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                flags=self.flags,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.flags == other.flags and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            flags: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            x: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            self.flags = flags
            self.x = x

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"flags={self.flags!r}")
            parts.append(f"x={self.x!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='718b50516ac021353a8be221abf870432e812650',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('for_pos', True, True, None, True, False, False, None), 'instance', 'factory"
            "', None, False, False, False), (('do_pos', True, True, None, True, False, False, None), 'instance', 'facto"
            "ry', None, False, False, False), (('done_pos', True, True, None, True, False, False, None), 'instance', 'f"
            "actory', None, False, False, False), (('select', True, True, None, True, False, False, None), 'instance', "
            "'value', None, False, False, False), (('braces', True, True, None, True, False, False, None), 'instance', "
            "'value', None, False, False, False), (('loop', True, True, None, True, False, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('do', True, True, None, True, False, False, None), 'instance', 'facto"
            "ry', None, False, False, False), (('do_last', True, True, None, True, False, False, None), 'instance', 'fa"
            "ctory', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()),"
            " ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'ForClause'),
    ),
)
def _process_dataclass__718b50516ac021353a8be221abf870432e812650():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default_factory = __dataclass__spec.fields[2].default.must().fn
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__default = __dataclass__spec.fields[5].default.must()
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__6__default_factory = __dataclass__spec.fields[6].default.must().fn
        __dataclass__init__fields__7__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__7__default_factory = __dataclass__spec.fields[7].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                for_pos=self.for_pos,
                do_pos=self.do_pos,
                done_pos=self.done_pos,
                select=self.select,
                braces=self.braces,
                loop=self.loop,
                do=self.do,
                do_last=self.do_last,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.for_pos == other.for_pos and
                self.do_pos == other.do_pos and
                self.done_pos == other.done_pos and
                self.select == other.select and
                self.braces == other.braces and
                self.loop == other.loop and
                self.do == other.do and
                self.do_last == other.do_last
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            for_pos: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            do_pos: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            done_pos: __dataclass__init__fields__2__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            select: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            braces: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            loop: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            do: __dataclass__init__fields__6__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            do_last: __dataclass__init__fields__7__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if for_pos is __dataclass__HAS_DEFAULT_FACTORY:
                for_pos = __dataclass__init__fields__0__default_factory()
            if do_pos is __dataclass__HAS_DEFAULT_FACTORY:
                do_pos = __dataclass__init__fields__1__default_factory()
            if done_pos is __dataclass__HAS_DEFAULT_FACTORY:
                done_pos = __dataclass__init__fields__2__default_factory()
            if do is __dataclass__HAS_DEFAULT_FACTORY:
                do = __dataclass__init__fields__6__default_factory()
            if do_last is __dataclass__HAS_DEFAULT_FACTORY:
                do_last = __dataclass__init__fields__7__default_factory()
            self.for_pos = for_pos
            self.do_pos = do_pos
            self.done_pos = done_pos
            self.select = select
            self.braces = braces
            self.loop = loop
            self.do = do
            self.do_last = do_last

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"for_pos={self.for_pos!r}")
            parts.append(f"do_pos={self.do_pos!r}")
            parts.append(f"done_pos={self.done_pos!r}")
            parts.append(f"select={self.select!r}")
            parts.append(f"braces={self.braces!r}")
            parts.append(f"loop={self.loop!r}")
            parts.append(f"do={self.do!r}")
            parts.append(f"do_last={self.do_last!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='639578498a49d29751bbba9a5b248c9b9e823d7c',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('position', True, True, None, True, False, False, None), 'instance', 'factor"
            "y', None, False, False, False), (('rsrv_word', True, True, None, True, False, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('parens', True, True, None, True, False, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('name', True, True, None, True, False, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('names', True, True, None, True, False, False, None), 'instance', 'fact"
            "ory', None, False, False, False), (('body', True, True, None, True, False, False, None), 'instance', 'valu"
            "e', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (()"
            ",), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'FuncDecl'),
    ),
)
def _process_dataclass__639578498a49d29751bbba9a5b248c9b9e823d7c():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default_factory = __dataclass__spec.fields[4].default.must().fn
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__default = __dataclass__spec.fields[5].default.must()
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                position=self.position,
                rsrv_word=self.rsrv_word,
                parens=self.parens,
                name=self.name,
                names=self.names,
                body=self.body,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.position == other.position and
                self.rsrv_word == other.rsrv_word and
                self.parens == other.parens and
                self.name == other.name and
                self.names == other.names and
                self.body == other.body
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            position: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            rsrv_word: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            parens: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            name: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            names: __dataclass__init__fields__4__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            body: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            if position is __dataclass__HAS_DEFAULT_FACTORY:
                position = __dataclass__init__fields__0__default_factory()
            if names is __dataclass__HAS_DEFAULT_FACTORY:
                names = __dataclass__init__fields__4__default_factory()
            self.position = position
            self.rsrv_word = rsrv_word
            self.parens = parens
            self.name = name
            self.names = names
            self.body = body

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"position={self.position!r}")
            parts.append(f"rsrv_word={self.rsrv_word!r}")
            parts.append(f"parens={self.parens!r}")
            parts.append(f"name={self.name!r}")
            parts.append(f"names={self.names!r}")
            parts.append(f"body={self.body!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='7bb33067b19e6a11670eeddc91f3fb8d821bc786',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('position', True, True, None, True, False, False, None), 'instance', 'factor"
            "y', None, False, False, False), (('then_pos', True, True, None, True, False, False, None), 'instance', 'fa"
            "ctory', None, False, False, False), (('fi_pos', True, True, None, True, False, False, None), 'instance', '"
            "factory', None, False, False, False), (('cond', True, True, None, True, False, False, None), 'instance', '"
            "factory', None, False, False, False), (('cond_last', True, True, None, True, False, False, None), 'instanc"
            "e', 'factory', None, False, False, False), (('then', True, True, None, True, False, False, None), 'instanc"
            "e', 'factory', None, False, False, False), (('then_last', True, True, None, True, False, False, None), 'in"
            "stance', 'factory', None, False, False, False), (('else_', True, True, None, True, False, False, None), 'i"
            "nstance', 'value', None, False, False, False), (('last', True, True, None, True, False, False, None), 'ins"
            "tance', 'factory', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, "
            "False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'IfClause'),
    ),
)
def _process_dataclass__7bb33067b19e6a11670eeddc91f3fb8d821bc786():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default_factory = __dataclass__spec.fields[2].default.must().fn
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default_factory = __dataclass__spec.fields[3].default.must().fn
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default_factory = __dataclass__spec.fields[4].default.must().fn
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__default_factory = __dataclass__spec.fields[5].default.must().fn
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__6__default_factory = __dataclass__spec.fields[6].default.must().fn
        __dataclass__init__fields__7__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__7__default = __dataclass__spec.fields[7].default.must()
        __dataclass__init__fields__8__annotation = __dataclass__spec.fields[8].annotation
        __dataclass__init__fields__8__default_factory = __dataclass__spec.fields[8].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                position=self.position,
                then_pos=self.then_pos,
                fi_pos=self.fi_pos,
                cond=self.cond,
                cond_last=self.cond_last,
                then=self.then,
                then_last=self.then_last,
                else_=self.else_,
                last=self.last,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.position == other.position and
                self.then_pos == other.then_pos and
                self.fi_pos == other.fi_pos and
                self.cond == other.cond and
                self.cond_last == other.cond_last and
                self.then == other.then and
                self.then_last == other.then_last and
                self.else_ == other.else_ and
                self.last == other.last
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            position: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            then_pos: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            fi_pos: __dataclass__init__fields__2__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            cond: __dataclass__init__fields__3__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            cond_last: __dataclass__init__fields__4__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            then: __dataclass__init__fields__5__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            then_last: __dataclass__init__fields__6__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            else_: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
            last: __dataclass__init__fields__8__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if position is __dataclass__HAS_DEFAULT_FACTORY:
                position = __dataclass__init__fields__0__default_factory()
            if then_pos is __dataclass__HAS_DEFAULT_FACTORY:
                then_pos = __dataclass__init__fields__1__default_factory()
            if fi_pos is __dataclass__HAS_DEFAULT_FACTORY:
                fi_pos = __dataclass__init__fields__2__default_factory()
            if cond is __dataclass__HAS_DEFAULT_FACTORY:
                cond = __dataclass__init__fields__3__default_factory()
            if cond_last is __dataclass__HAS_DEFAULT_FACTORY:
                cond_last = __dataclass__init__fields__4__default_factory()
            if then is __dataclass__HAS_DEFAULT_FACTORY:
                then = __dataclass__init__fields__5__default_factory()
            if then_last is __dataclass__HAS_DEFAULT_FACTORY:
                then_last = __dataclass__init__fields__6__default_factory()
            if last is __dataclass__HAS_DEFAULT_FACTORY:
                last = __dataclass__init__fields__8__default_factory()
            self.position = position
            self.then_pos = then_pos
            self.fi_pos = fi_pos
            self.cond = cond
            self.cond_last = cond_last
            self.then = then
            self.then_last = then_last
            self.else_ = else_
            self.last = last

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"position={self.position!r}")
            parts.append(f"then_pos={self.then_pos!r}")
            parts.append(f"fi_pos={self.fi_pos!r}")
            parts.append(f"cond={self.cond!r}")
            parts.append(f"cond_last={self.cond_last!r}")
            parts.append(f"then={self.then!r}")
            parts.append(f"then_last={self.then_last!r}")
            parts.append(f"else_={self.else_!r}")
            parts.append(f"last={self.last!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='80b20491546de536ebb7675b9cf020fa37845d94',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('let', True, True, None, True, False, False, None), 'instance', 'factory', N"
            "one, False, False, False), (('exprs', True, True, None, True, False, False, None), 'instance', 'factory', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'LetClause'),
    ),
)
def _process_dataclass__80b20491546de536ebb7675b9cf020fa37845d94():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                let=self.let,
                exprs=self.exprs,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.let == other.let and
                self.exprs == other.exprs
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            let: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            exprs: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if let is __dataclass__HAS_DEFAULT_FACTORY:
                let = __dataclass__init__fields__0__default_factory()
            if exprs is __dataclass__HAS_DEFAULT_FACTORY:
                exprs = __dataclass__init__fields__1__default_factory()
            self.let = let
            self.exprs = exprs

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"let={self.let!r}")
            parts.append(f"exprs={self.exprs!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='7f19e80ab0c30a94aa2dd528022d558b04994beb',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, True, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('value_pos', True, True, None, True, True, False, None), 'instance', 'factory"
            "', None, False, False, False), (('value_end', True, True, None, True, True, False, None), 'instance', 'fac"
            "tory', None, False, False, False), (('value', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (("
            "),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'Lit'),
    ),
)
def _process_dataclass__7f19e80ab0c30a94aa2dd528022d558b04994beb():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                value_pos=self.value_pos,
                value_end=self.value_end,
                value=self.value,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.value_pos == other.value_pos and
                self.value_end == other.value_end and
                self.value == other.value
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            *,
            value_pos: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            value_end: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            value: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            if value_pos is __dataclass__HAS_DEFAULT_FACTORY:
                value_pos = __dataclass__init__fields__0__default_factory()
            if value_end is __dataclass__HAS_DEFAULT_FACTORY:
                value_end = __dataclass__init__fields__1__default_factory()
            self.value_pos = value_pos
            self.value_end = value_end
            self.value = value

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"value_pos={self.value_pos!r}")
            parts.append(f"value_end={self.value_end!r}")
            parts.append(f"value={self.value!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='60db1017b5cdb43e3d3f9efc582377ba89f3c12e',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('dollar', True, True, None, True, False, False, None), 'instance', 'factory'"
            ", None, False, False, False), (('rbrace', True, True, None, True, False, False, None), 'instance', 'factor"
            "y', None, False, False, False), (('short', True, True, None, True, False, False, None), 'instance', 'value"
            "', None, False, False, False), (('flags', True, True, None, True, False, False, None), 'instance', 'value'"
            ", None, False, False, False), (('excl', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('length', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('width', True, True, None, True, False, False, None), 'instance', 'value', N"
            "one, False, False, False), (('is_set', True, True, None, True, False, False, None), 'instance', 'value', N"
            "one, False, False, False), (('split', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('glob_subst', True, True, None, True, False, False, None), 'instance', 'value'"
            ", None, False, False, False), (('rc_expand', True, True, None, True, False, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('param', True, True, None, True, False, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('nested_param', True, True, None, True, False, False, None), 'instance',"
            " 'value', None, False, False, False), (('index', True, True, None, True, False, False, None), 'instance', "
            "'value', None, False, False, False), (('modifiers', True, True, None, True, False, False, None), 'instance"
            "', 'factory', None, False, False, False), (('slice', True, True, None, True, False, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('repl', True, True, None, True, False, False, None), 'instance'"
            ", 'value', None, False, False, False), (('names', True, True, None, True, False, False, None), 'instance',"
            " 'value', None, False, False, False), (('exp', True, True, None, True, False, False, None), 'instance', 'v"
            "alue', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), "
            "((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'ParamExp'),
    ),
)
def _process_dataclass__60db1017b5cdb43e3d3f9efc582377ba89f3c12e():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__00__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__01__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__01__default_factory = __dataclass__spec.fields[1].default.must().fn
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
        __dataclass__init__fields__14__default_factory = __dataclass__spec.fields[14].default.must().fn
        __dataclass__init__fields__15__annotation = __dataclass__spec.fields[15].annotation
        __dataclass__init__fields__15__default = __dataclass__spec.fields[15].default.must()
        __dataclass__init__fields__16__annotation = __dataclass__spec.fields[16].annotation
        __dataclass__init__fields__16__default = __dataclass__spec.fields[16].default.must()
        __dataclass__init__fields__17__annotation = __dataclass__spec.fields[17].annotation
        __dataclass__init__fields__17__default = __dataclass__spec.fields[17].default.must()
        __dataclass__init__fields__18__annotation = __dataclass__spec.fields[18].annotation
        __dataclass__init__fields__18__default = __dataclass__spec.fields[18].default.must()
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                dollar=self.dollar,
                rbrace=self.rbrace,
                short=self.short,
                flags=self.flags,
                excl=self.excl,
                length=self.length,
                width=self.width,
                is_set=self.is_set,
                split=self.split,
                glob_subst=self.glob_subst,
                rc_expand=self.rc_expand,
                param=self.param,
                nested_param=self.nested_param,
                index=self.index,
                modifiers=self.modifiers,
                slice=self.slice,
                repl=self.repl,
                names=self.names,
                exp=self.exp,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.dollar == other.dollar and
                self.rbrace == other.rbrace and
                self.short == other.short and
                self.flags == other.flags and
                self.excl == other.excl and
                self.length == other.length and
                self.width == other.width and
                self.is_set == other.is_set and
                self.split == other.split and
                self.glob_subst == other.glob_subst and
                self.rc_expand == other.rc_expand and
                self.param == other.param and
                self.nested_param == other.nested_param and
                self.index == other.index and
                self.modifiers == other.modifiers and
                self.slice == other.slice and
                self.repl == other.repl and
                self.names == other.names and
                self.exp == other.exp
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            dollar: __dataclass__init__fields__00__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            rbrace: __dataclass__init__fields__01__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            short: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            flags: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            excl: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            length: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            width: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            is_set: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            split: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            glob_subst: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            rc_expand: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            param: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            nested_param: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            index: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            modifiers: __dataclass__init__fields__14__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            slice: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            repl: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            names: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
            exp: __dataclass__init__fields__18__annotation = __dataclass__init__fields__18__default,
        ) -> __dataclass__None:
            if dollar is __dataclass__HAS_DEFAULT_FACTORY:
                dollar = __dataclass__init__fields__00__default_factory()
            if rbrace is __dataclass__HAS_DEFAULT_FACTORY:
                rbrace = __dataclass__init__fields__01__default_factory()
            if modifiers is __dataclass__HAS_DEFAULT_FACTORY:
                modifiers = __dataclass__init__fields__14__default_factory()
            self.dollar = dollar
            self.rbrace = rbrace
            self.short = short
            self.flags = flags
            self.excl = excl
            self.length = length
            self.width = width
            self.is_set = is_set
            self.split = split
            self.glob_subst = glob_subst
            self.rc_expand = rc_expand
            self.param = param
            self.nested_param = nested_param
            self.index = index
            self.modifiers = modifiers
            self.slice = slice
            self.repl = repl
            self.names = names
            self.exp = exp

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"dollar={self.dollar!r}")
            parts.append(f"rbrace={self.rbrace!r}")
            parts.append(f"short={self.short!r}")
            parts.append(f"flags={self.flags!r}")
            parts.append(f"excl={self.excl!r}")
            parts.append(f"length={self.length!r}")
            parts.append(f"width={self.width!r}")
            parts.append(f"is_set={self.is_set!r}")
            parts.append(f"split={self.split!r}")
            parts.append(f"glob_subst={self.glob_subst!r}")
            parts.append(f"rc_expand={self.rc_expand!r}")
            parts.append(f"param={self.param!r}")
            parts.append(f"nested_param={self.nested_param!r}")
            parts.append(f"index={self.index!r}")
            parts.append(f"modifiers={self.modifiers!r}")
            parts.append(f"slice={self.slice!r}")
            parts.append(f"repl={self.repl!r}")
            parts.append(f"names={self.names!r}")
            parts.append(f"exp={self.exp!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b8c35160f9e869467cc7963d35066d9c49497260',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('lparen', True, True, None, True, False, False, None), 'instance', 'factory'"
            ", None, False, False, False), (('rparen', True, True, None, True, False, False, None), 'instance', 'factor"
            "y', None, False, False, False), (('x', True, True, None, True, False, False, None), 'instance', 'value', N"
            "one, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'ParenArithm'),
        ('omxtra.text.shparse.nodes', 'ParenTest'),
    ),
)
def _process_dataclass__b8c35160f9e869467cc7963d35066d9c49497260():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                lparen=self.lparen,
                rparen=self.rparen,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.lparen == other.lparen and
                self.rparen == other.rparen and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            lparen: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            rparen: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            x: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            if lparen is __dataclass__HAS_DEFAULT_FACTORY:
                lparen = __dataclass__init__fields__0__default_factory()
            if rparen is __dataclass__HAS_DEFAULT_FACTORY:
                rparen = __dataclass__init__fields__1__default_factory()
            self.lparen = lparen
            self.rparen = rparen
            self.x = x

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"lparen={self.lparen!r}")
            parts.append(f"rparen={self.rparen!r}")
            parts.append(f"x={self.x!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='df1eb35fe4645c60aaab9902cb8a8a4cfc470196',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('offs', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('line_col', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'Pos'),
    ),
)
def _process_dataclass__df1eb35fe4645c60aaab9902cb8a8a4cfc470196():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                offs=self.offs,
                line_col=self.line_col,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.offs == other.offs and
                self.line_col == other.line_col
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            offs: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            line_col: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            self.offs = offs
            self.line_col = line_col

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"offs={self.offs!r}")
            parts.append(f"line_col={self.line_col!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='8382b26f1b39f28cdc75fbfffb3ab86978993aa2',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('op_pos', True, True, None, True, False, False, None), 'instance', 'factory'"
            ", None, False, False, False), (('rparen', True, True, None, True, False, False, None), 'instance', 'factor"
            "y', None, False, False, False), (('op', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('stmts', True, True, None, True, False, False, None), 'instance', 'factory',"
            " None, False, False, False), (('last', True, True, None, True, False, False, None), 'instance', 'factory',"
            " None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'ProcSubst'),
    ),
)
def _process_dataclass__8382b26f1b39f28cdc75fbfffb3ab86978993aa2():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default_factory = __dataclass__spec.fields[3].default.must().fn
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default_factory = __dataclass__spec.fields[4].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                op_pos=self.op_pos,
                rparen=self.rparen,
                op=self.op,
                stmts=self.stmts,
                last=self.last,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.op_pos == other.op_pos and
                self.rparen == other.rparen and
                self.op == other.op and
                self.stmts == other.stmts and
                self.last == other.last
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            op_pos: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            rparen: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            op: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            stmts: __dataclass__init__fields__3__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            last: __dataclass__init__fields__4__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if op_pos is __dataclass__HAS_DEFAULT_FACTORY:
                op_pos = __dataclass__init__fields__0__default_factory()
            if rparen is __dataclass__HAS_DEFAULT_FACTORY:
                rparen = __dataclass__init__fields__1__default_factory()
            if stmts is __dataclass__HAS_DEFAULT_FACTORY:
                stmts = __dataclass__init__fields__3__default_factory()
            if last is __dataclass__HAS_DEFAULT_FACTORY:
                last = __dataclass__init__fields__4__default_factory()
            self.op_pos = op_pos
            self.rparen = rparen
            self.op = op
            self.stmts = stmts
            self.last = last

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"op_pos={self.op_pos!r}")
            parts.append(f"rparen={self.rparen!r}")
            parts.append(f"op={self.op!r}")
            parts.append(f"stmts={self.stmts!r}")
            parts.append(f"last={self.last!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='46085236b56f89fa2e64226a43151632ea133f7d',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('op_pos', True, True, None, True, False, False, None), 'instance', 'factory'"
            ", None, False, False, False), (('op', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('n', True, True, None, True, False, False, None), 'instance', 'value', None, F"
            "alse, False, False), (('word', True, True, None, True, False, False, None), 'instance', 'value', None, Fal"
            "se, False, False), (('hdoc', True, True, None, True, False, False, None), 'instance', 'value', None, False"
            ", False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,"
            ")))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'Redirect'),
    ),
)
def _process_dataclass__46085236b56f89fa2e64226a43151632ea133f7d():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                op_pos=self.op_pos,
                op=self.op,
                n=self.n,
                word=self.word,
                hdoc=self.hdoc,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.op_pos == other.op_pos and
                self.op == other.op and
                self.n == other.n and
                self.word == other.word and
                self.hdoc == other.hdoc
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            op_pos: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            op: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            n: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            word: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            hdoc: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            if op_pos is __dataclass__HAS_DEFAULT_FACTORY:
                op_pos = __dataclass__init__fields__0__default_factory()
            self.op_pos = op_pos
            self.op = op
            self.n = n
            self.word = word
            self.hdoc = hdoc

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"op_pos={self.op_pos!r}")
            parts.append(f"op={self.op!r}")
            parts.append(f"n={self.n!r}")
            parts.append(f"word={self.word!r}")
            parts.append(f"hdoc={self.hdoc!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='320921465b4af348229a4a99552d294cf6c40900',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('all', True, True, None, True, False, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('orig', True, True, None, True, False, False, None), 'instance', 'value', None,"
            " False, False, False), (('with_', True, True, None, True, False, False, None), 'instance', 'value', None, "
            "False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (F"
            "alse,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'Replace'),
    ),
)
def _process_dataclass__320921465b4af348229a4a99552d294cf6c40900():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                all=self.all,
                orig=self.orig,
                with_=self.with_,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.all == other.all and
                self.orig == other.orig and
                self.with_ == other.with_
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            all: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            orig: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            with_: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            self.all = all
            self.orig = orig
            self.with_ = with_

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"all={self.all!r}")
            parts.append(f"orig={self.orig!r}")
            parts.append(f"with_={self.with_!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='2c8351abfc6d7186f894db36d2841b71ebdd72e5',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('left', True, True, None, True, False, False, None), 'instance', 'factory', "
            "None, False, False, False), (('right', True, True, None, True, False, False, None), 'instance', 'factory',"
            " None, False, False, False), (('dollar', True, True, None, True, False, False, None), 'instance', 'value',"
            " None, False, False, False), (('value', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'SglQuoted'),
    ),
)
def _process_dataclass__2c8351abfc6d7186f894db36d2841b71ebdd72e5():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                left=self.left,
                right=self.right,
                dollar=self.dollar,
                value=self.value,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.left == other.left and
                self.right == other.right and
                self.dollar == other.dollar and
                self.value == other.value
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            left: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            right: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            dollar: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            value: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            if left is __dataclass__HAS_DEFAULT_FACTORY:
                left = __dataclass__init__fields__0__default_factory()
            if right is __dataclass__HAS_DEFAULT_FACTORY:
                right = __dataclass__init__fields__1__default_factory()
            self.left = left
            self.right = right
            self.dollar = dollar
            self.value = value

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"left={self.left!r}")
            parts.append(f"right={self.right!r}")
            parts.append(f"dollar={self.dollar!r}")
            parts.append(f"value={self.value!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='105384dd0e27050a365360393d452308f59fa5d6',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('offset', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('length', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'Slice'),
    ),
)
def _process_dataclass__105384dd0e27050a365360393d452308f59fa5d6():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                offset=self.offset,
                length=self.length,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.offset == other.offset and
                self.length == other.length
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            offset: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            length: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            self.offset = offset
            self.length = length

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"offset={self.offset!r}")
            parts.append(f"length={self.length!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='2ed74e5d98f84a209e88719db60909e4a8a444d0',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('comments', True, True, None, True, False, False, None), 'instance', 'factor"
            "y', None, False, False, False), (('cmd', True, True, None, True, False, False, None), 'instance', 'value',"
            " None, False, False, False), (('position', True, True, None, True, False, False, None), 'instance', 'facto"
            "ry', None, False, False, False), (('semicolon', True, True, None, True, False, False, None), 'instance', '"
            "factory', None, False, False, False), (('negated', True, True, None, True, False, False, None), 'instance'"
            ", 'value', None, False, False, False), (('background', True, True, None, True, False, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('coprocess', True, True, None, True, False, False, None), 'in"
            "stance', 'value', None, False, False, False), (('disown', True, True, None, True, False, False, None), 'in"
            "stance', 'value', None, False, False, False), (('redirs', True, True, None, True, False, False, None), 'in"
            "stance', 'factory', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False,"
            " False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'Stmt'),
    ),
)
def _process_dataclass__2ed74e5d98f84a209e88719db60909e4a8a444d0():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default_factory = __dataclass__spec.fields[2].default.must().fn
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default_factory = __dataclass__spec.fields[3].default.must().fn
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__default = __dataclass__spec.fields[5].default.must()
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__6__default = __dataclass__spec.fields[6].default.must()
        __dataclass__init__fields__7__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__7__default = __dataclass__spec.fields[7].default.must()
        __dataclass__init__fields__8__annotation = __dataclass__spec.fields[8].annotation
        __dataclass__init__fields__8__default_factory = __dataclass__spec.fields[8].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                comments=self.comments,
                cmd=self.cmd,
                position=self.position,
                semicolon=self.semicolon,
                negated=self.negated,
                background=self.background,
                coprocess=self.coprocess,
                disown=self.disown,
                redirs=self.redirs,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.comments == other.comments and
                self.cmd == other.cmd and
                self.position == other.position and
                self.semicolon == other.semicolon and
                self.negated == other.negated and
                self.background == other.background and
                self.coprocess == other.coprocess and
                self.disown == other.disown and
                self.redirs == other.redirs
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            comments: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            cmd: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            position: __dataclass__init__fields__2__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            semicolon: __dataclass__init__fields__3__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            negated: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            background: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            coprocess: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
            disown: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
            redirs: __dataclass__init__fields__8__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if comments is __dataclass__HAS_DEFAULT_FACTORY:
                comments = __dataclass__init__fields__0__default_factory()
            if position is __dataclass__HAS_DEFAULT_FACTORY:
                position = __dataclass__init__fields__2__default_factory()
            if semicolon is __dataclass__HAS_DEFAULT_FACTORY:
                semicolon = __dataclass__init__fields__3__default_factory()
            if redirs is __dataclass__HAS_DEFAULT_FACTORY:
                redirs = __dataclass__init__fields__8__default_factory()
            self.comments = comments
            self.cmd = cmd
            self.position = position
            self.semicolon = semicolon
            self.negated = negated
            self.background = background
            self.coprocess = coprocess
            self.disown = disown
            self.redirs = redirs

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"comments={self.comments!r}")
            parts.append(f"cmd={self.cmd!r}")
            parts.append(f"position={self.position!r}")
            parts.append(f"semicolon={self.semicolon!r}")
            parts.append(f"negated={self.negated!r}")
            parts.append(f"background={self.background!r}")
            parts.append(f"coprocess={self.coprocess!r}")
            parts.append(f"disown={self.disown!r}")
            parts.append(f"redirs={self.redirs!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='955db194ac6c6d650095a79b5ced1f963470eb70',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('lparen', True, True, None, True, False, False, None), 'instance', 'factory'"
            ", None, False, False, False), (('rparen', True, True, None, True, False, False, None), 'instance', 'factor"
            "y', None, False, False, False), (('stmts', True, True, None, True, False, False, None), 'instance', 'facto"
            "ry', None, False, False, False), (('last', True, True, None, True, False, False, None), 'instance', 'facto"
            "ry', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (("
            "),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'Subshell'),
    ),
)
def _process_dataclass__955db194ac6c6d650095a79b5ced1f963470eb70():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default_factory = __dataclass__spec.fields[2].default.must().fn
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default_factory = __dataclass__spec.fields[3].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                lparen=self.lparen,
                rparen=self.rparen,
                stmts=self.stmts,
                last=self.last,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.lparen == other.lparen and
                self.rparen == other.rparen and
                self.stmts == other.stmts and
                self.last == other.last
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            lparen: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            rparen: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            stmts: __dataclass__init__fields__2__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            last: __dataclass__init__fields__3__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if lparen is __dataclass__HAS_DEFAULT_FACTORY:
                lparen = __dataclass__init__fields__0__default_factory()
            if rparen is __dataclass__HAS_DEFAULT_FACTORY:
                rparen = __dataclass__init__fields__1__default_factory()
            if stmts is __dataclass__HAS_DEFAULT_FACTORY:
                stmts = __dataclass__init__fields__2__default_factory()
            if last is __dataclass__HAS_DEFAULT_FACTORY:
                last = __dataclass__init__fields__3__default_factory()
            self.lparen = lparen
            self.rparen = rparen
            self.stmts = stmts
            self.last = last

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"lparen={self.lparen!r}")
            parts.append(f"rparen={self.rparen!r}")
            parts.append(f"stmts={self.stmts!r}")
            parts.append(f"last={self.last!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='5a72583c55e25908b069020a87f56fd2d6d0805e',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('left', True, True, None, True, False, False, None), 'instance', 'factory', "
            "None, False, False, False), (('right', True, True, None, True, False, False, None), 'instance', 'factory',"
            " None, False, False, False), (('x', True, True, None, True, False, False, None), 'instance', 'value', None"
            ", False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), "
            "(False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'TestClause'),
    ),
)
def _process_dataclass__5a72583c55e25908b069020a87f56fd2d6d0805e():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                left=self.left,
                right=self.right,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.left == other.left and
                self.right == other.right and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            left: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            right: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            x: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            if left is __dataclass__HAS_DEFAULT_FACTORY:
                left = __dataclass__init__fields__0__default_factory()
            if right is __dataclass__HAS_DEFAULT_FACTORY:
                right = __dataclass__init__fields__1__default_factory()
            self.left = left
            self.right = right
            self.x = x

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"left={self.left!r}")
            parts.append(f"right={self.right!r}")
            parts.append(f"x={self.x!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='95731c3b0aa48fd287369801029c8556df96cc51',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('position', True, True, None, True, False, False, None), 'instance', 'factor"
            "y', None, False, False, False), (('description', True, True, None, True, False, False, None), 'instance', "
            "'value', None, False, False, False), (('body', True, True, None, True, False, False, None), 'instance', 'v"
            "alue', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), "
            "((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'TestDecl'),
    ),
)
def _process_dataclass__95731c3b0aa48fd287369801029c8556df96cc51():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                position=self.position,
                description=self.description,
                body=self.body,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.position == other.position and
                self.description == other.description and
                self.body == other.body
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            position: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            description: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            body: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            if position is __dataclass__HAS_DEFAULT_FACTORY:
                position = __dataclass__init__fields__0__default_factory()
            self.position = position
            self.description = description
            self.body = body

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"position={self.position!r}")
            parts.append(f"description={self.description!r}")
            parts.append(f"body={self.body!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c54fc16b3c0fc956d5a2719be14b1003913168a0',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('time', True, True, None, True, False, False, None), 'instance', 'factory', "
            "None, False, False, False), (('posix_format', True, True, None, True, False, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('stmt', True, True, None, True, False, False, None), 'instance', 'valu"
            "e', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (()"
            ",), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'TimeClause'),
    ),
)
def _process_dataclass__c54fc16b3c0fc956d5a2719be14b1003913168a0():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                time=self.time,
                posix_format=self.posix_format,
                stmt=self.stmt,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.time == other.time and
                self.posix_format == other.posix_format and
                self.stmt == other.stmt
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            time: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            posix_format: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            stmt: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            if time is __dataclass__HAS_DEFAULT_FACTORY:
                time = __dataclass__init__fields__0__default_factory()
            self.time = time
            self.posix_format = posix_format
            self.stmt = stmt

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"time={self.time!r}")
            parts.append(f"posix_format={self.posix_format!r}")
            parts.append(f"stmt={self.stmt!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='df2da673a406cb1b7ffa6ab20c7a047a48f90082',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('op_pos', True, True, None, True, False, False, None), 'instance', 'factory'"
            ", None, False, False, False), (('op', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('post', True, True, None, True, False, False, None), 'instance', 'value', None"
            ", False, False, False), (('x', True, True, None, True, False, False, None), 'instance', 'value', None, Fal"
            "se, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (Fals"
            "e,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'UnaryArithm'),
    ),
)
def _process_dataclass__df2da673a406cb1b7ffa6ab20c7a047a48f90082():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                op_pos=self.op_pos,
                op=self.op,
                post=self.post,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.op_pos == other.op_pos and
                self.op == other.op and
                self.post == other.post and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            op_pos: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            op: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            post: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            x: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            if op_pos is __dataclass__HAS_DEFAULT_FACTORY:
                op_pos = __dataclass__init__fields__0__default_factory()
            self.op_pos = op_pos
            self.op = op
            self.post = post
            self.x = x

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"op_pos={self.op_pos!r}")
            parts.append(f"op={self.op!r}")
            parts.append(f"post={self.post!r}")
            parts.append(f"x={self.x!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='6d0e2a563b0422cb6ee7068f6e3816747c449fa8',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('op_pos', True, True, None, True, False, False, None), 'instance', 'factory'"
            ", None, False, False, False), (('op', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('x', True, True, None, True, False, False, None), 'instance', 'value', None, F"
            "alse, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (Fa"
            "lse,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'UnaryTest'),
    ),
)
def _process_dataclass__6d0e2a563b0422cb6ee7068f6e3816747c449fa8():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                op_pos=self.op_pos,
                op=self.op,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.op_pos == other.op_pos and
                self.op == other.op and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            op_pos: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            op: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            x: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            if op_pos is __dataclass__HAS_DEFAULT_FACTORY:
                op_pos = __dataclass__init__fields__0__default_factory()
            self.op_pos = op_pos
            self.op = op
            self.x = x

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"op_pos={self.op_pos!r}")
            parts.append(f"op={self.op!r}")
            parts.append(f"x={self.x!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='46a09e9b7a777fbc57c31ef7cf56e5c26cd2ae9e',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('while_pos', True, True, None, True, False, False, None), 'instance', 'facto"
            "ry', None, False, False, False), (('do_pos', True, True, None, True, False, False, None), 'instance', 'fac"
            "tory', None, False, False, False), (('done_pos', True, True, None, True, False, False, None), 'instance', "
            "'factory', None, False, False, False), (('until', True, True, None, True, False, False, None), 'instance',"
            " 'value', None, False, False, False), (('cond', True, True, None, True, False, False, None), 'instance', '"
            "factory', None, False, False, False), (('cond_last', True, True, None, True, False, False, None), 'instanc"
            "e', 'factory', None, False, False, False), (('do', True, True, None, True, False, False, None), 'instance'"
            ", 'factory', None, False, False, False), (('do_last', True, True, None, True, False, False, None), 'instan"
            "ce', 'factory', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, Fal"
            "se, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'WhileClause'),
    ),
)
def _process_dataclass__46a09e9b7a777fbc57c31ef7cf56e5c26cd2ae9e():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default_factory = __dataclass__spec.fields[2].default.must().fn
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default_factory = __dataclass__spec.fields[4].default.must().fn
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__default_factory = __dataclass__spec.fields[5].default.must().fn
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__6__default_factory = __dataclass__spec.fields[6].default.must().fn
        __dataclass__init__fields__7__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__7__default_factory = __dataclass__spec.fields[7].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                while_pos=self.while_pos,
                do_pos=self.do_pos,
                done_pos=self.done_pos,
                until=self.until,
                cond=self.cond,
                cond_last=self.cond_last,
                do=self.do,
                do_last=self.do_last,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.while_pos == other.while_pos and
                self.do_pos == other.do_pos and
                self.done_pos == other.done_pos and
                self.until == other.until and
                self.cond == other.cond and
                self.cond_last == other.cond_last and
                self.do == other.do and
                self.do_last == other.do_last
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            while_pos: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            do_pos: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            done_pos: __dataclass__init__fields__2__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            until: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            cond: __dataclass__init__fields__4__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            cond_last: __dataclass__init__fields__5__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            do: __dataclass__init__fields__6__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            do_last: __dataclass__init__fields__7__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if while_pos is __dataclass__HAS_DEFAULT_FACTORY:
                while_pos = __dataclass__init__fields__0__default_factory()
            if do_pos is __dataclass__HAS_DEFAULT_FACTORY:
                do_pos = __dataclass__init__fields__1__default_factory()
            if done_pos is __dataclass__HAS_DEFAULT_FACTORY:
                done_pos = __dataclass__init__fields__2__default_factory()
            if cond is __dataclass__HAS_DEFAULT_FACTORY:
                cond = __dataclass__init__fields__4__default_factory()
            if cond_last is __dataclass__HAS_DEFAULT_FACTORY:
                cond_last = __dataclass__init__fields__5__default_factory()
            if do is __dataclass__HAS_DEFAULT_FACTORY:
                do = __dataclass__init__fields__6__default_factory()
            if do_last is __dataclass__HAS_DEFAULT_FACTORY:
                do_last = __dataclass__init__fields__7__default_factory()
            self.while_pos = while_pos
            self.do_pos = do_pos
            self.done_pos = done_pos
            self.until = until
            self.cond = cond
            self.cond_last = cond_last
            self.do = do
            self.do_last = do_last

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"while_pos={self.while_pos!r}")
            parts.append(f"do_pos={self.do_pos!r}")
            parts.append(f"done_pos={self.done_pos!r}")
            parts.append(f"until={self.until!r}")
            parts.append(f"cond={self.cond!r}")
            parts.append(f"cond_last={self.cond_last!r}")
            parts.append(f"do={self.do!r}")
            parts.append(f"do_last={self.do_last!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e35fd6a369b3560475ba0269c5ad330bcf0eb5ac',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('parts', True, True, None, True, False, False, None), 'instance', 'factory',"
            " None, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'Word'),
    ),
)
def _process_dataclass__e35fd6a369b3560475ba0269c5ad330bcf0eb5ac():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                parts=self.parts,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.parts == other.parts
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            parts: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if parts is __dataclass__HAS_DEFAULT_FACTORY:
                parts = __dataclass__init__fields__0__default_factory()
            self.parts = parts

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"parts={self.parts!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='72d83b313018d5ea2898bde48aa0a3a17e686181',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('name', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('in_pos', True, True, None, True, False, False, None), 'instance', 'factory', "
            "None, False, False, False), (('items', True, True, None, True, False, False, None), 'instance', 'factory',"
            " None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.nodes', 'WordIter'),
    ),
)
def _process_dataclass__72d83b313018d5ea2898bde48aa0a3a17e686181():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default = __dataclass__spec.fields[0].default.must()
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default_factory = __dataclass__spec.fields[1].default.must().fn
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default_factory = __dataclass__spec.fields[2].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                name=self.name,
                in_pos=self.in_pos,
                items=self.items,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.in_pos == other.in_pos and
                self.items == other.items
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            in_pos: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            items: __dataclass__init__fields__2__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if in_pos is __dataclass__HAS_DEFAULT_FACTORY:
                in_pos = __dataclass__init__fields__1__default_factory()
            if items is __dataclass__HAS_DEFAULT_FACTORY:
                items = __dataclass__init__fields__2__default_factory()
            self.name = name
            self.in_pos = in_pos
            self.items = items

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"in_pos={self.in_pos!r}")
            parts.append(f"items={self.items!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d11ae78a78eaab9d44db4ac37578dab1e61c53d1',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('filename', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('pos', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('feature', True, True, None, True, False, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('langs', True, True, None, True, False, False, None), 'instance', 'mis"
            "sing', None, False, False, False), (('lang_used', True, True, None, True, False, False, None), 'instance',"
            " 'missing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, "
            "()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.parser', 'LangError'),
    ),
)
def _process_dataclass__d11ae78a78eaab9d44db4ac37578dab1e61c53d1():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                filename=self.filename,
                pos=self.pos,
                feature=self.feature,
                langs=self.langs,
                lang_used=self.lang_used,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.filename == other.filename and
                self.pos == other.pos and
                self.feature == other.feature and
                self.langs == other.langs and
                self.lang_used == other.lang_used
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            filename: __dataclass__init__fields__0__annotation,
            pos: __dataclass__init__fields__1__annotation,
            feature: __dataclass__init__fields__2__annotation,
            langs: __dataclass__init__fields__3__annotation,
            lang_used: __dataclass__init__fields__4__annotation,
        ) -> __dataclass__None:
            self.filename = filename
            self.pos = pos
            self.feature = feature
            self.langs = langs
            self.lang_used = lang_used

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"filename={self.filename!r}")
            parts.append(f"pos={self.pos!r}")
            parts.append(f"feature={self.feature!r}")
            parts.append(f"langs={self.langs!r}")
            parts.append(f"lang_used={self.lang_used!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='4b7b12d00243bad9ae960c34a19ea61a4366904d',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('filename', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('pos', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('text', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('incomplete', True, True, None, True, False, False, None), 'instance', 'v"
            "alue', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), "
            "((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.parser', 'ParseError'),
    ),
)
def _process_dataclass__4b7b12d00243bad9ae960c34a19ea61a4366904d():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                filename=self.filename,
                pos=self.pos,
                text=self.text,
                incomplete=self.incomplete,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.filename == other.filename and
                self.pos == other.pos and
                self.text == other.text and
                self.incomplete == other.incomplete
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            filename: __dataclass__init__fields__0__annotation,
            pos: __dataclass__init__fields__1__annotation,
            text: __dataclass__init__fields__2__annotation,
            incomplete: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            self.filename = filename
            self.pos = pos
            self.text = text
            self.incomplete = incomplete

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"filename={self.filename!r}")
            parts.append(f"pos={self.pos!r}")
            parts.append(f"text={self.text!r}")
            parts.append(f"incomplete={self.incomplete!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='38bbee4a37ab0041a039423f47b7f0c5c20774f4',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('start', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('end', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.pattern', 'NegExtGlobGroup'),
    ),
)
def _process_dataclass__38bbee4a37ab0041a039423f47b7f0c5c20774f4():
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
                start=self.start,
                end=self.end,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.start == other.start and
                self.end == other.end
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'start',
            'end',
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
                self.start,
                self.end,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            start: __dataclass__init__fields__0__annotation,
            end: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'start', start)
            __dataclass__object_setattr(self, 'end', end)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"start={self.start!r}")
            parts.append(f"end={self.end!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='ef1c58b8f0f76ba3588b6ded0d846257ace5454c',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('offset', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('s', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.shparse.quote', 'QuoteError'),
    ),
)
def _process_dataclass__ef1c58b8f0f76ba3588b6ded0d846257ace5454c():
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
                offset=self.offset,
                s=self.s,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.offset == other.offset and
                self.s == other.s
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            offset: __dataclass__init__fields__0__annotation,
            s: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            self.offset = offset
            self.s = s

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"offset={self.offset!r}")
            parts.append(f"s={self.s!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
