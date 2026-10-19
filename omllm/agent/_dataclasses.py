# @om-generated
# type: ignore
# ruff: noqa
# flake8: noqa


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
    installer_sha1='0bbc572461db0e8cf0bb47b4bfb151a4488764ea',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('location', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (()"
            ",), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.dummy.weather', 'GetWeatherParams'),
    ),
)
def _process_dataclass__0bbc572461db0e8cf0bb47b4bfb151a4488764ea():
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
                location=self.location,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.location == other.location
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'location',
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
                self.location,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            location: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'location', location)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"location={self.location!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='018fdc061046af08399a06df8437ed8b94609eb6',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('context', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False), (('llm_context', True, True, None, True, True, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('context_budget', True, True, None, True, True, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('reduction', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, Fals"
            "e, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.lifecycle.managers', 'ContextLifecycleResult'),
    ),
)
def _process_dataclass__018fdc061046af08399a06df8437ed8b94609eb6():
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
                context=self.context,
                llm_context=self.llm_context,
                context_budget=self.context_budget,
                reduction=self.reduction,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.context == other.context and
                self.llm_context == other.llm_context and
                self.context_budget == other.context_budget and
                self.reduction == other.reduction
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'context',
            'llm_context',
            'context_budget',
            'reduction',
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
                self.llm_context,
                self.context_budget,
                self.reduction,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            context: __dataclass__init__fields__0__annotation,
            llm_context: __dataclass__init__fields__1__annotation,
            context_budget: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            reduction: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'context', context)
            __dataclass__object_setattr(self, 'llm_context', llm_context)
            __dataclass__object_setattr(self, 'context_budget', context_budget)
            __dataclass__object_setattr(self, 'reduction', reduction)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"context={self.context!r}")
            parts.append(f"llm_context={self.llm_context!r}")
            parts.append(f"context_budget={self.context_budget!r}")
            parts.append(f"reduction={self.reduction!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='90ae1a3679bd09add6879688c325c2eedec72908',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('keep_recent_tokens', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False), (('max_summary_tokens', True, True, None, True, True, False, None), '"
            "instance', 'value', None, False, False, False), (('safety_margin_tokens', True, True, None, True, True, Fa"
            "lse, None), 'instance', 'value', None, False, False, False), (('max_tool_call_chars', True, True, None, Tr"
            "ue, True, False, None), 'instance', 'value', None, False, False, False), (('options', True, True, None, Tr"
            "ue, True, False, None), 'instance', 'value', None, False, False, False), (('system_prompt', True, True, No"
            "ne, True, True, False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), "
            "(False,), (), (False,), (False, True, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.lifecycle.summarizing', 'SummarizingContextCompactor.Config'),
    ),
)
def _process_dataclass__90ae1a3679bd09add6879688c325c2eedec72908():
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
                keep_recent_tokens=self.keep_recent_tokens,
                max_summary_tokens=self.max_summary_tokens,
                safety_margin_tokens=self.safety_margin_tokens,
                max_tool_call_chars=self.max_tool_call_chars,
                options=self.options,
                system_prompt=self.system_prompt,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.keep_recent_tokens == other.keep_recent_tokens and
                self.max_summary_tokens == other.max_summary_tokens and
                self.safety_margin_tokens == other.safety_margin_tokens and
                self.max_tool_call_chars == other.max_tool_call_chars and
                self.options == other.options and
                self.system_prompt == other.system_prompt
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'keep_recent_tokens',
            'max_summary_tokens',
            'safety_margin_tokens',
            'max_tool_call_chars',
            'options',
            'system_prompt',
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
                self.keep_recent_tokens,
                self.max_summary_tokens,
                self.safety_margin_tokens,
                self.max_tool_call_chars,
                self.options,
                self.system_prompt,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            keep_recent_tokens: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            max_summary_tokens: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            safety_margin_tokens: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            max_tool_call_chars: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            options: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            system_prompt: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'keep_recent_tokens', keep_recent_tokens)
            __dataclass__object_setattr(self, 'max_summary_tokens', max_summary_tokens)
            __dataclass__object_setattr(self, 'safety_margin_tokens', safety_margin_tokens)
            __dataclass__object_setattr(self, 'max_tool_call_chars', max_tool_call_chars)
            __dataclass__object_setattr(self, 'options', options)
            __dataclass__object_setattr(self, 'system_prompt', system_prompt)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"keep_recent_tokens={self.keep_recent_tokens!r}")
            parts.append(f"max_summary_tokens={self.max_summary_tokens!r}")
            parts.append(f"safety_margin_tokens={self.safety_margin_tokens!r}")
            parts.append(f"max_tool_call_chars={self.max_tool_call_chars!r}")
            parts.append(f"options={self.options!r}")
            parts.append(f"system_prompt={self.system_prompt!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='0e3d1e47f89e148b5cca3cb38c1260de116f6bf2',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, True, False, False, Fals"
            "e, False, True, True), ((('v', True, True, None, True, False, False, None), 'instance', 'missing', None, F"
            "alse, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, True, ()), ((),), (), (Fa"
            "lse,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.remote.docker', 'DockerContainerIdt'),
    ),
)
def _process_dataclass__0e3d1e47f89e148b5cca3cb38c1260de116f6bf2():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__ctx['omcore.dataclasses.impl.concerns.init.InitGenericAnnotations']['v']
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                v=self.v,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.v == other.v
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'v',
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
                self.v,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            v: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'v', v)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"{self.v!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='9003e8dbfc3095143ba476e83e3b4de72bf8d5f9',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('docker', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('payload_file', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('startup_timeout_s', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('shutdown_timeout_s', True, True, None, True, True, False, None)"
            ", 'instance', 'value', None, False, False, False), (('stderr_tail_bytes', True, True, None, True, True, Fa"
            "lse, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (Fal"
            "se,), (False, True, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.remote.docker', 'DockerRemoteAgentConfig'),
    ),
)
def _process_dataclass__9003e8dbfc3095143ba476e83e3b4de72bf8d5f9():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                docker=self.docker,
                payload_file=self.payload_file,
                startup_timeout_s=self.startup_timeout_s,
                shutdown_timeout_s=self.shutdown_timeout_s,
                stderr_tail_bytes=self.stderr_tail_bytes,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.docker == other.docker and
                self.payload_file == other.payload_file and
                self.startup_timeout_s == other.startup_timeout_s and
                self.shutdown_timeout_s == other.shutdown_timeout_s and
                self.stderr_tail_bytes == other.stderr_tail_bytes
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'docker',
            'payload_file',
            'startup_timeout_s',
            'shutdown_timeout_s',
            'stderr_tail_bytes',
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
                self.docker,
                self.payload_file,
                self.startup_timeout_s,
                self.shutdown_timeout_s,
                self.stderr_tail_bytes,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            docker: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            payload_file: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            startup_timeout_s: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            shutdown_timeout_s: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            stderr_tail_bytes: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'docker', docker)
            __dataclass__object_setattr(self, 'payload_file', payload_file)
            __dataclass__object_setattr(self, 'startup_timeout_s', startup_timeout_s)
            __dataclass__object_setattr(self, 'shutdown_timeout_s', shutdown_timeout_s)
            __dataclass__object_setattr(self, 'stderr_tail_bytes', stderr_tail_bytes)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"docker={self.docker!r}")
            parts.append(f"payload_file={self.payload_file!r}")
            parts.append(f"startup_timeout_s={self.startup_timeout_s!r}")
            parts.append(f"shutdown_timeout_s={self.shutdown_timeout_s!r}")
            parts.append(f"stderr_tail_bytes={self.stderr_tail_bytes!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='85cd619aecbfba28d37348067b94498e9b8ffc41',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('priority', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('text', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.systemprompt.types', 'SystemPromptPart'),
    ),
)
def _process_dataclass__85cd619aecbfba28d37348067b94498e9b8ffc41():
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
                priority=self.priority,
                text=self.text,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.priority == other.priority and
                self.text == other.text
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'priority',
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
                self.priority,
                self.text,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            priority: __dataclass__init__fields__0__annotation,
            text: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'priority', priority)
            __dataclass__object_setattr(self, 'text', text)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"priority={self.priority!r}")
            parts.append(f"text={self.text!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b8c86e6b626e3011e546963edc5d720c817815ec',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('fn', True, True, None, True, True, False, None), 'instance', 'missing', None,"
            " False, False, False), (('llm_tool', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('params_cls', True, True, None, True, True, False, None), 'instance', 'missing"
            "', None, False, False, False), (('params_param', True, True, None, True, True, False, None), 'instance', '"
            "missing', None, False, False, False), (('ctx_param', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('progress_param', True, True, None, True, True, False, None), 'i"
            "nstance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, "
            "False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.tools.reflect', '_ReflectedToolExecutor'),
    ),
)
def _process_dataclass__b8c86e6b626e3011e546963edc5d720c817815ec():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                fn=self.fn,
                llm_tool=self.llm_tool,
                params_cls=self.params_cls,
                params_param=self.params_param,
                ctx_param=self.ctx_param,
                progress_param=self.progress_param,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.fn == other.fn and
                self.llm_tool == other.llm_tool and
                self.params_cls == other.params_cls and
                self.params_param == other.params_param and
                self.ctx_param == other.ctx_param and
                self.progress_param == other.progress_param
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'fn',
            'llm_tool',
            'params_cls',
            'params_param',
            'ctx_param',
            'progress_param',
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
                self.fn,
                self.llm_tool,
                self.params_cls,
                self.params_param,
                self.ctx_param,
                self.progress_param,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            fn: __dataclass__init__fields__0__annotation,
            llm_tool: __dataclass__init__fields__1__annotation,
            params_cls: __dataclass__init__fields__2__annotation,
            params_param: __dataclass__init__fields__3__annotation,
            ctx_param: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            progress_param: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'fn', fn)
            __dataclass__object_setattr(self, 'llm_tool', llm_tool)
            __dataclass__object_setattr(self, 'params_cls', params_cls)
            __dataclass__object_setattr(self, 'params_param', params_param)
            __dataclass__object_setattr(self, 'ctx_param', ctx_param)
            __dataclass__object_setattr(self, 'progress_param', progress_param)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"fn={self.fn!r}")
            parts.append(f"llm_tool={self.llm_tool!r}")
            parts.append(f"params_cls={self.params_cls!r}")
            parts.append(f"params_param={self.params_param!r}")
            parts.append(f"ctx_param={self.ctx_param!r}")
            parts.append(f"progress_param={self.progress_param!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='a6bc98edde7e408cb99d962cd84babd7589b52b3',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('system_prompt', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('messages', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('tools', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False), (('usage', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('context_budget', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False), (('projection', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()"
            "), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.contexts', 'Context'),
    ),
)
def _process_dataclass__a6bc98edde7e408cb99d962cd84babd7589b52b3():
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
                usage=self.usage,
                context_budget=self.context_budget,
                projection=self.projection,
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
                self.tools == other.tools and
                self.usage == other.usage and
                self.context_budget == other.context_budget and
                self.projection == other.projection
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'system_prompt',
            'messages',
            'tools',
            'usage',
            'context_budget',
            'projection',
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
                self.usage,
                self.context_budget,
                self.projection,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            system_prompt: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            messages: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            tools: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            usage: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            context_budget: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            projection: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'system_prompt', system_prompt)
            __dataclass__object_setattr(self, 'messages', messages)
            __dataclass__object_setattr(self, 'tools', tools)
            __dataclass__object_setattr(self, 'usage', usage)
            __dataclass__object_setattr(self, 'context_budget', context_budget)
            __dataclass__object_setattr(self, 'projection', projection)

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
            if (s := __dataclass__repr__default_fn(self.usage)) is not None:
                parts.append(f"usage={s}")
            if (s := __dataclass__repr__default_fn(self.context_budget)) is not None:
                parts.append(f"context_budget={s}")
            if (s := __dataclass__repr__default_fn(self.projection)) is not None:
                parts.append(f"projection={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d68abd5d871c0e5392c61e36cc0e8d1bc0a46a50',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('message', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (()"
            ",), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.errors', 'ErrorStopReasonError'),
    ),
)
def _process_dataclass__d68abd5d871c0e5392c61e36cc0e8d1bc0a46a50():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                message=self.message,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.message == other.message
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            message: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            self.message = message

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"message={self.message!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='a5f45175102de5a359fa6903f207668252b908c7',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('tool_name', True, True, None, True, False, False, None), 'instance', 'missi"
            "ng', None, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ("
            "(),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.errors', 'UnknownToolError'),
    ),
)
def _process_dataclass__a5f45175102de5a359fa6903f207668252b908c7():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                tool_name=self.tool_name,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.tool_name == other.tool_name
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            tool_name: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            self.tool_name = tool_name

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"tool_name={self.tool_name!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='78b2484125ecbe9d61b4176d6f503ceaaa756b77',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('context', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False), (('new_messages', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('reason', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('error', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.events', 'AgentEndEvent'),
    ),
)
def _process_dataclass__78b2484125ecbe9d61b4176d6f503ceaaa756b77():
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
                context=self.context,
                new_messages=self.new_messages,
                reason=self.reason,
                error=self.error,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.context == other.context and
                self.new_messages == other.new_messages and
                self.reason == other.reason and
                self.error == other.error
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'context',
            'new_messages',
            'reason',
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
                self.context,
                self.new_messages,
                self.reason,
                self.error,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            context: __dataclass__init__fields__0__annotation,
            new_messages: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            reason: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            error: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'context', context)
            __dataclass__object_setattr(self, 'new_messages', new_messages)
            __dataclass__object_setattr(self, 'reason', reason)
            __dataclass__object_setattr(self, 'error', error)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"context={self.context!r}")
            parts.append(f"new_messages={self.new_messages!r}")
            parts.append(f"reason={self.reason!r}")
            parts.append(f"error={self.error!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='2e9c2c8314bdc172df0c232bdc5c95c17700fd22',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), (), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.events', 'AgentStartEvent'),
        ('omllm.agent.types.events', 'Event'),
        ('omllm.agent.types.events', 'TurnEvent'),
        ('omllm.agent.types.events', 'TurnStartEvent'),
        ('omllm.agent.types.messages', 'AgentMessage'),
        ('omllm.agent.types.progress', 'ToolProgressUpdate'),
        ('omllm.agent.types.tools', 'ToolResultDetails'),
    ),
)
def _process_dataclass__2e9c2c8314bdc172df0c232bdc5c95c17700fd22():
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
    installer_sha1='8f5aaa30fa821e73795c1f7fd66711a1ba018734',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('reduction', True, True, None, True, True, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('projection', True, True, None, True, True, False, None), 'instance', 'mis"
            "sing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), "
            "((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.events', 'ContextReductionEvent'),
    ),
)
def _process_dataclass__8f5aaa30fa821e73795c1f7fd66711a1ba018734():
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
                reduction=self.reduction,
                projection=self.projection,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.reduction == other.reduction and
                self.projection == other.projection
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'reduction',
            'projection',
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
                self.reduction,
                self.projection,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            reduction: __dataclass__init__fields__0__annotation,
            projection: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'reduction', reduction)
            __dataclass__object_setattr(self, 'projection', projection)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"reduction={self.reduction!r}")
            parts.append(f"projection={self.projection!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='40551fda1ce93b7df625a54ad6fb3456aa1fedfb',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('context_budget', True, True, None, True, False, False, None), 'instance', 'm"
            "issing', None, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()"
            "), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.events', 'ContextWindowEvent'),
    ),
)
def _process_dataclass__40551fda1ce93b7df625a54ad6fb3456aa1fedfb():
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
                context_budget=self.context_budget,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.context_budget == other.context_budget
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'context_budget',
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
                self.context_budget,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            context_budget: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'context_budget', context_budget)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"context_budget={self.context_budget!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='443f96aefb37bb37b55c3fece9238f42eb4a4e2f',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('event', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.events', 'LlmAiStreamEvent'),
    ),
)
def _process_dataclass__443f96aefb37bb37b55c3fece9238f42eb4a4e2f():
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
                event=self.event,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.event == other.event
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'event',
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
                self.event,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            event: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'event', event)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"event={self.event!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='8391854f5c047fd9c1722f16fc3b25525da8fd5d',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('attempts', True, True, None, True, True, False, None), 'instance', 'missing',"
            " None, False, False, False), (('delay_s', True, True, None, True, True, False, None), 'instance', 'missing"
            "', None, False, False, False), (('error', True, True, None, True, True, False, None), 'instance', 'missing"
            "', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.events', 'LlmRetryEvent'),
    ),
)
def _process_dataclass__8391854f5c047fd9c1722f16fc3b25525da8fd5d():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                attempts=self.attempts,
                delay_s=self.delay_s,
                error=self.error,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.attempts == other.attempts and
                self.delay_s == other.delay_s and
                self.error == other.error
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'attempts',
            'delay_s',
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
                self.attempts,
                self.delay_s,
                self.error,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            attempts: __dataclass__init__fields__0__annotation,
            delay_s: __dataclass__init__fields__1__annotation,
            error: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'attempts', attempts)
            __dataclass__object_setattr(self, 'delay_s', delay_s)
            __dataclass__object_setattr(self, 'error', error)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"attempts={self.attempts!r}")
            parts.append(f"delay_s={self.delay_s!r}")
            parts.append(f"error={self.error!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='9ba480dd881f585ec598afcd80222fc42d7708c5',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('message', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False), (('index', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.events', 'MessageAddedEvent'),
    ),
)
def _process_dataclass__9ba480dd881f585ec598afcd80222fc42d7708c5():
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
                message=self.message,
                index=self.index,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.message == other.message and
                self.index == other.index
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'message',
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
                self.message,
                self.index,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            message: __dataclass__init__fields__0__annotation,
            index: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'message', message)
            __dataclass__object_setattr(self, 'index', index)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"message={self.message!r}")
            parts.append(f"index={self.index!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='afba3e3445edefd932da80fbfc510ea9ed1b510f',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('new_state', True, True, None, True, True, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('old_state', True, True, None, True, True, False, None), 'instance', 'miss"
            "ing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ("
            "(),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.events', 'StateUpdateEvent'),
    ),
)
def _process_dataclass__afba3e3445edefd932da80fbfc510ea9ed1b510f():
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
                new_state=self.new_state,
                old_state=self.old_state,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.new_state == other.new_state and
                self.old_state == other.old_state
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'new_state',
            'old_state',
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
                self.new_state,
                self.old_state,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            new_state: __dataclass__init__fields__0__annotation,
            old_state: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'new_state', new_state)
            __dataclass__object_setattr(self, 'old_state', old_state)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"new_state={self.new_state!r}")
            parts.append(f"old_state={self.old_state!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='3ee21752b99496fb07aa42a77b3ccd5c041e06cb',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('tool', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('context', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('result', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.events', 'ToolExecutionEndEvent'),
    ),
)
def _process_dataclass__3ee21752b99496fb07aa42a77b3ccd5c041e06cb():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                tool=self.tool,
                context=self.context,
                result=self.result,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.tool == other.tool and
                self.context == other.context and
                self.result == other.result
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'tool',
            'context',
            'result',
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
                self.tool,
                self.context,
                self.result,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            tool: __dataclass__init__fields__0__annotation,
            context: __dataclass__init__fields__1__annotation,
            result: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'tool', tool)
            __dataclass__object_setattr(self, 'context', context)
            __dataclass__object_setattr(self, 'result', result)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"tool={self.tool!r}")
            parts.append(f"context={self.context!r}")
            parts.append(f"result={self.result!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='811c653f545298e1bacc4c9d00396b3a4510de60',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('tool', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('context', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.events', 'ToolExecutionEvent'),
        ('omllm.agent.types.events', 'ToolExecutionStartEvent'),
    ),
)
def _process_dataclass__811c653f545298e1bacc4c9d00396b3a4510de60():
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
                tool=self.tool,
                context=self.context,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.tool == other.tool and
                self.context == other.context
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'tool',
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
                self.tool,
                self.context,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            tool: __dataclass__init__fields__0__annotation,
            context: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'tool', tool)
            __dataclass__object_setattr(self, 'context', context)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"tool={self.tool!r}")
            parts.append(f"context={self.context!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='1646fd67e7010a92e87fffd9b0b9248eb2f85b72',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('tool', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('context', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('update', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.events', 'ToolExecutionUpdateEvent'),
    ),
)
def _process_dataclass__1646fd67e7010a92e87fffd9b0b9248eb2f85b72():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                tool=self.tool,
                context=self.context,
                update=self.update,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.tool == other.tool and
                self.context == other.context and
                self.update == other.update
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'tool',
            'context',
            'update',
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
                self.tool,
                self.context,
                self.update,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            tool: __dataclass__init__fields__0__annotation,
            context: __dataclass__init__fields__1__annotation,
            update: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'tool', tool)
            __dataclass__object_setattr(self, 'context', context)
            __dataclass__object_setattr(self, 'update', update)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"tool={self.tool!r}")
            parts.append(f"context={self.context!r}")
            parts.append(f"update={self.update!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='5b58e8a9451d86a46cdcee91977feb0500511744',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('message', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False), (('usage', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('context_budget', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (("
            "),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.events', 'TurnEndEvent'),
    ),
)
def _process_dataclass__5b58e8a9451d86a46cdcee91977feb0500511744():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                message=self.message,
                usage=self.usage,
                context_budget=self.context_budget,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.message == other.message and
                self.usage == other.usage and
                self.context_budget == other.context_budget
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'message',
            'usage',
            'context_budget',
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
                self.usage,
                self.context_budget,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            message: __dataclass__init__fields__0__annotation,
            usage: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            context_budget: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'message', message)
            __dataclass__object_setattr(self, 'usage', usage)
            __dataclass__object_setattr(self, 'context_budget', context_budget)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"message={self.message!r}")
            parts.append(f"usage={self.usage!r}")
            parts.append(f"context_budget={self.context_budget!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='20666fa5fc80a59e091dea2a703ea6af1af75041',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('context_limit', True, True, None, True, True, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('input_limit', True, True, None, True, True, False, None), 'instance',"
            " 'missing', None, False, False, False), (('threshold', True, True, None, True, True, False, None), 'instan"
            "ce', 'missing', None, False, False, False), (('output_reserve', True, True, None, True, True, False, None)"
            ", 'instance', 'missing', None, False, False, False), (('observed_input', True, True, None, True, True, Fal"
            "se, None), 'instance', 'value', None, False, False, False), (('estimated_input', True, True, None, True, T"
            "rue, False, None), 'instance', 'value', None, False, False, False)), True, 0, ()), ((False,), (False,), ()"
            ", (False,), (False, True, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.lifecycle', 'ContextBudget'),
    ),
)
def _process_dataclass__20666fa5fc80a59e091dea2a703ea6af1af75041():
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
                context_limit=self.context_limit,
                input_limit=self.input_limit,
                threshold=self.threshold,
                output_reserve=self.output_reserve,
                observed_input=self.observed_input,
                estimated_input=self.estimated_input,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.context_limit == other.context_limit and
                self.input_limit == other.input_limit and
                self.threshold == other.threshold and
                self.output_reserve == other.output_reserve and
                self.observed_input == other.observed_input and
                self.estimated_input == other.estimated_input
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'context_limit',
            'input_limit',
            'threshold',
            'output_reserve',
            'observed_input',
            'estimated_input',
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
                self.context_limit,
                self.input_limit,
                self.threshold,
                self.output_reserve,
                self.observed_input,
                self.estimated_input,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            context_limit: __dataclass__init__fields__0__annotation,
            input_limit: __dataclass__init__fields__1__annotation,
            threshold: __dataclass__init__fields__2__annotation,
            output_reserve: __dataclass__init__fields__3__annotation,
            observed_input: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            estimated_input: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'context_limit', context_limit)
            __dataclass__object_setattr(self, 'input_limit', input_limit)
            __dataclass__object_setattr(self, 'threshold', threshold)
            __dataclass__object_setattr(self, 'output_reserve', output_reserve)
            __dataclass__object_setattr(self, 'observed_input', observed_input)
            __dataclass__object_setattr(self, 'estimated_input', estimated_input)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.context_limit)) is not None:
                parts.append(f"context_limit={s}")
            if (s := __dataclass__repr__default_fn(self.input_limit)) is not None:
                parts.append(f"input_limit={s}")
            if (s := __dataclass__repr__default_fn(self.threshold)) is not None:
                parts.append(f"threshold={s}")
            if (s := __dataclass__repr__default_fn(self.output_reserve)) is not None:
                parts.append(f"output_reserve={s}")
            if (s := __dataclass__repr__default_fn(self.observed_input)) is not None:
                parts.append(f"observed_input={s}")
            if (s := __dataclass__repr__default_fn(self.estimated_input)) is not None:
                parts.append(f"estimated_input={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='9e6024d5a447f98c2bd9649ed72e58ce88ce472a',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('ZERO', True, True, None, True, None, False, None), 'class_var', 'missing', No"
            "ne, False, False, False), (('output_reserve_tokens', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('safety_margin_tokens', True, True, None, True, True, False, Non"
            "e), 'instance', 'value', None, False, False, False), (('max_tool_result_chars', True, True, None, True, Tr"
            "ue, False, None), 'instance', 'value', None, False, False, False), (('keep_recent_tokens', True, True, Non"
            "e, True, True, False, None), 'instance', 'value', None, False, False, False), (('prune_min_chars', True, T"
            "rue, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('prune_headroom_to"
            "kens', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('pru"
            "ne_tool_results', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, Fal"
            "se), (('prunable_tool_names', True, True, None, True, True, False, None), 'instance', 'value', None, False"
            ", False, False), (('max_overflow_retries', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, True, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.lifecycle', 'ContextLifecycleConfig'),
    ),
)
def _process_dataclass__9e6024d5a447f98c2bd9649ed72e58ce88ce472a():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                output_reserve_tokens=self.output_reserve_tokens,
                safety_margin_tokens=self.safety_margin_tokens,
                max_tool_result_chars=self.max_tool_result_chars,
                keep_recent_tokens=self.keep_recent_tokens,
                prune_min_chars=self.prune_min_chars,
                prune_headroom_tokens=self.prune_headroom_tokens,
                prune_tool_results=self.prune_tool_results,
                prunable_tool_names=self.prunable_tool_names,
                max_overflow_retries=self.max_overflow_retries,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.output_reserve_tokens == other.output_reserve_tokens and
                self.safety_margin_tokens == other.safety_margin_tokens and
                self.max_tool_result_chars == other.max_tool_result_chars and
                self.keep_recent_tokens == other.keep_recent_tokens and
                self.prune_min_chars == other.prune_min_chars and
                self.prune_headroom_tokens == other.prune_headroom_tokens and
                self.prune_tool_results == other.prune_tool_results and
                self.prunable_tool_names == other.prunable_tool_names and
                self.max_overflow_retries == other.max_overflow_retries
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'ZERO',
            'output_reserve_tokens',
            'safety_margin_tokens',
            'max_tool_result_chars',
            'keep_recent_tokens',
            'prune_min_chars',
            'prune_headroom_tokens',
            'prune_tool_results',
            'prunable_tool_names',
            'max_overflow_retries',
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
                self.output_reserve_tokens,
                self.safety_margin_tokens,
                self.max_tool_result_chars,
                self.keep_recent_tokens,
                self.prune_min_chars,
                self.prune_headroom_tokens,
                self.prune_tool_results,
                self.prunable_tool_names,
                self.max_overflow_retries,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            output_reserve_tokens: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            safety_margin_tokens: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            max_tool_result_chars: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            keep_recent_tokens: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            prune_min_chars: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            prune_headroom_tokens: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            prune_tool_results: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            prunable_tool_names: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            max_overflow_retries: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'output_reserve_tokens', output_reserve_tokens)
            __dataclass__object_setattr(self, 'safety_margin_tokens', safety_margin_tokens)
            __dataclass__object_setattr(self, 'max_tool_result_chars', max_tool_result_chars)
            __dataclass__object_setattr(self, 'keep_recent_tokens', keep_recent_tokens)
            __dataclass__object_setattr(self, 'prune_min_chars', prune_min_chars)
            __dataclass__object_setattr(self, 'prune_headroom_tokens', prune_headroom_tokens)
            __dataclass__object_setattr(self, 'prune_tool_results', prune_tool_results)
            __dataclass__object_setattr(self, 'prunable_tool_names', prunable_tool_names)
            __dataclass__object_setattr(self, 'max_overflow_retries', max_overflow_retries)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"output_reserve_tokens={self.output_reserve_tokens!r}")
            parts.append(f"safety_margin_tokens={self.safety_margin_tokens!r}")
            parts.append(f"max_tool_result_chars={self.max_tool_result_chars!r}")
            parts.append(f"keep_recent_tokens={self.keep_recent_tokens!r}")
            parts.append(f"prune_min_chars={self.prune_min_chars!r}")
            parts.append(f"prune_headroom_tokens={self.prune_headroom_tokens!r}")
            parts.append(f"prune_tool_results={self.prune_tool_results!r}")
            parts.append(f"prunable_tool_names={self.prunable_tool_names!r}")
            parts.append(f"max_overflow_retries={self.max_overflow_retries!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='7807d79774ced53d683930a710631bc3d9d90c07',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('ZERO', True, True, None, True, None, False, None), 'class_var', 'missing', No"
            "ne, False, False, False), (('summary', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('first_kept_message_index', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('tool_results', True, True, None, True, True, False, None), '"
            "instance', 'value', 'callable', False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (F"
            "alse, True, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.lifecycle', 'ContextProjection'),
    ),
)
def _process_dataclass__7807d79774ced53d683930a710631bc3d9d90c07():
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
        __dataclass__init__fields__3__coerce = __dataclass__spec.fields[3].coerce
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
                summary=self.summary,
                first_kept_message_index=self.first_kept_message_index,
                tool_results=self.tool_results,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.summary == other.summary and
                self.first_kept_message_index == other.first_kept_message_index and
                self.tool_results == other.tool_results
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'ZERO',
            'summary',
            'first_kept_message_index',
            'tool_results',
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
                self.summary,
                self.first_kept_message_index,
                self.tool_results,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            summary: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            first_kept_message_index: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            tool_results: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            tool_results = __dataclass__init__fields__3__coerce(tool_results)
            __dataclass__object_setattr(self, 'summary', summary)
            __dataclass__object_setattr(self, 'first_kept_message_index', first_kept_message_index)
            __dataclass__object_setattr(self, 'tool_results', tool_results)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.summary)) is not None:
                parts.append(f"summary={s}")
            if (s := __dataclass__repr__default_fn(self.first_kept_message_index)) is not None:
                parts.append(f"first_kept_message_index={s}")
            if (s := __dataclass__repr__default_fn(self.tool_results)) is not None:
                parts.append(f"tool_results={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b72c1f825252b22287955ec7d70d7f82a82bb017',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('reason', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('before_tokens', True, True, None, True, True, False, None), 'instance', 'mis"
            "sing', None, False, False, False), (('after_tokens', True, True, None, True, True, False, None), 'instance"
            "', 'missing', None, False, False, False), (('tool_result_indices', True, True, None, True, True, False, No"
            "ne), 'instance', 'value', None, False, False, False), (('compacted', True, True, None, True, True, False, "
            "None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,),"
            " (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.lifecycle', 'ContextReduction'),
    ),
)
def _process_dataclass__b72c1f825252b22287955ec7d70d7f82a82bb017():
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
                reason=self.reason,
                before_tokens=self.before_tokens,
                after_tokens=self.after_tokens,
                tool_result_indices=self.tool_result_indices,
                compacted=self.compacted,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.reason == other.reason and
                self.before_tokens == other.before_tokens and
                self.after_tokens == other.after_tokens and
                self.tool_result_indices == other.tool_result_indices and
                self.compacted == other.compacted
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'reason',
            'before_tokens',
            'after_tokens',
            'tool_result_indices',
            'compacted',
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
                self.reason,
                self.before_tokens,
                self.after_tokens,
                self.tool_result_indices,
                self.compacted,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            reason: __dataclass__init__fields__0__annotation,
            before_tokens: __dataclass__init__fields__1__annotation,
            after_tokens: __dataclass__init__fields__2__annotation,
            tool_result_indices: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            compacted: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'reason', reason)
            __dataclass__object_setattr(self, 'before_tokens', before_tokens)
            __dataclass__object_setattr(self, 'after_tokens', after_tokens)
            __dataclass__object_setattr(self, 'tool_result_indices', tool_result_indices)
            __dataclass__object_setattr(self, 'compacted', compacted)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"reason={self.reason!r}")
            parts.append(f"before_tokens={self.before_tokens!r}")
            parts.append(f"after_tokens={self.after_tokens!r}")
            parts.append(f"tool_result_indices={self.tool_result_indices!r}")
            parts.append(f"compacted={self.compacted!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='a759ae59fd3fc2a3a35c7e17e91dc06c76d882f0',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('message_index', True, True, None, True, True, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('max_chars', True, True, None, True, True, False, None), 'instance', '"
            "missing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, True, ())"
            ", ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.lifecycle', 'ToolResultProjection'),
    ),
)
def _process_dataclass__a759ae59fd3fc2a3a35c7e17e91dc06c76d882f0():
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
                message_index=self.message_index,
                max_chars=self.max_chars,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.message_index == other.message_index and
                self.max_chars == other.max_chars
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'message_index',
            'max_chars',
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
                self.message_index,
                self.max_chars,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            message_index: __dataclass__init__fields__0__annotation,
            max_chars: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'message_index', message_index)
            __dataclass__object_setattr(self, 'max_chars', max_chars)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"message_index={self.message_index!r}")
            parts.append(f"max_chars={self.max_chars!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='78adff5f335086083b17d0a1ff962c9c3975ebdf',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('ZERO', True, True, None, True, None, False, None), 'class_var', 'missing', No"
            "ne, False, False, False), (('input', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('output', True, True, None, True, True, False, None), 'instance', 'value', None,"
            " False, False, False), (('reasoning', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('cache_read', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('cache_write', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.lifecycle', 'UsageLedger'),
    ),
)
def _process_dataclass__78adff5f335086083b17d0a1ff962c9c3975ebdf():
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
            'ZERO',
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
            input: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            output: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            reasoning: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            cache_read: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            cache_write: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
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
    installer_sha1='2dfa811b949b35676a88102b391ea95d4de8bab9',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, True, False, False, False, Fals"
            "e, False, True, False), ((('info', True, True, None, True, False, False, None), 'instance', 'missing', Non"
            "e, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.messages', 'InfoAgentMessage'),
    ),
)
def _process_dataclass__2dfa811b949b35676a88102b391ea95d4de8bab9():
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
            try:
                return self.__dataclass_hash__
            except AttributeError:
                pass
            object.__setattr__(
                self,
                '__dataclass_hash__',
                h := hash((
                    self.info,
                ))
            )
            return h

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
            parts.append(f"{self.info!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c7f11b81a743c16469d8d5b9c20b11c81b5d380c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, True, False), ((('text', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('stream', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (),"
            " (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.progress', 'OutputToolProgressUpdate'),
    ),
)
def _process_dataclass__c7f11b81a743c16469d8d5b9c20b11c81b5d380c():
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
                text=self.text,
                stream=self.stream,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.text == other.text and
                self.stream == other.stream
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'text',
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
                self.text,
                self.stream,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            text: __dataclass__init__fields__0__annotation,
            *,
            stream: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'text', text)
            __dataclass__object_setattr(self, 'stream', stream)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"{self.text!r}")
            parts.append(f"stream={self.stream!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='805461898627314a0912c5682c019aef914669d1',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('context', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('model', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('turn_config', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('tool_env', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.states', 'State'),
    ),
)
def _process_dataclass__805461898627314a0912c5682c019aef914669d1():
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
                context=self.context,
                model=self.model,
                turn_config=self.turn_config,
                tool_env=self.tool_env,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.context == other.context and
                self.model == other.model and
                self.turn_config == other.turn_config and
                self.tool_env == other.tool_env
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'context',
            'model',
            'turn_config',
            'tool_env',
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
                self.model,
                self.turn_config,
                self.tool_env,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            context: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            model: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            turn_config: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            tool_env: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'context', context)
            __dataclass__object_setattr(self, 'model', model)
            __dataclass__object_setattr(self, 'turn_config', turn_config)
            __dataclass__object_setattr(self, 'tool_env', tool_env)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.context)) is not None:
                parts.append(f"context={s}")
            if (s := __dataclass__repr__default_fn(self.model)) is not None:
                parts.append(f"model={s}")
            if (s := __dataclass__repr__default_fn(self.turn_config)) is not None:
                parts.append(f"turn_config={s}")
            if (s := __dataclass__repr__default_fn(self.tool_env)) is not None:
                parts.append(f"tool_env={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e9e97322e81fdcecb16325026328dee49c6c816d',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('llm_tool', True, True, None, True, True, False, None), 'instance', 'missing',"
            " None, False, False, False), (('executor', True, True, None, True, True, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('summarizer', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), "
            "((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.tools', 'Tool'),
    ),
)
def _process_dataclass__e9e97322e81fdcecb16325026328dee49c6c816d():
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
                llm_tool=self.llm_tool,
                executor=self.executor,
                summarizer=self.summarizer,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.llm_tool == other.llm_tool and
                self.executor == other.executor and
                self.summarizer == other.summarizer
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'llm_tool',
            'executor',
            'summarizer',
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
                self.llm_tool,
                self.executor,
                self.summarizer,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            llm_tool: __dataclass__init__fields__0__annotation,
            executor: __dataclass__init__fields__1__annotation,
            summarizer: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'llm_tool', llm_tool)
            __dataclass__object_setattr(self, 'executor', executor)
            __dataclass__object_setattr(self, 'summarizer', summarizer)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"llm_tool={self.llm_tool!r}")
            parts.append(f"executor={self.executor!r}")
            parts.append(f"summarizer={self.summarizer!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='deda3ca5e512a267637e8f82f80f9d4d3b05aad5',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('tool', True, True, None, True, True, False, None), 'instance', 'value', None,"
            " False, False, False), (('args', True, True, None, True, True, False, None), 'instance', 'missing', None, "
            "False, False, False), (('llm_tool_call', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('env', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('progress', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (),"
            " (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.tools', 'ToolContext'),
    ),
)
def _process_dataclass__deda3ca5e512a267637e8f82f80f9d4d3b05aad5():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default = __dataclass__spec.fields[0].default.must()
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
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
                tool=self.tool,
                args=self.args,
                llm_tool_call=self.llm_tool_call,
                env=self.env,
                progress=self.progress,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.tool == other.tool and
                self.args == other.args and
                self.llm_tool_call == other.llm_tool_call and
                self.env == other.env and
                self.progress == other.progress
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'tool',
            'args',
            'llm_tool_call',
            'env',
            'progress',
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
                self.tool,
                self.args,
                self.llm_tool_call,
                self.env,
                self.progress,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            tool: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            args: __dataclass__init__fields__1__annotation,
            llm_tool_call: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            env: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            progress: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'tool', tool)
            __dataclass__object_setattr(self, 'args', args)
            __dataclass__object_setattr(self, 'llm_tool_call', llm_tool_call)
            __dataclass__object_setattr(self, 'env', env)
            __dataclass__object_setattr(self, 'progress', progress)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"tool={self.tool!r}")
            parts.append(f"args={self.args!r}")
            parts.append(f"llm_tool_call={self.llm_tool_call!r}")
            parts.append(f"env={self.env!r}")
            parts.append(f"progress={self.progress!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='1c027595cfe95cbc51b1c9d3c6dd399fa0f43c5b',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('description', True, True, None, True, False, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('params', True, True, None, True, False, False, None), 'instance', 'va"
            "lue', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ("
            "(),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.tools', 'ToolDescription'),
    ),
)
def _process_dataclass__1c027595cfe95cbc51b1c9d3c6dd399fa0f43c5b():
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
                description=self.description,
                params=self.params,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.description == other.description and
                self.params == other.params
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'description',
            'params',
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
                self.description,
                self.params,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            description: __dataclass__init__fields__0__annotation,
            params: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'description', description)
            __dataclass__object_setattr(self, 'params', params)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"description={self.description!r}")
            parts.append(f"params={self.params!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='fdb5b1219424335e6d4f33553dbb26a7fd3f92bd',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('cwd', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False), (('processes', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), "
            "(False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.tools', 'ToolEnvironment'),
    ),
)
def _process_dataclass__fdb5b1219424335e6d4f33553dbb26a7fd3f92bd():
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
                cwd=self.cwd,
                processes=self.processes,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.cwd == other.cwd and
                self.processes == other.processes
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'cwd',
            'processes',
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
                self.cwd,
                self.processes,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            cwd: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            processes: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'cwd', cwd)
            __dataclass__object_setattr(self, 'processes', processes)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"cwd={self.cwd!r}")
            parts.append(f"processes={self.processes!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b29f78677806ae4563bc1a7158ed4cc742bf8962',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('content', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False), (('error', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('details', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('display', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.tools', 'ToolResult'),
    ),
)
def _process_dataclass__b29f78677806ae4563bc1a7158ed4cc742bf8962():
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
                content=self.content,
                error=self.error,
                details=self.details,
                display=self.display,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.content == other.content and
                self.error == other.error and
                self.details == other.details and
                self.display == other.display
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'content',
            'error',
            'details',
            'display',
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
                self.error,
                self.details,
                self.display,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            content: __dataclass__init__fields__0__annotation,
            error: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            details: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            display: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'content', content)
            __dataclass__object_setattr(self, 'error', error)
            __dataclass__object_setattr(self, 'details', details)
            __dataclass__object_setattr(self, 'display', display)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"content={self.content!r}")
            parts.append(f"error={self.error!r}")
            parts.append(f"details={self.details!r}")
            parts.append(f"display={self.display!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='5093fd11ff03c6ffc623140f7a80e91138fc2136',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, True, False), ((('tools', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False),), False, 1, ()), ((False,), (False,), (), (False,), (False, False, ('getter',))"
            ", ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.tools', 'ToolSet'),
    ),
)
def _process_dataclass__5093fd11ff03c6ffc623140f7a80e91138fc2136():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__init_fns__0 = __dataclass__ctx['omcore.dataclasses.impl.concerns.init.InitFunctions'].values[0]
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                tools=self.tools,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.tools == other.tools
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
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
                self.tools,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            tools: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'tools', tools)
            __dataclass__init__init_fns__0(self)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"{self.tools!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='697c3085651cffe35ad77cb93eaa2d09df9d6d7c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('max_retries', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('initial_delay_s', True, True, None, True, True, False, None), 'instance',"
            " 'value', None, False, False, False), (('max_delay_s', True, True, None, True, True, False, None), 'instan"
            "ce', 'value', None, False, False, False), (('multiplier', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, Fal"
            "se, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.turns', 'LlmRetryConfig'),
    ),
)
def _process_dataclass__697c3085651cffe35ad77cb93eaa2d09df9d6d7c():
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
                max_retries=self.max_retries,
                initial_delay_s=self.initial_delay_s,
                max_delay_s=self.max_delay_s,
                multiplier=self.multiplier,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.max_retries == other.max_retries and
                self.initial_delay_s == other.initial_delay_s and
                self.max_delay_s == other.max_delay_s and
                self.multiplier == other.multiplier
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'max_retries',
            'initial_delay_s',
            'max_delay_s',
            'multiplier',
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
                self.max_retries,
                self.initial_delay_s,
                self.max_delay_s,
                self.multiplier,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            max_retries: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            initial_delay_s: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            max_delay_s: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            multiplier: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'max_retries', max_retries)
            __dataclass__object_setattr(self, 'initial_delay_s', initial_delay_s)
            __dataclass__object_setattr(self, 'max_delay_s', max_delay_s)
            __dataclass__object_setattr(self, 'multiplier', multiplier)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.max_retries)) is not None:
                parts.append(f"max_retries={s}")
            if (s := __dataclass__repr__default_fn(self.initial_delay_s)) is not None:
                parts.append(f"initial_delay_s={s}")
            if (s := __dataclass__repr__default_fn(self.max_delay_s)) is not None:
                parts.append(f"max_delay_s={s}")
            if (s := __dataclass__repr__default_fn(self.multiplier)) is not None:
                parts.append(f"multiplier={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='768114af10393989818894df60399fdcae369695',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('llm_options', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('max_turns', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('llm_retry', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('context_lifecycle', True, True, None, True, True, False, None), 'inst"
            "ance', 'value', None, False, False, False), (('max_concurrent_tool_calls', True, True, None, True, True, F"
            "alse, None), 'instance', 'value', None, True, False, False), (('cancel_timeout_s', True, True, None, True,"
            " True, False, None), 'instance', 'value', None, True, False, False), (('steering_skips_pending_tool_calls'"
            ", True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False)), True, 0, ("
            ")), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.turns', 'TurnConfig'),
    ),
)
def _process_dataclass__768114af10393989818894df60399fdcae369695():
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
        __dataclass__init__fields__4__validate = __dataclass__spec.fields[4].validate
        __dataclass__init__fields__5__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__5__default = __dataclass__spec.fields[5].default.must()
        __dataclass__init__fields__5__validate = __dataclass__spec.fields[5].validate
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__6__default = __dataclass__spec.fields[6].default.must()
        __dataclass__repr__default_fn = __dataclass__spec.default_repr_fn
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
                llm_options=self.llm_options,
                max_turns=self.max_turns,
                llm_retry=self.llm_retry,
                context_lifecycle=self.context_lifecycle,
                max_concurrent_tool_calls=self.max_concurrent_tool_calls,
                cancel_timeout_s=self.cancel_timeout_s,
                steering_skips_pending_tool_calls=self.steering_skips_pending_tool_calls,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.llm_options == other.llm_options and
                self.max_turns == other.max_turns and
                self.llm_retry == other.llm_retry and
                self.context_lifecycle == other.context_lifecycle and
                self.max_concurrent_tool_calls == other.max_concurrent_tool_calls and
                self.cancel_timeout_s == other.cancel_timeout_s and
                self.steering_skips_pending_tool_calls == other.steering_skips_pending_tool_calls
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'llm_options',
            'max_turns',
            'llm_retry',
            'context_lifecycle',
            'max_concurrent_tool_calls',
            'cancel_timeout_s',
            'steering_skips_pending_tool_calls',
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
                self.llm_options,
                self.max_turns,
                self.llm_retry,
                self.context_lifecycle,
                self.max_concurrent_tool_calls,
                self.cancel_timeout_s,
                self.steering_skips_pending_tool_calls,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            llm_options: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            max_turns: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            llm_retry: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            context_lifecycle: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            max_concurrent_tool_calls: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            cancel_timeout_s: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            steering_skips_pending_tool_calls: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
        ) -> __dataclass__None:
            if not __dataclass__init__fields__4__validate(max_concurrent_tool_calls): 
                raise __dataclass__FieldFnValidationError(
                    obj=self,
                    fn=__dataclass__init__fields__4__validate,
                    field='max_concurrent_tool_calls',
                    value=max_concurrent_tool_calls,
                )
            if not __dataclass__init__fields__5__validate(cancel_timeout_s): 
                raise __dataclass__FieldFnValidationError(
                    obj=self,
                    fn=__dataclass__init__fields__5__validate,
                    field='cancel_timeout_s',
                    value=cancel_timeout_s,
                )
            __dataclass__object_setattr(self, 'llm_options', llm_options)
            __dataclass__object_setattr(self, 'max_turns', max_turns)
            __dataclass__object_setattr(self, 'llm_retry', llm_retry)
            __dataclass__object_setattr(self, 'context_lifecycle', context_lifecycle)
            __dataclass__object_setattr(self, 'max_concurrent_tool_calls', max_concurrent_tool_calls)
            __dataclass__object_setattr(self, 'cancel_timeout_s', cancel_timeout_s)
            __dataclass__object_setattr(self, 'steering_skips_pending_tool_calls', steering_skips_pending_tool_calls)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.llm_options)) is not None:
                parts.append(f"llm_options={s}")
            if (s := __dataclass__repr__default_fn(self.max_turns)) is not None:
                parts.append(f"max_turns={s}")
            if (s := __dataclass__repr__default_fn(self.llm_retry)) is not None:
                parts.append(f"llm_retry={s}")
            if (s := __dataclass__repr__default_fn(self.context_lifecycle)) is not None:
                parts.append(f"context_lifecycle={s}")
            if (s := __dataclass__repr__default_fn(self.max_concurrent_tool_calls)) is not None:
                parts.append(f"max_concurrent_tool_calls={s}")
            if (s := __dataclass__repr__default_fn(self.cancel_timeout_s)) is not None:
                parts.append(f"cancel_timeout_s={s}")
            if (s := __dataclass__repr__default_fn(self.steering_skips_pending_tool_calls)) is not None:
                parts.append(f"steering_skips_pending_tool_calls={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e0077e76389929cf6183d76bc50356541c955654',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('in_state', True, True, None, True, True, False, None), 'instance', 'missing',"
            " None, False, False, False), (('new_messages', True, True, None, True, True, False, None), 'instance', 'mi"
            "ssing', None, False, False, False), (('subscriber', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, False, False, False), (('inbox', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()),"
            " ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.turns', 'TurnParams'),
    ),
)
def _process_dataclass__e0077e76389929cf6183d76bc50356541c955654():
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
                in_state=self.in_state,
                new_messages=self.new_messages,
                subscriber=self.subscriber,
                inbox=self.inbox,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.in_state == other.in_state and
                self.new_messages == other.new_messages and
                self.subscriber == other.subscriber and
                self.inbox == other.inbox
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'in_state',
            'new_messages',
            'subscriber',
            'inbox',
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
                self.in_state,
                self.new_messages,
                self.subscriber,
                self.inbox,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            in_state: __dataclass__init__fields__0__annotation,
            new_messages: __dataclass__init__fields__1__annotation,
            subscriber: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            inbox: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'in_state', in_state)
            __dataclass__object_setattr(self, 'new_messages', new_messages)
            __dataclass__object_setattr(self, 'subscriber', subscriber)
            __dataclass__object_setattr(self, 'inbox', inbox)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.in_state)) is not None:
                parts.append(f"in_state={s}")
            if (s := __dataclass__repr__default_fn(self.new_messages)) is not None:
                parts.append(f"new_messages={s}")
            if (s := __dataclass__repr__default_fn(self.subscriber)) is not None:
                parts.append(f"subscriber={s}")
            if (s := __dataclass__repr__default_fn(self.inbox)) is not None:
                parts.append(f"inbox={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b4d34d19692d2b810add7acd98c65da4e9fd5206',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('config', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('context', True, True, None, True, True, False, None), 'instance', 'missing',"
            " None, False, False, False), (('new_messages', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('reason', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('error', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.agent.types.turns', 'TurnResult'),
    ),
)
def _process_dataclass__b4d34d19692d2b810add7acd98c65da4e9fd5206():
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
                config=self.config,
                context=self.context,
                new_messages=self.new_messages,
                reason=self.reason,
                error=self.error,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.config == other.config and
                self.context == other.context and
                self.new_messages == other.new_messages and
                self.reason == other.reason and
                self.error == other.error
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'config',
            'context',
            'new_messages',
            'reason',
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
                self.config,
                self.context,
                self.new_messages,
                self.reason,
                self.error,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            config: __dataclass__init__fields__0__annotation,
            context: __dataclass__init__fields__1__annotation,
            new_messages: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            reason: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            error: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'config', config)
            __dataclass__object_setattr(self, 'context', context)
            __dataclass__object_setattr(self, 'new_messages', new_messages)
            __dataclass__object_setattr(self, 'reason', reason)
            __dataclass__object_setattr(self, 'error', error)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.config)) is not None:
                parts.append(f"config={s}")
            if (s := __dataclass__repr__default_fn(self.context)) is not None:
                parts.append(f"context={s}")
            if (s := __dataclass__repr__default_fn(self.new_messages)) is not None:
                parts.append(f"new_messages={s}")
            if (s := __dataclass__repr__default_fn(self.reason)) is not None:
                parts.append(f"reason={s}")
            if (s := __dataclass__repr__default_fn(self.error)) is not None:
                parts.append(f"error={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
