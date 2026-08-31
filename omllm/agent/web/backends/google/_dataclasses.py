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
        "Plans(tup=(CopyPlan(fields=('search_time', 'total_results', 'x')), EqPlan(fields=('search_time', 'total_result"
        "s', 'x')), FrozenPlan(fields=('search_time', 'total_results', 'x'), allow_dynamic_dunder_attrs=False), HashPla"
        "n(action='add', fields=('search_time', 'total_results', 'x'), cache=False), InitPlan(fields=(InitPlan.Field(na"
        "me='search_time', annotation=OpRef(name='init.fields.0.annotation'), default=OpRef(name='init.fields.0.default"
        "'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None"
        ", check_type=None), InitPlan.Field(name='total_results', annotation=OpRef(name='init.fields.1.annotation'), de"
        "fault=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False, field_type=FieldTy"
        "pe.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='x', annotation=OpRef(name='ini"
        "t.fields.2.annotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, overrid"
        "e=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_"
        "params=('search_time', 'total_results', 'x'), kw_only_params=(), frozen=True, slots=False, post_init_params=No"
        "ne, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='search_time', kw_only=False, fn=None)"
        ", ReprPlan.Field(name='total_results', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='9011cfb69ca0947e15e02520950d8710d0d53d0a',
    cls_names=(
        ('omllm.agent.web.backends.google.protocol', 'CseSearchInfo'),
    ),
)
def _process_dataclass__9011cfb69ca0947e15e02520950d8710d0d53d0a():
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
                search_time=self.search_time,
                total_results=self.total_results,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.search_time == other.search_time and
                self.total_results == other.total_results and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'search_time',
            'total_results',
            'x',
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
                self.search_time,
                self.total_results,
                self.x,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            search_time: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            total_results: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            x: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'search_time', search_time)
            __dataclass__object_setattr(self, 'total_results', total_results)
            __dataclass__object_setattr(self, 'x', x)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"search_time={self.search_time!r}")
            parts.append(f"total_results={self.total_results!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('kind', 'info', 'items', 'x')), EqPlan(fields=('kind', 'info', 'items', 'x')), Fro"
        "zenPlan(fields=('kind', 'info', 'items', 'x'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', field"
        "s=('kind', 'info', 'items', 'x'), cache=False), InitPlan(fields=(InitPlan.Field(name='kind', annotation=OpRef("
        "name='init.fields.0.annotation'), default=OpRef(name='init.fields.0.default'), default_factory=None, init=True"
        ", override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field("
        "name='info', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), d"
        "efault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, che"
        "ck_type=None), InitPlan.Field(name='items', annotation=OpRef(name='init.fields.2.annotation'), default=OpRef(n"
        "ame='init.fields.2.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, "
        "coerce=None, validate=None, check_type=None), InitPlan.Field(name='x', annotation=OpRef(name='init.fields.3.an"
        "notation'), default=OpRef(name='init.fields.3.default'), default_factory=None, init=True, override=False, fiel"
        "d_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('kind"
        "', 'info', 'items', 'x'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), val"
        "idate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='kind', kw_only=False, fn=None), ReprPlan.Field(name='info"
        "', kw_only=False, fn=None), ReprPlan.Field(name='items', kw_only=False, fn=None)), id=False, terse=False, defa"
        "ult_fn=None)))"
    ),
    plan_repr_sha1='6a5c9824784a2112a23d98269f609312c1509aad',
    cls_names=(
        ('omllm.agent.web.backends.google.protocol', 'CseSearchResponse'),
    ),
)
def _process_dataclass__6a5c9824784a2112a23d98269f609312c1509aad():
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
                info=self.info,
                items=self.items,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.kind == other.kind and
                self.info == other.info and
                self.items == other.items and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'kind',
            'info',
            'items',
            'x',
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
                self.info,
                self.items,
                self.x,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            kind: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            info: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            items: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            x: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'kind', kind)
            __dataclass__object_setattr(self, 'info', info)
            __dataclass__object_setattr(self, 'items', items)
            __dataclass__object_setattr(self, 'x', x)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"kind={self.kind!r}")
            parts.append(f"info={self.info!r}")
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
        "Plans(tup=(CopyPlan(fields=('kind', 'title', 'html_title', 'link', 'display_link', 'snippet', 'html_snippet', "
        "'cache_id', 'formatted_url', 'html_formatted_url', 'mime', 'file_format', 'x')), EqPlan(fields=('kind', 'title"
        "', 'html_title', 'link', 'display_link', 'snippet', 'html_snippet', 'cache_id', 'formatted_url', 'html_formatt"
        "ed_url', 'mime', 'file_format', 'x')), FrozenPlan(fields=('kind', 'title', 'html_title', 'link', 'display_link"
        "', 'snippet', 'html_snippet', 'cache_id', 'formatted_url', 'html_formatted_url', 'mime', 'file_format', 'x'), "
        "allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('kind', 'title', 'html_title', 'link', 'disp"
        "lay_link', 'snippet', 'html_snippet', 'cache_id', 'formatted_url', 'html_formatted_url', 'mime', 'file_format'"
        ", 'x'), cache=False), InitPlan(fields=(InitPlan.Field(name='kind', annotation=OpRef(name='init.fields.00.annot"
        "ation'), default=OpRef(name='init.fields.00.default'), default_factory=None, init=True, override=False, field_"
        "type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='title', annotation"
        "=OpRef(name='init.fields.01.annotation'), default=OpRef(name='init.fields.01.default'), default_factory=None, "
        "init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPl"
        "an.Field(name='html_title', annotation=OpRef(name='init.fields.02.annotation'), default=OpRef(name='init.field"
        "s.02.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, v"
        "alidate=None, check_type=None), InitPlan.Field(name='link', annotation=OpRef(name='init.fields.03.annotation')"
        ", default=OpRef(name='init.fields.03.default'), default_factory=None, init=True, override=False, field_type=Fi"
        "eldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='display_link', annotation"
        "=OpRef(name='init.fields.04.annotation'), default=OpRef(name='init.fields.04.default'), default_factory=None, "
        "init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPl"
        "an.Field(name='snippet', annotation=OpRef(name='init.fields.05.annotation'), default=OpRef(name='init.fields.0"
        "5.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, vali"
        "date=None, check_type=None), InitPlan.Field(name='html_snippet', annotation=OpRef(name='init.fields.06.annotat"
        "ion'), default=OpRef(name='init.fields.06.default'), default_factory=None, init=True, override=False, field_ty"
        "pe=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='cache_id', annotatio"
        "n=OpRef(name='init.fields.07.annotation'), default=OpRef(name='init.fields.07.default'), default_factory=None,"
        " init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitP"
        "lan.Field(name='formatted_url', annotation=OpRef(name='init.fields.08.annotation'), default=OpRef(name='init.f"
        "ields.08.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=Non"
        "e, validate=None, check_type=None), InitPlan.Field(name='html_formatted_url', annotation=OpRef(name='init.fiel"
        "ds.09.annotation'), default=OpRef(name='init.fields.09.default'), default_factory=None, init=True, override=Fa"
        "lse, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='mime', "
        "annotation=OpRef(name='init.fields.10.annotation'), default=OpRef(name='init.fields.10.default'), default_fact"
        "ory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=Non"
        "e), InitPlan.Field(name='file_format', annotation=OpRef(name='init.fields.11.annotation'), default=OpRef(name="
        "'init.fields.11.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coe"
        "rce=None, validate=None, check_type=None), InitPlan.Field(name='x', annotation=OpRef(name='init.fields.12.anno"
        "tation'), default=OpRef(name='init.fields.12.default'), default_factory=None, init=True, override=False, field"
        "_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('kind'"
        ", 'title', 'html_title', 'link', 'display_link', 'snippet', 'html_snippet', 'cache_id', 'formatted_url', 'html"
        "_formatted_url', 'mime', 'file_format', 'x'), kw_only_params=(), frozen=True, slots=False, post_init_params=No"
        "ne, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='kind', kw_only=False, fn=None), ReprP"
        "lan.Field(name='title', kw_only=False, fn=None), ReprPlan.Field(name='html_title', kw_only=False, fn=None), Re"
        "prPlan.Field(name='link', kw_only=False, fn=None), ReprPlan.Field(name='display_link', kw_only=False, fn=None)"
        ", ReprPlan.Field(name='snippet', kw_only=False, fn=None), ReprPlan.Field(name='html_snippet', kw_only=False, f"
        "n=None), ReprPlan.Field(name='cache_id', kw_only=False, fn=None), ReprPlan.Field(name='formatted_url', kw_only"
        "=False, fn=None), ReprPlan.Field(name='html_formatted_url', kw_only=False, fn=None), ReprPlan.Field(name='mime"
        "', kw_only=False, fn=None), ReprPlan.Field(name='file_format', kw_only=False, fn=None)), id=False, terse=False"
        ", default_fn=None)))"
    ),
    plan_repr_sha1='4fe5bb897a686ca1487bb8d85e655d4100c4a8f2',
    cls_names=(
        ('omllm.agent.web.backends.google.protocol', 'CseSearchResult'),
    ),
)
def _process_dataclass__4fe5bb897a686ca1487bb8d85e655d4100c4a8f2():
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
        __dataclass__init__fields__10__annotation,
        __dataclass__init__fields__10__default,
        __dataclass__init__fields__11__annotation,
        __dataclass__init__fields__11__default,
        __dataclass__init__fields__12__annotation,
        __dataclass__init__fields__12__default,
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
                title=self.title,
                html_title=self.html_title,
                link=self.link,
                display_link=self.display_link,
                snippet=self.snippet,
                html_snippet=self.html_snippet,
                cache_id=self.cache_id,
                formatted_url=self.formatted_url,
                html_formatted_url=self.html_formatted_url,
                mime=self.mime,
                file_format=self.file_format,
                x=self.x,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.kind == other.kind and
                self.title == other.title and
                self.html_title == other.html_title and
                self.link == other.link and
                self.display_link == other.display_link and
                self.snippet == other.snippet and
                self.html_snippet == other.html_snippet and
                self.cache_id == other.cache_id and
                self.formatted_url == other.formatted_url and
                self.html_formatted_url == other.html_formatted_url and
                self.mime == other.mime and
                self.file_format == other.file_format and
                self.x == other.x
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'kind',
            'title',
            'html_title',
            'link',
            'display_link',
            'snippet',
            'html_snippet',
            'cache_id',
            'formatted_url',
            'html_formatted_url',
            'mime',
            'file_format',
            'x',
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
                self.title,
                self.html_title,
                self.link,
                self.display_link,
                self.snippet,
                self.html_snippet,
                self.cache_id,
                self.formatted_url,
                self.html_formatted_url,
                self.mime,
                self.file_format,
                self.x,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            kind: __dataclass__init__fields__00__annotation = __dataclass__init__fields__00__default,
            title: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            html_title: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            link: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            display_link: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            snippet: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            html_snippet: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            cache_id: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            formatted_url: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            html_formatted_url: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            mime: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            file_format: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            x: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'kind', kind)
            __dataclass__object_setattr(self, 'title', title)
            __dataclass__object_setattr(self, 'html_title', html_title)
            __dataclass__object_setattr(self, 'link', link)
            __dataclass__object_setattr(self, 'display_link', display_link)
            __dataclass__object_setattr(self, 'snippet', snippet)
            __dataclass__object_setattr(self, 'html_snippet', html_snippet)
            __dataclass__object_setattr(self, 'cache_id', cache_id)
            __dataclass__object_setattr(self, 'formatted_url', formatted_url)
            __dataclass__object_setattr(self, 'html_formatted_url', html_formatted_url)
            __dataclass__object_setattr(self, 'mime', mime)
            __dataclass__object_setattr(self, 'file_format', file_format)
            __dataclass__object_setattr(self, 'x', x)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"kind={self.kind!r}")
            parts.append(f"title={self.title!r}")
            parts.append(f"html_title={self.html_title!r}")
            parts.append(f"link={self.link!r}")
            parts.append(f"display_link={self.display_link!r}")
            parts.append(f"snippet={self.snippet!r}")
            parts.append(f"html_snippet={self.html_snippet!r}")
            parts.append(f"cache_id={self.cache_id!r}")
            parts.append(f"formatted_url={self.formatted_url!r}")
            parts.append(f"html_formatted_url={self.html_formatted_url!r}")
            parts.append(f"mime={self.mime!r}")
            parts.append(f"file_format={self.file_format!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
