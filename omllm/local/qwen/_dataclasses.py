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
    installer_sha1='2bf5818ad4160410a4ee25ace966c7517e477ba1',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('w', True, True, None, True, False, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('scales', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('biases', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('bits', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('group', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('shape', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.backends.mlx', 'MlxQWeight'),
    ),
)
def _process_dataclass__2bf5818ad4160410a4ee25ace966c7517e477ba1():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                w=self.w,
                scales=self.scales,
                biases=self.biases,
                bits=self.bits,
                group=self.group,
                shape=self.shape,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.w == other.w and
                self.scales == other.scales and
                self.biases == other.biases and
                self.bits == other.bits and
                self.group == other.group and
                self.shape == other.shape
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            w: __dataclass__init__fields__0__annotation,
            scales: __dataclass__init__fields__1__annotation,
            biases: __dataclass__init__fields__2__annotation,
            bits: __dataclass__init__fields__3__annotation,
            group: __dataclass__init__fields__4__annotation,
            shape: __dataclass__init__fields__5__annotation,
        ) -> __dataclass__None:
            self.w = w
            self.scales = scales
            self.biases = biases
            self.bits = bits
            self.group = group
            self.shape = shape

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"w={self.w!r}")
            parts.append(f"scales={self.scales!r}")
            parts.append(f"biases={self.biases!r}")
            parts.append(f"bits={self.bits!r}")
            parts.append(f"group={self.group!r}")
            parts.append(f"shape={self.shape!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='8906dd9cf35a7c6060f3652ea8accce5aa449cca',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('q', True, True, None, True, False, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('scale', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('bias', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('bits', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('group', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('shape', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.backends.tinygrad', 'TinyQWeight'),
        ('omllm.local.qwen.backends.torch', 'TorchQWeight'),
        ('omllm.local.qwen.quant', 'QWeight'),
    ),
)
def _process_dataclass__8906dd9cf35a7c6060f3652ea8accce5aa449cca():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                q=self.q,
                scale=self.scale,
                bias=self.bias,
                bits=self.bits,
                group=self.group,
                shape=self.shape,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.q == other.q and
                self.scale == other.scale and
                self.bias == other.bias and
                self.bits == other.bits and
                self.group == other.group and
                self.shape == other.shape
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            q: __dataclass__init__fields__0__annotation,
            scale: __dataclass__init__fields__1__annotation,
            bias: __dataclass__init__fields__2__annotation,
            bits: __dataclass__init__fields__3__annotation,
            group: __dataclass__init__fields__4__annotation,
            shape: __dataclass__init__fields__5__annotation,
        ) -> __dataclass__None:
            self.q = q
            self.scale = scale
            self.bias = bias
            self.bits = bits
            self.group = group
            self.shape = shape

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"q={self.q!r}")
            parts.append(f"scale={self.scale!r}")
            parts.append(f"bias={self.bias!r}")
            parts.append(f"bits={self.bits!r}")
            parts.append(f"group={self.group!r}")
            parts.append(f"shape={self.shape!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='799681b69f6a44e7ab26f91f04e7ddf81e74bf0c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('block_n', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('block_k', True, True, None, True, False, False, None), 'instance', 'value',"
            " None, False, False, False), (('num_warps', True, True, None, True, False, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('num_stages', True, True, None, True, False, False, None), 'instance', '"
            "value', None, False, False, False), (('split_k', True, True, None, True, False, False, None), 'instance', "
            "'value', None, False, False, False), (('fma', True, True, None, True, False, False, None), 'instance', 'va"
            "lue', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ("
            "(),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.backends.torch_triton', 'GemvConfig'),
    ),
)
def _process_dataclass__799681b69f6a44e7ab26f91f04e7ddf81e74bf0c():
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
                block_n=self.block_n,
                block_k=self.block_k,
                num_warps=self.num_warps,
                num_stages=self.num_stages,
                split_k=self.split_k,
                fma=self.fma,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.block_n == other.block_n and
                self.block_k == other.block_k and
                self.num_warps == other.num_warps and
                self.num_stages == other.num_stages and
                self.split_k == other.split_k and
                self.fma == other.fma
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'block_n',
            'block_k',
            'num_warps',
            'num_stages',
            'split_k',
            'fma',
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
                self.block_n,
                self.block_k,
                self.num_warps,
                self.num_stages,
                self.split_k,
                self.fma,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            block_n: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            block_k: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            num_warps: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            num_stages: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            split_k: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            fma: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'block_n', block_n)
            __dataclass__object_setattr(self, 'block_k', block_k)
            __dataclass__object_setattr(self, 'num_warps', num_warps)
            __dataclass__object_setattr(self, 'num_stages', num_stages)
            __dataclass__object_setattr(self, 'split_k', split_k)
            __dataclass__object_setattr(self, 'fma', fma)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"block_n={self.block_n!r}")
            parts.append(f"block_k={self.block_k!r}")
            parts.append(f"num_warps={self.num_warps!r}")
            parts.append(f"num_stages={self.num_stages!r}")
            parts.append(f"split_k={self.split_k!r}")
            parts.append(f"fma={self.fma!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='9832aac84b6cbcfd6428ff7267dba9d7620bbef5',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('content', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('reasoning', True, True, None, True, False, False, None), 'instance', 'mi"
            "ssing', None, False, False, False), (('tool_calls', True, True, None, True, False, False, None), 'instance"
            "', 'missing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False"
            ", ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.chat', 'Parsed'),
    ),
)
def _process_dataclass__9832aac84b6cbcfd6428ff7267dba9d7620bbef5():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                content=self.content,
                reasoning=self.reasoning,
                tool_calls=self.tool_calls,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.content == other.content and
                self.reasoning == other.reasoning and
                self.tool_calls == other.tool_calls
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            content: __dataclass__init__fields__0__annotation,
            reasoning: __dataclass__init__fields__1__annotation,
            tool_calls: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            self.content = content
            self.reasoning = reasoning
            self.tool_calls = tool_calls

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"content={self.content!r}")
            parts.append(f"reasoning={self.reasoning!r}")
            parts.append(f"tool_calls={self.tool_calls!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='56e23b89303016228a308dedebb1b271d62785d3',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('root', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('hits', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('misses', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.paramcache', 'ParamCache'),
    ),
)
def _process_dataclass__56e23b89303016228a308dedebb1b271d62785d3():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                root=self.root,
                hits=self.hits,
                misses=self.misses,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.root == other.root and
                self.hits == other.hits and
                self.misses == other.misses
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            root: __dataclass__init__fields__0__annotation,
            hits: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            misses: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            self.root = root
            self.hits = hits
            self.misses = misses

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"root={self.root!r}")
            parts.append(f"hits={self.hits!r}")
            parts.append(f"misses={self.misses!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='0c39811345dcc877a06255a948b454441703e682',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('tokens', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('cache', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('logits', True, True, None, True, False, False, None), 'instance', 'missi"
            "ng', None, False, False, False), (('hidden', True, True, None, True, False, False, None), 'instance', 'mis"
            "sing', None, False, False, False), (('mtp_kv', True, True, None, True, False, False, None), 'instance', 'm"
            "issing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ())"
            ", ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.prefixcache', 'Snapshot'),
    ),
)
def _process_dataclass__0c39811345dcc877a06255a948b454441703e682():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                tokens=self.tokens,
                cache=self.cache,
                logits=self.logits,
                hidden=self.hidden,
                mtp_kv=self.mtp_kv,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.tokens == other.tokens and
                self.cache == other.cache and
                self.logits == other.logits and
                self.hidden == other.hidden and
                self.mtp_kv == other.mtp_kv
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            tokens: __dataclass__init__fields__0__annotation,
            cache: __dataclass__init__fields__1__annotation,
            logits: __dataclass__init__fields__2__annotation,
            hidden: __dataclass__init__fields__3__annotation,
            mtp_kv: __dataclass__init__fields__4__annotation,
        ) -> __dataclass__None:
            self.tokens = tokens
            self.cache = cache
            self.logits = logits
            self.hidden = hidden
            self.mtp_kv = mtp_kv

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"tokens={self.tokens!r}")
            parts.append(f"cache={self.cache!r}")
            parts.append(f"logits={self.logits!r}")
            parts.append(f"hidden={self.hidden!r}")
            parts.append(f"mtp_kv={self.mtp_kv!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e66247fef380feb524f3d6543a3b59eabf70f441',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('snap', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('tier', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('nbytes', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('tick', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.prefixcache', '_Entry'),
    ),
)
def _process_dataclass__e66247fef380feb524f3d6543a3b59eabf70f441():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                snap=self.snap,
                tier=self.tier,
                nbytes=self.nbytes,
                tick=self.tick,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.snap == other.snap and
                self.tier == other.tier and
                self.nbytes == other.nbytes and
                self.tick == other.tick
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            snap: __dataclass__init__fields__0__annotation,
            tier: __dataclass__init__fields__1__annotation,
            nbytes: __dataclass__init__fields__2__annotation,
            tick: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            self.snap = snap
            self.tier = tier
            self.nbytes = nbytes
            self.tick = tick

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"snap={self.snap!r}")
            parts.append(f"tier={self.tier!r}")
            parts.append(f"nbytes={self.nbytes!r}")
            parts.append(f"tick={self.tick!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='dcf48406d81f2167fe6a5494e01e66407f477a82',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('messages', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('tools', True, True, None, True, False, False, None), 'instance', 'missi"
            "ng', None, False, False, False), (('stream', True, True, None, True, False, False, None), 'instance', 'mis"
            "sing', None, False, False, False), (('max_tokens', True, True, None, True, False, False, None), 'instance'"
            ", 'missing', None, False, False, False), (('temperature', True, True, None, True, False, False, None), 'in"
            "stance', 'missing', None, False, False, False), (('top_k', True, True, None, True, False, False, None), 'i"
            "nstance', 'missing', None, False, False, False), (('top_p', True, True, None, True, False, False, None), '"
            "instance', 'missing', None, False, False, False), (('min_p', True, True, None, True, False, False, None), "
            "'instance', 'missing', None, False, False, False), (('presence_penalty', True, True, None, True, False, Fa"
            "lse, None), 'instance', 'missing', None, False, False, False), (('frequency_penalty', True, True, None, Tr"
            "ue, False, False, None), 'instance', 'missing', None, False, False, False), (('seed', True, True, None, Tr"
            "ue, False, False, None), 'instance', 'missing', None, False, False, False), (('stop', True, True, None, Tr"
            "ue, False, False, None), 'instance', 'missing', None, False, False, False), (('enable_thinking', True, Tru"
            "e, None, True, False, False, None), 'instance', 'missing', None, False, False, False), (('model', True, Tr"
            "ue, None, True, False, False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((Fa"
            "lse,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.serving', 'Request'),
    ),
)
def _process_dataclass__dcf48406d81f2167fe6a5494e01e66407f477a82():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__01__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__02__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__03__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__04__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__05__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__06__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__07__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__08__annotation = __dataclass__spec.fields[8].annotation
        __dataclass__init__fields__09__annotation = __dataclass__spec.fields[9].annotation
        __dataclass__init__fields__10__annotation = __dataclass__spec.fields[10].annotation
        __dataclass__init__fields__11__annotation = __dataclass__spec.fields[11].annotation
        __dataclass__init__fields__12__annotation = __dataclass__spec.fields[12].annotation
        __dataclass__init__fields__13__annotation = __dataclass__spec.fields[13].annotation
        __dataclass__init__fields__13__default = __dataclass__spec.fields[13].default.must()
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                messages=self.messages,
                tools=self.tools,
                stream=self.stream,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_k=self.top_k,
                top_p=self.top_p,
                min_p=self.min_p,
                presence_penalty=self.presence_penalty,
                frequency_penalty=self.frequency_penalty,
                seed=self.seed,
                stop=self.stop,
                enable_thinking=self.enable_thinking,
                model=self.model,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.messages == other.messages and
                self.tools == other.tools and
                self.stream == other.stream and
                self.max_tokens == other.max_tokens and
                self.temperature == other.temperature and
                self.top_k == other.top_k and
                self.top_p == other.top_p and
                self.min_p == other.min_p and
                self.presence_penalty == other.presence_penalty and
                self.frequency_penalty == other.frequency_penalty and
                self.seed == other.seed and
                self.stop == other.stop and
                self.enable_thinking == other.enable_thinking and
                self.model == other.model
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            messages: __dataclass__init__fields__00__annotation,
            tools: __dataclass__init__fields__01__annotation,
            stream: __dataclass__init__fields__02__annotation,
            max_tokens: __dataclass__init__fields__03__annotation,
            temperature: __dataclass__init__fields__04__annotation,
            top_k: __dataclass__init__fields__05__annotation,
            top_p: __dataclass__init__fields__06__annotation,
            min_p: __dataclass__init__fields__07__annotation,
            presence_penalty: __dataclass__init__fields__08__annotation,
            frequency_penalty: __dataclass__init__fields__09__annotation,
            seed: __dataclass__init__fields__10__annotation,
            stop: __dataclass__init__fields__11__annotation,
            enable_thinking: __dataclass__init__fields__12__annotation,
            model: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
        ) -> __dataclass__None:
            self.messages = messages
            self.tools = tools
            self.stream = stream
            self.max_tokens = max_tokens
            self.temperature = temperature
            self.top_k = top_k
            self.top_p = top_p
            self.min_p = min_p
            self.presence_penalty = presence_penalty
            self.frequency_penalty = frequency_penalty
            self.seed = seed
            self.stop = stop
            self.enable_thinking = enable_thinking
            self.model = model

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"messages={self.messages!r}")
            parts.append(f"tools={self.tools!r}")
            parts.append(f"stream={self.stream!r}")
            parts.append(f"max_tokens={self.max_tokens!r}")
            parts.append(f"temperature={self.temperature!r}")
            parts.append(f"top_k={self.top_k!r}")
            parts.append(f"top_p={self.top_p!r}")
            parts.append(f"min_p={self.min_p!r}")
            parts.append(f"presence_penalty={self.presence_penalty!r}")
            parts.append(f"frequency_penalty={self.frequency_penalty!r}")
            parts.append(f"seed={self.seed!r}")
            parts.append(f"stop={self.stop!r}")
            parts.append(f"enable_thinking={self.enable_thinking!r}")
            parts.append(f"model={self.model!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c48019302faa066acad5f1cf315c314f2d11cec9',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('text', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('ids', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('content', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('reasoning', True, True, None, True, False, False, None), 'instance', 'mis"
            "sing', None, False, False, False), (('tool_calls', True, True, None, True, False, False, None), 'instance'"
            ", 'missing', None, False, False, False), (('finish_reason', True, True, None, True, False, False, None), '"
            "instance', 'missing', None, False, False, False), (('prompt_tokens', True, True, None, True, False, False,"
            " None), 'instance', 'missing', None, False, False, False), (('prompt_reused', True, True, None, True, Fals"
            "e, False, None), 'instance', 'missing', None, False, False, False), (('completion_tokens', True, True, Non"
            "e, True, False, False, None), 'instance', 'missing', None, False, False, False), (('prefill_s', True, True"
            ", None, True, False, False, None), 'instance', 'missing', None, False, False, False), (('total_s', True, T"
            "rue, None, True, False, False, None), 'instance', 'missing', None, False, False, False), (('spec_rounds', "
            "True, True, None, True, False, False, None), 'instance', 'missing', None, False, False, False), (('spec_ac"
            "cepted', True, True, None, True, False, False, None), 'instance', 'missing', None, False, False, False)), "
            "False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.serving', 'Result'),
    ),
)
def _process_dataclass__c48019302faa066acad5f1cf315c314f2d11cec9():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__01__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__02__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__03__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__04__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__05__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__06__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__07__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__08__annotation = __dataclass__spec.fields[8].annotation
        __dataclass__init__fields__09__annotation = __dataclass__spec.fields[9].annotation
        __dataclass__init__fields__10__annotation = __dataclass__spec.fields[10].annotation
        __dataclass__init__fields__11__annotation = __dataclass__spec.fields[11].annotation
        __dataclass__init__fields__12__annotation = __dataclass__spec.fields[12].annotation
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                text=self.text,
                ids=self.ids,
                content=self.content,
                reasoning=self.reasoning,
                tool_calls=self.tool_calls,
                finish_reason=self.finish_reason,
                prompt_tokens=self.prompt_tokens,
                prompt_reused=self.prompt_reused,
                completion_tokens=self.completion_tokens,
                prefill_s=self.prefill_s,
                total_s=self.total_s,
                spec_rounds=self.spec_rounds,
                spec_accepted=self.spec_accepted,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.text == other.text and
                self.ids == other.ids and
                self.content == other.content and
                self.reasoning == other.reasoning and
                self.tool_calls == other.tool_calls and
                self.finish_reason == other.finish_reason and
                self.prompt_tokens == other.prompt_tokens and
                self.prompt_reused == other.prompt_reused and
                self.completion_tokens == other.completion_tokens and
                self.prefill_s == other.prefill_s and
                self.total_s == other.total_s and
                self.spec_rounds == other.spec_rounds and
                self.spec_accepted == other.spec_accepted
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            text: __dataclass__init__fields__00__annotation,
            ids: __dataclass__init__fields__01__annotation,
            content: __dataclass__init__fields__02__annotation,
            reasoning: __dataclass__init__fields__03__annotation,
            tool_calls: __dataclass__init__fields__04__annotation,
            finish_reason: __dataclass__init__fields__05__annotation,
            prompt_tokens: __dataclass__init__fields__06__annotation,
            prompt_reused: __dataclass__init__fields__07__annotation,
            completion_tokens: __dataclass__init__fields__08__annotation,
            prefill_s: __dataclass__init__fields__09__annotation,
            total_s: __dataclass__init__fields__10__annotation,
            spec_rounds: __dataclass__init__fields__11__annotation,
            spec_accepted: __dataclass__init__fields__12__annotation,
        ) -> __dataclass__None:
            self.text = text
            self.ids = ids
            self.content = content
            self.reasoning = reasoning
            self.tool_calls = tool_calls
            self.finish_reason = finish_reason
            self.prompt_tokens = prompt_tokens
            self.prompt_reused = prompt_reused
            self.completion_tokens = completion_tokens
            self.prefill_s = prefill_s
            self.total_s = total_s
            self.spec_rounds = spec_rounds
            self.spec_accepted = spec_accepted

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"text={self.text!r}")
            parts.append(f"ids={self.ids!r}")
            parts.append(f"content={self.content!r}")
            parts.append(f"reasoning={self.reasoning!r}")
            parts.append(f"tool_calls={self.tool_calls!r}")
            parts.append(f"finish_reason={self.finish_reason!r}")
            parts.append(f"prompt_tokens={self.prompt_tokens!r}")
            parts.append(f"prompt_reused={self.prompt_reused!r}")
            parts.append(f"completion_tokens={self.completion_tokens!r}")
            parts.append(f"prefill_s={self.prefill_s!r}")
            parts.append(f"total_s={self.total_s!r}")
            parts.append(f"spec_rounds={self.spec_rounds!r}")
            parts.append(f"spec_accepted={self.spec_accepted!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='aeadcd505a0473f653f113d5ce934ef122ec3caa',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('temperature', True, True, None, True, False, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('top_k', True, True, None, True, False, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('top_p', True, True, None, True, False, False, None), 'instance', 'value"
            "', None, False, False, False), (('min_p', True, True, None, True, False, False, None), 'instance', 'value'"
            ", None, False, False, False), (('presence_penalty', True, True, None, True, False, False, None), 'instance"
            "', 'value', None, False, False, False), (('frequency_penalty', True, True, None, True, False, False, None)"
            ", 'instance', 'value', None, False, False, False), (('max_tokens', True, True, None, True, False, False, N"
            "one), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), "
            "(False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.serving', 'SamplingDefaults'),
    ),
)
def _process_dataclass__aeadcd505a0473f653f113d5ce934ef122ec3caa():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                temperature=self.temperature,
                top_k=self.top_k,
                top_p=self.top_p,
                min_p=self.min_p,
                presence_penalty=self.presence_penalty,
                frequency_penalty=self.frequency_penalty,
                max_tokens=self.max_tokens,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.temperature == other.temperature and
                self.top_k == other.top_k and
                self.top_p == other.top_p and
                self.min_p == other.min_p and
                self.presence_penalty == other.presence_penalty and
                self.frequency_penalty == other.frequency_penalty and
                self.max_tokens == other.max_tokens
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            temperature: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            top_k: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            top_p: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            min_p: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            presence_penalty: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            frequency_penalty: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            max_tokens: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
        ) -> __dataclass__None:
            self.temperature = temperature
            self.top_k = top_k
            self.top_p = top_p
            self.min_p = min_p
            self.presence_penalty = presence_penalty
            self.frequency_penalty = frequency_penalty
            self.max_tokens = max_tokens

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"temperature={self.temperature!r}")
            parts.append(f"top_k={self.top_k!r}")
            parts.append(f"top_p={self.top_p!r}")
            parts.append(f"min_p={self.min_p!r}")
            parts.append(f"presence_penalty={self.presence_penalty!r}")
            parts.append(f"frequency_penalty={self.frequency_penalty!r}")
            parts.append(f"max_tokens={self.max_tokens!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='3ff2a1d64778c1fea14e350f65e18aa8fae199f8',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('values', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('scale', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('bias', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('bits', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('group', True, True, None, True, False, False, None), 'instance', 'missin"
            "g', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (()"
            ",), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.weights', 'NativeQuant'),
    ),
)
def _process_dataclass__3ff2a1d64778c1fea14e350f65e18aa8fae199f8():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                values=self.values,
                scale=self.scale,
                bias=self.bias,
                bits=self.bits,
                group=self.group,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.values == other.values and
                self.scale == other.scale and
                self.bias == other.bias and
                self.bits == other.bits and
                self.group == other.group
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            values: __dataclass__init__fields__0__annotation,
            scale: __dataclass__init__fields__1__annotation,
            bias: __dataclass__init__fields__2__annotation,
            bits: __dataclass__init__fields__3__annotation,
            group: __dataclass__init__fields__4__annotation,
        ) -> __dataclass__None:
            self.values = values
            self.scale = scale
            self.bias = bias
            self.bits = bits
            self.group = group

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"values={self.values!r}")
            parts.append(f"scale={self.scale!r}")
            parts.append(f"bias={self.bias!r}")
            parts.append(f"bits={self.bits!r}")
            parts.append(f"group={self.group!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='04795627c6271cd9b38624010a3d28e1289b1586',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('manifest_path', True, True, None, True, False, False, None), 'instance', 'm"
            "issing', None, False, False, False), (('manifest', True, True, None, True, False, False, None), 'instance'"
            ", 'missing', None, False, False, False), (('blobs_dir', True, True, None, True, False, False, None), 'inst"
            "ance', 'missing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, F"
            "alse, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.weights', 'OllamaModel'),
    ),
)
def _process_dataclass__04795627c6271cd9b38624010a3d28e1289b1586():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                manifest_path=self.manifest_path,
                manifest=self.manifest,
                blobs_dir=self.blobs_dir,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.manifest_path == other.manifest_path and
                self.manifest == other.manifest and
                self.blobs_dir == other.blobs_dir
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            manifest_path: __dataclass__init__fields__0__annotation,
            manifest: __dataclass__init__fields__1__annotation,
            blobs_dir: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            self.manifest_path = manifest_path
            self.manifest = manifest
            self.blobs_dir = blobs_dir

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"manifest_path={self.manifest_path!r}")
            parts.append(f"manifest={self.manifest!r}")
            parts.append(f"blobs_dir={self.blobs_dir!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='0c7f910a58079f6f388c514a35dab18d80a24ed6',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('vocab_size', True, True, None, True, False, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('hidden_size', True, True, None, True, False, False, None), 'instance'"
            ", 'missing', None, False, False, False), (('num_layers', True, True, None, True, False, False, None), 'ins"
            "tance', 'missing', None, False, False, False), (('intermediate_size', True, True, None, True, False, False"
            ", None), 'instance', 'missing', None, False, False, False), (('rms_eps', True, True, None, True, False, Fa"
            "lse, None), 'instance', 'missing', None, False, False, False), (('num_heads', True, True, None, True, Fals"
            "e, False, None), 'instance', 'missing', None, False, False, False), (('num_kv_heads', True, True, None, Tr"
            "ue, False, False, None), 'instance', 'missing', None, False, False, False), (('head_dim', True, True, None"
            ", True, False, False, None), 'instance', 'missing', None, False, False, False), (('rope_theta', True, True"
            ", None, True, False, False, None), 'instance', 'missing', None, False, False, False), (('rope_dim', True, "
            "True, None, True, False, False, None), 'instance', 'missing', None, False, False, False), (('num_k_heads',"
            " True, True, None, True, False, False, None), 'instance', 'missing', None, False, False, False), (('num_v_"
            "heads', True, True, None, True, False, False, None), 'instance', 'missing', None, False, False, False), (("
            "'head_k_dim', True, True, None, True, False, False, None), 'instance', 'missing', None, False, False, Fals"
            "e), (('head_v_dim', True, True, None, True, False, False, None), 'instance', 'missing', None, False, False"
            ", False), (('conv_kernel', True, True, None, True, False, False, None), 'instance', 'missing', None, False"
            ", False, False), (('layer_types', True, True, None, True, False, False, None), 'instance', 'missing', None"
            ", False, False, False), (('context_length', True, True, None, True, False, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('rope_scaling', True, True, None, True, False, False, None), 'instance',"
            " 'value', None, False, False, False), (('tied_embeddings', True, True, None, True, False, False, None), 'i"
            "nstance', 'value', None, False, False, False), (('num_mtp_layers', True, True, None, True, False, False, N"
            "one), 'instance', 'value', None, False, False, False), (('extra', True, True, None, True, False, False, No"
            "ne), 'instance', 'factory', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,),"
            " (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.weights', 'Qwen35Config'),
    ),
)
def _process_dataclass__0c7f910a58079f6f388c514a35dab18d80a24ed6():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__01__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__02__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__03__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__04__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__05__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__06__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__07__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__08__annotation = __dataclass__spec.fields[8].annotation
        __dataclass__init__fields__09__annotation = __dataclass__spec.fields[9].annotation
        __dataclass__init__fields__10__annotation = __dataclass__spec.fields[10].annotation
        __dataclass__init__fields__11__annotation = __dataclass__spec.fields[11].annotation
        __dataclass__init__fields__12__annotation = __dataclass__spec.fields[12].annotation
        __dataclass__init__fields__13__annotation = __dataclass__spec.fields[13].annotation
        __dataclass__init__fields__14__annotation = __dataclass__spec.fields[14].annotation
        __dataclass__init__fields__15__annotation = __dataclass__spec.fields[15].annotation
        __dataclass__init__fields__16__annotation = __dataclass__spec.fields[16].annotation
        __dataclass__init__fields__16__default = __dataclass__spec.fields[16].default.must()
        __dataclass__init__fields__17__annotation = __dataclass__spec.fields[17].annotation
        __dataclass__init__fields__17__default = __dataclass__spec.fields[17].default.must()
        __dataclass__init__fields__18__annotation = __dataclass__spec.fields[18].annotation
        __dataclass__init__fields__18__default = __dataclass__spec.fields[18].default.must()
        __dataclass__init__fields__19__annotation = __dataclass__spec.fields[19].annotation
        __dataclass__init__fields__19__default = __dataclass__spec.fields[19].default.must()
        __dataclass__init__fields__20__annotation = __dataclass__spec.fields[20].annotation
        __dataclass__init__fields__20__default_factory = __dataclass__spec.fields[20].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                vocab_size=self.vocab_size,
                hidden_size=self.hidden_size,
                num_layers=self.num_layers,
                intermediate_size=self.intermediate_size,
                rms_eps=self.rms_eps,
                num_heads=self.num_heads,
                num_kv_heads=self.num_kv_heads,
                head_dim=self.head_dim,
                rope_theta=self.rope_theta,
                rope_dim=self.rope_dim,
                num_k_heads=self.num_k_heads,
                num_v_heads=self.num_v_heads,
                head_k_dim=self.head_k_dim,
                head_v_dim=self.head_v_dim,
                conv_kernel=self.conv_kernel,
                layer_types=self.layer_types,
                context_length=self.context_length,
                rope_scaling=self.rope_scaling,
                tied_embeddings=self.tied_embeddings,
                num_mtp_layers=self.num_mtp_layers,
                extra=self.extra,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.vocab_size == other.vocab_size and
                self.hidden_size == other.hidden_size and
                self.num_layers == other.num_layers and
                self.intermediate_size == other.intermediate_size and
                self.rms_eps == other.rms_eps and
                self.num_heads == other.num_heads and
                self.num_kv_heads == other.num_kv_heads and
                self.head_dim == other.head_dim and
                self.rope_theta == other.rope_theta and
                self.rope_dim == other.rope_dim and
                self.num_k_heads == other.num_k_heads and
                self.num_v_heads == other.num_v_heads and
                self.head_k_dim == other.head_k_dim and
                self.head_v_dim == other.head_v_dim and
                self.conv_kernel == other.conv_kernel and
                self.layer_types == other.layer_types and
                self.context_length == other.context_length and
                self.rope_scaling == other.rope_scaling and
                self.tied_embeddings == other.tied_embeddings and
                self.num_mtp_layers == other.num_mtp_layers and
                self.extra == other.extra
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            vocab_size: __dataclass__init__fields__00__annotation,
            hidden_size: __dataclass__init__fields__01__annotation,
            num_layers: __dataclass__init__fields__02__annotation,
            intermediate_size: __dataclass__init__fields__03__annotation,
            rms_eps: __dataclass__init__fields__04__annotation,
            num_heads: __dataclass__init__fields__05__annotation,
            num_kv_heads: __dataclass__init__fields__06__annotation,
            head_dim: __dataclass__init__fields__07__annotation,
            rope_theta: __dataclass__init__fields__08__annotation,
            rope_dim: __dataclass__init__fields__09__annotation,
            num_k_heads: __dataclass__init__fields__10__annotation,
            num_v_heads: __dataclass__init__fields__11__annotation,
            head_k_dim: __dataclass__init__fields__12__annotation,
            head_v_dim: __dataclass__init__fields__13__annotation,
            conv_kernel: __dataclass__init__fields__14__annotation,
            layer_types: __dataclass__init__fields__15__annotation,
            context_length: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            rope_scaling: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
            tied_embeddings: __dataclass__init__fields__18__annotation = __dataclass__init__fields__18__default,
            num_mtp_layers: __dataclass__init__fields__19__annotation = __dataclass__init__fields__19__default,
            extra: __dataclass__init__fields__20__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if extra is __dataclass__HAS_DEFAULT_FACTORY:
                extra = __dataclass__init__fields__20__default_factory()
            self.vocab_size = vocab_size
            self.hidden_size = hidden_size
            self.num_layers = num_layers
            self.intermediate_size = intermediate_size
            self.rms_eps = rms_eps
            self.num_heads = num_heads
            self.num_kv_heads = num_kv_heads
            self.head_dim = head_dim
            self.rope_theta = rope_theta
            self.rope_dim = rope_dim
            self.num_k_heads = num_k_heads
            self.num_v_heads = num_v_heads
            self.head_k_dim = head_k_dim
            self.head_v_dim = head_v_dim
            self.conv_kernel = conv_kernel
            self.layer_types = layer_types
            self.context_length = context_length
            self.rope_scaling = rope_scaling
            self.tied_embeddings = tied_embeddings
            self.num_mtp_layers = num_mtp_layers
            self.extra = extra

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"vocab_size={self.vocab_size!r}")
            parts.append(f"hidden_size={self.hidden_size!r}")
            parts.append(f"num_layers={self.num_layers!r}")
            parts.append(f"intermediate_size={self.intermediate_size!r}")
            parts.append(f"rms_eps={self.rms_eps!r}")
            parts.append(f"num_heads={self.num_heads!r}")
            parts.append(f"num_kv_heads={self.num_kv_heads!r}")
            parts.append(f"head_dim={self.head_dim!r}")
            parts.append(f"rope_theta={self.rope_theta!r}")
            parts.append(f"rope_dim={self.rope_dim!r}")
            parts.append(f"num_k_heads={self.num_k_heads!r}")
            parts.append(f"num_v_heads={self.num_v_heads!r}")
            parts.append(f"head_k_dim={self.head_k_dim!r}")
            parts.append(f"head_v_dim={self.head_v_dim!r}")
            parts.append(f"conv_kernel={self.conv_kernel!r}")
            parts.append(f"layer_types={self.layer_types!r}")
            parts.append(f"context_length={self.context_length!r}")
            parts.append(f"rope_scaling={self.rope_scaling!r}")
            parts.append(f"tied_embeddings={self.tied_embeddings!r}")
            parts.append(f"num_mtp_layers={self.num_mtp_layers!r}")
            parts.append(f"extra={self.extra!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
