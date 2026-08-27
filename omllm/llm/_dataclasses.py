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
        "Plans(tup=(CopyPlan(fields=('uncached_input_tokens', 'cache_read_tokens', 'cache_write_tokens')), EqPlan(field"
        "s=('uncached_input_tokens', 'cache_read_tokens', 'cache_write_tokens')), FrozenPlan(fields=('uncached_input_to"
        "kens', 'cache_read_tokens', 'cache_write_tokens'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', f"
        "ields=('uncached_input_tokens', 'cache_read_tokens', 'cache_write_tokens'), cache=False), InitPlan(fields=(Ini"
        "tPlan.Field(name='uncached_input_tokens', annotation=OpRef(name='init.fields.0.annotation'), default=None, def"
        "ault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check"
        "_type=None), InitPlan.Field(name='cache_read_tokens', annotation=OpRef(name='init.fields.1.annotation'), defau"
        "lt=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate"
        "=None, check_type=None), InitPlan.Field(name='cache_write_tokens', annotation=OpRef(name='init.fields.2.annota"
        "tion'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=N"
        "one, validate=None, check_type=None)), self_param='self', std_params=(), kw_only_params=('uncached_input_token"
        "s', 'cache_read_tokens', 'cache_write_tokens'), frozen=True, slots=False, post_init_params=None, init_fns=(), "
        "validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='uncached_input_tokens', kw_only=True, fn=None), ReprPl"
        "an.Field(name='cache_read_tokens', kw_only=True, fn=None), ReprPlan.Field(name='cache_write_tokens', kw_only=T"
        "rue, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='299b40a7eb7cf228bd2cef6d52029e8385e912ee',
    cls_names=(
        ('omllm.llm.backends.scripted.caching', 'SimulatedCacheUsage'),
    ),
)
def _process_dataclass__299b40a7eb7cf228bd2cef6d52029e8385e912ee():
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
                uncached_input_tokens=self.uncached_input_tokens,
                cache_read_tokens=self.cache_read_tokens,
                cache_write_tokens=self.cache_write_tokens,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.uncached_input_tokens == other.uncached_input_tokens and
                self.cache_read_tokens == other.cache_read_tokens and
                self.cache_write_tokens == other.cache_write_tokens
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'uncached_input_tokens',
            'cache_read_tokens',
            'cache_write_tokens',
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
                self.uncached_input_tokens,
                self.cache_read_tokens,
                self.cache_write_tokens,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            uncached_input_tokens: __dataclass__init__fields__0__annotation,
            cache_read_tokens: __dataclass__init__fields__1__annotation,
            cache_write_tokens: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'uncached_input_tokens', uncached_input_tokens)
            __dataclass__object_setattr(self, 'cache_read_tokens', cache_read_tokens)
            __dataclass__object_setattr(self, 'cache_write_tokens', cache_write_tokens)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"uncached_input_tokens={self.uncached_input_tokens!r}")
            parts.append(f"cache_read_tokens={self.cache_read_tokens!r}")
            parts.append(f"cache_write_tokens={self.cache_write_tokens!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('invocation_index', 'url', 'headers', 'payload', 'request')), EqPlan(fields=('invo"
        "cation_index', 'url', 'headers', 'payload', 'request')), FrozenPlan(fields=('invocation_index', 'url', 'header"
        "s', 'payload', 'request'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('invocation_index"
        "', 'url', 'headers', 'payload', 'request'), cache=False), InitPlan(fields=(InitPlan.Field(name='invocation_ind"
        "ex', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, overrid"
        "e=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='url"
        "', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override="
        "False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='heade"
        "rs', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, overrid"
        "e=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='pay"
        "load', annotation=OpRef(name='init.fields.3.annotation'), default=None, default_factory=None, init=True, overr"
        "ide=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='r"
        "equest', annotation=OpRef(name='init.fields.4.annotation'), default=None, default_factory=None, init=True, ove"
        "rride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', "
        "std_params=(), kw_only_params=('invocation_index', 'url', 'headers', 'payload', 'request'), frozen=True, slots"
        "=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='invocation"
        "_index', kw_only=True, fn=None), ReprPlan.Field(name='url', kw_only=True, fn=None), ReprPlan.Field(name='heade"
        "rs', kw_only=True, fn=None), ReprPlan.Field(name='payload', kw_only=True, fn=None)), id=False, terse=False, de"
        "fault_fn=None)))"
    ),
    plan_repr_sha1='8bfec5afdb1e62f2af91cb224a06e5389f0c82b1',
    cls_names=(
        ('omllm.llm.backends.scripted.http', 'RecordedHttpRequest'),
    ),
)
def _process_dataclass__8bfec5afdb1e62f2af91cb224a06e5389f0c82b1():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__4__annotation,
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
                invocation_index=self.invocation_index,
                url=self.url,
                headers=self.headers,
                payload=self.payload,
                request=self.request,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.invocation_index == other.invocation_index and
                self.url == other.url and
                self.headers == other.headers and
                self.payload == other.payload and
                self.request == other.request
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'invocation_index',
            'url',
            'headers',
            'payload',
            'request',
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
                self.invocation_index,
                self.url,
                self.headers,
                self.payload,
                self.request,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            invocation_index: __dataclass__init__fields__0__annotation,
            url: __dataclass__init__fields__1__annotation,
            headers: __dataclass__init__fields__2__annotation,
            payload: __dataclass__init__fields__3__annotation,
            request: __dataclass__init__fields__4__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'invocation_index', invocation_index)
            __dataclass__object_setattr(self, 'url', url)
            __dataclass__object_setattr(self, 'headers', headers)
            __dataclass__object_setattr(self, 'payload', payload)
            __dataclass__object_setattr(self, 'request', request)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"invocation_index={self.invocation_index!r}")
            parts.append(f"url={self.url!r}")
            parts.append(f"headers={self.headers!r}")
            parts.append(f"payload={self.payload!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('status', 'error_type', 'message', 'body')), EqPlan(fields=('status', 'error_type'"
        ", 'message', 'body')), FrozenPlan(fields=('status', 'error_type', 'message', 'body'), allow_dynamic_dunder_att"
        "rs=False), HashPlan(action='add', fields=('status', 'error_type', 'message', 'body'), cache=False), InitPlan(f"
        "ields=(InitPlan.Field(name='status', annotation=OpRef(name='init.fields.0.annotation'), default=OpRef(name='in"
        "it.fields.0.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce="
        "None, validate=None, check_type=None), InitPlan.Field(name='error_type', annotation=OpRef(name='init.fields.1."
        "annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False, fi"
        "eld_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='message', anno"
        "tation=OpRef(name='init.fields.2.annotation'), default=OpRef(name='init.fields.2.default'), default_factory=No"
        "ne, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), In"
        "itPlan.Field(name='body', annotation=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.fields.3"
        ".default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, valid"
        "ate=None, check_type=None)), self_param='self', std_params=(), kw_only_params=('status', 'error_type', 'messag"
        "e', 'body'), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=("
        "ReprPlan.Field(name='status', kw_only=True, fn=None), ReprPlan.Field(name='error_type', kw_only=True, fn=None)"
        ", ReprPlan.Field(name='message', kw_only=True, fn=None), ReprPlan.Field(name='body', kw_only=True, fn=None)), "
        "id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='52c85f3b0b204b19f682f473cb0f0b46cecb07ea',
    cls_names=(
        ('omllm.llm.backends.scripted.http', 'ScriptedHttpError'),
    ),
)
def _process_dataclass__52c85f3b0b204b19f682f473cb0f0b46cecb07ea():
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
                status=self.status,
                error_type=self.error_type,
                message=self.message,
                body=self.body,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.status == other.status and
                self.error_type == other.error_type and
                self.message == other.message and
                self.body == other.body
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'status',
            'error_type',
            'message',
            'body',
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
                self.status,
                self.error_type,
                self.message,
                self.body,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            status: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            error_type: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            message: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            body: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'status', status)
            __dataclass__object_setattr(self, 'error_type', error_type)
            __dataclass__object_setattr(self, 'message', message)
            __dataclass__object_setattr(self, 'body', body)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"status={self.status!r}")
            parts.append(f"error_type={self.error_type!r}")
            parts.append(f"message={self.message!r}")
            parts.append(f"body={self.body!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('error',)), EqPlan(fields=('error',)), FrozenPlan(fields=('error',), allow_dynamic"
        "_dunder_attrs=False), HashPlan(action='add', fields=('error',), cache=False), InitPlan(fields=(InitPlan.Field("
        "name='error', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True"
        ", override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='s"
        "elf', std_params=(), kw_only_params=('error',), frozen=True, slots=False, post_init_params=None, init_fns=(), "
        "validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='error', kw_only=True, fn=None),), id=False, terse=Fals"
        "e, default_fn=None)))"
    ),
    plan_repr_sha1='8e3102c34a8353555bb37d1cb52be4aede648133',
    cls_names=(
        ('omllm.llm.backends.scripted.http', 'ScriptedHttpException'),
    ),
)
def _process_dataclass__8e3102c34a8353555bb37d1cb52be4aede648133():
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
                error=self.error,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.error == other.error
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
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
                self.error,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            error: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'error', error)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"error={self.error!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('invocation_index', 'chunk_index')), EqPlan(fields=('invocation_index', 'chunk_ind"
        "ex')), FrozenPlan(fields=('invocation_index', 'chunk_index'), allow_dynamic_dunder_attrs=False), HashPlan(acti"
        "on='add', fields=('invocation_index', 'chunk_index'), cache=False), InitPlan(fields=(InitPlan.Field(name='invo"
        "cation_index', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=Tru"
        "e, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field"
        "(name='chunk_index', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, in"
        "it=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_pa"
        "ram='self', std_params=(), kw_only_params=('invocation_index', 'chunk_index'), frozen=True, slots=False, post_"
        "init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='invocation_index', kw_o"
        "nly=True, fn=None), ReprPlan.Field(name='chunk_index', kw_only=True, fn=None)), id=False, terse=False, default"
        "_fn=None)))"
    ),
    plan_repr_sha1='9a19ea77899fe30cb68f4092977361881227e768',
    cls_names=(
        ('omllm.llm.backends.scripted.http', 'ScriptedHttpGatePoint'),
    ),
)
def _process_dataclass__9a19ea77899fe30cb68f4092977361881227e768():
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
                invocation_index=self.invocation_index,
                chunk_index=self.chunk_index,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.invocation_index == other.invocation_index and
                self.chunk_index == other.chunk_index
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'invocation_index',
            'chunk_index',
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
                self.invocation_index,
                self.chunk_index,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            invocation_index: __dataclass__init__fields__0__annotation,
            chunk_index: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'invocation_index', invocation_index)
            __dataclass__object_setattr(self, 'chunk_index', chunk_index)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"invocation_index={self.invocation_index!r}")
            parts.append(f"chunk_index={self.chunk_index!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('body', 'status', 'headers', 'byte_chunk_size')), EqPlan(fields=('body', 'status',"
        " 'headers', 'byte_chunk_size')), FrozenPlan(fields=('body', 'status', 'headers', 'byte_chunk_size'), allow_dyn"
        "amic_dunder_attrs=False), HashPlan(action='add', fields=('body', 'status', 'headers', 'byte_chunk_size'), cach"
        "e=False), InitPlan(fields=(InitPlan.Field(name='body', annotation=OpRef(name='init.fields.0.annotation'), defa"
        "ult=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validat"
        "e=None, check_type=None), InitPlan.Field(name='status', annotation=OpRef(name='init.fields.1.annotation'), def"
        "ault=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False, field_type=FieldTyp"
        "e.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='headers', annotation=OpRef(name"
        "='init.fields.2.annotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, ov"
        "erride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name"
        "='byte_chunk_size', annotation=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.fields.3.defau"
        "lt'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=No"
        "ne, check_type=None)), self_param='self', std_params=(), kw_only_params=('body', 'status', 'headers', 'byte_ch"
        "unk_size'), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(R"
        "eprPlan.Field(name='body', kw_only=True, fn=None), ReprPlan.Field(name='status', kw_only=True, fn=None), ReprP"
        "lan.Field(name='headers', kw_only=True, fn=None), ReprPlan.Field(name='byte_chunk_size', kw_only=True, fn=None"
        ")), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='ff00c840a9e0b24f0eca59c68d32dba54eefecd4',
    cls_names=(
        ('omllm.llm.backends.scripted.http', 'ScriptedHttpRawResponse'),
        ('omllm.llm.backends.scripted.http', 'ScriptedRenderedHttpResponse'),
    ),
)
def _process_dataclass__ff00c840a9e0b24f0eca59c68d32dba54eefecd4():
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
                body=self.body,
                status=self.status,
                headers=self.headers,
                byte_chunk_size=self.byte_chunk_size,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.body == other.body and
                self.status == other.status and
                self.headers == other.headers and
                self.byte_chunk_size == other.byte_chunk_size
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'body',
            'status',
            'headers',
            'byte_chunk_size',
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
                self.body,
                self.status,
                self.headers,
                self.byte_chunk_size,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            body: __dataclass__init__fields__0__annotation,
            status: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            headers: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            byte_chunk_size: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'body', body)
            __dataclass__object_setattr(self, 'status', status)
            __dataclass__object_setattr(self, 'headers', headers)
            __dataclass__object_setattr(self, 'byte_chunk_size', byte_chunk_size)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"body={self.body!r}")
            parts.append(f"status={self.status!r}")
            parts.append(f"headers={self.headers!r}")
            parts.append(f"byte_chunk_size={self.byte_chunk_size!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('content', 'stop_reason', 'usage', 'response_id', 'model', 'chunk_chars')), EqPlan"
        "(fields=('content', 'stop_reason', 'usage', 'response_id', 'model', 'chunk_chars')), FrozenPlan(fields=('conte"
        "nt', 'stop_reason', 'usage', 'response_id', 'model', 'chunk_chars'), allow_dynamic_dunder_attrs=False), HashPl"
        "an(action='add', fields=('content', 'stop_reason', 'usage', 'response_id', 'model', 'chunk_chars'), cache=Fals"
        "e), InitPlan(fields=(InitPlan.Field(name='content', annotation=OpRef(name='init.fields.0.annotation'), default"
        "=OpRef(name='init.fields.0.default'), default_factory=None, init=True, override=False, field_type=FieldType.IN"
        "STANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='stop_reason', annotation=OpRef(name"
        "='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, ov"
        "erride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name"
        "='usage', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=OpRef(name='init.fi"
        "elds.2.default_factory'), init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None"
        ", check_type=None), InitPlan.Field(name='response_id', annotation=OpRef(name='init.fields.3.annotation'), defa"
        "ult=OpRef(name='init.fields.3.default'), default_factory=None, init=True, override=False, field_type=FieldType"
        ".INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='model', annotation=OpRef(name='i"
        "nit.fields.4.annotation'), default=OpRef(name='init.fields.4.default'), default_factory=None, init=True, overr"
        "ide=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='c"
        "hunk_chars', annotation=OpRef(name='init.fields.5.annotation'), default=OpRef(name='init.fields.5.default'), d"
        "efault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, che"
        "ck_type=None)), self_param='self', std_params=(), kw_only_params=('content', 'stop_reason', 'usage', 'response"
        "_id', 'model', 'chunk_chars'), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()),"
        " ReprPlan(fields=(ReprPlan.Field(name='content', kw_only=True, fn=None), ReprPlan.Field(name='stop_reason', kw"
        "_only=True, fn=None), ReprPlan.Field(name='usage', kw_only=True, fn=None), ReprPlan.Field(name='response_id', "
        "kw_only=True, fn=None), ReprPlan.Field(name='model', kw_only=True, fn=None), ReprPlan.Field(name='chunk_chars'"
        ", kw_only=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='ef6add4d1b67b1a2721339e76179651d43fe2e67',
    cls_names=(
        ('omllm.llm.backends.scripted.http', 'ScriptedHttpResponse'),
    ),
)
def _process_dataclass__ef6add4d1b67b1a2721339e76179651d43fe2e67():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__default,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default_factory,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__3__default,
        __dataclass__init__fields__4__annotation,
        __dataclass__init__fields__4__default,
        __dataclass__init__fields__5__annotation,
        __dataclass__init__fields__5__default,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__HAS_DEFAULT_FACTORY=dataclasses._HAS_DEFAULT_FACTORY,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__object_setattr=object.__setattr__,  # noqa
        __dataclass__set_cls_attr,
    ):
        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                content=self.content,
                stop_reason=self.stop_reason,
                usage=self.usage,
                response_id=self.response_id,
                model=self.model,
                chunk_chars=self.chunk_chars,
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
                self.usage == other.usage and
                self.response_id == other.response_id and
                self.model == other.model and
                self.chunk_chars == other.chunk_chars
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'content',
            'stop_reason',
            'usage',
            'response_id',
            'model',
            'chunk_chars',
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
                self.content,
                self.stop_reason,
                self.usage,
                self.response_id,
                self.model,
                self.chunk_chars,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            content: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            stop_reason: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            usage: __dataclass__init__fields__2__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            response_id: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            model: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            chunk_chars: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            if usage is __dataclass__HAS_DEFAULT_FACTORY:
                usage = __dataclass__init__fields__2__default_factory()
            __dataclass__object_setattr(self, 'content', content)
            __dataclass__object_setattr(self, 'stop_reason', stop_reason)
            __dataclass__object_setattr(self, 'usage', usage)
            __dataclass__object_setattr(self, 'response_id', response_id)
            __dataclass__object_setattr(self, 'model', model)
            __dataclass__object_setattr(self, 'chunk_chars', chunk_chars)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"content={self.content!r}")
            parts.append(f"stop_reason={self.stop_reason!r}")
            parts.append(f"usage={self.usage!r}")
            parts.append(f"response_id={self.response_id!r}")
            parts.append(f"model={self.model!r}")
            parts.append(f"chunk_chars={self.chunk_chars!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('result', 'expect')), EqPlan(fields=('result', 'expect')), FrozenPlan(fields=('res"
        "ult', 'expect'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('result', 'expect'), cache="
        "False), InitPlan(fields=(InitPlan.Field(name='result', annotation=OpRef(name='init.fields.0.annotation'), defa"
        "ult=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validat"
        "e=None, check_type=None), InitPlan.Field(name='expect', annotation=OpRef(name='init.fields.1.annotation'), def"
        "ault=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False, field_type=FieldTyp"
        "e.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=(), kw_only_params=('"
        "result', 'expect'), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(f"
        "ields=(ReprPlan.Field(name='result', kw_only=True, fn=None),), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='f3ae3e411939198cb44490026a2b5c359a77f03c',
    cls_names=(
        ('omllm.llm.backends.scripted.http', 'ScriptedHttpTurn'),
    ),
)
def _process_dataclass__f3ae3e411939198cb44490026a2b5c359a77f03c():
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
                result=self.result,
                expect=self.expect,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.result == other.result and
                self.expect == other.expect
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'result',
            'expect',
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
                self.result,
                self.expect,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            result: __dataclass__init__fields__0__annotation,
            expect: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'result', result)
            __dataclass__object_setattr(self, 'expect', expect)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"result={self.result!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('status', 'error_type', 'message')), EqPlan(fields=('status', 'error_type', 'messa"
        "ge')), FrozenPlan(fields=('status', 'error_type', 'message'), allow_dynamic_dunder_attrs=False), HashPlan(acti"
        "on='add', fields=('status', 'error_type', 'message'), cache=False), InitPlan(fields=(InitPlan.Field(name='stat"
        "us', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, overrid"
        "e=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='err"
        "or_type', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, ov"
        "erride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name"
        "='message', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, "
        "override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self"
        "', std_params=(), kw_only_params=('status', 'error_type', 'message'), frozen=True, slots=False, post_init_para"
        "ms=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='status', kw_only=True, fn=None),"
        " ReprPlan.Field(name='error_type', kw_only=True, fn=None), ReprPlan.Field(name='message', kw_only=True, fn=Non"
        "e)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='1470811756ade0e2d8bb587c1531500c1899fd0d',
    cls_names=(
        ('omllm.llm.backends.scripted.http', 'ScriptedHttpValidationError'),
    ),
)
def _process_dataclass__1470811756ade0e2d8bb587c1531500c1899fd0d():
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
                status=self.status,
                error_type=self.error_type,
                message=self.message,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.status == other.status and
                self.error_type == other.error_type and
                self.message == other.message
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'status',
            'error_type',
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
                self.status,
                self.error_type,
                self.message,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            status: __dataclass__init__fields__0__annotation,
            error_type: __dataclass__init__fields__1__annotation,
            message: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'status', status)
            __dataclass__object_setattr(self, 'error_type', error_type)
            __dataclass__object_setattr(self, 'message', message)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"status={self.status!r}")
            parts.append(f"error_type={self.error_type!r}")
            parts.append(f"message={self.message!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('uncached_input_tokens', 'output_tokens', 'reasoning_tokens', 'cache_read_tokens',"
        " 'cache_write_tokens', 'total_tokens')), EqPlan(fields=('uncached_input_tokens', 'output_tokens', 'reasoning_t"
        "okens', 'cache_read_tokens', 'cache_write_tokens', 'total_tokens')), FrozenPlan(fields=('uncached_input_tokens"
        "', 'output_tokens', 'reasoning_tokens', 'cache_read_tokens', 'cache_write_tokens', 'total_tokens'), allow_dyna"
        "mic_dunder_attrs=False), HashPlan(action='add', fields=('uncached_input_tokens', 'output_tokens', 'reasoning_t"
        "okens', 'cache_read_tokens', 'cache_write_tokens', 'total_tokens'), cache=False), InitPlan(fields=(InitPlan.Fi"
        "eld(name='uncached_input_tokens', annotation=OpRef(name='init.fields.0.annotation'), default=OpRef(name='init."
        "fields.0.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=Non"
        "e, validate=None, check_type=None), InitPlan.Field(name='output_tokens', annotation=OpRef(name='init.fields.1."
        "annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False, fi"
        "eld_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='reasoning_toke"
        "ns', annotation=OpRef(name='init.fields.2.annotation'), default=OpRef(name='init.fields.2.default'), default_f"
        "actory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type="
        "None), InitPlan.Field(name='cache_read_tokens', annotation=OpRef(name='init.fields.3.annotation'), default=OpR"
        "ef(name='init.fields.3.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTAN"
        "CE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='cache_write_tokens', annotation=OpRef(n"
        "ame='init.fields.4.annotation'), default=OpRef(name='init.fields.4.default'), default_factory=None, init=True,"
        " override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(n"
        "ame='total_tokens', annotation=OpRef(name='init.fields.5.annotation'), default=OpRef(name='init.fields.5.defau"
        "lt'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=No"
        "ne, check_type=None)), self_param='self', std_params=(), kw_only_params=('uncached_input_tokens', 'output_toke"
        "ns', 'reasoning_tokens', 'cache_read_tokens', 'cache_write_tokens', 'total_tokens'), frozen=True, slots=False,"
        " post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='uncached_input_to"
        "kens', kw_only=True, fn=None), ReprPlan.Field(name='output_tokens', kw_only=True, fn=None), ReprPlan.Field(nam"
        "e='reasoning_tokens', kw_only=True, fn=None), ReprPlan.Field(name='cache_read_tokens', kw_only=True, fn=None),"
        " ReprPlan.Field(name='cache_write_tokens', kw_only=True, fn=None), ReprPlan.Field(name='total_tokens', kw_only"
        "=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='1b09836376b94a3e047c25922d8ba72bb28bd5d8',
    cls_names=(
        ('omllm.llm.backends.scripted.http', 'ScriptedUsage'),
    ),
)
def _process_dataclass__1b09836376b94a3e047c25922d8ba72bb28bd5d8():
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
                uncached_input_tokens=self.uncached_input_tokens,
                output_tokens=self.output_tokens,
                reasoning_tokens=self.reasoning_tokens,
                cache_read_tokens=self.cache_read_tokens,
                cache_write_tokens=self.cache_write_tokens,
                total_tokens=self.total_tokens,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.uncached_input_tokens == other.uncached_input_tokens and
                self.output_tokens == other.output_tokens and
                self.reasoning_tokens == other.reasoning_tokens and
                self.cache_read_tokens == other.cache_read_tokens and
                self.cache_write_tokens == other.cache_write_tokens and
                self.total_tokens == other.total_tokens
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'uncached_input_tokens',
            'output_tokens',
            'reasoning_tokens',
            'cache_read_tokens',
            'cache_write_tokens',
            'total_tokens',
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
                self.uncached_input_tokens,
                self.output_tokens,
                self.reasoning_tokens,
                self.cache_read_tokens,
                self.cache_write_tokens,
                self.total_tokens,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            uncached_input_tokens: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            output_tokens: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            reasoning_tokens: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            cache_read_tokens: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            cache_write_tokens: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            total_tokens: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'uncached_input_tokens', uncached_input_tokens)
            __dataclass__object_setattr(self, 'output_tokens', output_tokens)
            __dataclass__object_setattr(self, 'reasoning_tokens', reasoning_tokens)
            __dataclass__object_setattr(self, 'cache_read_tokens', cache_read_tokens)
            __dataclass__object_setattr(self, 'cache_write_tokens', cache_write_tokens)
            __dataclass__object_setattr(self, 'total_tokens', total_tokens)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"uncached_input_tokens={self.uncached_input_tokens!r}")
            parts.append(f"output_tokens={self.output_tokens!r}")
            parts.append(f"reasoning_tokens={self.reasoning_tokens!r}")
            parts.append(f"cache_read_tokens={self.cache_read_tokens!r}")
            parts.append(f"cache_write_tokens={self.cache_write_tokens!r}")
            parts.append(f"total_tokens={self.total_tokens!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('turns', 'on_exhausted', 'gate')), EqPlan(fields=('turns', 'on_exhausted', 'gate')"
        "), FrozenPlan(fields=('turns', 'on_exhausted', 'gate'), allow_dynamic_dunder_attrs=False), HashPlan(action='ad"
        "d', fields=('turns', 'on_exhausted', 'gate'), cache=False), InitPlan(fields=(InitPlan.Field(name='turns', anno"
        "tation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, "
        "field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='on_exhausted"
        "', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_fac"
        "tory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=No"
        "ne), InitPlan.Field(name='gate', annotation=OpRef(name='init.fields.2.annotation'), default=OpRef(name='init.f"
        "ields.2.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None"
        ", validate=None, check_type=None)), self_param='self', std_params=('turns',), kw_only_params=('on_exhausted', "
        "'gate'), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(Repr"
        "Plan.Field(name='turns', kw_only=False, fn=None), ReprPlan.Field(name='on_exhausted', kw_only=True, fn=None)),"
        " id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='02f84fcd12deb6df8995d076ef13a04d4bf96d30',
    cls_names=(
        ('omllm.llm.backends.scripted.scripts', 'BackendScript'),
    ),
)
def _process_dataclass__02f84fcd12deb6df8995d076ef13a04d4bf96d30():
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
                turns=self.turns,
                on_exhausted=self.on_exhausted,
                gate=self.gate,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.turns == other.turns and
                self.on_exhausted == other.on_exhausted and
                self.gate == other.gate
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'turns',
            'on_exhausted',
            'gate',
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
                self.turns,
                self.on_exhausted,
                self.gate,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            turns: __dataclass__init__fields__0__annotation,
            *,
            on_exhausted: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            gate: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'turns', turns)
            __dataclass__object_setattr(self, 'on_exhausted', on_exhausted)
            __dataclass__object_setattr(self, 'gate', gate)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"turns={self.turns!r}")
            parts.append(f"on_exhausted={self.on_exhausted!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('invocation_index', 'emission_index')), EqPlan(fields=('invocation_index', 'emissi"
        "on_index')), FrozenPlan(fields=('invocation_index', 'emission_index'), allow_dynamic_dunder_attrs=False), Hash"
        "Plan(action='add', fields=('invocation_index', 'emission_index'), cache=False), InitPlan(fields=(InitPlan.Fiel"
        "d(name='invocation_index', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=No"
        "ne, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), In"
        "itPlan.Field(name='emission_index', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_f"
        "actory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type="
        "None)), self_param='self', std_params=(), kw_only_params=('invocation_index', 'emission_index'), frozen=True, "
        "slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='invoc"
        "ation_index', kw_only=True, fn=None), ReprPlan.Field(name='emission_index', kw_only=True, fn=None)), id=False,"
        " terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='b5bc3c99353f0757f5ac59c5c1b82a17728260e9',
    cls_names=(
        ('omllm.llm.backends.scripted.scripts', 'BackendScriptGatePoint'),
    ),
)
def _process_dataclass__b5bc3c99353f0757f5ac59c5c1b82a17728260e9():
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
                invocation_index=self.invocation_index,
                emission_index=self.emission_index,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.invocation_index == other.invocation_index and
                self.emission_index == other.emission_index
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'invocation_index',
            'emission_index',
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
                self.invocation_index,
                self.emission_index,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            invocation_index: __dataclass__init__fields__0__annotation,
            emission_index: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'invocation_index', invocation_index)
            __dataclass__object_setattr(self, 'emission_index', emission_index)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"invocation_index={self.invocation_index!r}")
            parts.append(f"emission_index={self.emission_index!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('invocation_index', 'context', 'options')), EqPlan(fields=('invocation_index', 'co"
        "ntext', 'options')), FrozenPlan(fields=('invocation_index', 'context', 'options'), allow_dynamic_dunder_attrs="
        "False), HashPlan(action='add', fields=('invocation_index', 'context', 'options'), cache=False), InitPlan(field"
        "s=(InitPlan.Field(name='invocation_index', annotation=OpRef(name='init.fields.0.annotation'), default=None, de"
        "fault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, chec"
        "k_type=None), InitPlan.Field(name='context', annotation=OpRef(name='init.fields.1.annotation'), default=None, "
        "default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, ch"
        "eck_type=None), InitPlan.Field(name='options', annotation=OpRef(name='init.fields.2.annotation'), default=None"
        ", default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, "
        "check_type=None)), self_param='self', std_params=(), kw_only_params=('invocation_index', 'context', 'options')"
        ", frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Fi"
        "eld(name='invocation_index', kw_only=True, fn=None), ReprPlan.Field(name='context', kw_only=True, fn=None), Re"
        "prPlan.Field(name='options', kw_only=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='348e5aaf8f4c095049932b594f0938f813cf7dd0',
    cls_names=(
        ('omllm.llm.backends.scripted.scripts', 'BackendScriptInvocation'),
    ),
)
def _process_dataclass__348e5aaf8f4c095049932b594f0938f813cf7dd0():
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
                invocation_index=self.invocation_index,
                context=self.context,
                options=self.options,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.invocation_index == other.invocation_index and
                self.context == other.context and
                self.options == other.options
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'invocation_index',
            'context',
            'options',
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
                self.invocation_index,
                self.context,
                self.options,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            invocation_index: __dataclass__init__fields__0__annotation,
            context: __dataclass__init__fields__1__annotation,
            options: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'invocation_index', invocation_index)
            __dataclass__object_setattr(self, 'context', context)
            __dataclass__object_setattr(self, 'options', options)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"invocation_index={self.invocation_index!r}")
            parts.append(f"context={self.context!r}")
            parts.append(f"options={self.options!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('message', 'error', 'chunk_size', 'expect')), EqPlan(fields=('message', 'error', '"
        "chunk_size', 'expect')), FrozenPlan(fields=('message', 'error', 'chunk_size', 'expect'), allow_dynamic_dunder_"
        "attrs=False), HashPlan(action='add', fields=('message', 'error', 'chunk_size', 'expect'), cache=False), InitPl"
        "an(fields=(InitPlan.Field(name='message', annotation=OpRef(name='init.fields.0.annotation'), default=OpRef(nam"
        "e='init.fields.0.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, co"
        "erce=None, validate=None, check_type=None), InitPlan.Field(name='error', annotation=OpRef(name='init.fields.1."
        "annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False, fi"
        "eld_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='chunk_size', a"
        "nnotation=OpRef(name='init.fields.2.annotation'), default=OpRef(name='init.fields.2.default'), default_factory"
        "=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),"
        " InitPlan.Field(name='expect', annotation=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.fie"
        "lds.3.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, "
        "validate=None, check_type=None)), self_param='self', std_params=('message',), kw_only_params=('error', 'chunk_"
        "size', 'expect'), frozen=True, slots=False, post_init_params=(), init_fns=(), validate_fns=()), ReprPlan(field"
        "s=(ReprPlan.Field(name='message', kw_only=False, fn=None), ReprPlan.Field(name='chunk_size', kw_only=True, fn="
        "None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='5855412b24a357a8582cac1ab84bf086324797ed',
    cls_names=(
        ('omllm.llm.backends.scripted.scripts', 'BackendScriptTurn'),
    ),
)
def _process_dataclass__5855412b24a357a8582cac1ab84bf086324797ed():
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
                message=self.message,
                error=self.error,
                chunk_size=self.chunk_size,
                expect=self.expect,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.message == other.message and
                self.error == other.error and
                self.chunk_size == other.chunk_size and
                self.expect == other.expect
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'message',
            'error',
            'chunk_size',
            'expect',
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
                self.message,
                self.error,
                self.chunk_size,
                self.expect,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            message: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            *,
            error: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            chunk_size: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            expect: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'message', message)
            __dataclass__object_setattr(self, 'error', error)
            __dataclass__object_setattr(self, 'chunk_size', chunk_size)
            __dataclass__object_setattr(self, 'expect', expect)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"message={self.message!r}")
            parts.append(f"chunk_size={self.chunk_size!r}")
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
        ('omllm.llm.types.compat', 'Compat'),
        ('omllm.llm.types.content', 'Content'),
        ('omllm.llm.types.messages', 'Message'),
        ('omllm.llm.types.streams', 'AiStreamEvent'),
        ('omllm.llm.types.streams', 'StreamEndAiStreamEvent'),
        ('omllm.llm.types.streams', 'StreamStartAiStreamEvent'),
        ('omllm.llm.types.tools', 'ToolDtype'),
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
        "Plans(tup=(CopyPlan(fields=('url_path', 'max_tokens_field', 'reasoning_field', 'cost_mode')), EqPlan(fields=('"
        "url_path', 'max_tokens_field', 'reasoning_field', 'cost_mode')), FrozenPlan(fields=('url_path', 'max_tokens_fi"
        "eld', 'reasoning_field', 'cost_mode'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('url_"
        "path', 'max_tokens_field', 'reasoning_field', 'cost_mode'), cache=False), InitPlan(fields=(InitPlan.Field(name"
        "='url_path', annotation=OpRef(name='init.fields.0.annotation'), default=OpRef(name='init.fields.0.default'), d"
        "efault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, che"
        "ck_type=None), InitPlan.Field(name='max_tokens_field', annotation=OpRef(name='init.fields.1.annotation'), defa"
        "ult=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False, field_type=FieldType"
        ".INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='reasoning_field', annotation=OpR"
        "ef(name='init.fields.2.annotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=T"
        "rue, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Fie"
        "ld(name='cost_mode', annotation=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.fields.3.defa"
        "ult'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=N"
        "one, check_type=None)), self_param='self', std_params=(), kw_only_params=('url_path', 'max_tokens_field', 'rea"
        "soning_field', 'cost_mode'), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), R"
        "eprPlan(fields=(ReprPlan.Field(name='url_path', kw_only=True, fn=None), ReprPlan.Field(name='max_tokens_field'"
        ", kw_only=True, fn=None), ReprPlan.Field(name='reasoning_field', kw_only=True, fn=None), ReprPlan.Field(name='"
        "cost_mode', kw_only=True, fn=None)), id=False, terse=False, default_fn=OpRef(name='repr.default_fn'))))"
    ),
    plan_repr_sha1='8af31b6054998dd4ccb2219abb4f0e8df90d62fa',
    cls_names=(
        ('omllm.llm.types.compat', 'OpenaiCompat'),
    ),
)
def _process_dataclass__8af31b6054998dd4ccb2219abb4f0e8df90d62fa():
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
        __dataclass__repr__default_fn,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('url_path',)), EqPlan(fields=('url_path',)), FrozenPlan(fields=('url_path',), allo"
        "w_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('url_path',), cache=False), InitPlan(fields=(Ini"
        "tPlan.Field(name='url_path', annotation=OpRef(name='init.fields.0.annotation'), default=OpRef(name='init.field"
        "s.0.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, va"
        "lidate=None, check_type=None),), self_param='self', std_params=(), kw_only_params=('url_path',), frozen=True, "
        "slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='url_p"
        "ath', kw_only=True, fn=None),), id=False, terse=False, default_fn=OpRef(name='repr.default_fn'))))"
    ),
    plan_repr_sha1='d0f647a82e689876f62ad2bb03d2c36faa264ac9',
    cls_names=(
        ('omllm.llm.types.compat', 'OpenaiResponsesCompat'),
    ),
)
def _process_dataclass__d0f647a82e689876f62ad2bb03d2c36faa264ac9():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__default,
        __dataclass__repr__default_fn,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('text', 'backend_signature')), EqPlan(fields=('text', 'backend_signature')), Froze"
        "nPlan(fields=('text', 'backend_signature'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=("
        "'text', 'backend_signature'), cache=True), InitPlan(fields=(InitPlan.Field(name='text', annotation=OpRef(name="
        "'init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldTy"
        "pe.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='backend_signature', annotation"
        "=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, in"
        "it=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_pa"
        "ram='self', std_params=('text',), kw_only_params=('backend_signature',), frozen=True, slots=False, post_init_p"
        "arams=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='text', kw_only=False, fn=None"
        "), ReprPlan.Field(name='backend_signature', kw_only=True, fn=None)), id=False, terse=True, default_fn=OpRef(na"
        "me='repr.default_fn'))))"
    ),
    plan_repr_sha1='a65a2e4a2f335305689f0fb4917863975614542a',
    cls_names=(
        ('omllm.llm.types.content', 'TextContent'),
    ),
)
def _process_dataclass__a65a2e4a2f335305689f0fb4917863975614542a():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
        __dataclass__repr__default_fn,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('text', 'backend_signature', 'redacted')), EqPlan(fields=('text', 'backend_signatu"
        "re', 'redacted')), FrozenPlan(fields=('text', 'backend_signature', 'redacted'), allow_dynamic_dunder_attrs=Fal"
        "se), HashPlan(action='add', fields=('text', 'backend_signature', 'redacted'), cache=True), InitPlan(fields=(In"
        "itPlan.Field(name='text', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=Non"
        "e, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), Ini"
        "tPlan.Field(name='backend_signature', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='i"
        "nit.fields.1.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce"
        "=None, validate=None, check_type=None), InitPlan.Field(name='redacted', annotation=OpRef(name='init.fields.2.a"
        "nnotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, override=False, fie"
        "ld_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('tex"
        "t',), kw_only_params=('backend_signature', 'redacted'), frozen=True, slots=False, post_init_params=None, init_"
        "fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='text', kw_only=False, fn=None), ReprPlan.Field"
        "(name='backend_signature', kw_only=True, fn=None), ReprPlan.Field(name='redacted', kw_only=True, fn=None)), id"
        "=False, terse=True, default_fn=OpRef(name='repr.default_fn'))))"
    ),
    plan_repr_sha1='142f52fd3fd83101d3bdbde37c68a98ac4bf17d9',
    cls_names=(
        ('omllm.llm.types.content', 'ThinkingContent'),
    ),
)
def _process_dataclass__142f52fd3fd83101d3bdbde37c68a98ac4bf17d9():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default,
        __dataclass__repr__default_fn,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('id', 'name', 'args', 'backend_signature')), EqPlan(fields=('id', 'name', 'args', "
        "'backend_signature')), FrozenPlan(fields=('id', 'name', 'args', 'backend_signature'), allow_dynamic_dunder_att"
        "rs=False), HashPlan(action='add', fields=('id', 'name', 'args', 'backend_signature'), cache=True), InitPlan(fi"
        "elds=(InitPlan.Field(name='id', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_facto"
        "ry=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None"
        "), InitPlan.Field(name='name', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factor"
        "y=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)"
        ", InitPlan.Field(name='args', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory"
        "=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),"
        " InitPlan.Field(name='backend_signature', annotation=OpRef(name='init.fields.3.annotation'), default=OpRef(nam"
        "e='init.fields.3.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, co"
        "erce=None, validate=None, check_type=None)), self_param='self', std_params=('id', 'name', 'args'), kw_only_par"
        "ams=('backend_signature',), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), Re"
        "prPlan(fields=(ReprPlan.Field(name='id', kw_only=False, fn=None), ReprPlan.Field(name='name', kw_only=False, f"
        "n=None), ReprPlan.Field(name='args', kw_only=False, fn=None), ReprPlan.Field(name='backend_signature', kw_only"
        "=True, fn=None)), id=False, terse=False, default_fn=OpRef(name='repr.default_fn'))))"
    ),
    plan_repr_sha1='e6d183fbcbea3434f6346c3c22c12e38c1980ac1',
    cls_names=(
        ('omllm.llm.types.content', 'ToolCall'),
    ),
)
def _process_dataclass__e6d183fbcbea3434f6346c3c22c12e38c1980ac1():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__3__default,
        __dataclass__repr__default_fn,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('system_prompt', 'messages', 'tools')), EqPlan(fields=('system_prompt', 'messages'"
        ", 'tools')), FrozenPlan(fields=('system_prompt', 'messages', 'tools'), allow_dynamic_dunder_attrs=False), Hash"
        "Plan(action='add', fields=('system_prompt', 'messages', 'tools'), cache=False), InitPlan(fields=(InitPlan.Fiel"
        "d(name='system_prompt', annotation=OpRef(name='init.fields.0.annotation'), default=OpRef(name='init.fields.0.d"
        "efault'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validat"
        "e=None, check_type=None), InitPlan.Field(name='messages', annotation=OpRef(name='init.fields.1.annotation'), d"
        "efault=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False, field_type=FieldT"
        "ype.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='tools', annotation=OpRef(name"
        "='init.fields.2.annotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, ov"
        "erride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self',"
        " std_params=(), kw_only_params=('system_prompt', 'messages', 'tools'), frozen=True, slots=False, post_init_par"
        "ams=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='system_prompt', kw_only=True, f"
        "n=None), ReprPlan.Field(name='messages', kw_only=True, fn=None), ReprPlan.Field(name='tools', kw_only=True, fn"
        "=None)), id=False, terse=False, default_fn=OpRef(name='repr.default_fn'))))"
    ),
    plan_repr_sha1='6bddc86ea07270ffb6ce8028c896f9175ddeb8ec',
    cls_names=(
        ('omllm.llm.types.context', 'Context'),
    ),
)
def _process_dataclass__6bddc86ea07270ffb6ce8028c896f9175ddeb8ec():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__default,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default,
        __dataclass__repr__default_fn,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('content', 'stop_reason', 'token_usage')), EqPlan(fields=('content', 'stop_reason'"
        ", 'token_usage')), FrozenPlan(fields=('content', 'stop_reason', 'token_usage'), allow_dynamic_dunder_attrs=Fal"
        "se), HashPlan(action='add', fields=('content', 'stop_reason', 'token_usage'), cache=True), InitPlan(fields=(In"
        "itPlan.Field(name='content', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory="
        "None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), "
        "InitPlan.Field(name='stop_reason', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init"
        ".fields.1.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=No"
        "ne, validate=None, check_type=None), InitPlan.Field(name='token_usage', annotation=OpRef(name='init.fields.2.a"
        "nnotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, override=False, fie"
        "ld_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('con"
        "tent', 'stop_reason', 'token_usage'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init"
        "_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='content', kw_only=False, fn=None), ReprPlan.F"
        "ield(name='stop_reason', kw_only=False, fn=None), ReprPlan.Field(name='token_usage', kw_only=False, fn=None)),"
        " id=False, terse=True, default_fn=OpRef(name='repr.default_fn'))))"
    ),
    plan_repr_sha1='061935bc1a01224c96eb8768cf808ad905d79747',
    cls_names=(
        ('omllm.llm.types.messages', 'AiMessage'),
    ),
)
def _process_dataclass__061935bc1a01224c96eb8768cf808ad905d79747():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default,
        __dataclass__repr__default_fn,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('source', 'input', 'output', 'reasoning', 'cache_read', 'cache_write', 'total')), "
        "EqPlan(fields=('source', 'input', 'output', 'reasoning', 'cache_read', 'cache_write', 'total')), FrozenPlan(fi"
        "elds=('source', 'input', 'output', 'reasoning', 'cache_read', 'cache_write', 'total'), allow_dynamic_dunder_at"
        "trs=False), HashPlan(action='add', fields=('source', 'input', 'output', 'reasoning', 'cache_read', 'cache_writ"
        "e', 'total'), cache=True), InitPlan(fields=(InitPlan.Field(name='source', annotation=OpRef(name='init.fields.0"
        ".annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, c"
        "oerce=None, validate=None, check_type=None), InitPlan.Field(name='input', annotation=OpRef(name='init.fields.1"
        ".annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False, f"
        "ield_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='output', anno"
        "tation=OpRef(name='init.fields.2.annotation'), default=OpRef(name='init.fields.2.default'), default_factory=No"
        "ne, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), In"
        "itPlan.Field(name='reasoning', annotation=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.fie"
        "lds.3.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, "
        "validate=None, check_type=None), InitPlan.Field(name='cache_read', annotation=OpRef(name='init.fields.4.annota"
        "tion'), default=OpRef(name='init.fields.4.default'), default_factory=None, init=True, override=False, field_ty"
        "pe=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='cache_write', annota"
        "tion=OpRef(name='init.fields.5.annotation'), default=OpRef(name='init.fields.5.default'), default_factory=None"
        ", init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), Init"
        "Plan.Field(name='total', annotation=OpRef(name='init.fields.6.annotation'), default=OpRef(name='init.fields.6."
        "default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, valida"
        "te=None, check_type=None)), self_param='self', std_params=(), kw_only_params=('source', 'input', 'output', 're"
        "asoning', 'cache_read', 'cache_write', 'total'), frozen=True, slots=False, post_init_params=None, init_fns=(),"
        " validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='source', kw_only=True, fn=None), ReprPlan.Field(name="
        "'input', kw_only=True, fn=None), ReprPlan.Field(name='output', kw_only=True, fn=None), ReprPlan.Field(name='re"
        "asoning', kw_only=True, fn=None), ReprPlan.Field(name='cache_read', kw_only=True, fn=None), ReprPlan.Field(nam"
        "e='cache_write', kw_only=True, fn=None), ReprPlan.Field(name='total', kw_only=True, fn=None)), id=False, terse"
        "=False, default_fn=OpRef(name='repr.default_fn'))))"
    ),
    plan_repr_sha1='a0bc9b4d734d83792cb85d52bd8e1463bbf059f3',
    cls_names=(
        ('omllm.llm.types.messages', 'TokenCost'),
    ),
)
def _process_dataclass__a0bc9b4d734d83792cb85d52bd8e1463bbf059f3():
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
        __dataclass__init__fields__5__annotation,
        __dataclass__init__fields__5__default,
        __dataclass__init__fields__6__annotation,
        __dataclass__init__fields__6__default,
        __dataclass__repr__default_fn,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('input', 'output', 'reasoning', 'cache_read', 'cache_write', 'total', 'cost')), Eq"
        "Plan(fields=('input', 'output', 'reasoning', 'cache_read', 'cache_write', 'total', 'cost')), FrozenPlan(fields"
        "=('input', 'output', 'reasoning', 'cache_read', 'cache_write', 'total', 'cost'), allow_dynamic_dunder_attrs=Fa"
        "lse), HashPlan(action='add', fields=('input', 'output', 'reasoning', 'cache_read', 'cache_write', 'total', 'co"
        "st'), cache=True), InitPlan(fields=(InitPlan.Field(name='input', annotation=OpRef(name='init.fields.0.annotati"
        "on'), default=OpRef(name='init.fields.0.default'), default_factory=None, init=True, override=False, field_type"
        "=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='output', annotation=Op"
        "Ref(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init="
        "True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Fi"
        "eld(name='reasoning', annotation=OpRef(name='init.fields.2.annotation'), default=OpRef(name='init.fields.2.def"
        "ault'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate="
        "None, check_type=None), InitPlan.Field(name='cache_read', annotation=OpRef(name='init.fields.3.annotation'), d"
        "efault=OpRef(name='init.fields.3.default'), default_factory=None, init=True, override=False, field_type=FieldT"
        "ype.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='cache_write', annotation=OpRe"
        "f(name='init.fields.4.annotation'), default=OpRef(name='init.fields.4.default'), default_factory=None, init=Tr"
        "ue, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Fiel"
        "d(name='total', annotation=OpRef(name='init.fields.5.annotation'), default=OpRef(name='init.fields.5.default')"
        ", default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, "
        "check_type=None), InitPlan.Field(name='cost', annotation=OpRef(name='init.fields.6.annotation'), default=OpRef"
        "(name='init.fields.6.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE"
        ", coerce=None, validate=None, check_type=None)), self_param='self', std_params=(), kw_only_params=('input', 'o"
        "utput', 'reasoning', 'cache_read', 'cache_write', 'total', 'cost'), frozen=True, slots=False, post_init_params"
        "=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='input', kw_only=True, fn=None), Re"
        "prPlan.Field(name='output', kw_only=True, fn=None), ReprPlan.Field(name='reasoning', kw_only=True, fn=None), R"
        "eprPlan.Field(name='cache_read', kw_only=True, fn=None), ReprPlan.Field(name='cache_write', kw_only=True, fn=N"
        "one), ReprPlan.Field(name='total', kw_only=True, fn=None), ReprPlan.Field(name='cost', kw_only=True, fn=None))"
        ", id=False, terse=False, default_fn=OpRef(name='repr.default_fn'))))"
    ),
    plan_repr_sha1='79d9675f68939e252c61967b5a3eba4415a8c341',
    cls_names=(
        ('omllm.llm.types.messages', 'TokenUsage'),
    ),
)
def _process_dataclass__79d9675f68939e252c61967b5a3eba4415a8c341():
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
        __dataclass__repr__default_fn,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('tool_call_id', 'tool_name', 'content')), EqPlan(fields=('tool_call_id', 'tool_nam"
        "e', 'content')), FrozenPlan(fields=('tool_call_id', 'tool_name', 'content'), allow_dynamic_dunder_attrs=False)"
        ", HashPlan(action='add', fields=('tool_call_id', 'tool_name', 'content'), cache=True), InitPlan(fields=(InitPl"
        "an.Field(name='tool_call_id', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory"
        "=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),"
        " InitPlan.Field(name='tool_name', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_fac"
        "tory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=No"
        "ne), InitPlan.Field(name='content', annotation=OpRef(name='init.fields.2.annotation'), default=OpRef(name='ini"
        "t.fields.2.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=N"
        "one, validate=None, check_type=None)), self_param='self', std_params=(), kw_only_params=('tool_call_id', 'tool"
        "_name', 'content'), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(f"
        "ields=(ReprPlan.Field(name='tool_call_id', kw_only=True, fn=None), ReprPlan.Field(name='tool_name', kw_only=Tr"
        "ue, fn=None), ReprPlan.Field(name='content', kw_only=True, fn=None)), id=False, terse=True, default_fn=None)))"
    ),
    plan_repr_sha1='56a267900b9bd6d479eb65c8d8f0b3792a866284',
    cls_names=(
        ('omllm.llm.types.messages', 'ToolResultMessage'),
    ),
)
def _process_dataclass__56a267900b9bd6d479eb65c8d8f0b3792a866284():
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
                tool_call_id=self.tool_call_id,
                tool_name=self.tool_name,
                content=self.content,
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
                self.content == other.content
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'tool_call_id',
            'tool_name',
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
                    self.tool_call_id,
                    self.tool_name,
                    self.content,
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
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'tool_call_id', tool_call_id)
            __dataclass__object_setattr(self, 'tool_name', tool_name)
            __dataclass__object_setattr(self, 'content', content)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"tool_call_id={self.tool_call_id!r}")
            parts.append(f"tool_name={self.tool_name!r}")
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
        "Plans(tup=(CopyPlan(fields=('content',)), EqPlan(fields=('content',)), FrozenPlan(fields=('content',), allow_d"
        "ynamic_dunder_attrs=False), HashPlan(action='add', fields=('content',), cache=True), InitPlan(fields=(InitPlan"
        ".Field(name='content', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, "
        "init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self"
        "_param='self', std_params=('content',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, in"
        "it_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='content', kw_only=False, fn=None),), id=Fal"
        "se, terse=True, default_fn=None)))"
    ),
    plan_repr_sha1='44982acb11cf798fbaef59a3118993dec288d9c2',
    cls_names=(
        ('omllm.llm.types.messages', 'UserMessage'),
    ),
)
def _process_dataclass__44982acb11cf798fbaef59a3118993dec288d9c2():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('control_style', 'retentions', 'key')), EqPlan(fields=('control_style', 'retention"
        "s', 'key')), FrozenPlan(fields=('control_style', 'retentions', 'key'), allow_dynamic_dunder_attrs=False), Hash"
        "Plan(action='add', fields=('control_style', 'retentions', 'key'), cache=False), InitPlan(fields=(InitPlan.Fiel"
        "d(name='control_style', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None,"
        " init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitP"
        "lan.Field(name='retentions', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.field"
        "s.1.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, va"
        "lidate=None, check_type=None), InitPlan.Field(name='key', annotation=OpRef(name='init.fields.2.annotation'), d"
        "efault=OpRef(name='init.fields.2.default'), default_factory=None, init=True, override=False, field_type=FieldT"
        "ype.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=(), kw_only_params="
        "('control_style', 'retentions', 'key'), frozen=True, slots=False, post_init_params=None, init_fns=(), validate"
        "_fns=()), ReprPlan(fields=(ReprPlan.Field(name='control_style', kw_only=True, fn=None), ReprPlan.Field(name='r"
        "etentions', kw_only=True, fn=None), ReprPlan.Field(name='key', kw_only=True, fn=None)), id=False, terse=False,"
        " default_fn=OpRef(name='repr.default_fn'))))"
    ),
    plan_repr_sha1='62d7648385bcff6be1254f65f055e0cce791cec8',
    cls_names=(
        ('omllm.llm.types.models', 'CacheCapabilities'),
    ),
)
def _process_dataclass__62d7648385bcff6be1254f65f055e0cce791cec8():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default,
        __dataclass__repr__default_fn,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('key', 'name', 'backend', 'compat', 'cache', 'pricing', 'http', 'default_options')"
        "), EqPlan(fields=('key', 'name', 'backend', 'compat', 'cache', 'pricing', 'http', 'default_options')), FrozenP"
        "lan(fields=('key', 'name', 'backend', 'compat', 'cache', 'pricing', 'http', 'default_options'), allow_dynamic_"
        "dunder_attrs=False), HashPlan(action='add', fields=('key', 'name', 'backend', 'compat', 'cache', 'pricing', 'h"
        "ttp', 'default_options'), cache=False), InitPlan(fields=(InitPlan.Field(name='key', annotation=OpRef(name='ini"
        "t.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.I"
        "NSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='name', annotation=OpRef(name='init"
        ".fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override"
        "=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='back"
        "end', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, overri"
        "de=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='co"
        "mpat', annotation=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default'), default"
        "_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_typ"
        "e=None), InitPlan.Field(name='cache', annotation=OpRef(name='init.fields.4.annotation'), default=OpRef(name='i"
        "nit.fields.4.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce"
        "=None, validate=None, check_type=None), InitPlan.Field(name='pricing', annotation=OpRef(name='init.fields.5.an"
        "notation'), default=OpRef(name='init.fields.5.default'), default_factory=None, init=True, override=False, fiel"
        "d_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='http', annotatio"
        "n=OpRef(name='init.fields.6.annotation'), default=OpRef(name='init.fields.6.default'), default_factory=None, i"
        "nit=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPla"
        "n.Field(name='default_options', annotation=OpRef(name='init.fields.7.annotation'), default=OpRef(name='init.fi"
        "elds.7.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None,"
        " validate=None, check_type=None)), self_param='self', std_params=(), kw_only_params=('key', 'name', 'backend',"
        " 'compat', 'cache', 'pricing', 'http', 'default_options'), frozen=True, slots=False, post_init_params=None, in"
        "it_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='key', kw_only=True, fn=None), ReprPlan.Fiel"
        "d(name='name', kw_only=True, fn=None), ReprPlan.Field(name='backend', kw_only=True, fn=None), ReprPlan.Field(n"
        "ame='compat', kw_only=True, fn=None), ReprPlan.Field(name='cache', kw_only=True, fn=None), ReprPlan.Field(name"
        "='pricing', kw_only=True, fn=None), ReprPlan.Field(name='http', kw_only=True, fn=None), ReprPlan.Field(name='d"
        "efault_options', kw_only=True, fn=None)), id=False, terse=False, default_fn=OpRef(name='repr.default_fn'))))"
    ),
    plan_repr_sha1='19dd6ca6db49fca726283097baf13b72b37bcfc6',
    cls_names=(
        ('omllm.llm.types.models', 'Model'),
    ),
)
def _process_dataclass__19dd6ca6db49fca726283097baf13b72b37bcfc6():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
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
        __dataclass__repr__default_fn,
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
                name=self.name,
                backend=self.backend,
                compat=self.compat,
                cache=self.cache,
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
                self.name == other.name and
                self.backend == other.backend and
                self.compat == other.compat and
                self.cache == other.cache and
                self.pricing == other.pricing and
                self.http == other.http and
                self.default_options == other.default_options
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'key',
            'name',
            'backend',
            'compat',
            'cache',
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
                self.name,
                self.backend,
                self.compat,
                self.cache,
                self.pricing,
                self.http,
                self.default_options,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            key: __dataclass__init__fields__0__annotation,
            name: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            backend: __dataclass__init__fields__2__annotation,
            compat: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            cache: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            pricing: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            http: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
            default_options: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'backend', backend)
            __dataclass__object_setattr(self, 'compat', compat)
            __dataclass__object_setattr(self, 'cache', cache)
            __dataclass__object_setattr(self, 'pricing', pricing)
            __dataclass__object_setattr(self, 'http', http)
            __dataclass__object_setattr(self, 'default_options', default_options)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.key)) is not None:
                parts.append(f"key={s}")
            if (s := __dataclass__repr__default_fn(self.name)) is not None:
                parts.append(f"name={s}")
            if (s := __dataclass__repr__default_fn(self.backend)) is not None:
                parts.append(f"backend={s}")
            if (s := __dataclass__repr__default_fn(self.compat)) is not None:
                parts.append(f"compat={s}")
            if (s := __dataclass__repr__default_fn(self.cache)) is not None:
                parts.append(f"cache={s}")
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('base_url', 'extra_headers')), EqPlan(fields=('base_url', 'extra_headers')), Froze"
        "nPlan(fields=('base_url', 'extra_headers'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=("
        "'base_url', 'extra_headers'), cache=False), InitPlan(fields=(InitPlan.Field(name='base_url', annotation=OpRef("
        "name='init.fields.0.annotation'), default=OpRef(name='init.fields.0.default'), default_factory=None, init=True"
        ", override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field("
        "name='extra_headers', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.def"
        "ault'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate="
        "None, check_type=None)), self_param='self', std_params=(), kw_only_params=('base_url', 'extra_headers'), froze"
        "n=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(nam"
        "e='base_url', kw_only=True, fn=None), ReprPlan.Field(name='extra_headers', kw_only=True, fn=None)), id=False, "
        "terse=False, default_fn=OpRef(name='repr.default_fn'))))"
    ),
    plan_repr_sha1='6c89d81d5ca3b78c4d52109711a234163e2ba7ce',
    cls_names=(
        ('omllm.llm.types.models', 'Model.Http'),
    ),
)
def _process_dataclass__6c89d81d5ca3b78c4d52109711a234163e2ba7ce():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__default,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
        __dataclass__repr__default_fn,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('provider', 'id')), EqPlan(fields=('provider', 'id')), FrozenPlan(fields=('provide"
        "r', 'id'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('provider', 'id'), cache=True), I"
        "nitPlan(fields=(InitPlan.Field(name='provider', annotation=OpRef(name='init.fields.0.annotation'), default=Non"
        "e, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None,"
        " check_type=None), InitPlan.Field(name='id', annotation=OpRef(name='init.fields.1.annotation'), default=None, "
        "default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, ch"
        "eck_type=None)), self_param='self', std_params=('provider', 'id'), kw_only_params=(), frozen=True, slots=False"
        ", post_init_params=(), init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='provider', kw_only"
        "=False, fn=None), ReprPlan.Field(name='id', kw_only=False, fn=None)), id=False, terse=True, default_fn=None)))"
    ),
    plan_repr_sha1='a7b5c57ce0097a16cde0613f080138d253ed649c',
    cls_names=(
        ('omllm.llm.types.models', 'ModelKey'),
    ),
)
def _process_dataclass__a7b5c57ce0097a16cde0613f080138d253ed649c():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('input', 'output', 'reasoning', 'cache_read', 'cache_write')), EqPlan(fields=('inp"
        "ut', 'output', 'reasoning', 'cache_read', 'cache_write')), FrozenPlan(fields=('input', 'output', 'reasoning', "
        "'cache_read', 'cache_write'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('input', 'outp"
        "ut', 'reasoning', 'cache_read', 'cache_write'), cache=False), InitPlan(fields=(InitPlan.Field(name='input', an"
        "notation=OpRef(name='init.fields.0.annotation'), default=OpRef(name='init.fields.0.default'), default_factory="
        "None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), "
        "InitPlan.Field(name='output', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fiel"
        "ds.1.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, v"
        "alidate=None, check_type=None), InitPlan.Field(name='reasoning', annotation=OpRef(name='init.fields.2.annotati"
        "on'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, override=False, field_type"
        "=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='cache_read', annotatio"
        "n=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default'), default_factory=None, i"
        "nit=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPla"
        "n.Field(name='cache_write', annotation=OpRef(name='init.fields.4.annotation'), default=OpRef(name='init.fields"
        ".4.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, val"
        "idate=None, check_type=None)), self_param='self', std_params=(), kw_only_params=('input', 'output', 'reasoning"
        "', 'cache_read', 'cache_write'), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()"
        "), ReprPlan(fields=(ReprPlan.Field(name='input', kw_only=True, fn=None), ReprPlan.Field(name='output', kw_only"
        "=True, fn=None), ReprPlan.Field(name='reasoning', kw_only=True, fn=None), ReprPlan.Field(name='cache_read', kw"
        "_only=True, fn=None), ReprPlan.Field(name='cache_write', kw_only=True, fn=None)), id=False, terse=False, defau"
        "lt_fn=OpRef(name='repr.default_fn'))))"
    ),
    plan_repr_sha1='a5f4b089b8c09aae799266776a389d5a09b9d2ac',
    cls_names=(
        ('omllm.llm.types.models', 'TokenPricing'),
    ),
)
def _process_dataclass__a5f4b089b8c09aae799266776a389d5a09b9d2ac():
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
        __dataclass__repr__default_fn,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('max_tokens', 'thinking', 'cache_key', 'cache_retention')), EqPlan(fields=('max_to"
        "kens', 'thinking', 'cache_key', 'cache_retention')), FrozenPlan(fields=('max_tokens', 'thinking', 'cache_key',"
        " 'cache_retention'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('max_tokens', 'thinking"
        "', 'cache_key', 'cache_retention'), cache=False), InitPlan(fields=(InitPlan.Field(name='max_tokens', annotatio"
        "n=OpRef(name='init.fields.0.annotation'), default=OpRef(name='init.fields.0.default'), default_factory=None, i"
        "nit=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPla"
        "n.Field(name='thinking', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1."
        "default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, valida"
        "te=None, check_type=None), InitPlan.Field(name='cache_key', annotation=OpRef(name='init.fields.2.annotation'),"
        " default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, override=False, field_type=Fiel"
        "dType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='cache_retention', annotatio"
        "n=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default'), default_factory=None, i"
        "nit=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_p"
        "aram='self', std_params=(), kw_only_params=('max_tokens', 'thinking', 'cache_key', 'cache_retention'), frozen="
        "True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name="
        "'max_tokens', kw_only=True, fn=None), ReprPlan.Field(name='thinking', kw_only=True, fn=None), ReprPlan.Field(n"
        "ame='cache_key', kw_only=True, fn=None), ReprPlan.Field(name='cache_retention', kw_only=True, fn=None)), id=Fa"
        "lse, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='8186e59bc324a6fc6135e82385d9c308e96e4d55',
    cls_names=(
        ('omllm.llm.types.options', 'Options'),
    ),
)
def _process_dataclass__8186e59bc324a6fc6135e82385d9c308e96e4d55():
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
                max_tokens=self.max_tokens,
                thinking=self.thinking,
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
                self.cache_key == other.cache_key and
                self.cache_retention == other.cache_retention
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'max_tokens',
            'thinking',
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
                self.cache_key,
                self.cache_retention,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            max_tokens: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            thinking: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            cache_key: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            cache_retention: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'max_tokens', max_tokens)
            __dataclass__object_setattr(self, 'thinking', thinking)
            __dataclass__object_setattr(self, 'cache_key', cache_key)
            __dataclass__object_setattr(self, 'cache_retention', cache_retention)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"max_tokens={self.max_tokens!r}")
            parts.append(f"thinking={self.thinking!r}")
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('content_index',)), EqPlan(fields=('content_index',)), FrozenPlan(fields=('content"
        "_index',), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('content_index',), cache=False), "
        "InitPlan(fields=(InitPlan.Field(name='content_index', annotation=OpRef(name='init.fields.0.annotation'), defau"
        "lt=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate"
        "=None, check_type=None),), self_param='self', std_params=(), kw_only_params=('content_index',), frozen=True, s"
        "lots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='conten"
        "t_index', kw_only=True, fn=None),), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='8b93f579e9d14927b8f9e080e28cd444d77c7026',
    cls_names=(
        ('omllm.llm.types.streams', 'ContentAiStreamEvent'),
        ('omllm.llm.types.streams', 'TextStartAiStreamEvent'),
        ('omllm.llm.types.streams', 'ThinkingStartAiStreamEvent'),
    ),
)
def _process_dataclass__8b93f579e9d14927b8f9e080e28cd444d77c7026():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('content_index', 'text')), EqPlan(fields=('content_index', 'text')), FrozenPlan(fi"
        "elds=('content_index', 'text'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('content_ind"
        "ex', 'text'), cache=True), InitPlan(fields=(InitPlan.Field(name='content_index', annotation=OpRef(name='init.f"
        "ields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INST"
        "ANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='text', annotation=OpRef(name='init.fi"
        "elds.1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTA"
        "NCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('text',), kw_only_params=('"
        "content_index',), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fie"
        "lds=(ReprPlan.Field(name='text', kw_only=False, fn=None), ReprPlan.Field(name='content_index', kw_only=True, f"
        "n=None)), id=False, terse=True, default_fn=None)))"
    ),
    plan_repr_sha1='6ec0fa6131765fb8aeb272cd50f97d3cebf5c411',
    cls_names=(
        ('omllm.llm.types.streams', 'TextDeltaAiStreamEvent'),
        ('omllm.llm.types.streams', 'TextEndAiStreamEvent'),
        ('omllm.llm.types.streams', 'ThinkingDeltaAiStreamEvent'),
        ('omllm.llm.types.streams', 'ThinkingEndAiStreamEvent'),
        ('omllm.llm.types.streams', 'ToolCallDeltaAiStreamEvent'),
    ),
)
def _process_dataclass__6ec0fa6131765fb8aeb272cd50f97d3cebf5c411():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('content_index', 'tool_call')), EqPlan(fields=('content_index', 'tool_call')), Fro"
        "zenPlan(fields=('content_index', 'tool_call'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', field"
        "s=('content_index', 'tool_call'), cache=True), InitPlan(fields=(InitPlan.Field(name='content_index', annotatio"
        "n=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field"
        "_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='tool_call', annot"
        "ation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, f"
        "ield_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('t"
        "ool_call',), kw_only_params=('content_index',), frozen=True, slots=False, post_init_params=None, init_fns=(), "
        "validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='tool_call', kw_only=False, fn=None), ReprPlan.Field(na"
        "me='content_index', kw_only=True, fn=None)), id=False, terse=True, default_fn=None)))"
    ),
    plan_repr_sha1='8979899b272f9867717857f9c97e2af99d4df08c',
    cls_names=(
        ('omllm.llm.types.streams', 'ToolCallEndAiStreamEvent'),
    ),
)
def _process_dataclass__8979899b272f9867717857f9c97e2af99d4df08c():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('content_index',)), EqPlan(fields=('content_index',)), FrozenPlan(fields=('content"
        "_index',), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('content_index',), cache=True), I"
        "nitPlan(fields=(InitPlan.Field(name='content_index', annotation=OpRef(name='init.fields.0.annotation'), defaul"
        "t=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate="
        "None, check_type=None),), self_param='self', std_params=(), kw_only_params=('content_index',), frozen=True, sl"
        "ots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='content"
        "_index', kw_only=True, fn=None),), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='2f297aff3600bf09ca74d5106118f3c78a4c2890',
    cls_names=(
        ('omllm.llm.types.streams', 'ToolCallStartAiStreamEvent'),
    ),
)
def _process_dataclass__2f297aff3600bf09ca74d5106118f3c78a4c2890():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('type', 'values')), EqPlan(fields=('type', 'values')), FrozenPlan(fields=('type', "
        "'values'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('type', 'values'), cache=False), "
        "InitPlan(fields=(InitPlan.Field(name='type', annotation=OpRef(name='init.fields.0.annotation'), default=None, "
        "default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, ch"
        "eck_type=None), InitPlan.Field(name='values', annotation=OpRef(name='init.fields.1.annotation'), default=None,"
        " default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, c"
        "heck_type=None)), self_param='self', std_params=('type', 'values'), kw_only_params=(), frozen=True, slots=Fals"
        "e, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='type', kw_only="
        "False, fn=None), ReprPlan.Field(name='values', kw_only=False, fn=None)), id=False, terse=True, default_fn=None"
        ")))"
    ),
    plan_repr_sha1='922e75739507bda9dce73a0d3dc05534b1cc9ae5',
    cls_names=(
        ('omllm.llm.types.tools', 'EnumToolDtype'),
    ),
)
def _process_dataclass__922e75739507bda9dce73a0d3dc05534b1cc9ae5():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('key', 'value')), EqPlan(fields=('key', 'value')), FrozenPlan(fields=('key', 'valu"
        "e'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('key', 'value'), cache=False), InitPlan"
        "(fields=(InitPlan.Field(name='key', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_f"
        "actory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type="
        "None), InitPlan.Field(name='value', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_f"
        "actory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type="
        "None)), self_param='self', std_params=('key', 'value'), kw_only_params=(), frozen=True, slots=False, post_init"
        "_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='key', kw_only=False, fn=Non"
        "e), ReprPlan.Field(name='value', kw_only=False, fn=None)), id=False, terse=True, default_fn=None)))"
    ),
    plan_repr_sha1='2ded8afb50edd07329da6b7055981919a83dec56',
    cls_names=(
        ('omllm.llm.types.tools', 'MappingToolDtype'),
    ),
)
def _process_dataclass__2ded8afb50edd07329da6b7055981919a83dec56():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('type',)), EqPlan(fields=('type',)), FrozenPlan(fields=('type',), allow_dynamic_du"
        "nder_attrs=False), HashPlan(action='add', fields=('type',), cache=False), InitPlan(fields=(InitPlan.Field(name"
        "='type', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, ove"
        "rride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='self',"
        " std_params=('type',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), valida"
        "te_fns=()), ReprPlan(fields=(ReprPlan.Field(name='type', kw_only=False, fn=None),), id=False, terse=True, defa"
        "ult_fn=None)))"
    ),
    plan_repr_sha1='1d0b04d8ebb0bdb077bc9721fb19aafcadf99422',
    cls_names=(
        ('omllm.llm.types.tools', 'NullableToolDtype'),
    ),
)
def _process_dataclass__1d0b04d8ebb0bdb077bc9721fb19aafcadf99422():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('fields',)), EqPlan(fields=('fields',)), FrozenPlan(fields=('fields',), allow_dyna"
        "mic_dunder_attrs=False), HashPlan(action='add', fields=('fields',), cache=False), InitPlan(fields=(InitPlan.Fi"
        "eld(name='fields', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init"
        "=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_par"
        "am='self', std_params=('fields',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fn"
        "s=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='fields', kw_only=False, fn=None),), id=False, te"
        "rse=True, default_fn=None)))"
    ),
    plan_repr_sha1='178374af8c25e44a33c44ece98db0c96fe041247',
    cls_names=(
        ('omllm.llm.types.tools', 'ObjectToolDtype'),
    ),
)
def _process_dataclass__178374af8c25e44a33c44ece98db0c96fe041247():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('type',)), EqPlan(fields=('type',)), FrozenPlan(fields=('type',), allow_dynamic_du"
        "nder_attrs=False), HashPlan(action='add', fields=('type',), cache=False), InitPlan(fields=(InitPlan.Field(name"
        "='type', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, ove"
        "rride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='self',"
        " std_params=('type',), kw_only_params=(), frozen=True, slots=False, post_init_params=(), init_fns=(), validate"
        "_fns=()), ReprPlan(fields=(ReprPlan.Field(name='type', kw_only=False, fn=None),), id=False, terse=True, defaul"
        "t_fn=None)))"
    ),
    plan_repr_sha1='b7657835eed1f3e17dbdae82eb197181dd5862db',
    cls_names=(
        ('omllm.llm.types.tools', 'PrimitiveToolDtype'),
    ),
)
def _process_dataclass__b7657835eed1f3e17dbdae82eb197181dd5862db():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('element',)), EqPlan(fields=('element',)), FrozenPlan(fields=('element',), allow_d"
        "ynamic_dunder_attrs=False), HashPlan(action='add', fields=('element',), cache=False), InitPlan(fields=(InitPla"
        "n.Field(name='element', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None,"
        " init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), sel"
        "f_param='self', std_params=('element',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, i"
        "nit_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='element', kw_only=False, fn=None),), id=Fa"
        "lse, terse=True, default_fn=None)))"
    ),
    plan_repr_sha1='95d65e05398b42908ba7d67d961be3c1dae7f5b4',
    cls_names=(
        ('omllm.llm.types.tools', 'SequenceToolDtype'),
    ),
)
def _process_dataclass__95d65e05398b42908ba7d67d961be3c1dae7f5b4():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('name', 'description', 'params', 'allow_additional_params', 'return_type', 'return"
        "_description')), EqPlan(fields=('name', 'description', 'params', 'allow_additional_params', 'return_type', 're"
        "turn_description')), FrozenPlan(fields=('name', 'description', 'params', 'allow_additional_params', 'return_ty"
        "pe', 'return_description'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('name', 'descrip"
        "tion', 'params', 'allow_additional_params', 'return_type', 'return_description'), cache=False), InitPlan(field"
        "s=(InitPlan.Field(name='name', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factor"
        "y=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=OpRef(name='init.fields.0.coerce'), v"
        "alidate=None, check_type=None), InitPlan.Field(name='description', annotation=OpRef(name='init.fields.1.annota"
        "tion'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False, field_ty"
        "pe=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='params', annotation="
        "OpRef(name='init.fields.2.annotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, ini"
        "t=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan."
        "Field(name='allow_additional_params', annotation=OpRef(name='init.fields.3.annotation'), default=OpRef(name='i"
        "nit.fields.3.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce"
        "=None, validate=None, check_type=None), InitPlan.Field(name='return_type', annotation=OpRef(name='init.fields."
        "4.annotation'), default=OpRef(name='init.fields.4.default'), default_factory=None, init=True, override=False, "
        "field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='return_descr"
        "iption', annotation=OpRef(name='init.fields.5.annotation'), default=OpRef(name='init.fields.5.default'), defau"
        "lt_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_t"
        "ype=None)), self_param='self', std_params=(), kw_only_params=('name', 'description', 'params', 'allow_addition"
        "al_params', 'return_type', 'return_description'), frozen=True, slots=False, post_init_params=None, init_fns=(O"
        "pRef(name='init.init_fns.0'),), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='name', kw_only=True, f"
        "n=None), ReprPlan.Field(name='description', kw_only=True, fn=None), ReprPlan.Field(name='params', kw_only=True"
        ", fn=None), ReprPlan.Field(name='allow_additional_params', kw_only=True, fn=None), ReprPlan.Field(name='return"
        "_type', kw_only=True, fn=None), ReprPlan.Field(name='return_description', kw_only=True, fn=None)), id=False, t"
        "erse=False, default_fn=OpRef(name='repr.default_fn'))))"
    ),
    plan_repr_sha1='482a03d99c8e3142d26141858c5b43bbf158cbd7',
    cls_names=(
        ('omllm.llm.types.tools', 'Tool'),
    ),
)
def _process_dataclass__482a03d99c8e3142d26141858c5b43bbf158cbd7():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__coerce,
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
        __dataclass__init__init_fns__0,
        __dataclass__repr__default_fn,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('name', 'description', 'type', 'optional')), EqPlan(fields=('name', 'description',"
        " 'type', 'optional')), FrozenPlan(fields=('name', 'description', 'type', 'optional'), allow_dynamic_dunder_att"
        "rs=False), HashPlan(action='add', fields=('name', 'description', 'type', 'optional'), cache=False), InitPlan(f"
        "ields=(InitPlan.Field(name='name', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_fa"
        "ctory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=OpRef(name='init.fields.0.coerce'"
        "), validate=None, check_type=None), InitPlan.Field(name='description', annotation=OpRef(name='init.fields.1.an"
        "notation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False, fiel"
        "d_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='type', annotatio"
        "n=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=False, field"
        "_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='optional', annota"
        "tion=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default'), default_factory=None"
        ", init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), sel"
        "f_param='self', std_params=(), kw_only_params=('name', 'description', 'type', 'optional'), frozen=True, slots="
        "False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='name', kw_o"
        "nly=True, fn=None), ReprPlan.Field(name='description', kw_only=True, fn=None), ReprPlan.Field(name='type', kw_"
        "only=True, fn=None), ReprPlan.Field(name='optional', kw_only=True, fn=OpRef(name='repr.fns.3.fn'))), id=False,"
        " terse=False, default_fn=OpRef(name='repr.default_fn'))))"
    ),
    plan_repr_sha1='1a1a12f7a96aaaec9e65285fcb70f4b9d2d7b570',
    cls_names=(
        ('omllm.llm.types.tools', 'ToolParam'),
    ),
)
def _process_dataclass__1a1a12f7a96aaaec9e65285fcb70f4b9d2d7b570():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__coerce,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__3__default,
        __dataclass__repr__default_fn,
        __dataclass__repr__fns__3__fn,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('elements',)), EqPlan(fields=('elements',)), FrozenPlan(fields=('elements',), allo"
        "w_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('elements',), cache=False), InitPlan(fields=(Ini"
        "tPlan.Field(name='elements', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory="
        "None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),)"
        ", self_param='self', std_params=('elements',), kw_only_params=(), frozen=True, slots=False, post_init_params=N"
        "one, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='elements', kw_only=False, fn=None),)"
        ", id=False, terse=True, default_fn=None)))"
    ),
    plan_repr_sha1='a72c7b37c724624d1543d1cc8dffce6fcbbad416',
    cls_names=(
        ('omllm.llm.types.tools', 'TupleToolDtype'),
    ),
)
def _process_dataclass__a72c7b37c724624d1543d1cc8dffce6fcbbad416():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('args',)), EqPlan(fields=('args',)), FrozenPlan(fields=('args',), allow_dynamic_du"
        "nder_attrs=False), HashPlan(action='add', fields=('args',), cache=False), InitPlan(fields=(InitPlan.Field(name"
        "='args', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, ove"
        "rride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='self',"
        " std_params=('args',), kw_only_params=(), frozen=True, slots=False, post_init_params=(), init_fns=(), validate"
        "_fns=()), ReprPlan(fields=(ReprPlan.Field(name='args', kw_only=False, fn=None),), id=False, terse=True, defaul"
        "t_fn=None)))"
    ),
    plan_repr_sha1='ad919be3aed733ce0d02ac2f6d4c55bbced3d288',
    cls_names=(
        ('omllm.llm.types.tools', 'UnionToolDtype'),
    ),
)
def _process_dataclass__ad919be3aed733ce0d02ac2f6d4c55bbced3d288():
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
