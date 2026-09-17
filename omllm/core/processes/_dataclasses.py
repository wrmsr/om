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
    installer_sha1='0371f82a7e4a09f38c44484adfa34341a8273eec',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('spec', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('argv', True, True, None, True, True, False, None), 'instance', 'missing', None"
            ", False, False, False), (('env', True, True, None, True, True, False, None), 'instance', 'missing', None, "
            "False, False, False), (('control_fd', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('send_fds', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('owned_fds', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.launch.launcher', 'LaunchPlan'),
    ),
)
def _process_dataclass__0371f82a7e4a09f38c44484adfa34341a8273eec():
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
                spec=self.spec,
                argv=self.argv,
                env=self.env,
                control_fd=self.control_fd,
                send_fds=self.send_fds,
                owned_fds=self.owned_fds,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.spec == other.spec and
                self.argv == other.argv and
                self.env == other.env and
                self.control_fd == other.control_fd and
                self.send_fds == other.send_fds and
                self.owned_fds == other.owned_fds
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'spec',
            'argv',
            'env',
            'control_fd',
            'send_fds',
            'owned_fds',
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
                self.spec,
                self.argv,
                self.env,
                self.control_fd,
                self.send_fds,
                self.owned_fds,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            spec: __dataclass__init__fields__0__annotation,
            argv: __dataclass__init__fields__1__annotation,
            env: __dataclass__init__fields__2__annotation,
            control_fd: __dataclass__init__fields__3__annotation,
            send_fds: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            owned_fds: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'spec', spec)
            __dataclass__object_setattr(self, 'argv', argv)
            __dataclass__object_setattr(self, 'env', env)
            __dataclass__object_setattr(self, 'control_fd', control_fd)
            __dataclass__object_setattr(self, 'send_fds', send_fds)
            __dataclass__object_setattr(self, 'owned_fds', owned_fds)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"spec={self.spec!r}")
            parts.append(f"argv={self.argv!r}")
            parts.append(f"env={self.env!r}")
            parts.append(f"control_fd={self.control_fd!r}")
            parts.append(f"send_fds={self.send_fds!r}")
            parts.append(f"owned_fds={self.owned_fds!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='df9ce849a02c2c1ff67e515352eb5f46a2eda8ca',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('remove', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('keep', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (F"
            "alse,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.launch.transforms', 'EnvScrubTransform'),
    ),
)
def _process_dataclass__df9ce849a02c2c1ff67e515352eb5f46a2eda8ca():
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
                remove=self.remove,
                keep=self.keep,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.remove == other.remove and
                self.keep == other.keep
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'remove',
            'keep',
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
                self.remove,
                self.keep,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            remove: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            keep: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'remove', remove)
            __dataclass__object_setattr(self, 'keep', keep)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"remove={self.remove!r}")
            parts.append(f"keep={self.keep!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='ef83b825100e9837aac95092c17d0de799082448',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('stdin_fd', True, True, None, True, True, False, None), 'instance', 'missing',"
            " None, False, False, False), (('stdout_fd', True, True, None, True, True, False, None), 'instance', 'missi"
            "ng', None, False, False, False), (('stderr_fd', True, True, None, True, True, False, None), 'instance', 'm"
            "issing', None, False, False, False), (('child_fds', True, True, None, True, True, False, None), 'instance'"
            ", 'missing', None, False, False, False), (('parent_fds', True, True, None, True, True, False, None), 'inst"
            "ance', 'missing', None, False, False, False), (('stdin_w', True, True, None, True, True, False, None), 'in"
            "stance', 'missing', None, False, False, False), (('output_reads', True, True, None, True, True, False, Non"
            "e), 'instance', 'missing', None, False, False, False), (('pty_master_fd', True, True, None, True, True, Fa"
            "lse, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (Fal"
            "se,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.managers.stdio', 'StdioSetup'),
    ),
)
def _process_dataclass__ef83b825100e9837aac95092c17d0de799082448():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                stdin_fd=self.stdin_fd,
                stdout_fd=self.stdout_fd,
                stderr_fd=self.stderr_fd,
                child_fds=self.child_fds,
                parent_fds=self.parent_fds,
                stdin_w=self.stdin_w,
                output_reads=self.output_reads,
                pty_master_fd=self.pty_master_fd,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.stdin_fd == other.stdin_fd and
                self.stdout_fd == other.stdout_fd and
                self.stderr_fd == other.stderr_fd and
                self.child_fds == other.child_fds and
                self.parent_fds == other.parent_fds and
                self.stdin_w == other.stdin_w and
                self.output_reads == other.output_reads and
                self.pty_master_fd == other.pty_master_fd
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'stdin_fd',
            'stdout_fd',
            'stderr_fd',
            'child_fds',
            'parent_fds',
            'stdin_w',
            'output_reads',
            'pty_master_fd',
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
                self.stdin_fd,
                self.stdout_fd,
                self.stderr_fd,
                self.child_fds,
                self.parent_fds,
                self.stdin_w,
                self.output_reads,
                self.pty_master_fd,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            stdin_fd: __dataclass__init__fields__0__annotation,
            stdout_fd: __dataclass__init__fields__1__annotation,
            stderr_fd: __dataclass__init__fields__2__annotation,
            child_fds: __dataclass__init__fields__3__annotation,
            parent_fds: __dataclass__init__fields__4__annotation,
            stdin_w: __dataclass__init__fields__5__annotation,
            output_reads: __dataclass__init__fields__6__annotation,
            pty_master_fd: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'stdin_fd', stdin_fd)
            __dataclass__object_setattr(self, 'stdout_fd', stdout_fd)
            __dataclass__object_setattr(self, 'stderr_fd', stderr_fd)
            __dataclass__object_setattr(self, 'child_fds', child_fds)
            __dataclass__object_setattr(self, 'parent_fds', parent_fds)
            __dataclass__object_setattr(self, 'stdin_w', stdin_w)
            __dataclass__object_setattr(self, 'output_reads', output_reads)
            __dataclass__object_setattr(self, 'pty_master_fd', pty_master_fd)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"stdin_fd={self.stdin_fd!r}")
            parts.append(f"stdout_fd={self.stdout_fd!r}")
            parts.append(f"stderr_fd={self.stderr_fd!r}")
            parts.append(f"child_fds={self.child_fds!r}")
            parts.append(f"parent_fds={self.parent_fds!r}")
            parts.append(f"stdin_w={self.stdin_w!r}")
            parts.append(f"output_reads={self.output_reads!r}")
            parts.append(f"pty_master_fd={self.pty_master_fd!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d12672cc1d8a3b9682433c1dee057488ab91c91d',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('shim_python', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('spill_dir', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('default_options', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('close_policy', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('spawn_timeout_s', True, True, None, True, True, False, Non"
            "e), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (F"
            "alse, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.managers.types', 'ManagerConfig'),
    ),
)
def _process_dataclass__d12672cc1d8a3b9682433c1dee057488ab91c91d():
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
                shim_python=self.shim_python,
                spill_dir=self.spill_dir,
                default_options=self.default_options,
                close_policy=self.close_policy,
                spawn_timeout_s=self.spawn_timeout_s,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.shim_python == other.shim_python and
                self.spill_dir == other.spill_dir and
                self.default_options == other.default_options and
                self.close_policy == other.close_policy and
                self.spawn_timeout_s == other.spawn_timeout_s
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'shim_python',
            'spill_dir',
            'default_options',
            'close_policy',
            'spawn_timeout_s',
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
                self.shim_python,
                self.spill_dir,
                self.default_options,
                self.close_policy,
                self.spawn_timeout_s,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            shim_python: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            spill_dir: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            default_options: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            close_policy: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            spawn_timeout_s: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'shim_python', shim_python)
            __dataclass__object_setattr(self, 'spill_dir', spill_dir)
            __dataclass__object_setattr(self, 'default_options', default_options)
            __dataclass__object_setattr(self, 'close_policy', close_policy)
            __dataclass__object_setattr(self, 'spawn_timeout_s', spawn_timeout_s)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"shim_python={self.shim_python!r}")
            parts.append(f"spill_dir={self.spill_dir!r}")
            parts.append(f"default_options={self.default_options!r}")
            parts.append(f"close_policy={self.close_policy!r}")
            parts.append(f"spawn_timeout_s={self.spawn_timeout_s!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c86110517c5f77a5d0964c07a63d08142c9e9556',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('policy', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('bwrap', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('new_session', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.sandbox.bwrap', 'BwrapSandbox'),
    ),
)
def _process_dataclass__c86110517c5f77a5d0964c07a63d08142c9e9556():
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
                policy=self.policy,
                bwrap=self.bwrap,
                new_session=self.new_session,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.policy == other.policy and
                self.bwrap == other.bwrap and
                self.new_session == other.new_session
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'policy',
            'bwrap',
            'new_session',
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
                self.policy,
                self.bwrap,
                self.new_session,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            policy: __dataclass__init__fields__0__annotation,
            bwrap: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            new_session: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'policy', policy)
            __dataclass__object_setattr(self, 'bwrap', bwrap)
            __dataclass__object_setattr(self, 'new_session', new_session)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.policy)) is not None:
                parts.append(f"policy={s}")
            if (s := __dataclass__repr__default_fn(self.bwrap)) is not None:
                parts.append(f"bwrap={s}")
            if (s := __dataclass__repr__default_fn(self.new_session)) is not None:
                parts.append(f"new_session={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='3b3d3348cfcd355ed4312dcab4a13f00ff1bdeb6',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('read_roots', True, True, None, True, True, False, None), 'instance', 'value',"
            " 'callable', False, False, False), (('write_roots', True, True, None, True, True, False, None), 'instance'"
            ", 'value', 'callable', False, False, False), (('system_read_roots', True, True, None, True, True, False, N"
            "one), 'instance', 'value', 'callable', False, False, False), (('exec_paths', True, True, None, True, True,"
            " False, None), 'instance', 'value', 'callable', False, False, False), (('allow_fork', True, True, None, Tr"
            "ue, True, False, None), 'instance', 'value', None, False, False, False), (('mach_lookup', True, True, None"
            ", True, True, False, None), 'instance', 'value', 'callable', False, False, False), (('sysctl_names', True,"
            " True, None, True, True, False, None), 'instance', 'value', 'callable', False, False, False), (('allow_net"
            "work', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('dev"
            "', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('allow_p"
            "roc', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('priv"
            "ate_tmp', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False)), Tr"
            "ue, 0, ()), ((False,), (False,), (), (False,), (False, True, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.sandbox.policy', 'SandboxPolicy'),
    ),
)
def _process_dataclass__3b3d3348cfcd355ed4312dcab4a13f00ff1bdeb6():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__00__coerce = __dataclass__spec.fields[0].coerce
        __dataclass__init__fields__00__default = __dataclass__spec.fields[0].default.must()
        __dataclass__init__fields__01__annotation = __dataclass__spec.fields[1].annotation
        __dataclass__init__fields__01__coerce = __dataclass__spec.fields[1].coerce
        __dataclass__init__fields__01__default = __dataclass__spec.fields[1].default.must()
        __dataclass__init__fields__02__annotation = __dataclass__spec.fields[2].annotation
        __dataclass__init__fields__02__coerce = __dataclass__spec.fields[2].coerce
        __dataclass__init__fields__02__default = __dataclass__spec.fields[2].default.must()
        __dataclass__init__fields__03__annotation = __dataclass__spec.fields[3].annotation
        __dataclass__init__fields__03__coerce = __dataclass__spec.fields[3].coerce
        __dataclass__init__fields__03__default = __dataclass__spec.fields[3].default.must()
        __dataclass__init__fields__04__annotation = __dataclass__spec.fields[4].annotation
        __dataclass__init__fields__04__default = __dataclass__spec.fields[4].default.must()
        __dataclass__init__fields__05__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__05__coerce = __dataclass__spec.fields[5].coerce
        __dataclass__init__fields__05__default = __dataclass__spec.fields[5].default.must()
        __dataclass__init__fields__06__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__06__coerce = __dataclass__spec.fields[6].coerce
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
                read_roots=self.read_roots,
                write_roots=self.write_roots,
                system_read_roots=self.system_read_roots,
                exec_paths=self.exec_paths,
                allow_fork=self.allow_fork,
                mach_lookup=self.mach_lookup,
                sysctl_names=self.sysctl_names,
                allow_network=self.allow_network,
                dev=self.dev,
                allow_proc=self.allow_proc,
                private_tmp=self.private_tmp,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.read_roots == other.read_roots and
                self.write_roots == other.write_roots and
                self.system_read_roots == other.system_read_roots and
                self.exec_paths == other.exec_paths and
                self.allow_fork == other.allow_fork and
                self.mach_lookup == other.mach_lookup and
                self.sysctl_names == other.sysctl_names and
                self.allow_network == other.allow_network and
                self.dev == other.dev and
                self.allow_proc == other.allow_proc and
                self.private_tmp == other.private_tmp
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'read_roots',
            'write_roots',
            'system_read_roots',
            'exec_paths',
            'allow_fork',
            'mach_lookup',
            'sysctl_names',
            'allow_network',
            'dev',
            'allow_proc',
            'private_tmp',
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
                self.read_roots,
                self.write_roots,
                self.system_read_roots,
                self.exec_paths,
                self.allow_fork,
                self.mach_lookup,
                self.sysctl_names,
                self.allow_network,
                self.dev,
                self.allow_proc,
                self.private_tmp,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            read_roots: __dataclass__init__fields__00__annotation = __dataclass__init__fields__00__default,
            write_roots: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            system_read_roots: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            exec_paths: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            allow_fork: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            mach_lookup: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            sysctl_names: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            allow_network: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            dev: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            allow_proc: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            private_tmp: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
        ) -> __dataclass__None:
            read_roots = __dataclass__init__fields__00__coerce(read_roots)
            write_roots = __dataclass__init__fields__01__coerce(write_roots)
            system_read_roots = __dataclass__init__fields__02__coerce(system_read_roots)
            exec_paths = __dataclass__init__fields__03__coerce(exec_paths)
            mach_lookup = __dataclass__init__fields__05__coerce(mach_lookup)
            sysctl_names = __dataclass__init__fields__06__coerce(sysctl_names)
            __dataclass__object_setattr(self, 'read_roots', read_roots)
            __dataclass__object_setattr(self, 'write_roots', write_roots)
            __dataclass__object_setattr(self, 'system_read_roots', system_read_roots)
            __dataclass__object_setattr(self, 'exec_paths', exec_paths)
            __dataclass__object_setattr(self, 'allow_fork', allow_fork)
            __dataclass__object_setattr(self, 'mach_lookup', mach_lookup)
            __dataclass__object_setattr(self, 'sysctl_names', sysctl_names)
            __dataclass__object_setattr(self, 'allow_network', allow_network)
            __dataclass__object_setattr(self, 'dev', dev)
            __dataclass__object_setattr(self, 'allow_proc', allow_proc)
            __dataclass__object_setattr(self, 'private_tmp', private_tmp)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.read_roots)) is not None:
                parts.append(f"read_roots={s}")
            if (s := __dataclass__repr__default_fn(self.write_roots)) is not None:
                parts.append(f"write_roots={s}")
            if (s := __dataclass__repr__default_fn(self.system_read_roots)) is not None:
                parts.append(f"system_read_roots={s}")
            if (s := __dataclass__repr__default_fn(self.exec_paths)) is not None:
                parts.append(f"exec_paths={s}")
            if (s := __dataclass__repr__default_fn(self.allow_fork)) is not None:
                parts.append(f"allow_fork={s}")
            if (s := __dataclass__repr__default_fn(self.mach_lookup)) is not None:
                parts.append(f"mach_lookup={s}")
            if (s := __dataclass__repr__default_fn(self.sysctl_names)) is not None:
                parts.append(f"sysctl_names={s}")
            if (s := __dataclass__repr__default_fn(self.allow_network)) is not None:
                parts.append(f"allow_network={s}")
            if (s := __dataclass__repr__default_fn(self.dev)) is not None:
                parts.append(f"dev={s}")
            if (s := __dataclass__repr__default_fn(self.allow_proc)) is not None:
                parts.append(f"allow_proc={s}")
            if (s := __dataclass__repr__default_fn(self.private_tmp)) is not None:
                parts.append(f"private_tmp={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e7b34011eabb53e42e089cac515693670229e4e6',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('profile', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False), (('params', True, True, None, True, True, False, None), 'instance', 'missing',"
            " None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.sandbox.seatbelt', 'SeatbeltProfile'),
    ),
)
def _process_dataclass__e7b34011eabb53e42e089cac515693670229e4e6():
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
                profile=self.profile,
                params=self.params,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.profile == other.profile and
                self.params == other.params
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'profile',
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
                self.profile,
                self.params,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            profile: __dataclass__init__fields__0__annotation,
            params: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'profile', profile)
            __dataclass__object_setattr(self, 'params', params)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"profile={self.profile!r}")
            parts.append(f"params={self.params!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='742e410c2a6e143141ba7ce7b698dd8d45e44898',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('policy', True, True, None, True, True, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('sandbox_exec', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.sandbox.seatbelt', 'SeatbeltSandbox'),
    ),
)
def _process_dataclass__742e410c2a6e143141ba7ce7b698dd8d45e44898():
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
                policy=self.policy,
                sandbox_exec=self.sandbox_exec,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.policy == other.policy and
                self.sandbox_exec == other.sandbox_exec
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'policy',
            'sandbox_exec',
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
                self.policy,
                self.sandbox_exec,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            policy: __dataclass__init__fields__0__annotation,
            sandbox_exec: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'policy', policy)
            __dataclass__object_setattr(self, 'sandbox_exec', sandbox_exec)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.policy)) is not None:
                parts.append(f"policy={s}")
            if (s := __dataclass__repr__default_fn(self.sandbox_exec)) is not None:
                parts.append(f"sandbox_exec={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='71a3579f9ad08e8688beceb8077de12c2e296678',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('s', True, True, None, True, False, False, None), 'instance', 'missing', None"
            ", False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (),"
            " (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.sandbox.seatbelt', '_SxQuote'),
    ),
)
def _process_dataclass__71a3579f9ad08e8688beceb8077de12c2e296678():
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
                s=self.s,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.s == other.s
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            's',
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
                self.s,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            s: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 's', s)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"s={self.s!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='2ae51b611b6dc44956666ad30933628eb4c1e7f9',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('overall_timeout_s', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, True, ()),"
            " ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.scopes.policies', 'ScopeClosePolicy'),
    ),
)
def _process_dataclass__2ae51b611b6dc44956666ad30933628eb4c1e7f9():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default = __dataclass__spec.fields[0].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                overall_timeout_s=self.overall_timeout_s,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.overall_timeout_s == other.overall_timeout_s
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'overall_timeout_s',
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
                self.overall_timeout_s,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            overall_timeout_s: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'overall_timeout_s', overall_timeout_s)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"overall_timeout_s={self.overall_timeout_s!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='5ffe12d3ee076b15df5f72262bc81630aa0ca3fe',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('process', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False), (('returncode', True, True, None, True, True, False, None), 'instance', 'missi"
            "ng', None, False, False, False), (('output', True, True, None, True, True, False, None), 'instance', 'miss"
            "ing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ("
            "(),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.scopes.scope', 'ProcessRun'),
    ),
)
def _process_dataclass__5ffe12d3ee076b15df5f72262bc81630aa0ca3fe():
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
                process=self.process,
                returncode=self.returncode,
                output=self.output,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.process == other.process and
                self.returncode == other.returncode and
                self.output == other.output
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'process',
            'returncode',
            'output',
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
                self.process,
                self.returncode,
                self.output,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            process: __dataclass__init__fields__0__annotation,
            returncode: __dataclass__init__fields__1__annotation,
            output: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'process', process)
            __dataclass__object_setattr(self, 'returncode', returncode)
            __dataclass__object_setattr(self, 'output', output)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"process={self.process!r}")
            parts.append(f"returncode={self.returncode!r}")
            parts.append(f"output={self.output!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='2d773a40042aa41ebc92140d5438925f7aa6d7d9',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('num_processes', True, True, None, True, True, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('num_abandoned', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('errors', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ("
            ")), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.scopes.scope', 'ScopeCloseResult'),
    ),
)
def _process_dataclass__2d773a40042aa41ebc92140d5438925f7aa6d7d9():
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
                num_processes=self.num_processes,
                num_abandoned=self.num_abandoned,
                errors=self.errors,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.num_processes == other.num_processes and
                self.num_abandoned == other.num_abandoned and
                self.errors == other.errors
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'num_processes',
            'num_abandoned',
            'errors',
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
                self.num_processes,
                self.num_abandoned,
                self.errors,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            num_processes: __dataclass__init__fields__0__annotation,
            num_abandoned: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            errors: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'num_processes', num_processes)
            __dataclass__object_setattr(self, 'num_abandoned', num_abandoned)
            __dataclass__object_setattr(self, 'errors', errors)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"num_processes={self.num_processes!r}")
            parts.append(f"num_abandoned={self.num_abandoned!r}")
            parts.append(f"errors={self.errors!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='9cce39b7442fc8693e4c57752c11891e035b6a8b',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, True, False, False, False, Fals"
            "e, False, False, False), ((('fd', True, True, None, True, False, False, None), 'instance', 'missing', None"
            ", False, False, False), (('data', True, True, None, True, False, False, None), 'instance', 'missing', None"
            ", False, False, False), (('t_mono_ns', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False), (('t_wall_ns', True, True, None, True, True, False, None), 'instance', 'missin"
            "g', None, False, False, False), (('seq', True, True, None, True, True, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('offset', True, True, None, True, True, False, None), 'instance', 'missing"
            "', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (True,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.spool.frames', 'SpoolRecord'),
    ),
)
def _process_dataclass__9cce39b7442fc8693e4c57752c11891e035b6a8b():
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
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                fd=self.fd,
                data=self.data,
                t_mono_ns=self.t_mono_ns,
                t_wall_ns=self.t_wall_ns,
                seq=self.seq,
                offset=self.offset,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.fd == other.fd and
                self.data == other.data and
                self.t_mono_ns == other.t_mono_ns and
                self.t_wall_ns == other.t_wall_ns and
                self.seq == other.seq and
                self.offset == other.offset
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'fd',
            'data',
            't_mono_ns',
            't_wall_ns',
            'seq',
            'offset',
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
                    self.fd,
                    self.data,
                    self.t_mono_ns,
                    self.t_wall_ns,
                    self.seq,
                    self.offset,
                ))
            )
            return h

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            fd: __dataclass__init__fields__0__annotation,
            data: __dataclass__init__fields__1__annotation,
            *,
            t_mono_ns: __dataclass__init__fields__2__annotation,
            t_wall_ns: __dataclass__init__fields__3__annotation,
            seq: __dataclass__init__fields__4__annotation,
            offset: __dataclass__init__fields__5__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'fd', fd)
            __dataclass__object_setattr(self, 'data', data)
            __dataclass__object_setattr(self, 't_mono_ns', t_mono_ns)
            __dataclass__object_setattr(self, 't_wall_ns', t_wall_ns)
            __dataclass__object_setattr(self, 'seq', seq)
            __dataclass__object_setattr(self, 'offset', offset)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='aba28530a8e5f6106010161989ed3a5617d616e5',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('records', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False), (('start', True, True, None, True, True, False, None), 'instance', 'missing', "
            "None, False, False, False), (('end', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('total', True, True, None, True, True, False, None), 'instance', 'missing', No"
            "ne, False, False, False), (('dropped_before', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('ended', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.spool.spool', 'SpoolRead'),
    ),
)
def _process_dataclass__aba28530a8e5f6106010161989ed3a5617d616e5():
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
                records=self.records,
                start=self.start,
                end=self.end,
                total=self.total,
                dropped_before=self.dropped_before,
                ended=self.ended,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.records == other.records and
                self.start == other.start and
                self.end == other.end and
                self.total == other.total and
                self.dropped_before == other.dropped_before and
                self.ended == other.ended
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'records',
            'start',
            'end',
            'total',
            'dropped_before',
            'ended',
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
                self.records,
                self.start,
                self.end,
                self.total,
                self.dropped_before,
                self.ended,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            records: __dataclass__init__fields__0__annotation,
            start: __dataclass__init__fields__1__annotation,
            end: __dataclass__init__fields__2__annotation,
            total: __dataclass__init__fields__3__annotation,
            dropped_before: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            ended: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'records', records)
            __dataclass__object_setattr(self, 'start', start)
            __dataclass__object_setattr(self, 'end', end)
            __dataclass__object_setattr(self, 'total', total)
            __dataclass__object_setattr(self, 'dropped_before', dropped_before)
            __dataclass__object_setattr(self, 'ended', ended)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"records={self.records!r}")
            parts.append(f"start={self.start!r}")
            parts.append(f"end={self.end!r}")
            parts.append(f"total={self.total!r}")
            parts.append(f"dropped_before={self.dropped_before!r}")
            parts.append(f"ended={self.ended!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='81aac9fd77ab66ada6ba11d6c6b15a7529b4f9b1',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('container', True, True, None, True, True, False, None), 'instance', 'missing'"
            ", 'callable', False, False, False), (('user', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('extra_flags', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False), (('docker', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), "
            "((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.targets.docker', 'DockerExecTarget'),
    ),
)
def _process_dataclass__81aac9fd77ab66ada6ba11d6c6b15a7529b4f9b1():
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
                container=self.container,
                user=self.user,
                extra_flags=self.extra_flags,
                docker=self.docker,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.container == other.container and
                self.user == other.user and
                self.extra_flags == other.extra_flags and
                self.docker == other.docker
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'container',
            'user',
            'extra_flags',
            'docker',
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
                self.container,
                self.user,
                self.extra_flags,
                self.docker,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            container: __dataclass__init__fields__0__annotation,
            user: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            extra_flags: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            docker: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            container = __dataclass__init__fields__0__coerce(container)
            __dataclass__object_setattr(self, 'container', container)
            __dataclass__object_setattr(self, 'user', user)
            __dataclass__object_setattr(self, 'extra_flags', extra_flags)
            __dataclass__object_setattr(self, 'docker', docker)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.container)) is not None:
                parts.append(f"container={s}")
            if (s := __dataclass__repr__default_fn(self.user)) is not None:
                parts.append(f"user={s}")
            if (s := __dataclass__repr__default_fn(self.extra_flags)) is not None:
                parts.append(f"extra_flags={s}")
            if (s := __dataclass__repr__default_fn(self.docker)) is not None:
                parts.append(f"docker={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='1a01e9e4e3a9b0caced2a26e31c9be72049b7d70',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('host', True, True, None, True, True, False, None), 'instance', 'missing', 'ca"
            "llable', False, False, False), (('user', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('port', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('identity_file', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False), (('control_path', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False), (('control_persist', True, True, None, True, True, False, None), 'inst"
            "ance', 'value', None, False, False, False), (('no_host_key_checking', True, True, None, True, True, False,"
            " None), 'instance', 'value', None, False, False, False), (('extra_options', True, True, None, True, True, "
            "False, None), 'instance', 'value', None, False, False, False), (('ssh', True, True, None, True, True, Fals"
            "e, None), 'instance', 'value', None, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,"
            "), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.targets.ssh', 'SshTarget'),
    ),
)
def _process_dataclass__1a01e9e4e3a9b0caced2a26e31c9be72049b7d70():
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
        __dataclass__init__fields__6__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__6__default = __dataclass__spec.fields[6].default.must()
        __dataclass__init__fields__7__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__7__default = __dataclass__spec.fields[7].default.must()
        __dataclass__init__fields__8__annotation = __dataclass__spec.fields[8].annotation
        __dataclass__init__fields__8__default = __dataclass__spec.fields[8].default.must()
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
                host=self.host,
                user=self.user,
                port=self.port,
                identity_file=self.identity_file,
                control_path=self.control_path,
                control_persist=self.control_persist,
                no_host_key_checking=self.no_host_key_checking,
                extra_options=self.extra_options,
                ssh=self.ssh,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.host == other.host and
                self.user == other.user and
                self.port == other.port and
                self.identity_file == other.identity_file and
                self.control_path == other.control_path and
                self.control_persist == other.control_persist and
                self.no_host_key_checking == other.no_host_key_checking and
                self.extra_options == other.extra_options and
                self.ssh == other.ssh
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'host',
            'user',
            'port',
            'identity_file',
            'control_path',
            'control_persist',
            'no_host_key_checking',
            'extra_options',
            'ssh',
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
                self.host,
                self.user,
                self.port,
                self.identity_file,
                self.control_path,
                self.control_persist,
                self.no_host_key_checking,
                self.extra_options,
                self.ssh,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            host: __dataclass__init__fields__0__annotation,
            user: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            port: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            identity_file: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            control_path: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            control_persist: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            no_host_key_checking: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
            extra_options: __dataclass__init__fields__7__annotation = __dataclass__init__fields__7__default,
            ssh: __dataclass__init__fields__8__annotation = __dataclass__init__fields__8__default,
        ) -> __dataclass__None:
            host = __dataclass__init__fields__0__coerce(host)
            __dataclass__object_setattr(self, 'host', host)
            __dataclass__object_setattr(self, 'user', user)
            __dataclass__object_setattr(self, 'port', port)
            __dataclass__object_setattr(self, 'identity_file', identity_file)
            __dataclass__object_setattr(self, 'control_path', control_path)
            __dataclass__object_setattr(self, 'control_persist', control_persist)
            __dataclass__object_setattr(self, 'no_host_key_checking', no_host_key_checking)
            __dataclass__object_setattr(self, 'extra_options', extra_options)
            __dataclass__object_setattr(self, 'ssh', ssh)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.host)) is not None:
                parts.append(f"host={s}")
            if (s := __dataclass__repr__default_fn(self.user)) is not None:
                parts.append(f"user={s}")
            if (s := __dataclass__repr__default_fn(self.port)) is not None:
                parts.append(f"port={s}")
            if (s := __dataclass__repr__default_fn(self.identity_file)) is not None:
                parts.append(f"identity_file={s}")
            if (s := __dataclass__repr__default_fn(self.control_path)) is not None:
                parts.append(f"control_path={s}")
            if (s := __dataclass__repr__default_fn(self.control_persist)) is not None:
                parts.append(f"control_persist={s}")
            if (s := __dataclass__repr__default_fn(self.no_host_key_checking)) is not None:
                parts.append(f"no_host_key_checking={s}")
            if (s := __dataclass__repr__default_fn(self.extra_options)) is not None:
                parts.append(f"extra_options={s}")
            if (s := __dataclass__repr__default_fn(self.ssh)) is not None:
                parts.append(f"ssh={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='fdadf05e0604cd200484ba64fb548aae8fa0af71',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, False, False, False, False, False, False, False, False, Fa"
            "lse, False, False, False), ((('stage', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('errno', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('message', True, True, None, True, False, False, None), 'instance', 'missi"
            "ng', None, False, False, False), (('argv', True, True, None, True, False, False, None), 'instance', 'value"
            "', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.types.errors', 'SpawnError'),
    ),
)
def _process_dataclass__fdadf05e0604cd200484ba64fb548aae8fa0af71():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                stage=self.stage,
                errno=self.errno,
                message=self.message,
                argv=self.argv,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.stage == other.stage and
                self.errno == other.errno and
                self.message == other.message and
                self.argv == other.argv
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            stage: __dataclass__init__fields__0__annotation,
            errno: __dataclass__init__fields__1__annotation,
            message: __dataclass__init__fields__2__annotation,
            argv: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            self.stage = stage
            self.errno = errno
            self.message = message
            self.argv = argv

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"stage={self.stage!r}")
            parts.append(f"errno={self.errno!r}")
            parts.append(f"message={self.message!r}")
            parts.append(f"argv={self.argv!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='07e3040a2b4c534c29936d07ce8263a463115ce7',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('process_id', True, True, None, True, True, False, None), 'instance', 'missing"
            "', None, False, False, False), (('pid', True, True, None, True, True, False, None), 'instance', 'missing',"
            " None, False, False, False), (('scope_path', True, True, None, True, True, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('state', True, True, None, True, True, False, None), 'instance', 'miss"
            "ing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ("
            "(),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.types.events', 'ProcessAbandonedEvent'),
    ),
)
def _process_dataclass__07e3040a2b4c534c29936d07ce8263a463115ce7():
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
                process_id=self.process_id,
                pid=self.pid,
                scope_path=self.scope_path,
                state=self.state,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.process_id == other.process_id and
                self.pid == other.pid and
                self.scope_path == other.scope_path and
                self.state == other.state
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'process_id',
            'pid',
            'scope_path',
            'state',
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
                self.process_id,
                self.pid,
                self.scope_path,
                self.state,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            process_id: __dataclass__init__fields__0__annotation,
            pid: __dataclass__init__fields__1__annotation,
            scope_path: __dataclass__init__fields__2__annotation,
            state: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'process_id', process_id)
            __dataclass__object_setattr(self, 'pid', pid)
            __dataclass__object_setattr(self, 'scope_path', scope_path)
            __dataclass__object_setattr(self, 'state', state)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"process_id={self.process_id!r}")
            parts.append(f"pid={self.pid!r}")
            parts.append(f"scope_path={self.scope_path!r}")
            parts.append(f"state={self.state!r}")
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
    ),
    cls_names=(
        ('omllm.core.processes.types.events', 'ProcessEvent'),
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
    installer_sha1='ed91946114af3c03ac94f5f83dfcb1532b7bdd0e',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('process_id', True, True, None, True, True, False, None), 'instance', 'missing"
            "', None, False, False, False), (('pid', True, True, None, True, True, False, None), 'instance', 'missing',"
            " None, False, False, False), (('scope_path', True, True, None, True, True, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('returncode', True, True, None, True, True, False, None), 'instance', "
            "'missing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ("
            ")), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.types.events', 'ProcessExitedEvent'),
        ('omllm.core.processes.types.events', 'ProcessReapedEvent'),
    ),
)
def _process_dataclass__ed91946114af3c03ac94f5f83dfcb1532b7bdd0e():
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
                process_id=self.process_id,
                pid=self.pid,
                scope_path=self.scope_path,
                returncode=self.returncode,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.process_id == other.process_id and
                self.pid == other.pid and
                self.scope_path == other.scope_path and
                self.returncode == other.returncode
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'process_id',
            'pid',
            'scope_path',
            'returncode',
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
                self.process_id,
                self.pid,
                self.scope_path,
                self.returncode,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            process_id: __dataclass__init__fields__0__annotation,
            pid: __dataclass__init__fields__1__annotation,
            scope_path: __dataclass__init__fields__2__annotation,
            returncode: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'process_id', process_id)
            __dataclass__object_setattr(self, 'pid', pid)
            __dataclass__object_setattr(self, 'scope_path', scope_path)
            __dataclass__object_setattr(self, 'returncode', returncode)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"process_id={self.process_id!r}")
            parts.append(f"pid={self.pid!r}")
            parts.append(f"scope_path={self.scope_path!r}")
            parts.append(f"returncode={self.returncode!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='a7807ec8b489484a630ffdbc3923102f200b1ee6',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('process_id', True, True, None, True, True, False, None), 'instance', 'missing"
            "', None, False, False, False), (('pid', True, True, None, True, True, False, None), 'instance', 'missing',"
            " None, False, False, False), (('scope_path', True, True, None, True, True, False, None), 'instance', 'miss"
            "ing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ("
            "(),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.types.events', 'ProcessLifecycleEvent'),
    ),
)
def _process_dataclass__a7807ec8b489484a630ffdbc3923102f200b1ee6():
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
                process_id=self.process_id,
                pid=self.pid,
                scope_path=self.scope_path,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.process_id == other.process_id and
                self.pid == other.pid and
                self.scope_path == other.scope_path
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'process_id',
            'pid',
            'scope_path',
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
                self.process_id,
                self.pid,
                self.scope_path,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            process_id: __dataclass__init__fields__0__annotation,
            pid: __dataclass__init__fields__1__annotation,
            scope_path: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'process_id', process_id)
            __dataclass__object_setattr(self, 'pid', pid)
            __dataclass__object_setattr(self, 'scope_path', scope_path)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"process_id={self.process_id!r}")
            parts.append(f"pid={self.pid!r}")
            parts.append(f"scope_path={self.scope_path!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='16d19e443ab9241dd54221760700baf22a17af1a',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('process_id', True, True, None, True, True, False, None), 'instance', 'missing"
            "', None, False, False, False), (('pid', True, True, None, True, True, False, None), 'instance', 'missing',"
            " None, False, False, False), (('scope_path', True, True, None, True, True, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('reason', True, True, None, True, True, False, None), 'instance', 'mis"
            "sing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), "
            "((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.types.events', 'ProcessPoisonedEvent'),
    ),
)
def _process_dataclass__16d19e443ab9241dd54221760700baf22a17af1a():
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
                process_id=self.process_id,
                pid=self.pid,
                scope_path=self.scope_path,
                reason=self.reason,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.process_id == other.process_id and
                self.pid == other.pid and
                self.scope_path == other.scope_path and
                self.reason == other.reason
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'process_id',
            'pid',
            'scope_path',
            'reason',
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
                self.process_id,
                self.pid,
                self.scope_path,
                self.reason,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            process_id: __dataclass__init__fields__0__annotation,
            pid: __dataclass__init__fields__1__annotation,
            scope_path: __dataclass__init__fields__2__annotation,
            reason: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'process_id', process_id)
            __dataclass__object_setattr(self, 'pid', pid)
            __dataclass__object_setattr(self, 'scope_path', scope_path)
            __dataclass__object_setattr(self, 'reason', reason)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"process_id={self.process_id!r}")
            parts.append(f"pid={self.pid!r}")
            parts.append(f"scope_path={self.scope_path!r}")
            parts.append(f"reason={self.reason!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e40259201f6e92e094acf6414d49d38383a9de53',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('process_id', True, True, None, True, True, False, None), 'instance', 'missing"
            "', None, False, False, False), (('pid', True, True, None, True, True, False, None), 'instance', 'missing',"
            " None, False, False, False), (('scope_path', True, True, None, True, True, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('old_scope_path', True, True, None, True, True, False, None), 'instanc"
            "e', 'missing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, Fals"
            "e, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.types.events', 'ProcessReparentedEvent'),
    ),
)
def _process_dataclass__e40259201f6e92e094acf6414d49d38383a9de53():
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
                process_id=self.process_id,
                pid=self.pid,
                scope_path=self.scope_path,
                old_scope_path=self.old_scope_path,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.process_id == other.process_id and
                self.pid == other.pid and
                self.scope_path == other.scope_path and
                self.old_scope_path == other.old_scope_path
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'process_id',
            'pid',
            'scope_path',
            'old_scope_path',
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
                self.process_id,
                self.pid,
                self.scope_path,
                self.old_scope_path,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            process_id: __dataclass__init__fields__0__annotation,
            pid: __dataclass__init__fields__1__annotation,
            scope_path: __dataclass__init__fields__2__annotation,
            old_scope_path: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'process_id', process_id)
            __dataclass__object_setattr(self, 'pid', pid)
            __dataclass__object_setattr(self, 'scope_path', scope_path)
            __dataclass__object_setattr(self, 'old_scope_path', old_scope_path)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"process_id={self.process_id!r}")
            parts.append(f"pid={self.pid!r}")
            parts.append(f"scope_path={self.scope_path!r}")
            parts.append(f"old_scope_path={self.old_scope_path!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d43d5f5e3e6617cc9e5c557a8f4d4d2083aa34fc',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('process_id', True, True, None, True, True, False, None), 'instance', 'missing"
            "', None, False, False, False), (('pid', True, True, None, True, True, False, None), 'instance', 'missing',"
            " None, False, False, False), (('scope_path', True, True, None, True, True, False, None), 'instance', 'miss"
            "ing', None, False, False, False), (('argv', True, True, None, True, True, False, None), 'instance', 'missi"
            "ng', None, False, False, False), (('name', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.types.events', 'ProcessSpawnedEvent'),
    ),
)
def _process_dataclass__d43d5f5e3e6617cc9e5c557a8f4d4d2083aa34fc():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                process_id=self.process_id,
                pid=self.pid,
                scope_path=self.scope_path,
                argv=self.argv,
                name=self.name,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.process_id == other.process_id and
                self.pid == other.pid and
                self.scope_path == other.scope_path and
                self.argv == other.argv and
                self.name == other.name
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'process_id',
            'pid',
            'scope_path',
            'argv',
            'name',
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
                self.process_id,
                self.pid,
                self.scope_path,
                self.argv,
                self.name,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            process_id: __dataclass__init__fields__0__annotation,
            pid: __dataclass__init__fields__1__annotation,
            scope_path: __dataclass__init__fields__2__annotation,
            argv: __dataclass__init__fields__3__annotation,
            name: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'process_id', process_id)
            __dataclass__object_setattr(self, 'pid', pid)
            __dataclass__object_setattr(self, 'scope_path', scope_path)
            __dataclass__object_setattr(self, 'argv', argv)
            __dataclass__object_setattr(self, 'name', name)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"process_id={self.process_id!r}")
            parts.append(f"pid={self.pid!r}")
            parts.append(f"scope_path={self.scope_path!r}")
            parts.append(f"argv={self.argv!r}")
            parts.append(f"name={self.name!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e1d1399b5d759895e310fa36a666a89f96194c35',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('scope_path', True, True, None, True, True, False, None), 'instance', 'missing"
            "', None, False, False, False), (('num_processes', True, True, None, True, True, False, None), 'instance', "
            "'missing', None, False, False, False), (('num_abandoned', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, Fa"
            "lse, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.types.events', 'ScopeClosedEvent'),
    ),
)
def _process_dataclass__e1d1399b5d759895e310fa36a666a89f96194c35():
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
                scope_path=self.scope_path,
                num_processes=self.num_processes,
                num_abandoned=self.num_abandoned,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.scope_path == other.scope_path and
                self.num_processes == other.num_processes and
                self.num_abandoned == other.num_abandoned
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'scope_path',
            'num_processes',
            'num_abandoned',
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
                self.scope_path,
                self.num_processes,
                self.num_abandoned,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            scope_path: __dataclass__init__fields__0__annotation,
            num_processes: __dataclass__init__fields__1__annotation,
            num_abandoned: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'scope_path', scope_path)
            __dataclass__object_setattr(self, 'num_processes', num_processes)
            __dataclass__object_setattr(self, 'num_abandoned', num_abandoned)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"scope_path={self.scope_path!r}")
            parts.append(f"num_processes={self.num_processes!r}")
            parts.append(f"num_abandoned={self.num_abandoned!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='62cf072dbcd094c2f969b9a153e8ddccf5453910',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('scope_path', True, True, None, True, True, False, None), 'instance', 'missing"
            "', None, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), (()"
            ",), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.types.events', 'ScopeEvent'),
        ('omllm.core.processes.types.events', 'ScopeOpenedEvent'),
    ),
)
def _process_dataclass__62cf072dbcd094c2f969b9a153e8ddccf5453910():
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
                scope_path=self.scope_path,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.scope_path == other.scope_path
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'scope_path',
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
                self.scope_path,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            scope_path: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'scope_path', scope_path)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"scope_path={self.scope_path!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c2ede84a2bddfbb71a4f115ebb3274de47480920',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('user', True, True, None, True, True, False, None), 'instance', 'value', None,"
            " False, False, False), (('group', True, True, None, True, True, False, None), 'instance', 'value', None, F"
            "alse, False, False), (('extra_groups', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.types.options', 'Credentials'),
    ),
)
def _process_dataclass__c2ede84a2bddfbb71a4f115ebb3274de47480920():
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
                user=self.user,
                group=self.group,
                extra_groups=self.extra_groups,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.user == other.user and
                self.group == other.group and
                self.extra_groups == other.extra_groups
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'user',
            'group',
            'extra_groups',
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
                self.user,
                self.group,
                self.extra_groups,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            user: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            group: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            extra_groups: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'user', user)
            __dataclass__object_setattr(self, 'group', group)
            __dataclass__object_setattr(self, 'extra_groups', extra_groups)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"user={self.user!r}")
            parts.append(f"group={self.group!r}")
            parts.append(f"extra_groups={self.extra_groups!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='36d5209b78c945ea8a4b1b50d99ff5fc43cfac77',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('signal', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.types.options', 'Deathsig'),
    ),
)
def _process_dataclass__36d5209b78c945ea8a4b1b50d99ff5fc43cfac77():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default = __dataclass__spec.fields[0].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                signal=self.signal,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.signal == other.signal
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'signal',
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
                self.signal,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            signal: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'signal', signal)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"signal={self.signal!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='40733ba6ae9b777bf5e2feb83e79eb04fa032879',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, True, False, False, Fals"
            "e, False, True, True), ((('v', True, True, None, True, False, False, None), 'instance', 'missing', None, F"
            "alse, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (F"
            "alse,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.types.options', 'PassFd'),
        ('omllm.core.processes.types.options', 'RunTimeout'),
        ('omllm.core.processes.types.options', 'Tag'),
        ('omllm.core.processes.types.options', 'Umask'),
    ),
)
def _process_dataclass__40733ba6ae9b777bf5e2feb83e79eb04fa032879():
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
    installer_sha1='15e6e0a0d75a26916602416a3bfabf241728edce',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('resource', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('soft', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False), (('hard', True, True, None, True, False, False, None), 'instance', 'missing"
            "', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),"
            "), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.types.options', 'Rlimit'),
    ),
)
def _process_dataclass__15e6e0a0d75a26916602416a3bfabf241728edce():
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
                resource=self.resource,
                soft=self.soft,
                hard=self.hard,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.resource == other.resource and
                self.soft == other.soft and
                self.hard == other.hard
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'resource',
            'soft',
            'hard',
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
                self.resource,
                self.soft,
                self.hard,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            resource: __dataclass__init__fields__0__annotation,
            soft: __dataclass__init__fields__1__annotation,
            hard: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'resource', resource)
            __dataclass__object_setattr(self, 'soft', soft)
            __dataclass__object_setattr(self, 'hard', hard)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"resource={self.resource!r}")
            parts.append(f"soft={self.soft!r}")
            parts.append(f"hard={self.hard!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c176d65cd567cd08b713fa0be39730f9d9c0b893',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('mode', True, True, None, True, True, False, None), 'instance', 'value', None,"
            " False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), "
            "(False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.types.options', 'SessionMode'),
    ),
)
def _process_dataclass__c176d65cd567cd08b713fa0be39730f9d9c0b893():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__0__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__0__default = __dataclass__spec.fields[0].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                mode=self.mode,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.mode == other.mode
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'mode',
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
                self.mode,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            mode: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'mode', mode)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"mode={self.mode!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='7a627fed829a21150ba95491a1df06ae7d6995ed',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('memory_cap', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('spill', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('keep_spill', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, True, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.types.options', 'SpoolPolicy'),
    ),
)
def _process_dataclass__7a627fed829a21150ba95491a1df06ae7d6995ed():
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
                memory_cap=self.memory_cap,
                spill=self.spill,
                keep_spill=self.keep_spill,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.memory_cap == other.memory_cap and
                self.spill == other.spill and
                self.keep_spill == other.keep_spill
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'memory_cap',
            'spill',
            'keep_spill',
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
                self.memory_cap,
                self.spill,
                self.keep_spill,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            memory_cap: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            spill: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            keep_spill: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'memory_cap', memory_cap)
            __dataclass__object_setattr(self, 'spill', spill)
            __dataclass__object_setattr(self, 'keep_spill', keep_spill)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"memory_cap={self.memory_cap!r}")
            parts.append(f"spill={self.spill!r}")
            parts.append(f"keep_spill={self.keep_spill!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b7e1f7d13a8d8515b788790b1833e40169f453ec',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('signal', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('grace_s', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('kill_s', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('close_stdin', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('process_group', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('drain_s', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('on_stuck', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, True, ()), ("
            "(),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.types.options', 'TerminationPolicy'),
    ),
)
def _process_dataclass__b7e1f7d13a8d8515b788790b1833e40169f453ec():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                signal=self.signal,
                grace_s=self.grace_s,
                kill_s=self.kill_s,
                close_stdin=self.close_stdin,
                process_group=self.process_group,
                drain_s=self.drain_s,
                on_stuck=self.on_stuck,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.signal == other.signal and
                self.grace_s == other.grace_s and
                self.kill_s == other.kill_s and
                self.close_stdin == other.close_stdin and
                self.process_group == other.process_group and
                self.drain_s == other.drain_s and
                self.on_stuck == other.on_stuck
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'signal',
            'grace_s',
            'kill_s',
            'close_stdin',
            'process_group',
            'drain_s',
            'on_stuck',
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
                self.signal,
                self.grace_s,
                self.kill_s,
                self.close_stdin,
                self.process_group,
                self.drain_s,
                self.on_stuck,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            signal: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            grace_s: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            kill_s: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            close_stdin: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            process_group: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            drain_s: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
            on_stuck: __dataclass__init__fields__6__annotation = __dataclass__init__fields__6__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'signal', signal)
            __dataclass__object_setattr(self, 'grace_s', grace_s)
            __dataclass__object_setattr(self, 'kill_s', kill_s)
            __dataclass__object_setattr(self, 'close_stdin', close_stdin)
            __dataclass__object_setattr(self, 'process_group', process_group)
            __dataclass__object_setattr(self, 'drain_s', drain_s)
            __dataclass__object_setattr(self, 'on_stuck', on_stuck)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"signal={self.signal!r}")
            parts.append(f"grace_s={self.grace_s!r}")
            parts.append(f"kill_s={self.kill_s!r}")
            parts.append(f"close_stdin={self.close_stdin!r}")
            parts.append(f"process_group={self.process_group!r}")
            parts.append(f"drain_s={self.drain_s!r}")
            parts.append(f"on_stuck={self.on_stuck!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='eb7fd37a989e2c08ca802524c5e65a9ab93d6436',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, True, False, False, False, Fals"
            "e, False, False, False), ((('argv', True, True, None, True, False, False, None), 'instance', 'missing', 'c"
            "allable', False, False, False), (('cwd', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('env', True, True, None, True, True, False, None), 'instance', 'value', 'cal"
            "lable', False, False, False), (('stdio', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('name', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), "
            "(False,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.types.specs', 'ProcessSpec'),
    ),
)
def _process_dataclass__eb7fd37a989e2c08ca802524c5e65a9ab93d6436():
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
        __dataclass__init__fields__2__coerce = __dataclass__spec.fields[2].coerce
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
                argv=self.argv,
                cwd=self.cwd,
                env=self.env,
                stdio=self.stdio,
                name=self.name,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.argv == other.argv and
                self.cwd == other.cwd and
                self.env == other.env and
                self.stdio == other.stdio and
                self.name == other.name
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'argv',
            'cwd',
            'env',
            'stdio',
            'name',
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
                    self.argv,
                    self.cwd,
                    self.env,
                    self.stdio,
                    self.name,
                ))
            )
            return h

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            argv: __dataclass__init__fields__0__annotation,
            *,
            cwd: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            env: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            stdio: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            name: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            argv = __dataclass__init__fields__0__coerce(argv)
            env = __dataclass__init__fields__2__coerce(env)
            __dataclass__object_setattr(self, 'argv', argv)
            __dataclass__object_setattr(self, 'cwd', cwd)
            __dataclass__object_setattr(self, 'env', env)
            __dataclass__object_setattr(self, 'stdio', stdio)
            __dataclass__object_setattr(self, 'name', name)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.argv)) is not None:
                parts.append(f"argv={s}")
            if (s := __dataclass__repr__default_fn(self.cwd)) is not None:
                parts.append(f"cwd={s}")
            if (s := __dataclass__repr__default_fn(self.env)) is not None:
                parts.append(f"env={s}")
            if (s := __dataclass__repr__default_fn(self.stdio)) is not None:
                parts.append(f"stdio={s}")
            if (s := __dataclass__repr__default_fn(self.name)) is not None:
                parts.append(f"name={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='59c3be5a5e41f4ee994054ae35a7e2e1e65ec221',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, True, False, False, False, False"
            ", False, False, False), ((('stdin', True, True, None, True, True, False, None), 'instance', 'value', None,"
            " False, False, False), (('stdout', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False), (('stderr', True, True, None, True, True, False, None), 'instance', 'value', None, F"
            "alse, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, True, ()), ((),), (), (Fal"
            "se,)))"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.types.specs', 'ProcessStdio'),
    ),
)
def _process_dataclass__59c3be5a5e41f4ee994054ae35a7e2e1e65ec221():
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
                stdin=self.stdin,
                stdout=self.stdout,
                stderr=self.stderr,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.stdin == other.stdin and
                self.stdout == other.stdout and
                self.stderr == other.stderr
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'stdin',
            'stdout',
            'stderr',
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
                    self.stdin,
                    self.stdout,
                    self.stderr,
                ))
            )
            return h

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            stdin: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            stdout: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            stderr: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'stdin', stdin)
            __dataclass__object_setattr(self, 'stdout', stdout)
            __dataclass__object_setattr(self, 'stderr', stderr)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"stdin={self.stdin!r}")
            parts.append(f"stdout={self.stdout!r}")
            parts.append(f"stderr={self.stderr!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b9ed46e78200b5480dfd2b0108f5a3e97735c797',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, True, False, False, False, False"
            ", False, False, False), ((('rows', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False), (('cols', True, True, None, True, True, False, None), 'instance', 'value', None, Fal"
            "se, False, False), (('term', True, True, None, True, True, False, None), 'instance', 'value', None, False,"
            " False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, True, ()), ((),), (), (False,))"
            ")"
        ),
    ),
    cls_names=(
        ('omllm.core.processes.types.specs', 'PtyStdio'),
    ),
)
def _process_dataclass__b9ed46e78200b5480dfd2b0108f5a3e97735c797():
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
                rows=self.rows,
                cols=self.cols,
                term=self.term,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.rows == other.rows and
                self.cols == other.cols and
                self.term == other.term
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'rows',
            'cols',
            'term',
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
                    self.rows,
                    self.cols,
                    self.term,
                ))
            )
            return h

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            rows: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            cols: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            term: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'rows', rows)
            __dataclass__object_setattr(self, 'cols', cols)
            __dataclass__object_setattr(self, 'term', term)
            self.__post_init__()

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"rows={self.rows!r}")
            parts.append(f"cols={self.cols!r}")
            parts.append(f"term={self.term!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
