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


IMPLEMENTATION_KEY = '0bbef0e54293e6dab1d0e699c31ca637b42078baf288201f600000b591c92b24'


@_register(
    installer_sha1='99cc714a1fb5115f9896d7c3a83918ccaa3cb9cd',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('input', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('input_cached', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('input_cache_write', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, False, False, False), (('output', True, True, None, True, True, False, None), 'instance',"
            " 'value', None, False, False, False), (('reasoning', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('context_input', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('context_limit', True, True, None, True, True, False, None"
            "), 'instance', 'value', None, False, False, False), (('context_estimated', True, True, None, True, True, F"
            "alse, None), 'instance', 'value', None, False, False, False), (('_SUFFIXES', True, True, None, True, None,"
            " False, None), 'class_var', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), "
            "(False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.ui.tui.minitui.app', 'MinituiChatApp.Usage'),
    ),
)
def _process_dataclass__99cc714a1fb5115f9896d7c3a83918ccaa3cb9cd():
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
        __dataclass__init__fields__7__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__7__default = __dataclass__spec.fields[7].default.must()
        __dataclass__init__fields__8__annotation = __dataclass__spec.fields[8].annotation
        __dataclass__init__fields__8__default = __dataclass__spec.fields[8].default.must()
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
                input_cached=self.input_cached,
                input_cache_write=self.input_cache_write,
                output=self.output,
                reasoning=self.reasoning,
                context_input=self.context_input,
                context_limit=self.context_limit,
                context_estimated=self.context_estimated,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.input == other.input and
                self.input_cached == other.input_cached and
                self.input_cache_write == other.input_cache_write and
                self.output == other.output and
                self.reasoning == other.reasoning and
                self.context_input == other.context_input and
                self.context_limit == other.context_limit and
                self.context_estimated == other.context_estimated
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'input',
            'input_cached',
            'input_cache_write',
            'output',
            'reasoning',
            'context_input',
            'context_limit',
            'context_estimated',
            '_SUFFIXES',
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
                self.input_cached,
                self.input_cache_write,
                self.output,
                self.reasoning,
                self.context_input,
                self.context_limit,
                self.context_estimated,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            input: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            input_cached: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            input_cache_write: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            output: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            reasoning: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            context_input: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            context_limit: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
            context_estimated: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'input', input)
            __dataclass__object_setattr(self, 'input_cached', input_cached)
            __dataclass__object_setattr(self, 'input_cache_write', input_cache_write)
            __dataclass__object_setattr(self, 'output', output)
            __dataclass__object_setattr(self, 'reasoning', reasoning)
            __dataclass__object_setattr(self, 'context_input', context_input)
            __dataclass__object_setattr(self, 'context_limit', context_limit)
            __dataclass__object_setattr(self, 'context_estimated', context_estimated)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"input={self.input!r}")
            parts.append(f"input_cached={self.input_cached!r}")
            parts.append(f"input_cache_write={self.input_cache_write!r}")
            parts.append(f"output={self.output!r}")
            parts.append(f"reasoning={self.reasoning!r}")
            parts.append(f"context_input={self.context_input!r}")
            parts.append(f"context_limit={self.context_limit!r}")
            parts.append(f"context_estimated={self.context_estimated!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='7c8419065adf03ae4b9b38b00947afbeac0905ea',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('speaker', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('at', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('text', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.ui.tui.minitui.app', 'TurnRecord'),
    ),
)
def _process_dataclass__7c8419065adf03ae4b9b38b00947afbeac0905ea():
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
                speaker=self.speaker,
                at=self.at,
                text=self.text,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.speaker == other.speaker and
                self.at == other.at and
                self.text == other.text
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'speaker',
            'at',
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
                self.speaker,
                self.at,
                self.text,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            speaker: __dataclass__init__fields__0__annotation,
            at: __dataclass__init__fields__1__annotation,
            text: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'speaker', speaker)
            __dataclass__object_setattr(self, 'at', at)
            __dataclass__object_setattr(self, 'text', text)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"speaker={self.speaker!r}")
            parts.append(f"at={self.at!r}")
            parts.append(f"text={self.text!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='aa668fdad59913367e4c9a882d6a0f66a504904c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('key', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('title', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('call_summary', True, True, None, True, False, False, None), 'instance', 'mis"
            "sing', None, False, False, False), (('detail', True, True, None, True, False, False, None), 'instance', 'm"
            "issing', None, False, False, False), (('on_respond', True, True, None, True, False, False, None), 'instanc"
            "e', 'missing', None, False, False, False), (('on_cancel', True, True, None, True, False, False, None), 'in"
            "stance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, F"
            "alse, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.ui.tui.minitui.app', '_PermissionCardRequest'),
    ),
)
def _process_dataclass__aa668fdad59913367e4c9a882d6a0f66a504904c():
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
                key=self.key,
                title=self.title,
                call_summary=self.call_summary,
                detail=self.detail,
                on_respond=self.on_respond,
                on_cancel=self.on_cancel,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.key == other.key and
                self.title == other.title and
                self.call_summary == other.call_summary and
                self.detail == other.detail and
                self.on_respond == other.on_respond and
                self.on_cancel == other.on_cancel
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'key',
            'title',
            'call_summary',
            'detail',
            'on_respond',
            'on_cancel',
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
                self.title,
                self.call_summary,
                self.detail,
                self.on_respond,
                self.on_cancel,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            key: __dataclass__init__fields__0__annotation,
            title: __dataclass__init__fields__1__annotation,
            call_summary: __dataclass__init__fields__2__annotation,
            detail: __dataclass__init__fields__3__annotation,
            on_respond: __dataclass__init__fields__4__annotation,
            on_cancel: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'title', title)
            __dataclass__object_setattr(self, 'call_summary', call_summary)
            __dataclass__object_setattr(self, 'detail', detail)
            __dataclass__object_setattr(self, 'on_respond', on_respond)
            __dataclass__object_setattr(self, 'on_cancel', on_cancel)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"key={self.key!r}")
            parts.append(f"title={self.title!r}")
            parts.append(f"call_summary={self.call_summary!r}")
            parts.append(f"detail={self.detail!r}")
            parts.append(f"on_respond={self.on_respond!r}")
            parts.append(f"on_cancel={self.on_cancel!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d39348b3936a059efcf9d01ff2133be25a6045d1',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('title', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('call_summary', True, True, None, True, False, False, None), 'instance', 'm"
            "issing', None, False, False, False), (('base_detail', True, True, None, True, False, False, None), 'instan"
            "ce', 'missing', None, False, False, False), (('card', True, True, None, True, False, False, None), 'instan"
            "ce', 'missing', None, False, False, False), (('ready_to_finalize', True, True, None, True, False, False, N"
            "one), 'instance', 'value', None, False, False, False), (('finalize_timer', True, True, None, True, False, "
            "False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (F"
            "alse,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.ui.tui.minitui.app', '_ToolCardEntry'),
    ),
)
def _process_dataclass__d39348b3936a059efcf9d01ff2133be25a6045d1():
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
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__default = __dataclass__spec.fields[5].default.must()
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                title=self.title,
                call_summary=self.call_summary,
                base_detail=self.base_detail,
                card=self.card,
                ready_to_finalize=self.ready_to_finalize,
                finalize_timer=self.finalize_timer,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.title == other.title and
                self.call_summary == other.call_summary and
                self.base_detail == other.base_detail and
                self.card == other.card and
                self.ready_to_finalize == other.ready_to_finalize and
                self.finalize_timer == other.finalize_timer
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            title: __dataclass__init__fields__0__annotation,
            call_summary: __dataclass__init__fields__1__annotation,
            base_detail: __dataclass__init__fields__2__annotation,
            card: __dataclass__init__fields__3__annotation,
            ready_to_finalize: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            finalize_timer: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            self.title = title
            self.call_summary = call_summary
            self.base_detail = base_detail
            self.card = card
            self.ready_to_finalize = ready_to_finalize
            self.finalize_timer = finalize_timer

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"title={self.title!r}")
            parts.append(f"call_summary={self.call_summary!r}")
            parts.append(f"base_detail={self.base_detail!r}")
            parts.append(f"card={self.card!r}")
            parts.append(f"ready_to_finalize={self.ready_to_finalize!r}")
            parts.append(f"finalize_timer={self.finalize_timer!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
