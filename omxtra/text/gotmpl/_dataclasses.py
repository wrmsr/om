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
    installer_sha1='3e95f80dea0498d1fb8cf017afb10aa6f0150d2b',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('name', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('msg', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, True, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.gotmpl.exec', 'ExecError'),
    ),
)
def _process_dataclass__3e95f80dea0498d1fb8cf017afb10aa6f0150d2b():
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
                name=self.name,
                msg=self.msg,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.msg == other.msg
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
            msg: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            self.name = name
            self.msg = msg
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"msg={self.msg!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='44173097d93e35f65e393bf42b6a21482d1b7eee',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('tmpl', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('wr', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('vars', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('node', True, True, None, True, False, False, None), 'instance', 'value', None"
            ", False, False, False), (('depth', True, True, None, True, False, False, None), 'instance', 'value', None,"
            " False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), ("
            "False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.gotmpl.exec', 'State'),
    ),
)
def _process_dataclass__44173097d93e35f65e393bf42b6a21482d1b7eee():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                tmpl=self.tmpl,
                wr=self.wr,
                vars=self.vars,
                node=self.node,
                depth=self.depth,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.tmpl == other.tmpl and
                self.wr == other.wr and
                self.vars == other.vars and
                self.node == other.node and
                self.depth == other.depth
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            tmpl: __dataclass__init__fields__0__annotation,
            wr: __dataclass__init__fields__1__annotation,
            vars: __dataclass__init__fields__2__annotation,
            node: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            depth: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            self.tmpl = tmpl
            self.wr = wr
            self.vars = vars
            self.node = node
            self.depth = depth

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"tmpl={self.tmpl!r}")
            parts.append(f"wr={self.wr!r}")
            parts.append(f"vars={self.vars!r}")
            parts.append(f"node={self.node!r}")
            parts.append(f"depth={self.depth!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='3431def90bebf3670af0052bc64e0a9c406a73a8',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('name', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('value', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.gotmpl.exec', 'Variable'),
    ),
)
def _process_dataclass__3431def90bebf3670af0052bc64e0a9c406a73a8():
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

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
            value: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            self.name = name
            self.value = value

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
    installer_sha1='24bc2c8d3e2c4c2c451513685a6cbd9a255d6103',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('emit_comment', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False), (('break_ok', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('continue_ok', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()),"
            " ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.gotmpl.lex', 'LexOptions'),
    ),
)
def _process_dataclass__24bc2c8d3e2c4c2c451513685a6cbd9a255d6103():
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
                emit_comment=self.emit_comment,
                break_ok=self.break_ok,
                continue_ok=self.continue_ok,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.emit_comment == other.emit_comment and
                self.break_ok == other.break_ok and
                self.continue_ok == other.continue_ok
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'emit_comment',
            'break_ok',
            'continue_ok',
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
                self.emit_comment,
                self.break_ok,
                self.continue_ok,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            emit_comment: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            break_ok: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            continue_ok: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'emit_comment', emit_comment)
            __dataclass__object_setattr(self, 'break_ok', break_ok)
            __dataclass__object_setattr(self, 'continue_ok', continue_ok)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"emit_comment={self.emit_comment!r}")
            parts.append(f"break_ok={self.break_ok!r}")
            parts.append(f"continue_ok={self.continue_ok!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='8cf63883aa92351177e072b87aae929ff60b4bf0',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('typ', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('pos', True, True, None, True, False, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('val', True, True, None, True, False, False, None), 'instance', 'missing', None"
            ", False, False, False), (('line', True, True, None, True, False, False, None), 'instance', 'missing', None"
            ", False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), "
            "(False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.gotmpl.lex', 'Token'),
    ),
)
def _process_dataclass__8cf63883aa92351177e072b87aae929ff60b4bf0():
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
                typ=self.typ,
                pos=self.pos,
                val=self.val,
                line=self.line,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.typ == other.typ and
                self.pos == other.pos and
                self.val == other.val and
                self.line == other.line
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'typ',
            'pos',
            'val',
            'line',
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
                self.typ,
                self.pos,
                self.val,
                self.line,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            typ: __dataclass__init__fields__0__annotation,
            pos: __dataclass__init__fields__1__annotation,
            val: __dataclass__init__fields__2__annotation,
            line: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'typ', typ)
            __dataclass__object_setattr(self, 'pos', pos)
            __dataclass__object_setattr(self, 'val', val)
            __dataclass__object_setattr(self, 'line', line)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"typ={self.typ!r}")
            parts.append(f"pos={self.pos!r}")
            parts.append(f"val={self.val!r}")
            parts.append(f"line={self.line!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='067e09fd0d05283ac55d9bd3a29ed01ec347edd1',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('type', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('pos', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('tree', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('line', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('pipe', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.gotmpl.nodes', 'ActionNode'),
    ),
)
def _process_dataclass__067e09fd0d05283ac55d9bd3a29ed01ec347edd1():
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
                type=self.type,
                pos=self.pos,
                tree=self.tree,
                line=self.line,
                pipe=self.pipe,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type and
                self.pos == other.pos and
                self.tree == other.tree and
                self.line == other.line and
                self.pipe == other.pipe
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            type: __dataclass__init__fields__0__annotation,
            pos: __dataclass__init__fields__1__annotation,
            tree: __dataclass__init__fields__2__annotation,
            line: __dataclass__init__fields__3__annotation,
            pipe: __dataclass__init__fields__4__annotation,
        ) -> __dataclass__None:
            self.type = type
            self.pos = pos
            self.tree = tree
            self.line = line
            self.pipe = pipe

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"type={self.type!r}")
            parts.append(f"pos={self.pos!r}")
            parts.append(f"tree={self.tree!r}")
            parts.append(f"line={self.line!r}")
            parts.append(f"pipe={self.pipe!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='21ae466e132ff78286b44330a1f090247e77ca41',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('type', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('pos', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('tree', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('is_true', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.gotmpl.nodes', 'BoolNode'),
    ),
)
def _process_dataclass__21ae466e132ff78286b44330a1f090247e77ca41():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                type=self.type,
                pos=self.pos,
                tree=self.tree,
                is_true=self.is_true,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type and
                self.pos == other.pos and
                self.tree == other.tree and
                self.is_true == other.is_true
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            type: __dataclass__init__fields__0__annotation,
            pos: __dataclass__init__fields__1__annotation,
            tree: __dataclass__init__fields__2__annotation,
            is_true: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            self.type = type
            self.pos = pos
            self.tree = tree
            self.is_true = is_true

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"type={self.type!r}")
            parts.append(f"pos={self.pos!r}")
            parts.append(f"tree={self.tree!r}")
            parts.append(f"is_true={self.is_true!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='9b04159c0996c2b95585ab56d24e0f5e38fdbefd',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('type', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('pos', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('tree', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('line', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('pipe', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('lst', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('else_lst', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.gotmpl.nodes', 'BranchNode'),
        ('omxtra.text.gotmpl.nodes', 'IfNode'),
        ('omxtra.text.gotmpl.nodes', 'RangeNode'),
        ('omxtra.text.gotmpl.nodes', 'WithNode'),
    ),
)
def _process_dataclass__9b04159c0996c2b95585ab56d24e0f5e38fdbefd():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                type=self.type,
                pos=self.pos,
                tree=self.tree,
                line=self.line,
                pipe=self.pipe,
                lst=self.lst,
                else_lst=self.else_lst,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type and
                self.pos == other.pos and
                self.tree == other.tree and
                self.line == other.line and
                self.pipe == other.pipe and
                self.lst == other.lst and
                self.else_lst == other.else_lst
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            type: __dataclass__init__fields__0__annotation,
            pos: __dataclass__init__fields__1__annotation,
            tree: __dataclass__init__fields__2__annotation,
            line: __dataclass__init__fields__3__annotation,
            pipe: __dataclass__init__fields__4__annotation,
            lst: __dataclass__init__fields__5__annotation,
            else_lst: __dataclass__init__fields__6__annotation,
        ) -> __dataclass__None:
            self.type = type
            self.pos = pos
            self.tree = tree
            self.line = line
            self.pipe = pipe
            self.lst = lst
            self.else_lst = else_lst

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"type={self.type!r}")
            parts.append(f"pos={self.pos!r}")
            parts.append(f"tree={self.tree!r}")
            parts.append(f"line={self.line!r}")
            parts.append(f"pipe={self.pipe!r}")
            parts.append(f"lst={self.lst!r}")
            parts.append(f"else_lst={self.else_lst!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='4ea8546dbad5698723314eee16de52090763c867',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('type', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('pos', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('tree', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('line', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.gotmpl.nodes', 'BreakNode'),
        ('omxtra.text.gotmpl.nodes', 'ContinueNode'),
        ('omxtra.text.gotmpl.nodes', 'ElseNode'),
    ),
)
def _process_dataclass__4ea8546dbad5698723314eee16de52090763c867():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                type=self.type,
                pos=self.pos,
                tree=self.tree,
                line=self.line,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type and
                self.pos == other.pos and
                self.tree == other.tree and
                self.line == other.line
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            type: __dataclass__init__fields__0__annotation,
            pos: __dataclass__init__fields__1__annotation,
            tree: __dataclass__init__fields__2__annotation,
            line: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            self.type = type
            self.pos = pos
            self.tree = tree
            self.line = line

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"type={self.type!r}")
            parts.append(f"pos={self.pos!r}")
            parts.append(f"tree={self.tree!r}")
            parts.append(f"line={self.line!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='37a56a79ea598fca4ea73119a3f98c9b46958f86',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('type', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('pos', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('tree', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('node', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('field', True, True, None, True, False, False, None), 'instance', 'factory', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.gotmpl.nodes', 'ChainNode'),
    ),
)
def _process_dataclass__37a56a79ea598fca4ea73119a3f98c9b46958f86():
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
        __dataclass__init__fields__4__default_factory = __dataclass__spec.fields[4].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                type=self.type,
                pos=self.pos,
                tree=self.tree,
                node=self.node,
                field=self.field,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type and
                self.pos == other.pos and
                self.tree == other.tree and
                self.node == other.node and
                self.field == other.field
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            type: __dataclass__init__fields__0__annotation,
            pos: __dataclass__init__fields__1__annotation,
            tree: __dataclass__init__fields__2__annotation,
            node: __dataclass__init__fields__3__annotation,
            field: __dataclass__init__fields__4__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if field is __dataclass__HAS_DEFAULT_FACTORY:
                field = __dataclass__init__fields__4__default_factory()
            self.type = type
            self.pos = pos
            self.tree = tree
            self.node = node
            self.field = field

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"type={self.type!r}")
            parts.append(f"pos={self.pos!r}")
            parts.append(f"tree={self.tree!r}")
            parts.append(f"node={self.node!r}")
            parts.append(f"field={self.field!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e35650de2e9bfe512d9b24eeabdb2ab9516a0a81',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('type', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('pos', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('tree', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('args', True, True, None, True, False, False, None), 'instance', 'factory', N"
            "one, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.gotmpl.nodes', 'CommandNode'),
    ),
)
def _process_dataclass__e35650de2e9bfe512d9b24eeabdb2ab9516a0a81():
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
        __dataclass__init__fields__3__default_factory = __dataclass__spec.fields[3].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                type=self.type,
                pos=self.pos,
                tree=self.tree,
                args=self.args,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type and
                self.pos == other.pos and
                self.tree == other.tree and
                self.args == other.args
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            type: __dataclass__init__fields__0__annotation,
            pos: __dataclass__init__fields__1__annotation,
            tree: __dataclass__init__fields__2__annotation,
            args: __dataclass__init__fields__3__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if args is __dataclass__HAS_DEFAULT_FACTORY:
                args = __dataclass__init__fields__3__default_factory()
            self.type = type
            self.pos = pos
            self.tree = tree
            self.args = args

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"type={self.type!r}")
            parts.append(f"pos={self.pos!r}")
            parts.append(f"tree={self.tree!r}")
            parts.append(f"args={self.args!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='946ca2e8e831ed4a11de714dc3f597f6cf5d99dc',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('type', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('pos', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('tree', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('text', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.gotmpl.nodes', 'CommentNode'),
        ('omxtra.text.gotmpl.nodes', 'TextNode'),
    ),
)
def _process_dataclass__946ca2e8e831ed4a11de714dc3f597f6cf5d99dc():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                type=self.type,
                pos=self.pos,
                tree=self.tree,
                text=self.text,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type and
                self.pos == other.pos and
                self.tree == other.tree and
                self.text == other.text
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            type: __dataclass__init__fields__0__annotation,
            pos: __dataclass__init__fields__1__annotation,
            tree: __dataclass__init__fields__2__annotation,
            text: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            self.type = type
            self.pos = pos
            self.tree = tree
            self.text = text

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"type={self.type!r}")
            parts.append(f"pos={self.pos!r}")
            parts.append(f"tree={self.tree!r}")
            parts.append(f"text={self.text!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='864b2a02b3155f51fe0f0abe95ac8eb32ed8ee22',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('type', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('pos', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('tree', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.gotmpl.nodes', 'DotNode'),
        ('omxtra.text.gotmpl.nodes', 'EndNode'),
        ('omxtra.text.gotmpl.nodes', 'NilNode'),
        ('omxtra.text.gotmpl.nodes', 'Node'),
    ),
)
def _process_dataclass__864b2a02b3155f51fe0f0abe95ac8eb32ed8ee22():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                type=self.type,
                pos=self.pos,
                tree=self.tree,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type and
                self.pos == other.pos and
                self.tree == other.tree
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            type: __dataclass__init__fields__0__annotation,
            pos: __dataclass__init__fields__1__annotation,
            tree: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            self.type = type
            self.pos = pos
            self.tree = tree

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"type={self.type!r}")
            parts.append(f"pos={self.pos!r}")
            parts.append(f"tree={self.tree!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='1d4d5ade19781a4ed4687bc7c251eecf987adf39',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('type', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('pos', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('tree', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('ident', True, True, None, True, False, False, None), 'instance', 'factory', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.gotmpl.nodes', 'FieldNode'),
    ),
)
def _process_dataclass__1d4d5ade19781a4ed4687bc7c251eecf987adf39():
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
        __dataclass__init__fields__3__default_factory = __dataclass__spec.fields[3].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                type=self.type,
                pos=self.pos,
                tree=self.tree,
                ident=self.ident,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type and
                self.pos == other.pos and
                self.tree == other.tree and
                self.ident == other.ident
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            type: __dataclass__init__fields__0__annotation,
            pos: __dataclass__init__fields__1__annotation,
            tree: __dataclass__init__fields__2__annotation,
            ident: __dataclass__init__fields__3__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if ident is __dataclass__HAS_DEFAULT_FACTORY:
                ident = __dataclass__init__fields__3__default_factory()
            self.type = type
            self.pos = pos
            self.tree = tree
            self.ident = ident

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"type={self.type!r}")
            parts.append(f"pos={self.pos!r}")
            parts.append(f"tree={self.tree!r}")
            parts.append(f"ident={self.ident!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='210a2d0e4d593f360cacaf8d7d39ffd636203849',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('type', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('pos', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('tree', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('ident', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.gotmpl.nodes', 'IdentifierNode'),
        ('omxtra.text.gotmpl.nodes', 'VariableNode'),
    ),
)
def _process_dataclass__210a2d0e4d593f360cacaf8d7d39ffd636203849():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                type=self.type,
                pos=self.pos,
                tree=self.tree,
                ident=self.ident,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type and
                self.pos == other.pos and
                self.tree == other.tree and
                self.ident == other.ident
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            type: __dataclass__init__fields__0__annotation,
            pos: __dataclass__init__fields__1__annotation,
            tree: __dataclass__init__fields__2__annotation,
            ident: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            self.type = type
            self.pos = pos
            self.tree = tree
            self.ident = ident

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"type={self.type!r}")
            parts.append(f"pos={self.pos!r}")
            parts.append(f"tree={self.tree!r}")
            parts.append(f"ident={self.ident!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='ef9884c55cf32431054fe5f9dcf2dcd99c12f3e5',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('type', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('pos', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('tree', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('nodes', True, True, None, True, False, False, None), 'instance', 'factory', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.gotmpl.nodes', 'ListNode'),
    ),
)
def _process_dataclass__ef9884c55cf32431054fe5f9dcf2dcd99c12f3e5():
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
        __dataclass__init__fields__3__default_factory = __dataclass__spec.fields[3].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                type=self.type,
                pos=self.pos,
                tree=self.tree,
                nodes=self.nodes,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type and
                self.pos == other.pos and
                self.tree == other.tree and
                self.nodes == other.nodes
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            type: __dataclass__init__fields__0__annotation,
            pos: __dataclass__init__fields__1__annotation,
            tree: __dataclass__init__fields__2__annotation,
            nodes: __dataclass__init__fields__3__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if nodes is __dataclass__HAS_DEFAULT_FACTORY:
                nodes = __dataclass__init__fields__3__default_factory()
            self.type = type
            self.pos = pos
            self.tree = tree
            self.nodes = nodes

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"type={self.type!r}")
            parts.append(f"pos={self.pos!r}")
            parts.append(f"tree={self.tree!r}")
            parts.append(f"nodes={self.nodes!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='2e480dd8cc80921513cba8f9169b9c81ea2c17ed',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('type', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('pos', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('tree', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('text', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('is_int', True, True, None, True, False, False, None), 'instance', 'value', N"
            "one, False, False, False), (('is_uint', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('is_float', True, True, None, True, False, False, None), 'instance', 'value'"
            ", None, False, False, False), (('is_complex', True, True, None, True, False, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('int64', True, True, None, True, False, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('uint64', True, True, None, True, False, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('float64', True, True, None, True, False, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('complex128', True, True, None, True, False, False, None), 'instance',"
            " 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()"
            "), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.gotmpl.nodes', 'NumberNode'),
    ),
)
def _process_dataclass__2e480dd8cc80921513cba8f9169b9c81ea2c17ed():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                type=self.type,
                pos=self.pos,
                tree=self.tree,
                text=self.text,
                is_int=self.is_int,
                is_uint=self.is_uint,
                is_float=self.is_float,
                is_complex=self.is_complex,
                int64=self.int64,
                uint64=self.uint64,
                float64=self.float64,
                complex128=self.complex128,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type and
                self.pos == other.pos and
                self.tree == other.tree and
                self.text == other.text and
                self.is_int == other.is_int and
                self.is_uint == other.is_uint and
                self.is_float == other.is_float and
                self.is_complex == other.is_complex and
                self.int64 == other.int64 and
                self.uint64 == other.uint64 and
                self.float64 == other.float64 and
                self.complex128 == other.complex128
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            type: __dataclass__init__fields__00__annotation,
            pos: __dataclass__init__fields__01__annotation,
            tree: __dataclass__init__fields__02__annotation,
            text: __dataclass__init__fields__03__annotation,
            is_int: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            is_uint: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            is_float: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            is_complex: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            int64: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            uint64: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            float64: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            complex128: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
        ) -> __dataclass__None:
            self.type = type
            self.pos = pos
            self.tree = tree
            self.text = text
            self.is_int = is_int
            self.is_uint = is_uint
            self.is_float = is_float
            self.is_complex = is_complex
            self.int64 = int64
            self.uint64 = uint64
            self.float64 = float64
            self.complex128 = complex128

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"type={self.type!r}")
            parts.append(f"pos={self.pos!r}")
            parts.append(f"tree={self.tree!r}")
            parts.append(f"text={self.text!r}")
            parts.append(f"is_int={self.is_int!r}")
            parts.append(f"is_uint={self.is_uint!r}")
            parts.append(f"is_float={self.is_float!r}")
            parts.append(f"is_complex={self.is_complex!r}")
            parts.append(f"int64={self.int64!r}")
            parts.append(f"uint64={self.uint64!r}")
            parts.append(f"float64={self.float64!r}")
            parts.append(f"complex128={self.complex128!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c23259157ad30a8e4a377e2ddfa51d2dfc527c25',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('type', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('pos', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('tree', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('line', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('is_assign', True, True, None, True, False, False, None), 'instance', 'value'"
            ", None, False, False, False), (('decl', True, True, None, True, False, False, None), 'instance', 'factory'"
            ", None, False, False, False), (('cmds', True, True, None, True, False, False, None), 'instance', 'factory'"
            ", None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.gotmpl.nodes', 'PipeNode'),
    ),
)
def _process_dataclass__c23259157ad30a8e4a377e2ddfa51d2dfc527c25():
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
                type=self.type,
                pos=self.pos,
                tree=self.tree,
                line=self.line,
                is_assign=self.is_assign,
                decl=self.decl,
                cmds=self.cmds,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type and
                self.pos == other.pos and
                self.tree == other.tree and
                self.line == other.line and
                self.is_assign == other.is_assign and
                self.decl == other.decl and
                self.cmds == other.cmds
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            type: __dataclass__init__fields__0__annotation,
            pos: __dataclass__init__fields__1__annotation,
            tree: __dataclass__init__fields__2__annotation,
            line: __dataclass__init__fields__3__annotation,
            is_assign: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            decl: __dataclass__init__fields__5__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            cmds: __dataclass__init__fields__6__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if decl is __dataclass__HAS_DEFAULT_FACTORY:
                decl = __dataclass__init__fields__5__default_factory()
            if cmds is __dataclass__HAS_DEFAULT_FACTORY:
                cmds = __dataclass__init__fields__6__default_factory()
            self.type = type
            self.pos = pos
            self.tree = tree
            self.line = line
            self.is_assign = is_assign
            self.decl = decl
            self.cmds = cmds

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"type={self.type!r}")
            parts.append(f"pos={self.pos!r}")
            parts.append(f"tree={self.tree!r}")
            parts.append(f"line={self.line!r}")
            parts.append(f"is_assign={self.is_assign!r}")
            parts.append(f"decl={self.decl!r}")
            parts.append(f"cmds={self.cmds!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='46602c3c54508d1120bc8883cc0da2c0de2d111f',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('type', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('pos', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('tree', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('quoted', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('text', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.gotmpl.nodes', 'StringNode'),
    ),
)
def _process_dataclass__46602c3c54508d1120bc8883cc0da2c0de2d111f():
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
                type=self.type,
                pos=self.pos,
                tree=self.tree,
                quoted=self.quoted,
                text=self.text,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type and
                self.pos == other.pos and
                self.tree == other.tree and
                self.quoted == other.quoted and
                self.text == other.text
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            type: __dataclass__init__fields__0__annotation,
            pos: __dataclass__init__fields__1__annotation,
            tree: __dataclass__init__fields__2__annotation,
            quoted: __dataclass__init__fields__3__annotation,
            text: __dataclass__init__fields__4__annotation,
        ) -> __dataclass__None:
            self.type = type
            self.pos = pos
            self.tree = tree
            self.quoted = quoted
            self.text = text

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"type={self.type!r}")
            parts.append(f"pos={self.pos!r}")
            parts.append(f"tree={self.tree!r}")
            parts.append(f"quoted={self.quoted!r}")
            parts.append(f"text={self.text!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='81717b1787ada081182a88dcc93e6d3300b19c89',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('type', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('pos', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('tree', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('line', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('name', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('pipe', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.gotmpl.nodes', 'TemplateNode'),
    ),
)
def _process_dataclass__81717b1787ada081182a88dcc93e6d3300b19c89():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                type=self.type,
                pos=self.pos,
                tree=self.tree,
                line=self.line,
                name=self.name,
                pipe=self.pipe,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type and
                self.pos == other.pos and
                self.tree == other.tree and
                self.line == other.line and
                self.name == other.name and
                self.pipe == other.pipe
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            type: __dataclass__init__fields__0__annotation,
            pos: __dataclass__init__fields__1__annotation,
            tree: __dataclass__init__fields__2__annotation,
            line: __dataclass__init__fields__3__annotation,
            name: __dataclass__init__fields__4__annotation,
            pipe: __dataclass__init__fields__5__annotation,
        ) -> __dataclass__None:
            self.type = type
            self.pos = pos
            self.tree = tree
            self.line = line
            self.name = name
            self.pipe = pipe

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"type={self.type!r}")
            parts.append(f"pos={self.pos!r}")
            parts.append(f"tree={self.tree!r}")
            parts.append(f"line={self.line!r}")
            parts.append(f"name={self.name!r}")
            parts.append(f"pipe={self.pipe!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='6cbce590bb308e379913d1d0c5db66470907a84c',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, True, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('tmpl', True, True, None, True, True, False, None), 'instance', 'factory', No"
            "ne, False, False, False), (('tmpl_lock', True, False, None, True, True, False, None), 'instance', 'factory"
            "', None, False, False, False), (('option', True, True, None, True, True, False, None), 'instance', 'factor"
            "y', None, False, False, False), (('parse_funcs', True, True, None, True, True, False, None), 'instance', '"
            "factory', None, False, False, False), (('exec_funcs', True, True, None, True, True, False, None), 'instanc"
            "e', 'factory', None, False, False, False), (('funcs_lock', True, False, None, True, True, False, None), 'i"
            "nstance', 'factory', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False"
            ", False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.gotmpl.tmpl', 'Common'),
    ),
)
def _process_dataclass__6cbce590bb308e379913d1d0c5db66470907a84c():
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
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                tmpl=self.tmpl,
                tmpl_lock=self.tmpl_lock,
                option=self.option,
                parse_funcs=self.parse_funcs,
                exec_funcs=self.exec_funcs,
                funcs_lock=self.funcs_lock,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.tmpl == other.tmpl and
                self.tmpl_lock == other.tmpl_lock and
                self.option == other.option and
                self.parse_funcs == other.parse_funcs and
                self.exec_funcs == other.exec_funcs and
                self.funcs_lock == other.funcs_lock
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            *,
            tmpl: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            tmpl_lock: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            option: __dataclass__init__fields__2__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            parse_funcs: __dataclass__init__fields__3__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            exec_funcs: __dataclass__init__fields__4__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            funcs_lock: __dataclass__init__fields__5__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if tmpl is __dataclass__HAS_DEFAULT_FACTORY:
                tmpl = __dataclass__init__fields__0__default_factory()
            if tmpl_lock is __dataclass__HAS_DEFAULT_FACTORY:
                tmpl_lock = __dataclass__init__fields__1__default_factory()
            if option is __dataclass__HAS_DEFAULT_FACTORY:
                option = __dataclass__init__fields__2__default_factory()
            if parse_funcs is __dataclass__HAS_DEFAULT_FACTORY:
                parse_funcs = __dataclass__init__fields__3__default_factory()
            if exec_funcs is __dataclass__HAS_DEFAULT_FACTORY:
                exec_funcs = __dataclass__init__fields__4__default_factory()
            if funcs_lock is __dataclass__HAS_DEFAULT_FACTORY:
                funcs_lock = __dataclass__init__fields__5__default_factory()
            self.tmpl = tmpl
            self.tmpl_lock = tmpl_lock
            self.option = option
            self.parse_funcs = parse_funcs
            self.exec_funcs = exec_funcs
            self.funcs_lock = funcs_lock

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"tmpl={self.tmpl!r}")
            parts.append(f"option={self.option!r}")
            parts.append(f"parse_funcs={self.parse_funcs!r}")
            parts.append(f"exec_funcs={self.exec_funcs!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='149d817b187c548385b5ef1f604df89bcc337a81',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('missing_key', True, True, None, True, False, False, None), 'instance', 'val"
            "ue', None, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ("
            "(),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omxtra.text.gotmpl.tmpl', 'Option'),
    ),
)
def _process_dataclass__149d817b187c548385b5ef1f604df89bcc337a81():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default = __dataclass__spec.fields[0].default.must()
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                missing_key=self.missing_key,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.missing_key == other.missing_key
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            missing_key: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
        ) -> __dataclass__None:
            self.missing_key = missing_key

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"missing_key={self.missing_key!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
