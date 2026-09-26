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
    installer_sha1='2e1c2a1971838e517f50429f8008a6ae0984233a',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('http_status', True, True, None, True, True, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('code', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('error_type', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('provider_status', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('message', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, "
            "()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.backends.base.http', 'HttpErrorDetails'),
    ),
)
def _process_dataclass__2e1c2a1971838e517f50429f8008a6ae0984233a():
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
                http_status=self.http_status,
                code=self.code,
                error_type=self.error_type,
                provider_status=self.provider_status,
                message=self.message,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.http_status == other.http_status and
                self.code == other.code and
                self.error_type == other.error_type and
                self.provider_status == other.provider_status and
                self.message == other.message
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'http_status',
            'code',
            'error_type',
            'provider_status',
            'message',
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
                self.http_status,
                self.code,
                self.error_type,
                self.provider_status,
                self.message,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            http_status: __dataclass__init__fields__0__annotation,
            code: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            error_type: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            provider_status: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            message: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'http_status', http_status)
            __dataclass__object_setattr(self, 'code', code)
            __dataclass__object_setattr(self, 'error_type', error_type)
            __dataclass__object_setattr(self, 'provider_status', provider_status)
            __dataclass__object_setattr(self, 'message', message)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"http_status={self.http_status!r}")
            parts.append(f"code={self.code!r}")
            parts.append(f"error_type={self.error_type!r}")
            parts.append(f"provider_status={self.provider_status!r}")
            parts.append(f"message={self.message!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b437895e997b1cc68c4e36257f02a65e2a894180',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), (), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), (), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.compat', 'Compat'),
        ('omllm.llm.types.content', 'Content'),
        ('omllm.llm.types.messages', 'Message'),
        ('omllm.llm.types.streams', 'AiStreamEvent'),
        ('omllm.llm.types.streams', 'StreamEndAiStreamEvent'),
        ('omllm.llm.types.streams', 'StreamStartAiStreamEvent'),
        ('omllm.llm.types.tools', 'ToolDtype'),
    ),
)
def _process_dataclass__b437895e997b1cc68c4e36257f02a65e2a894180():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
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
    installer_sha1='33241d34d9ddd182ea9506ee6472d2ba82cf8f86',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('url_path', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('max_tokens_field', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False), (('reasoning_field', True, True, None, True, True, False, None), 'inst"
            "ance', 'value', None, False, False, False), (('cost_mode', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, Fa"
            "lse, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.compat', 'OpenaiCompletionsCompat'),
    ),
)
def _process_dataclass__33241d34d9ddd182ea9506ee6472d2ba82cf8f86():
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
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                url_path=self.url_path,
                max_tokens_field=self.max_tokens_field,
                reasoning_field=self.reasoning_field,
                cost_mode=self.cost_mode,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.url_path == other.url_path and
                self.max_tokens_field == other.max_tokens_field and
                self.reasoning_field == other.reasoning_field and
                self.cost_mode == other.cost_mode
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'url_path',
            'max_tokens_field',
            'reasoning_field',
            'cost_mode',
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
                self.url_path,
                self.max_tokens_field,
                self.reasoning_field,
                self.cost_mode,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            url_path: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            max_tokens_field: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            reasoning_field: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            cost_mode: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'url_path', url_path)
            __dataclass__object_setattr(self, 'max_tokens_field', max_tokens_field)
            __dataclass__object_setattr(self, 'reasoning_field', reasoning_field)
            __dataclass__object_setattr(self, 'cost_mode', cost_mode)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.url_path)) is not None:
                parts.append(f"url_path={s}")
            if (s := __dataclass__repr__default_fn(self.max_tokens_field)) is not None:
                parts.append(f"max_tokens_field={s}")
            if (s := __dataclass__repr__default_fn(self.reasoning_field)) is not None:
                parts.append(f"reasoning_field={s}")
            if (s := __dataclass__repr__default_fn(self.cost_mode)) is not None:
                parts.append(f"cost_mode={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='a53546a1deda1ce830b93ec5ca07872d50b30922',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('url_path', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False),), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.compat', 'OpenaiResponsesCompat'),
    ),
)
def _process_dataclass__a53546a1deda1ce830b93ec5ca07872d50b30922():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default = __dataclass__spec.fields[0].default.must()
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                url_path=self.url_path,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.url_path == other.url_path
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'url_path',
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
                self.url_path,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            url_path: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'url_path', url_path)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.url_path)) is not None:
                parts.append(f"url_path={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='03b63c0f0f1f90450786b6bbe562b78d382fd8e6',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, True, False, False, False, Fals"
            "e, False, True, False), ((('text', True, True, None, True, False, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('backend_signature', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ("
            "(),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.content', 'TextContent'),
    ),
)
def _process_dataclass__03b63c0f0f1f90450786b6bbe562b78d382fd8e6():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                text=self.text,
                backend_signature=self.backend_signature,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.text == other.text and
                self.backend_signature == other.backend_signature
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'text',
            'backend_signature',
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
            try:
                return self.__dataclass_hash__
            except AttributeError:
                pass
            object.__setattr__(
                self,
                '__dataclass_hash__',
                h := hash((
                    self.text,
                    self.backend_signature,
                ))
            )
            return h

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            text: __dataclass__init__fields__0__annotation,
            *,
            backend_signature: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'text', text)
            __dataclass__object_setattr(self, 'backend_signature', backend_signature)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.text)) is not None:
                parts.append(f"{s}")
            if (s := __dataclass__repr__default_fn(self.backend_signature)) is not None:
                parts.append(f"backend_signature={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='3d004bb709cfd5191544d5d9edf1cfb6a6c1cc52',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, True, False, False, False, Fals"
            "e, False, True, False), ((('text', True, True, None, True, False, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('backend_signature', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('redacted', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), "
            "((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.content', 'ThinkingContent'),
    ),
)
def _process_dataclass__3d004bb709cfd5191544d5d9edf1cfb6a6c1cc52():
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
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                text=self.text,
                backend_signature=self.backend_signature,
                redacted=self.redacted,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.text == other.text and
                self.backend_signature == other.backend_signature and
                self.redacted == other.redacted
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'text',
            'backend_signature',
            'redacted',
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
            try:
                return self.__dataclass_hash__
            except AttributeError:
                pass
            object.__setattr__(
                self,
                '__dataclass_hash__',
                h := hash((
                    self.text,
                    self.backend_signature,
                    self.redacted,
                ))
            )
            return h

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            text: __dataclass__init__fields__0__annotation,
            *,
            backend_signature: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            redacted: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'text', text)
            __dataclass__object_setattr(self, 'backend_signature', backend_signature)
            __dataclass__object_setattr(self, 'redacted', redacted)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.text)) is not None:
                parts.append(f"{s}")
            if (s := __dataclass__repr__default_fn(self.backend_signature)) is not None:
                parts.append(f"backend_signature={s}")
            if (s := __dataclass__repr__default_fn(self.redacted)) is not None:
                parts.append(f"redacted={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d67f1405db8f2bfe0ccb83ee5c761c1c1e20350f',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, True, False, False, False, Fals"
            "e, False, False, False), ((('id', True, True, None, True, False, False, None), 'instance', 'missing', None"
            ", False, False, False), (('name', True, True, None, True, False, False, None), 'instance', 'missing', None"
            ", False, False, False), (('args', True, True, None, True, False, False, None), 'instance', 'missing', None"
            ", False, False, False), (('backend_signature', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (("
            "),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.content', 'ToolCall'),
    ),
)
def _process_dataclass__d67f1405db8f2bfe0ccb83ee5c761c1c1e20350f():
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
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                id=self.id,
                name=self.name,
                args=self.args,
                backend_signature=self.backend_signature,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.id == other.id and
                self.name == other.name and
                self.args == other.args and
                self.backend_signature == other.backend_signature
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'id',
            'name',
            'args',
            'backend_signature',
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
            try:
                return self.__dataclass_hash__
            except AttributeError:
                pass
            object.__setattr__(
                self,
                '__dataclass_hash__',
                h := hash((
                    self.id,
                    self.name,
                    self.args,
                    self.backend_signature,
                ))
            )
            return h

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            id: __dataclass__init__fields__0__annotation,
            name: __dataclass__init__fields__1__annotation,
            args: __dataclass__init__fields__2__annotation,
            *,
            backend_signature: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'id', id)
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'args', args)
            __dataclass__object_setattr(self, 'backend_signature', backend_signature)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.id)) is not None:
                parts.append(f"id={s}")
            if (s := __dataclass__repr__default_fn(self.name)) is not None:
                parts.append(f"name={s}")
            if (s := __dataclass__repr__default_fn(self.args)) is not None:
                parts.append(f"args={s}")
            if (s := __dataclass__repr__default_fn(self.backend_signature)) is not None:
                parts.append(f"backend_signature={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='01c176423c1233357d20327fea699b5b4b00ae58',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('system_prompt', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('messages', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('tools', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.context', 'Context'),
    ),
)
def _process_dataclass__01c176423c1233357d20327fea699b5b4b00ae58():
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
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                system_prompt=self.system_prompt,
                messages=self.messages,
                tools=self.tools,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.system_prompt == other.system_prompt and
                self.messages == other.messages and
                self.tools == other.tools
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'system_prompt',
            'messages',
            'tools',
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
                self.system_prompt,
                self.messages,
                self.tools,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            system_prompt: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            messages: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            tools: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'system_prompt', system_prompt)
            __dataclass__object_setattr(self, 'messages', messages)
            __dataclass__object_setattr(self, 'tools', tools)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.system_prompt)) is not None:
                parts.append(f"system_prompt={s}")
            if (s := __dataclass__repr__default_fn(self.messages)) is not None:
                parts.append(f"messages={s}")
            if (s := __dataclass__repr__default_fn(self.tools)) is not None:
                parts.append(f"tools={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='73589c6acd06a96ebb0bfcd5a62126cf15ed673a',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, True, False, False, False, Fals"
            "e, False, True, False), ((('content', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('stop_reason', True, True, None, True, False, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('token_usage', True, True, None, True, False, False, None), 'instance',"
            " 'value', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ())"
            ", ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.messages', 'AiMessage'),
    ),
)
def _process_dataclass__73589c6acd06a96ebb0bfcd5a62126cf15ed673a():
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
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                content=self.content,
                stop_reason=self.stop_reason,
                token_usage=self.token_usage,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.content == other.content and
                self.stop_reason == other.stop_reason and
                self.token_usage == other.token_usage
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'content',
            'stop_reason',
            'token_usage',
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
            try:
                return self.__dataclass_hash__
            except AttributeError:
                pass
            object.__setattr__(
                self,
                '__dataclass_hash__',
                h := hash((
                    self.content,
                    self.stop_reason,
                    self.token_usage,
                ))
            )
            return h

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            content: __dataclass__init__fields__0__annotation,
            stop_reason: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            token_usage: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'content', content)
            __dataclass__object_setattr(self, 'stop_reason', stop_reason)
            __dataclass__object_setattr(self, 'token_usage', token_usage)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.content)) is not None:
                parts.append(f"{s}")
            if (s := __dataclass__repr__default_fn(self.stop_reason)) is not None:
                parts.append(f"{s}")
            if (s := __dataclass__repr__default_fn(self.token_usage)) is not None:
                parts.append(f"{s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='6ab8a16093c54e5146d685aeda1602f92ab5de9c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, True, False, False, False, False"
            ", False, False, False), ((('source', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('input', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('output', True, True, None, True, True, False, None), 'instance', 'value', None,"
            " False, False, False), (('reasoning', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('cache_read', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('cache_write', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('total', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.messages', 'TokenCost'),
    ),
)
def _process_dataclass__6ab8a16093c54e5146d685aeda1602f92ab5de9c():
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
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__6__default = __dataclass__spec.fields[6].default.must()
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                source=self.source,
                input=self.input,
                output=self.output,
                reasoning=self.reasoning,
                cache_read=self.cache_read,
                cache_write=self.cache_write,
                total=self.total,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.source == other.source and
                self.input == other.input and
                self.output == other.output and
                self.reasoning == other.reasoning and
                self.cache_read == other.cache_read and
                self.cache_write == other.cache_write and
                self.total == other.total
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'source',
            'input',
            'output',
            'reasoning',
            'cache_read',
            'cache_write',
            'total',
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
            try:
                return self.__dataclass_hash__
            except AttributeError:
                pass
            object.__setattr__(
                self,
                '__dataclass_hash__',
                h := hash((
                    self.source,
                    self.input,
                    self.output,
                    self.reasoning,
                    self.cache_read,
                    self.cache_write,
                    self.total,
                ))
            )
            return h

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            source: __dataclass__init__fields__0__annotation,
            input: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            output: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            reasoning: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            cache_read: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            cache_write: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            total: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'source', source)
            __dataclass__object_setattr(self, 'input', input)
            __dataclass__object_setattr(self, 'output', output)
            __dataclass__object_setattr(self, 'reasoning', reasoning)
            __dataclass__object_setattr(self, 'cache_read', cache_read)
            __dataclass__object_setattr(self, 'cache_write', cache_write)
            __dataclass__object_setattr(self, 'total', total)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.source)) is not None:
                parts.append(f"source={s}")
            if (s := __dataclass__repr__default_fn(self.input)) is not None:
                parts.append(f"input={s}")
            if (s := __dataclass__repr__default_fn(self.output)) is not None:
                parts.append(f"output={s}")
            if (s := __dataclass__repr__default_fn(self.reasoning)) is not None:
                parts.append(f"reasoning={s}")
            if (s := __dataclass__repr__default_fn(self.cache_read)) is not None:
                parts.append(f"cache_read={s}")
            if (s := __dataclass__repr__default_fn(self.cache_write)) is not None:
                parts.append(f"cache_write={s}")
            if (s := __dataclass__repr__default_fn(self.total)) is not None:
                parts.append(f"total={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='77b85af967ff8bf505995ad32a8eaf99edbd533e',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, True, False, False, False, False"
            ", False, False, False), ((('input', True, True, None, True, True, False, None), 'instance', 'value', None,"
            " False, False, False), (('output', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False), (('reasoning', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('cache_read', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('cache_write', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False), (('total', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('cost', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (),"
            " (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.messages', 'TokenUsage'),
    ),
)
def _process_dataclass__77b85af967ff8bf505995ad32a8eaf99edbd533e():
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
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__6__default = __dataclass__spec.fields[6].default.must()
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                input=self.input,
                output=self.output,
                reasoning=self.reasoning,
                cache_read=self.cache_read,
                cache_write=self.cache_write,
                total=self.total,
                cost=self.cost,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.input == other.input and
                self.output == other.output and
                self.reasoning == other.reasoning and
                self.cache_read == other.cache_read and
                self.cache_write == other.cache_write and
                self.total == other.total and
                self.cost == other.cost
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'input',
            'output',
            'reasoning',
            'cache_read',
            'cache_write',
            'total',
            'cost',
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
            try:
                return self.__dataclass_hash__
            except AttributeError:
                pass
            object.__setattr__(
                self,
                '__dataclass_hash__',
                h := hash((
                    self.input,
                    self.output,
                    self.reasoning,
                    self.cache_read,
                    self.cache_write,
                    self.total,
                    self.cost,
                ))
            )
            return h

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            input: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            output: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            reasoning: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            cache_read: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            cache_write: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            total: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            cost: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'input', input)
            __dataclass__object_setattr(self, 'output', output)
            __dataclass__object_setattr(self, 'reasoning', reasoning)
            __dataclass__object_setattr(self, 'cache_read', cache_read)
            __dataclass__object_setattr(self, 'cache_write', cache_write)
            __dataclass__object_setattr(self, 'total', total)
            __dataclass__object_setattr(self, 'cost', cost)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.input)) is not None:
                parts.append(f"input={s}")
            if (s := __dataclass__repr__default_fn(self.output)) is not None:
                parts.append(f"output={s}")
            if (s := __dataclass__repr__default_fn(self.reasoning)) is not None:
                parts.append(f"reasoning={s}")
            if (s := __dataclass__repr__default_fn(self.cache_read)) is not None:
                parts.append(f"cache_read={s}")
            if (s := __dataclass__repr__default_fn(self.cache_write)) is not None:
                parts.append(f"cache_write={s}")
            if (s := __dataclass__repr__default_fn(self.total)) is not None:
                parts.append(f"total={s}")
            if (s := __dataclass__repr__default_fn(self.cost)) is not None:
                parts.append(f"cost={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='1811253961cf62a364c4dd562c66135bd35c6b4a',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, True, False, False, False, False"
            ", False, True, False), ((('tool_call_id', True, True, None, True, True, False, None), 'instance', 'missing"
            "', None, False, False, False), (('tool_name', True, True, None, True, True, False, None), 'instance', 'mis"
            "sing', None, False, False, False), (('content', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('is_error', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()),"
            " ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.messages', 'ToolResultMessage'),
    ),
)
def _process_dataclass__1811253961cf62a364c4dd562c66135bd35c6b4a():
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
                tool_call_id=self.tool_call_id,
                tool_name=self.tool_name,
                content=self.content,
                is_error=self.is_error,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.tool_call_id == other.tool_call_id and
                self.tool_name == other.tool_name and
                self.content == other.content and
                self.is_error == other.is_error
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'tool_call_id',
            'tool_name',
            'content',
            'is_error',
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
            try:
                return self.__dataclass_hash__
            except AttributeError:
                pass
            object.__setattr__(
                self,
                '__dataclass_hash__',
                h := hash((
                    self.tool_call_id,
                    self.tool_name,
                    self.content,
                    self.is_error,
                ))
            )
            return h

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            tool_call_id: __dataclass__init__fields__0__annotation,
            tool_name: __dataclass__init__fields__1__annotation,
            content: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            is_error: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'tool_call_id', tool_call_id)
            __dataclass__object_setattr(self, 'tool_name', tool_name)
            __dataclass__object_setattr(self, 'content', content)
            __dataclass__object_setattr(self, 'is_error', is_error)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"tool_call_id={self.tool_call_id!r}")
            parts.append(f"tool_name={self.tool_name!r}")
            parts.append(f"content={self.content!r}")
            parts.append(f"is_error={self.is_error!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b14bb55f0c85ebd85db2c4cf48a2fd43c569f18e',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, True, False, False, False, Fals"
            "e, False, True, False), ((('content', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.messages', 'UserMessage'),
    ),
)
def _process_dataclass__b14bb55f0c85ebd85db2c4cf48a2fd43c569f18e():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                content=self.content,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.content == other.content
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
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
            try:
                return self.__dataclass_hash__
            except AttributeError:
                pass
            object.__setattr__(
                self,
                '__dataclass_hash__',
                h := hash((
                    self.content,
                ))
            )
            return h

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            content: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'content', content)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"{self.content!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='bc02c695271bc73a188d8cf86151ad8ebdc355d9',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('control_style', True, True, None, True, True, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('retentions', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False), (('key', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (()"
            ",), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.models', 'CacheCapabilities'),
    ),
)
def _process_dataclass__bc02c695271bc73a188d8cf86151ad8ebdc355d9():
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
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                control_style=self.control_style,
                retentions=self.retentions,
                key=self.key,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.control_style == other.control_style and
                self.retentions == other.retentions and
                self.key == other.key
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'control_style',
            'retentions',
            'key',
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
                self.control_style,
                self.retentions,
                self.key,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            control_style: __dataclass__init__fields__0__annotation,
            retentions: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            key: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'control_style', control_style)
            __dataclass__object_setattr(self, 'retentions', retentions)
            __dataclass__object_setattr(self, 'key', key)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.control_style)) is not None:
                parts.append(f"control_style={s}")
            if (s := __dataclass__repr__default_fn(self.retentions)) is not None:
                parts.append(f"retentions={s}")
            if (s := __dataclass__repr__default_fn(self.key)) is not None:
                parts.append(f"key={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='310cc65a84bae9ea8451bfed57a5a0e20498bcd4',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('key', True, True, None, True, True, False, None), 'instance', 'missing', None"
            ", False, False, False), (('backend', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('name', True, True, None, True, True, False, None), 'instance', 'value', None,"
            " False, False, False), (('compat', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False), (('cache', True, True, None, True, True, False, None), 'instance', 'value', None, Fa"
            "lse, False, False), (('reasoning_efforts', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('reasoning_efforts_with_tools', True, True, None, True, True, False, None)"
            ", 'instance', 'value', None, False, False, False), (('limits', True, True, None, True, True, False, None),"
            " 'instance', 'value', None, False, False, False), (('pricing', True, True, None, True, True, False, None),"
            " 'instance', 'value', None, False, False, False), (('http', True, True, None, True, True, False, None), 'i"
            "nstance', 'value', None, False, False, False), (('default_options', True, True, None, True, True, False, N"
            "one), 'instance', 'value', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), ("
            "False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.models', 'Model'),
    ),
)
def _process_dataclass__310cc65a84bae9ea8451bfed57a5a0e20498bcd4():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__01__annotation = __dataclass__spec.fields[1].annotation
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
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                key=self.key,
                backend=self.backend,
                name=self.name,
                compat=self.compat,
                cache=self.cache,
                reasoning_efforts=self.reasoning_efforts,
                reasoning_efforts_with_tools=self.reasoning_efforts_with_tools,
                limits=self.limits,
                pricing=self.pricing,
                http=self.http,
                default_options=self.default_options,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.key == other.key and
                self.backend == other.backend and
                self.name == other.name and
                self.compat == other.compat and
                self.cache == other.cache and
                self.reasoning_efforts == other.reasoning_efforts and
                self.reasoning_efforts_with_tools == other.reasoning_efforts_with_tools and
                self.limits == other.limits and
                self.pricing == other.pricing and
                self.http == other.http and
                self.default_options == other.default_options
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'key',
            'backend',
            'name',
            'compat',
            'cache',
            'reasoning_efforts',
            'reasoning_efforts_with_tools',
            'limits',
            'pricing',
            'http',
            'default_options',
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
                self.backend,
                self.name,
                self.compat,
                self.cache,
                self.reasoning_efforts,
                self.reasoning_efforts_with_tools,
                self.limits,
                self.pricing,
                self.http,
                self.default_options,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            key: __dataclass__init__fields__00__annotation,
            backend: __dataclass__init__fields__01__annotation,
            name: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            compat: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            cache: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            reasoning_efforts: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            reasoning_efforts_with_tools: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            limits: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            pricing: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            http: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            default_options: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'backend', backend)
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'compat', compat)
            __dataclass__object_setattr(self, 'cache', cache)
            __dataclass__object_setattr(self, 'reasoning_efforts', reasoning_efforts)
            __dataclass__object_setattr(self, 'reasoning_efforts_with_tools', reasoning_efforts_with_tools)
            __dataclass__object_setattr(self, 'limits', limits)
            __dataclass__object_setattr(self, 'pricing', pricing)
            __dataclass__object_setattr(self, 'http', http)
            __dataclass__object_setattr(self, 'default_options', default_options)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.key)) is not None:
                parts.append(f"key={s}")
            if (s := __dataclass__repr__default_fn(self.backend)) is not None:
                parts.append(f"backend={s}")
            if (s := __dataclass__repr__default_fn(self.name)) is not None:
                parts.append(f"name={s}")
            if (s := __dataclass__repr__default_fn(self.compat)) is not None:
                parts.append(f"compat={s}")
            if (s := __dataclass__repr__default_fn(self.cache)) is not None:
                parts.append(f"cache={s}")
            if (s := __dataclass__repr__default_fn(self.reasoning_efforts)) is not None:
                parts.append(f"reasoning_efforts={s}")
            if (s := __dataclass__repr__default_fn(self.reasoning_efforts_with_tools)) is not None:
                parts.append(f"reasoning_efforts_with_tools={s}")
            if (s := __dataclass__repr__default_fn(self.limits)) is not None:
                parts.append(f"limits={s}")
            if (s := __dataclass__repr__default_fn(self.pricing)) is not None:
                parts.append(f"pricing={s}")
            if (s := __dataclass__repr__default_fn(self.http)) is not None:
                parts.append(f"http={s}")
            if (s := __dataclass__repr__default_fn(self.default_options)) is not None:
                parts.append(f"default_options={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c35e74da0f0490f6f065cd19ed7ab578ce9e861f',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('base_url', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('extra_headers', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (()"
            ",), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.models', 'Model.Http'),
    ),
)
def _process_dataclass__c35e74da0f0490f6f065cd19ed7ab578ce9e861f():
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
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                base_url=self.base_url,
                extra_headers=self.extra_headers,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.base_url == other.base_url and
                self.extra_headers == other.extra_headers
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'base_url',
            'extra_headers',
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
                self.base_url,
                self.extra_headers,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            base_url: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            extra_headers: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'base_url', base_url)
            __dataclass__object_setattr(self, 'extra_headers', extra_headers)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.base_url)) is not None:
                parts.append(f"base_url={s}")
            if (s := __dataclass__repr__default_fn(self.extra_headers)) is not None:
                parts.append(f"extra_headers={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='ec91dedc9bf4e27b6274437e69dc4c4488e8c3ce',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, True, False, False, False, Fals"
            "e, False, True, False), ((('provider', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('id', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, True, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.models', 'ModelKey'),
    ),
)
def _process_dataclass__ec91dedc9bf4e27b6274437e69dc4c4488e8c3ce():
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
                provider=self.provider,
                id=self.id,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.provider == other.provider and
                self.id == other.id
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'provider',
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
            try:
                return self.__dataclass_hash__
            except AttributeError:
                pass
            object.__setattr__(
                self,
                '__dataclass_hash__',
                h := hash((
                    self.provider,
                    self.id,
                ))
            )
            return h

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            provider: __dataclass__init__fields__0__annotation,
            id: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'provider', provider)
            __dataclass__object_setattr(self, 'id', id)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"{self.provider!r}")
            parts.append(f"{self.id!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='83263e330e5e68cd9ce9e2e545125d5fd4853965',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('context', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False), (('output', True, True, None, True, True, False, None), 'instance', 'missing',"
            " None, False, False, False), (('input', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, True, ()), ((),), (),"
            " (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.models', 'ModelLimits'),
    ),
)
def _process_dataclass__83263e330e5e68cd9ce9e2e545125d5fd4853965():
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
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                context=self.context,
                output=self.output,
                input=self.input,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.context == other.context and
                self.output == other.output and
                self.input == other.input
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'context',
            'output',
            'input',
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
                self.context,
                self.output,
                self.input,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            context: __dataclass__init__fields__0__annotation,
            output: __dataclass__init__fields__1__annotation,
            input: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'context', context)
            __dataclass__object_setattr(self, 'output', output)
            __dataclass__object_setattr(self, 'input', input)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.context)) is not None:
                parts.append(f"context={s}")
            if (s := __dataclass__repr__default_fn(self.output)) is not None:
                parts.append(f"output={s}")
            if (s := __dataclass__repr__default_fn(self.input)) is not None:
                parts.append(f"input={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='f1940bdce2f09a064f1feae555b3d46ca457813e',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('input', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('output', True, True, None, True, True, False, None), 'instance', 'value', None,"
            " False, False, False), (('reasoning', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('cache_read', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('cache_write', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.models', 'TokenPricing'),
    ),
)
def _process_dataclass__f1940bdce2f09a064f1feae555b3d46ca457813e():
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
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                input=self.input,
                output=self.output,
                reasoning=self.reasoning,
                cache_read=self.cache_read,
                cache_write=self.cache_write,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.input == other.input and
                self.output == other.output and
                self.reasoning == other.reasoning and
                self.cache_read == other.cache_read and
                self.cache_write == other.cache_write
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'input',
            'output',
            'reasoning',
            'cache_read',
            'cache_write',
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
                self.input,
                self.output,
                self.reasoning,
                self.cache_read,
                self.cache_write,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            input: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            output: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            reasoning: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            cache_read: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            cache_write: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'input', input)
            __dataclass__object_setattr(self, 'output', output)
            __dataclass__object_setattr(self, 'reasoning', reasoning)
            __dataclass__object_setattr(self, 'cache_read', cache_read)
            __dataclass__object_setattr(self, 'cache_write', cache_write)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.input)) is not None:
                parts.append(f"input={s}")
            if (s := __dataclass__repr__default_fn(self.output)) is not None:
                parts.append(f"output={s}")
            if (s := __dataclass__repr__default_fn(self.reasoning)) is not None:
                parts.append(f"reasoning={s}")
            if (s := __dataclass__repr__default_fn(self.cache_read)) is not None:
                parts.append(f"cache_read={s}")
            if (s := __dataclass__repr__default_fn(self.cache_write)) is not None:
                parts.append(f"cache_write={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d2ab7a668058a4fe241651d81e6f984e78cb900b',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('ZERO', True, True, None, True, None, False, None), 'class_var', 'missing', No"
            "ne, False, False, False), (('max_tokens', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('thinking', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('reasoning_effort', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, True, False, False), (('cache_key', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('cache_retention', True, True, None, True, True, False, None), '"
            "instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False,"
            " False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.options', 'Options'),
    ),
)
def _process_dataclass__d2ab7a668058a4fe241651d81e6f984e78cb900b():
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
        __dataclass__init__fields__3__validate = __dataclass__spec.fields[3].validate
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__default = __dataclass__spec.fields[5].default.must()
        __dataclass__FieldFnValidationError = __dataclass__globals['__dataclass__FieldFnValidationError']
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                max_tokens=self.max_tokens,
                thinking=self.thinking,
                reasoning_effort=self.reasoning_effort,
                cache_key=self.cache_key,
                cache_retention=self.cache_retention,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.max_tokens == other.max_tokens and
                self.thinking == other.thinking and
                self.reasoning_effort == other.reasoning_effort and
                self.cache_key == other.cache_key and
                self.cache_retention == other.cache_retention
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'ZERO',
            'max_tokens',
            'thinking',
            'reasoning_effort',
            'cache_key',
            'cache_retention',
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
                self.max_tokens,
                self.thinking,
                self.reasoning_effort,
                self.cache_key,
                self.cache_retention,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            max_tokens: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            thinking: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            reasoning_effort: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            cache_key: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            cache_retention: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            if not __dataclass__init__fields__3__validate(reasoning_effort): 
                raise __dataclass__FieldFnValidationError(
                    obj=self,
                    fn=__dataclass__init__fields__3__validate,
                    field='reasoning_effort',
                    value=reasoning_effort,
                )
            __dataclass__object_setattr(self, 'max_tokens', max_tokens)
            __dataclass__object_setattr(self, 'thinking', thinking)
            __dataclass__object_setattr(self, 'reasoning_effort', reasoning_effort)
            __dataclass__object_setattr(self, 'cache_key', cache_key)
            __dataclass__object_setattr(self, 'cache_retention', cache_retention)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"max_tokens={self.max_tokens!r}")
            parts.append(f"thinking={self.thinking!r}")
            parts.append(f"reasoning_effort={self.reasoning_effort!r}")
            parts.append(f"cache_key={self.cache_key!r}")
            parts.append(f"cache_retention={self.cache_retention!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='6dfce0a6a7f55b58aa1423cf1b0c48bb05860bf1',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('content_index', True, True, None, True, True, False, None), 'instance', 'mis"
            "sing', None, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()),"
            " ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.streams', 'ContentAiStreamEvent'),
        ('omllm.llm.types.streams', 'TextStartAiStreamEvent'),
        ('omllm.llm.types.streams', 'ThinkingStartAiStreamEvent'),
    ),
)
def _process_dataclass__6dfce0a6a7f55b58aa1423cf1b0c48bb05860bf1():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                content_index=self.content_index,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.content_index == other.content_index
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'content_index',
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
                self.content_index,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            content_index: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'content_index', content_index)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"content_index={self.content_index!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='785d3340e352108621db70b3991eefc1b9e6ad6d',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, True, False, False, False, Fals"
            "e, False, True, False), ((('content_index', True, True, None, True, True, False, None), 'instance', 'missi"
            "ng', None, False, False, False), (('text', True, True, None, True, False, False, None), 'instance', 'missi"
            "ng', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (("
            "),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.streams', 'TextDeltaAiStreamEvent'),
        ('omllm.llm.types.streams', 'TextEndAiStreamEvent'),
        ('omllm.llm.types.streams', 'ThinkingDeltaAiStreamEvent'),
        ('omllm.llm.types.streams', 'ThinkingEndAiStreamEvent'),
        ('omllm.llm.types.streams', 'ToolCallDeltaAiStreamEvent'),
    ),
)
def _process_dataclass__785d3340e352108621db70b3991eefc1b9e6ad6d():
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
                content_index=self.content_index,
                text=self.text,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.content_index == other.content_index and
                self.text == other.text
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'content_index',
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
            try:
                return self.__dataclass_hash__
            except AttributeError:
                pass
            object.__setattr__(
                self,
                '__dataclass_hash__',
                h := hash((
                    self.content_index,
                    self.text,
                ))
            )
            return h

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            text: __dataclass__init__fields__1__annotation,
            *,
            content_index: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'content_index', content_index)
            __dataclass__object_setattr(self, 'text', text)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"{self.text!r}")
            parts.append(f"content_index={self.content_index!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='22b56f42c1e3080324a73a7ffdcfa93f3b1428bb',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, True, False, False, False, Fals"
            "e, False, True, False), ((('content_index', True, True, None, True, True, False, None), 'instance', 'missi"
            "ng', None, False, False, False), (('tool_call', True, True, None, True, False, False, None), 'instance', '"
            "missing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()"
            "), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.streams', 'ToolCallEndAiStreamEvent'),
    ),
)
def _process_dataclass__22b56f42c1e3080324a73a7ffdcfa93f3b1428bb():
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
                content_index=self.content_index,
                tool_call=self.tool_call,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.content_index == other.content_index and
                self.tool_call == other.tool_call
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'content_index',
            'tool_call',
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
            try:
                return self.__dataclass_hash__
            except AttributeError:
                pass
            object.__setattr__(
                self,
                '__dataclass_hash__',
                h := hash((
                    self.content_index,
                    self.tool_call,
                ))
            )
            return h

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            tool_call: __dataclass__init__fields__1__annotation,
            *,
            content_index: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'content_index', content_index)
            __dataclass__object_setattr(self, 'tool_call', tool_call)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"{self.tool_call!r}")
            parts.append(f"content_index={self.content_index!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='6d7824d7a618ba9a6a216a2668ce02f26bd54483',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, True, False, False, False, Fals"
            "e, False, False, False), ((('content_index', True, True, None, True, True, False, None), 'instance', 'miss"
            "ing', None, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), "
            "((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.streams', 'ToolCallStartAiStreamEvent'),
    ),
)
def _process_dataclass__6d7824d7a618ba9a6a216a2668ce02f26bd54483():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                content_index=self.content_index,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.content_index == other.content_index
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'content_index',
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
            try:
                return self.__dataclass_hash__
            except AttributeError:
                pass
            object.__setattr__(
                self,
                '__dataclass_hash__',
                h := hash((
                    self.content_index,
                ))
            )
            return h

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            content_index: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'content_index', content_index)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"content_index={self.content_index!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='72e676f092a1cc56ffd099d541d8c15b2c624b57',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, True, False), ((('type', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('values', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.tools', 'EnumToolDtype'),
    ),
)
def _process_dataclass__72e676f092a1cc56ffd099d541d8c15b2c624b57():
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
                type=self.type,
                values=self.values,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type and
                self.values == other.values
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'type',
            'values',
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
                self.values,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            type: __dataclass__init__fields__0__annotation,
            values: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'type', type)
            __dataclass__object_setattr(self, 'values', values)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"{self.type!r}")
            parts.append(f"{self.values!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='ec429fc080b3c91c1dda151f6aaa24a313872a17',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, True, False), ((('key', True, True, None, True, False, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('value', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.tools', 'MappingToolDtype'),
    ),
)
def _process_dataclass__ec429fc080b3c91c1dda151f6aaa24a313872a17():
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
                key=self.key,
                value=self.value,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.key == other.key and
                self.value == other.value
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'key',
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
                self.key,
                self.value,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            key: __dataclass__init__fields__0__annotation,
            value: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'value', value)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"{self.key!r}")
            parts.append(f"{self.value!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='dde0a1aa2e8a444b6873def0fee730ac66beb444',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, True, False), ((('type', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.tools', 'NullableToolDtype'),
    ),
)
def _process_dataclass__dde0a1aa2e8a444b6873def0fee730ac66beb444():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                type=self.type,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'type',
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
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            type: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'type', type)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"{self.type!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='0907dd5a6a2b8b49a9cf9fc4107af9bd3ad005c9',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, True, False), ((('fields', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.tools', 'ObjectToolDtype'),
    ),
)
def _process_dataclass__0907dd5a6a2b8b49a9cf9fc4107af9bd3ad005c9():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                fields=self.fields,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.fields == other.fields
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'fields',
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
                self.fields,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            fields: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'fields', fields)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"{self.fields!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c53842a68b20c4a6314a86f212781d146e5ba23c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, True, False), ((('type', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, True, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.tools', 'PrimitiveToolDtype'),
    ),
)
def _process_dataclass__c53842a68b20c4a6314a86f212781d146e5ba23c():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                type=self.type,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'type',
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
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            type: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'type', type)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"{self.type!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='eeefbc8165d858fc71db8571850b59c11d98bd28',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, True, False), ((('element', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.tools', 'SequenceToolDtype'),
    ),
)
def _process_dataclass__eeefbc8165d858fc71db8571850b59c11d98bd28():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                element=self.element,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.element == other.element
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'element',
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
                self.element,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            element: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'element', element)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"{self.element!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='608991abc44e0fddcf6c11f1c17a884cc5324ed0',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('name', True, True, None, True, True, False, None), 'instance', 'missing', 'ca"
            "llable', False, False, False), (('description', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('params', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('allow_additional_params', True, True, None, True, True, False, None),"
            " 'instance', 'value', None, False, False, False), (('return_type', True, True, None, True, True, False, No"
            "ne), 'instance', 'value', None, False, False, False), (('return_description', True, True, None, True, True"
            ", False, None), 'instance', 'value', None, False, False, False)), True, 1, ()), ((False,), (False,), (), ("
            "False,), (False, False, ('getter',)), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.tools', 'Tool'),
    ),
)
def _process_dataclass__608991abc44e0fddcf6c11f1c17a884cc5324ed0():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__coerce = __dataclass__spec.fields[0].coerce
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
        __dataclass__init__init_fns__0 = __dataclass__ctx['omcore.dataclasses.impl.concerns.init.InitFunctions'].values[0]
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                name=self.name,
                description=self.description,
                params=self.params,
                allow_additional_params=self.allow_additional_params,
                return_type=self.return_type,
                return_description=self.return_description,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.description == other.description and
                self.params == other.params and
                self.allow_additional_params == other.allow_additional_params and
                self.return_type == other.return_type and
                self.return_description == other.return_description
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'description',
            'params',
            'allow_additional_params',
            'return_type',
            'return_description',
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
                self.name,
                self.description,
                self.params,
                self.allow_additional_params,
                self.return_type,
                self.return_description,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            name: __dataclass__init__fields__0__annotation,
            description: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            params: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            allow_additional_params: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            return_type: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            return_description: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            name = __dataclass__init__fields__0__coerce(name)
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'description', description)
            __dataclass__object_setattr(self, 'params', params)
            __dataclass__object_setattr(self, 'allow_additional_params', allow_additional_params)
            __dataclass__object_setattr(self, 'return_type', return_type)
            __dataclass__object_setattr(self, 'return_description', return_description)
            __dataclass__init__init_fns__0(self)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.name)) is not None:
                parts.append(f"name={s}")
            if (s := __dataclass__repr__default_fn(self.description)) is not None:
                parts.append(f"description={s}")
            if (s := __dataclass__repr__default_fn(self.params)) is not None:
                parts.append(f"params={s}")
            if (s := __dataclass__repr__default_fn(self.allow_additional_params)) is not None:
                parts.append(f"allow_additional_params={s}")
            if (s := __dataclass__repr__default_fn(self.return_type)) is not None:
                parts.append(f"return_type={s}")
            if (s := __dataclass__repr__default_fn(self.return_description)) is not None:
                parts.append(f"return_description={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='3335c6f43733e3d41bf1b8e6d242a76bf1619037',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('name', True, True, None, True, True, False, None), 'instance', 'missing', 'ca"
            "llable', False, False, False), (('description', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('type', True, True, None, True, True, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('optional', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, True)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (("
            "),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.tools', 'ToolParam'),
    ),
)
def _process_dataclass__3335c6f43733e3d41bf1b8e6d242a76bf1619037():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__coerce = __dataclass__spec.fields[0].coerce
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
        __dataclass__repr__fns__3__fn = __dataclass__spec.fields[3].repr_fn
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                name=self.name,
                description=self.description,
                type=self.type,
                optional=self.optional,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.description == other.description and
                self.type == other.type and
                self.optional == other.optional
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'description',
            'type',
            'optional',
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
                self.name,
                self.description,
                self.type,
                self.optional,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            name: __dataclass__init__fields__0__annotation,
            description: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            type: __dataclass__init__fields__2__annotation,
            optional: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            name = __dataclass__init__fields__0__coerce(name)
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'description', description)
            __dataclass__object_setattr(self, 'type', type)
            __dataclass__object_setattr(self, 'optional', optional)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.name)) is not None:
                parts.append(f"name={s}")
            if (s := __dataclass__repr__default_fn(self.description)) is not None:
                parts.append(f"description={s}")
            if (s := __dataclass__repr__default_fn(self.type)) is not None:
                parts.append(f"type={s}")
            if (s := __dataclass__repr__fns__3__fn(self.optional)) is not None:
                parts.append(f"optional={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='130b2e3e21e89269e2acfbe420ffcc2d9f5db58a',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, True, False), ((('elements', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.tools', 'TupleToolDtype'),
    ),
)
def _process_dataclass__130b2e3e21e89269e2acfbe420ffcc2d9f5db58a():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                elements=self.elements,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.elements == other.elements
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'elements',
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
                self.elements,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            elements: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'elements', elements)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"{self.elements!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='69984f4f612c4f7678da51bc8ff52c5c1d0e61e7',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, True, False), ((('args', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, True, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.llm.types.tools', 'UnionToolDtype'),
    ),
)
def _process_dataclass__69984f4f612c4f7678da51bc8ff52c5c1d0e61e7():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                args=self.args,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.args == other.args
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'args',
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
                self.args,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            args: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'args', args)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"{self.args!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
