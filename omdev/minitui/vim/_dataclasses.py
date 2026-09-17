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


IMPLEMENTATION_KEY = '0bbef0e54293e6dab1d0e699c31ca637b42078baf288201f600000b591c92b24'


@_register(
    installer_sha1='b6c196a8b667f5d194d90ea460a2d1b1853c92a7',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('edits', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('cursor_before', True, True, None, True, False, False, None), 'instance', 'm"
            "issing', None, False, False, False), (('cursor_after', True, True, None, True, False, False, None), 'insta"
            "nce', 'missing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, Fa"
            "lse, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.minitui.vim.engine', '_UndoEntry'),
    ),
)
def _process_dataclass__b6c196a8b667f5d194d90ea460a2d1b1853c92a7():
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
                edits=self.edits,
                cursor_before=self.cursor_before,
                cursor_after=self.cursor_after,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.edits == other.edits and
                self.cursor_before == other.cursor_before and
                self.cursor_after == other.cursor_after
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'edits',
            'cursor_before',
            'cursor_after',
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
                self.edits,
                self.cursor_before,
                self.cursor_after,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            edits: __dataclass__init__fields__0__annotation,
            cursor_before: __dataclass__init__fields__1__annotation,
            cursor_after: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'edits', edits)
            __dataclass__object_setattr(self, 'cursor_before', cursor_before)
            __dataclass__object_setattr(self, 'cursor_after', cursor_after)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"edits={self.edits!r}")
            parts.append(f"cursor_before={self.cursor_before!r}")
            parts.append(f"cursor_after={self.cursor_after!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='fc97faf1cd4ed944e937870b4fdf8b7b71f23e3d',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('target', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('kind', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('keeps_curswant', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False), (('to_first_nonblank', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('curswant_eol', True, True, None, True, True, False, None)"
            ", 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (Fal"
            "se, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.minitui.vim.motions', 'MotionResult'),
    ),
)
def _process_dataclass__fc97faf1cd4ed944e937870b4fdf8b7b71f23e3d():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                target=self.target,
                kind=self.kind,
                keeps_curswant=self.keeps_curswant,
                to_first_nonblank=self.to_first_nonblank,
                curswant_eol=self.curswant_eol,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.target == other.target and
                self.kind == other.kind and
                self.keeps_curswant == other.keeps_curswant and
                self.to_first_nonblank == other.to_first_nonblank and
                self.curswant_eol == other.curswant_eol
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'target',
            'kind',
            'keeps_curswant',
            'to_first_nonblank',
            'curswant_eol',
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
                self.kind,
                self.keeps_curswant,
                self.to_first_nonblank,
                self.curswant_eol,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            target: __dataclass__init__fields__0__annotation,
            kind: __dataclass__init__fields__1__annotation,
            *,
            keeps_curswant: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            to_first_nonblank: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            curswant_eol: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'target', target)
            __dataclass__object_setattr(self, 'kind', kind)
            __dataclass__object_setattr(self, 'keeps_curswant', keeps_curswant)
            __dataclass__object_setattr(self, 'to_first_nonblank', to_first_nonblank)
            __dataclass__object_setattr(self, 'curswant_eol', curswant_eol)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"target={self.target!r}")
            parts.append(f"kind={self.kind!r}")
            parts.append(f"keeps_curswant={self.keeps_curswant!r}")
            parts.append(f"to_first_nonblank={self.to_first_nonblank!r}")
            parts.append(f"curswant_eol={self.curswant_eol!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='026afb5d024e07e4ec6d695e2bef612a0037cfa4',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('tabstop', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('shiftwidth', True, True, None, True, False, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('expandtab', True, True, None, True, False, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('autoindent', True, True, None, True, False, False, None), 'instance'"
            ", 'value', None, False, False, False), (('number', True, True, None, True, False, False, None), 'instance'"
            ", 'value', None, False, False, False), (('numberwidth', True, True, None, True, False, False, None), 'inst"
            "ance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, Fal"
            "se, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.minitui.vim.options', 'VimOptions'),
    ),
)
def _process_dataclass__026afb5d024e07e4ec6d695e2bef612a0037cfa4():
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
                tabstop=self.tabstop,
                shiftwidth=self.shiftwidth,
                expandtab=self.expandtab,
                autoindent=self.autoindent,
                number=self.number,
                numberwidth=self.numberwidth,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.tabstop == other.tabstop and
                self.shiftwidth == other.shiftwidth and
                self.expandtab == other.expandtab and
                self.autoindent == other.autoindent and
                self.number == other.number and
                self.numberwidth == other.numberwidth
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'tabstop',
            'shiftwidth',
            'expandtab',
            'autoindent',
            'number',
            'numberwidth',
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
                self.tabstop,
                self.shiftwidth,
                self.expandtab,
                self.autoindent,
                self.number,
                self.numberwidth,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            tabstop: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            shiftwidth: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            expandtab: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            autoindent: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            number: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            numberwidth: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'tabstop', tabstop)
            __dataclass__object_setattr(self, 'shiftwidth', shiftwidth)
            __dataclass__object_setattr(self, 'expandtab', expandtab)
            __dataclass__object_setattr(self, 'autoindent', autoindent)
            __dataclass__object_setattr(self, 'number', number)
            __dataclass__object_setattr(self, 'numberwidth', numberwidth)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"tabstop={self.tabstop!r}")
            parts.append(f"shiftwidth={self.shiftwidth!r}")
            parts.append(f"expandtab={self.expandtab!r}")
            parts.append(f"autoindent={self.autoindent!r}")
            parts.append(f"number={self.number!r}")
            parts.append(f"numberwidth={self.numberwidth!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='1cd6c360edd454d5ccf62c215864d63b48219312',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('register', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('count', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('has_count', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('op', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False), (('doubled', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False), (('motion_key', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('motion_arg', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('tobj', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('action', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('action_arg', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.minitui.vim.parsing', 'Command'),
    ),
)
def _process_dataclass__1cd6c360edd454d5ccf62c215864d63b48219312():
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
                register=self.register,
                count=self.count,
                has_count=self.has_count,
                op=self.op,
                doubled=self.doubled,
                motion_key=self.motion_key,
                motion_arg=self.motion_arg,
                tobj=self.tobj,
                action=self.action,
                action_arg=self.action_arg,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.register == other.register and
                self.count == other.count and
                self.has_count == other.has_count and
                self.op == other.op and
                self.doubled == other.doubled and
                self.motion_key == other.motion_key and
                self.motion_arg == other.motion_arg and
                self.tobj == other.tobj and
                self.action == other.action and
                self.action_arg == other.action_arg
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'register',
            'count',
            'has_count',
            'op',
            'doubled',
            'motion_key',
            'motion_arg',
            'tobj',
            'action',
            'action_arg',
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
                self.register,
                self.count,
                self.has_count,
                self.op,
                self.doubled,
                self.motion_key,
                self.motion_arg,
                self.tobj,
                self.action,
                self.action_arg,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            register: __dataclass__init__fields__00__annotation = __dataclass__init__fields__00__default,
            count: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            has_count: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            op: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            doubled: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            motion_key: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            motion_arg: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            tobj: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            action: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            action_arg: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'register', register)
            __dataclass__object_setattr(self, 'count', count)
            __dataclass__object_setattr(self, 'has_count', has_count)
            __dataclass__object_setattr(self, 'op', op)
            __dataclass__object_setattr(self, 'doubled', doubled)
            __dataclass__object_setattr(self, 'motion_key', motion_key)
            __dataclass__object_setattr(self, 'motion_arg', motion_arg)
            __dataclass__object_setattr(self, 'tobj', tobj)
            __dataclass__object_setattr(self, 'action', action)
            __dataclass__object_setattr(self, 'action_arg', action_arg)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"register={self.register!r}")
            parts.append(f"count={self.count!r}")
            parts.append(f"has_count={self.has_count!r}")
            parts.append(f"op={self.op!r}")
            parts.append(f"doubled={self.doubled!r}")
            parts.append(f"motion_key={self.motion_key!r}")
            parts.append(f"motion_arg={self.motion_arg!r}")
            parts.append(f"tobj={self.tobj!r}")
            parts.append(f"action={self.action!r}")
            parts.append(f"action_arg={self.action_arg!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='6ee8ba7554e80f4063a9756b779217bcdb575389',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('pieces', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('kind', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.minitui.vim.registers', 'RegValue'),
    ),
)
def _process_dataclass__6ee8ba7554e80f4063a9756b779217bcdb575389():
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
                pieces=self.pieces,
                kind=self.kind,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.pieces == other.pieces and
                self.kind == other.kind
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'pieces',
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

        def __hash__(self):
            return hash((
                self.pieces,
                self.kind,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            pieces: __dataclass__init__fields__0__annotation,
            kind: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'pieces', pieces)
            __dataclass__object_setattr(self, 'kind', kind)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"pieces={self.pieces!r}")
            parts.append(f"kind={self.kind!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e5bf9be8d48b02177ee763afec7b6a832d858b0d',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('span', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('tag', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.minitui.vim.status', 'Decoration'),
    ),
)
def _process_dataclass__e5bf9be8d48b02177ee763afec7b6a832d858b0d():
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
                span=self.span,
                tag=self.tag,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.span == other.span and
                self.tag == other.tag
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'span',
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
                self.span,
                self.tag,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            span: __dataclass__init__fields__0__annotation,
            tag: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'span', span)
            __dataclass__object_setattr(self, 'tag', tag)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"span={self.span!r}")
            parts.append(f"tag={self.tag!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='3b0eb3b68357b5defd522ed5674fe0a704e705f6',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('mode', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('pending', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('cmdline', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('message', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('cursor_count', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.minitui.vim.status', 'VimStatus'),
    ),
)
def _process_dataclass__3b0eb3b68357b5defd522ed5674fe0a704e705f6():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                mode=self.mode,
                pending=self.pending,
                cmdline=self.cmdline,
                message=self.message,
                cursor_count=self.cursor_count,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.mode == other.mode and
                self.pending == other.pending and
                self.cmdline == other.cmdline and
                self.message == other.message and
                self.cursor_count == other.cursor_count
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'mode',
            'pending',
            'cmdline',
            'message',
            'cursor_count',
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
                self.mode,
                self.pending,
                self.cmdline,
                self.message,
                self.cursor_count,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            mode: __dataclass__init__fields__0__annotation,
            pending: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            cmdline: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            message: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            cursor_count: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'mode', mode)
            __dataclass__object_setattr(self, 'pending', pending)
            __dataclass__object_setattr(self, 'cmdline', cmdline)
            __dataclass__object_setattr(self, 'message', message)
            __dataclass__object_setattr(self, 'cursor_count', cursor_count)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"mode={self.mode!r}")
            parts.append(f"pending={self.pending!r}")
            parts.append(f"cmdline={self.cmdline!r}")
            parts.append(f"message={self.message!r}")
            parts.append(f"cursor_count={self.cursor_count!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='7eaf9d567a663637ab745102e7f879c735b08b55',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('start_row', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('end_row', True, True, None, True, False, False, None), 'instance', 'mis"
            "sing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), "
            "((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.minitui.vim.substitutes', 'ExRange'),
    ),
)
def _process_dataclass__7eaf9d567a663637ab745102e7f879c735b08b55():
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
                start_row=self.start_row,
                end_row=self.end_row,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.start_row == other.start_row and
                self.end_row == other.end_row
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'start_row',
            'end_row',
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
                self.start_row,
                self.end_row,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            start_row: __dataclass__init__fields__0__annotation,
            end_row: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'start_row', start_row)
            __dataclass__object_setattr(self, 'end_row', end_row)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"start_row={self.start_row!r}")
            parts.append(f"end_row={self.end_row!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='2d7b7e4322041c9edc9442c6effcd3316d0177ea',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('replaced', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('lines', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('last_row', True, True, None, True, False, False, None), 'instance', 'mi"
            "ssing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()),"
            " ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.minitui.vim.substitutes', 'SubstituteResult'),
    ),
)
def _process_dataclass__2d7b7e4322041c9edc9442c6effcd3316d0177ea():
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
                replaced=self.replaced,
                lines=self.lines,
                last_row=self.last_row,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.replaced == other.replaced and
                self.lines == other.lines and
                self.last_row == other.last_row
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'replaced',
            'lines',
            'last_row',
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
                self.replaced,
                self.lines,
                self.last_row,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            replaced: __dataclass__init__fields__0__annotation,
            lines: __dataclass__init__fields__1__annotation,
            last_row: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'replaced', replaced)
            __dataclass__object_setattr(self, 'lines', lines)
            __dataclass__object_setattr(self, 'last_row', last_row)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"replaced={self.replaced!r}")
            parts.append(f"lines={self.lines!r}")
            parts.append(f"last_row={self.last_row!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='33ade4706fff818fd2a01d9297318d5153143dff',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('pattern', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('replacement', True, True, None, True, False, False, None), 'instance', 'm"
            "issing', None, False, False, False), (('every', True, True, None, True, False, False, None), 'instance', '"
            "value', None, False, False, False), (('ignore_case', True, True, None, True, False, False, None), 'instanc"
            "e', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False,"
            " ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.minitui.vim.substitutes', 'SubstituteSpec'),
    ),
)
def _process_dataclass__33ade4706fff818fd2a01d9297318d5153143dff():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                pattern=self.pattern,
                replacement=self.replacement,
                every=self.every,
                ignore_case=self.ignore_case,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.pattern == other.pattern and
                self.replacement == other.replacement and
                self.every == other.every and
                self.ignore_case == other.ignore_case
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'pattern',
            'replacement',
            'every',
            'ignore_case',
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
                self.pattern,
                self.replacement,
                self.every,
                self.ignore_case,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            pattern: __dataclass__init__fields__0__annotation,
            replacement: __dataclass__init__fields__1__annotation,
            every: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            ignore_case: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'pattern', pattern)
            __dataclass__object_setattr(self, 'replacement', replacement)
            __dataclass__object_setattr(self, 'every', every)
            __dataclass__object_setattr(self, 'ignore_case', ignore_case)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"pattern={self.pattern!r}")
            parts.append(f"replacement={self.replacement!r}")
            parts.append(f"every={self.every!r}")
            parts.append(f"ignore_case={self.ignore_case!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
