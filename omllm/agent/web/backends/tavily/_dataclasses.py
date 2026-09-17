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


IMPLEMENTATION_KEY = '0b058e19e67cdb26e91b1c38203523e9cefe1242a3d73dbb76cc5c75c41df941'


@_register(
    installer_sha1='57fdf55511d0a4d05a75b45c854ff8c72a1a226d',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('urls', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('include_images', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('include_favicon', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('extract_depth', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('format', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('timeout', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()),"
            " (), (), False))"
        ),
    ),
    cls_names=(
        ('omllm.agent.web.backends.tavily.protocol', 'ExtractRequest'),
    ),
)
def _process_dataclass__57fdf55511d0a4d05a75b45c854ff8c72a1a226d():
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
                urls=self.urls,
                include_images=self.include_images,
                include_favicon=self.include_favicon,
                extract_depth=self.extract_depth,
                format=self.format,
                timeout=self.timeout,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.urls == other.urls and
                self.include_images == other.include_images and
                self.include_favicon == other.include_favicon and
                self.extract_depth == other.extract_depth and
                self.format == other.format and
                self.timeout == other.timeout
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'urls',
            'include_images',
            'include_favicon',
            'extract_depth',
            'format',
            'timeout',
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
                self.urls,
                self.include_images,
                self.include_favicon,
                self.extract_depth,
                self.format,
                self.timeout,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            urls: __dataclass__init__fields__0__annotation,
            include_images: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            include_favicon: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            extract_depth: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            format: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            timeout: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'urls', urls)
            __dataclass__object_setattr(self, 'include_images', include_images)
            __dataclass__object_setattr(self, 'include_favicon', include_favicon)
            __dataclass__object_setattr(self, 'extract_depth', extract_depth)
            __dataclass__object_setattr(self, 'format', format)
            __dataclass__object_setattr(self, 'timeout', timeout)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"urls={self.urls!r}")
            parts.append(f"include_images={self.include_images!r}")
            parts.append(f"include_favicon={self.include_favicon!r}")
            parts.append(f"extract_depth={self.extract_depth!r}")
            parts.append(f"format={self.format!r}")
            parts.append(f"timeout={self.timeout!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='bcffe3a22a695885ca94862f3034537014e849bd',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('results', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False), (('failed_results', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('response_time', True, True, None, True, True, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('request_id', True, True, None, True, True, False, None), 'inst"
            "ance', 'value', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), "
            "(), (), False))"
        ),
    ),
    cls_names=(
        ('omllm.agent.web.backends.tavily.protocol', 'ExtractResponse'),
    ),
)
def _process_dataclass__bcffe3a22a695885ca94862f3034537014e849bd():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                results=self.results,
                failed_results=self.failed_results,
                response_time=self.response_time,
                request_id=self.request_id,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.results == other.results and
                self.failed_results == other.failed_results and
                self.response_time == other.response_time and
                self.request_id == other.request_id
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'results',
            'failed_results',
            'response_time',
            'request_id',
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
                self.results,
                self.failed_results,
                self.response_time,
                self.request_id,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            results: __dataclass__init__fields__0__annotation,
            failed_results: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            response_time: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            request_id: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'results', results)
            __dataclass__object_setattr(self, 'failed_results', failed_results)
            __dataclass__object_setattr(self, 'response_time', response_time)
            __dataclass__object_setattr(self, 'request_id', request_id)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"results={self.results!r}")
            parts.append(f"failed_results={self.failed_results!r}")
            parts.append(f"response_time={self.response_time!r}")
            parts.append(f"request_id={self.request_id!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='1e0f12390b4aa9ccf758997afba7f98ffaaa868e',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('url', True, True, None, True, True, False, None), 'instance', 'missing', None"
            ", False, False, False), (('error', True, True, None, True, True, False, None), 'instance', 'missing', None"
            ", False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('omllm.agent.web.backends.tavily.protocol', 'ExtractResponse.FailedResult'),
    ),
)
def _process_dataclass__1e0f12390b4aa9ccf758997afba7f98ffaaa868e():
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
                url=self.url,
                error=self.error,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.url == other.url and
                self.error == other.error
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'url',
            'error',
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
                self.url,
                self.error,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            url: __dataclass__init__fields__0__annotation,
            error: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'url', url)
            __dataclass__object_setattr(self, 'error', error)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"url={self.url!r}")
            parts.append(f"error={self.error!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b2df5aa1e40193abd073daf92282c42fad2284a7',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('url', True, True, None, True, True, False, None), 'instance', 'missing', None"
            ", False, False, False), (('raw_content', True, True, None, True, True, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('images', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('favicon', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('omllm.agent.web.backends.tavily.protocol', 'ExtractResponse.Result'),
    ),
)
def _process_dataclass__b2df5aa1e40193abd073daf92282c42fad2284a7():
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
                url=self.url,
                raw_content=self.raw_content,
                images=self.images,
                favicon=self.favicon,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.url == other.url and
                self.raw_content == other.raw_content and
                self.images == other.images and
                self.favicon == other.favicon
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'url',
            'raw_content',
            'images',
            'favicon',
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
                self.url,
                self.raw_content,
                self.images,
                self.favicon,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            url: __dataclass__init__fields__0__annotation,
            raw_content: __dataclass__init__fields__1__annotation,
            images: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            favicon: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'url', url)
            __dataclass__object_setattr(self, 'raw_content', raw_content)
            __dataclass__object_setattr(self, 'images', images)
            __dataclass__object_setattr(self, 'favicon', favicon)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"url={self.url!r}")
            parts.append(f"raw_content={self.raw_content!r}")
            parts.append(f"images={self.images!r}")
            parts.append(f"favicon={self.favicon!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='da4aecbe5b0cb9e20473bd58098cc3dca378fa2a',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('query', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('auto_parameters', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('topic', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('search_depth', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False), (('chunks_per_source', True, True, None, True, True, False, None), 'i"
            "nstance', 'value', None, False, False, False), (('max_results', True, True, None, True, True, False, None)"
            ", 'instance', 'value', None, False, False, False), (('time_range', True, True, None, True, True, False, No"
            "ne), 'instance', 'value', None, False, False, False), (('start_date', True, True, None, True, True, False,"
            " None), 'instance', 'value', None, False, False, False), (('end_date', True, True, None, True, True, False"
            ", None), 'instance', 'value', None, False, False, False), (('include_answer', True, True, None, True, True"
            ", False, None), 'instance', 'value', None, False, False, False), (('include_raw_content', True, True, None"
            ", True, True, False, None), 'instance', 'value', None, False, False, False), (('include_images', True, Tru"
            "e, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('include_image_descr"
            "iptions', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('"
            "include_favicon', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, Fal"
            "se), (('include_domains', True, True, None, True, True, False, None), 'instance', 'value', None, False, Fa"
            "lse, False), (('exclude_domains', True, True, None, True, True, False, None), 'instance', 'value', None, F"
            "alse, False, False), (('country', True, True, None, True, True, False, None), 'instance', 'value', None, F"
            "alse, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('omllm.agent.web.backends.tavily.protocol', 'SearchRequest'),
    ),
)
def _process_dataclass__da4aecbe5b0cb9e20473bd58098cc3dca378fa2a():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
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
        __dataclass__init__fields__13__annotation = __dataclass__spec.fields[13].annotation
        __dataclass__init__fields__13__default = __dataclass__spec.fields[13].default.must()
        __dataclass__init__fields__14__annotation = __dataclass__spec.fields[14].annotation
        __dataclass__init__fields__14__default = __dataclass__spec.fields[14].default.must()
        __dataclass__init__fields__15__annotation = __dataclass__spec.fields[15].annotation
        __dataclass__init__fields__15__default = __dataclass__spec.fields[15].default.must()
        __dataclass__init__fields__16__annotation = __dataclass__spec.fields[16].annotation
        __dataclass__init__fields__16__default = __dataclass__spec.fields[16].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                query=self.query,
                auto_parameters=self.auto_parameters,
                topic=self.topic,
                search_depth=self.search_depth,
                chunks_per_source=self.chunks_per_source,
                max_results=self.max_results,
                time_range=self.time_range,
                start_date=self.start_date,
                end_date=self.end_date,
                include_answer=self.include_answer,
                include_raw_content=self.include_raw_content,
                include_images=self.include_images,
                include_image_descriptions=self.include_image_descriptions,
                include_favicon=self.include_favicon,
                include_domains=self.include_domains,
                exclude_domains=self.exclude_domains,
                country=self.country,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.query == other.query and
                self.auto_parameters == other.auto_parameters and
                self.topic == other.topic and
                self.search_depth == other.search_depth and
                self.chunks_per_source == other.chunks_per_source and
                self.max_results == other.max_results and
                self.time_range == other.time_range and
                self.start_date == other.start_date and
                self.end_date == other.end_date and
                self.include_answer == other.include_answer and
                self.include_raw_content == other.include_raw_content and
                self.include_images == other.include_images and
                self.include_image_descriptions == other.include_image_descriptions and
                self.include_favicon == other.include_favicon and
                self.include_domains == other.include_domains and
                self.exclude_domains == other.exclude_domains and
                self.country == other.country
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'query',
            'auto_parameters',
            'topic',
            'search_depth',
            'chunks_per_source',
            'max_results',
            'time_range',
            'start_date',
            'end_date',
            'include_answer',
            'include_raw_content',
            'include_images',
            'include_image_descriptions',
            'include_favicon',
            'include_domains',
            'exclude_domains',
            'country',
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
                self.query,
                self.auto_parameters,
                self.topic,
                self.search_depth,
                self.chunks_per_source,
                self.max_results,
                self.time_range,
                self.start_date,
                self.end_date,
                self.include_answer,
                self.include_raw_content,
                self.include_images,
                self.include_image_descriptions,
                self.include_favicon,
                self.include_domains,
                self.exclude_domains,
                self.country,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            query: __dataclass__init__fields__00__annotation,
            auto_parameters: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            topic: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            search_depth: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            chunks_per_source: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            max_results: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            time_range: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            start_date: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            end_date: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            include_answer: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            include_raw_content: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            include_images: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            include_image_descriptions: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            include_favicon: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            include_domains: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            exclude_domains: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            country: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'query', query)
            __dataclass__object_setattr(self, 'auto_parameters', auto_parameters)
            __dataclass__object_setattr(self, 'topic', topic)
            __dataclass__object_setattr(self, 'search_depth', search_depth)
            __dataclass__object_setattr(self, 'chunks_per_source', chunks_per_source)
            __dataclass__object_setattr(self, 'max_results', max_results)
            __dataclass__object_setattr(self, 'time_range', time_range)
            __dataclass__object_setattr(self, 'start_date', start_date)
            __dataclass__object_setattr(self, 'end_date', end_date)
            __dataclass__object_setattr(self, 'include_answer', include_answer)
            __dataclass__object_setattr(self, 'include_raw_content', include_raw_content)
            __dataclass__object_setattr(self, 'include_images', include_images)
            __dataclass__object_setattr(self, 'include_image_descriptions', include_image_descriptions)
            __dataclass__object_setattr(self, 'include_favicon', include_favicon)
            __dataclass__object_setattr(self, 'include_domains', include_domains)
            __dataclass__object_setattr(self, 'exclude_domains', exclude_domains)
            __dataclass__object_setattr(self, 'country', country)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"query={self.query!r}")
            parts.append(f"auto_parameters={self.auto_parameters!r}")
            parts.append(f"topic={self.topic!r}")
            parts.append(f"search_depth={self.search_depth!r}")
            parts.append(f"chunks_per_source={self.chunks_per_source!r}")
            parts.append(f"max_results={self.max_results!r}")
            parts.append(f"time_range={self.time_range!r}")
            parts.append(f"start_date={self.start_date!r}")
            parts.append(f"end_date={self.end_date!r}")
            parts.append(f"include_answer={self.include_answer!r}")
            parts.append(f"include_raw_content={self.include_raw_content!r}")
            parts.append(f"include_images={self.include_images!r}")
            parts.append(f"include_image_descriptions={self.include_image_descriptions!r}")
            parts.append(f"include_favicon={self.include_favicon!r}")
            parts.append(f"include_domains={self.include_domains!r}")
            parts.append(f"exclude_domains={self.exclude_domains!r}")
            parts.append(f"country={self.country!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='40c14063f6cc9cdc616785555d5915abee3ecc49',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('query', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('answer', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('images', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('results', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('follow_up_questions', True, True, None, True, True, False, None), 'instance',"
            " 'value', None, False, False, False), (('auto_parameters', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('response_time', True, True, None, True, True, False, None"
            "), 'instance', 'value', None, False, False, False), (('request_id', True, True, None, True, True, False, N"
            "one), 'instance', 'value', None, False, False, False)), False, 0, ()), (False, False, (), False, (False, F"
            "alse, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('omllm.agent.web.backends.tavily.protocol', 'SearchResponse'),
    ),
)
def _process_dataclass__40c14063f6cc9cdc616785555d5915abee3ecc49():
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
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__default = __dataclass__spec.fields[5].default.must()
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__6__default = __dataclass__spec.fields[6].default.must()
        __dataclass__init__fields__7__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__7__default = __dataclass__spec.fields[7].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                query=self.query,
                answer=self.answer,
                images=self.images,
                results=self.results,
                follow_up_questions=self.follow_up_questions,
                auto_parameters=self.auto_parameters,
                response_time=self.response_time,
                request_id=self.request_id,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.query == other.query and
                self.answer == other.answer and
                self.images == other.images and
                self.results == other.results and
                self.follow_up_questions == other.follow_up_questions and
                self.auto_parameters == other.auto_parameters and
                self.response_time == other.response_time and
                self.request_id == other.request_id
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'query',
            'answer',
            'images',
            'results',
            'follow_up_questions',
            'auto_parameters',
            'response_time',
            'request_id',
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
                self.query,
                self.answer,
                self.images,
                self.results,
                self.follow_up_questions,
                self.auto_parameters,
                self.response_time,
                self.request_id,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            query: __dataclass__init__fields__0__annotation,
            answer: __dataclass__init__fields__1__annotation,
            images: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            results: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            follow_up_questions: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            auto_parameters: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            response_time: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
            request_id: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'query', query)
            __dataclass__object_setattr(self, 'answer', answer)
            __dataclass__object_setattr(self, 'images', images)
            __dataclass__object_setattr(self, 'results', results)
            __dataclass__object_setattr(self, 'follow_up_questions', follow_up_questions)
            __dataclass__object_setattr(self, 'auto_parameters', auto_parameters)
            __dataclass__object_setattr(self, 'response_time', response_time)
            __dataclass__object_setattr(self, 'request_id', request_id)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"query={self.query!r}")
            parts.append(f"answer={self.answer!r}")
            parts.append(f"images={self.images!r}")
            parts.append(f"results={self.results!r}")
            parts.append(f"follow_up_questions={self.follow_up_questions!r}")
            parts.append(f"auto_parameters={self.auto_parameters!r}")
            parts.append(f"response_time={self.response_time!r}")
            parts.append(f"request_id={self.request_id!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='3b28fa6cb56a318cb386ac5254de804bba5cde8f',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('url', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False), (('description', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('omllm.agent.web.backends.tavily.protocol', 'SearchResponse.Image'),
    ),
)
def _process_dataclass__3b28fa6cb56a318cb386ac5254de804bba5cde8f():
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
                url=self.url,
                description=self.description,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.url == other.url and
                self.description == other.description
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'url',
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
                self.url,
                self.description,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            url: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            description: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'url', url)
            __dataclass__object_setattr(self, 'description', description)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"url={self.url!r}")
            parts.append(f"description={self.description!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='ba0f77ef42d19dc10806160d74f48862b9feee11',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('title', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('url', True, True, None, True, True, False, None), 'instance', 'value', None, Fa"
            "lse, False, False), (('content', True, True, None, True, True, False, None), 'instance', 'value', None, Fa"
            "lse, False, False), (('score', True, True, None, True, True, False, None), 'instance', 'value', None, Fals"
            "e, False, False), (('raw_content', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False), (('favicon', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False)), False, 0, ()), (False, False, (), False, (False, False, ()), (), (), False))"
        ),
    ),
    cls_names=(
        ('omllm.agent.web.backends.tavily.protocol', 'SearchResponse.Result'),
    ),
)
def _process_dataclass__ba0f77ef42d19dc10806160d74f48862b9feee11():
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
                title=self.title,
                url=self.url,
                content=self.content,
                score=self.score,
                raw_content=self.raw_content,
                favicon=self.favicon,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.title == other.title and
                self.url == other.url and
                self.content == other.content and
                self.score == other.score and
                self.raw_content == other.raw_content and
                self.favicon == other.favicon
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'title',
            'url',
            'content',
            'score',
            'raw_content',
            'favicon',
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
                self.title,
                self.url,
                self.content,
                self.score,
                self.raw_content,
                self.favicon,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            title: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            url: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            content: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            score: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            raw_content: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            favicon: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'title', title)
            __dataclass__object_setattr(self, 'url', url)
            __dataclass__object_setattr(self, 'content', content)
            __dataclass__object_setattr(self, 'score', score)
            __dataclass__object_setattr(self, 'raw_content', raw_content)
            __dataclass__object_setattr(self, 'favicon', favicon)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"title={self.title!r}")
            parts.append(f"url={self.url!r}")
            parts.append(f"content={self.content!r}")
            parts.append(f"score={self.score!r}")
            parts.append(f"raw_content={self.raw_content!r}")
            parts.append(f"favicon={self.favicon!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
