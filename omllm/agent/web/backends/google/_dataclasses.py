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
    installer_sha1='f15ddbee6740e149707357af65cc994f29a19fd4',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('search_time', True, True, None, True, False, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('total_results', True, True, None, True, False, False, None), 'instance'"
            ", 'value', None, False, False, False), (('x', True, False, None, True, False, False, None), 'instance', 'v"
            "alue', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), "
            "((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.web.backends.google.protocol', 'CseSearchInfo'),
    ),
)
def _process_dataclass__f15ddbee6740e149707357af65cc994f29a19fd4():
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
    installer_sha1='2841dc085cc800371c986c46f75aa07913ac3c17',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('kind', True, True, None, True, False, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('info', True, True, None, True, False, False, None), 'instance', 'value', None,"
            " False, False, False), (('items', True, True, None, True, False, False, None), 'instance', 'value', None, "
            "False, False, False), (('x', True, False, None, True, False, False, None), 'instance', 'value', None, Fals"
            "e, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False"
            ",)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.web.backends.google.protocol', 'CseSearchResponse'),
    ),
)
def _process_dataclass__2841dc085cc800371c986c46f75aa07913ac3c17():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
    installer_sha1='efe0845d63bfc65db3ba89dc30e8257b1770d984',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('kind', True, True, None, True, False, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('title', True, True, None, True, False, False, None), 'instance', 'value', None"
            ", False, False, False), (('html_title', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('link', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('display_link', True, True, None, True, False, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('snippet', True, True, None, True, False, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('html_snippet', True, True, None, True, False, False, None), 'instance'"
            ", 'value', None, False, False, False), (('cache_id', True, True, None, True, False, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('formatted_url', True, True, None, True, False, False, None), '"
            "instance', 'value', None, False, False, False), (('html_formatted_url', True, True, None, True, False, Fal"
            "se, None), 'instance', 'value', None, False, False, False), (('mime', True, True, None, True, False, False"
            ", None), 'instance', 'value', None, False, False, False), (('file_format', True, True, None, True, False, "
            "False, None), 'instance', 'value', None, False, False, False), (('x', True, False, None, True, False, Fals"
            "e, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False"
            ",), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.web.backends.google.protocol', 'CseSearchResult'),
    ),
)
def _process_dataclass__efe0845d63bfc65db3ba89dc30e8257b1770d984():
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
        __dataclass__init__fields__10__annotation = __dataclass__spec.fields[10].annotation
        __dataclass__init__fields__10__default = __dataclass__spec.fields[10].default.must()
        __dataclass__init__fields__11__annotation = __dataclass__spec.fields[11].annotation
        __dataclass__init__fields__11__default = __dataclass__spec.fields[11].default.must()
        __dataclass__init__fields__12__annotation = __dataclass__spec.fields[12].annotation
        __dataclass__init__fields__12__default = __dataclass__spec.fields[12].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

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
