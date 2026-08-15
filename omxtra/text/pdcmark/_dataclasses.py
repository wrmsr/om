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
        "Plans(tup=(CopyPlan(fields=('open_start', 'kind')), EqPlan(fields=('open_start', 'kind')), FrozenPlan(fields=("
        "'open_start', 'kind'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('open_start', 'kind')"
        ", cache=False), InitPlan(fields=(InitPlan.Field(name='open_start', annotation=OpRef(name='init.fields.0.annota"
        "tion'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=N"
        "one, validate=None, check_type=None), InitPlan.Field(name='kind', annotation=OpRef(name='init.fields.1.annotat"
        "ion'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False, field_typ"
        "e=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('open_star"
        "t', 'kind'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=())"
        ", ReprPlan(fields=(ReprPlan.Field(name='open_start', kw_only=False, fn=None), ReprPlan.Field(name='kind', kw_o"
        "nly=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='f473e20a450081cf6cd69ae589d80b94c0ab1e72',
    cls_names=(
        ('omxtra.text.pdcmark.blocks.containers', 'OpenBlockQuote'),
    ),
)
def _process_dataclass__f473e20a450081cf6cd69ae589d80b94c0ab1e72():
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
                open_start=self.open_start,
                kind=self.kind,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.open_start == other.open_start and
                self.kind == other.kind
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'open_start',
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
                self.open_start,
                self.kind,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            open_start: __dataclass__init__fields__0__annotation,
            kind: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'open_start', open_start)
            __dataclass__object_setattr(self, 'kind', kind)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"open_start={self.open_start!r}")
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
        "Plans(tup=(CopyPlan(fields=('content_indent', 'open_start', 'open_next', 'began_empty')), EqPlan(fields=('cont"
        "ent_indent', 'open_start', 'open_next', 'began_empty')), FrozenPlan(fields=('content_indent', 'open_start', 'o"
        "pen_next', 'began_empty'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('content_indent',"
        " 'open_start', 'open_next', 'began_empty'), cache=False), InitPlan(fields=(InitPlan.Field(name='content_indent"
        "', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override="
        "False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='open_"
        "start', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, over"
        "ride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='"
        "open_next', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, "
        "override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(na"
        "me='began_empty', annotation=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default"
        "'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None"
        ", check_type=None)), self_param='self', std_params=('content_indent', 'open_start', 'open_next', 'began_empty'"
        "), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan"
        "(fields=(ReprPlan.Field(name='content_indent', kw_only=False, fn=None), ReprPlan.Field(name='open_start', kw_o"
        "nly=False, fn=None), ReprPlan.Field(name='open_next', kw_only=False, fn=None), ReprPlan.Field(name='began_empt"
        "y', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='4610be8cbe9931a0c893c78cc1404838f9193981',
    cls_names=(
        ('omxtra.text.pdcmark.blocks.containers', 'OpenItem'),
    ),
)
def _process_dataclass__4610be8cbe9931a0c893c78cc1404838f9193981():
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
                content_indent=self.content_indent,
                open_start=self.open_start,
                open_next=self.open_next,
                began_empty=self.began_empty,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.content_indent == other.content_indent and
                self.open_start == other.open_start and
                self.open_next == other.open_next and
                self.began_empty == other.began_empty
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'content_indent',
            'open_start',
            'open_next',
            'began_empty',
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
                self.content_indent,
                self.open_start,
                self.open_next,
                self.began_empty,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            content_indent: __dataclass__init__fields__0__annotation,
            open_start: __dataclass__init__fields__1__annotation,
            open_next: __dataclass__init__fields__2__annotation,
            began_empty: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'content_indent', content_indent)
            __dataclass__object_setattr(self, 'open_start', open_start)
            __dataclass__object_setattr(self, 'open_next', open_next)
            __dataclass__object_setattr(self, 'began_empty', began_empty)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"content_indent={self.content_indent!r}")
            parts.append(f"open_start={self.open_start!r}")
            parts.append(f"open_next={self.open_next!r}")
            parts.append(f"began_empty={self.began_empty!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('is_ordered', 'marker_char', 'start', 'open_start', 'had_blank', 'is_loose')), EqP"
        "lan(fields=('is_ordered', 'marker_char', 'start', 'open_start', 'had_blank', 'is_loose')), FrozenPlan(fields=("
        "'is_ordered', 'marker_char', 'start', 'open_start', 'had_blank', 'is_loose'), allow_dynamic_dunder_attrs=False"
        "), HashPlan(action='add', fields=('is_ordered', 'marker_char', 'start', 'open_start', 'had_blank', 'is_loose')"
        ", cache=False), InitPlan(fields=(InitPlan.Field(name='is_ordered', annotation=OpRef(name='init.fields.0.annota"
        "tion'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=N"
        "one, validate=None, check_type=None), InitPlan.Field(name='marker_char', annotation=OpRef(name='init.fields.1."
        "annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, co"
        "erce=None, validate=None, check_type=None), InitPlan.Field(name='start', annotation=OpRef(name='init.fields.2."
        "annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, co"
        "erce=None, validate=None, check_type=None), InitPlan.Field(name='open_start', annotation=OpRef(name='init.fiel"
        "ds.3.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANC"
        "E, coerce=None, validate=None, check_type=None), InitPlan.Field(name='had_blank', annotation=OpRef(name='init."
        "fields.4.annotation'), default=OpRef(name='init.fields.4.default'), default_factory=None, init=True, override="
        "False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='is_lo"
        "ose', annotation=OpRef(name='init.fields.5.annotation'), default=OpRef(name='init.fields.5.default'), default_"
        "factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type"
        "=None)), self_param='self', std_params=('is_ordered', 'marker_char', 'start', 'open_start', 'had_blank', 'is_l"
        "oose'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), Rep"
        "rPlan(fields=(ReprPlan.Field(name='is_ordered', kw_only=False, fn=None), ReprPlan.Field(name='marker_char', kw"
        "_only=False, fn=None), ReprPlan.Field(name='start', kw_only=False, fn=None), ReprPlan.Field(name='open_start',"
        " kw_only=False, fn=None), ReprPlan.Field(name='had_blank', kw_only=False, fn=None), ReprPlan.Field(name='is_lo"
        "ose', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='0a12b8cecba0aa485658b551073b6901af53f13a',
    cls_names=(
        ('omxtra.text.pdcmark.blocks.containers', 'OpenList'),
    ),
)
def _process_dataclass__0a12b8cecba0aa485658b551073b6901af53f13a():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
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
                is_ordered=self.is_ordered,
                marker_char=self.marker_char,
                start=self.start,
                open_start=self.open_start,
                had_blank=self.had_blank,
                is_loose=self.is_loose,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.is_ordered == other.is_ordered and
                self.marker_char == other.marker_char and
                self.start == other.start and
                self.open_start == other.open_start and
                self.had_blank == other.had_blank and
                self.is_loose == other.is_loose
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'is_ordered',
            'marker_char',
            'start',
            'open_start',
            'had_blank',
            'is_loose',
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
                self.is_ordered,
                self.marker_char,
                self.start,
                self.open_start,
                self.had_blank,
                self.is_loose,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            is_ordered: __dataclass__init__fields__0__annotation,
            marker_char: __dataclass__init__fields__1__annotation,
            start: __dataclass__init__fields__2__annotation,
            open_start: __dataclass__init__fields__3__annotation,
            had_blank: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            is_loose: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'is_ordered', is_ordered)
            __dataclass__object_setattr(self, 'marker_char', marker_char)
            __dataclass__object_setattr(self, 'start', start)
            __dataclass__object_setattr(self, 'open_start', open_start)
            __dataclass__object_setattr(self, 'had_blank', had_blank)
            __dataclass__object_setattr(self, 'is_loose', is_loose)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"is_ordered={self.is_ordered!r}")
            parts.append(f"marker_char={self.marker_char!r}")
            parts.append(f"start={self.start!r}")
            parts.append(f"open_start={self.open_start!r}")
            parts.append(f"had_blank={self.had_blank!r}")
            parts.append(f"is_loose={self.is_loose!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('text', 'line_start', 'line_next')), EqPlan(fields=('text', 'line_start', 'line_ne"
        "xt')), FrozenPlan(fields=('text', 'line_start', 'line_next'), allow_dynamic_dunder_attrs=False), HashPlan(acti"
        "on='add', fields=('text', 'line_start', 'line_next'), cache=False), InitPlan(fields=(InitPlan.Field(name='text"
        "', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override="
        "False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='line_"
        "start', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, over"
        "ride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='"
        "line_next', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, "
        "override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self"
        "', std_params=('text', 'line_start', 'line_next'), kw_only_params=(), frozen=True, slots=False, post_init_para"
        "ms=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='text', kw_only=False, fn=None), "
        "ReprPlan.Field(name='line_start', kw_only=False, fn=None), ReprPlan.Field(name='line_next', kw_only=False, fn="
        "None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='09be7c3cbeca615725bc0040391ebc1be2dd71cb',
    cls_names=(
        ('omxtra.text.pdcmark.blocks.leaves', 'BufferedLine'),
    ),
)
def _process_dataclass__09be7c3cbeca615725bc0040391ebc1be2dd71cb():
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
                text=self.text,
                line_start=self.line_start,
                line_next=self.line_next,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.text == other.text and
                self.line_start == other.line_start and
                self.line_next == other.line_next
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'text',
            'line_start',
            'line_next',
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
                self.line_start,
                self.line_next,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            text: __dataclass__init__fields__0__annotation,
            line_start: __dataclass__init__fields__1__annotation,
            line_next: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'text', text)
            __dataclass__object_setattr(self, 'line_start', line_start)
            __dataclass__object_setattr(self, 'line_next', line_next)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"text={self.text!r}")
            parts.append(f"line_start={self.line_start!r}")
            parts.append(f"line_next={self.line_next!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('fence_char', 'fence_length', 'fence_indent', 'info', 'open_start', 'open_next', '"
        "content')), EqPlan(fields=('fence_char', 'fence_length', 'fence_indent', 'info', 'open_start', 'open_next', 'c"
        "ontent')), FrozenPlan(fields=('fence_char', 'fence_length', 'fence_indent', 'info', 'open_start', 'open_next',"
        " 'content'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('fence_char', 'fence_length', '"
        "fence_indent', 'info', 'open_start', 'open_next', 'content'), cache=False), InitPlan(fields=(InitPlan.Field(na"
        "me='fence_char', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=T"
        "rue, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Fie"
        "ld(name='fence_length', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None,"
        " init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitP"
        "lan.Field(name='fence_indent', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factor"
        "y=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)"
        ", InitPlan.Field(name='info', annotation=OpRef(name='init.fields.3.annotation'), default=None, default_factory"
        "=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),"
        " InitPlan.Field(name='open_start', annotation=OpRef(name='init.fields.4.annotation'), default=None, default_fa"
        "ctory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=N"
        "one), InitPlan.Field(name='open_next', annotation=OpRef(name='init.fields.5.annotation'), default=None, defaul"
        "t_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_ty"
        "pe=None), InitPlan.Field(name='content', annotation=OpRef(name='init.fields.6.annotation'), default=None, defa"
        "ult_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_"
        "type=None)), self_param='self', std_params=('fence_char', 'fence_length', 'fence_indent', 'info', 'open_start'"
        ", 'open_next', 'content'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), va"
        "lidate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='fence_char', kw_only=False, fn=None), ReprPlan.Field(nam"
        "e='fence_length', kw_only=False, fn=None), ReprPlan.Field(name='fence_indent', kw_only=False, fn=None), ReprPl"
        "an.Field(name='info', kw_only=False, fn=None), ReprPlan.Field(name='open_start', kw_only=False, fn=None), Repr"
        "Plan.Field(name='open_next', kw_only=False, fn=None), ReprPlan.Field(name='content', kw_only=False, fn=None)),"
        " id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='21ad90326076404474ddf34fc8dab77e52bbc92e',
    cls_names=(
        ('omxtra.text.pdcmark.blocks.leaves', 'OpenFencedCode'),
    ),
)
def _process_dataclass__21ad90326076404474ddf34fc8dab77e52bbc92e():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__4__annotation,
        __dataclass__init__fields__5__annotation,
        __dataclass__init__fields__6__annotation,
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
                fence_char=self.fence_char,
                fence_length=self.fence_length,
                fence_indent=self.fence_indent,
                info=self.info,
                open_start=self.open_start,
                open_next=self.open_next,
                content=self.content,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.fence_char == other.fence_char and
                self.fence_length == other.fence_length and
                self.fence_indent == other.fence_indent and
                self.info == other.info and
                self.open_start == other.open_start and
                self.open_next == other.open_next and
                self.content == other.content
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'fence_char',
            'fence_length',
            'fence_indent',
            'info',
            'open_start',
            'open_next',
            'content',
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
                self.fence_char,
                self.fence_length,
                self.fence_indent,
                self.info,
                self.open_start,
                self.open_next,
                self.content,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            fence_char: __dataclass__init__fields__0__annotation,
            fence_length: __dataclass__init__fields__1__annotation,
            fence_indent: __dataclass__init__fields__2__annotation,
            info: __dataclass__init__fields__3__annotation,
            open_start: __dataclass__init__fields__4__annotation,
            open_next: __dataclass__init__fields__5__annotation,
            content: __dataclass__init__fields__6__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'fence_char', fence_char)
            __dataclass__object_setattr(self, 'fence_length', fence_length)
            __dataclass__object_setattr(self, 'fence_indent', fence_indent)
            __dataclass__object_setattr(self, 'info', info)
            __dataclass__object_setattr(self, 'open_start', open_start)
            __dataclass__object_setattr(self, 'open_next', open_next)
            __dataclass__object_setattr(self, 'content', content)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"fence_char={self.fence_char!r}")
            parts.append(f"fence_length={self.fence_length!r}")
            parts.append(f"fence_indent={self.fence_indent!r}")
            parts.append(f"info={self.info!r}")
            parts.append(f"open_start={self.open_start!r}")
            parts.append(f"open_next={self.open_next!r}")
            parts.append(f"content={self.content!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('html_type', 'open_start', 'lines')), EqPlan(fields=('html_type', 'open_start', 'l"
        "ines')), FrozenPlan(fields=('html_type', 'open_start', 'lines'), allow_dynamic_dunder_attrs=False), HashPlan(a"
        "ction='add', fields=('html_type', 'open_start', 'lines'), cache=False), InitPlan(fields=(InitPlan.Field(name='"
        "html_type', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, "
        "override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(na"
        "me='open_start', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=T"
        "rue, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Fie"
        "ld(name='lines', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=T"
        "rue, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param="
        "'self', std_params=('html_type', 'open_start', 'lines'), kw_only_params=(), frozen=True, slots=False, post_ini"
        "t_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='html_type', kw_only=False,"
        " fn=None), ReprPlan.Field(name='open_start', kw_only=False, fn=None), ReprPlan.Field(name='lines', kw_only=Fal"
        "se, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='01f1730dd87c622d5bd6eda384fd39438485b889',
    cls_names=(
        ('omxtra.text.pdcmark.blocks.leaves', 'OpenHtmlBlock'),
    ),
)
def _process_dataclass__01f1730dd87c622d5bd6eda384fd39438485b889():
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
                html_type=self.html_type,
                open_start=self.open_start,
                lines=self.lines,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.html_type == other.html_type and
                self.open_start == other.open_start and
                self.lines == other.lines
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'html_type',
            'open_start',
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
                self.html_type,
                self.open_start,
                self.lines,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            html_type: __dataclass__init__fields__0__annotation,
            open_start: __dataclass__init__fields__1__annotation,
            lines: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'html_type', html_type)
            __dataclass__object_setattr(self, 'open_start', open_start)
            __dataclass__object_setattr(self, 'lines', lines)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"html_type={self.html_type!r}")
            parts.append(f"open_start={self.open_start!r}")
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
        "Plans(tup=(CopyPlan(fields=('lines',)), EqPlan(fields=('lines',)), FrozenPlan(fields=('lines',), allow_dynamic"
        "_dunder_attrs=False), HashPlan(action='add', fields=('lines',), cache=False), InitPlan(fields=(InitPlan.Field("
        "name='lines', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True"
        ", override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='s"
        "elf', std_params=('lines',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), "
        "validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='lines', kw_only=False, fn=None),), id=False, terse=Fal"
        "se, default_fn=None)))"
    ),
    plan_repr_sha1='610a8f96e0bf5d331d060f28494af9acfba8eec7',
    cls_names=(
        ('omxtra.text.pdcmark.blocks.leaves', 'OpenIndentedCode'),
        ('omxtra.text.pdcmark.blocks.leaves', 'OpenParagraph'),
    ),
)
def _process_dataclass__610a8f96e0bf5d331d060f28494af9acfba8eec7():
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
                lines=self.lines,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.lines == other.lines
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
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
                self.lines,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            lines: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'lines', lines)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
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
        "Plans(tup=(CopyPlan(fields=('alignments', 'open_start')), EqPlan(fields=('alignments', 'open_start')), FrozenP"
        "lan(fields=('alignments', 'open_start'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('al"
        "ignments', 'open_start'), cache=False), InitPlan(fields=(InitPlan.Field(name='alignments', annotation=OpRef(na"
        "me='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=Fiel"
        "dType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='open_start', annotation=OpR"
        "ef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, field_type"
        "=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('alignments"
        "', 'open_start'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fn"
        "s=()), ReprPlan(fields=(ReprPlan.Field(name='alignments', kw_only=False, fn=None), ReprPlan.Field(name='open_s"
        "tart', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='8eb4719da5e01e5a5de49be8fb44b93b2d4abcb7',
    cls_names=(
        ('omxtra.text.pdcmark.blocks.leaves', 'OpenTable'),
    ),
)
def _process_dataclass__8eb4719da5e01e5a5de49be8fb44b93b2d4abcb7():
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
                alignments=self.alignments,
                open_start=self.open_start,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.alignments == other.alignments and
                self.open_start == other.open_start
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'alignments',
            'open_start',
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
                self.alignments,
                self.open_start,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            alignments: __dataclass__init__fields__0__annotation,
            open_start: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'alignments', alignments)
            __dataclass__object_setattr(self, 'open_start', open_start)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"alignments={self.alignments!r}")
            parts.append(f"open_start={self.open_start!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('dest', 'title')), EqPlan(fields=('dest', 'title')), FrozenPlan(fields=('dest', 't"
        "itle'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('dest', 'title'), cache=False), Init"
        "Plan(fields=(InitPlan.Field(name='dest', annotation=OpRef(name='init.fields.0.annotation'), default=None, defa"
        "ult_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_"
        "type=None), InitPlan.Field(name='title', annotation=OpRef(name='init.fields.1.annotation'), default=None, defa"
        "ult_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_"
        "type=None)), self_param='self', std_params=('dest', 'title'), kw_only_params=(), frozen=True, slots=False, pos"
        "t_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='dest', kw_only=False,"
        " fn=None), ReprPlan.Field(name='title', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='9c0ce0ea26c29a66732113469b244b5370df857a',
    cls_names=(
        ('omxtra.text.pdcmark.blocks.refdefs', 'LinkDef'),
    ),
)
def _process_dataclass__9c0ce0ea26c29a66732113469b244b5370df857a():
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
                dest=self.dest,
                title=self.title,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.dest == other.dest and
                self.title == other.title
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'dest',
            'title',
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
                self.dest,
                self.title,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            dest: __dataclass__init__fields__0__annotation,
            title: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'dest', dest)
            __dataclass__object_setattr(self, 'title', title)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"dest={self.dest!r}")
            parts.append(f"title={self.title!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('lines_consumed', 'label', 'link_def')), EqPlan(fields=('lines_consumed', 'label',"
        " 'link_def')), FrozenPlan(fields=('lines_consumed', 'label', 'link_def'), allow_dynamic_dunder_attrs=False), H"
        "ashPlan(action='add', fields=('lines_consumed', 'label', 'link_def'), cache=False), InitPlan(fields=(InitPlan."
        "Field(name='lines_consumed', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory="
        "None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), "
        "InitPlan.Field(name='label', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory="
        "None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), "
        "InitPlan.Field(name='link_def', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_facto"
        "ry=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None"
        ")), self_param='self', std_params=('lines_consumed', 'label', 'link_def'), kw_only_params=(), frozen=True, slo"
        "ts=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='lines_co"
        "nsumed', kw_only=False, fn=None), ReprPlan.Field(name='label', kw_only=False, fn=None), ReprPlan.Field(name='l"
        "ink_def', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='ea4c8c21d5247739ddbe50b76c2da881456660d3',
    cls_names=(
        ('omxtra.text.pdcmark.blocks.refdefs', 'RefDefMatch'),
    ),
)
def _process_dataclass__ea4c8c21d5247739ddbe50b76c2da881456660d3():
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
                lines_consumed=self.lines_consumed,
                label=self.label,
                link_def=self.link_def,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.lines_consumed == other.lines_consumed and
                self.label == other.label and
                self.link_def == other.link_def
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'lines_consumed',
            'label',
            'link_def',
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
                self.lines_consumed,
                self.label,
                self.link_def,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            lines_consumed: __dataclass__init__fields__0__annotation,
            label: __dataclass__init__fields__1__annotation,
            link_def: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'lines_consumed', lines_consumed)
            __dataclass__object_setattr(self, 'label', label)
            __dataclass__object_setattr(self, 'link_def', link_def)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"lines_consumed={self.lines_consumed!r}")
            parts.append(f"label={self.label!r}")
            parts.append(f"link_def={self.link_def!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('span', 'link_type', 'reference')), EqPlan(fields=('span', 'link_type', 'reference"
        "')), FrozenPlan(fields=('span', 'link_type', 'reference'), allow_dynamic_dunder_attrs=False), HashPlan(action="
        "'add', fields=('span', 'link_type', 'reference'), cache=False), InitPlan(fields=(InitPlan.Field(name='span', a"
        "nnotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=Fals"
        "e, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='link_type"
        "', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override="
        "False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='refer"
        "ence', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, overr"
        "ide=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', st"
        "d_params=('span', 'link_type', 'reference'), kw_only_params=(), frozen=True, slots=False, post_init_params=Non"
        "e, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='span', kw_only=False, fn=None), ReprPl"
        "an.Field(name='link_type', kw_only=False, fn=None), ReprPlan.Field(name='reference', kw_only=False, fn=None)),"
        " id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='9794b86a77a6237edc70735366efcbe2bd84c28f',
    cls_names=(
        ('omxtra.text.pdcmark.brokenlinks', 'BrokenLink'),
    ),
)
def _process_dataclass__9794b86a77a6237edc70735366efcbe2bd84c28f():
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
                span=self.span,
                link_type=self.link_type,
                reference=self.reference,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.span == other.span and
                self.link_type == other.link_type and
                self.reference == other.reference
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'span',
            'link_type',
            'reference',
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
                self.link_type,
                self.reference,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            span: __dataclass__init__fields__0__annotation,
            link_type: __dataclass__init__fields__1__annotation,
            reference: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'span', span)
            __dataclass__object_setattr(self, 'link_type', link_type)
            __dataclass__object_setattr(self, 'reference', reference)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"span={self.span!r}")
            parts.append(f"link_type={self.link_type!r}")
            parts.append(f"reference={self.reference!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('dest_url', 'title')), EqPlan(fields=('dest_url', 'title')), FrozenPlan(fields=('d"
        "est_url', 'title'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('dest_url', 'title'), ca"
        "che=False), InitPlan(fields=(InitPlan.Field(name='dest_url', annotation=OpRef(name='init.fields.0.annotation')"
        ", default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, v"
        "alidate=None, check_type=None), InitPlan.Field(name='title', annotation=OpRef(name='init.fields.1.annotation')"
        ", default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, v"
        "alidate=None, check_type=None)), self_param='self', std_params=('dest_url', 'title'), kw_only_params=(), froze"
        "n=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(nam"
        "e='dest_url', kw_only=False, fn=None), ReprPlan.Field(name='title', kw_only=False, fn=None)), id=False, terse="
        "False, default_fn=None)))"
    ),
    plan_repr_sha1='778b8e912dcb079c132ff562c4b2b32790478844',
    cls_names=(
        ('omxtra.text.pdcmark.brokenlinks', 'BrokenLinkResolution'),
    ),
)
def _process_dataclass__778b8e912dcb079c132ff562c4b2b32790478844():
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
                dest_url=self.dest_url,
                title=self.title,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.dest_url == other.dest_url and
                self.title == other.title
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'dest_url',
            'title',
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
                self.dest_url,
                self.title,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            dest_url: __dataclass__init__fields__0__annotation,
            title: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'dest_url', dest_url)
            __dataclass__object_setattr(self, 'title', title)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"dest_url={self.dest_url!r}")
            parts.append(f"title={self.title!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('kind',)), EqPlan(fields=('kind',)), FrozenPlan(fields=('kind',), allow_dynamic_du"
        "nder_attrs=False), HashPlan(action='add', fields=('kind',), cache=False), InitPlan(fields=(InitPlan.Field(name"
        "='kind', annotation=OpRef(name='init.fields.0.annotation'), default=OpRef(name='init.fields.0.default'), defau"
        "lt_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_t"
        "ype=None),), self_param='self', std_params=('kind',), kw_only_params=(), frozen=True, slots=False, post_init_p"
        "arams=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='kind', kw_only=False, fn=None"
        "),), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='3f5be9355acdf1b2d4bb8c8c12b6cc14d2605453',
    cls_names=(
        ('omxtra.text.pdcmark.events', 'BlockQuote'),
    ),
)
def _process_dataclass__3f5be9355acdf1b2d4bb8c8c12b6cc14d2605453():
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
                kind=self.kind,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.kind == other.kind
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
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
                self.kind,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            kind: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'kind', kind)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
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
        "Plans(tup=(CopyPlan(fields=('offset', 'text')), EqPlan(fields=('offset', 'text')), FrozenPlan(fields=('offset'"
        ", 'text'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('offset', 'text'), cache=False), "
        "InitPlan(fields=(InitPlan.Field(name='offset', annotation=OpRef(name='init.fields.0.annotation'), default=None"
        ", default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, "
        "check_type=None), InitPlan.Field(name='text', annotation=OpRef(name='init.fields.1.annotation'), default=None,"
        " default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, c"
        "heck_type=None)), self_param='self', std_params=('offset', 'text'), kw_only_params=(), frozen=True, slots=Fals"
        "e, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='offset', kw_onl"
        "y=False, fn=None), ReprPlan.Field(name='text', kw_only=False, fn=None)), id=False, terse=False, default_fn=Non"
        "e)))"
    ),
    plan_repr_sha1='97e0740ab965d4b6b7e832e5d055c3bd3b1a0f1f',
    cls_names=(
        ('omxtra.text.pdcmark.events', 'Code'),
        ('omxtra.text.pdcmark.events', 'Html'),
        ('omxtra.text.pdcmark.events', 'InlineHtml'),
        ('omxtra.text.pdcmark.events', 'Text'),
    ),
)
def _process_dataclass__97e0740ab965d4b6b7e832e5d055c3bd3b1a0f1f():
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
                offset=self.offset,
                text=self.text,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.offset == other.offset and
                self.text == other.text
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'offset',
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
                self.offset,
                self.text,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            offset: __dataclass__init__fields__0__annotation,
            text: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'offset', offset)
            __dataclass__object_setattr(self, 'text', text)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"offset={self.offset!r}")
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
        "Plans(tup=(CopyPlan(fields=()), EqPlan(fields=()), FrozenPlan(fields=(), allow_dynamic_dunder_attrs=False), Ha"
        "shPlan(action='add', fields=(), cache=False), InitPlan(fields=(), self_param='self', std_params=(), kw_only_pa"
        "rams=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(), i"
        "d=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='e1f7edfe11f2b721d6a656c46e698fedc95461bb',
    cls_names=(
        ('omxtra.text.pdcmark.events', 'Emphasis'),
        ('omxtra.text.pdcmark.events', 'HtmlBlock'),
        ('omxtra.text.pdcmark.events', 'IndentedCodeBlock'),
        ('omxtra.text.pdcmark.events', 'Item'),
        ('omxtra.text.pdcmark.events', 'Paragraph'),
        ('omxtra.text.pdcmark.events', 'Strikethrough'),
        ('omxtra.text.pdcmark.events', 'Strong'),
        ('omxtra.text.pdcmark.events', 'TableCell'),
        ('omxtra.text.pdcmark.events', 'TableHead'),
        ('omxtra.text.pdcmark.events', 'TableRow'),
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
        "Plans(tup=(CopyPlan(fields=('offset', 'tag')), EqPlan(fields=('offset', 'tag')), FrozenPlan(fields=('offset', "
        "'tag'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('offset', 'tag'), cache=False), Init"
        "Plan(fields=(InitPlan.Field(name='offset', annotation=OpRef(name='init.fields.0.annotation'), default=None, de"
        "fault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, chec"
        "k_type=None), InitPlan.Field(name='tag', annotation=OpRef(name='init.fields.1.annotation'), default=None, defa"
        "ult_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_"
        "type=None)), self_param='self', std_params=('offset', 'tag'), kw_only_params=(), frozen=True, slots=False, pos"
        "t_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='offset', kw_only=Fals"
        "e, fn=None), ReprPlan.Field(name='tag', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='9dfade586e5b9482317fbffae35d491e9863dfe9',
    cls_names=(
        ('omxtra.text.pdcmark.events', 'End'),
        ('omxtra.text.pdcmark.events', 'Start'),
    ),
)
def _process_dataclass__9dfade586e5b9482317fbffae35d491e9863dfe9():
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
                offset=self.offset,
                tag=self.tag,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.offset == other.offset and
                self.tag == other.tag
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'offset',
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
                self.offset,
                self.tag,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            offset: __dataclass__init__fields__0__annotation,
            tag: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'offset', offset)
            __dataclass__object_setattr(self, 'tag', tag)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"offset={self.offset!r}")
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
        "Plans(tup=(CopyPlan(fields=('info',)), EqPlan(fields=('info',)), FrozenPlan(fields=('info',), allow_dynamic_du"
        "nder_attrs=False), HashPlan(action='add', fields=('info',), cache=False), InitPlan(fields=(InitPlan.Field(name"
        "='info', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, ove"
        "rride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='self',"
        " std_params=('info',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), valida"
        "te_fns=()), ReprPlan(fields=(ReprPlan.Field(name='info', kw_only=False, fn=None),), id=False, terse=False, def"
        "ault_fn=None)))"
    ),
    plan_repr_sha1='1297c0162c2cacdc48359d2bf282d3e2019101f7',
    cls_names=(
        ('omxtra.text.pdcmark.events', 'FencedCodeBlock'),
    ),
)
def _process_dataclass__1297c0162c2cacdc48359d2bf282d3e2019101f7():
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
                info=self.info,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.info == other.info
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'info',
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
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            info: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'info', info)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"info={self.info!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('offset',)), EqPlan(fields=('offset',)), FrozenPlan(fields=('offset',), allow_dyna"
        "mic_dunder_attrs=False), HashPlan(action='add', fields=('offset',), cache=False), InitPlan(fields=(InitPlan.Fi"
        "eld(name='offset', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init"
        "=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_par"
        "am='self', std_params=('offset',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fn"
        "s=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='offset', kw_only=False, fn=None),), id=False, te"
        "rse=False, default_fn=None)))"
    ),
    plan_repr_sha1='030f89ec7f5defe7a6587163f1e64ddee0c04b34',
    cls_names=(
        ('omxtra.text.pdcmark.events', 'HardBreak'),
        ('omxtra.text.pdcmark.events', 'Rule'),
        ('omxtra.text.pdcmark.events', 'SoftBreak'),
        ('omxtra.text.pdcmark.events', '_OffsetEvent'),
    ),
)
def _process_dataclass__030f89ec7f5defe7a6587163f1e64ddee0c04b34():
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
                offset=self.offset,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.offset == other.offset
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
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

        def __hash__(self):
            return hash((
                self.offset,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            offset: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'offset', offset)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"offset={self.offset!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('level',)), EqPlan(fields=('level',)), FrozenPlan(fields=('level',), allow_dynamic"
        "_dunder_attrs=False), HashPlan(action='add', fields=('level',), cache=False), InitPlan(fields=(InitPlan.Field("
        "name='level', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True"
        ", override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='s"
        "elf', std_params=('level',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), "
        "validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='level', kw_only=False, fn=None),), id=False, terse=Fal"
        "se, default_fn=None)))"
    ),
    plan_repr_sha1='c657d65df1498def5df3519cd2e599886b5ed9f4',
    cls_names=(
        ('omxtra.text.pdcmark.events', 'Heading'),
    ),
)
def _process_dataclass__c657d65df1498def5df3519cd2e599886b5ed9f4():
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
                level=self.level,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.level == other.level
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'level',
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
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            level: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'level', level)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"level={self.level!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('link_type', 'dest_url', 'title', 'id')), EqPlan(fields=('link_type', 'dest_url', "
        "'title', 'id')), FrozenPlan(fields=('link_type', 'dest_url', 'title', 'id'), allow_dynamic_dunder_attrs=False)"
        ", HashPlan(action='add', fields=('link_type', 'dest_url', 'title', 'id'), cache=False), InitPlan(fields=(InitP"
        "lan.Field(name='link_type', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=N"
        "one, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), I"
        "nitPlan.Field(name='dest_url', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factor"
        "y=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)"
        ", InitPlan.Field(name='title', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factor"
        "y=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)"
        ", InitPlan.Field(name='id', annotation=OpRef(name='init.fields.3.annotation'), default=None, default_factory=N"
        "one, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), "
        "self_param='self', std_params=('link_type', 'dest_url', 'title', 'id'), kw_only_params=(), frozen=True, slots="
        "False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='link_type',"
        " kw_only=False, fn=None), ReprPlan.Field(name='dest_url', kw_only=False, fn=None), ReprPlan.Field(name='title'"
        ", kw_only=False, fn=None), ReprPlan.Field(name='id', kw_only=False, fn=None)), id=False, terse=False, default_"
        "fn=None)))"
    ),
    plan_repr_sha1='59783d3f1e0baa3ec39a6bc399650de4905e561c',
    cls_names=(
        ('omxtra.text.pdcmark.events', 'Image'),
        ('omxtra.text.pdcmark.events', 'Link'),
        ('omxtra.text.pdcmark.inlines.links', '_Resolved'),
    ),
)
def _process_dataclass__59783d3f1e0baa3ec39a6bc399650de4905e561c():
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
                link_type=self.link_type,
                dest_url=self.dest_url,
                title=self.title,
                id=self.id,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.link_type == other.link_type and
                self.dest_url == other.dest_url and
                self.title == other.title and
                self.id == other.id
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'link_type',
            'dest_url',
            'title',
            'id',
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
                self.link_type,
                self.dest_url,
                self.title,
                self.id,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            link_type: __dataclass__init__fields__0__annotation,
            dest_url: __dataclass__init__fields__1__annotation,
            title: __dataclass__init__fields__2__annotation,
            id: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'link_type', link_type)
            __dataclass__object_setattr(self, 'dest_url', dest_url)
            __dataclass__object_setattr(self, 'title', title)
            __dataclass__object_setattr(self, 'id', id)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"link_type={self.link_type!r}")
            parts.append(f"dest_url={self.dest_url!r}")
            parts.append(f"title={self.title!r}")
            parts.append(f"id={self.id!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('start', 'tight')), EqPlan(fields=('start', 'tight')), FrozenPlan(fields=('start',"
        " 'tight'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('start', 'tight'), cache=False), "
        "InitPlan(fields=(InitPlan.Field(name='start', annotation=OpRef(name='init.fields.0.annotation'), default=OpRef"
        "(name='init.fields.0.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE"
        ", coerce=None, validate=None, check_type=None), InitPlan.Field(name='tight', annotation=OpRef(name='init.field"
        "s.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False"
        ", field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params="
        "('start', 'tight'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_"
        "fns=()), ReprPlan(fields=(ReprPlan.Field(name='start', kw_only=False, fn=None), ReprPlan.Field(name='tight', k"
        "w_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='c5a0ff9b6e5038b5f82b3b9fbf3b7b8b42406706',
    cls_names=(
        ('omxtra.text.pdcmark.events', 'List'),
    ),
)
def _process_dataclass__c5a0ff9b6e5038b5f82b3b9fbf3b7b8b42406706():
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
                start=self.start,
                tight=self.tight,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.start == other.start and
                self.tight == other.tight
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'start',
            'tight',
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
                self.tight,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            start: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            tight: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'start', start)
            __dataclass__object_setattr(self, 'tight', tight)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"start={self.start!r}")
            parts.append(f"tight={self.tight!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('alignments',)), EqPlan(fields=('alignments',)), FrozenPlan(fields=('alignments',)"
        ", allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('alignments',), cache=False), InitPlan(fie"
        "lds=(InitPlan.Field(name='alignments', annotation=OpRef(name='init.fields.0.annotation'), default=None, defaul"
        "t_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_ty"
        "pe=None),), self_param='self', std_params=('alignments',), kw_only_params=(), frozen=True, slots=False, post_i"
        "nit_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='alignments', kw_only=Fal"
        "se, fn=None),), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='c8607306cc1b115e96f058b0dc108a3a982d10a0',
    cls_names=(
        ('omxtra.text.pdcmark.events', 'Table'),
    ),
)
def _process_dataclass__c8607306cc1b115e96f058b0dc108a3a982d10a0():
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
                alignments=self.alignments,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.alignments == other.alignments
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'alignments',
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
                self.alignments,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            alignments: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'alignments', alignments)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"alignments={self.alignments!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('offset', 'checked')), EqPlan(fields=('offset', 'checked')), FrozenPlan(fields=('o"
        "ffset', 'checked'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('offset', 'checked'), ca"
        "che=False), InitPlan(fields=(InitPlan.Field(name='offset', annotation=OpRef(name='init.fields.0.annotation'), "
        "default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, val"
        "idate=None, check_type=None), InitPlan.Field(name='checked', annotation=OpRef(name='init.fields.1.annotation')"
        ", default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, v"
        "alidate=None, check_type=None)), self_param='self', std_params=('offset', 'checked'), kw_only_params=(), froze"
        "n=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(nam"
        "e='offset', kw_only=False, fn=None), ReprPlan.Field(name='checked', kw_only=False, fn=None)), id=False, terse="
        "False, default_fn=None)))"
    ),
    plan_repr_sha1='d8c91b6764e1050a74c91dabb6f74845be507320',
    cls_names=(
        ('omxtra.text.pdcmark.events', 'TaskListMarker'),
    ),
)
def _process_dataclass__d8c91b6764e1050a74c91dabb6f74845be507320():
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
                offset=self.offset,
                checked=self.checked,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.offset == other.offset and
                self.checked == other.checked
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'offset',
            'checked',
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
                self.offset,
                self.checked,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            offset: __dataclass__init__fields__0__annotation,
            checked: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'offset', offset)
            __dataclass__object_setattr(self, 'checked', checked)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"offset={self.offset!r}")
            parts.append(f"checked={self.checked!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('remaining',)), EqPlan(fields=('remaining',)), HashPlan(action='set_none', fields="
        "None, cache=None), InitPlan(fields=(InitPlan.Field(name='remaining', annotation=OpRef(name='init.fields.0.anno"
        "tation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce"
        "=None, validate=None, check_type=None),), self_param='self', std_params=('remaining',), kw_only_params=(), fro"
        "zen=False, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field("
        "name='remaining', kw_only=False, fn=None),), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='c431f0482fabe055164f0d04224947b0be007de5',
    cls_names=(
        ('omxtra.text.pdcmark.inlines.links', 'Fuel'),
    ),
)
def _process_dataclass__c431f0482fabe055164f0d04224947b0be007de5():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                remaining=self.remaining,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.remaining == other.remaining
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            remaining: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            self.remaining = remaining

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"remaining={self.remaining!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('node_index', 'is_image', 'active')), EqPlan(fields=('node_index', 'is_image', 'ac"
        "tive')), HashPlan(action='set_none', fields=None, cache=None), InitPlan(fields=(InitPlan.Field(name='node_inde"
        "x', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override"
        "=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='is_i"
        "mage', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, overr"
        "ide=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='a"
        "ctive', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, over"
        "ride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', s"
        "td_params=('node_index', 'is_image', 'active'), kw_only_params=(), frozen=False, slots=False, post_init_params"
        "=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='node_index', kw_only=False, fn=Non"
        "e), ReprPlan.Field(name='is_image', kw_only=False, fn=None), ReprPlan.Field(name='active', kw_only=False, fn=N"
        "one)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='b430cf6fed0b56b5862b48e762daa962109ed8de',
    cls_names=(
        ('omxtra.text.pdcmark.inlines.links', '_LinkStackEntry'),
    ),
)
def _process_dataclass__b430cf6fed0b56b5862b48e762daa962109ed8de():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                node_index=self.node_index,
                is_image=self.is_image,
                active=self.active,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.node_index == other.node_index and
                self.is_image == other.is_image and
                self.active == other.active
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            node_index: __dataclass__init__fields__0__annotation,
            is_image: __dataclass__init__fields__1__annotation,
            active: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            self.node_index = node_index
            self.is_image = is_image
            self.active = active

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"node_index={self.node_index!r}")
            parts.append(f"is_image={self.is_image!r}")
            parts.append(f"active={self.active!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('offset', 'target', 'is_email')), EqPlan(fields=('offset', 'target', 'is_email')),"
        " HashPlan(action='set_none', fields=None, cache=None), InitPlan(fields=(InitPlan.Field(name='offset', annotati"
        "on=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, fiel"
        "d_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='target', annotat"
        "ion=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, fie"
        "ld_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='is_email', anno"
        "tation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=False, "
        "field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('"
        "offset', 'target', 'is_email'), kw_only_params=(), frozen=False, slots=False, post_init_params=None, init_fns="
        "(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='offset', kw_only=False, fn=None), ReprPlan.Field(n"
        "ame='target', kw_only=False, fn=None), ReprPlan.Field(name='is_email', kw_only=False, fn=None)), id=False, ter"
        "se=False, default_fn=None)))"
    ),
    plan_repr_sha1='fb295fcb76eb45194083b59d5ab764ef63d25246',
    cls_names=(
        ('omxtra.text.pdcmark.inlines.nodes', 'AutolinkNode'),
    ),
)
def _process_dataclass__fb295fcb76eb45194083b59d5ab764ef63d25246():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                offset=self.offset,
                target=self.target,
                is_email=self.is_email,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.offset == other.offset and
                self.target == other.target and
                self.is_email == other.is_email
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            offset: __dataclass__init__fields__0__annotation,
            target: __dataclass__init__fields__1__annotation,
            is_email: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            self.offset = offset
            self.target = target
            self.is_email = is_email

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"offset={self.offset!r}")
            parts.append(f"target={self.target!r}")
            parts.append(f"is_email={self.is_email!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('offset', 'text')), EqPlan(fields=('offset', 'text')), HashPlan(action='set_none',"
        " fields=None, cache=None), InitPlan(fields=(InitPlan.Field(name='offset', annotation=OpRef(name='init.fields.0"
        ".annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, c"
        "oerce=None, validate=None, check_type=None), InitPlan.Field(name='text', annotation=OpRef(name='init.fields.1."
        "annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, co"
        "erce=None, validate=None, check_type=None)), self_param='self', std_params=('offset', 'text'), kw_only_params="
        "(), frozen=False, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan"
        ".Field(name='offset', kw_only=False, fn=None), ReprPlan.Field(name='text', kw_only=False, fn=None)), id=False,"
        " terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='a2a86acf3d3bd47481ddfeceb58346fdf602dabb',
    cls_names=(
        ('omxtra.text.pdcmark.inlines.nodes', 'CodeNode'),
        ('omxtra.text.pdcmark.inlines.nodes', 'HtmlNode'),
        ('omxtra.text.pdcmark.inlines.nodes', 'TextNode'),
    ),
)
def _process_dataclass__a2a86acf3d3bd47481ddfeceb58346fdf602dabb():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                offset=self.offset,
                text=self.text,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.offset == other.offset and
                self.text == other.text
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            offset: __dataclass__init__fields__0__annotation,
            text: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            self.offset = offset
            self.text = text

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"offset={self.offset!r}")
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
        "Plans(tup=(CopyPlan(fields=('offset', 'char', 'count', 'can_open', 'can_close', 'original_count')), EqPlan(fie"
        "lds=('offset', 'char', 'count', 'can_open', 'can_close', 'original_count')), HashPlan(action='set_none', field"
        "s=None, cache=None), InitPlan(fields=(InitPlan.Field(name='offset', annotation=OpRef(name='init.fields.0.annot"
        "ation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce="
        "None, validate=None, check_type=None), InitPlan.Field(name='char', annotation=OpRef(name='init.fields.1.annota"
        "tion'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=N"
        "one, validate=None, check_type=None), InitPlan.Field(name='count', annotation=OpRef(name='init.fields.2.annota"
        "tion'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=N"
        "one, validate=None, check_type=None), InitPlan.Field(name='can_open', annotation=OpRef(name='init.fields.3.ann"
        "otation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerc"
        "e=None, validate=None, check_type=None), InitPlan.Field(name='can_close', annotation=OpRef(name='init.fields.4"
        ".annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, c"
        "oerce=None, validate=None, check_type=None), InitPlan.Field(name='original_count', annotation=OpRef(name='init"
        ".fields.5.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.IN"
        "STANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('offset', 'char', 'count"
        "', 'can_open', 'can_close', 'original_count'), kw_only_params=(), frozen=False, slots=False, post_init_params="
        "None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='offset', kw_only=False, fn=None), R"
        "eprPlan.Field(name='char', kw_only=False, fn=None), ReprPlan.Field(name='count', kw_only=False, fn=None), Repr"
        "Plan.Field(name='can_open', kw_only=False, fn=None), ReprPlan.Field(name='can_close', kw_only=False, fn=None),"
        " ReprPlan.Field(name='original_count', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='6fa2718b84ea4ebc409b668174a2559e9e14b32e',
    cls_names=(
        ('omxtra.text.pdcmark.inlines.nodes', 'DelimNode'),
    ),
)
def _process_dataclass__6fa2718b84ea4ebc409b668174a2559e9e14b32e():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__4__annotation,
        __dataclass__init__fields__5__annotation,
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                offset=self.offset,
                char=self.char,
                count=self.count,
                can_open=self.can_open,
                can_close=self.can_close,
                original_count=self.original_count,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.offset == other.offset and
                self.char == other.char and
                self.count == other.count and
                self.can_open == other.can_open and
                self.can_close == other.can_close and
                self.original_count == other.original_count
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            offset: __dataclass__init__fields__0__annotation,
            char: __dataclass__init__fields__1__annotation,
            count: __dataclass__init__fields__2__annotation,
            can_open: __dataclass__init__fields__3__annotation,
            can_close: __dataclass__init__fields__4__annotation,
            original_count: __dataclass__init__fields__5__annotation,
        ) -> __dataclass__None:
            self.offset = offset
            self.char = char
            self.count = count
            self.can_open = can_open
            self.can_close = can_close
            self.original_count = original_count

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"offset={self.offset!r}")
            parts.append(f"char={self.char!r}")
            parts.append(f"count={self.count!r}")
            parts.append(f"can_open={self.can_open!r}")
            parts.append(f"can_close={self.can_close!r}")
            parts.append(f"original_count={self.original_count!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('offset', 'kind', 'children')), EqPlan(fields=('offset', 'kind', 'children')), Has"
        "hPlan(action='set_none', fields=None, cache=None), InitPlan(fields=(InitPlan.Field(name='offset', annotation=O"
        "pRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_ty"
        "pe=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='kind', annotation=Op"
        "Ref(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, field_typ"
        "e=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='children', annotation"
        "=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=False, field_"
        "type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('offset"
        "', 'kind', 'children'), kw_only_params=(), frozen=False, slots=False, post_init_params=None, init_fns=(), vali"
        "date_fns=()), ReprPlan(fields=(ReprPlan.Field(name='offset', kw_only=False, fn=None), ReprPlan.Field(name='kin"
        "d', kw_only=False, fn=None), ReprPlan.Field(name='children', kw_only=False, fn=None)), id=False, terse=False, "
        "default_fn=None)))"
    ),
    plan_repr_sha1='c2a11cd52e17110bb4381e8f938eec9ba6179cbb',
    cls_names=(
        ('omxtra.text.pdcmark.inlines.nodes', 'EmphasisGroup'),
    ),
)
def _process_dataclass__c2a11cd52e17110bb4381e8f938eec9ba6179cbb():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                offset=self.offset,
                kind=self.kind,
                children=self.children,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.offset == other.offset and
                self.kind == other.kind and
                self.children == other.children
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            offset: __dataclass__init__fields__0__annotation,
            kind: __dataclass__init__fields__1__annotation,
            children: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            self.offset = offset
            self.kind = kind
            self.children = children

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"offset={self.offset!r}")
            parts.append(f"kind={self.kind!r}")
            parts.append(f"children={self.children!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('offset',)), EqPlan(fields=('offset',)), HashPlan(action='set_none', fields=None, "
        "cache=None), InitPlan(fields=(InitPlan.Field(name='offset', annotation=OpRef(name='init.fields.0.annotation'),"
        " default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, va"
        "lidate=None, check_type=None),), self_param='self', std_params=('offset',), kw_only_params=(), frozen=False, s"
        "lots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='offset"
        "', kw_only=False, fn=None),), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='3e00211e6a72d5f070161d015c11e3bc8dc599b3',
    cls_names=(
        ('omxtra.text.pdcmark.inlines.nodes', 'HardBreakNode'),
        ('omxtra.text.pdcmark.inlines.nodes', 'SoftBreakNode'),
    ),
)
def _process_dataclass__3e00211e6a72d5f070161d015c11e3bc8dc599b3():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                offset=self.offset,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.offset == other.offset
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            offset: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            self.offset = offset

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"offset={self.offset!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('offset', 'consumed_end', 'kind', 'raw_consumed', 'dest_url', 'title', 'label', 's"
        "uffix_joined', 'joined_start')), EqPlan(fields=('offset', 'consumed_end', 'kind', 'raw_consumed', 'dest_url', "
        "'title', 'label', 'suffix_joined', 'joined_start')), HashPlan(action='set_none', fields=None, cache=None), Ini"
        "tPlan(fields=(InitPlan.Field(name='offset', annotation=OpRef(name='init.fields.0.annotation'), default=None, d"
        "efault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, che"
        "ck_type=None), InitPlan.Field(name='consumed_end', annotation=OpRef(name='init.fields.1.annotation'), default="
        "None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=No"
        "ne, check_type=None), InitPlan.Field(name='kind', annotation=OpRef(name='init.fields.2.annotation'), default=N"
        "one, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=Non"
        "e, check_type=None), InitPlan.Field(name='raw_consumed', annotation=OpRef(name='init.fields.3.annotation'), de"
        "fault=OpRef(name='init.fields.3.default'), default_factory=None, init=True, override=False, field_type=FieldTy"
        "pe.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='dest_url', annotation=OpRef(na"
        "me='init.fields.4.annotation'), default=OpRef(name='init.fields.4.default'), default_factory=None, init=True, "
        "override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(na"
        "me='title', annotation=OpRef(name='init.fields.5.annotation'), default=OpRef(name='init.fields.5.default'), de"
        "fault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, chec"
        "k_type=None), InitPlan.Field(name='label', annotation=OpRef(name='init.fields.6.annotation'), default=OpRef(na"
        "me='init.fields.6.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, c"
        "oerce=None, validate=None, check_type=None), InitPlan.Field(name='suffix_joined', annotation=OpRef(name='init."
        "fields.7.annotation'), default=OpRef(name='init.fields.7.default'), default_factory=None, init=True, override="
        "False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='joine"
        "d_start', annotation=OpRef(name='init.fields.8.annotation'), default=OpRef(name='init.fields.8.default'), defa"
        "ult_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_"
        "type=None)), self_param='self', std_params=('offset', 'consumed_end', 'kind', 'raw_consumed', 'dest_url', 'tit"
        "le', 'label', 'suffix_joined', 'joined_start'), kw_only_params=(), frozen=False, slots=False, post_init_params"
        "=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='offset', kw_only=False, fn=None), "
        "ReprPlan.Field(name='consumed_end', kw_only=False, fn=None), ReprPlan.Field(name='kind', kw_only=False, fn=Non"
        "e), ReprPlan.Field(name='raw_consumed', kw_only=False, fn=None), ReprPlan.Field(name='dest_url', kw_only=False"
        ", fn=None), ReprPlan.Field(name='title', kw_only=False, fn=None), ReprPlan.Field(name='label', kw_only=False, "
        "fn=None), ReprPlan.Field(name='suffix_joined', kw_only=False, fn=None), ReprPlan.Field(name='joined_start', kw"
        "_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='4cc30e72ed846a97d02cb025d789a42764d964bb',
    cls_names=(
        ('omxtra.text.pdcmark.inlines.nodes', 'LinkCloseNode'),
    ),
)
def _process_dataclass__4cc30e72ed846a97d02cb025d789a42764d964bb():
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
        __dataclass__init__fields__7__annotation,
        __dataclass__init__fields__7__default,
        __dataclass__init__fields__8__annotation,
        __dataclass__init__fields__8__default,
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                offset=self.offset,
                consumed_end=self.consumed_end,
                kind=self.kind,
                raw_consumed=self.raw_consumed,
                dest_url=self.dest_url,
                title=self.title,
                label=self.label,
                suffix_joined=self.suffix_joined,
                joined_start=self.joined_start,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.offset == other.offset and
                self.consumed_end == other.consumed_end and
                self.kind == other.kind and
                self.raw_consumed == other.raw_consumed and
                self.dest_url == other.dest_url and
                self.title == other.title and
                self.label == other.label and
                self.suffix_joined == other.suffix_joined and
                self.joined_start == other.joined_start
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            offset: __dataclass__init__fields__0__annotation,
            consumed_end: __dataclass__init__fields__1__annotation,
            kind: __dataclass__init__fields__2__annotation,
            raw_consumed: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            dest_url: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            title: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            label: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
            suffix_joined: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
            joined_start: __dataclass__init__fields__8__annotation = __dataclass__init__fields__8__default,
        ) -> __dataclass__None:
            self.offset = offset
            self.consumed_end = consumed_end
            self.kind = kind
            self.raw_consumed = raw_consumed
            self.dest_url = dest_url
            self.title = title
            self.label = label
            self.suffix_joined = suffix_joined
            self.joined_start = joined_start

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"offset={self.offset!r}")
            parts.append(f"consumed_end={self.consumed_end!r}")
            parts.append(f"kind={self.kind!r}")
            parts.append(f"raw_consumed={self.raw_consumed!r}")
            parts.append(f"dest_url={self.dest_url!r}")
            parts.append(f"title={self.title!r}")
            parts.append(f"label={self.label!r}")
            parts.append(f"suffix_joined={self.suffix_joined!r}")
            parts.append(f"joined_start={self.joined_start!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('offset', 'is_image', 'link_type', 'dest_url', 'title', 'id', 'children')), EqPlan"
        "(fields=('offset', 'is_image', 'link_type', 'dest_url', 'title', 'id', 'children')), HashPlan(action='set_none"
        "', fields=None, cache=None), InitPlan(fields=(InitPlan.Field(name='offset', annotation=OpRef(name='init.fields"
        ".0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE,"
        " coerce=None, validate=None, check_type=None), InitPlan.Field(name='is_image', annotation=OpRef(name='init.fie"
        "lds.1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTAN"
        "CE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='link_type', annotation=OpRef(name='init"
        ".fields.2.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.IN"
        "STANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='dest_url', annotation=OpRef(name='i"
        "nit.fields.3.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType"
        ".INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='title', annotation=OpRef(name='i"
        "nit.fields.4.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType"
        ".INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='id', annotation=OpRef(name='init"
        ".fields.5.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.IN"
        "STANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='children', annotation=OpRef(name='i"
        "nit.fields.6.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType"
        ".INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('offset', 'is_image',"
        " 'link_type', 'dest_url', 'title', 'id', 'children'), kw_only_params=(), frozen=False, slots=False, post_init_"
        "params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='offset', kw_only=False, fn=N"
        "one), ReprPlan.Field(name='is_image', kw_only=False, fn=None), ReprPlan.Field(name='link_type', kw_only=False,"
        " fn=None), ReprPlan.Field(name='dest_url', kw_only=False, fn=None), ReprPlan.Field(name='title', kw_only=False"
        ", fn=None), ReprPlan.Field(name='id', kw_only=False, fn=None), ReprPlan.Field(name='children', kw_only=False, "
        "fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='8e4e6993d0b55ab695d424822fe4ccff8485b2c0',
    cls_names=(
        ('omxtra.text.pdcmark.inlines.nodes', 'LinkGroup'),
    ),
)
def _process_dataclass__8e4e6993d0b55ab695d424822fe4ccff8485b2c0():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__4__annotation,
        __dataclass__init__fields__5__annotation,
        __dataclass__init__fields__6__annotation,
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                offset=self.offset,
                is_image=self.is_image,
                link_type=self.link_type,
                dest_url=self.dest_url,
                title=self.title,
                id=self.id,
                children=self.children,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.offset == other.offset and
                self.is_image == other.is_image and
                self.link_type == other.link_type and
                self.dest_url == other.dest_url and
                self.title == other.title and
                self.id == other.id and
                self.children == other.children
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            offset: __dataclass__init__fields__0__annotation,
            is_image: __dataclass__init__fields__1__annotation,
            link_type: __dataclass__init__fields__2__annotation,
            dest_url: __dataclass__init__fields__3__annotation,
            title: __dataclass__init__fields__4__annotation,
            id: __dataclass__init__fields__5__annotation,
            children: __dataclass__init__fields__6__annotation,
        ) -> __dataclass__None:
            self.offset = offset
            self.is_image = is_image
            self.link_type = link_type
            self.dest_url = dest_url
            self.title = title
            self.id = id
            self.children = children

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"offset={self.offset!r}")
            parts.append(f"is_image={self.is_image!r}")
            parts.append(f"link_type={self.link_type!r}")
            parts.append(f"dest_url={self.dest_url!r}")
            parts.append(f"title={self.title!r}")
            parts.append(f"id={self.id!r}")
            parts.append(f"children={self.children!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('offset', 'is_image', 'joined_end')), EqPlan(fields=('offset', 'is_image', 'joined"
        "_end')), HashPlan(action='set_none', fields=None, cache=None), InitPlan(fields=(InitPlan.Field(name='offset', "
        "annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=Fal"
        "se, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='is_image"
        "', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override="
        "False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='joine"
        "d_end', annotation=OpRef(name='init.fields.2.annotation'), default=OpRef(name='init.fields.2.default'), defaul"
        "t_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_ty"
        "pe=None)), self_param='self', std_params=('offset', 'is_image', 'joined_end'), kw_only_params=(), frozen=False"
        ", slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='off"
        "set', kw_only=False, fn=None), ReprPlan.Field(name='is_image', kw_only=False, fn=None), ReprPlan.Field(name='j"
        "oined_end', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='2d4ea75aeb9982910f145b2e3be74a88965266e6',
    cls_names=(
        ('omxtra.text.pdcmark.inlines.nodes', 'LinkOpenNode'),
    ),
)
def _process_dataclass__2d4ea75aeb9982910f145b2e3be74a88965266e6():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default,
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                offset=self.offset,
                is_image=self.is_image,
                joined_end=self.joined_end,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.offset == other.offset and
                self.is_image == other.is_image and
                self.joined_end == other.joined_end
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            offset: __dataclass__init__fields__0__annotation,
            is_image: __dataclass__init__fields__1__annotation,
            joined_end: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            self.offset = offset
            self.is_image = is_image
            self.joined_end = joined_end

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"offset={self.offset!r}")
            parts.append(f"is_image={self.is_image!r}")
            parts.append(f"joined_end={self.joined_end!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('nodes', 'retokenize', 'raw_slice')), EqPlan(fields=('nodes', 'retokenize', 'raw_s"
        "lice')), FrozenPlan(fields=('nodes', 'retokenize', 'raw_slice'), allow_dynamic_dunder_attrs=False), HashPlan(a"
        "ction='add', fields=('nodes', 'retokenize', 'raw_slice'), cache=False), InitPlan(fields=(InitPlan.Field(name='"
        "nodes', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, over"
        "ride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='"
        "retokenize', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True,"
        " override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(n"
        "ame='raw_slice', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=T"
        "rue, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param="
        "'self', std_params=('nodes', 'retokenize', 'raw_slice'), kw_only_params=(), frozen=True, slots=False, post_ini"
        "t_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='nodes', kw_only=False, fn="
        "None), ReprPlan.Field(name='retokenize', kw_only=False, fn=None), ReprPlan.Field(name='raw_slice', kw_only=Fal"
        "se, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='f130a909203a702df904b602440105cb25dea97a',
    cls_names=(
        ('omxtra.text.pdcmark.inlines.tokenize', 'TokenizedBlock'),
    ),
)
def _process_dataclass__f130a909203a702df904b602440105cb25dea97a():
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
                nodes=self.nodes,
                retokenize=self.retokenize,
                raw_slice=self.raw_slice,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.nodes == other.nodes and
                self.retokenize == other.retokenize and
                self.raw_slice == other.raw_slice
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'nodes',
            'retokenize',
            'raw_slice',
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
                self.nodes,
                self.retokenize,
                self.raw_slice,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            nodes: __dataclass__init__fields__0__annotation,
            retokenize: __dataclass__init__fields__1__annotation,
            raw_slice: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'nodes', nodes)
            __dataclass__object_setattr(self, 'retokenize', retokenize)
            __dataclass__object_setattr(self, 'raw_slice', raw_slice)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"nodes={self.nodes!r}")
            parts.append(f"retokenize={self.retokenize!r}")
            parts.append(f"raw_slice={self.raw_slice!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('text', 'lines', 'line_starts')), EqPlan(fields=('text', 'lines', 'line_starts')),"
        " FrozenPlan(fields=('text', 'lines', 'line_starts'), allow_dynamic_dunder_attrs=False), HashPlan(action='add',"
        " fields=('text', 'lines', 'line_starts'), cache=False), InitPlan(fields=(InitPlan.Field(name='text', annotatio"
        "n=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field"
        "_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='lines', annotatio"
        "n=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, field"
        "_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='line_starts', ann"
        "otation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=False,"
        " field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=("
        "'text', 'lines', 'line_starts'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns="
        "(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='text', kw_only=False, fn=None), ReprPlan.Field(nam"
        "e='lines', kw_only=False, fn=None), ReprPlan.Field(name='line_starts', kw_only=False, fn=None)), id=False, ter"
        "se=False, default_fn=None)))"
    ),
    plan_repr_sha1='06fc25ca5253c374afebd4da3298f8ac13b0e756',
    cls_names=(
        ('omxtra.text.pdcmark.inlines.tokenize', '_Joined'),
    ),
)
def _process_dataclass__06fc25ca5253c374afebd4da3298f8ac13b0e756():
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
                text=self.text,
                lines=self.lines,
                line_starts=self.line_starts,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.text == other.text and
                self.lines == other.lines and
                self.line_starts == other.line_starts
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'text',
            'lines',
            'line_starts',
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
                self.lines,
                self.line_starts,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            text: __dataclass__init__fields__0__annotation,
            lines: __dataclass__init__fields__1__annotation,
            line_starts: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'text', text)
            __dataclass__object_setattr(self, 'lines', lines)
            __dataclass__object_setattr(self, 'line_starts', line_starts)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"text={self.text!r}")
            parts.append(f"lines={self.lines!r}")
            parts.append(f"line_starts={self.line_starts!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('joined_start', 'source_start', 'source_next', 'text_len')), EqPlan(fields=('joine"
        "d_start', 'source_start', 'source_next', 'text_len')), FrozenPlan(fields=('joined_start', 'source_start', 'sou"
        "rce_next', 'text_len'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('joined_start', 'sou"
        "rce_start', 'source_next', 'text_len'), cache=False), InitPlan(fields=(InitPlan.Field(name='joined_start', ann"
        "otation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False,"
        " field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='source_star"
        "t', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override"
        "=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='sour"
        "ce_next', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, ov"
        "erride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name"
        "='text_len', annotation=OpRef(name='init.fields.3.annotation'), default=None, default_factory=None, init=True,"
        " override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='sel"
        "f', std_params=('joined_start', 'source_start', 'source_next', 'text_len'), kw_only_params=(), frozen=True, sl"
        "ots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='joined_"
        "start', kw_only=False, fn=None), ReprPlan.Field(name='source_start', kw_only=False, fn=None), ReprPlan.Field(n"
        "ame='source_next', kw_only=False, fn=None), ReprPlan.Field(name='text_len', kw_only=False, fn=None)), id=False"
        ", terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='760ef82b87db34e4d3645e0f51eb43fac6f472b2',
    cls_names=(
        ('omxtra.text.pdcmark.inlines.tokenize', '_LineInfo'),
    ),
)
def _process_dataclass__760ef82b87db34e4d3645e0f51eb43fac6f472b2():
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
                joined_start=self.joined_start,
                source_start=self.source_start,
                source_next=self.source_next,
                text_len=self.text_len,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.joined_start == other.joined_start and
                self.source_start == other.source_start and
                self.source_next == other.source_next and
                self.text_len == other.text_len
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'joined_start',
            'source_start',
            'source_next',
            'text_len',
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
                self.joined_start,
                self.source_start,
                self.source_next,
                self.text_len,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            joined_start: __dataclass__init__fields__0__annotation,
            source_start: __dataclass__init__fields__1__annotation,
            source_next: __dataclass__init__fields__2__annotation,
            text_len: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'joined_start', joined_start)
            __dataclass__object_setattr(self, 'source_start', source_start)
            __dataclass__object_setattr(self, 'source_next', source_next)
            __dataclass__object_setattr(self, 'text_len', text_len)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"joined_start={self.joined_start!r}")
            parts.append(f"source_start={self.source_start!r}")
            parts.append(f"source_next={self.source_next!r}")
            parts.append(f"text_len={self.text_len!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('tables', 'strikethrough', 'tasklists', 'gfm_blockquote_kinds', 'max_nested_parens"
        "', 'max_container_depth', 'link_ref_expansion_min', 'prescan_refdefs', 'broken_link_resolver')), EqPlan(fields"
        "=('tables', 'strikethrough', 'tasklists', 'gfm_blockquote_kinds', 'max_nested_parens', 'max_container_depth', "
        "'link_ref_expansion_min', 'prescan_refdefs', 'broken_link_resolver')), FrozenPlan(fields=('tables', 'strikethr"
        "ough', 'tasklists', 'gfm_blockquote_kinds', 'max_nested_parens', 'max_container_depth', 'link_ref_expansion_mi"
        "n', 'prescan_refdefs', 'broken_link_resolver'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fiel"
        "ds=('tables', 'strikethrough', 'tasklists', 'gfm_blockquote_kinds', 'max_nested_parens', 'max_container_depth'"
        ", 'link_ref_expansion_min', 'prescan_refdefs', 'broken_link_resolver'), cache=False), InitPlan(fields=(InitPla"
        "n.Field(name='tables', annotation=OpRef(name='init.fields.0.annotation'), default=OpRef(name='init.fields.0.de"
        "fault'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate"
        "=None, check_type=None), InitPlan.Field(name='strikethrough', annotation=OpRef(name='init.fields.1.annotation'"
        "), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False, field_type=Fi"
        "eldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='tasklists', annotation=Op"
        "Ref(name='init.fields.2.annotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init="
        "True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Fi"
        "eld(name='gfm_blockquote_kinds', annotation=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.f"
        "ields.3.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None"
        ", validate=None, check_type=None), InitPlan.Field(name='max_nested_parens', annotation=OpRef(name='init.fields"
        ".4.annotation'), default=OpRef(name='init.fields.4.default'), default_factory=None, init=True, override=False,"
        " field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='max_contain"
        "er_depth', annotation=OpRef(name='init.fields.5.annotation'), default=OpRef(name='init.fields.5.default'), def"
        "ault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check"
        "_type=None), InitPlan.Field(name='link_ref_expansion_min', annotation=OpRef(name='init.fields.6.annotation'), "
        "default=OpRef(name='init.fields.6.default'), default_factory=None, init=True, override=False, field_type=Field"
        "Type.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='prescan_refdefs', annotation"
        "=OpRef(name='init.fields.7.annotation'), default=OpRef(name='init.fields.7.default'), default_factory=None, in"
        "it=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan"
        ".Field(name='broken_link_resolver', annotation=OpRef(name='init.fields.8.annotation'), default=OpRef(name='ini"
        "t.fields.8.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=N"
        "one, validate=None, check_type=None)), self_param='self', std_params=(), kw_only_params=('tables', 'strikethro"
        "ugh', 'tasklists', 'gfm_blockquote_kinds', 'max_nested_parens', 'max_container_depth', 'link_ref_expansion_min"
        "', 'prescan_refdefs', 'broken_link_resolver'), frozen=True, slots=False, post_init_params=None, init_fns=(), v"
        "alidate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='tables', kw_only=True, fn=None), ReprPlan.Field(name='s"
        "trikethrough', kw_only=True, fn=None), ReprPlan.Field(name='tasklists', kw_only=True, fn=None), ReprPlan.Field"
        "(name='gfm_blockquote_kinds', kw_only=True, fn=None), ReprPlan.Field(name='max_nested_parens', kw_only=True, f"
        "n=None), ReprPlan.Field(name='max_container_depth', kw_only=True, fn=None), ReprPlan.Field(name='link_ref_expa"
        "nsion_min', kw_only=True, fn=None), ReprPlan.Field(name='prescan_refdefs', kw_only=True, fn=None), ReprPlan.Fi"
        "eld(name='broken_link_resolver', kw_only=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='0096e0e753310a1953a10d84401ac73750a42aa6',
    cls_names=(
        ('omxtra.text.pdcmark.options', 'Options'),
    ),
)
def _process_dataclass__0096e0e753310a1953a10d84401ac73750a42aa6():
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
        __dataclass__init__fields__6__annotation,
        __dataclass__init__fields__6__default,
        __dataclass__init__fields__7__annotation,
        __dataclass__init__fields__7__default,
        __dataclass__init__fields__8__annotation,
        __dataclass__init__fields__8__default,
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
                tables=self.tables,
                strikethrough=self.strikethrough,
                tasklists=self.tasklists,
                gfm_blockquote_kinds=self.gfm_blockquote_kinds,
                max_nested_parens=self.max_nested_parens,
                max_container_depth=self.max_container_depth,
                link_ref_expansion_min=self.link_ref_expansion_min,
                prescan_refdefs=self.prescan_refdefs,
                broken_link_resolver=self.broken_link_resolver,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.tables == other.tables and
                self.strikethrough == other.strikethrough and
                self.tasklists == other.tasklists and
                self.gfm_blockquote_kinds == other.gfm_blockquote_kinds and
                self.max_nested_parens == other.max_nested_parens and
                self.max_container_depth == other.max_container_depth and
                self.link_ref_expansion_min == other.link_ref_expansion_min and
                self.prescan_refdefs == other.prescan_refdefs and
                self.broken_link_resolver == other.broken_link_resolver
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'tables',
            'strikethrough',
            'tasklists',
            'gfm_blockquote_kinds',
            'max_nested_parens',
            'max_container_depth',
            'link_ref_expansion_min',
            'prescan_refdefs',
            'broken_link_resolver',
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
                self.tables,
                self.strikethrough,
                self.tasklists,
                self.gfm_blockquote_kinds,
                self.max_nested_parens,
                self.max_container_depth,
                self.link_ref_expansion_min,
                self.prescan_refdefs,
                self.broken_link_resolver,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            tables: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            strikethrough: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            tasklists: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            gfm_blockquote_kinds: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            max_nested_parens: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            max_container_depth: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            link_ref_expansion_min: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
            prescan_refdefs: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
            broken_link_resolver: __dataclass__init__fields__8__annotation = __dataclass__init__fields__8__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'tables', tables)
            __dataclass__object_setattr(self, 'strikethrough', strikethrough)
            __dataclass__object_setattr(self, 'tasklists', tasklists)
            __dataclass__object_setattr(self, 'gfm_blockquote_kinds', gfm_blockquote_kinds)
            __dataclass__object_setattr(self, 'max_nested_parens', max_nested_parens)
            __dataclass__object_setattr(self, 'max_container_depth', max_container_depth)
            __dataclass__object_setattr(self, 'link_ref_expansion_min', link_ref_expansion_min)
            __dataclass__object_setattr(self, 'prescan_refdefs', prescan_refdefs)
            __dataclass__object_setattr(self, 'broken_link_resolver', broken_link_resolver)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"tables={self.tables!r}")
            parts.append(f"strikethrough={self.strikethrough!r}")
            parts.append(f"tasklists={self.tasklists!r}")
            parts.append(f"gfm_blockquote_kinds={self.gfm_blockquote_kinds!r}")
            parts.append(f"max_nested_parens={self.max_nested_parens!r}")
            parts.append(f"max_container_depth={self.max_container_depth!r}")
            parts.append(f"link_ref_expansion_min={self.link_ref_expansion_min!r}")
            parts.append(f"prescan_refdefs={self.prescan_refdefs!r}")
            parts.append(f"broken_link_resolver={self.broken_link_resolver!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('level', 'content_start', 'content_end')), EqPlan(fields=('level', 'content_start'"
        ", 'content_end')), FrozenPlan(fields=('level', 'content_start', 'content_end'), allow_dynamic_dunder_attrs=Fal"
        "se), HashPlan(action='add', fields=('level', 'content_start', 'content_end'), cache=False), InitPlan(fields=(I"
        "nitPlan.Field(name='level', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=N"
        "one, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), I"
        "nitPlan.Field(name='content_start', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_f"
        "actory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type="
        "None), InitPlan.Field(name='content_end', annotation=OpRef(name='init.fields.2.annotation'), default=None, def"
        "ault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check"
        "_type=None)), self_param='self', std_params=('level', 'content_start', 'content_end'), kw_only_params=(), froz"
        "en=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(na"
        "me='level', kw_only=False, fn=None), ReprPlan.Field(name='content_start', kw_only=False, fn=None), ReprPlan.Fi"
        "eld(name='content_end', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='24516b07a527090b1db30e4e83827919baef224e',
    cls_names=(
        ('omxtra.text.pdcmark.scanning.atx', 'AtxOpen'),
    ),
)
def _process_dataclass__24516b07a527090b1db30e4e83827919baef224e():
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
                level=self.level,
                content_start=self.content_start,
                content_end=self.content_end,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.level == other.level and
                self.content_start == other.content_start and
                self.content_end == other.content_end
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'level',
            'content_start',
            'content_end',
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
                self.content_start,
                self.content_end,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            level: __dataclass__init__fields__0__annotation,
            content_start: __dataclass__init__fields__1__annotation,
            content_end: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'level', level)
            __dataclass__object_setattr(self, 'content_start', content_start)
            __dataclass__object_setattr(self, 'content_end', content_end)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"level={self.level!r}")
            parts.append(f"content_start={self.content_start!r}")
            parts.append(f"content_end={self.content_end!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('end', 'target', 'is_email')), EqPlan(fields=('end', 'target', 'is_email')), Froze"
        "nPlan(fields=('end', 'target', 'is_email'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=("
        "'end', 'target', 'is_email'), cache=False), InitPlan(fields=(InitPlan.Field(name='end', annotation=OpRef(name="
        "'init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldTy"
        "pe.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='target', annotation=OpRef(name"
        "='init.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldT"
        "ype.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='is_email', annotation=OpRef(n"
        "ame='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=False, field_type=Fie"
        "ldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('end', 'target'"
        ", 'is_email'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=("
        ")), ReprPlan(fields=(ReprPlan.Field(name='end', kw_only=False, fn=None), ReprPlan.Field(name='target', kw_only"
        "=False, fn=None), ReprPlan.Field(name='is_email', kw_only=False, fn=None)), id=False, terse=False, default_fn="
        "None)))"
    ),
    plan_repr_sha1='ee0f9e5701128a07f382c143a25216bedb83e746',
    cls_names=(
        ('omxtra.text.pdcmark.scanning.autolinks', 'AutolinkMatch'),
    ),
)
def _process_dataclass__ee0f9e5701128a07f382c143a25216bedb83e746():
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
                end=self.end,
                target=self.target,
                is_email=self.is_email,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.end == other.end and
                self.target == other.target and
                self.is_email == other.is_email
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'end',
            'target',
            'is_email',
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
                self.end,
                self.target,
                self.is_email,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            end: __dataclass__init__fields__0__annotation,
            target: __dataclass__init__fields__1__annotation,
            is_email: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'end', end)
            __dataclass__object_setattr(self, 'target', target)
            __dataclass__object_setattr(self, 'is_email', is_email)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"end={self.end!r}")
            parts.append(f"target={self.target!r}")
            parts.append(f"is_email={self.is_email!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('end', 'decoded')), EqPlan(fields=('end', 'decoded')), FrozenPlan(fields=('end', '"
        "decoded'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('end', 'decoded'), cache=False), "
        "InitPlan(fields=(InitPlan.Field(name='end', annotation=OpRef(name='init.fields.0.annotation'), default=None, d"
        "efault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, che"
        "ck_type=None), InitPlan.Field(name='decoded', annotation=OpRef(name='init.fields.1.annotation'), default=None,"
        " default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, c"
        "heck_type=None)), self_param='self', std_params=('end', 'decoded'), kw_only_params=(), frozen=True, slots=Fals"
        "e, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='end', kw_only=F"
        "alse, fn=None), ReprPlan.Field(name='decoded', kw_only=False, fn=None)), id=False, terse=False, default_fn=Non"
        "e)))"
    ),
    plan_repr_sha1='9cc576a363965741551ddaf94ef20b2f7e9b151e',
    cls_names=(
        ('omxtra.text.pdcmark.scanning.entities', 'EntityMatch'),
    ),
)
def _process_dataclass__9cc576a363965741551ddaf94ef20b2f7e9b151e():
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
                end=self.end,
                decoded=self.decoded,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.end == other.end and
                self.decoded == other.decoded
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'end',
            'decoded',
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
                self.end,
                self.decoded,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            end: __dataclass__init__fields__0__annotation,
            decoded: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'end', end)
            __dataclass__object_setattr(self, 'decoded', decoded)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"end={self.end!r}")
            parts.append(f"decoded={self.decoded!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('fence_char', 'fence_length', 'indent', 'info')), EqPlan(fields=('fence_char', 'fe"
        "nce_length', 'indent', 'info')), FrozenPlan(fields=('fence_char', 'fence_length', 'indent', 'info'), allow_dyn"
        "amic_dunder_attrs=False), HashPlan(action='add', fields=('fence_char', 'fence_length', 'indent', 'info'), cach"
        "e=False), InitPlan(fields=(InitPlan.Field(name='fence_char', annotation=OpRef(name='init.fields.0.annotation')"
        ", default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, v"
        "alidate=None, check_type=None), InitPlan.Field(name='fence_length', annotation=OpRef(name='init.fields.1.annot"
        "ation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce="
        "None, validate=None, check_type=None), InitPlan.Field(name='indent', annotation=OpRef(name='init.fields.2.anno"
        "tation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce"
        "=None, validate=None, check_type=None), InitPlan.Field(name='info', annotation=OpRef(name='init.fields.3.annot"
        "ation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce="
        "None, validate=None, check_type=None)), self_param='self', std_params=('fence_char', 'fence_length', 'indent',"
        " 'info'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), R"
        "eprPlan(fields=(ReprPlan.Field(name='fence_char', kw_only=False, fn=None), ReprPlan.Field(name='fence_length',"
        " kw_only=False, fn=None), ReprPlan.Field(name='indent', kw_only=False, fn=None), ReprPlan.Field(name='info', k"
        "w_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='df2fcbef761e58921d69cac2fe4f24aad4498878',
    cls_names=(
        ('omxtra.text.pdcmark.scanning.fences', 'FenceOpen'),
    ),
)
def _process_dataclass__df2fcbef761e58921d69cac2fe4f24aad4498878():
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
                fence_char=self.fence_char,
                fence_length=self.fence_length,
                indent=self.indent,
                info=self.info,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.fence_char == other.fence_char and
                self.fence_length == other.fence_length and
                self.indent == other.indent and
                self.info == other.info
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'fence_char',
            'fence_length',
            'indent',
            'info',
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
                self.fence_char,
                self.fence_length,
                self.indent,
                self.info,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            fence_char: __dataclass__init__fields__0__annotation,
            fence_length: __dataclass__init__fields__1__annotation,
            indent: __dataclass__init__fields__2__annotation,
            info: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'fence_char', fence_char)
            __dataclass__object_setattr(self, 'fence_length', fence_length)
            __dataclass__object_setattr(self, 'indent', indent)
            __dataclass__object_setattr(self, 'info', info)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"fence_char={self.fence_char!r}")
            parts.append(f"fence_length={self.fence_length!r}")
            parts.append(f"indent={self.indent!r}")
            parts.append(f"info={self.info!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('type', 'can_interrupt_paragraph')), EqPlan(fields=('type', 'can_interrupt_paragra"
        "ph')), FrozenPlan(fields=('type', 'can_interrupt_paragraph'), allow_dynamic_dunder_attrs=False), HashPlan(acti"
        "on='add', fields=('type', 'can_interrupt_paragraph'), cache=False), InitPlan(fields=(InitPlan.Field(name='type"
        "', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override="
        "False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='can_i"
        "nterrupt_paragraph', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, in"
        "it=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_pa"
        "ram='self', std_params=('type', 'can_interrupt_paragraph'), kw_only_params=(), frozen=True, slots=False, post_"
        "init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='type', kw_only=False, f"
        "n=None), ReprPlan.Field(name='can_interrupt_paragraph', kw_only=False, fn=None)), id=False, terse=False, defau"
        "lt_fn=None)))"
    ),
    plan_repr_sha1='a44b262961c800bd2c35c06536a8f7aae563150f',
    cls_names=(
        ('omxtra.text.pdcmark.scanning.htmlblocks', 'HtmlBlockStart'),
    ),
)
def _process_dataclass__a44b262961c800bd2c35c06536a8f7aae563150f():
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
                type=self.type,
                can_interrupt_paragraph=self.can_interrupt_paragraph,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type and
                self.can_interrupt_paragraph == other.can_interrupt_paragraph
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'type',
            'can_interrupt_paragraph',
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
                self.can_interrupt_paragraph,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            type: __dataclass__init__fields__0__annotation,
            can_interrupt_paragraph: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'type', type)
            __dataclass__object_setattr(self, 'can_interrupt_paragraph', can_interrupt_paragraph)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"type={self.type!r}")
            parts.append(f"can_interrupt_paragraph={self.can_interrupt_paragraph!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('end',)), EqPlan(fields=('end',)), FrozenPlan(fields=('end',), allow_dynamic_dunde"
        "r_attrs=False), HashPlan(action='add', fields=('end',), cache=False), InitPlan(fields=(InitPlan.Field(name='en"
        "d', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override"
        "=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='self', std_"
        "params=('end',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns"
        "=()), ReprPlan(fields=(ReprPlan.Field(name='end', kw_only=False, fn=None),), id=False, terse=False, default_fn"
        "=None)))"
    ),
    plan_repr_sha1='cd5a62d47e1ea8c3a374b0e2db232f4607bb6e57',
    cls_names=(
        ('omxtra.text.pdcmark.scanning.inlinehtml', 'InlineHtmlMatch'),
    ),
)
def _process_dataclass__cd5a62d47e1ea8c3a374b0e2db232f4607bb6e57():
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
                end=self.end,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.end == other.end
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
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
                self.end,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            end: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'end', end)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
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
        "Plans(tup=(CopyPlan(fields=('end', 'dest')), EqPlan(fields=('end', 'dest')), FrozenPlan(fields=('end', 'dest')"
        ", allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('end', 'dest'), cache=False), InitPlan(fie"
        "lds=(InitPlan.Field(name='end', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_facto"
        "ry=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None"
        "), InitPlan.Field(name='dest', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factor"
        "y=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)"
        "), self_param='self', std_params=('end', 'dest'), kw_only_params=(), frozen=True, slots=False, post_init_param"
        "s=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='end', kw_only=False, fn=None), Re"
        "prPlan.Field(name='dest', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='a2a61cc302e490f5e73b8b7d904d71bd2801660d',
    cls_names=(
        ('omxtra.text.pdcmark.scanning.links', 'LinkDestScan'),
    ),
)
def _process_dataclass__a2a61cc302e490f5e73b8b7d904d71bd2801660d():
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
                end=self.end,
                dest=self.dest,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.end == other.end and
                self.dest == other.dest
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'end',
            'dest',
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
                self.end,
                self.dest,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            end: __dataclass__init__fields__0__annotation,
            dest: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'end', end)
            __dataclass__object_setattr(self, 'dest', dest)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"end={self.end!r}")
            parts.append(f"dest={self.dest!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('end', 'raw')), EqPlan(fields=('end', 'raw')), FrozenPlan(fields=('end', 'raw'), a"
        "llow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('end', 'raw'), cache=False), InitPlan(fields="
        "(InitPlan.Field(name='end', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=N"
        "one, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), I"
        "nitPlan.Field(name='raw', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=Non"
        "e, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), se"
        "lf_param='self', std_params=('end', 'raw'), kw_only_params=(), frozen=True, slots=False, post_init_params=None"
        ", init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='end', kw_only=False, fn=None), ReprPlan"
        ".Field(name='raw', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='17199c38632cbd009956250091d9bfe463ca3da4',
    cls_names=(
        ('omxtra.text.pdcmark.scanning.links', 'LinkLabelScan'),
    ),
)
def _process_dataclass__17199c38632cbd009956250091d9bfe463ca3da4():
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
                end=self.end,
                raw=self.raw,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.end == other.end and
                self.raw == other.raw
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'end',
            'raw',
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
                self.end,
                self.raw,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            end: __dataclass__init__fields__0__annotation,
            raw: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'end', end)
            __dataclass__object_setattr(self, 'raw', raw)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"end={self.end!r}")
            parts.append(f"raw={self.raw!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('end', 'title')), EqPlan(fields=('end', 'title')), FrozenPlan(fields=('end', 'titl"
        "e'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('end', 'title'), cache=False), InitPlan"
        "(fields=(InitPlan.Field(name='end', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_f"
        "actory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type="
        "None), InitPlan.Field(name='title', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_f"
        "actory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type="
        "None)), self_param='self', std_params=('end', 'title'), kw_only_params=(), frozen=True, slots=False, post_init"
        "_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='end', kw_only=False, fn=Non"
        "e), ReprPlan.Field(name='title', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='962f4542253090c3196cbca4b164bd9053dea7b2',
    cls_names=(
        ('omxtra.text.pdcmark.scanning.links', 'LinkTitleScan'),
    ),
)
def _process_dataclass__962f4542253090c3196cbca4b164bd9053dea7b2():
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
                end=self.end,
                title=self.title,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.end == other.end and
                self.title == other.title
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'end',
            'title',
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
                self.end,
                self.title,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            end: __dataclass__init__fields__0__annotation,
            title: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'end', end)
            __dataclass__object_setattr(self, 'title', title)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"end={self.end!r}")
            parts.append(f"title={self.title!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('char', 'is_ordered', 'start', 'marker_width')), EqPlan(fields=('char', 'is_ordere"
        "d', 'start', 'marker_width')), FrozenPlan(fields=('char', 'is_ordered', 'start', 'marker_width'), allow_dynami"
        "c_dunder_attrs=False), HashPlan(action='add', fields=('char', 'is_ordered', 'start', 'marker_width'), cache=Fa"
        "lse), InitPlan(fields=(InitPlan.Field(name='char', annotation=OpRef(name='init.fields.0.annotation'), default="
        "None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=No"
        "ne, check_type=None), InitPlan.Field(name='is_ordered', annotation=OpRef(name='init.fields.1.annotation'), def"
        "ault=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, valida"
        "te=None, check_type=None), InitPlan.Field(name='start', annotation=OpRef(name='init.fields.2.annotation'), def"
        "ault=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, valida"
        "te=None, check_type=None), InitPlan.Field(name='marker_width', annotation=OpRef(name='init.fields.3.annotation"
        "'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None,"
        " validate=None, check_type=None)), self_param='self', std_params=('char', 'is_ordered', 'start', 'marker_width"
        "'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPla"
        "n(fields=(ReprPlan.Field(name='char', kw_only=False, fn=None), ReprPlan.Field(name='is_ordered', kw_only=False"
        ", fn=None), ReprPlan.Field(name='start', kw_only=False, fn=None), ReprPlan.Field(name='marker_width', kw_only="
        "False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='3fd5963a66c7184bede11ea27d5c9d1d4658803e',
    cls_names=(
        ('omxtra.text.pdcmark.scanning.lists', 'ListMarker'),
    ),
)
def _process_dataclass__3fd5963a66c7184bede11ea27d5c9d1d4658803e():
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
                char=self.char,
                is_ordered=self.is_ordered,
                start=self.start,
                marker_width=self.marker_width,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.char == other.char and
                self.is_ordered == other.is_ordered and
                self.start == other.start and
                self.marker_width == other.marker_width
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'char',
            'is_ordered',
            'start',
            'marker_width',
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
                self.char,
                self.is_ordered,
                self.start,
                self.marker_width,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            char: __dataclass__init__fields__0__annotation,
            is_ordered: __dataclass__init__fields__1__annotation,
            start: __dataclass__init__fields__2__annotation,
            marker_width: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'char', char)
            __dataclass__object_setattr(self, 'is_ordered', is_ordered)
            __dataclass__object_setattr(self, 'start', start)
            __dataclass__object_setattr(self, 'marker_width', marker_width)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"char={self.char!r}")
            parts.append(f"is_ordered={self.is_ordered!r}")
            parts.append(f"start={self.start!r}")
            parts.append(f"marker_width={self.marker_width!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('checked', 'end')), EqPlan(fields=('checked', 'end')), FrozenPlan(fields=('checked"
        "', 'end'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('checked', 'end'), cache=False), "
        "InitPlan(fields=(InitPlan.Field(name='checked', annotation=OpRef(name='init.fields.0.annotation'), default=Non"
        "e, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None,"
        " check_type=None), InitPlan.Field(name='end', annotation=OpRef(name='init.fields.1.annotation'), default=None,"
        " default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, c"
        "heck_type=None)), self_param='self', std_params=('checked', 'end'), kw_only_params=(), frozen=True, slots=Fals"
        "e, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='checked', kw_on"
        "ly=False, fn=None), ReprPlan.Field(name='end', kw_only=False, fn=None)), id=False, terse=False, default_fn=Non"
        "e)))"
    ),
    plan_repr_sha1='e58023484a4dc14f1cc3887c6dce3d0f87a47aa7',
    cls_names=(
        ('omxtra.text.pdcmark.scanning.lists', 'TaskListMark'),
    ),
)
def _process_dataclass__e58023484a4dc14f1cc3887c6dce3d0f87a47aa7():
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
                checked=self.checked,
                end=self.end,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.checked == other.checked and
                self.end == other.end
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'checked',
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
                self.checked,
                self.end,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            checked: __dataclass__init__fields__0__annotation,
            end: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'checked', checked)
            __dataclass__object_setattr(self, 'end', end)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"checked={self.checked!r}")
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
        "Plans(tup=(CopyPlan(fields=('committed', 'tentative')), EqPlan(fields=('committed', 'tentative')), FrozenPlan("
        "fields=('committed', 'tentative'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('committe"
        "d', 'tentative'), cache=False), InitPlan(fields=(InitPlan.Field(name='committed', annotation=OpRef(name='init."
        "fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INS"
        "TANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='tentative', annotation=OpRef(name='i"
        "nit.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType"
        ".INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=(), kw_only_params=('c"
        "ommitted', 'tentative'), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprP"
        "lan(fields=(ReprPlan.Field(name='committed', kw_only=True, fn=None), ReprPlan.Field(name='tentative', kw_only="
        "True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='f0577614750abccbeaf683610b1dad4ca7488caa',
    cls_names=(
        ('omxtra.text.pdcmark.streaming.output', 'FeedOutput'),
    ),
)
def _process_dataclass__f0577614750abccbeaf683610b1dad4ca7488caa():
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
                committed=self.committed,
                tentative=self.tentative,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.committed == other.committed and
                self.tentative == other.tentative
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'committed',
            'tentative',
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
                self.committed,
                self.tentative,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            committed: __dataclass__init__fields__0__annotation,
            tentative: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'committed', committed)
            __dataclass__object_setattr(self, 'tentative', tentative)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"committed={self.committed!r}")
            parts.append(f"tentative={self.tentative!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
