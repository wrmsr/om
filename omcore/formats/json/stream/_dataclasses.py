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
        "Plans(tup=(CopyPlan(fields=('yield_object_lists',)), EqPlan(fields=('yield_object_lists',)), FrozenPlan(fields"
        "=('yield_object_lists',), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('yield_object_list"
        "s',), cache=False), InitPlan(fields=(InitPlan.Field(name='yield_object_lists', annotation=OpRef(name='init.fie"
        "lds.0.annotation'), default=OpRef(name='init.fields.0.default'), default_factory=None, init=True, override=Fal"
        "se, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='self', std_para"
        "ms=(), kw_only_params=('yield_object_lists',), frozen=True, slots=False, post_init_params=None, init_fns=(), v"
        "alidate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='yield_object_lists', kw_only=True, fn=None),), id=False"
        ", terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='bd617922db09996f01733e694b25f95d8781a999',
    cls_names=(
        ('omcore.formats.json.stream.building', 'JsonValueBuilder.Config'),
    ),
)
def _process_dataclass__bd617922db09996f01733e694b25f95d8781a999():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('message', 'pos')), EqPlan(fields=('message', 'pos')), HashPlan(action='set_none',"
        " fields=None, cache=None), InitPlan(fields=(InitPlan.Field(name='message', annotation=OpRef(name='init.fields."
        "0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, "
        "coerce=None, validate=None, check_type=None), InitPlan.Field(name='pos', annotation=OpRef(name='init.fields.1."
        "annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, co"
        "erce=None, validate=None, check_type=None)), self_param='self', std_params=('message', 'pos'), kw_only_params="
        "(), frozen=False, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan"
        ".Field(name='message', kw_only=False, fn=None), ReprPlan.Field(name='pos', kw_only=False, fn=None)), id=False,"
        " terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='58f0ca2d364d5cdd303a12a7ca8b59a7dc77c92f',
    cls_names=(
        ('omcore.formats.json.stream.lexing', 'JsonStreamLexError'),
    ),
)
def _process_dataclass__58f0ca2d364d5cdd303a12a7ca8b59a7dc77c92f():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('include_raw', 'allow_extended_space', 'include_space', 'allow_comments', 'include"
        "_comments', 'allow_single_quotes', 'string_literal_parser', 'allow_extended_number_literals', 'number_literal_"
        "parser', 'allow_extended_idents')), EqPlan(fields=('include_raw', 'allow_extended_space', 'include_space', 'al"
        "low_comments', 'include_comments', 'allow_single_quotes', 'string_literal_parser', 'allow_extended_number_lite"
        "rals', 'number_literal_parser', 'allow_extended_idents')), FrozenPlan(fields=('include_raw', 'allow_extended_s"
        "pace', 'include_space', 'allow_comments', 'include_comments', 'allow_single_quotes', 'string_literal_parser', "
        "'allow_extended_number_literals', 'number_literal_parser', 'allow_extended_idents'), allow_dynamic_dunder_attr"
        "s=False), HashPlan(action='add', fields=('include_raw', 'allow_extended_space', 'include_space', 'allow_commen"
        "ts', 'include_comments', 'allow_single_quotes', 'string_literal_parser', 'allow_extended_number_literals', 'nu"
        "mber_literal_parser', 'allow_extended_idents'), cache=False), InitPlan(fields=(InitPlan.Field(name='include_ra"
        "w', annotation=OpRef(name='init.fields.00.annotation'), default=OpRef(name='init.fields.00.default'), default_"
        "factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type"
        "=None), InitPlan.Field(name='allow_extended_space', annotation=OpRef(name='init.fields.01.annotation'), defaul"
        "t=OpRef(name='init.fields.01.default'), default_factory=None, init=True, override=False, field_type=FieldType."
        "INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='include_space', annotation=OpRef("
        "name='init.fields.02.annotation'), default=OpRef(name='init.fields.02.default'), default_factory=None, init=Tr"
        "ue, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Fiel"
        "d(name='allow_comments', annotation=OpRef(name='init.fields.03.annotation'), default=OpRef(name='init.fields.0"
        "3.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, vali"
        "date=None, check_type=None), InitPlan.Field(name='include_comments', annotation=OpRef(name='init.fields.04.ann"
        "otation'), default=OpRef(name='init.fields.04.default'), default_factory=None, init=True, override=False, fiel"
        "d_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='allow_single_quo"
        "tes', annotation=OpRef(name='init.fields.05.annotation'), default=OpRef(name='init.fields.05.default'), defaul"
        "t_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_ty"
        "pe=None), InitPlan.Field(name='string_literal_parser', annotation=OpRef(name='init.fields.06.annotation'), def"
        "ault=OpRef(name='init.fields.06.default'), default_factory=None, init=True, override=False, field_type=FieldTy"
        "pe.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='allow_extended_number_literals"
        "', annotation=OpRef(name='init.fields.07.annotation'), default=OpRef(name='init.fields.07.default'), default_f"
        "actory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type="
        "None), InitPlan.Field(name='number_literal_parser', annotation=OpRef(name='init.fields.08.annotation'), defaul"
        "t=OpRef(name='init.fields.08.default'), default_factory=None, init=True, override=False, field_type=FieldType."
        "INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='allow_extended_idents', annotatio"
        "n=OpRef(name='init.fields.09.annotation'), default=OpRef(name='init.fields.09.default'), default_factory=None,"
        " init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self"
        "_param='self', std_params=(), kw_only_params=('include_raw', 'allow_extended_space', 'include_space', 'allow_c"
        "omments', 'include_comments', 'allow_single_quotes', 'string_literal_parser', 'allow_extended_number_literals'"
        ", 'number_literal_parser', 'allow_extended_idents'), frozen=True, slots=False, post_init_params=None, init_fns"
        "=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='include_raw', kw_only=True, fn=None), ReprPlan.Fi"
        "eld(name='allow_extended_space', kw_only=True, fn=None), ReprPlan.Field(name='include_space', kw_only=True, fn"
        "=None), ReprPlan.Field(name='allow_comments', kw_only=True, fn=None), ReprPlan.Field(name='include_comments', "
        "kw_only=True, fn=None), ReprPlan.Field(name='allow_single_quotes', kw_only=True, fn=None), ReprPlan.Field(name"
        "='string_literal_parser', kw_only=True, fn=None), ReprPlan.Field(name='allow_extended_number_literals', kw_onl"
        "y=True, fn=None), ReprPlan.Field(name='number_literal_parser', kw_only=True, fn=None), ReprPlan.Field(name='al"
        "low_extended_idents', kw_only=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='7b5211c0fdb0e00fa699a0aa58f797a0bbc74fe2',
    cls_names=(
        ('omcore.formats.json.stream.lexing', 'JsonStreamLexer.Config'),
    ),
)
def _process_dataclass__7b5211c0fdb0e00fa699a0aa58f797a0bbc74fe2():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('message', 'pos')), EqPlan(fields=('message', 'pos')), HashPlan(action='set_none',"
        " fields=None, cache=None), InitPlan(fields=(InitPlan.Field(name='message', annotation=OpRef(name='init.fields."
        "0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, "
        "coerce=None, validate=None, check_type=None), InitPlan.Field(name='pos', annotation=OpRef(name='init.fields.1."
        "annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False, fi"
        "eld_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('me"
        "ssage', 'pos'), kw_only_params=(), frozen=False, slots=False, post_init_params=None, init_fns=(), validate_fns"
        "=()), ReprPlan(fields=(ReprPlan.Field(name='message', kw_only=False, fn=None), ReprPlan.Field(name='pos', kw_o"
        "nly=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='abe5bc98b2c8c1cb3732168025c5f81d006598b6',
    cls_names=(
        ('omcore.formats.json.stream.parsing', 'JsonStreamParseError'),
    ),
)
def _process_dataclass__abe5bc98b2c8c1cb3732168025c5f81d006598b6():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__set_cls_attr,
    ):
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('allow_trailing_commas', 'allow_ident_values', 'allow_extended_idents')), EqPlan(f"
        "ields=('allow_trailing_commas', 'allow_ident_values', 'allow_extended_idents')), FrozenPlan(fields=('allow_tra"
        "iling_commas', 'allow_ident_values', 'allow_extended_idents'), allow_dynamic_dunder_attrs=False), HashPlan(act"
        "ion='add', fields=('allow_trailing_commas', 'allow_ident_values', 'allow_extended_idents'), cache=False), Init"
        "Plan(fields=(InitPlan.Field(name='allow_trailing_commas', annotation=OpRef(name='init.fields.0.annotation'), d"
        "efault=OpRef(name='init.fields.0.default'), default_factory=None, init=True, override=False, field_type=FieldT"
        "ype.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='allow_ident_values', annotati"
        "on=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, "
        "init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPl"
        "an.Field(name='allow_extended_idents', annotation=OpRef(name='init.fields.2.annotation'), default=OpRef(name='"
        "init.fields.2.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerc"
        "e=None, validate=None, check_type=None)), self_param='self', std_params=(), kw_only_params=('allow_trailing_co"
        "mmas', 'allow_ident_values', 'allow_extended_idents'), frozen=True, slots=False, post_init_params=None, init_f"
        "ns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='allow_trailing_commas', kw_only=True, fn=None),"
        " ReprPlan.Field(name='allow_ident_values', kw_only=True, fn=None), ReprPlan.Field(name='allow_extended_idents'"
        ", kw_only=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='f4439dd61ec1bfaa3ec60b12a392de695d66b565',
    cls_names=(
        ('omcore.formats.json.stream.parsing', 'JsonStreamParser.Config'),
    ),
)
def _process_dataclass__f4439dd61ec1bfaa3ec60b12a392de695d66b565():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__default,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('indent', 'separators', 'sort_keys', 'style', 'ensure_ascii', 'delimiter')), EqPla"
        "n(fields=('indent', 'separators', 'sort_keys', 'style', 'ensure_ascii', 'delimiter')), FrozenPlan(fields=('ind"
        "ent', 'separators', 'sort_keys', 'style', 'ensure_ascii', 'delimiter'), allow_dynamic_dunder_attrs=False), Has"
        "hPlan(action='add', fields=('indent', 'separators', 'sort_keys', 'style', 'ensure_ascii', 'delimiter'), cache="
        "False), InitPlan(fields=(InitPlan.Field(name='indent', annotation=OpRef(name='init.fields.0.annotation'), defa"
        "ult=OpRef(name='init.fields.0.default'), default_factory=None, init=True, override=False, field_type=FieldType"
        ".INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='separators', annotation=OpRef(na"
        "me='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, "
        "override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(na"
        "me='sort_keys', annotation=OpRef(name='init.fields.2.annotation'), default=OpRef(name='init.fields.2.default')"
        ", default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, "
        "check_type=None), InitPlan.Field(name='style', annotation=OpRef(name='init.fields.3.annotation'), default=OpRe"
        "f(name='init.fields.3.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANC"
        "E, coerce=None, validate=None, check_type=None), InitPlan.Field(name='ensure_ascii', annotation=OpRef(name='in"
        "it.fields.4.annotation'), default=OpRef(name='init.fields.4.default'), default_factory=None, init=True, overri"
        "de=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='de"
        "limiter', annotation=OpRef(name='init.fields.5.annotation'), default=OpRef(name='init.fields.5.default'), defa"
        "ult_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_"
        "type=None)), self_param='self', std_params=(), kw_only_params=('indent', 'separators', 'sort_keys', 'style', '"
        "ensure_ascii', 'delimiter'), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), R"
        "eprPlan(fields=(ReprPlan.Field(name='indent', kw_only=True, fn=None), ReprPlan.Field(name='separators', kw_onl"
        "y=True, fn=None), ReprPlan.Field(name='sort_keys', kw_only=True, fn=None), ReprPlan.Field(name='style', kw_onl"
        "y=True, fn=None), ReprPlan.Field(name='ensure_ascii', kw_only=True, fn=None), ReprPlan.Field(name='delimiter',"
        " kw_only=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='cc5cc7d5e0377a089813ddf7d419c8f2d2c4e0d5',
    cls_names=(
        ('omcore.formats.json.stream.rendering', 'StreamJsonRenderer.Config'),
    ),
)
def _process_dataclass__cc5cc7d5e0377a089813ddf7d419c8f2d2c4e0d5():
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
                indent=self.indent,
                separators=self.separators,
                sort_keys=self.sort_keys,
                style=self.style,
                ensure_ascii=self.ensure_ascii,
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
                self.style == other.style and
                self.ensure_ascii == other.ensure_ascii and
                self.delimiter == other.delimiter
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'indent',
            'separators',
            'sort_keys',
            'style',
            'ensure_ascii',
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
                self.style,
                self.ensure_ascii,
                self.delimiter,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            indent: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            separators: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            sort_keys: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            style: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            ensure_ascii: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            delimiter: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'indent', indent)
            __dataclass__object_setattr(self, 'separators', separators)
            __dataclass__object_setattr(self, 'sort_keys', sort_keys)
            __dataclass__object_setattr(self, 'style', style)
            __dataclass__object_setattr(self, 'ensure_ascii', ensure_ascii)
            __dataclass__object_setattr(self, 'delimiter', delimiter)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"indent={self.indent!r}")
            parts.append(f"separators={self.separators!r}")
            parts.append(f"sort_keys={self.sort_keys!r}")
            parts.append(f"style={self.style!r}")
            parts.append(f"ensure_ascii={self.ensure_ascii!r}")
            parts.append(f"delimiter={self.delimiter!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
