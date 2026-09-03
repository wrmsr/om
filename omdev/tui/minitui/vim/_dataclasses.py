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
        "Plans(tup=(CopyPlan(fields=('edits', 'cursor_before', 'cursor_after')), EqPlan(fields=('edits', 'cursor_before"
        "', 'cursor_after')), FrozenPlan(fields=('edits', 'cursor_before', 'cursor_after'), allow_dynamic_dunder_attrs="
        "False), HashPlan(action='add', fields=('edits', 'cursor_before', 'cursor_after'), cache=False), InitPlan(field"
        "s=(InitPlan.Field(name='edits', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_facto"
        "ry=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None"
        "), InitPlan.Field(name='cursor_before', annotation=OpRef(name='init.fields.1.annotation'), default=None, defau"
        "lt_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_t"
        "ype=None), InitPlan.Field(name='cursor_after', annotation=OpRef(name='init.fields.2.annotation'), default=None"
        ", default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, "
        "check_type=None)), self_param='self', std_params=('edits', 'cursor_before', 'cursor_after'), kw_only_params=()"
        ", frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Fi"
        "eld(name='edits', kw_only=False, fn=None), ReprPlan.Field(name='cursor_before', kw_only=False, fn=None), ReprP"
        "lan.Field(name='cursor_after', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='d6accabbca152039e84e31966f08f2cecf66e911',
    cls_names=(
        ('omdev.tui.minitui.vim.engine', '_UndoEntry'),
    ),
)
def _process_dataclass__d6accabbca152039e84e31966f08f2cecf66e911():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('target', 'kind', 'keeps_curswant', 'to_first_nonblank', 'curswant_eol')), EqPlan("
        "fields=('target', 'kind', 'keeps_curswant', 'to_first_nonblank', 'curswant_eol')), FrozenPlan(fields=('target'"
        ", 'kind', 'keeps_curswant', 'to_first_nonblank', 'curswant_eol'), allow_dynamic_dunder_attrs=False), HashPlan("
        "action='add', fields=('target', 'kind', 'keeps_curswant', 'to_first_nonblank', 'curswant_eol'), cache=False), "
        "InitPlan(fields=(InitPlan.Field(name='target', annotation=OpRef(name='init.fields.0.annotation'), default=None"
        ", default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, "
        "check_type=None), InitPlan.Field(name='kind', annotation=OpRef(name='init.fields.1.annotation'), default=None,"
        " default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, c"
        "heck_type=None), InitPlan.Field(name='keeps_curswant', annotation=OpRef(name='init.fields.2.annotation'), defa"
        "ult=OpRef(name='init.fields.2.default'), default_factory=None, init=True, override=False, field_type=FieldType"
        ".INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='to_first_nonblank', annotation=O"
        "pRef(name='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default'), default_factory=None, init"
        "=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.F"
        "ield(name='curswant_eol', annotation=OpRef(name='init.fields.4.annotation'), default=OpRef(name='init.fields.4"
        ".default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, valid"
        "ate=None, check_type=None)), self_param='self', std_params=('target', 'kind'), kw_only_params=('keeps_curswant"
        "', 'to_first_nonblank', 'curswant_eol'), frozen=True, slots=False, post_init_params=None, init_fns=(), validat"
        "e_fns=()), ReprPlan(fields=(ReprPlan.Field(name='target', kw_only=False, fn=None), ReprPlan.Field(name='kind',"
        " kw_only=False, fn=None), ReprPlan.Field(name='keeps_curswant', kw_only=True, fn=None), ReprPlan.Field(name='t"
        "o_first_nonblank', kw_only=True, fn=None), ReprPlan.Field(name='curswant_eol', kw_only=True, fn=None)), id=Fal"
        "se, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='59d23a89b75e09cb04c128ef1ce8cd105c66a91b',
    cls_names=(
        ('omdev.tui.minitui.vim.motions', 'MotionResult'),
    ),
)
def _process_dataclass__59d23a89b75e09cb04c128ef1ce8cd105c66a91b():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__3__default,
        __dataclass__init__fields__4__annotation,
        __dataclass__init__fields__4__default,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('tabstop', 'shiftwidth', 'expandtab', 'autoindent', 'number', 'numberwidth')), EqP"
        "lan(fields=('tabstop', 'shiftwidth', 'expandtab', 'autoindent', 'number', 'numberwidth')), FrozenPlan(fields=("
        "'tabstop', 'shiftwidth', 'expandtab', 'autoindent', 'number', 'numberwidth'), allow_dynamic_dunder_attrs=False"
        "), HashPlan(action='add', fields=('tabstop', 'shiftwidth', 'expandtab', 'autoindent', 'number', 'numberwidth')"
        ", cache=False), InitPlan(fields=(InitPlan.Field(name='tabstop', annotation=OpRef(name='init.fields.0.annotatio"
        "n'), default=OpRef(name='init.fields.0.default'), default_factory=None, init=True, override=False, field_type="
        "FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='shiftwidth', annotation"
        "=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, in"
        "it=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan"
        ".Field(name='expandtab', annotation=OpRef(name='init.fields.2.annotation'), default=OpRef(name='init.fields.2."
        "default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, valida"
        "te=None, check_type=None), InitPlan.Field(name='autoindent', annotation=OpRef(name='init.fields.3.annotation')"
        ", default=OpRef(name='init.fields.3.default'), default_factory=None, init=True, override=False, field_type=Fie"
        "ldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='number', annotation=OpRef("
        "name='init.fields.4.annotation'), default=OpRef(name='init.fields.4.default'), default_factory=None, init=True"
        ", override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field("
        "name='numberwidth', annotation=OpRef(name='init.fields.5.annotation'), default=OpRef(name='init.fields.5.defau"
        "lt'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=No"
        "ne, check_type=None)), self_param='self', std_params=('tabstop', 'shiftwidth', 'expandtab', 'autoindent', 'num"
        "ber', 'numberwidth'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validat"
        "e_fns=()), ReprPlan(fields=(ReprPlan.Field(name='tabstop', kw_only=False, fn=None), ReprPlan.Field(name='shift"
        "width', kw_only=False, fn=None), ReprPlan.Field(name='expandtab', kw_only=False, fn=None), ReprPlan.Field(name"
        "='autoindent', kw_only=False, fn=None), ReprPlan.Field(name='number', kw_only=False, fn=None), ReprPlan.Field("
        "name='numberwidth', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='be9f15be09dba37e58af2e8a9ebf213913e2cd8a',
    cls_names=(
        ('omdev.tui.minitui.vim.options', 'VimOptions'),
    ),
)
def _process_dataclass__be9f15be09dba37e58af2e8a9ebf213913e2cd8a():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__default,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('register', 'count', 'has_count', 'op', 'doubled', 'motion_key', 'motion_arg', 'to"
        "bj', 'action', 'action_arg')), EqPlan(fields=('register', 'count', 'has_count', 'op', 'doubled', 'motion_key',"
        " 'motion_arg', 'tobj', 'action', 'action_arg')), FrozenPlan(fields=('register', 'count', 'has_count', 'op', 'd"
        "oubled', 'motion_key', 'motion_arg', 'tobj', 'action', 'action_arg'), allow_dynamic_dunder_attrs=False), HashP"
        "lan(action='add', fields=('register', 'count', 'has_count', 'op', 'doubled', 'motion_key', 'motion_arg', 'tobj"
        "', 'action', 'action_arg'), cache=False), InitPlan(fields=(InitPlan.Field(name='register', annotation=OpRef(na"
        "me='init.fields.00.annotation'), default=OpRef(name='init.fields.00.default'), default_factory=None, init=True"
        ", override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field("
        "name='count', annotation=OpRef(name='init.fields.01.annotation'), default=OpRef(name='init.fields.01.default')"
        ", default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, "
        "check_type=None), InitPlan.Field(name='has_count', annotation=OpRef(name='init.fields.02.annotation'), default"
        "=OpRef(name='init.fields.02.default'), default_factory=None, init=True, override=False, field_type=FieldType.I"
        "NSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='op', annotation=OpRef(name='init.f"
        "ields.03.annotation'), default=OpRef(name='init.fields.03.default'), default_factory=None, init=True, override"
        "=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='doub"
        "led', annotation=OpRef(name='init.fields.04.annotation'), default=OpRef(name='init.fields.04.default'), defaul"
        "t_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_ty"
        "pe=None), InitPlan.Field(name='motion_key', annotation=OpRef(name='init.fields.05.annotation'), default=OpRef("
        "name='init.fields.05.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE"
        ", coerce=None, validate=None, check_type=None), InitPlan.Field(name='motion_arg', annotation=OpRef(name='init."
        "fields.06.annotation'), default=OpRef(name='init.fields.06.default'), default_factory=None, init=True, overrid"
        "e=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='tob"
        "j', annotation=OpRef(name='init.fields.07.annotation'), default=OpRef(name='init.fields.07.default'), default_"
        "factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type"
        "=None), InitPlan.Field(name='action', annotation=OpRef(name='init.fields.08.annotation'), default=OpRef(name='"
        "init.fields.08.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coer"
        "ce=None, validate=None, check_type=None), InitPlan.Field(name='action_arg', annotation=OpRef(name='init.fields"
        ".09.annotation'), default=OpRef(name='init.fields.09.default'), default_factory=None, init=True, override=Fals"
        "e, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params"
        "=(), kw_only_params=('register', 'count', 'has_count', 'op', 'doubled', 'motion_key', 'motion_arg', 'tobj', 'a"
        "ction', 'action_arg'), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPla"
        "n(fields=(ReprPlan.Field(name='register', kw_only=True, fn=None), ReprPlan.Field(name='count', kw_only=True, f"
        "n=None), ReprPlan.Field(name='has_count', kw_only=True, fn=None), ReprPlan.Field(name='op', kw_only=True, fn=N"
        "one), ReprPlan.Field(name='doubled', kw_only=True, fn=None), ReprPlan.Field(name='motion_key', kw_only=True, f"
        "n=None), ReprPlan.Field(name='motion_arg', kw_only=True, fn=None), ReprPlan.Field(name='tobj', kw_only=True, f"
        "n=None), ReprPlan.Field(name='action', kw_only=True, fn=None), ReprPlan.Field(name='action_arg', kw_only=True,"
        " fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='aa8199857a99a28777023cf5d23898457a1ff553',
    cls_names=(
        ('omdev.tui.minitui.vim.parsing', 'Command'),
    ),
)
def _process_dataclass__aa8199857a99a28777023cf5d23898457a1ff553():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__00__annotation,
        __dataclass__init__fields__00__default,
        __dataclass__init__fields__01__annotation,
        __dataclass__init__fields__01__default,
        __dataclass__init__fields__02__annotation,
        __dataclass__init__fields__02__default,
        __dataclass__init__fields__03__annotation,
        __dataclass__init__fields__03__default,
        __dataclass__init__fields__04__annotation,
        __dataclass__init__fields__04__default,
        __dataclass__init__fields__05__annotation,
        __dataclass__init__fields__05__default,
        __dataclass__init__fields__06__annotation,
        __dataclass__init__fields__06__default,
        __dataclass__init__fields__07__annotation,
        __dataclass__init__fields__07__default,
        __dataclass__init__fields__08__annotation,
        __dataclass__init__fields__08__default,
        __dataclass__init__fields__09__annotation,
        __dataclass__init__fields__09__default,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('pieces', 'kind')), EqPlan(fields=('pieces', 'kind')), FrozenPlan(fields=('pieces'"
        ", 'kind'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('pieces', 'kind'), cache=False), "
        "InitPlan(fields=(InitPlan.Field(name='pieces', annotation=OpRef(name='init.fields.0.annotation'), default=None"
        ", default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, "
        "check_type=None), InitPlan.Field(name='kind', annotation=OpRef(name='init.fields.1.annotation'), default=None,"
        " default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, c"
        "heck_type=None)), self_param='self', std_params=('pieces', 'kind'), kw_only_params=(), frozen=True, slots=Fals"
        "e, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='pieces', kw_onl"
        "y=False, fn=None), ReprPlan.Field(name='kind', kw_only=False, fn=None)), id=False, terse=False, default_fn=Non"
        "e)))"
    ),
    plan_repr_sha1='3556feaaaf1f1d3b66b8011e0c76fb5779a694c9',
    cls_names=(
        ('omdev.tui.minitui.vim.registers', 'RegValue'),
    ),
)
def _process_dataclass__3556feaaaf1f1d3b66b8011e0c76fb5779a694c9():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('span', 'tag')), EqPlan(fields=('span', 'tag')), FrozenPlan(fields=('span', 'tag')"
        ", allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('span', 'tag'), cache=False), InitPlan(fie"
        "lds=(InitPlan.Field(name='span', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_fact"
        "ory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=Non"
        "e), InitPlan.Field(name='tag', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factor"
        "y=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)"
        "), self_param='self', std_params=('span', 'tag'), kw_only_params=(), frozen=True, slots=False, post_init_param"
        "s=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='span', kw_only=False, fn=None), R"
        "eprPlan.Field(name='tag', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='0c197ba2089899db7f7e91669688463fbc8b9e27',
    cls_names=(
        ('omdev.tui.minitui.vim.status', 'Decoration'),
    ),
)
def _process_dataclass__0c197ba2089899db7f7e91669688463fbc8b9e27():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('mode', 'pending', 'cmdline', 'message', 'cursor_count')), EqPlan(fields=('mode', "
        "'pending', 'cmdline', 'message', 'cursor_count')), FrozenPlan(fields=('mode', 'pending', 'cmdline', 'message',"
        " 'cursor_count'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('mode', 'pending', 'cmdlin"
        "e', 'message', 'cursor_count'), cache=False), InitPlan(fields=(InitPlan.Field(name='mode', annotation=OpRef(na"
        "me='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=Fiel"
        "dType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='pending', annotation=OpRef("
        "name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True"
        ", override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field("
        "name='cmdline', annotation=OpRef(name='init.fields.2.annotation'), default=OpRef(name='init.fields.2.default')"
        ", default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, "
        "check_type=None), InitPlan.Field(name='message', annotation=OpRef(name='init.fields.3.annotation'), default=Op"
        "Ref(name='init.fields.3.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTA"
        "NCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='cursor_count', annotation=OpRef(name='"
        "init.fields.4.annotation'), default=OpRef(name='init.fields.4.default'), default_factory=None, init=True, over"
        "ride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', s"
        "td_params=(), kw_only_params=('mode', 'pending', 'cmdline', 'message', 'cursor_count'), frozen=True, slots=Fal"
        "se, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='mode', kw_only"
        "=True, fn=None), ReprPlan.Field(name='pending', kw_only=True, fn=None), ReprPlan.Field(name='cmdline', kw_only"
        "=True, fn=None), ReprPlan.Field(name='message', kw_only=True, fn=None), ReprPlan.Field(name='cursor_count', kw"
        "_only=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='c951b441129b10feb8cb51e52267df339bccbd49',
    cls_names=(
        ('omdev.tui.minitui.vim.status', 'VimStatus'),
    ),
)
def _process_dataclass__c951b441129b10feb8cb51e52267df339bccbd49():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('start_row', 'end_row')), EqPlan(fields=('start_row', 'end_row')), FrozenPlan(fiel"
        "ds=('start_row', 'end_row'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('start_row', 'e"
        "nd_row'), cache=False), InitPlan(fields=(InitPlan.Field(name='start_row', annotation=OpRef(name='init.fields.0"
        ".annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, c"
        "oerce=None, validate=None, check_type=None), InitPlan.Field(name='end_row', annotation=OpRef(name='init.fields"
        ".1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE,"
        " coerce=None, validate=None, check_type=None)), self_param='self', std_params=('start_row', 'end_row'), kw_onl"
        "y_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=("
        "ReprPlan.Field(name='start_row', kw_only=False, fn=None), ReprPlan.Field(name='end_row', kw_only=False, fn=Non"
        "e)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='49a65af234c0c6fcb1ef134454600aa61472eb03',
    cls_names=(
        ('omdev.tui.minitui.vim.substitutes', 'ExRange'),
    ),
)
def _process_dataclass__49a65af234c0c6fcb1ef134454600aa61472eb03():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('replaced', 'lines', 'last_row')), EqPlan(fields=('replaced', 'lines', 'last_row')"
        "), FrozenPlan(fields=('replaced', 'lines', 'last_row'), allow_dynamic_dunder_attrs=False), HashPlan(action='ad"
        "d', fields=('replaced', 'lines', 'last_row'), cache=False), InitPlan(fields=(InitPlan.Field(name='replaced', a"
        "nnotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=Fals"
        "e, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='lines', a"
        "nnotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override=Fals"
        "e, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='last_row'"
        ", annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=F"
        "alse, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_par"
        "ams=('replaced', 'lines', 'last_row'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, ini"
        "t_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='replaced', kw_only=False, fn=None), ReprPlan"
        ".Field(name='lines', kw_only=False, fn=None), ReprPlan.Field(name='last_row', kw_only=False, fn=None)), id=Fal"
        "se, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='c9b71f9d6c085da692fa39b94c6e2d1360492bfc',
    cls_names=(
        ('omdev.tui.minitui.vim.substitutes', 'SubstituteResult'),
    ),
)
def _process_dataclass__c9b71f9d6c085da692fa39b94c6e2d1360492bfc():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('pattern', 'replacement', 'every', 'ignore_case')), EqPlan(fields=('pattern', 'rep"
        "lacement', 'every', 'ignore_case')), FrozenPlan(fields=('pattern', 'replacement', 'every', 'ignore_case'), all"
        "ow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('pattern', 'replacement', 'every', 'ignore_case"
        "'), cache=False), InitPlan(fields=(InitPlan.Field(name='pattern', annotation=OpRef(name='init.fields.0.annotat"
        "ion'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=No"
        "ne, validate=None, check_type=None), InitPlan.Field(name='replacement', annotation=OpRef(name='init.fields.1.a"
        "nnotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coe"
        "rce=None, validate=None, check_type=None), InitPlan.Field(name='every', annotation=OpRef(name='init.fields.2.a"
        "nnotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, override=False, fie"
        "ld_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='ignore_case', a"
        "nnotation=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default'), default_factory"
        "=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None))"
        ", self_param='self', std_params=('pattern', 'replacement', 'every', 'ignore_case'), kw_only_params=(), frozen="
        "True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name="
        "'pattern', kw_only=False, fn=None), ReprPlan.Field(name='replacement', kw_only=False, fn=None), ReprPlan.Field"
        "(name='every', kw_only=False, fn=None), ReprPlan.Field(name='ignore_case', kw_only=False, fn=None)), id=False,"
        " terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='41d0b93d847273f753f36af2eb801fe647c06cfe',
    cls_names=(
        ('omdev.tui.minitui.vim.substitutes', 'SubstituteSpec'),
    ),
)
def _process_dataclass__41d0b93d847273f753f36af2eb801fe647c06cfe():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__3__default,
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
