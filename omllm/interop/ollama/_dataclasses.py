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
    installer_sha1='da8c5806e7f17fba17eb07bd6b1dde4995d50426',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('model', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('stream', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('options', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('format', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('keep_alive', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.interop.ollama.protocol', 'BaseGenerateRequest'),
    ),
)
def _process_dataclass__da8c5806e7f17fba17eb07bd6b1dde4995d50426():
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
                model=self.model,
                stream=self.stream,
                options=self.options,
                format=self.format,
                keep_alive=self.keep_alive,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.model == other.model and
                self.stream == other.stream and
                self.options == other.options and
                self.format == other.format and
                self.keep_alive == other.keep_alive
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'model',
            'stream',
            'options',
            'format',
            'keep_alive',
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
                self.model,
                self.stream,
                self.options,
                self.format,
                self.keep_alive,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            model: __dataclass__init__fields__0__annotation,
            stream: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            options: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            format: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            keep_alive: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'model', model)
            __dataclass__object_setattr(self, 'stream', stream)
            __dataclass__object_setattr(self, 'options', options)
            __dataclass__object_setattr(self, 'format', format)
            __dataclass__object_setattr(self, 'keep_alive', keep_alive)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"model={self.model!r}")
            parts.append(f"stream={self.stream!r}")
            parts.append(f"options={self.options!r}")
            parts.append(f"format={self.format!r}")
            parts.append(f"keep_alive={self.keep_alive!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='415fdfd053d61c9d186a588adee5d9b9c47b009b',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('model', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('created_at', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('done', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('done_reason', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('total_duration', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('load_duration', True, True, None, True, True, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('prompt_eval_count', True, True, None, True, True, False, None)"
            ", 'instance', 'value', None, False, False, False), (('prompt_eval_duration', True, True, None, True, True,"
            " False, None), 'instance', 'value', None, False, False, False), (('eval_count', True, True, None, True, Tr"
            "ue, False, None), 'instance', 'value', None, False, False, False), (('eval_duration', True, True, None, Tr"
            "ue, True, False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False"
            ",), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.interop.ollama.protocol', 'BaseGenerateResponse'),
    ),
)
def _process_dataclass__415fdfd053d61c9d186a588adee5d9b9c47b009b():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                model=self.model,
                created_at=self.created_at,
                done=self.done,
                done_reason=self.done_reason,
                total_duration=self.total_duration,
                load_duration=self.load_duration,
                prompt_eval_count=self.prompt_eval_count,
                prompt_eval_duration=self.prompt_eval_duration,
                eval_count=self.eval_count,
                eval_duration=self.eval_duration,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.model == other.model and
                self.created_at == other.created_at and
                self.done == other.done and
                self.done_reason == other.done_reason and
                self.total_duration == other.total_duration and
                self.load_duration == other.load_duration and
                self.prompt_eval_count == other.prompt_eval_count and
                self.prompt_eval_duration == other.prompt_eval_duration and
                self.eval_count == other.eval_count and
                self.eval_duration == other.eval_duration
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'model',
            'created_at',
            'done',
            'done_reason',
            'total_duration',
            'load_duration',
            'prompt_eval_count',
            'prompt_eval_duration',
            'eval_count',
            'eval_duration',
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
                self.model,
                self.created_at,
                self.done,
                self.done_reason,
                self.total_duration,
                self.load_duration,
                self.prompt_eval_count,
                self.prompt_eval_duration,
                self.eval_count,
                self.eval_duration,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            model: __dataclass__init__fields__00__annotation = __dataclass__init__fields__00__default,
            created_at: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            done: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            done_reason: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            total_duration: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            load_duration: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            prompt_eval_count: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            prompt_eval_duration: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            eval_count: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            eval_duration: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'model', model)
            __dataclass__object_setattr(self, 'created_at', created_at)
            __dataclass__object_setattr(self, 'done', done)
            __dataclass__object_setattr(self, 'done_reason', done_reason)
            __dataclass__object_setattr(self, 'total_duration', total_duration)
            __dataclass__object_setattr(self, 'load_duration', load_duration)
            __dataclass__object_setattr(self, 'prompt_eval_count', prompt_eval_count)
            __dataclass__object_setattr(self, 'prompt_eval_duration', prompt_eval_duration)
            __dataclass__object_setattr(self, 'eval_count', eval_count)
            __dataclass__object_setattr(self, 'eval_duration', eval_duration)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"model={self.model!r}")
            parts.append(f"created_at={self.created_at!r}")
            parts.append(f"done={self.done!r}")
            parts.append(f"done_reason={self.done_reason!r}")
            parts.append(f"total_duration={self.total_duration!r}")
            parts.append(f"load_duration={self.load_duration!r}")
            parts.append(f"prompt_eval_count={self.prompt_eval_count!r}")
            parts.append(f"prompt_eval_duration={self.prompt_eval_duration!r}")
            parts.append(f"eval_count={self.eval_count!r}")
            parts.append(f"eval_duration={self.eval_duration!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b9700b794f469d90a58fa833a07a7cdbf914bd15',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('model', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.interop.ollama.protocol', 'BaseRequest'),
    ),
)
def _process_dataclass__b9700b794f469d90a58fa833a07a7cdbf914bd15():
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
                model=self.model,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.model == other.model
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'model',
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
                self.model,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            model: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'model', model)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"model={self.model!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='120256592f040eda58f5e8c4007b0b44f1d64e6c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('model', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('stream', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (),"
            " (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.interop.ollama.protocol', 'BaseStreamableRequest'),
    ),
)
def _process_dataclass__120256592f040eda58f5e8c4007b0b44f1d64e6c():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
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
                model=self.model,
                stream=self.stream,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.model == other.model and
                self.stream == other.stream
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'model',
            'stream',
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
                self.model,
                self.stream,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            model: __dataclass__init__fields__0__annotation,
            stream: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'model', model)
            __dataclass__object_setattr(self, 'stream', stream)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"model={self.model!r}")
            parts.append(f"stream={self.stream!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e93c23e33a930da6c8a2918c24e7b0831eeba471',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('model', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('stream', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('options', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('format', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('keep_alive', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('messages', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('tools', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('think', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), ("
            "False,)))"
        ),
    ),
    cls_names=(
        ('omllm.interop.ollama.protocol', 'ChatRequest'),
    ),
)
def _process_dataclass__e93c23e33a930da6c8a2918c24e7b0831eeba471():
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
        __dataclass__init__fields__7__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__7__default = __dataclass__spec.fields[7].default.must()
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
                model=self.model,
                stream=self.stream,
                options=self.options,
                format=self.format,
                keep_alive=self.keep_alive,
                messages=self.messages,
                tools=self.tools,
                think=self.think,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.model == other.model and
                self.stream == other.stream and
                self.options == other.options and
                self.format == other.format and
                self.keep_alive == other.keep_alive and
                self.messages == other.messages and
                self.tools == other.tools and
                self.think == other.think
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'model',
            'stream',
            'options',
            'format',
            'keep_alive',
            'messages',
            'tools',
            'think',
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
                self.model,
                self.stream,
                self.options,
                self.format,
                self.keep_alive,
                self.messages,
                self.tools,
                self.think,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            model: __dataclass__init__fields__0__annotation,
            stream: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            options: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            format: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            keep_alive: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            messages: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            tools: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
            think: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'model', model)
            __dataclass__object_setattr(self, 'stream', stream)
            __dataclass__object_setattr(self, 'options', options)
            __dataclass__object_setattr(self, 'format', format)
            __dataclass__object_setattr(self, 'keep_alive', keep_alive)
            __dataclass__object_setattr(self, 'messages', messages)
            __dataclass__object_setattr(self, 'tools', tools)
            __dataclass__object_setattr(self, 'think', think)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.model)) is not None:
                parts.append(f"model={s}")
            if (s := __dataclass__repr__default_fn(self.stream)) is not None:
                parts.append(f"stream={s}")
            if (s := __dataclass__repr__default_fn(self.options)) is not None:
                parts.append(f"options={s}")
            if (s := __dataclass__repr__default_fn(self.format)) is not None:
                parts.append(f"format={s}")
            if (s := __dataclass__repr__default_fn(self.keep_alive)) is not None:
                parts.append(f"keep_alive={s}")
            if (s := __dataclass__repr__default_fn(self.messages)) is not None:
                parts.append(f"messages={s}")
            if (s := __dataclass__repr__default_fn(self.tools)) is not None:
                parts.append(f"tools={s}")
            if (s := __dataclass__repr__default_fn(self.think)) is not None:
                parts.append(f"think={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='7d8c7645c771078abaa19f5084e82bcc3547a037',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('model', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('created_at', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('done', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('done_reason', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('total_duration', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('load_duration', True, True, None, True, True, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('prompt_eval_count', True, True, None, True, True, False, None)"
            ", 'instance', 'value', None, False, False, False), (('prompt_eval_duration', True, True, None, True, True,"
            " False, None), 'instance', 'value', None, False, False, False), (('eval_count', True, True, None, True, Tr"
            "ue, False, None), 'instance', 'value', None, False, False, False), (('eval_duration', True, True, None, Tr"
            "ue, True, False, None), 'instance', 'value', None, False, False, False), (('message', True, True, None, Tr"
            "ue, True, False, None), 'instance', 'missing', None, False, False, False)), True, 0, ()), ((False,), (Fals"
            "e,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.interop.ollama.protocol', 'ChatResponse'),
    ),
)
def _process_dataclass__7d8c7645c771078abaa19f5084e82bcc3547a037():
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
                model=self.model,
                created_at=self.created_at,
                done=self.done,
                done_reason=self.done_reason,
                total_duration=self.total_duration,
                load_duration=self.load_duration,
                prompt_eval_count=self.prompt_eval_count,
                prompt_eval_duration=self.prompt_eval_duration,
                eval_count=self.eval_count,
                eval_duration=self.eval_duration,
                message=self.message,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.model == other.model and
                self.created_at == other.created_at and
                self.done == other.done and
                self.done_reason == other.done_reason and
                self.total_duration == other.total_duration and
                self.load_duration == other.load_duration and
                self.prompt_eval_count == other.prompt_eval_count and
                self.prompt_eval_duration == other.prompt_eval_duration and
                self.eval_count == other.eval_count and
                self.eval_duration == other.eval_duration and
                self.message == other.message
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'model',
            'created_at',
            'done',
            'done_reason',
            'total_duration',
            'load_duration',
            'prompt_eval_count',
            'prompt_eval_duration',
            'eval_count',
            'eval_duration',
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
                self.model,
                self.created_at,
                self.done,
                self.done_reason,
                self.total_duration,
                self.load_duration,
                self.prompt_eval_count,
                self.prompt_eval_duration,
                self.eval_count,
                self.eval_duration,
                self.message,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            model: __dataclass__init__fields__00__annotation = __dataclass__init__fields__00__default,
            created_at: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            done: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            done_reason: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            total_duration: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            load_duration: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            prompt_eval_count: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            prompt_eval_duration: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            eval_count: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            eval_duration: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            message: __dataclass__init__fields__10__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'model', model)
            __dataclass__object_setattr(self, 'created_at', created_at)
            __dataclass__object_setattr(self, 'done', done)
            __dataclass__object_setattr(self, 'done_reason', done_reason)
            __dataclass__object_setattr(self, 'total_duration', total_duration)
            __dataclass__object_setattr(self, 'load_duration', load_duration)
            __dataclass__object_setattr(self, 'prompt_eval_count', prompt_eval_count)
            __dataclass__object_setattr(self, 'prompt_eval_duration', prompt_eval_duration)
            __dataclass__object_setattr(self, 'eval_count', eval_count)
            __dataclass__object_setattr(self, 'eval_duration', eval_duration)
            __dataclass__object_setattr(self, 'message', message)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.model)) is not None:
                parts.append(f"model={s}")
            if (s := __dataclass__repr__default_fn(self.created_at)) is not None:
                parts.append(f"created_at={s}")
            if (s := __dataclass__repr__default_fn(self.done)) is not None:
                parts.append(f"done={s}")
            if (s := __dataclass__repr__default_fn(self.done_reason)) is not None:
                parts.append(f"done_reason={s}")
            if (s := __dataclass__repr__default_fn(self.total_duration)) is not None:
                parts.append(f"total_duration={s}")
            if (s := __dataclass__repr__default_fn(self.load_duration)) is not None:
                parts.append(f"load_duration={s}")
            if (s := __dataclass__repr__default_fn(self.prompt_eval_count)) is not None:
                parts.append(f"prompt_eval_count={s}")
            if (s := __dataclass__repr__default_fn(self.prompt_eval_duration)) is not None:
                parts.append(f"prompt_eval_duration={s}")
            if (s := __dataclass__repr__default_fn(self.eval_count)) is not None:
                parts.append(f"eval_count={s}")
            if (s := __dataclass__repr__default_fn(self.eval_duration)) is not None:
                parts.append(f"eval_duration={s}")
            if (s := __dataclass__repr__default_fn(self.message)) is not None:
                parts.append(f"message={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='11b91e515e3154e8483141c961a17e04c312f892',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('model', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('stream', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('options', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('format', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('keep_alive', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('prompt', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('suffix', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('system', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('template', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('context', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('raw', True, True, None, True, True, False, None), 'instance', 'value', None, F"
            "alse, False, False), (('images', True, True, None, True, True, False, None), 'instance', 'value', None, Fa"
            "lse, False, False), (('think', True, True, None, True, True, False, None), 'instance', 'value', None, Fals"
            "e, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,"
            ")))"
        ),
    ),
    cls_names=(
        ('omllm.interop.ollama.protocol', 'GenerateRequest'),
    ),
)
def _process_dataclass__11b91e515e3154e8483141c961a17e04c312f892():
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
                model=self.model,
                stream=self.stream,
                options=self.options,
                format=self.format,
                keep_alive=self.keep_alive,
                prompt=self.prompt,
                suffix=self.suffix,
                system=self.system,
                template=self.template,
                context=self.context,
                raw=self.raw,
                images=self.images,
                think=self.think,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.model == other.model and
                self.stream == other.stream and
                self.options == other.options and
                self.format == other.format and
                self.keep_alive == other.keep_alive and
                self.prompt == other.prompt and
                self.suffix == other.suffix and
                self.system == other.system and
                self.template == other.template and
                self.context == other.context and
                self.raw == other.raw and
                self.images == other.images and
                self.think == other.think
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'model',
            'stream',
            'options',
            'format',
            'keep_alive',
            'prompt',
            'suffix',
            'system',
            'template',
            'context',
            'raw',
            'images',
            'think',
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
                self.model,
                self.stream,
                self.options,
                self.format,
                self.keep_alive,
                self.prompt,
                self.suffix,
                self.system,
                self.template,
                self.context,
                self.raw,
                self.images,
                self.think,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            model: __dataclass__init__fields__00__annotation,
            stream: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            options: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            format: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            keep_alive: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            prompt: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            suffix: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            system: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            template: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            context: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            raw: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            images: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            think: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'model', model)
            __dataclass__object_setattr(self, 'stream', stream)
            __dataclass__object_setattr(self, 'options', options)
            __dataclass__object_setattr(self, 'format', format)
            __dataclass__object_setattr(self, 'keep_alive', keep_alive)
            __dataclass__object_setattr(self, 'prompt', prompt)
            __dataclass__object_setattr(self, 'suffix', suffix)
            __dataclass__object_setattr(self, 'system', system)
            __dataclass__object_setattr(self, 'template', template)
            __dataclass__object_setattr(self, 'context', context)
            __dataclass__object_setattr(self, 'raw', raw)
            __dataclass__object_setattr(self, 'images', images)
            __dataclass__object_setattr(self, 'think', think)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.model)) is not None:
                parts.append(f"model={s}")
            if (s := __dataclass__repr__default_fn(self.stream)) is not None:
                parts.append(f"stream={s}")
            if (s := __dataclass__repr__default_fn(self.options)) is not None:
                parts.append(f"options={s}")
            if (s := __dataclass__repr__default_fn(self.format)) is not None:
                parts.append(f"format={s}")
            if (s := __dataclass__repr__default_fn(self.keep_alive)) is not None:
                parts.append(f"keep_alive={s}")
            if (s := __dataclass__repr__default_fn(self.prompt)) is not None:
                parts.append(f"prompt={s}")
            if (s := __dataclass__repr__default_fn(self.suffix)) is not None:
                parts.append(f"suffix={s}")
            if (s := __dataclass__repr__default_fn(self.system)) is not None:
                parts.append(f"system={s}")
            if (s := __dataclass__repr__default_fn(self.template)) is not None:
                parts.append(f"template={s}")
            if (s := __dataclass__repr__default_fn(self.context)) is not None:
                parts.append(f"context={s}")
            if (s := __dataclass__repr__default_fn(self.raw)) is not None:
                parts.append(f"raw={s}")
            if (s := __dataclass__repr__default_fn(self.images)) is not None:
                parts.append(f"images={s}")
            if (s := __dataclass__repr__default_fn(self.think)) is not None:
                parts.append(f"think={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='7ac60029e02554cc9ad3482e28d115cbe690f5e0',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('model', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('created_at', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('done', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('done_reason', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('total_duration', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('load_duration', True, True, None, True, True, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('prompt_eval_count', True, True, None, True, True, False, None)"
            ", 'instance', 'value', None, False, False, False), (('prompt_eval_duration', True, True, None, True, True,"
            " False, None), 'instance', 'value', None, False, False, False), (('eval_count', True, True, None, True, Tr"
            "ue, False, None), 'instance', 'value', None, False, False, False), (('eval_duration', True, True, None, Tr"
            "ue, True, False, None), 'instance', 'value', None, False, False, False), (('response', True, True, None, T"
            "rue, True, False, None), 'instance', 'missing', None, False, False, False), (('thinking', True, True, None"
            ", True, True, False, None), 'instance', 'value', None, False, False, False), (('context', True, True, None"
            ", True, True, False, None), 'instance', 'value', None, False, False, False)), True, 0, ()), ((False,), (Fa"
            "lse,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.interop.ollama.protocol', 'GenerateResponse'),
    ),
)
def _process_dataclass__7ac60029e02554cc9ad3482e28d115cbe690f5e0():
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
        __dataclass__init__fields__11__annotation = __dataclass__spec.fields[11].annotation
        __dataclass__init__fields__11__default = __dataclass__spec.fields[11].default.must()
        __dataclass__init__fields__12__annotation = __dataclass__spec.fields[12].annotation
        __dataclass__init__fields__12__default = __dataclass__spec.fields[12].default.must()
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
                model=self.model,
                created_at=self.created_at,
                done=self.done,
                done_reason=self.done_reason,
                total_duration=self.total_duration,
                load_duration=self.load_duration,
                prompt_eval_count=self.prompt_eval_count,
                prompt_eval_duration=self.prompt_eval_duration,
                eval_count=self.eval_count,
                eval_duration=self.eval_duration,
                response=self.response,
                thinking=self.thinking,
                context=self.context,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.model == other.model and
                self.created_at == other.created_at and
                self.done == other.done and
                self.done_reason == other.done_reason and
                self.total_duration == other.total_duration and
                self.load_duration == other.load_duration and
                self.prompt_eval_count == other.prompt_eval_count and
                self.prompt_eval_duration == other.prompt_eval_duration and
                self.eval_count == other.eval_count and
                self.eval_duration == other.eval_duration and
                self.response == other.response and
                self.thinking == other.thinking and
                self.context == other.context
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'model',
            'created_at',
            'done',
            'done_reason',
            'total_duration',
            'load_duration',
            'prompt_eval_count',
            'prompt_eval_duration',
            'eval_count',
            'eval_duration',
            'response',
            'thinking',
            'context',
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
                self.model,
                self.created_at,
                self.done,
                self.done_reason,
                self.total_duration,
                self.load_duration,
                self.prompt_eval_count,
                self.prompt_eval_duration,
                self.eval_count,
                self.eval_duration,
                self.response,
                self.thinking,
                self.context,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            model: __dataclass__init__fields__00__annotation = __dataclass__init__fields__00__default,
            created_at: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            done: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            done_reason: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            total_duration: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            load_duration: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            prompt_eval_count: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            prompt_eval_duration: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            eval_count: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            eval_duration: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            response: __dataclass__init__fields__10__annotation,
            thinking: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            context: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'model', model)
            __dataclass__object_setattr(self, 'created_at', created_at)
            __dataclass__object_setattr(self, 'done', done)
            __dataclass__object_setattr(self, 'done_reason', done_reason)
            __dataclass__object_setattr(self, 'total_duration', total_duration)
            __dataclass__object_setattr(self, 'load_duration', load_duration)
            __dataclass__object_setattr(self, 'prompt_eval_count', prompt_eval_count)
            __dataclass__object_setattr(self, 'prompt_eval_duration', prompt_eval_duration)
            __dataclass__object_setattr(self, 'eval_count', eval_count)
            __dataclass__object_setattr(self, 'eval_duration', eval_duration)
            __dataclass__object_setattr(self, 'response', response)
            __dataclass__object_setattr(self, 'thinking', thinking)
            __dataclass__object_setattr(self, 'context', context)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.model)) is not None:
                parts.append(f"model={s}")
            if (s := __dataclass__repr__default_fn(self.created_at)) is not None:
                parts.append(f"created_at={s}")
            if (s := __dataclass__repr__default_fn(self.done)) is not None:
                parts.append(f"done={s}")
            if (s := __dataclass__repr__default_fn(self.done_reason)) is not None:
                parts.append(f"done_reason={s}")
            if (s := __dataclass__repr__default_fn(self.total_duration)) is not None:
                parts.append(f"total_duration={s}")
            if (s := __dataclass__repr__default_fn(self.load_duration)) is not None:
                parts.append(f"load_duration={s}")
            if (s := __dataclass__repr__default_fn(self.prompt_eval_count)) is not None:
                parts.append(f"prompt_eval_count={s}")
            if (s := __dataclass__repr__default_fn(self.prompt_eval_duration)) is not None:
                parts.append(f"prompt_eval_duration={s}")
            if (s := __dataclass__repr__default_fn(self.eval_count)) is not None:
                parts.append(f"eval_count={s}")
            if (s := __dataclass__repr__default_fn(self.eval_duration)) is not None:
                parts.append(f"eval_duration={s}")
            if (s := __dataclass__repr__default_fn(self.response)) is not None:
                parts.append(f"response={s}")
            if (s := __dataclass__repr__default_fn(self.thinking)) is not None:
                parts.append(f"thinking={s}")
            if (s := __dataclass__repr__default_fn(self.context)) is not None:
                parts.append(f"context={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='7bc1bedc97cae3cf6bc291cf4d9e3cf0dbc833df',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('name', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('model', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('remote_model', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('remote_host', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('modified_at', True, True, None, True, True, False, None), 'instance',"
            " 'missing', None, False, False, False), (('size', True, True, None, True, True, False, None), 'instance', "
            "'missing', None, False, False, False), (('digest', True, True, None, True, True, False, None), 'instance',"
            " 'missing', None, False, False, False), (('details', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ("
            ")), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.interop.ollama.protocol', 'ListModelResponse'),
    ),
)
def _process_dataclass__7bc1bedc97cae3cf6bc291cf4d9e3cf0dbc833df():
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
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__7__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__7__default = __dataclass__spec.fields[7].default.must()
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
                model=self.model,
                remote_model=self.remote_model,
                remote_host=self.remote_host,
                modified_at=self.modified_at,
                size=self.size,
                digest=self.digest,
                details=self.details,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.model == other.model and
                self.remote_model == other.remote_model and
                self.remote_host == other.remote_host and
                self.modified_at == other.modified_at and
                self.size == other.size and
                self.digest == other.digest and
                self.details == other.details
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'model',
            'remote_model',
            'remote_host',
            'modified_at',
            'size',
            'digest',
            'details',
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
                self.model,
                self.remote_model,
                self.remote_host,
                self.modified_at,
                self.size,
                self.digest,
                self.details,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            name: __dataclass__init__fields__0__annotation,
            model: __dataclass__init__fields__1__annotation,
            remote_model: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            remote_host: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            modified_at: __dataclass__init__fields__4__annotation,
            size: __dataclass__init__fields__5__annotation,
            digest: __dataclass__init__fields__6__annotation,
            details: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'model', model)
            __dataclass__object_setattr(self, 'remote_model', remote_model)
            __dataclass__object_setattr(self, 'remote_host', remote_host)
            __dataclass__object_setattr(self, 'modified_at', modified_at)
            __dataclass__object_setattr(self, 'size', size)
            __dataclass__object_setattr(self, 'digest', digest)
            __dataclass__object_setattr(self, 'details', details)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.name)) is not None:
                parts.append(f"name={s}")
            if (s := __dataclass__repr__default_fn(self.model)) is not None:
                parts.append(f"model={s}")
            if (s := __dataclass__repr__default_fn(self.remote_model)) is not None:
                parts.append(f"remote_model={s}")
            if (s := __dataclass__repr__default_fn(self.remote_host)) is not None:
                parts.append(f"remote_host={s}")
            if (s := __dataclass__repr__default_fn(self.modified_at)) is not None:
                parts.append(f"modified_at={s}")
            if (s := __dataclass__repr__default_fn(self.size)) is not None:
                parts.append(f"size={s}")
            if (s := __dataclass__repr__default_fn(self.digest)) is not None:
                parts.append(f"digest={s}")
            if (s := __dataclass__repr__default_fn(self.details)) is not None:
                parts.append(f"details={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='7f214bdbe37ae6274b98e86327365fdf2dc65047',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('role', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('content', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('thinking', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('images', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('tool_name', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('tool_calls', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.interop.ollama.protocol', 'Message'),
    ),
)
def _process_dataclass__7f214bdbe37ae6274b98e86327365fdf2dc65047():
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
                role=self.role,
                content=self.content,
                thinking=self.thinking,
                images=self.images,
                tool_name=self.tool_name,
                tool_calls=self.tool_calls,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.role == other.role and
                self.content == other.content and
                self.thinking == other.thinking and
                self.images == other.images and
                self.tool_name == other.tool_name and
                self.tool_calls == other.tool_calls
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'role',
            'content',
            'thinking',
            'images',
            'tool_name',
            'tool_calls',
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
                self.role,
                self.content,
                self.thinking,
                self.images,
                self.tool_name,
                self.tool_calls,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            role: __dataclass__init__fields__0__annotation,
            content: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            thinking: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            images: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            tool_name: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            tool_calls: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'role', role)
            __dataclass__object_setattr(self, 'content', content)
            __dataclass__object_setattr(self, 'thinking', thinking)
            __dataclass__object_setattr(self, 'images', images)
            __dataclass__object_setattr(self, 'tool_name', tool_name)
            __dataclass__object_setattr(self, 'tool_calls', tool_calls)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.role)) is not None:
                parts.append(f"role={s}")
            if (s := __dataclass__repr__default_fn(self.content)) is not None:
                parts.append(f"content={s}")
            if (s := __dataclass__repr__default_fn(self.thinking)) is not None:
                parts.append(f"thinking={s}")
            if (s := __dataclass__repr__default_fn(self.images)) is not None:
                parts.append(f"images={s}")
            if (s := __dataclass__repr__default_fn(self.tool_name)) is not None:
                parts.append(f"tool_name={s}")
            if (s := __dataclass__repr__default_fn(self.tool_calls)) is not None:
                parts.append(f"tool_calls={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='398df87b16f8f43b9953996d20e3abeee402adc7',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('id', True, True, None, True, True, False, None), 'instance', 'value', None, F"
            "alse, False, False), (('function', True, True, None, True, True, False, None), 'instance', 'missing', None"
            ", False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), "
            "(False,)))"
        ),
    ),
    cls_names=(
        ('omllm.interop.ollama.protocol', 'Message.ToolCall'),
    ),
)
def _process_dataclass__398df87b16f8f43b9953996d20e3abeee402adc7():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default = __dataclass__spec.fields[0].default.must()
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
                id=self.id,
                function=self.function,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.id == other.id and
                self.function == other.function
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'id',
            'function',
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
                self.id,
                self.function,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            id: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            function: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'id', id)
            __dataclass__object_setattr(self, 'function', function)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"id={self.id!r}")
            parts.append(f"function={self.function!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e14f6abb8bbef8dc989aadfb3cc47c65d6e7ba72',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('name', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('arguments', True, True, None, True, True, False, None), 'instance', 'missing',"
            " None, False, False, False), (('index', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.interop.ollama.protocol', 'Message.ToolCall.Function'),
    ),
)
def _process_dataclass__e14f6abb8bbef8dc989aadfb3cc47c65d6e7ba72():
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
                arguments=self.arguments,
                index=self.index,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.arguments == other.arguments and
                self.index == other.index
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'arguments',
            'index',
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
                self.arguments,
                self.index,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            name: __dataclass__init__fields__0__annotation,
            arguments: __dataclass__init__fields__1__annotation,
            index: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'arguments', arguments)
            __dataclass__object_setattr(self, 'index', index)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"arguments={self.arguments!r}")
            parts.append(f"index={self.index!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='4962813809665b0d5ab7a2faed29cdaab7c7ef69',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('parent_model', True, True, None, True, True, False, None), 'instance', 'missi"
            "ng', None, False, False, False), (('format', True, True, None, True, True, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('family', True, True, None, True, True, False, None), 'instance', 'mis"
            "sing', None, False, False, False), (('families', True, True, None, True, True, False, None), 'instance', '"
            "missing', None, False, False, False), (('parameter_size', True, True, None, True, True, False, None), 'ins"
            "tance', 'missing', None, False, False, False), (('quantization_level', True, True, None, True, True, False"
            ", None), 'instance', 'missing', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False"
            ",), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.interop.ollama.protocol', 'ModelDetails'),
    ),
)
def _process_dataclass__4962813809665b0d5ab7a2faed29cdaab7c7ef69():
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
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
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
                parent_model=self.parent_model,
                format=self.format,
                family=self.family,
                families=self.families,
                parameter_size=self.parameter_size,
                quantization_level=self.quantization_level,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.parent_model == other.parent_model and
                self.format == other.format and
                self.family == other.family and
                self.families == other.families and
                self.parameter_size == other.parameter_size and
                self.quantization_level == other.quantization_level
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'parent_model',
            'format',
            'family',
            'families',
            'parameter_size',
            'quantization_level',
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
                self.parent_model,
                self.format,
                self.family,
                self.families,
                self.parameter_size,
                self.quantization_level,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            parent_model: __dataclass__init__fields__0__annotation,
            format: __dataclass__init__fields__1__annotation,
            family: __dataclass__init__fields__2__annotation,
            families: __dataclass__init__fields__3__annotation,
            parameter_size: __dataclass__init__fields__4__annotation,
            quantization_level: __dataclass__init__fields__5__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'parent_model', parent_model)
            __dataclass__object_setattr(self, 'format', format)
            __dataclass__object_setattr(self, 'family', family)
            __dataclass__object_setattr(self, 'families', families)
            __dataclass__object_setattr(self, 'parameter_size', parameter_size)
            __dataclass__object_setattr(self, 'quantization_level', quantization_level)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.parent_model)) is not None:
                parts.append(f"parent_model={s}")
            if (s := __dataclass__repr__default_fn(self.format)) is not None:
                parts.append(f"format={s}")
            if (s := __dataclass__repr__default_fn(self.family)) is not None:
                parts.append(f"family={s}")
            if (s := __dataclass__repr__default_fn(self.families)) is not None:
                parts.append(f"families={s}")
            if (s := __dataclass__repr__default_fn(self.parameter_size)) is not None:
                parts.append(f"parameter_size={s}")
            if (s := __dataclass__repr__default_fn(self.quantization_level)) is not None:
                parts.append(f"quantization_level={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='2001158470a2091f2a50cf47e99d5574ff1e5d72',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('numa', True, True, None, True, True, False, None), 'instance', 'value', None,"
            " False, False, False), (('num_ctx', True, True, None, True, True, False, None), 'instance', 'value', None,"
            " False, False, False), (('num_batch', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('num_gpu', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('main_gpu', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('low_vram', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('f16_kv', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('logits_all', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('vocab_only', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('use_mmap', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('use_mlock', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('embedding_only', True, True, None, True, True, False, None), 'instan"
            "ce', 'value', None, False, False, False), (('num_thread', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('num_keep', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('seed', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('num_predict', True, True, None, True, True, False, None), 'i"
            "nstance', 'value', None, False, False, False), (('top_k', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('top_p', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('tfs_z', True, True, None, True, True, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('typical_p', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('repeat_last_n', True, True, None, True, True, False, None), "
            "'instance', 'value', None, False, False, False), (('temperature', True, True, None, True, True, False, Non"
            "e), 'instance', 'value', None, False, False, False), (('repeat_penalty', True, True, None, True, True, Fal"
            "se, None), 'instance', 'value', None, False, False, False), (('presence_penalty', True, True, None, True, "
            "True, False, None), 'instance', 'value', None, False, False, False), (('frequency_penalty', True, True, No"
            "ne, True, True, False, None), 'instance', 'value', None, False, False, False), (('mirostat', True, True, N"
            "one, True, True, False, None), 'instance', 'value', None, False, False, False), (('mirostat_tau', True, Tr"
            "ue, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('mirostat_eta', Tru"
            "e, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('penalize_newl"
            "ine', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('stop"
            "', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False)), True, 0, "
            "()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.interop.ollama.protocol', 'Options'),
    ),
)
def _process_dataclass__2001158470a2091f2a50cf47e99d5574ff1e5d72():
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
        __dataclass__init__fields__13__annotation = __dataclass__spec.fields[13].annotation
        __dataclass__init__fields__13__default = __dataclass__spec.fields[13].default.must()
        __dataclass__init__fields__14__annotation = __dataclass__spec.fields[14].annotation
        __dataclass__init__fields__14__default = __dataclass__spec.fields[14].default.must()
        __dataclass__init__fields__15__annotation = __dataclass__spec.fields[15].annotation
        __dataclass__init__fields__15__default = __dataclass__spec.fields[15].default.must()
        __dataclass__init__fields__16__annotation = __dataclass__spec.fields[16].annotation
        __dataclass__init__fields__16__default = __dataclass__spec.fields[16].default.must()
        __dataclass__init__fields__17__annotation = __dataclass__spec.fields[17].annotation
        __dataclass__init__fields__17__default = __dataclass__spec.fields[17].default.must()
        __dataclass__init__fields__18__annotation = __dataclass__spec.fields[18].annotation
        __dataclass__init__fields__18__default = __dataclass__spec.fields[18].default.must()
        __dataclass__init__fields__19__annotation = __dataclass__spec.fields[19].annotation
        __dataclass__init__fields__19__default = __dataclass__spec.fields[19].default.must()
        __dataclass__init__fields__20__annotation = __dataclass__spec.fields[20].annotation
        __dataclass__init__fields__20__default = __dataclass__spec.fields[20].default.must()
        __dataclass__init__fields__21__annotation = __dataclass__spec.fields[21].annotation
        __dataclass__init__fields__21__default = __dataclass__spec.fields[21].default.must()
        __dataclass__init__fields__22__annotation = __dataclass__spec.fields[22].annotation
        __dataclass__init__fields__22__default = __dataclass__spec.fields[22].default.must()
        __dataclass__init__fields__23__annotation = __dataclass__spec.fields[23].annotation
        __dataclass__init__fields__23__default = __dataclass__spec.fields[23].default.must()
        __dataclass__init__fields__24__annotation = __dataclass__spec.fields[24].annotation
        __dataclass__init__fields__24__default = __dataclass__spec.fields[24].default.must()
        __dataclass__init__fields__25__annotation = __dataclass__spec.fields[25].annotation
        __dataclass__init__fields__25__default = __dataclass__spec.fields[25].default.must()
        __dataclass__init__fields__26__annotation = __dataclass__spec.fields[26].annotation
        __dataclass__init__fields__26__default = __dataclass__spec.fields[26].default.must()
        __dataclass__init__fields__27__annotation = __dataclass__spec.fields[27].annotation
        __dataclass__init__fields__27__default = __dataclass__spec.fields[27].default.must()
        __dataclass__init__fields__28__annotation = __dataclass__spec.fields[28].annotation
        __dataclass__init__fields__28__default = __dataclass__spec.fields[28].default.must()
        __dataclass__init__fields__29__annotation = __dataclass__spec.fields[29].annotation
        __dataclass__init__fields__29__default = __dataclass__spec.fields[29].default.must()
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
                numa=self.numa,
                num_ctx=self.num_ctx,
                num_batch=self.num_batch,
                num_gpu=self.num_gpu,
                main_gpu=self.main_gpu,
                low_vram=self.low_vram,
                f16_kv=self.f16_kv,
                logits_all=self.logits_all,
                vocab_only=self.vocab_only,
                use_mmap=self.use_mmap,
                use_mlock=self.use_mlock,
                embedding_only=self.embedding_only,
                num_thread=self.num_thread,
                num_keep=self.num_keep,
                seed=self.seed,
                num_predict=self.num_predict,
                top_k=self.top_k,
                top_p=self.top_p,
                tfs_z=self.tfs_z,
                typical_p=self.typical_p,
                repeat_last_n=self.repeat_last_n,
                temperature=self.temperature,
                repeat_penalty=self.repeat_penalty,
                presence_penalty=self.presence_penalty,
                frequency_penalty=self.frequency_penalty,
                mirostat=self.mirostat,
                mirostat_tau=self.mirostat_tau,
                mirostat_eta=self.mirostat_eta,
                penalize_newline=self.penalize_newline,
                stop=self.stop,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.numa == other.numa and
                self.num_ctx == other.num_ctx and
                self.num_batch == other.num_batch and
                self.num_gpu == other.num_gpu and
                self.main_gpu == other.main_gpu and
                self.low_vram == other.low_vram and
                self.f16_kv == other.f16_kv and
                self.logits_all == other.logits_all and
                self.vocab_only == other.vocab_only and
                self.use_mmap == other.use_mmap and
                self.use_mlock == other.use_mlock and
                self.embedding_only == other.embedding_only and
                self.num_thread == other.num_thread and
                self.num_keep == other.num_keep and
                self.seed == other.seed and
                self.num_predict == other.num_predict and
                self.top_k == other.top_k and
                self.top_p == other.top_p and
                self.tfs_z == other.tfs_z and
                self.typical_p == other.typical_p and
                self.repeat_last_n == other.repeat_last_n and
                self.temperature == other.temperature and
                self.repeat_penalty == other.repeat_penalty and
                self.presence_penalty == other.presence_penalty and
                self.frequency_penalty == other.frequency_penalty and
                self.mirostat == other.mirostat and
                self.mirostat_tau == other.mirostat_tau and
                self.mirostat_eta == other.mirostat_eta and
                self.penalize_newline == other.penalize_newline and
                self.stop == other.stop
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'numa',
            'num_ctx',
            'num_batch',
            'num_gpu',
            'main_gpu',
            'low_vram',
            'f16_kv',
            'logits_all',
            'vocab_only',
            'use_mmap',
            'use_mlock',
            'embedding_only',
            'num_thread',
            'num_keep',
            'seed',
            'num_predict',
            'top_k',
            'top_p',
            'tfs_z',
            'typical_p',
            'repeat_last_n',
            'temperature',
            'repeat_penalty',
            'presence_penalty',
            'frequency_penalty',
            'mirostat',
            'mirostat_tau',
            'mirostat_eta',
            'penalize_newline',
            'stop',
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
                self.numa,
                self.num_ctx,
                self.num_batch,
                self.num_gpu,
                self.main_gpu,
                self.low_vram,
                self.f16_kv,
                self.logits_all,
                self.vocab_only,
                self.use_mmap,
                self.use_mlock,
                self.embedding_only,
                self.num_thread,
                self.num_keep,
                self.seed,
                self.num_predict,
                self.top_k,
                self.top_p,
                self.tfs_z,
                self.typical_p,
                self.repeat_last_n,
                self.temperature,
                self.repeat_penalty,
                self.presence_penalty,
                self.frequency_penalty,
                self.mirostat,
                self.mirostat_tau,
                self.mirostat_eta,
                self.penalize_newline,
                self.stop,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            numa: __dataclass__init__fields__00__annotation = __dataclass__init__fields__00__default,
            num_ctx: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            num_batch: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            num_gpu: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            main_gpu: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            low_vram: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            f16_kv: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            logits_all: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            vocab_only: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            use_mmap: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            use_mlock: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            embedding_only: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            num_thread: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            num_keep: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            seed: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            num_predict: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            top_k: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            top_p: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
            tfs_z: __dataclass__init__fields__18__annotation = __dataclass__init__fields__18__default,
            typical_p: __dataclass__init__fields__19__annotation = __dataclass__init__fields__19__default,
            repeat_last_n: __dataclass__init__fields__20__annotation = __dataclass__init__fields__20__default,
            temperature: __dataclass__init__fields__21__annotation = __dataclass__init__fields__21__default,
            repeat_penalty: __dataclass__init__fields__22__annotation = __dataclass__init__fields__22__default,
            presence_penalty: __dataclass__init__fields__23__annotation = __dataclass__init__fields__23__default,
            frequency_penalty: __dataclass__init__fields__24__annotation = __dataclass__init__fields__24__default,
            mirostat: __dataclass__init__fields__25__annotation = __dataclass__init__fields__25__default,
            mirostat_tau: __dataclass__init__fields__26__annotation = __dataclass__init__fields__26__default,
            mirostat_eta: __dataclass__init__fields__27__annotation = __dataclass__init__fields__27__default,
            penalize_newline: __dataclass__init__fields__28__annotation = __dataclass__init__fields__28__default,
            stop: __dataclass__init__fields__29__annotation = __dataclass__init__fields__29__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'numa', numa)
            __dataclass__object_setattr(self, 'num_ctx', num_ctx)
            __dataclass__object_setattr(self, 'num_batch', num_batch)
            __dataclass__object_setattr(self, 'num_gpu', num_gpu)
            __dataclass__object_setattr(self, 'main_gpu', main_gpu)
            __dataclass__object_setattr(self, 'low_vram', low_vram)
            __dataclass__object_setattr(self, 'f16_kv', f16_kv)
            __dataclass__object_setattr(self, 'logits_all', logits_all)
            __dataclass__object_setattr(self, 'vocab_only', vocab_only)
            __dataclass__object_setattr(self, 'use_mmap', use_mmap)
            __dataclass__object_setattr(self, 'use_mlock', use_mlock)
            __dataclass__object_setattr(self, 'embedding_only', embedding_only)
            __dataclass__object_setattr(self, 'num_thread', num_thread)
            __dataclass__object_setattr(self, 'num_keep', num_keep)
            __dataclass__object_setattr(self, 'seed', seed)
            __dataclass__object_setattr(self, 'num_predict', num_predict)
            __dataclass__object_setattr(self, 'top_k', top_k)
            __dataclass__object_setattr(self, 'top_p', top_p)
            __dataclass__object_setattr(self, 'tfs_z', tfs_z)
            __dataclass__object_setattr(self, 'typical_p', typical_p)
            __dataclass__object_setattr(self, 'repeat_last_n', repeat_last_n)
            __dataclass__object_setattr(self, 'temperature', temperature)
            __dataclass__object_setattr(self, 'repeat_penalty', repeat_penalty)
            __dataclass__object_setattr(self, 'presence_penalty', presence_penalty)
            __dataclass__object_setattr(self, 'frequency_penalty', frequency_penalty)
            __dataclass__object_setattr(self, 'mirostat', mirostat)
            __dataclass__object_setattr(self, 'mirostat_tau', mirostat_tau)
            __dataclass__object_setattr(self, 'mirostat_eta', mirostat_eta)
            __dataclass__object_setattr(self, 'penalize_newline', penalize_newline)
            __dataclass__object_setattr(self, 'stop', stop)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.numa)) is not None:
                parts.append(f"numa={s}")
            if (s := __dataclass__repr__default_fn(self.num_ctx)) is not None:
                parts.append(f"num_ctx={s}")
            if (s := __dataclass__repr__default_fn(self.num_batch)) is not None:
                parts.append(f"num_batch={s}")
            if (s := __dataclass__repr__default_fn(self.num_gpu)) is not None:
                parts.append(f"num_gpu={s}")
            if (s := __dataclass__repr__default_fn(self.main_gpu)) is not None:
                parts.append(f"main_gpu={s}")
            if (s := __dataclass__repr__default_fn(self.low_vram)) is not None:
                parts.append(f"low_vram={s}")
            if (s := __dataclass__repr__default_fn(self.f16_kv)) is not None:
                parts.append(f"f16_kv={s}")
            if (s := __dataclass__repr__default_fn(self.logits_all)) is not None:
                parts.append(f"logits_all={s}")
            if (s := __dataclass__repr__default_fn(self.vocab_only)) is not None:
                parts.append(f"vocab_only={s}")
            if (s := __dataclass__repr__default_fn(self.use_mmap)) is not None:
                parts.append(f"use_mmap={s}")
            if (s := __dataclass__repr__default_fn(self.use_mlock)) is not None:
                parts.append(f"use_mlock={s}")
            if (s := __dataclass__repr__default_fn(self.embedding_only)) is not None:
                parts.append(f"embedding_only={s}")
            if (s := __dataclass__repr__default_fn(self.num_thread)) is not None:
                parts.append(f"num_thread={s}")
            if (s := __dataclass__repr__default_fn(self.num_keep)) is not None:
                parts.append(f"num_keep={s}")
            if (s := __dataclass__repr__default_fn(self.seed)) is not None:
                parts.append(f"seed={s}")
            if (s := __dataclass__repr__default_fn(self.num_predict)) is not None:
                parts.append(f"num_predict={s}")
            if (s := __dataclass__repr__default_fn(self.top_k)) is not None:
                parts.append(f"top_k={s}")
            if (s := __dataclass__repr__default_fn(self.top_p)) is not None:
                parts.append(f"top_p={s}")
            if (s := __dataclass__repr__default_fn(self.tfs_z)) is not None:
                parts.append(f"tfs_z={s}")
            if (s := __dataclass__repr__default_fn(self.typical_p)) is not None:
                parts.append(f"typical_p={s}")
            if (s := __dataclass__repr__default_fn(self.repeat_last_n)) is not None:
                parts.append(f"repeat_last_n={s}")
            if (s := __dataclass__repr__default_fn(self.temperature)) is not None:
                parts.append(f"temperature={s}")
            if (s := __dataclass__repr__default_fn(self.repeat_penalty)) is not None:
                parts.append(f"repeat_penalty={s}")
            if (s := __dataclass__repr__default_fn(self.presence_penalty)) is not None:
                parts.append(f"presence_penalty={s}")
            if (s := __dataclass__repr__default_fn(self.frequency_penalty)) is not None:
                parts.append(f"frequency_penalty={s}")
            if (s := __dataclass__repr__default_fn(self.mirostat)) is not None:
                parts.append(f"mirostat={s}")
            if (s := __dataclass__repr__default_fn(self.mirostat_tau)) is not None:
                parts.append(f"mirostat_tau={s}")
            if (s := __dataclass__repr__default_fn(self.mirostat_eta)) is not None:
                parts.append(f"mirostat_eta={s}")
            if (s := __dataclass__repr__default_fn(self.penalize_newline)) is not None:
                parts.append(f"penalize_newline={s}")
            if (s := __dataclass__repr__default_fn(self.stop)) is not None:
                parts.append(f"stop={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='201e8130161d0c81b93711fa61446ee8b1df2e39',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('type', True, True, None, True, True, False, None), 'instance', 'value', None,"
            " False, False, False), (('function', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), ("
            "False,)))"
        ),
    ),
    cls_names=(
        ('omllm.interop.ollama.protocol', 'Tool'),
    ),
)
def _process_dataclass__201e8130161d0c81b93711fa61446ee8b1df2e39():
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
                type=self.type,
                function=self.function,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.type == other.type and
                self.function == other.function
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'type',
            'function',
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
                self.function,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            type: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            function: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'type', type)
            __dataclass__object_setattr(self, 'function', function)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.type)) is not None:
                parts.append(f"type={s}")
            if (s := __dataclass__repr__default_fn(self.function)) is not None:
                parts.append(f"function={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='4c0c88424936dfc689da9d4cf5078fd4c445db95',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('name', True, True, None, True, True, False, None), 'instance', 'value', None,"
            " False, False, False), (('description', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('parameters', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.interop.ollama.protocol', 'Tool.Function'),
    ),
)
def _process_dataclass__4c0c88424936dfc689da9d4cf5078fd4c445db95():
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
                name=self.name,
                description=self.description,
                parameters=self.parameters,
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
                self.parameters == other.parameters
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'description',
            'parameters',
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
                self.parameters,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            name: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            description: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            parameters: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'description', description)
            __dataclass__object_setattr(self, 'parameters', parameters)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.name)) is not None:
                parts.append(f"name={s}")
            if (s := __dataclass__repr__default_fn(self.description)) is not None:
                parts.append(f"description={s}")
            if (s := __dataclass__repr__default_fn(self.parameters)) is not None:
                parts.append(f"parameters={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
