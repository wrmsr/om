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
