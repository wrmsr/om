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


IMPLEMENTATION_KEY = 'b737c9e9784700f75d0a861cde465d33397d28232b0b31eac8c2d80a2eb74101'


@_register(
    installer_sha1='c1baa586f55fa012c3b8651e8602532e6fe03b35',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('backend', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('device', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('kv_dtype', True, True, None, True, False, False, None), 'instance', 'value'"
            ", None, False, False, False), (('compile', True, True, None, True, False, False, None), 'instance', 'value"
            "', None, False, False, False), (('compile_cache_dir', True, True, None, True, False, False, None), 'instan"
            "ce', 'value', None, False, False, False), (('triton_tuned', True, True, None, True, False, False, None), '"
            "instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False,"
            " False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.backends.inject', 'BackendConfig'),
    ),
)
def _process_dataclass__c1baa586f55fa012c3b8651e8602532e6fe03b35():
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
                backend=self.backend,
                device=self.device,
                kv_dtype=self.kv_dtype,
                compile=self.compile,
                compile_cache_dir=self.compile_cache_dir,
                triton_tuned=self.triton_tuned,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.backend == other.backend and
                self.device == other.device and
                self.kv_dtype == other.kv_dtype and
                self.compile == other.compile and
                self.compile_cache_dir == other.compile_cache_dir and
                self.triton_tuned == other.triton_tuned
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'backend',
            'device',
            'kv_dtype',
            'compile',
            'compile_cache_dir',
            'triton_tuned',
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
                self.backend,
                self.device,
                self.kv_dtype,
                self.compile,
                self.compile_cache_dir,
                self.triton_tuned,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            backend: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            device: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            kv_dtype: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            compile: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            compile_cache_dir: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            triton_tuned: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'backend', backend)
            __dataclass__object_setattr(self, 'device', device)
            __dataclass__object_setattr(self, 'kv_dtype', kv_dtype)
            __dataclass__object_setattr(self, 'compile', compile)
            __dataclass__object_setattr(self, 'compile_cache_dir', compile_cache_dir)
            __dataclass__object_setattr(self, 'triton_tuned', triton_tuned)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"backend={self.backend!r}")
            parts.append(f"device={self.device!r}")
            parts.append(f"kv_dtype={self.kv_dtype!r}")
            parts.append(f"compile={self.compile!r}")
            parts.append(f"compile_cache_dir={self.compile_cache_dir!r}")
            parts.append(f"triton_tuned={self.triton_tuned!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='73fa29e6a5ed12e668ab903c3a600466a6071e97',
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
def _process_dataclass__73fa29e6a5ed12e668ab903c3a600466a6071e97():
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
    installer_sha1='030e598f2fd59ebe3517822a2ee45e56cbb497ac',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('q', True, True, None, True, False, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('scale', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('bias', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('bits', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('group', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('shape', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('shifts', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('GEMV_MAX_M', True, True, None, True, None, False, None), 'class_var', 'va"
            "lue', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ("
            "(),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.backends.tinygrad', 'TinyQWeight'),
    ),
)
def _process_dataclass__030e598f2fd59ebe3517822a2ee45e56cbb497ac():
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
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__7__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__7__default = __dataclass__spec.fields[7].default.must()
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
                shifts=self.shifts,
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
                self.shape == other.shape and
                self.shifts == other.shifts
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
            shifts: __dataclass__init__fields__6__annotation,
        ) -> __dataclass__None:
            self.q = q
            self.scale = scale
            self.bias = bias
            self.bits = bits
            self.group = group
            self.shape = shape
            self.shifts = shifts

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
            parts.append(f"shifts={self.shifts!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='971d90b1116a2f9b60d8a87a9013958cf369f75b',
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
        ('omllm.local.qwen.backends.torch', 'TorchQExperts'),
        ('omllm.local.qwen.ops.quant', 'QWeight'),
    ),
)
def _process_dataclass__971d90b1116a2f9b60d8a87a9013958cf369f75b():
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
    installer_sha1='af59a89e71e2384e635fac46e0695509328d7c0f',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('q', True, True, None, True, False, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('scale', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('bias', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('bits', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('group', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('shape', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('launch', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.backends.torch', 'TorchQWeight'),
    ),
)
def _process_dataclass__af59a89e71e2384e635fac46e0695509328d7c0f():
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
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__6__default = __dataclass__spec.fields[6].default.must()
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
                launch=self.launch,
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
                self.shape == other.shape and
                self.launch == other.launch
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
            launch: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
        ) -> __dataclass__None:
            self.q = q
            self.scale = scale
            self.bias = bias
            self.bits = bits
            self.group = group
            self.shape = shape
            self.launch = launch

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
            parts.append(f"launch={self.launch!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='9eb19e80462f60f885c4278e8e544ce51a228b7c',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('tok', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('schema', True, True, None, True, False, False, None), 'instance', 'value', N"
            "one, False, False, False), (('thinking', True, True, None, True, False, False, None), 'instance', 'value',"
            " None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, True, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.constrain.grammar', 'JsonConstraint'),
    ),
)
def _process_dataclass__9eb19e80462f60f885c4278e8e544ce51a228b7c():
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
                tok=self.tok,
                schema=self.schema,
                thinking=self.thinking,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.tok == other.tok and
                self.schema == other.schema and
                self.thinking == other.thinking
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            tok: __dataclass__init__fields__0__annotation,
            schema: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            thinking: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            self.tok = tok
            self.schema = schema
            self.thinking = thinking
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"tok={self.tok!r}")
            parts.append(f"schema={self.schema!r}")
            parts.append(f"thinking={self.thinking!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c70ce9ed277dec4c7b15e920f95e8366be668461',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('tok', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('tools', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('tool_choice', True, True, None, True, False, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('thinking', True, True, None, True, False, False, None), 'instance', 'v"
            "alue', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, True, ()), ("
            "(),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.constrain.grammar', 'ToolConstraint'),
    ),
)
def _process_dataclass__c70ce9ed277dec4c7b15e920f95e8366be668461():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                tok=self.tok,
                tools=self.tools,
                tool_choice=self.tool_choice,
                thinking=self.thinking,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.tok == other.tok and
                self.tools == other.tools and
                self.tool_choice == other.tool_choice and
                self.thinking == other.thinking
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            tok: __dataclass__init__fields__0__annotation,
            tools: __dataclass__init__fields__1__annotation,
            tool_choice: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            thinking: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            self.tok = tok
            self.tools = tools
            self.tool_choice = tool_choice
            self.thinking = thinking
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"tok={self.tok!r}")
            parts.append(f"tools={self.tools!r}")
            parts.append(f"tool_choice={self.tool_choice!r}")
            parts.append(f"thinking={self.thinking!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='86043281ca224260645c0328594c6c7f145f419c',
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
            "one), 'instance', 'value', None, False, False, False), (('output_gate', True, True, None, True, False, Fal"
            "se, None), 'instance', 'value', None, False, False, False), (('extra', True, True, None, True, False, Fals"
            "e, None), 'instance', 'factory', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (Fal"
            "se,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.core.config', 'Qwen35Config'),
    ),
)
def _process_dataclass__86043281ca224260645c0328594c6c7f145f419c():
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
        __dataclass__init__fields__20__default = __dataclass__spec.fields[20].default.must()
        __dataclass__init__fields__21__annotation = __dataclass__spec.fields[21].annotation
        __dataclass__init__fields__21__default_factory = __dataclass__spec.fields[21].default.must().fn
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
                output_gate=self.output_gate,
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
                self.output_gate == other.output_gate and
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
            output_gate: __dataclass__init__fields__20__annotation = __dataclass__init__fields__20__default,
            extra: __dataclass__init__fields__21__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if extra is __dataclass__HAS_DEFAULT_FACTORY:
                extra = __dataclass__init__fields__21__default_factory()
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
            self.output_gate = output_gate
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
            parts.append(f"output_gate={self.output_gate!r}")
            parts.append(f"extra={self.extra!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e79f1626b80b0af441173b1bec386ec889b53a1d',
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
            "one), 'instance', 'value', None, False, False, False), (('output_gate', True, True, None, True, False, Fal"
            "se, None), 'instance', 'value', None, False, False, False), (('extra', True, True, None, True, False, Fals"
            "e, None), 'instance', 'factory', None, False, False, False), (('num_experts', True, True, None, True, Fals"
            "e, False, None), 'instance', 'value', None, False, False, False), (('num_experts_per_tok', True, True, Non"
            "e, True, False, False, None), 'instance', 'value', None, False, False, False), (('moe_intermediate_size', "
            "True, True, None, True, False, False, None), 'instance', 'value', None, False, False, False), (('shared_ex"
            "pert_intermediate_size', True, True, None, True, False, False, None), 'instance', 'value', None, False, Fa"
            "lse, False), (('norm_topk_prob', True, True, None, True, False, False, None), 'instance', 'value', None, F"
            "alse, False, False), (('hc_count', True, True, None, True, False, False, None), 'instance', 'value', None,"
            " False, False, False), (('hc_lowrank', True, True, None, True, False, False, None), 'instance', 'value', N"
            "one, False, False, False), (('indexer_heads', True, True, None, True, False, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('indexer_head_dim', True, True, None, True, False, False, None), 'inst"
            "ance', 'value', None, False, False, False), (('indexer_budget', True, True, None, True, False, False, None"
            "), 'instance', 'value', None, False, False, False), (('indexer_compress_ratio', True, True, None, True, Fa"
            "lse, False, None), 'instance', 'value', None, False, False, False), (('ple_layers', True, True, None, True"
            ", False, False, None), 'instance', 'factory', None, False, False, False), (('ple_embed_dim', True, True, N"
            "one, True, False, False, None), 'instance', 'value', None, False, False, False), (('ple_conv_kernel', True"
            ", True, None, True, False, False, None), 'instance', 'value', None, False, False, False), (('ngram_size', "
            "True, True, None, True, False, False, None), 'instance', 'value', None, False, False, False), (('heads_per"
            "_ngram', True, True, None, True, False, False, None), 'instance', 'value', None, False, False, False), (('"
            "ngram_vocab_size_base', True, True, None, True, False, False, None), 'instance', 'value', None, False, Fal"
            "se, False), (('ngram_vocab_divisor', True, True, None, True, False, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('ngram_seed', True, True, None, True, False, False, None), 'instance', 'value',"
            " None, False, False, False), (('eos_id', True, True, None, True, False, False, None), 'instance', 'value',"
            " None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.core.config', 'Qwen4ExpConfig'),
    ),
)
def _process_dataclass__e79f1626b80b0af441173b1bec386ec889b53a1d():
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
        __dataclass__init__fields__20__default = __dataclass__spec.fields[20].default.must()
        __dataclass__init__fields__21__annotation = __dataclass__spec.fields[21].annotation
        __dataclass__init__fields__21__default_factory = __dataclass__spec.fields[21].default.must().fn
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
        __dataclass__init__fields__30__annotation = __dataclass__spec.fields[30].annotation
        __dataclass__init__fields__30__default = __dataclass__spec.fields[30].default.must()
        __dataclass__init__fields__31__annotation = __dataclass__spec.fields[31].annotation
        __dataclass__init__fields__31__default = __dataclass__spec.fields[31].default.must()
        __dataclass__init__fields__32__annotation = __dataclass__spec.fields[32].annotation
        __dataclass__init__fields__32__default = __dataclass__spec.fields[32].default.must()
        __dataclass__init__fields__33__annotation = __dataclass__spec.fields[33].annotation
        __dataclass__init__fields__33__default_factory = __dataclass__spec.fields[33].default.must().fn
        __dataclass__init__fields__34__annotation = __dataclass__spec.fields[34].annotation
        __dataclass__init__fields__34__default = __dataclass__spec.fields[34].default.must()
        __dataclass__init__fields__35__annotation = __dataclass__spec.fields[35].annotation
        __dataclass__init__fields__35__default = __dataclass__spec.fields[35].default.must()
        __dataclass__init__fields__36__annotation = __dataclass__spec.fields[36].annotation
        __dataclass__init__fields__36__default = __dataclass__spec.fields[36].default.must()
        __dataclass__init__fields__37__annotation = __dataclass__spec.fields[37].annotation
        __dataclass__init__fields__37__default = __dataclass__spec.fields[37].default.must()
        __dataclass__init__fields__38__annotation = __dataclass__spec.fields[38].annotation
        __dataclass__init__fields__38__default = __dataclass__spec.fields[38].default.must()
        __dataclass__init__fields__39__annotation = __dataclass__spec.fields[39].annotation
        __dataclass__init__fields__39__default = __dataclass__spec.fields[39].default.must()
        __dataclass__init__fields__40__annotation = __dataclass__spec.fields[40].annotation
        __dataclass__init__fields__40__default = __dataclass__spec.fields[40].default.must()
        __dataclass__init__fields__41__annotation = __dataclass__spec.fields[41].annotation
        __dataclass__init__fields__41__default = __dataclass__spec.fields[41].default.must()
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
                output_gate=self.output_gate,
                extra=self.extra,
                num_experts=self.num_experts,
                num_experts_per_tok=self.num_experts_per_tok,
                moe_intermediate_size=self.moe_intermediate_size,
                shared_expert_intermediate_size=self.shared_expert_intermediate_size,
                norm_topk_prob=self.norm_topk_prob,
                hc_count=self.hc_count,
                hc_lowrank=self.hc_lowrank,
                indexer_heads=self.indexer_heads,
                indexer_head_dim=self.indexer_head_dim,
                indexer_budget=self.indexer_budget,
                indexer_compress_ratio=self.indexer_compress_ratio,
                ple_layers=self.ple_layers,
                ple_embed_dim=self.ple_embed_dim,
                ple_conv_kernel=self.ple_conv_kernel,
                ngram_size=self.ngram_size,
                heads_per_ngram=self.heads_per_ngram,
                ngram_vocab_size_base=self.ngram_vocab_size_base,
                ngram_vocab_divisor=self.ngram_vocab_divisor,
                ngram_seed=self.ngram_seed,
                eos_id=self.eos_id,
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
                self.output_gate == other.output_gate and
                self.extra == other.extra and
                self.num_experts == other.num_experts and
                self.num_experts_per_tok == other.num_experts_per_tok and
                self.moe_intermediate_size == other.moe_intermediate_size and
                self.shared_expert_intermediate_size == other.shared_expert_intermediate_size and
                self.norm_topk_prob == other.norm_topk_prob and
                self.hc_count == other.hc_count and
                self.hc_lowrank == other.hc_lowrank and
                self.indexer_heads == other.indexer_heads and
                self.indexer_head_dim == other.indexer_head_dim and
                self.indexer_budget == other.indexer_budget and
                self.indexer_compress_ratio == other.indexer_compress_ratio and
                self.ple_layers == other.ple_layers and
                self.ple_embed_dim == other.ple_embed_dim and
                self.ple_conv_kernel == other.ple_conv_kernel and
                self.ngram_size == other.ngram_size and
                self.heads_per_ngram == other.heads_per_ngram and
                self.ngram_vocab_size_base == other.ngram_vocab_size_base and
                self.ngram_vocab_divisor == other.ngram_vocab_divisor and
                self.ngram_seed == other.ngram_seed and
                self.eos_id == other.eos_id
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
            output_gate: __dataclass__init__fields__20__annotation = __dataclass__init__fields__20__default,
            extra: __dataclass__init__fields__21__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            num_experts: __dataclass__init__fields__22__annotation = __dataclass__init__fields__22__default,
            num_experts_per_tok: __dataclass__init__fields__23__annotation = __dataclass__init__fields__23__default,
            moe_intermediate_size: __dataclass__init__fields__24__annotation = __dataclass__init__fields__24__default,
            shared_expert_intermediate_size: __dataclass__init__fields__25__annotation = __dataclass__init__fields__25__default,
            norm_topk_prob: __dataclass__init__fields__26__annotation = __dataclass__init__fields__26__default,
            hc_count: __dataclass__init__fields__27__annotation = __dataclass__init__fields__27__default,
            hc_lowrank: __dataclass__init__fields__28__annotation = __dataclass__init__fields__28__default,
            indexer_heads: __dataclass__init__fields__29__annotation = __dataclass__init__fields__29__default,
            indexer_head_dim: __dataclass__init__fields__30__annotation = __dataclass__init__fields__30__default,
            indexer_budget: __dataclass__init__fields__31__annotation = __dataclass__init__fields__31__default,
            indexer_compress_ratio: __dataclass__init__fields__32__annotation = __dataclass__init__fields__32__default,
            ple_layers: __dataclass__init__fields__33__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            ple_embed_dim: __dataclass__init__fields__34__annotation = __dataclass__init__fields__34__default,
            ple_conv_kernel: __dataclass__init__fields__35__annotation = __dataclass__init__fields__35__default,
            ngram_size: __dataclass__init__fields__36__annotation = __dataclass__init__fields__36__default,
            heads_per_ngram: __dataclass__init__fields__37__annotation = __dataclass__init__fields__37__default,
            ngram_vocab_size_base: __dataclass__init__fields__38__annotation = __dataclass__init__fields__38__default,
            ngram_vocab_divisor: __dataclass__init__fields__39__annotation = __dataclass__init__fields__39__default,
            ngram_seed: __dataclass__init__fields__40__annotation = __dataclass__init__fields__40__default,
            eos_id: __dataclass__init__fields__41__annotation = __dataclass__init__fields__41__default,
        ) -> __dataclass__None:
            if extra is __dataclass__HAS_DEFAULT_FACTORY:
                extra = __dataclass__init__fields__21__default_factory()
            if ple_layers is __dataclass__HAS_DEFAULT_FACTORY:
                ple_layers = __dataclass__init__fields__33__default_factory()
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
            self.output_gate = output_gate
            self.extra = extra
            self.num_experts = num_experts
            self.num_experts_per_tok = num_experts_per_tok
            self.moe_intermediate_size = moe_intermediate_size
            self.shared_expert_intermediate_size = shared_expert_intermediate_size
            self.norm_topk_prob = norm_topk_prob
            self.hc_count = hc_count
            self.hc_lowrank = hc_lowrank
            self.indexer_heads = indexer_heads
            self.indexer_head_dim = indexer_head_dim
            self.indexer_budget = indexer_budget
            self.indexer_compress_ratio = indexer_compress_ratio
            self.ple_layers = ple_layers
            self.ple_embed_dim = ple_embed_dim
            self.ple_conv_kernel = ple_conv_kernel
            self.ngram_size = ngram_size
            self.heads_per_ngram = heads_per_ngram
            self.ngram_vocab_size_base = ngram_vocab_size_base
            self.ngram_vocab_divisor = ngram_vocab_divisor
            self.ngram_seed = ngram_seed
            self.eos_id = eos_id

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
            parts.append(f"output_gate={self.output_gate!r}")
            parts.append(f"extra={self.extra!r}")
            parts.append(f"num_experts={self.num_experts!r}")
            parts.append(f"num_experts_per_tok={self.num_experts_per_tok!r}")
            parts.append(f"moe_intermediate_size={self.moe_intermediate_size!r}")
            parts.append(f"shared_expert_intermediate_size={self.shared_expert_intermediate_size!r}")
            parts.append(f"norm_topk_prob={self.norm_topk_prob!r}")
            parts.append(f"hc_count={self.hc_count!r}")
            parts.append(f"hc_lowrank={self.hc_lowrank!r}")
            parts.append(f"indexer_heads={self.indexer_heads!r}")
            parts.append(f"indexer_head_dim={self.indexer_head_dim!r}")
            parts.append(f"indexer_budget={self.indexer_budget!r}")
            parts.append(f"indexer_compress_ratio={self.indexer_compress_ratio!r}")
            parts.append(f"ple_layers={self.ple_layers!r}")
            parts.append(f"ple_embed_dim={self.ple_embed_dim!r}")
            parts.append(f"ple_conv_kernel={self.ple_conv_kernel!r}")
            parts.append(f"ngram_size={self.ngram_size!r}")
            parts.append(f"heads_per_ngram={self.heads_per_ngram!r}")
            parts.append(f"ngram_vocab_size_base={self.ngram_vocab_size_base!r}")
            parts.append(f"ngram_vocab_divisor={self.ngram_vocab_divisor!r}")
            parts.append(f"ngram_seed={self.ngram_seed!r}")
            parts.append(f"eos_id={self.eos_id!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='8d77c87bb5f0e26bd86cc6a93a343105817f8be3',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('tokens', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('prompt_tokens', True, True, None, True, False, False, None), 'instance', '"
            "missing', None, False, False, False), (('reused', True, True, None, True, False, False, None), 'instance',"
            " 'missing', None, False, False, False), (('rounds', True, True, None, True, False, False, None), 'instance"
            "', 'value', None, False, False, False), (('drafted', True, True, None, True, False, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('accepted', True, True, None, True, False, False, None), 'insta"
            "nce', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, Fals"
            "e, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.decode.generation', 'Generated'),
    ),
)
def _process_dataclass__8d77c87bb5f0e26bd86cc6a93a343105817f8be3():
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
                tokens=self.tokens,
                prompt_tokens=self.prompt_tokens,
                reused=self.reused,
                rounds=self.rounds,
                drafted=self.drafted,
                accepted=self.accepted,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.tokens == other.tokens and
                self.prompt_tokens == other.prompt_tokens and
                self.reused == other.reused and
                self.rounds == other.rounds and
                self.drafted == other.drafted and
                self.accepted == other.accepted
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'tokens',
            'prompt_tokens',
            'reused',
            'rounds',
            'drafted',
            'accepted',
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
                self.tokens,
                self.prompt_tokens,
                self.reused,
                self.rounds,
                self.drafted,
                self.accepted,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            tokens: __dataclass__init__fields__0__annotation,
            prompt_tokens: __dataclass__init__fields__1__annotation,
            reused: __dataclass__init__fields__2__annotation,
            rounds: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            drafted: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            accepted: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'tokens', tokens)
            __dataclass__object_setattr(self, 'prompt_tokens', prompt_tokens)
            __dataclass__object_setattr(self, 'reused', reused)
            __dataclass__object_setattr(self, 'rounds', rounds)
            __dataclass__object_setattr(self, 'drafted', drafted)
            __dataclass__object_setattr(self, 'accepted', accepted)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"tokens={self.tokens!r}")
            parts.append(f"prompt_tokens={self.prompt_tokens!r}")
            parts.append(f"reused={self.reused!r}")
            parts.append(f"rounds={self.rounds!r}")
            parts.append(f"drafted={self.drafted!r}")
            parts.append(f"accepted={self.accepted!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='5021efc821704d9bf8c3cf606cabd96b2f382d12',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('capacity', True, True, None, True, False, False, None), 'instance', 'value',"
            " None, False, False, False), (('prefill_chunk', True, True, None, True, False, False, None), 'instance', '"
            "value', None, False, False, False), (('static', True, True, None, True, False, False, None), 'instance', '"
            "value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()),"
            " ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.decode.inject', 'DecodeConfig'),
    ),
)
def _process_dataclass__5021efc821704d9bf8c3cf606cabd96b2f382d12():
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
                capacity=self.capacity,
                prefill_chunk=self.prefill_chunk,
                static=self.static,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.capacity == other.capacity and
                self.prefill_chunk == other.prefill_chunk and
                self.static == other.static
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'capacity',
            'prefill_chunk',
            'static',
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
                self.capacity,
                self.prefill_chunk,
                self.static,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            capacity: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            prefill_chunk: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            static: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'capacity', capacity)
            __dataclass__object_setattr(self, 'prefill_chunk', prefill_chunk)
            __dataclass__object_setattr(self, 'static', static)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"capacity={self.capacity!r}")
            parts.append(f"prefill_chunk={self.prefill_chunk!r}")
            parts.append(f"static={self.static!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='90bf2cf94e50bb7fdb24aaf0b8f9c2db886d8402',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('mask', True, True, None, True, False, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('bias', True, True, None, True, False, False, None), 'instance', 'value', None,"
            " False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), ("
            "False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.decode.processors', 'Contribution'),
    ),
)
def _process_dataclass__90bf2cf94e50bb7fdb24aaf0b8f9c2db886d8402():
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
                mask=self.mask,
                bias=self.bias,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.mask == other.mask and
                self.bias == other.bias
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'mask',
            'bias',
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
                self.mask,
                self.bias,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            mask: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            bias: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'mask', mask)
            __dataclass__object_setattr(self, 'bias', bias)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"mask={self.mask!r}")
            parts.append(f"bias={self.bias!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='3c5d807a56a9cbfd366069fe29d2afa34e159ef0',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('tokens', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('q', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('q_d', True, True, None, True, False, False, None), 'instance', 'missing', Non"
            "e, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (),"
            " (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.decode.rounds', 'Drafts'),
    ),
)
def _process_dataclass__3c5d807a56a9cbfd366069fe29d2afa34e159ef0():
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
                tokens=self.tokens,
                q=self.q,
                q_d=self.q_d,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.tokens == other.tokens and
                self.q == other.q and
                self.q_d == other.q_d
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'tokens',
            'q',
            'q_d',
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
                self.tokens,
                self.q,
                self.q_d,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            tokens: __dataclass__init__fields__0__annotation,
            q: __dataclass__init__fields__1__annotation,
            q_d: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'tokens', tokens)
            __dataclass__object_setattr(self, 'q', q)
            __dataclass__object_setattr(self, 'q_d', q_d)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"tokens={self.tokens!r}")
            parts.append(f"q={self.q!r}")
            parts.append(f"q_d={self.q_d!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='ed6d679767f56a92f671092d3accfb1525a59a37',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('tokens', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('verified', True, True, None, True, False, False, None), 'instance', 'missi"
            "ng', None, False, False, False), (('drafts', True, True, None, True, False, False, None), 'instance', 'mis"
            "sing', None, False, False, False), (('accepted', True, True, None, True, False, False, None), 'instance', "
            "'missing', None, False, False, False), (('next_tok', True, True, None, True, False, False, None), 'instanc"
            "e', 'missing', None, False, False, False), (('next_arr', True, True, None, True, False, False, None), 'ins"
            "tance', 'missing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, "
            "False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.decode.rounds', 'Round'),
    ),
)
def _process_dataclass__ed6d679767f56a92f671092d3accfb1525a59a37():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                tokens=self.tokens,
                verified=self.verified,
                drafts=self.drafts,
                accepted=self.accepted,
                next_tok=self.next_tok,
                next_arr=self.next_arr,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.tokens == other.tokens and
                self.verified == other.verified and
                self.drafts == other.drafts and
                self.accepted == other.accepted and
                self.next_tok == other.next_tok and
                self.next_arr == other.next_arr
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'tokens',
            'verified',
            'drafts',
            'accepted',
            'next_tok',
            'next_arr',
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
                self.tokens,
                self.verified,
                self.drafts,
                self.accepted,
                self.next_tok,
                self.next_arr,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            tokens: __dataclass__init__fields__0__annotation,
            verified: __dataclass__init__fields__1__annotation,
            drafts: __dataclass__init__fields__2__annotation,
            accepted: __dataclass__init__fields__3__annotation,
            next_tok: __dataclass__init__fields__4__annotation,
            next_arr: __dataclass__init__fields__5__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'tokens', tokens)
            __dataclass__object_setattr(self, 'verified', verified)
            __dataclass__object_setattr(self, 'drafts', drafts)
            __dataclass__object_setattr(self, 'accepted', accepted)
            __dataclass__object_setattr(self, 'next_tok', next_tok)
            __dataclass__object_setattr(self, 'next_arr', next_arr)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"tokens={self.tokens!r}")
            parts.append(f"verified={self.verified!r}")
            parts.append(f"drafts={self.drafts!r}")
            parts.append(f"accepted={self.accepted!r}")
            parts.append(f"next_tok={self.next_tok!r}")
            parts.append(f"next_arr={self.next_arr!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='863852c85ce726bde1c54f4f1fc142df83a0b186',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('logits', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('hidden', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('states', True, True, None, True, False, False, None), 'instance', 'missi"
            "ng', None, False, False, False), (('stacked', True, True, None, True, False, False, None), 'instance', 'mi"
            "ssing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()),"
            " ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.decode.rounds', 'Verified'),
    ),
)
def _process_dataclass__863852c85ce726bde1c54f4f1fc142df83a0b186():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                logits=self.logits,
                hidden=self.hidden,
                states=self.states,
                stacked=self.stacked,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.logits == other.logits and
                self.hidden == other.hidden and
                self.states == other.states and
                self.stacked == other.stacked
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'logits',
            'hidden',
            'states',
            'stacked',
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
                self.logits,
                self.hidden,
                self.states,
                self.stacked,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            logits: __dataclass__init__fields__0__annotation,
            hidden: __dataclass__init__fields__1__annotation,
            states: __dataclass__init__fields__2__annotation,
            stacked: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'logits', logits)
            __dataclass__object_setattr(self, 'hidden', hidden)
            __dataclass__object_setattr(self, 'states', states)
            __dataclass__object_setattr(self, 'stacked', stacked)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"logits={self.logits!r}")
            parts.append(f"hidden={self.hidden!r}")
            parts.append(f"states={self.states!r}")
            parts.append(f"stacked={self.stacked!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='16b89d653f75a765bb7ce2edf75b5a43c44ee1f8',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('prompt', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('max_new_tokens', True, True, None, True, False, False, None), 'instance', "
            "'value', None, False, False, False), (('temperature', True, True, None, True, False, False, None), 'instan"
            "ce', 'value', None, False, False, False), (('top_k', True, True, None, True, False, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('top_p', True, True, None, True, False, False, None), 'instance"
            "', 'value', None, False, False, False), (('min_p', True, True, None, True, False, False, None), 'instance'"
            ", 'value', None, False, False, False), (('seed', True, True, None, True, False, False, None), 'instance', "
            "'value', None, False, False, False), (('presence_penalty', True, True, None, True, False, False, None), 'i"
            "nstance', 'value', None, False, False, False), (('frequency_penalty', True, True, None, True, False, False"
            ", None), 'instance', 'value', None, False, False, False), (('eos_ids', True, True, None, True, False, Fals"
            "e, None), 'instance', 'value', None, False, False, False), (('constraint', True, True, None, True, False, "
            "False, None), 'instance', 'value', None, False, False, False), (('on_token', True, True, None, True, False"
            ", False, None), 'instance', 'value', None, False, False, False), (('should_stop', True, True, None, True, "
            "False, False, None), 'instance', 'value', None, False, False, False), (('terminators', True, True, None, T"
            "rue, False, False, None), 'instance', 'value', None, False, False, False), (('observers', True, True, None"
            ", True, False, False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), ("
            "False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.decode.runners', 'GenerationParams'),
    ),
)
def _process_dataclass__16b89d653f75a765bb7ce2edf75b5a43c44ee1f8():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                prompt=self.prompt,
                max_new_tokens=self.max_new_tokens,
                temperature=self.temperature,
                top_k=self.top_k,
                top_p=self.top_p,
                min_p=self.min_p,
                seed=self.seed,
                presence_penalty=self.presence_penalty,
                frequency_penalty=self.frequency_penalty,
                eos_ids=self.eos_ids,
                constraint=self.constraint,
                on_token=self.on_token,
                should_stop=self.should_stop,
                terminators=self.terminators,
                observers=self.observers,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.prompt == other.prompt and
                self.max_new_tokens == other.max_new_tokens and
                self.temperature == other.temperature and
                self.top_k == other.top_k and
                self.top_p == other.top_p and
                self.min_p == other.min_p and
                self.seed == other.seed and
                self.presence_penalty == other.presence_penalty and
                self.frequency_penalty == other.frequency_penalty and
                self.eos_ids == other.eos_ids and
                self.constraint == other.constraint and
                self.on_token == other.on_token and
                self.should_stop == other.should_stop and
                self.terminators == other.terminators and
                self.observers == other.observers
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'prompt',
            'max_new_tokens',
            'temperature',
            'top_k',
            'top_p',
            'min_p',
            'seed',
            'presence_penalty',
            'frequency_penalty',
            'eos_ids',
            'constraint',
            'on_token',
            'should_stop',
            'terminators',
            'observers',
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
                self.prompt,
                self.max_new_tokens,
                self.temperature,
                self.top_k,
                self.top_p,
                self.min_p,
                self.seed,
                self.presence_penalty,
                self.frequency_penalty,
                self.eos_ids,
                self.constraint,
                self.on_token,
                self.should_stop,
                self.terminators,
                self.observers,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            prompt: __dataclass__init__fields__00__annotation,
            max_new_tokens: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            temperature: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            top_k: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            top_p: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            min_p: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            seed: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            presence_penalty: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            frequency_penalty: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            eos_ids: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            constraint: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            on_token: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            should_stop: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            terminators: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            observers: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'prompt', prompt)
            __dataclass__object_setattr(self, 'max_new_tokens', max_new_tokens)
            __dataclass__object_setattr(self, 'temperature', temperature)
            __dataclass__object_setattr(self, 'top_k', top_k)
            __dataclass__object_setattr(self, 'top_p', top_p)
            __dataclass__object_setattr(self, 'min_p', min_p)
            __dataclass__object_setattr(self, 'seed', seed)
            __dataclass__object_setattr(self, 'presence_penalty', presence_penalty)
            __dataclass__object_setattr(self, 'frequency_penalty', frequency_penalty)
            __dataclass__object_setattr(self, 'eos_ids', eos_ids)
            __dataclass__object_setattr(self, 'constraint', constraint)
            __dataclass__object_setattr(self, 'on_token', on_token)
            __dataclass__object_setattr(self, 'should_stop', should_stop)
            __dataclass__object_setattr(self, 'terminators', terminators)
            __dataclass__object_setattr(self, 'observers', observers)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"prompt={self.prompt!r}")
            parts.append(f"max_new_tokens={self.max_new_tokens!r}")
            parts.append(f"temperature={self.temperature!r}")
            parts.append(f"top_k={self.top_k!r}")
            parts.append(f"top_p={self.top_p!r}")
            parts.append(f"min_p={self.min_p!r}")
            parts.append(f"seed={self.seed!r}")
            parts.append(f"presence_penalty={self.presence_penalty!r}")
            parts.append(f"frequency_penalty={self.frequency_penalty!r}")
            parts.append(f"eos_ids={self.eos_ids!r}")
            parts.append(f"constraint={self.constraint!r}")
            parts.append(f"on_token={self.on_token!r}")
            parts.append(f"should_stop={self.should_stop!r}")
            parts.append(f"terminators={self.terminators!r}")
            parts.append(f"observers={self.observers!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='cee94571a5a1febb1198c89f29b8b4b4e2eae976',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('tokens', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('cache', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('logits', True, True, None, True, False, False, None), 'instance', 'missi"
            "ng', None, False, False, False), (('hidden', True, True, None, True, False, False, None), 'instance', 'mis"
            "sing', None, False, False, False), (('draft', True, True, None, True, False, False, None), 'instance', 'mi"
            "ssing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()),"
            " ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.decode.state', 'Snapshot'),
    ),
)
def _process_dataclass__cee94571a5a1febb1198c89f29b8b4b4e2eae976():
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
                draft=self.draft,
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
                self.draft == other.draft
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            tokens: __dataclass__init__fields__0__annotation,
            cache: __dataclass__init__fields__1__annotation,
            logits: __dataclass__init__fields__2__annotation,
            hidden: __dataclass__init__fields__3__annotation,
            draft: __dataclass__init__fields__4__annotation,
        ) -> __dataclass__None:
            self.tokens = tokens
            self.cache = cache
            self.logits = logits
            self.hidden = hidden
            self.draft = draft

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"tokens={self.tokens!r}")
            parts.append(f"cache={self.cache!r}")
            parts.append(f"logits={self.logits!r}")
            parts.append(f"hidden={self.hidden!r}")
            parts.append(f"draft={self.draft!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='37218a16b737ea700cf794dc09ee712fdc83e8aa',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('ops', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('tok', True, True, None, True, False, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('runner', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('prefix_cache', True, True, None, True, False, False, None), 'instance', 'val"
            "ue', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (("
            "),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.entrypoints.common', 'GenerationSetup'),
    ),
)
def _process_dataclass__37218a16b737ea700cf794dc09ee712fdc83e8aa():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                ops=self.ops,
                tok=self.tok,
                runner=self.runner,
                prefix_cache=self.prefix_cache,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.ops == other.ops and
                self.tok == other.tok and
                self.runner == other.runner and
                self.prefix_cache == other.prefix_cache
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'ops',
            'tok',
            'runner',
            'prefix_cache',
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
                self.ops,
                self.tok,
                self.runner,
                self.prefix_cache,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            ops: __dataclass__init__fields__0__annotation,
            tok: __dataclass__init__fields__1__annotation,
            runner: __dataclass__init__fields__2__annotation,
            prefix_cache: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'ops', ops)
            __dataclass__object_setattr(self, 'tok', tok)
            __dataclass__object_setattr(self, 'runner', runner)
            __dataclass__object_setattr(self, 'prefix_cache', prefix_cache)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"ops={self.ops!r}")
            parts.append(f"tok={self.tok!r}")
            parts.append(f"runner={self.runner!r}")
            parts.append(f"prefix_cache={self.prefix_cache!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d3bbe850a5e22133bde3f26822f24e8cfcb6c3ba',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('model', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('dtype', True, True, None, True, False, False, None), 'instance', 'value', N"
            "one, False, False, False), (('quant', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('group', True, True, None, True, False, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('policy', True, True, None, True, False, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('quant_search', True, True, None, True, False, False, None), 'instance', 'value"
            "', None, False, False, False), (('cache_dir', True, True, None, True, False, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('mtp', True, True, None, True, False, False, None), 'instance', 'value"
            "', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.load.inject', 'LoadConfig'),
    ),
)
def _process_dataclass__d3bbe850a5e22133bde3f26822f24e8cfcb6c3ba():
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
                dtype=self.dtype,
                quant=self.quant,
                group=self.group,
                policy=self.policy,
                quant_search=self.quant_search,
                cache_dir=self.cache_dir,
                mtp=self.mtp,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.model == other.model and
                self.dtype == other.dtype and
                self.quant == other.quant and
                self.group == other.group and
                self.policy == other.policy and
                self.quant_search == other.quant_search and
                self.cache_dir == other.cache_dir and
                self.mtp == other.mtp
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'model',
            'dtype',
            'quant',
            'group',
            'policy',
            'quant_search',
            'cache_dir',
            'mtp',
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
                self.dtype,
                self.quant,
                self.group,
                self.policy,
                self.quant_search,
                self.cache_dir,
                self.mtp,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            model: __dataclass__init__fields__0__annotation,
            dtype: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            quant: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            group: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            policy: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            quant_search: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            cache_dir: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
            mtp: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'model', model)
            __dataclass__object_setattr(self, 'dtype', dtype)
            __dataclass__object_setattr(self, 'quant', quant)
            __dataclass__object_setattr(self, 'group', group)
            __dataclass__object_setattr(self, 'policy', policy)
            __dataclass__object_setattr(self, 'quant_search', quant_search)
            __dataclass__object_setattr(self, 'cache_dir', cache_dir)
            __dataclass__object_setattr(self, 'mtp', mtp)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"model={self.model!r}")
            parts.append(f"dtype={self.dtype!r}")
            parts.append(f"quant={self.quant!r}")
            parts.append(f"group={self.group!r}")
            parts.append(f"policy={self.policy!r}")
            parts.append(f"quant_search={self.quant_search!r}")
            parts.append(f"cache_dir={self.cache_dir!r}")
            parts.append(f"mtp={self.mtp!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='6f702ddd3cf10a47a0baf244e5b31d8a9f5daec9',
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
        ('omllm.local.qwen.load.paramcache', 'ParamCache'),
    ),
)
def _process_dataclass__6f702ddd3cf10a47a0baf244e5b31d8a9f5daec9():
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
    installer_sha1='fa702d7bd4a1b88a687628521864d8fa40ad274c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('params', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('acquired', True, True, None, True, False, False, None), 'instance', 'missi"
            "ng', None, False, False, False), (('quantized', True, True, None, True, False, False, None), 'instance', '"
            "missing', None, False, False, False), (('nbytes', True, True, None, True, False, False, None), 'instance',"
            " 'missing', None, False, False, False), (('backend', True, True, None, True, False, False, None), 'instanc"
            "e', 'missing', None, False, False, False), (('recipe', True, True, None, True, False, False, None), 'insta"
            "nce', 'missing', None, False, False, False), (('cache_root', True, True, None, True, False, False, None), "
            "'instance', 'value', None, False, False, False), (('cache_hits', True, True, None, True, False, False, Non"
            "e), 'instance', 'value', None, False, False, False), (('cache_misses', True, True, None, True, False, Fals"
            "e, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False"
            ",), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.load.pipeline', 'LoadReport'),
    ),
)
def _process_dataclass__fa702d7bd4a1b88a687628521864d8fa40ad274c():
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
                params=self.params,
                acquired=self.acquired,
                quantized=self.quantized,
                nbytes=self.nbytes,
                backend=self.backend,
                recipe=self.recipe,
                cache_root=self.cache_root,
                cache_hits=self.cache_hits,
                cache_misses=self.cache_misses,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.params == other.params and
                self.acquired == other.acquired and
                self.quantized == other.quantized and
                self.nbytes == other.nbytes and
                self.backend == other.backend and
                self.recipe == other.recipe and
                self.cache_root == other.cache_root and
                self.cache_hits == other.cache_hits and
                self.cache_misses == other.cache_misses
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'params',
            'acquired',
            'quantized',
            'nbytes',
            'backend',
            'recipe',
            'cache_root',
            'cache_hits',
            'cache_misses',
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
                self.params,
                self.acquired,
                self.quantized,
                self.nbytes,
                self.backend,
                self.recipe,
                self.cache_root,
                self.cache_hits,
                self.cache_misses,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            params: __dataclass__init__fields__0__annotation,
            acquired: __dataclass__init__fields__1__annotation,
            quantized: __dataclass__init__fields__2__annotation,
            nbytes: __dataclass__init__fields__3__annotation,
            backend: __dataclass__init__fields__4__annotation,
            recipe: __dataclass__init__fields__5__annotation,
            cache_root: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
            cache_hits: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
            cache_misses: __dataclass__init__fields__8__annotation = __dataclass__init__fields__8__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'params', params)
            __dataclass__object_setattr(self, 'acquired', acquired)
            __dataclass__object_setattr(self, 'quantized', quantized)
            __dataclass__object_setattr(self, 'nbytes', nbytes)
            __dataclass__object_setattr(self, 'backend', backend)
            __dataclass__object_setattr(self, 'recipe', recipe)
            __dataclass__object_setattr(self, 'cache_root', cache_root)
            __dataclass__object_setattr(self, 'cache_hits', cache_hits)
            __dataclass__object_setattr(self, 'cache_misses', cache_misses)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"params={self.params!r}")
            parts.append(f"acquired={self.acquired!r}")
            parts.append(f"quantized={self.quantized!r}")
            parts.append(f"nbytes={self.nbytes!r}")
            parts.append(f"backend={self.backend!r}")
            parts.append(f"recipe={self.recipe!r}")
            parts.append(f"cache_root={self.cache_root!r}")
            parts.append(f"cache_hits={self.cache_hits!r}")
            parts.append(f"cache_misses={self.cache_misses!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='a4f429b3f9470261fd754a6077f10dde35b9247d',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('fusions', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('keep_f32', True, True, None, True, False, False, None), 'instance', 'value'"
            ", None, False, False, False), (('no_quant', True, True, None, True, False, False, None), 'instance', 'valu"
            "e', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (()"
            ",), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.load.plan', 'LayoutRules'),
    ),
)
def _process_dataclass__a4f429b3f9470261fd754a6077f10dde35b9247d():
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
                fusions=self.fusions,
                keep_f32=self.keep_f32,
                no_quant=self.no_quant,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.fusions == other.fusions and
                self.keep_f32 == other.keep_f32 and
                self.no_quant == other.no_quant
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'fusions',
            'keep_f32',
            'no_quant',
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
                self.fusions,
                self.keep_f32,
                self.no_quant,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            fusions: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            keep_f32: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            no_quant: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'fusions', fusions)
            __dataclass__object_setattr(self, 'keep_f32', keep_f32)
            __dataclass__object_setattr(self, 'no_quant', no_quant)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"fusions={self.fusions!r}")
            parts.append(f"keep_f32={self.keep_f32!r}")
            parts.append(f"no_quant={self.no_quant!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='26bd67d590d6f1f8116bd7993709418504855825',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('name', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('parts', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False), (('bits', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('keep_f32', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.load.plan', 'ParamSpec'),
    ),
)
def _process_dataclass__26bd67d590d6f1f8116bd7993709418504855825():
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
                name=self.name,
                parts=self.parts,
                bits=self.bits,
                keep_f32=self.keep_f32,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.parts == other.parts and
                self.bits == other.bits and
                self.keep_f32 == other.keep_f32
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'parts',
            'bits',
            'keep_f32',
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
                self.parts,
                self.bits,
                self.keep_f32,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
            parts: __dataclass__init__fields__1__annotation,
            bits: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            keep_f32: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'parts', parts)
            __dataclass__object_setattr(self, 'bits', bits)
            __dataclass__object_setattr(self, 'keep_f32', keep_f32)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"parts={self.parts!r}")
            parts.append(f"bits={self.bits!r}")
            parts.append(f"keep_f32={self.keep_f32!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='1fe6ccb05e22bf0dd9d203c6eaa832dcea7ad47a',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('quant', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('group', True, True, None, True, False, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('search', True, True, None, True, False, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('policy', True, True, None, True, False, False, None), 'instance', 'value', Non"
            "e, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, True, ()), ((),), (), "
            "(False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.load.recipe', 'LoadRecipe'),
    ),
)
def _process_dataclass__1fe6ccb05e22bf0dd9d203c6eaa832dcea7ad47a():
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
                quant=self.quant,
                group=self.group,
                search=self.search,
                policy=self.policy,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.quant == other.quant and
                self.group == other.group and
                self.search == other.search and
                self.policy == other.policy
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'quant',
            'group',
            'search',
            'policy',
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
                self.quant,
                self.group,
                self.search,
                self.policy,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            quant: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            group: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            search: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            policy: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'quant', quant)
            __dataclass__object_setattr(self, 'group', group)
            __dataclass__object_setattr(self, 'search', search)
            __dataclass__object_setattr(self, 'policy', policy)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"quant={self.quant!r}")
            parts.append(f"group={self.group!r}")
            parts.append(f"search={self.search!r}")
            parts.append(f"policy={self.policy!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='61eee654341468e0b903b290a26d55ca7efcd519',
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
        ('omllm.local.qwen.load.weights', 'NativeQuant'),
    ),
)
def _process_dataclass__61eee654341468e0b903b290a26d55ca7efcd519():
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
    installer_sha1='0a4248d882884871a6c95e286c28594147baa7bd',
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
        ('omllm.local.qwen.load.weights', 'OllamaModel'),
    ),
)
def _process_dataclass__0a4248d882884871a6c95e286c28594147baa7bd():
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
    installer_sha1='dc346acb8d24d224cbb868fd5a4e5b2fe08fcc40',
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
        ('omllm.local.qwen.prefix.cache', '_Entry'),
    ),
)
def _process_dataclass__dc346acb8d24d224cbb868fd5a4e5b2fe08fcc40():
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
    installer_sha1='e2d580eb8390b3733970c3370f42ef267dc7ed6e',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('enabled', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('device_mib', True, True, None, True, False, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('host_mib', True, True, None, True, False, False, None), 'instance', 'va"
            "lue', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ("
            "(),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.prefix.inject', 'PrefixConfig'),
    ),
)
def _process_dataclass__e2d580eb8390b3733970c3370f42ef267dc7ed6e():
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
                enabled=self.enabled,
                device_mib=self.device_mib,
                host_mib=self.host_mib,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.enabled == other.enabled and
                self.device_mib == other.device_mib and
                self.host_mib == other.host_mib
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'enabled',
            'device_mib',
            'host_mib',
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
                self.enabled,
                self.device_mib,
                self.host_mib,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            enabled: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            device_mib: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            host_mib: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'enabled', enabled)
            __dataclass__object_setattr(self, 'device_mib', device_mib)
            __dataclass__object_setattr(self, 'host_mib', host_mib)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"enabled={self.enabled!r}")
            parts.append(f"device_mib={self.device_mib!r}")
            parts.append(f"host_mib={self.host_mib!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='90743ff9b91b5e5027b585bbd2fe83f18e29e304',
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
        ('omllm.local.qwen.serve.chat', 'Parsed'),
    ),
)
def _process_dataclass__90743ff9b91b5e5027b585bbd2fe83f18e29e304():
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
    installer_sha1='20d35531653ed66162b9038d9330f51875cf15c0',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('defaults', True, True, None, True, False, False, None), 'instance', 'factory"
            "', None, False, False, False), (('enable_thinking', True, True, None, True, False, False, None), 'instance"
            "', 'value', None, False, False, False), (('preserve_thinking', True, True, None, True, False, False, None)"
            ", 'instance', 'value', None, False, False, False), (('max_queue', True, True, None, True, False, False, No"
            "ne), 'instance', 'value', None, False, False, False), (('model_name', True, True, None, True, False, False"
            ", None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,"
            "), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.serve.inject', 'ServeConfig'),
    ),
)
def _process_dataclass__20d35531653ed66162b9038d9330f51875cf15c0():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default_factory = __dataclass__spec.fields[0].default.must().fn
        __dataclass__init__fields__1__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__1__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__2__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__2__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__3__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__3__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__4__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__4__default = __dataclass__spec.fields[4].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                defaults=self.defaults,
                enable_thinking=self.enable_thinking,
                preserve_thinking=self.preserve_thinking,
                max_queue=self.max_queue,
                model_name=self.model_name,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.defaults == other.defaults and
                self.enable_thinking == other.enable_thinking and
                self.preserve_thinking == other.preserve_thinking and
                self.max_queue == other.max_queue and
                self.model_name == other.model_name
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'defaults',
            'enable_thinking',
            'preserve_thinking',
            'max_queue',
            'model_name',
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
                self.defaults,
                self.enable_thinking,
                self.preserve_thinking,
                self.max_queue,
                self.model_name,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            defaults: __dataclass__init__fields__0__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            enable_thinking: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            preserve_thinking: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            max_queue: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            model_name: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            if defaults is __dataclass__HAS_DEFAULT_FACTORY:
                defaults = __dataclass__init__fields__0__default_factory()
            __dataclass__object_setattr(self, 'defaults', defaults)
            __dataclass__object_setattr(self, 'enable_thinking', enable_thinking)
            __dataclass__object_setattr(self, 'preserve_thinking', preserve_thinking)
            __dataclass__object_setattr(self, 'max_queue', max_queue)
            __dataclass__object_setattr(self, 'model_name', model_name)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"defaults={self.defaults!r}")
            parts.append(f"enable_thinking={self.enable_thinking!r}")
            parts.append(f"preserve_thinking={self.preserve_thinking!r}")
            parts.append(f"max_queue={self.max_queue!r}")
            parts.append(f"model_name={self.model_name!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='cb85da736d989b86f8411668332ebf582b46ed9a',
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
            "ue, None, True, False, False, None), 'instance', 'value', None, False, False, False), (('tool_choice', Tru"
            "e, True, None, True, False, False, None), 'instance', 'value', None, False, False, False), (('response_for"
            "mat', True, True, None, True, False, False, None), 'instance', 'value', None, False, False, False)), False"
            ", 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.serve.serving', 'Request'),
    ),
)
def _process_dataclass__cb85da736d989b86f8411668332ebf582b46ed9a():
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
        __dataclass__init__fields__14__annotation = __dataclass__spec.fields[14].annotation
        __dataclass__init__fields__14__default = __dataclass__spec.fields[14].default.must()
        __dataclass__init__fields__15__annotation = __dataclass__spec.fields[15].annotation
        __dataclass__init__fields__15__default = __dataclass__spec.fields[15].default.must()
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
                tool_choice=self.tool_choice,
                response_format=self.response_format,
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
                self.model == other.model and
                self.tool_choice == other.tool_choice and
                self.response_format == other.response_format
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
            tool_choice: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            response_format: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
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
            self.tool_choice = tool_choice
            self.response_format = response_format

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
            parts.append(f"tool_choice={self.tool_choice!r}")
            parts.append(f"response_format={self.response_format!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='0a1e02fe714bf50e1167fbc2a482aef5fc27befc',
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
        ('omllm.local.qwen.serve.serving', 'Result'),
    ),
)
def _process_dataclass__0a1e02fe714bf50e1167fbc2a482aef5fc27befc():
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
    installer_sha1='9b4c404260e467053baf01f5efeef718d7ccdff5',
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
        ('omllm.local.qwen.serve.serving', 'SamplingDefaults'),
    ),
)
def _process_dataclass__9b4c404260e467053baf01f5efeef718d7ccdff5():
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
    installer_sha1='1c9e3f5dce2619aec2802a9d4f06b1c9ea3683a6',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('ngram', True, True, None, True, False, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('k', True, True, None, True, False, False, None), 'instance', 'value', None, F"
            "alse, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (Fa"
            "lse,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.spec.inject', 'LookupConfig'),
    ),
)
def _process_dataclass__1c9e3f5dce2619aec2802a9d4f06b1c9ea3683a6():
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
                ngram=self.ngram,
                k=self.k,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.ngram == other.ngram and
                self.k == other.k
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'ngram',
            'k',
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
                self.ngram,
                self.k,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            ngram: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            k: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'ngram', ngram)
            __dataclass__object_setattr(self, 'k', k)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"ngram={self.ngram!r}")
            parts.append(f"k={self.k!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c9998747efcad3054c711a8e2382df928649cdfb',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('k', True, True, None, True, False, False, None), 'instance', 'value', None, "
            "False, False, False), (('draft_vocab', True, True, None, True, False, False, None), 'instance', 'value', N"
            "one, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ("
            "), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.local.qwen.spec.inject', 'SpecConfig'),
    ),
)
def _process_dataclass__c9998747efcad3054c711a8e2382df928649cdfb():
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
                k=self.k,
                draft_vocab=self.draft_vocab,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.k == other.k and
                self.draft_vocab == other.draft_vocab
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'k',
            'draft_vocab',
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
                self.k,
                self.draft_vocab,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            k: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            draft_vocab: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'k', k)
            __dataclass__object_setattr(self, 'draft_vocab', draft_vocab)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"k={self.k!r}")
            parts.append(f"draft_vocab={self.draft_vocab!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
