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
        "Plans(tup=(CopyPlan(fields=('frame', 'regions')), EqPlan(fields=('frame', 'regions')), FrozenPlan(fields=('fra"
        "me', 'regions'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('frame', 'regions'), cache="
        "False), InitPlan(fields=(InitPlan.Field(name='frame', annotation=OpRef(name='init.fields.0.annotation'), defau"
        "lt=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate"
        "=None, check_type=None), InitPlan.Field(name='regions', annotation=OpRef(name='init.fields.1.annotation'), def"
        "ault=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, valida"
        "te=None, check_type=None)), self_param='self', std_params=('frame', 'regions'), kw_only_params=(), frozen=True"
        ", slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='fra"
        "me', kw_only=False, fn=None), ReprPlan.Field(name='regions', kw_only=False, fn=None)), id=False, terse=False, "
        "default_fn=None)))"
    ),
    plan_repr_sha1='3cfc026f307312ed7e797ee0dee1ad3d391b54f8',
    cls_names=(
        ('omdev.tui.minitui.controls.stacks', 'StackLayout'),
    ),
)
def _process_dataclass__3cfc026f307312ed7e797ee0dee1ad3d391b54f8():
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
                frame=self.frame,
                regions=self.regions,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.frame == other.frame and
                self.regions == other.regions
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'frame',
            'regions',
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
                self.frame,
                self.regions,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            frame: __dataclass__init__fields__0__annotation,
            regions: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'frame', frame)
            __dataclass__object_setattr(self, 'regions', regions)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"frame={self.frame!r}")
            parts.append(f"regions={self.regions!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('control', 'y_start', 'y_end', 'clip_top')), EqPlan(fields=('control', 'y_start', "
        "'y_end', 'clip_top')), FrozenPlan(fields=('control', 'y_start', 'y_end', 'clip_top'), allow_dynamic_dunder_att"
        "rs=False), HashPlan(action='add', fields=('control', 'y_start', 'y_end', 'clip_top'), cache=False), InitPlan(f"
        "ields=(InitPlan.Field(name='control', annotation=OpRef(name='init.fields.0.annotation'), default=None, default"
        "_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_typ"
        "e=None), InitPlan.Field(name='y_start', annotation=OpRef(name='init.fields.1.annotation'), default=None, defau"
        "lt_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_t"
        "ype=None), InitPlan.Field(name='y_end', annotation=OpRef(name='init.fields.2.annotation'), default=None, defau"
        "lt_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_t"
        "ype=None), InitPlan.Field(name='clip_top', annotation=OpRef(name='init.fields.3.annotation'), default=OpRef(na"
        "me='init.fields.3.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, c"
        "oerce=None, validate=None, check_type=None)), self_param='self', std_params=('control', 'y_start', 'y_end', 'c"
        "lip_top'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), "
        "ReprPlan(fields=(ReprPlan.Field(name='control', kw_only=False, fn=None), ReprPlan.Field(name='y_start', kw_onl"
        "y=False, fn=None), ReprPlan.Field(name='y_end', kw_only=False, fn=None), ReprPlan.Field(name='clip_top', kw_on"
        "ly=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='954d5e4a36b3798dd4bafdb230b25527804b0d6a',
    cls_names=(
        ('omdev.tui.minitui.controls.stacks', 'StackRegion'),
    ),
)
def _process_dataclass__954d5e4a36b3798dd4bafdb230b25527804b0d6a():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
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
                control=self.control,
                y_start=self.y_start,
                y_end=self.y_end,
                clip_top=self.clip_top,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.control == other.control and
                self.y_start == other.y_start and
                self.y_end == other.y_end and
                self.clip_top == other.clip_top
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'control',
            'y_start',
            'y_end',
            'clip_top',
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
                self.control,
                self.y_start,
                self.y_end,
                self.clip_top,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            control: __dataclass__init__fields__0__annotation,
            y_start: __dataclass__init__fields__1__annotation,
            y_end: __dataclass__init__fields__2__annotation,
            clip_top: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'control', control)
            __dataclass__object_setattr(self, 'y_start', y_start)
            __dataclass__object_setattr(self, 'y_end', y_end)
            __dataclass__object_setattr(self, 'clip_top', clip_top)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"control={self.control!r}")
            parts.append(f"y_start={self.y_start!r}")
            parts.append(f"y_end={self.y_end!r}")
            parts.append(f"clip_top={self.clip_top!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('label', 'description')), EqPlan(fields=('label', 'description')), FrozenPlan(fiel"
        "ds=('label', 'description'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('label', 'descr"
        "iption'), cache=False), InitPlan(fields=(InitPlan.Field(name='label', annotation=OpRef(name='init.fields.0.ann"
        "otation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerc"
        "e=None, validate=None, check_type=None), InitPlan.Field(name='description', annotation=OpRef(name='init.fields"
        ".1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False,"
        " field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=("
        "'label', 'description'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), vali"
        "date_fns=()), ReprPlan(fields=(ReprPlan.Field(name='label', kw_only=False, fn=None), ReprPlan.Field(name='desc"
        "ription', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='ac9984294423eb5d4108e6894070515566bb8172',
    cls_names=(
        ('omdev.tui.minitui.controls.suggestions', 'SuggestionItem'),
    ),
)
def _process_dataclass__ac9984294423eb5d4108e6894070515566bb8172():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
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
                label=self.label,
                description=self.description,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.label == other.label and
                self.description == other.description
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'label',
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
                self.label,
                self.description,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            label: __dataclass__init__fields__0__annotation,
            description: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'label', label)
            __dataclass__object_setattr(self, 'description', description)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"label={self.label!r}")
            parts.append(f"description={self.description!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('doc_row', 'start_col', 'end_col', 'first')), EqPlan(fields=('doc_row', 'start_col"
        "', 'end_col', 'first')), FrozenPlan(fields=('doc_row', 'start_col', 'end_col', 'first'), allow_dynamic_dunder_"
        "attrs=False), HashPlan(action='add', fields=('doc_row', 'start_col', 'end_col', 'first'), cache=False), InitPl"
        "an(fields=(InitPlan.Field(name='doc_row', annotation=OpRef(name='init.fields.0.annotation'), default=None, def"
        "ault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check"
        "_type=None), InitPlan.Field(name='start_col', annotation=OpRef(name='init.fields.1.annotation'), default=None,"
        " default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, c"
        "heck_type=None), InitPlan.Field(name='end_col', annotation=OpRef(name='init.fields.2.annotation'), default=Non"
        "e, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None,"
        " check_type=None), InitPlan.Field(name='first', annotation=OpRef(name='init.fields.3.annotation'), default=Non"
        "e, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None,"
        " check_type=None)), self_param='self', std_params=('doc_row', 'start_col', 'end_col', 'first'), kw_only_params"
        "=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan"
        ".Field(name='doc_row', kw_only=False, fn=None), ReprPlan.Field(name='start_col', kw_only=False, fn=None), Repr"
        "Plan.Field(name='end_col', kw_only=False, fn=None), ReprPlan.Field(name='first', kw_only=False, fn=None)), id="
        "False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='a2edcce1628e4def1067347058ceedf2ede47b34',
    cls_names=(
        ('omdev.tui.minitui.controls.textarea', '_WrapRow'),
    ),
)
def _process_dataclass__a2edcce1628e4def1067347058ceedf2ede47b34():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
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
                doc_row=self.doc_row,
                start_col=self.start_col,
                end_col=self.end_col,
                first=self.first,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.doc_row == other.doc_row and
                self.start_col == other.start_col and
                self.end_col == other.end_col and
                self.first == other.first
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'doc_row',
            'start_col',
            'end_col',
            'first',
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
                self.doc_row,
                self.start_col,
                self.end_col,
                self.first,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            doc_row: __dataclass__init__fields__0__annotation,
            start_col: __dataclass__init__fields__1__annotation,
            end_col: __dataclass__init__fields__2__annotation,
            first: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'doc_row', doc_row)
            __dataclass__object_setattr(self, 'start_col', start_col)
            __dataclass__object_setattr(self, 'end_col', end_col)
            __dataclass__object_setattr(self, 'first', first)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"doc_row={self.doc_row!r}")
            parts.append(f"start_col={self.start_col!r}")
            parts.append(f"end_col={self.end_col!r}")
            parts.append(f"first={self.first!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('pos', 'want')), EqPlan(fields=('pos', 'want')), FrozenPlan(fields=('pos', 'want')"
        ", allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('pos', 'want'), cache=False), InitPlan(fie"
        "lds=(InitPlan.Field(name='pos', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_facto"
        "ry=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None"
        "), InitPlan.Field(name='want', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fie"
        "lds.1.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, "
        "validate=None, check_type=None)), self_param='self', std_params=('pos',), kw_only_params=('want',), frozen=Tru"
        "e, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='po"
        "s', kw_only=False, fn=None), ReprPlan.Field(name='want', kw_only=True, fn=None)), id=False, terse=False, defau"
        "lt_fn=None)))"
    ),
    plan_repr_sha1='f1146d747d05277db997eecaa548f776f4410bcd',
    cls_names=(
        ('omdev.tui.minitui.docs.cursors', 'Cursor'),
    ),
)
def _process_dataclass__f1146d747d05277db997eecaa548f776f4410bcd():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
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
                pos=self.pos,
                want=self.want,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.pos == other.pos and
                self.want == other.want
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'pos',
            'want',
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
                self.pos,
                self.want,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            pos: __dataclass__init__fields__0__annotation,
            *,
            want: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'pos', pos)
            __dataclass__object_setattr(self, 'want', want)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"pos={self.pos!r}")
            parts.append(f"want={self.want!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('edit', 'inverse')), EqPlan(fields=('edit', 'inverse')), FrozenPlan(fields=('edit'"
        ", 'inverse'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('edit', 'inverse'), cache=Fals"
        "e), InitPlan(fields=(InitPlan.Field(name='edit', annotation=OpRef(name='init.fields.0.annotation'), default=No"
        "ne, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None"
        ", check_type=None), InitPlan.Field(name='inverse', annotation=OpRef(name='init.fields.1.annotation'), default="
        "None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=No"
        "ne, check_type=None)), self_param='self', std_params=('edit', 'inverse'), kw_only_params=(), frozen=True, slot"
        "s=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='edit', kw"
        "_only=False, fn=None), ReprPlan.Field(name='inverse', kw_only=False, fn=None)), id=False, terse=False, default"
        "_fn=None)))"
    ),
    plan_repr_sha1='1d31fac8b4351efdfe1d31d6a3b58146b8e445cd',
    cls_names=(
        ('omdev.tui.minitui.docs.edits', 'AppliedEdit'),
    ),
)
def _process_dataclass__1d31fac8b4351efdfe1d31d6a3b58146b8e445cd():
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
                edit=self.edit,
                inverse=self.inverse,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.edit == other.edit and
                self.inverse == other.inverse
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'edit',
            'inverse',
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
                self.edit,
                self.inverse,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            edit: __dataclass__init__fields__0__annotation,
            inverse: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'edit', edit)
            __dataclass__object_setattr(self, 'inverse', inverse)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"edit={self.edit!r}")
            parts.append(f"inverse={self.inverse!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('start', 'end', 'text')), EqPlan(fields=('start', 'end', 'text')), FrozenPlan(fiel"
        "ds=('start', 'end', 'text'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('start', 'end',"
        " 'text'), cache=False), InitPlan(fields=(InitPlan.Field(name='start', annotation=OpRef(name='init.fields.0.ann"
        "otation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerc"
        "e=None, validate=None, check_type=None), InitPlan.Field(name='end', annotation=OpRef(name='init.fields.1.annot"
        "ation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce="
        "None, validate=None, check_type=None), InitPlan.Field(name='text', annotation=OpRef(name='init.fields.2.annota"
        "tion'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=N"
        "one, validate=None, check_type=None)), self_param='self', std_params=('start', 'end', 'text'), kw_only_params="
        "(), frozen=True, slots=False, post_init_params=(), init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Fi"
        "eld(name='start', kw_only=False, fn=None), ReprPlan.Field(name='end', kw_only=False, fn=None), ReprPlan.Field("
        "name='text', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='6b1ef611db996e607e7410d6e9d4ab1b97c3b267',
    cls_names=(
        ('omdev.tui.minitui.docs.edits', 'TextEdit'),
    ),
)
def _process_dataclass__6b1ef611db996e607e7410d6e9d4ab1b97c3b267():
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
                start=self.start,
                end=self.end,
                text=self.text,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.start == other.start and
                self.end == other.end and
                self.text == other.text
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'start',
            'end',
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
                self.start,
                self.end,
                self.text,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            start: __dataclass__init__fields__0__annotation,
            end: __dataclass__init__fields__1__annotation,
            text: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'start', start)
            __dataclass__object_setattr(self, 'end', end)
            __dataclass__object_setattr(self, 'text', text)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"start={self.start!r}")
            parts.append(f"end={self.end!r}")
            parts.append(f"text={self.text!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('row', 'col')), EqPlan(fields=('row', 'col')), FrozenPlan(fields=('row', 'col'), a"
        "llow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('row', 'col'), cache=False), InitPlan(fields="
        "(InitPlan.Field(name='row', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=N"
        "one, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), I"
        "nitPlan.Field(name='col', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=Non"
        "e, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), se"
        "lf_param='self', std_params=('row', 'col'), kw_only_params=(), frozen=True, slots=False, post_init_params=None"
        ", init_fns=(), validate_fns=()), OrderPlan(fields=('row', 'col')), ReprPlan(fields=(ReprPlan.Field(name='row',"
        " kw_only=False, fn=None), ReprPlan.Field(name='col', kw_only=False, fn=None)), id=False, terse=False, default_"
        "fn=None)))"
    ),
    plan_repr_sha1='20aa75e5f04fa0079fa1d32266ee7199fffd28f2',
    cls_names=(
        ('omdev.tui.minitui.docs.positions', 'Pos'),
    ),
)
def _process_dataclass__20aa75e5f04fa0079fa1d32266ee7199fffd28f2():
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
                row=self.row,
                col=self.col,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.row == other.row and
                self.col == other.col
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'row',
            'col',
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
                self.row,
                self.col,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            row: __dataclass__init__fields__0__annotation,
            col: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'row', row)
            __dataclass__object_setattr(self, 'col', col)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        def __lt__(self, other):
            if other.__class__ is not self.__class__:
                return NotImplemented
            return (
                self.row,
                self.col,
            ) < (
                other.row,
                other.col,
            )

        __dataclass__set_cls_attr(__class__, '__lt__', __lt__, 'raise', set_qualname=True)

        def __le__(self, other):
            if other.__class__ is not self.__class__:
                return NotImplemented
            return (
                self.row,
                self.col,
            ) <= (
                other.row,
                other.col,
            )

        __dataclass__set_cls_attr(__class__, '__le__', __le__, 'raise', set_qualname=True)

        def __gt__(self, other):
            if other.__class__ is not self.__class__:
                return NotImplemented
            return (
                self.row,
                self.col,
            ) > (
                other.row,
                other.col,
            )

        __dataclass__set_cls_attr(__class__, '__gt__', __gt__, 'raise', set_qualname=True)

        def __ge__(self, other):
            if other.__class__ is not self.__class__:
                return NotImplemented
            return (
                self.row,
                self.col,
            ) >= (
                other.row,
                other.col,
            )

        __dataclass__set_cls_attr(__class__, '__ge__', __ge__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"row={self.row!r}")
            parts.append(f"col={self.col!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('kind', 'start', 'end')), EqPlan(fields=('kind', 'start', 'end')), FrozenPlan(fiel"
        "ds=('kind', 'start', 'end'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('kind', 'start'"
        ", 'end'), cache=False), InitPlan(fields=(InitPlan.Field(name='kind', annotation=OpRef(name='init.fields.0.anno"
        "tation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce"
        "=None, validate=None, check_type=None), InitPlan.Field(name='start', annotation=OpRef(name='init.fields.1.anno"
        "tation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce"
        "=None, validate=None, check_type=None), InitPlan.Field(name='end', annotation=OpRef(name='init.fields.2.annota"
        "tion'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=N"
        "one, validate=None, check_type=None)), self_param='self', std_params=('kind', 'start', 'end'), kw_only_params="
        "(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan."
        "Field(name='kind', kw_only=False, fn=None), ReprPlan.Field(name='start', kw_only=False, fn=None), ReprPlan.Fie"
        "ld(name='end', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='9f6a9acfb0bea82f081c340d814bc5f788039d55',
    cls_names=(
        ('omdev.tui.minitui.docs.positions', 'Span'),
    ),
)
def _process_dataclass__9f6a9acfb0bea82f081c340d814bc5f788039d55():
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
                kind=self.kind,
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
                self.kind == other.kind and
                self.start == other.start and
                self.end == other.end
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'kind',
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
                self.kind,
                self.start,
                self.end,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            kind: __dataclass__init__fields__0__annotation,
            start: __dataclass__init__fields__1__annotation,
            end: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'kind', kind)
            __dataclass__object_setattr(self, 'start', start)
            __dataclass__object_setattr(self, 'end', end)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"kind={self.kind!r}")
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('commands', 'unmatched')), EqPlan(fields=('commands', 'unmatched')), FrozenPlan(fi"
        "elds=('commands', 'unmatched'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('commands', "
        "'unmatched'), cache=False), InitPlan(fields=(InitPlan.Field(name='commands', annotation=OpRef(name='init.field"
        "s.0.annotation'), default=OpRef(name='init.fields.0.default'), default_factory=None, init=True, override=False"
        ", field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='unmatched'"
        ", annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_fact"
        "ory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=Non"
        "e)), self_param='self', std_params=('commands', 'unmatched'), kw_only_params=(), frozen=True, slots=False, pos"
        "t_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='commands', kw_only=Fa"
        "lse, fn=None), ReprPlan.Field(name='unmatched', kw_only=False, fn=None)), id=False, terse=False, default_fn=No"
        "ne)))"
    ),
    plan_repr_sha1='d63a29aca0b07f9c4057761e01c901d03418db81',
    cls_names=(
        ('omdev.tui.minitui.events.keymaps', 'KeymapMatch'),
    ),
)
def _process_dataclass__d63a29aca0b07f9c4057761e01c901d03418db81():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__default,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
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
                commands=self.commands,
                unmatched=self.unmatched,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.commands == other.commands and
                self.unmatched == other.unmatched
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'commands',
            'unmatched',
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
                self.commands,
                self.unmatched,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            commands: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            unmatched: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'commands', commands)
            __dataclass__object_setattr(self, 'unmatched', unmatched)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"commands={self.commands!r}")
            parts.append(f"unmatched={self.unmatched!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('base', 'ctrl', 'alt', 'shift', 'super_')), EqPlan(fields=('base', 'ctrl', 'alt', "
        "'shift', 'super_')), FrozenPlan(fields=('base', 'ctrl', 'alt', 'shift', 'super_'), allow_dynamic_dunder_attrs="
        "False), HashPlan(action='add', fields=('base', 'ctrl', 'alt', 'shift', 'super_'), cache=False), InitPlan(field"
        "s=(InitPlan.Field(name='base', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factor"
        "y=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)"
        ", InitPlan.Field(name='ctrl', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fiel"
        "ds.1.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, v"
        "alidate=None, check_type=None), InitPlan.Field(name='alt', annotation=OpRef(name='init.fields.2.annotation'), "
        "default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, override=False, field_type=Field"
        "Type.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='shift', annotation=OpRef(nam"
        "e='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default'), default_factory=None, init=True, o"
        "verride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(nam"
        "e='super_', annotation=OpRef(name='init.fields.4.annotation'), default=OpRef(name='init.fields.4.default'), de"
        "fault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, chec"
        "k_type=None)), self_param='self', std_params=('base',), kw_only_params=('ctrl', 'alt', 'shift', 'super_'), fro"
        "zen=True, slots=False, post_init_params=(), init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(nam"
        "e='base', kw_only=False, fn=None), ReprPlan.Field(name='ctrl', kw_only=True, fn=None), ReprPlan.Field(name='al"
        "t', kw_only=True, fn=None), ReprPlan.Field(name='shift', kw_only=True, fn=None), ReprPlan.Field(name='super_',"
        " kw_only=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='9d628ea6edc5ac579394df393cf9c532bf235976',
    cls_names=(
        ('omdev.tui.minitui.events.keys', 'Key'),
    ),
)
def _process_dataclass__9d628ea6edc5ac579394df393cf9c532bf235976():
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
                base=self.base,
                ctrl=self.ctrl,
                alt=self.alt,
                shift=self.shift,
                super_=self.super_,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.base == other.base and
                self.ctrl == other.ctrl and
                self.alt == other.alt and
                self.shift == other.shift and
                self.super_ == other.super_
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'base',
            'ctrl',
            'alt',
            'shift',
            'super_',
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
                self.base,
                self.ctrl,
                self.alt,
                self.shift,
                self.super_,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            base: __dataclass__init__fields__0__annotation,
            *,
            ctrl: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            alt: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            shift: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            super_: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'base', base)
            __dataclass__object_setattr(self, 'ctrl', ctrl)
            __dataclass__object_setattr(self, 'alt', alt)
            __dataclass__object_setattr(self, 'shift', shift)
            __dataclass__object_setattr(self, 'super_', super_)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"base={self.base!r}")
            parts.append(f"ctrl={self.ctrl!r}")
            parts.append(f"alt={self.alt!r}")
            parts.append(f"shift={self.shift!r}")
            parts.append(f"super_={self.super_!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('timeout_s',)), EqPlan(fields=('timeout_s',)), FrozenPlan(fields=('timeout_s',), a"
        "llow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('timeout_s',), cache=False), InitPlan(fields="
        "(InitPlan.Field(name='timeout_s', annotation=OpRef(name='init.fields.0.annotation'), default=OpRef(name='init."
        "fields.0.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=Non"
        "e, validate=None, check_type=None),), self_param='self', std_params=('timeout_s',), kw_only_params=(), frozen="
        "True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name="
        "'timeout_s', kw_only=False, fn=None),), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='c9180ff9898a845fd156029d69d6e884b20f9919',
    cls_names=(
        ('omdev.tui.minitui.events.parsing', 'Read1'),
    ),
)
def _process_dataclass__c9180ff9898a845fd156029d69d6e884b20f9919():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__default,
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
                timeout_s=self.timeout_s,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.timeout_s == other.timeout_s
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'timeout_s',
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
                self.timeout_s,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            timeout_s: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'timeout_s', timeout_s)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"timeout_s={self.timeout_s!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('x', 'y')), EqPlan(fields=('x', 'y')), FrozenPlan(fields=('x', 'y'), allow_dynamic"
        "_dunder_attrs=False), HashPlan(action='add', fields=('x', 'y'), cache=False), InitPlan(fields=(InitPlan.Field("
        "name='x', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, ov"
        "erride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name"
        "='y', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, overri"
        "de=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std"
        "_params=('x', 'y'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_"
        "fns=()), ReprPlan(fields=(ReprPlan.Field(name='x', kw_only=False, fn=None), ReprPlan.Field(name='y', kw_only=F"
        "alse, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='55e8b170c17862665dea908d974e50c0f8ed7f8d',
    cls_names=(
        ('omdev.tui.minitui.events.types', 'CursorPositionEvent'),
    ),
)
def _process_dataclass__55e8b170c17862665dea908d974e50c0f8ed7f8d():
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
                self.x == other.x and
                self.y == other.y
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'x',
            'y',
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
                self.x,
                self.y,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            x: __dataclass__init__fields__0__annotation,
            y: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'x', x)
            __dataclass__object_setattr(self, 'y', y)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('gained',)), EqPlan(fields=('gained',)), FrozenPlan(fields=('gained',), allow_dyna"
        "mic_dunder_attrs=False), HashPlan(action='add', fields=('gained',), cache=False), InitPlan(fields=(InitPlan.Fi"
        "eld(name='gained', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init"
        "=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_par"
        "am='self', std_params=('gained',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fn"
        "s=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='gained', kw_only=False, fn=None),), id=False, te"
        "rse=False, default_fn=None)))"
    ),
    plan_repr_sha1='a56050c1cbf85700e8905c53dea3a93674a1f3a4',
    cls_names=(
        ('omdev.tui.minitui.events.types', 'FocusEvent'),
    ),
)
def _process_dataclass__a56050c1cbf85700e8905c53dea3a93674a1f3a4():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
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
                gained=self.gained,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.gained == other.gained
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'gained',
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
                self.gained,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            gained: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'gained', gained)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"gained={self.gained!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=()), EqPlan(fields=()), FrozenPlan(fields=(), allow_dynamic_dunder_attrs=False), Ha"
        "shPlan(action='add', fields=(), cache=False), InitPlan(fields=(), self_param='self', std_params=(), kw_only_pa"
        "rams=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(), i"
        "d=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='e1f7edfe11f2b721d6a656c46e698fedc95461bb',
    cls_names=(
        ('omdev.tui.minitui.events.types', 'InputEofEvent'),
        ('omdev.tui.minitui.events.types', 'ResumeEvent'),
        ('omdev.tui.minitui.events.types', 'SuspendEvent'),
        ('omdev.tui.minitui.text.markdown.base', 'MdRule'),
    ),
)
def _process_dataclass__e1f7edfe11f2b721d6a656c46e698fedc95461bb():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__set_cls_attr,
    ):
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('key', 'text')), EqPlan(fields=('key', 'text')), FrozenPlan(fields=('key', 'text')"
        ", allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('key', 'text'), cache=False), InitPlan(fie"
        "lds=(InitPlan.Field(name='key', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_facto"
        "ry=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None"
        "), InitPlan.Field(name='text', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fie"
        "lds.1.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, "
        "validate=None, check_type=None)), self_param='self', std_params=('key',), kw_only_params=('text',), frozen=Tru"
        "e, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='ke"
        "y', kw_only=False, fn=None), ReprPlan.Field(name='text', kw_only=True, fn=None)), id=False, terse=False, defau"
        "lt_fn=None)))"
    ),
    plan_repr_sha1='b67b8d016105a93c2316b2bb944363f1b17c29d6',
    cls_names=(
        ('omdev.tui.minitui.events.types', 'KeyEvent'),
    ),
)
def _process_dataclass__b67b8d016105a93c2316b2bb944363f1b17c29d6():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
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
                key=self.key,
                text=self.text,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.key == other.key and
                self.text == other.text
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'key',
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
                self.key,
                self.text,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            key: __dataclass__init__fields__0__annotation,
            *,
            text: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'text', text)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"key={self.key!r}")
            parts.append(f"text={self.text!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('flags',)), EqPlan(fields=('flags',)), FrozenPlan(fields=('flags',), allow_dynamic"
        "_dunder_attrs=False), HashPlan(action='add', fields=('flags',), cache=False), InitPlan(fields=(InitPlan.Field("
        "name='flags', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True"
        ", override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='s"
        "elf', std_params=('flags',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), "
        "validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='flags', kw_only=False, fn=None),), id=False, terse=Fal"
        "se, default_fn=None)))"
    ),
    plan_repr_sha1='6deea0adbb767cb1899c738559d8ba69f34de3a0',
    cls_names=(
        ('omdev.tui.minitui.events.types', 'KittyFlagsEvent'),
    ),
)
def _process_dataclass__6deea0adbb767cb1899c738559d8ba69f34de3a0():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
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
                flags=self.flags,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.flags == other.flags
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'flags',
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
                self.flags,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            flags: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'flags', flags)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"flags={self.flags!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('mode', 'value')), EqPlan(fields=('mode', 'value')), FrozenPlan(fields=('mode', 'v"
        "alue'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('mode', 'value'), cache=False), Init"
        "Plan(fields=(InitPlan.Field(name='mode', annotation=OpRef(name='init.fields.0.annotation'), default=None, defa"
        "ult_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_"
        "type=None), InitPlan.Field(name='value', annotation=OpRef(name='init.fields.1.annotation'), default=None, defa"
        "ult_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_"
        "type=None)), self_param='self', std_params=('mode', 'value'), kw_only_params=(), frozen=True, slots=False, pos"
        "t_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='mode', kw_only=False,"
        " fn=None), ReprPlan.Field(name='value', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='11e61f10868c9b0244dcc0b1256b7448614cb7b3',
    cls_names=(
        ('omdev.tui.minitui.events.types', 'ModeReportEvent'),
    ),
)
def _process_dataclass__11e61f10868c9b0244dcc0b1256b7448614cb7b3():
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
                mode=self.mode,
                value=self.value,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.mode == other.mode and
                self.value == other.value
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'mode',
            'value',
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
                self.value,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            mode: __dataclass__init__fields__0__annotation,
            value: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'mode', mode)
            __dataclass__object_setattr(self, 'value', value)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"mode={self.mode!r}")
            parts.append(f"value={self.value!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('kind', 'x', 'y', 'button', 'ctrl', 'alt', 'shift')), EqPlan(fields=('kind', 'x', "
        "'y', 'button', 'ctrl', 'alt', 'shift')), FrozenPlan(fields=('kind', 'x', 'y', 'button', 'ctrl', 'alt', 'shift'"
        "), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('kind', 'x', 'y', 'button', 'ctrl', 'alt'"
        ", 'shift'), cache=False), InitPlan(fields=(InitPlan.Field(name='kind', annotation=OpRef(name='init.fields.0.an"
        "notation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coer"
        "ce=None, validate=None, check_type=None), InitPlan.Field(name='x', annotation=OpRef(name='init.fields.1.annota"
        "tion'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=N"
        "one, validate=None, check_type=None), InitPlan.Field(name='y', annotation=OpRef(name='init.fields.2.annotation"
        "'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None,"
        " validate=None, check_type=None), InitPlan.Field(name='button', annotation=OpRef(name='init.fields.3.annotatio"
        "n'), default=OpRef(name='init.fields.3.default'), default_factory=None, init=True, override=False, field_type="
        "FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='ctrl', annotation=OpRef"
        "(name='init.fields.4.annotation'), default=OpRef(name='init.fields.4.default'), default_factory=None, init=Tru"
        "e, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field"
        "(name='alt', annotation=OpRef(name='init.fields.5.annotation'), default=OpRef(name='init.fields.5.default'), d"
        "efault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, che"
        "ck_type=None), InitPlan.Field(name='shift', annotation=OpRef(name='init.fields.6.annotation'), default=OpRef(n"
        "ame='init.fields.6.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, "
        "coerce=None, validate=None, check_type=None)), self_param='self', std_params=('kind', 'x', 'y'), kw_only_param"
        "s=('button', 'ctrl', 'alt', 'shift'), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_f"
        "ns=()), ReprPlan(fields=(ReprPlan.Field(name='kind', kw_only=False, fn=None), ReprPlan.Field(name='x', kw_only"
        "=False, fn=None), ReprPlan.Field(name='y', kw_only=False, fn=None), ReprPlan.Field(name='button', kw_only=True"
        ", fn=None), ReprPlan.Field(name='ctrl', kw_only=True, fn=None), ReprPlan.Field(name='alt', kw_only=True, fn=No"
        "ne), ReprPlan.Field(name='shift', kw_only=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='d9c26b45b541dec4a801b0ee0fa10c3641fa8952',
    cls_names=(
        ('omdev.tui.minitui.events.types', 'MouseEvent'),
    ),
)
def _process_dataclass__d9c26b45b541dec4a801b0ee0fa10c3641fa8952():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__3__default,
        __dataclass__init__fields__4__annotation,
        __dataclass__init__fields__4__default,
        __dataclass__init__fields__5__annotation,
        __dataclass__init__fields__5__default,
        __dataclass__init__fields__6__annotation,
        __dataclass__init__fields__6__default,
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
                kind=self.kind,
                x=self.x,
                y=self.y,
                button=self.button,
                ctrl=self.ctrl,
                alt=self.alt,
                shift=self.shift,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.kind == other.kind and
                self.x == other.x and
                self.y == other.y and
                self.button == other.button and
                self.ctrl == other.ctrl and
                self.alt == other.alt and
                self.shift == other.shift
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'kind',
            'x',
            'y',
            'button',
            'ctrl',
            'alt',
            'shift',
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
                self.kind,
                self.x,
                self.y,
                self.button,
                self.ctrl,
                self.alt,
                self.shift,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            kind: __dataclass__init__fields__0__annotation,
            x: __dataclass__init__fields__1__annotation,
            y: __dataclass__init__fields__2__annotation,
            *,
            button: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            ctrl: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            alt: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            shift: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'kind', kind)
            __dataclass__object_setattr(self, 'x', x)
            __dataclass__object_setattr(self, 'y', y)
            __dataclass__object_setattr(self, 'button', button)
            __dataclass__object_setattr(self, 'ctrl', ctrl)
            __dataclass__object_setattr(self, 'alt', alt)
            __dataclass__object_setattr(self, 'shift', shift)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"kind={self.kind!r}")
            parts.append(f"x={self.x!r}")
            parts.append(f"y={self.y!r}")
            parts.append(f"button={self.button!r}")
            parts.append(f"ctrl={self.ctrl!r}")
            parts.append(f"alt={self.alt!r}")
            parts.append(f"shift={self.shift!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('text',)), EqPlan(fields=('text',)), FrozenPlan(fields=('text',), allow_dynamic_du"
        "nder_attrs=False), HashPlan(action='add', fields=('text',), cache=False), InitPlan(fields=(InitPlan.Field(name"
        "='text', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, ove"
        "rride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='self',"
        " std_params=('text',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), valida"
        "te_fns=()), ReprPlan(fields=(ReprPlan.Field(name='text', kw_only=False, fn=None),), id=False, terse=False, def"
        "ault_fn=None)))"
    ),
    plan_repr_sha1='ce2a4c81e0f66e62a54ea3adfdc532902daece78',
    cls_names=(
        ('omdev.tui.minitui.events.types', 'PasteEvent'),
        ('omdev.tui.minitui.events.types', 'UnknownSequenceEvent'),
    ),
)
def _process_dataclass__ce2a4c81e0f66e62a54ea3adfdc532902daece78():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
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
            __dataclass__object_setattr(self, 'text', text)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('height', 'width')), EqPlan(fields=('height', 'width')), FrozenPlan(fields=('heigh"
        "t', 'width'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('height', 'width'), cache=Fals"
        "e), InitPlan(fields=(InitPlan.Field(name='height', annotation=OpRef(name='init.fields.0.annotation'), default="
        "None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=No"
        "ne, check_type=None), InitPlan.Field(name='width', annotation=OpRef(name='init.fields.1.annotation'), default="
        "None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=No"
        "ne, check_type=None)), self_param='self', std_params=('height', 'width'), kw_only_params=(), frozen=True, slot"
        "s=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='height', "
        "kw_only=False, fn=None), ReprPlan.Field(name='width', kw_only=False, fn=None)), id=False, terse=False, default"
        "_fn=None)))"
    ),
    plan_repr_sha1='094659c4f4f035565abff5f1871a23021ca04458',
    cls_names=(
        ('omdev.tui.minitui.events.types', 'ResizeEvent'),
    ),
)
def _process_dataclass__094659c4f4f035565abff5f1871a23021ca04458():
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
                height=self.height,
                width=self.width,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.height == other.height and
                self.width == other.width
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'height',
            'width',
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
                self.height,
                self.width,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            height: __dataclass__init__fields__0__annotation,
            width: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'height', height)
            __dataclass__object_setattr(self, 'width', width)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"height={self.height!r}")
            parts.append(f"width={self.width!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('info', 'lines')), EqPlan(fields=('info', 'lines')), FrozenPlan(fields=('info', 'l"
        "ines'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('info', 'lines'), cache=False), Init"
        "Plan(fields=(InitPlan.Field(name='info', annotation=OpRef(name='init.fields.0.annotation'), default=None, defa"
        "ult_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_"
        "type=None), InitPlan.Field(name='lines', annotation=OpRef(name='init.fields.1.annotation'), default=None, defa"
        "ult_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_"
        "type=None)), self_param='self', std_params=('info', 'lines'), kw_only_params=(), frozen=True, slots=False, pos"
        "t_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='info', kw_only=False,"
        " fn=None), ReprPlan.Field(name='lines', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='a21e0430f301c7ef0a5440b6b257d185896c48a7',
    cls_names=(
        ('omdev.tui.minitui.text.markdown.base', 'MdCode'),
    ),
)
def _process_dataclass__a21e0430f301c7ef0a5440b6b257d185896c48a7():
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
                info=self.info,
                lines=self.lines,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.info == other.info and
                self.lines == other.lines
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'info',
            'lines',
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
                self.info,
                self.lines,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            info: __dataclass__init__fields__0__annotation,
            lines: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'info', info)
            __dataclass__object_setattr(self, 'lines', lines)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"info={self.info!r}")
            parts.append(f"lines={self.lines!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('level', 'spans')), EqPlan(fields=('level', 'spans')), FrozenPlan(fields=('level',"
        " 'spans'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('level', 'spans'), cache=False), "
        "InitPlan(fields=(InitPlan.Field(name='level', annotation=OpRef(name='init.fields.0.annotation'), default=None,"
        " default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, c"
        "heck_type=None), InitPlan.Field(name='spans', annotation=OpRef(name='init.fields.1.annotation'), default=None,"
        " default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, c"
        "heck_type=None)), self_param='self', std_params=('level', 'spans'), kw_only_params=(), frozen=True, slots=Fals"
        "e, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='level', kw_only"
        "=False, fn=None), ReprPlan.Field(name='spans', kw_only=False, fn=None)), id=False, terse=False, default_fn=Non"
        "e)))"
    ),
    plan_repr_sha1='cff15062ec7fb46ea1e30d0bc1b048495a515c2f',
    cls_names=(
        ('omdev.tui.minitui.text.markdown.base', 'MdHeading'),
    ),
)
def _process_dataclass__cff15062ec7fb46ea1e30d0bc1b048495a515c2f():
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
                level=self.level,
                spans=self.spans,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.level == other.level and
                self.spans == other.spans
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'level',
            'spans',
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
                self.level,
                self.spans,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            level: __dataclass__init__fields__0__annotation,
            spans: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'level', level)
            __dataclass__object_setattr(self, 'spans', spans)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"level={self.level!r}")
            parts.append(f"spans={self.spans!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('items',)), EqPlan(fields=('items',)), FrozenPlan(fields=('items',), allow_dynamic"
        "_dunder_attrs=False), HashPlan(action='add', fields=('items',), cache=False), InitPlan(fields=(InitPlan.Field("
        "name='items', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True"
        ", override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='s"
        "elf', std_params=('items',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), "
        "validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='items', kw_only=False, fn=None),), id=False, terse=Fal"
        "se, default_fn=None)))"
    ),
    plan_repr_sha1='045f1b7eb2701bb19dcbd715f0da1519cb736718',
    cls_names=(
        ('omdev.tui.minitui.text.markdown.base', 'MdList'),
    ),
)
def _process_dataclass__045f1b7eb2701bb19dcbd715f0da1519cb736718():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
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
                items=self.items,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.items == other.items
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'items',
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
                self.items,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            items: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'items', items)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"items={self.items!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('marker', 'spans', 'depth')), EqPlan(fields=('marker', 'spans', 'depth')), FrozenP"
        "lan(fields=('marker', 'spans', 'depth'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('ma"
        "rker', 'spans', 'depth'), cache=False), InitPlan(fields=(InitPlan.Field(name='marker', annotation=OpRef(name='"
        "init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldTyp"
        "e.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='spans', annotation=OpRef(name='"
        "init.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldTyp"
        "e.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='depth', annotation=OpRef(name='"
        "init.fields.2.annotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, over"
        "ride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', s"
        "td_params=('marker', 'spans', 'depth'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, in"
        "it_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='marker', kw_only=False, fn=None), ReprPlan."
        "Field(name='spans', kw_only=False, fn=None), ReprPlan.Field(name='depth', kw_only=False, fn=None)), id=False, "
        "terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='bb7a03cbd43e7d23176fa716158ceba1432f7f39',
    cls_names=(
        ('omdev.tui.minitui.text.markdown.base', 'MdListItem'),
    ),
)
def _process_dataclass__bb7a03cbd43e7d23176fa716158ceba1432f7f39():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default,
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
                marker=self.marker,
                spans=self.spans,
                depth=self.depth,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.marker == other.marker and
                self.spans == other.spans and
                self.depth == other.depth
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'marker',
            'spans',
            'depth',
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
                self.marker,
                self.spans,
                self.depth,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            marker: __dataclass__init__fields__0__annotation,
            spans: __dataclass__init__fields__1__annotation,
            depth: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'marker', marker)
            __dataclass__object_setattr(self, 'spans', spans)
            __dataclass__object_setattr(self, 'depth', depth)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"marker={self.marker!r}")
            parts.append(f"spans={self.spans!r}")
            parts.append(f"depth={self.depth!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('spans',)), EqPlan(fields=('spans',)), FrozenPlan(fields=('spans',), allow_dynamic"
        "_dunder_attrs=False), HashPlan(action='add', fields=('spans',), cache=False), InitPlan(fields=(InitPlan.Field("
        "name='spans', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True"
        ", override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='s"
        "elf', std_params=('spans',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), "
        "validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='spans', kw_only=False, fn=None),), id=False, terse=Fal"
        "se, default_fn=None)))"
    ),
    plan_repr_sha1='d94b59df909090eea539565bc0673f53316b9e81',
    cls_names=(
        ('omdev.tui.minitui.text.markdown.base', 'MdParagraph'),
        ('omdev.tui.minitui.text.markdown.base', 'MdQuote'),
    ),
)
def _process_dataclass__d94b59df909090eea539565bc0673f53316b9e81():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
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
                spans=self.spans,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.spans == other.spans
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'spans',
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
                self.spans,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            spans: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'spans', spans)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"spans={self.spans!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('head', 'rows', 'aligns')), EqPlan(fields=('head', 'rows', 'aligns')), FrozenPlan("
        "fields=('head', 'rows', 'aligns'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('head', '"
        "rows', 'aligns'), cache=False), InitPlan(fields=(InitPlan.Field(name='head', annotation=OpRef(name='init.field"
        "s.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE"
        ", coerce=None, validate=None, check_type=None), InitPlan.Field(name='rows', annotation=OpRef(name='init.fields"
        ".1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False,"
        " field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='aligns', an"
        "notation=OpRef(name='init.fields.2.annotation'), default=OpRef(name='init.fields.2.default'), default_factory="
        "None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)),"
        " self_param='self', std_params=('head', 'rows', 'aligns'), kw_only_params=(), frozen=True, slots=False, post_i"
        "nit_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='head', kw_only=False, fn"
        "=None), ReprPlan.Field(name='rows', kw_only=False, fn=None), ReprPlan.Field(name='aligns', kw_only=False, fn=N"
        "one)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='ac4ed671de5aaa12a6b000796da8c67792c20509',
    cls_names=(
        ('omdev.tui.minitui.text.markdown.base', 'MdTable'),
    ),
)
def _process_dataclass__ac4ed671de5aaa12a6b000796da8c67792c20509():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default,
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
                head=self.head,
                rows=self.rows,
                aligns=self.aligns,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.head == other.head and
                self.rows == other.rows and
                self.aligns == other.aligns
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'head',
            'rows',
            'aligns',
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
                self.head,
                self.rows,
                self.aligns,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            head: __dataclass__init__fields__0__annotation,
            rows: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            aligns: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'head', head)
            __dataclass__object_setattr(self, 'rows', rows)
            __dataclass__object_setattr(self, 'aligns', aligns)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"head={self.head!r}")
            parts.append(f"rows={self.rows!r}")
            parts.append(f"aligns={self.aligns!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('cells',)), EqPlan(fields=('cells',)), FrozenPlan(fields=('cells',), allow_dynamic"
        "_dunder_attrs=False), HashPlan(action='add', fields=('cells',), cache=False), InitPlan(fields=(InitPlan.Field("
        "name='cells', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True"
        ", override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='s"
        "elf', std_params=('cells',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), "
        "validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='cells', kw_only=False, fn=None),), id=False, terse=Fal"
        "se, default_fn=None)))"
    ),
    plan_repr_sha1='4eb31cc66f9d458eaa6f19fc81744b0e2ef696dd',
    cls_names=(
        ('omdev.tui.minitui.text.markdown.base', 'MdTableRow'),
    ),
)
def _process_dataclass__4eb31cc66f9d458eaa6f19fc81744b0e2ef696dd():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
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
                cells=self.cells,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.cells == other.cells
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'cells',
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
                self.cells,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            cells: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'cells', cells)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"cells={self.cells!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('text', 'style')), EqPlan(fields=('text', 'style')), FrozenPlan(fields=('text', 's"
        "tyle'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('text', 'style'), cache=False), Init"
        "Plan(fields=(InitPlan.Field(name='text', annotation=OpRef(name='init.fields.0.annotation'), default=None, defa"
        "ult_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_"
        "type=None), InitPlan.Field(name='style', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name"
        "='init.fields.1.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coe"
        "rce=None, validate=None, check_type=None)), self_param='self', std_params=('text', 'style'), kw_only_params=()"
        ", frozen=True, slots=False, post_init_params=(), init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Fiel"
        "d(name='text', kw_only=False, fn=None), ReprPlan.Field(name='style', kw_only=False, fn=None)), id=False, terse"
        "=False, default_fn=None)))"
    ),
    plan_repr_sha1='b2e41750b446b961abaac20bedf8d3b3a1360879',
    cls_names=(
        ('omdev.tui.minitui.text.segments', 'Segment'),
    ),
)
def _process_dataclass__b2e41750b446b961abaac20bedf8d3b3a1360879():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
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
                text=self.text,
                style=self.style,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.text == other.text and
                self.style == other.style
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'text',
            'style',
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
                self.style,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            text: __dataclass__init__fields__0__annotation,
            style: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'text', text)
            __dataclass__object_setattr(self, 'style', style)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"text={self.text!r}")
            parts.append(f"style={self.style!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
