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
        "Plans(tup=(CopyPlan(fields=('spec', 'argv', 'env', 'control_fd', 'send_fds', 'owned_fds')), EqPlan(fields=('sp"
        "ec', 'argv', 'env', 'control_fd', 'send_fds', 'owned_fds')), FrozenPlan(fields=('spec', 'argv', 'env', 'contro"
        "l_fd', 'send_fds', 'owned_fds'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('spec', 'ar"
        "gv', 'env', 'control_fd', 'send_fds', 'owned_fds'), cache=False), InitPlan(fields=(InitPlan.Field(name='spec',"
        " annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=Fa"
        "lse, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='argv', "
        "annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override=Fal"
        "se, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='env', an"
        "notation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=False"
        ", field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='control_fd"
        "', annotation=OpRef(name='init.fields.3.annotation'), default=None, default_factory=None, init=True, override="
        "False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='send_"
        "fds', annotation=OpRef(name='init.fields.4.annotation'), default=OpRef(name='init.fields.4.default'), default_"
        "factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type"
        "=None), InitPlan.Field(name='owned_fds', annotation=OpRef(name='init.fields.5.annotation'), default=OpRef(name"
        "='init.fields.5.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coe"
        "rce=None, validate=None, check_type=None)), self_param='self', std_params=(), kw_only_params=('spec', 'argv', "
        "'env', 'control_fd', 'send_fds', 'owned_fds'), frozen=True, slots=False, post_init_params=None, init_fns=(), v"
        "alidate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='spec', kw_only=True, fn=None), ReprPlan.Field(name='arg"
        "v', kw_only=True, fn=None), ReprPlan.Field(name='env', kw_only=True, fn=None), ReprPlan.Field(name='control_fd"
        "', kw_only=True, fn=None), ReprPlan.Field(name='send_fds', kw_only=True, fn=None), ReprPlan.Field(name='owned_"
        "fds', kw_only=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='4bc1b57adcea5798c1143724d439bb79fef3b28a',
    cls_names=(
        ('omllm.core.processes.launch.launcher', 'LaunchPlan'),
    ),
)
def _process_dataclass__4bc1b57adcea5798c1143724d439bb79fef3b28a():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('remove', 'keep')), EqPlan(fields=('remove', 'keep')), FrozenPlan(fields=('remove'"
        ", 'keep'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('remove', 'keep'), cache=False), "
        "InitPlan(fields=(InitPlan.Field(name='remove', annotation=OpRef(name='init.fields.0.annotation'), default=OpRe"
        "f(name='init.fields.0.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANC"
        "E, coerce=None, validate=None, check_type=None), InitPlan.Field(name='keep', annotation=OpRef(name='init.field"
        "s.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False"
        ", field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params="
        "(), kw_only_params=('remove', 'keep'), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_"
        "fns=()), ReprPlan(fields=(ReprPlan.Field(name='remove', kw_only=True, fn=None), ReprPlan.Field(name='keep', kw"
        "_only=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='d5e4f63ce7138d8b3a84c09932de4695692f22a7',
    cls_names=(
        ('omllm.core.processes.launch.transforms', 'EnvScrubTransform'),
    ),
)
def _process_dataclass__d5e4f63ce7138d8b3a84c09932de4695692f22a7():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__default,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('stdin_fd', 'stdout_fd', 'stderr_fd', 'child_fds', 'parent_fds', 'stdin_w', 'outpu"
        "t_reads', 'pty_master_fd')), EqPlan(fields=('stdin_fd', 'stdout_fd', 'stderr_fd', 'child_fds', 'parent_fds', '"
        "stdin_w', 'output_reads', 'pty_master_fd')), FrozenPlan(fields=('stdin_fd', 'stdout_fd', 'stderr_fd', 'child_f"
        "ds', 'parent_fds', 'stdin_w', 'output_reads', 'pty_master_fd'), allow_dynamic_dunder_attrs=False), HashPlan(ac"
        "tion='add', fields=('stdin_fd', 'stdout_fd', 'stderr_fd', 'child_fds', 'parent_fds', 'stdin_w', 'output_reads'"
        ", 'pty_master_fd'), cache=False), InitPlan(fields=(InitPlan.Field(name='stdin_fd', annotation=OpRef(name='init"
        ".fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.IN"
        "STANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='stdout_fd', annotation=OpRef(name='"
        "init.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldTyp"
        "e.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='stderr_fd', annotation=OpRef(na"
        "me='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=False, field_type=Fiel"
        "dType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='child_fds', annotation=OpRe"
        "f(name='init.fields.3.annotation'), default=None, default_factory=None, init=True, override=False, field_type="
        "FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='parent_fds', annotation"
        "=OpRef(name='init.fields.4.annotation'), default=None, default_factory=None, init=True, override=False, field_"
        "type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='stdin_w', annotati"
        "on=OpRef(name='init.fields.5.annotation'), default=None, default_factory=None, init=True, override=False, fiel"
        "d_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='output_reads', a"
        "nnotation=OpRef(name='init.fields.6.annotation'), default=None, default_factory=None, init=True, override=Fals"
        "e, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='pty_maste"
        "r_fd', annotation=OpRef(name='init.fields.7.annotation'), default=OpRef(name='init.fields.7.default'), default"
        "_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_typ"
        "e=None)), self_param='self', std_params=(), kw_only_params=('stdin_fd', 'stdout_fd', 'stderr_fd', 'child_fds',"
        " 'parent_fds', 'stdin_w', 'output_reads', 'pty_master_fd'), frozen=True, slots=False, post_init_params=None, i"
        "nit_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='stdin_fd', kw_only=True, fn=None), ReprPla"
        "n.Field(name='stdout_fd', kw_only=True, fn=None), ReprPlan.Field(name='stderr_fd', kw_only=True, fn=None), Rep"
        "rPlan.Field(name='child_fds', kw_only=True, fn=None), ReprPlan.Field(name='parent_fds', kw_only=True, fn=None)"
        ", ReprPlan.Field(name='stdin_w', kw_only=True, fn=None), ReprPlan.Field(name='output_reads', kw_only=True, fn="
        "None), ReprPlan.Field(name='pty_master_fd', kw_only=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='a0953f5bad341f1112fcab7c77882e0c6d269fa8',
    cls_names=(
        ('omllm.core.processes.managers.stdio', 'StdioSetup'),
    ),
)
def _process_dataclass__a0953f5bad341f1112fcab7c77882e0c6d269fa8():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__4__annotation,
        __dataclass__init__fields__5__annotation,
        __dataclass__init__fields__6__annotation,
        __dataclass__init__fields__7__annotation,
        __dataclass__init__fields__7__default,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('shim_python', 'spill_dir', 'default_options', 'close_policy', 'spawn_timeout_s'))"
        ", EqPlan(fields=('shim_python', 'spill_dir', 'default_options', 'close_policy', 'spawn_timeout_s')), FrozenPla"
        "n(fields=('shim_python', 'spill_dir', 'default_options', 'close_policy', 'spawn_timeout_s'), allow_dynamic_dun"
        "der_attrs=False), HashPlan(action='add', fields=('shim_python', 'spill_dir', 'default_options', 'close_policy'"
        ", 'spawn_timeout_s'), cache=False), InitPlan(fields=(InitPlan.Field(name='shim_python', annotation=OpRef(name="
        "'init.fields.0.annotation'), default=OpRef(name='init.fields.0.default'), default_factory=None, init=True, ove"
        "rride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name="
        "'spill_dir', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), d"
        "efault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, che"
        "ck_type=None), InitPlan.Field(name='default_options', annotation=OpRef(name='init.fields.2.annotation'), defau"
        "lt=OpRef(name='init.fields.2.default'), default_factory=None, init=True, override=False, field_type=FieldType."
        "INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='close_policy', annotation=OpRef(n"
        "ame='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default'), default_factory=None, init=True,"
        " override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(n"
        "ame='spawn_timeout_s', annotation=OpRef(name='init.fields.4.annotation'), default=OpRef(name='init.fields.4.de"
        "fault'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate"
        "=None, check_type=None)), self_param='self', std_params=(), kw_only_params=('shim_python', 'spill_dir', 'defau"
        "lt_options', 'close_policy', 'spawn_timeout_s'), frozen=True, slots=False, post_init_params=None, init_fns=(),"
        " validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='shim_python', kw_only=True, fn=None), ReprPlan.Field("
        "name='spill_dir', kw_only=True, fn=None), ReprPlan.Field(name='default_options', kw_only=True, fn=None), ReprP"
        "lan.Field(name='close_policy', kw_only=True, fn=None), ReprPlan.Field(name='spawn_timeout_s', kw_only=True, fn"
        "=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='a2b043166b6926b743f271a348e9635f0e81d563',
    cls_names=(
        ('omllm.core.processes.managers.types', 'ManagerConfig'),
    ),
)
def _process_dataclass__a2b043166b6926b743f271a348e9635f0e81d563():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('policy', 'bwrap', 'new_session')), EqPlan(fields=('policy', 'bwrap', 'new_session"
        "')), FrozenPlan(fields=('policy', 'bwrap', 'new_session'), allow_dynamic_dunder_attrs=False), HashPlan(action="
        "'add', fields=('policy', 'bwrap', 'new_session'), cache=False), InitPlan(fields=(InitPlan.Field(name='policy',"
        " annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=Fa"
        "lse, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='bwrap',"
        " annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_facto"
        "ry=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None"
        "), InitPlan.Field(name='new_session', annotation=OpRef(name='init.fields.2.annotation'), default=OpRef(name='i"
        "nit.fields.2.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce"
        "=None, validate=None, check_type=None)), self_param='self', std_params=(), kw_only_params=('policy', 'bwrap', "
        "'new_session'), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(field"
        "s=(ReprPlan.Field(name='policy', kw_only=True, fn=None), ReprPlan.Field(name='bwrap', kw_only=True, fn=None), "
        "ReprPlan.Field(name='new_session', kw_only=True, fn=None)), id=False, terse=False, default_fn=OpRef(name='repr"
        ".default_fn'))))"
    ),
    plan_repr_sha1='b0970e45851c1e889b0d27399f609e750cce1e3f',
    cls_names=(
        ('omllm.core.processes.sandbox.bwrap', 'BwrapSandbox'),
    ),
)
def _process_dataclass__b0970e45851c1e889b0d27399f609e750cce1e3f():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('read_roots', 'write_roots', 'system_read_roots', 'exec_paths', 'allow_fork', 'mac"
        "h_lookup', 'sysctl_names', 'allow_network', 'dev', 'allow_proc', 'private_tmp')), EqPlan(fields=('read_roots',"
        " 'write_roots', 'system_read_roots', 'exec_paths', 'allow_fork', 'mach_lookup', 'sysctl_names', 'allow_network"
        "', 'dev', 'allow_proc', 'private_tmp')), FrozenPlan(fields=('read_roots', 'write_roots', 'system_read_roots', "
        "'exec_paths', 'allow_fork', 'mach_lookup', 'sysctl_names', 'allow_network', 'dev', 'allow_proc', 'private_tmp'"
        "), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('read_roots', 'write_roots', 'system_read"
        "_roots', 'exec_paths', 'allow_fork', 'mach_lookup', 'sysctl_names', 'allow_network', 'dev', 'allow_proc', 'pri"
        "vate_tmp'), cache=False), InitPlan(fields=(InitPlan.Field(name='read_roots', annotation=OpRef(name='init.field"
        "s.00.annotation'), default=OpRef(name='init.fields.00.default'), default_factory=None, init=True, override=Fal"
        "se, field_type=FieldType.INSTANCE, coerce=OpRef(name='init.fields.00.coerce'), validate=None, check_type=None)"
        ", InitPlan.Field(name='write_roots', annotation=OpRef(name='init.fields.01.annotation'), default=OpRef(name='i"
        "nit.fields.01.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerc"
        "e=OpRef(name='init.fields.01.coerce'), validate=None, check_type=None), InitPlan.Field(name='system_read_roots"
        "', annotation=OpRef(name='init.fields.02.annotation'), default=OpRef(name='init.fields.02.default'), default_f"
        "actory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=OpRef(name='init.fields.02.coerc"
        "e'), validate=None, check_type=None), InitPlan.Field(name='exec_paths', annotation=OpRef(name='init.fields.03."
        "annotation'), default=OpRef(name='init.fields.03.default'), default_factory=None, init=True, override=False, f"
        "ield_type=FieldType.INSTANCE, coerce=OpRef(name='init.fields.03.coerce'), validate=None, check_type=None), Ini"
        "tPlan.Field(name='allow_fork', annotation=OpRef(name='init.fields.04.annotation'), default=OpRef(name='init.fi"
        "elds.04.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None"
        ", validate=None, check_type=None), InitPlan.Field(name='mach_lookup', annotation=OpRef(name='init.fields.05.an"
        "notation'), default=OpRef(name='init.fields.05.default'), default_factory=None, init=True, override=False, fie"
        "ld_type=FieldType.INSTANCE, coerce=OpRef(name='init.fields.05.coerce'), validate=None, check_type=None), InitP"
        "lan.Field(name='sysctl_names', annotation=OpRef(name='init.fields.06.annotation'), default=OpRef(name='init.fi"
        "elds.06.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=OpRe"
        "f(name='init.fields.06.coerce'), validate=None, check_type=None), InitPlan.Field(name='allow_network', annotat"
        "ion=OpRef(name='init.fields.07.annotation'), default=OpRef(name='init.fields.07.default'), default_factory=Non"
        "e, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), Ini"
        "tPlan.Field(name='dev', annotation=OpRef(name='init.fields.08.annotation'), default=OpRef(name='init.fields.08"
        ".default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, valid"
        "ate=None, check_type=None), InitPlan.Field(name='allow_proc', annotation=OpRef(name='init.fields.09.annotation"
        "'), default=OpRef(name='init.fields.09.default'), default_factory=None, init=True, override=False, field_type="
        "FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='private_tmp', annotatio"
        "n=OpRef(name='init.fields.10.annotation'), default=OpRef(name='init.fields.10.default'), default_factory=None,"
        " init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self"
        "_param='self', std_params=(), kw_only_params=('read_roots', 'write_roots', 'system_read_roots', 'exec_paths', "
        "'allow_fork', 'mach_lookup', 'sysctl_names', 'allow_network', 'dev', 'allow_proc', 'private_tmp'), frozen=True"
        ", slots=False, post_init_params=(), init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='read_"
        "roots', kw_only=True, fn=None), ReprPlan.Field(name='write_roots', kw_only=True, fn=None), ReprPlan.Field(name"
        "='system_read_roots', kw_only=True, fn=None), ReprPlan.Field(name='exec_paths', kw_only=True, fn=None), ReprPl"
        "an.Field(name='allow_fork', kw_only=True, fn=None), ReprPlan.Field(name='mach_lookup', kw_only=True, fn=None),"
        " ReprPlan.Field(name='sysctl_names', kw_only=True, fn=None), ReprPlan.Field(name='allow_network', kw_only=True"
        ", fn=None), ReprPlan.Field(name='dev', kw_only=True, fn=None), ReprPlan.Field(name='allow_proc', kw_only=True,"
        " fn=None), ReprPlan.Field(name='private_tmp', kw_only=True, fn=None)), id=False, terse=False, default_fn=OpRef"
        "(name='repr.default_fn'))))"
    ),
    plan_repr_sha1='51c4f658a1a04e8aaf46a6a0f4cb659684c3a8bb',
    cls_names=(
        ('omllm.core.processes.sandbox.policy', 'SandboxPolicy'),
    ),
)
def _process_dataclass__51c4f658a1a04e8aaf46a6a0f4cb659684c3a8bb():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__00__annotation,
        __dataclass__init__fields__00__coerce,
        __dataclass__init__fields__00__default,
        __dataclass__init__fields__01__annotation,
        __dataclass__init__fields__01__coerce,
        __dataclass__init__fields__01__default,
        __dataclass__init__fields__02__annotation,
        __dataclass__init__fields__02__coerce,
        __dataclass__init__fields__02__default,
        __dataclass__init__fields__03__annotation,
        __dataclass__init__fields__03__coerce,
        __dataclass__init__fields__03__default,
        __dataclass__init__fields__04__annotation,
        __dataclass__init__fields__04__default,
        __dataclass__init__fields__05__annotation,
        __dataclass__init__fields__05__coerce,
        __dataclass__init__fields__05__default,
        __dataclass__init__fields__06__annotation,
        __dataclass__init__fields__06__coerce,
        __dataclass__init__fields__06__default,
        __dataclass__init__fields__07__annotation,
        __dataclass__init__fields__07__default,
        __dataclass__init__fields__08__annotation,
        __dataclass__init__fields__08__default,
        __dataclass__init__fields__09__annotation,
        __dataclass__init__fields__09__default,
        __dataclass__init__fields__10__annotation,
        __dataclass__init__fields__10__default,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('profile', 'params')), EqPlan(fields=('profile', 'params')), FrozenPlan(fields=('p"
        "rofile', 'params'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('profile', 'params'), ca"
        "che=False), InitPlan(fields=(InitPlan.Field(name='profile', annotation=OpRef(name='init.fields.0.annotation'),"
        " default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, va"
        "lidate=None, check_type=None), InitPlan.Field(name='params', annotation=OpRef(name='init.fields.1.annotation')"
        ", default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, v"
        "alidate=None, check_type=None)), self_param='self', std_params=(), kw_only_params=('profile', 'params'), froze"
        "n=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(nam"
        "e='profile', kw_only=True, fn=None), ReprPlan.Field(name='params', kw_only=True, fn=None)), id=False, terse=Fa"
        "lse, default_fn=None)))"
    ),
    plan_repr_sha1='b552a2229a072b3978f2076ad20c792806d037c3',
    cls_names=(
        ('omllm.core.processes.sandbox.seatbelt', 'SeatbeltProfile'),
    ),
)
def _process_dataclass__b552a2229a072b3978f2076ad20c792806d037c3():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('policy', 'sandbox_exec')), EqPlan(fields=('policy', 'sandbox_exec')), FrozenPlan("
        "fields=('policy', 'sandbox_exec'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('policy',"
        " 'sandbox_exec'), cache=False), InitPlan(fields=(InitPlan.Field(name='policy', annotation=OpRef(name='init.fie"
        "lds.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTAN"
        "CE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='sandbox_exec', annotation=OpRef(name='i"
        "nit.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, overr"
        "ide=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', st"
        "d_params=(), kw_only_params=('policy', 'sandbox_exec'), frozen=True, slots=False, post_init_params=None, init_"
        "fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='policy', kw_only=True, fn=None), ReprPlan.Fiel"
        "d(name='sandbox_exec', kw_only=True, fn=None)), id=False, terse=False, default_fn=OpRef(name='repr.default_fn'"
        "))))"
    ),
    plan_repr_sha1='9a5f5c90daad24f9b293093f3d6e1575328b393c',
    cls_names=(
        ('omllm.core.processes.sandbox.seatbelt', 'SeatbeltSandbox'),
    ),
)
def _process_dataclass__9a5f5c90daad24f9b293093f3d6e1575328b393c():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('s',)), EqPlan(fields=('s',)), FrozenPlan(fields=('s',), allow_dynamic_dunder_attr"
        "s=False), HashPlan(action='add', fields=('s',), cache=False), InitPlan(fields=(InitPlan.Field(name='s', annota"
        "tion=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, fi"
        "eld_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='self', std_params=('s"
        "',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPl"
        "an(fields=(ReprPlan.Field(name='s', kw_only=False, fn=None),), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='30a5dd74853303d917aae5f67d4e7189615d1440',
    cls_names=(
        ('omllm.core.processes.sandbox.seatbelt', '_SxQuote'),
    ),
)
def _process_dataclass__30a5dd74853303d917aae5f67d4e7189615d1440():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('overall_timeout_s',)), EqPlan(fields=('overall_timeout_s',)), FrozenPlan(fields=("
        "'overall_timeout_s',), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('overall_timeout_s',)"
        ", cache=False), InitPlan(fields=(InitPlan.Field(name='overall_timeout_s', annotation=OpRef(name='init.fields.0"
        ".annotation'), default=OpRef(name='init.fields.0.default'), default_factory=None, init=True, override=False, f"
        "ield_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='self', std_params=()"
        ", kw_only_params=('overall_timeout_s',), frozen=True, slots=False, post_init_params=(), init_fns=(), validate_"
        "fns=()), ReprPlan(fields=(ReprPlan.Field(name='overall_timeout_s', kw_only=True, fn=None),), id=False, terse=F"
        "alse, default_fn=None)))"
    ),
    plan_repr_sha1='f36479c5e2b9f4d715b9dcbbe68751ec7070fb0e',
    cls_names=(
        ('omllm.core.processes.scopes.policies', 'ScopeClosePolicy'),
    ),
)
def _process_dataclass__f36479c5e2b9f4d715b9dcbbe68751ec7070fb0e():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__default,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('process', 'returncode', 'output')), EqPlan(fields=('process', 'returncode', 'outp"
        "ut')), FrozenPlan(fields=('process', 'returncode', 'output'), allow_dynamic_dunder_attrs=False), HashPlan(acti"
        "on='add', fields=('process', 'returncode', 'output'), cache=False), InitPlan(fields=(InitPlan.Field(name='proc"
        "ess', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, overri"
        "de=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='re"
        "turncode', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, o"
        "verride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(nam"
        "e='output', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, "
        "override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self"
        "', std_params=(), kw_only_params=('process', 'returncode', 'output'), frozen=True, slots=False, post_init_para"
        "ms=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='process', kw_only=True, fn=None)"
        ", ReprPlan.Field(name='returncode', kw_only=True, fn=None), ReprPlan.Field(name='output', kw_only=True, fn=Non"
        "e)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='1927cd9f3e6b6c79a323684d39eac3003d4d6696',
    cls_names=(
        ('omllm.core.processes.scopes.scope', 'ProcessRun'),
    ),
)
def _process_dataclass__1927cd9f3e6b6c79a323684d39eac3003d4d6696():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('num_processes', 'num_abandoned', 'errors')), EqPlan(fields=('num_processes', 'num"
        "_abandoned', 'errors')), FrozenPlan(fields=('num_processes', 'num_abandoned', 'errors'), allow_dynamic_dunder_"
        "attrs=False), HashPlan(action='add', fields=('num_processes', 'num_abandoned', 'errors'), cache=False), InitPl"
        "an(fields=(InitPlan.Field(name='num_processes', annotation=OpRef(name='init.fields.0.annotation'), default=Non"
        "e, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None,"
        " check_type=None), InitPlan.Field(name='num_abandoned', annotation=OpRef(name='init.fields.1.annotation'), def"
        "ault=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False, field_type=FieldTyp"
        "e.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='errors', annotation=OpRef(name="
        "'init.fields.2.annotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, ove"
        "rride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', "
        "std_params=(), kw_only_params=('num_processes', 'num_abandoned', 'errors'), frozen=True, slots=False, post_ini"
        "t_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='num_processes', kw_only=Tr"
        "ue, fn=None), ReprPlan.Field(name='num_abandoned', kw_only=True, fn=None), ReprPlan.Field(name='errors', kw_on"
        "ly=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='59fe7fd0579fcc265615ade7ef49e8ef948b8f4e',
    cls_names=(
        ('omllm.core.processes.scopes.scope', 'ScopeCloseResult'),
    ),
)
def _process_dataclass__59fe7fd0579fcc265615ade7ef49e8ef948b8f4e():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('fd', 'data', 't_mono_ns', 't_wall_ns', 'seq', 'offset')), EqPlan(fields=('fd', 'd"
        "ata', 't_mono_ns', 't_wall_ns', 'seq', 'offset')), FrozenPlan(fields=('fd', 'data', 't_mono_ns', 't_wall_ns', "
        "'seq', 'offset'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('fd', 'data', 't_mono_ns',"
        " 't_wall_ns', 'seq', 'offset'), cache=True), InitPlan(fields=(InitPlan.Field(name='fd', annotation=OpRef(name="
        "'init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldTy"
        "pe.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='data', annotation=OpRef(name='"
        "init.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldTyp"
        "e.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='t_mono_ns', annotation=OpRef(na"
        "me='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=False, field_type=Fiel"
        "dType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='t_wall_ns', annotation=OpRe"
        "f(name='init.fields.3.annotation'), default=None, default_factory=None, init=True, override=False, field_type="
        "FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='seq', annotation=OpRef("
        "name='init.fields.4.annotation'), default=None, default_factory=None, init=True, override=False, field_type=Fi"
        "eldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='offset', annotation=OpRef"
        "(name='init.fields.5.annotation'), default=None, default_factory=None, init=True, override=False, field_type=F"
        "ieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('fd', 'data')"
        ", kw_only_params=('t_mono_ns', 't_wall_ns', 'seq', 'offset'), frozen=True, slots=False, post_init_params=None,"
        " init_fns=(), validate_fns=())))"
    ),
    plan_repr_sha1='7f4f5d57e2cbbbad5742004412d1b3ac0b8ac4ca',
    cls_names=(
        ('omllm.core.processes.spool.frames', 'SpoolRecord'),
    ),
)
def _process_dataclass__7f4f5d57e2cbbbad5742004412d1b3ac0b8ac4ca():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__4__annotation,
        __dataclass__init__fields__5__annotation,
        __dataclass__FrozenInstanceError=dataclasses.FrozenInstanceError,  # noqa
        __dataclass__None=None,  # noqa
        __dataclass__object_setattr=object.__setattr__,  # noqa
        __dataclass__set_cls_attr,
    ):
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('records', 'start', 'end', 'total', 'dropped_before', 'ended')), EqPlan(fields=('r"
        "ecords', 'start', 'end', 'total', 'dropped_before', 'ended')), FrozenPlan(fields=('records', 'start', 'end', '"
        "total', 'dropped_before', 'ended'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('records"
        "', 'start', 'end', 'total', 'dropped_before', 'ended'), cache=False), InitPlan(fields=(InitPlan.Field(name='re"
        "cords', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, over"
        "ride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='"
        "start', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, over"
        "ride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='"
        "end', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, overri"
        "de=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='to"
        "tal', annotation=OpRef(name='init.fields.3.annotation'), default=None, default_factory=None, init=True, overri"
        "de=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='dr"
        "opped_before', annotation=OpRef(name='init.fields.4.annotation'), default=OpRef(name='init.fields.4.default'),"
        " default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, c"
        "heck_type=None), InitPlan.Field(name='ended', annotation=OpRef(name='init.fields.5.annotation'), default=OpRef"
        "(name='init.fields.5.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE"
        ", coerce=None, validate=None, check_type=None)), self_param='self', std_params=(), kw_only_params=('records', "
        "'start', 'end', 'total', 'dropped_before', 'ended'), frozen=True, slots=False, post_init_params=None, init_fns"
        "=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='records', kw_only=True, fn=None), ReprPlan.Field("
        "name='start', kw_only=True, fn=None), ReprPlan.Field(name='end', kw_only=True, fn=None), ReprPlan.Field(name='"
        "total', kw_only=True, fn=None), ReprPlan.Field(name='dropped_before', kw_only=True, fn=None), ReprPlan.Field(n"
        "ame='ended', kw_only=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='014259256148ffa689d1e6af6f24270167250212',
    cls_names=(
        ('omllm.core.processes.spool.spool', 'SpoolRead'),
    ),
)
def _process_dataclass__014259256148ffa689d1e6af6f24270167250212():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('container', 'user', 'extra_flags', 'docker')), EqPlan(fields=('container', 'user'"
        ", 'extra_flags', 'docker')), FrozenPlan(fields=('container', 'user', 'extra_flags', 'docker'), allow_dynamic_d"
        "under_attrs=False), HashPlan(action='add', fields=('container', 'user', 'extra_flags', 'docker'), cache=False)"
        ", InitPlan(fields=(InitPlan.Field(name='container', annotation=OpRef(name='init.fields.0.annotation'), default"
        "=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=OpRef(name='init"
        ".fields.0.coerce'), validate=None, check_type=None), InitPlan.Field(name='user', annotation=OpRef(name='init.f"
        "ields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=F"
        "alse, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='extra_"
        "flags', annotation=OpRef(name='init.fields.2.annotation'), default=OpRef(name='init.fields.2.default'), defaul"
        "t_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_ty"
        "pe=None), InitPlan.Field(name='docker', annotation=OpRef(name='init.fields.3.annotation'), default=OpRef(name="
        "'init.fields.3.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coer"
        "ce=None, validate=None, check_type=None)), self_param='self', std_params=(), kw_only_params=('container', 'use"
        "r', 'extra_flags', 'docker'), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), "
        "ReprPlan(fields=(ReprPlan.Field(name='container', kw_only=True, fn=None), ReprPlan.Field(name='user', kw_only="
        "True, fn=None), ReprPlan.Field(name='extra_flags', kw_only=True, fn=None), ReprPlan.Field(name='docker', kw_on"
        "ly=True, fn=None)), id=False, terse=False, default_fn=OpRef(name='repr.default_fn'))))"
    ),
    plan_repr_sha1='bb15c23275aaa6b4e82483ce7a8c6e10924b283b',
    cls_names=(
        ('omllm.core.processes.targets.docker', 'DockerExecTarget'),
    ),
)
def _process_dataclass__bb15c23275aaa6b4e82483ce7a8c6e10924b283b():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('host', 'user', 'port', 'identity_file', 'control_path', 'control_persist', 'no_ho"
        "st_key_checking', 'extra_options', 'ssh')), EqPlan(fields=('host', 'user', 'port', 'identity_file', 'control_p"
        "ath', 'control_persist', 'no_host_key_checking', 'extra_options', 'ssh')), FrozenPlan(fields=('host', 'user', "
        "'port', 'identity_file', 'control_path', 'control_persist', 'no_host_key_checking', 'extra_options', 'ssh'), a"
        "llow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('host', 'user', 'port', 'identity_file', 'con"
        "trol_path', 'control_persist', 'no_host_key_checking', 'extra_options', 'ssh'), cache=False), InitPlan(fields="
        "(InitPlan.Field(name='host', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory="
        "None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=OpRef(name='init.fields.0.coerce'), val"
        "idate=None, check_type=None), InitPlan.Field(name='user', annotation=OpRef(name='init.fields.1.annotation'), d"
        "efault=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False, field_type=FieldT"
        "ype.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='port', annotation=OpRef(name="
        "'init.fields.2.annotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, ove"
        "rride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name="
        "'identity_file', annotation=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default'"
        "), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None,"
        " check_type=None), InitPlan.Field(name='control_path', annotation=OpRef(name='init.fields.4.annotation'), defa"
        "ult=OpRef(name='init.fields.4.default'), default_factory=None, init=True, override=False, field_type=FieldType"
        ".INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='control_persist', annotation=OpR"
        "ef(name='init.fields.5.annotation'), default=OpRef(name='init.fields.5.default'), default_factory=None, init=T"
        "rue, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Fie"
        "ld(name='no_host_key_checking', annotation=OpRef(name='init.fields.6.annotation'), default=OpRef(name='init.fi"
        "elds.6.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None,"
        " validate=None, check_type=None), InitPlan.Field(name='extra_options', annotation=OpRef(name='init.fields.7.an"
        "notation'), default=OpRef(name='init.fields.7.default'), default_factory=None, init=True, override=False, fiel"
        "d_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='ssh', annotation"
        "=OpRef(name='init.fields.8.annotation'), default=OpRef(name='init.fields.8.default'), default_factory=None, in"
        "it=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_pa"
        "ram='self', std_params=(), kw_only_params=('host', 'user', 'port', 'identity_file', 'control_path', 'control_p"
        "ersist', 'no_host_key_checking', 'extra_options', 'ssh'), frozen=True, slots=False, post_init_params=None, ini"
        "t_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='host', kw_only=True, fn=None), ReprPlan.Fiel"
        "d(name='user', kw_only=True, fn=None), ReprPlan.Field(name='port', kw_only=True, fn=None), ReprPlan.Field(name"
        "='identity_file', kw_only=True, fn=None), ReprPlan.Field(name='control_path', kw_only=True, fn=None), ReprPlan"
        ".Field(name='control_persist', kw_only=True, fn=None), ReprPlan.Field(name='no_host_key_checking', kw_only=Tru"
        "e, fn=None), ReprPlan.Field(name='extra_options', kw_only=True, fn=None), ReprPlan.Field(name='ssh', kw_only=T"
        "rue, fn=None)), id=False, terse=False, default_fn=OpRef(name='repr.default_fn'))))"
    ),
    plan_repr_sha1='ecf30ed9a10c30376827f71a44ea23d04e81ebac',
    cls_names=(
        ('omllm.core.processes.targets.ssh', 'SshTarget'),
    ),
)
def _process_dataclass__ecf30ed9a10c30376827f71a44ea23d04e81ebac():
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
        __dataclass__init__fields__6__annotation,
        __dataclass__init__fields__6__default,
        __dataclass__init__fields__7__annotation,
        __dataclass__init__fields__7__default,
        __dataclass__init__fields__8__annotation,
        __dataclass__init__fields__8__default,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('stage', 'errno', 'message', 'argv')), EqPlan(fields=('stage', 'errno', 'message',"
        " 'argv')), HashPlan(action='set_none', fields=None, cache=None), InitPlan(fields=(InitPlan.Field(name='stage',"
        " annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=Fa"
        "lse, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='errno',"
        " annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override=Fa"
        "lse, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='message"
        "', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override="
        "False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='argv'"
        ", annotation=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default'), default_fact"
        "ory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=Non"
        "e)), self_param='self', std_params=('stage', 'errno', 'message', 'argv'), kw_only_params=(), frozen=False, slo"
        "ts=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='stage', "
        "kw_only=False, fn=None), ReprPlan.Field(name='errno', kw_only=False, fn=None), ReprPlan.Field(name='message', "
        "kw_only=False, fn=None), ReprPlan.Field(name='argv', kw_only=False, fn=None)), id=False, terse=False, default_"
        "fn=None)))"
    ),
    plan_repr_sha1='6bd870c188b5ac0bd1d834e685c284c262cd1eb2',
    cls_names=(
        ('omllm.core.processes.types.errors', 'SpawnError'),
    ),
)
def _process_dataclass__6bd870c188b5ac0bd1d834e685c284c262cd1eb2():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__3__default,
        __dataclass__None=None,  # noqa
        __dataclass___recursive_repr=reprlib.recursive_repr,  # noqa
        __dataclass__set_cls_attr,
    ):
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('process_id', 'pid', 'scope_path', 'state')), EqPlan(fields=('process_id', 'pid', "
        "'scope_path', 'state')), FrozenPlan(fields=('process_id', 'pid', 'scope_path', 'state'), allow_dynamic_dunder_"
        "attrs=False), HashPlan(action='add', fields=('process_id', 'pid', 'scope_path', 'state'), cache=False), InitPl"
        "an(fields=(InitPlan.Field(name='process_id', annotation=OpRef(name='init.fields.0.annotation'), default=None, "
        "default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, ch"
        "eck_type=None), InitPlan.Field(name='pid', annotation=OpRef(name='init.fields.1.annotation'), default=None, de"
        "fault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, chec"
        "k_type=None), InitPlan.Field(name='scope_path', annotation=OpRef(name='init.fields.2.annotation'), default=Non"
        "e, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None,"
        " check_type=None), InitPlan.Field(name='state', annotation=OpRef(name='init.fields.3.annotation'), default=Non"
        "e, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None,"
        " check_type=None)), self_param='self', std_params=(), kw_only_params=('process_id', 'pid', 'scope_path', 'stat"
        "e'), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan"
        ".Field(name='process_id', kw_only=True, fn=None), ReprPlan.Field(name='pid', kw_only=True, fn=None), ReprPlan."
        "Field(name='scope_path', kw_only=True, fn=None), ReprPlan.Field(name='state', kw_only=True, fn=None)), id=Fals"
        "e, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='b142ac80b580a067d4667bafd436680004d70a13',
    cls_names=(
        ('omllm.core.processes.types.events', 'ProcessAbandonedEvent'),
    ),
)
def _process_dataclass__b142ac80b580a067d4667bafd436680004d70a13():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=()), EqPlan(fields=()), FrozenPlan(fields=(), allow_dynamic_dunder_attrs=False), Ha"
        "shPlan(action='add', fields=(), cache=False), InitPlan(fields=(), self_param='self', std_params=(), kw_only_pa"
        "rams=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(), i"
        "d=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='e1f7edfe11f2b721d6a656c46e698fedc95461bb',
    cls_names=(
        ('omllm.core.processes.types.events', 'ProcessEvent'),
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
        "Plans(tup=(CopyPlan(fields=('process_id', 'pid', 'scope_path', 'returncode')), EqPlan(fields=('process_id', 'p"
        "id', 'scope_path', 'returncode')), FrozenPlan(fields=('process_id', 'pid', 'scope_path', 'returncode'), allow_"
        "dynamic_dunder_attrs=False), HashPlan(action='add', fields=('process_id', 'pid', 'scope_path', 'returncode'), "
        "cache=False), InitPlan(fields=(InitPlan.Field(name='process_id', annotation=OpRef(name='init.fields.0.annotati"
        "on'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=Non"
        "e, validate=None, check_type=None), InitPlan.Field(name='pid', annotation=OpRef(name='init.fields.1.annotation"
        "'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None,"
        " validate=None, check_type=None), InitPlan.Field(name='scope_path', annotation=OpRef(name='init.fields.2.annot"
        "ation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce="
        "None, validate=None, check_type=None), InitPlan.Field(name='returncode', annotation=OpRef(name='init.fields.3."
        "annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, co"
        "erce=None, validate=None, check_type=None)), self_param='self', std_params=(), kw_only_params=('process_id', '"
        "pid', 'scope_path', 'returncode'), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns="
        "()), ReprPlan(fields=(ReprPlan.Field(name='process_id', kw_only=True, fn=None), ReprPlan.Field(name='pid', kw_"
        "only=True, fn=None), ReprPlan.Field(name='scope_path', kw_only=True, fn=None), ReprPlan.Field(name='returncode"
        "', kw_only=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='5409f904bee0df22eece1a4568e4244dbb6f65d3',
    cls_names=(
        ('omllm.core.processes.types.events', 'ProcessExitedEvent'),
        ('omllm.core.processes.types.events', 'ProcessReapedEvent'),
    ),
)
def _process_dataclass__5409f904bee0df22eece1a4568e4244dbb6f65d3():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('process_id', 'pid', 'scope_path')), EqPlan(fields=('process_id', 'pid', 'scope_pa"
        "th')), FrozenPlan(fields=('process_id', 'pid', 'scope_path'), allow_dynamic_dunder_attrs=False), HashPlan(acti"
        "on='add', fields=('process_id', 'pid', 'scope_path'), cache=False), InitPlan(fields=(InitPlan.Field(name='proc"
        "ess_id', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, ove"
        "rride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name="
        "'pid', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, overr"
        "ide=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='s"
        "cope_path', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, "
        "override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self"
        "', std_params=(), kw_only_params=('process_id', 'pid', 'scope_path'), frozen=True, slots=False, post_init_para"
        "ms=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='process_id', kw_only=True, fn=No"
        "ne), ReprPlan.Field(name='pid', kw_only=True, fn=None), ReprPlan.Field(name='scope_path', kw_only=True, fn=Non"
        "e)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='e093c157cc0fc076230b50b62b78c9dbc7860db0',
    cls_names=(
        ('omllm.core.processes.types.events', 'ProcessLifecycleEvent'),
    ),
)
def _process_dataclass__e093c157cc0fc076230b50b62b78c9dbc7860db0():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('process_id', 'pid', 'scope_path', 'reason')), EqPlan(fields=('process_id', 'pid',"
        " 'scope_path', 'reason')), FrozenPlan(fields=('process_id', 'pid', 'scope_path', 'reason'), allow_dynamic_dund"
        "er_attrs=False), HashPlan(action='add', fields=('process_id', 'pid', 'scope_path', 'reason'), cache=False), In"
        "itPlan(fields=(InitPlan.Field(name='process_id', annotation=OpRef(name='init.fields.0.annotation'), default=No"
        "ne, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None"
        ", check_type=None), InitPlan.Field(name='pid', annotation=OpRef(name='init.fields.1.annotation'), default=None"
        ", default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, "
        "check_type=None), InitPlan.Field(name='scope_path', annotation=OpRef(name='init.fields.2.annotation'), default"
        "=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=N"
        "one, check_type=None), InitPlan.Field(name='reason', annotation=OpRef(name='init.fields.3.annotation'), defaul"
        "t=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate="
        "None, check_type=None)), self_param='self', std_params=(), kw_only_params=('process_id', 'pid', 'scope_path', "
        "'reason'), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(Re"
        "prPlan.Field(name='process_id', kw_only=True, fn=None), ReprPlan.Field(name='pid', kw_only=True, fn=None), Rep"
        "rPlan.Field(name='scope_path', kw_only=True, fn=None), ReprPlan.Field(name='reason', kw_only=True, fn=None)), "
        "id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='f82e4121ad9e1de13cd57f99c31eafe003feb3c7',
    cls_names=(
        ('omllm.core.processes.types.events', 'ProcessPoisonedEvent'),
    ),
)
def _process_dataclass__f82e4121ad9e1de13cd57f99c31eafe003feb3c7():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('process_id', 'pid', 'scope_path', 'old_scope_path')), EqPlan(fields=('process_id'"
        ", 'pid', 'scope_path', 'old_scope_path')), FrozenPlan(fields=('process_id', 'pid', 'scope_path', 'old_scope_pa"
        "th'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('process_id', 'pid', 'scope_path', 'ol"
        "d_scope_path'), cache=False), InitPlan(fields=(InitPlan.Field(name='process_id', annotation=OpRef(name='init.f"
        "ields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INST"
        "ANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='pid', annotation=OpRef(name='init.fie"
        "lds.1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTAN"
        "CE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='scope_path', annotation=OpRef(name='ini"
        "t.fields.2.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.I"
        "NSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='old_scope_path', annotation=OpRef("
        "name='init.fields.3.annotation'), default=None, default_factory=None, init=True, override=False, field_type=Fi"
        "eldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=(), kw_only_par"
        "ams=('process_id', 'pid', 'scope_path', 'old_scope_path'), frozen=True, slots=False, post_init_params=None, in"
        "it_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='process_id', kw_only=True, fn=None), ReprPl"
        "an.Field(name='pid', kw_only=True, fn=None), ReprPlan.Field(name='scope_path', kw_only=True, fn=None), ReprPla"
        "n.Field(name='old_scope_path', kw_only=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='4f6217c4a9ba13eff1c63fa7edca4a70c15c6e81',
    cls_names=(
        ('omllm.core.processes.types.events', 'ProcessReparentedEvent'),
    ),
)
def _process_dataclass__4f6217c4a9ba13eff1c63fa7edca4a70c15c6e81():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('process_id', 'pid', 'scope_path', 'argv', 'name')), EqPlan(fields=('process_id', "
        "'pid', 'scope_path', 'argv', 'name')), FrozenPlan(fields=('process_id', 'pid', 'scope_path', 'argv', 'name'), "
        "allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('process_id', 'pid', 'scope_path', 'argv', '"
        "name'), cache=False), InitPlan(fields=(InitPlan.Field(name='process_id', annotation=OpRef(name='init.fields.0."
        "annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, co"
        "erce=None, validate=None, check_type=None), InitPlan.Field(name='pid', annotation=OpRef(name='init.fields.1.an"
        "notation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coer"
        "ce=None, validate=None, check_type=None), InitPlan.Field(name='scope_path', annotation=OpRef(name='init.fields"
        ".2.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE,"
        " coerce=None, validate=None, check_type=None), InitPlan.Field(name='argv', annotation=OpRef(name='init.fields."
        "3.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, "
        "coerce=None, validate=None, check_type=None), InitPlan.Field(name='name', annotation=OpRef(name='init.fields.4"
        ".annotation'), default=OpRef(name='init.fields.4.default'), default_factory=None, init=True, override=False, f"
        "ield_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=(),"
        " kw_only_params=('process_id', 'pid', 'scope_path', 'argv', 'name'), frozen=True, slots=False, post_init_param"
        "s=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='process_id', kw_only=True, fn=Non"
        "e), ReprPlan.Field(name='pid', kw_only=True, fn=None), ReprPlan.Field(name='scope_path', kw_only=True, fn=None"
        "), ReprPlan.Field(name='argv', kw_only=True, fn=None), ReprPlan.Field(name='name', kw_only=True, fn=None)), id"
        "=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='56c1e9adf90660305d8c05948098412ad28aadd9',
    cls_names=(
        ('omllm.core.processes.types.events', 'ProcessSpawnedEvent'),
    ),
)
def _process_dataclass__56c1e9adf90660305d8c05948098412ad28aadd9():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__4__annotation,
        __dataclass__init__fields__4__default,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('scope_path', 'num_processes', 'num_abandoned')), EqPlan(fields=('scope_path', 'nu"
        "m_processes', 'num_abandoned')), FrozenPlan(fields=('scope_path', 'num_processes', 'num_abandoned'), allow_dyn"
        "amic_dunder_attrs=False), HashPlan(action='add', fields=('scope_path', 'num_processes', 'num_abandoned'), cach"
        "e=False), InitPlan(fields=(InitPlan.Field(name='scope_path', annotation=OpRef(name='init.fields.0.annotation')"
        ", default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, v"
        "alidate=None, check_type=None), InitPlan.Field(name='num_processes', annotation=OpRef(name='init.fields.1.anno"
        "tation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce"
        "=None, validate=None, check_type=None), InitPlan.Field(name='num_abandoned', annotation=OpRef(name='init.field"
        "s.2.annotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, override=False"
        ", field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params="
        "(), kw_only_params=('scope_path', 'num_processes', 'num_abandoned'), frozen=True, slots=False, post_init_param"
        "s=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='scope_path', kw_only=True, fn=Non"
        "e), ReprPlan.Field(name='num_processes', kw_only=True, fn=None), ReprPlan.Field(name='num_abandoned', kw_only="
        "True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='8d943650426f34712c448e0a77b8e2dba1f246fd',
    cls_names=(
        ('omllm.core.processes.types.events', 'ScopeClosedEvent'),
    ),
)
def _process_dataclass__8d943650426f34712c448e0a77b8e2dba1f246fd():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('scope_path',)), EqPlan(fields=('scope_path',)), FrozenPlan(fields=('scope_path',)"
        ", allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('scope_path',), cache=False), InitPlan(fie"
        "lds=(InitPlan.Field(name='scope_path', annotation=OpRef(name='init.fields.0.annotation'), default=None, defaul"
        "t_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_ty"
        "pe=None),), self_param='self', std_params=(), kw_only_params=('scope_path',), frozen=True, slots=False, post_i"
        "nit_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='scope_path', kw_only=Tru"
        "e, fn=None),), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='524a82161f342e6602cfacfede4ac8fd91b42a86',
    cls_names=(
        ('omllm.core.processes.types.events', 'ScopeEvent'),
        ('omllm.core.processes.types.events', 'ScopeOpenedEvent'),
    ),
)
def _process_dataclass__524a82161f342e6602cfacfede4ac8fd91b42a86():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('user', 'group', 'extra_groups')), EqPlan(fields=('user', 'group', 'extra_groups')"
        "), FrozenPlan(fields=('user', 'group', 'extra_groups'), allow_dynamic_dunder_attrs=False), HashPlan(action='ad"
        "d', fields=('user', 'group', 'extra_groups'), cache=False), InitPlan(fields=(InitPlan.Field(name='user', annot"
        "ation=OpRef(name='init.fields.0.annotation'), default=OpRef(name='init.fields.0.default'), default_factory=Non"
        "e, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), Ini"
        "tPlan.Field(name='group', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1"
        ".default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, valid"
        "ate=None, check_type=None), InitPlan.Field(name='extra_groups', annotation=OpRef(name='init.fields.2.annotatio"
        "n'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, override=False, field_type="
        "FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=(), kw_only_p"
        "arams=('user', 'group', 'extra_groups'), frozen=True, slots=False, post_init_params=None, init_fns=(), validat"
        "e_fns=()), ReprPlan(fields=(ReprPlan.Field(name='user', kw_only=True, fn=None), ReprPlan.Field(name='group', k"
        "w_only=True, fn=None), ReprPlan.Field(name='extra_groups', kw_only=True, fn=None)), id=False, terse=False, def"
        "ault_fn=None)))"
    ),
    plan_repr_sha1='bcf55b44da72046dade7386e11cc800cb84805d6',
    cls_names=(
        ('omllm.core.processes.types.options', 'Credentials'),
    ),
)
def _process_dataclass__bcf55b44da72046dade7386e11cc800cb84805d6():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__default,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('signal',)), EqPlan(fields=('signal',)), FrozenPlan(fields=('signal',), allow_dyna"
        "mic_dunder_attrs=False), HashPlan(action='add', fields=('signal',), cache=False), InitPlan(fields=(InitPlan.Fi"
        "eld(name='signal', annotation=OpRef(name='init.fields.0.annotation'), default=OpRef(name='init.fields.0.defaul"
        "t'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=Non"
        "e, check_type=None),), self_param='self', std_params=(), kw_only_params=('signal',), frozen=True, slots=False,"
        " post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='signal', kw_only="
        "True, fn=None),), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='fb1225c02c13f5ee8445c1f2782cadb0546ce21e',
    cls_names=(
        ('omllm.core.processes.types.options', 'Deathsig'),
    ),
)
def _process_dataclass__fb1225c02c13f5ee8445c1f2782cadb0546ce21e():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__default,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('v',)), EqPlan(fields=('v',)), FrozenPlan(fields=('v',), allow_dynamic_dunder_attr"
        "s=False), HashPlan(action='add', fields=('v',), cache=False), InitPlan(fields=(InitPlan.Field(name='v', annota"
        "tion=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, fi"
        "eld_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='self', std_params=('v"
        "',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPl"
        "an(fields=(ReprPlan.Field(name='v', kw_only=False, fn=None),), id=False, terse=True, default_fn=None)))"
    ),
    plan_repr_sha1='3576262424b3ef8ff20966fa3744e5dba9a2ae7d',
    cls_names=(
        ('omllm.core.processes.types.options', 'PassFd'),
        ('omllm.core.processes.types.options', 'RunTimeout'),
        ('omllm.core.processes.types.options', 'Tag'),
        ('omllm.core.processes.types.options', 'Umask'),
    ),
)
def _process_dataclass__3576262424b3ef8ff20966fa3744e5dba9a2ae7d():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('resource', 'soft', 'hard')), EqPlan(fields=('resource', 'soft', 'hard')), FrozenP"
        "lan(fields=('resource', 'soft', 'hard'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('re"
        "source', 'soft', 'hard'), cache=False), InitPlan(fields=(InitPlan.Field(name='resource', annotation=OpRef(name"
        "='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldT"
        "ype.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='soft', annotation=OpRef(name="
        "'init.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldTy"
        "pe.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='hard', annotation=OpRef(name='"
        "init.fields.2.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldTyp"
        "e.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('resource', 'soft', "
        "'hard'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), Re"
        "prPlan(fields=(ReprPlan.Field(name='resource', kw_only=False, fn=None), ReprPlan.Field(name='soft', kw_only=Fa"
        "lse, fn=None), ReprPlan.Field(name='hard', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='bed9a923e60938e1d1a9800af51f05a3932cd149',
    cls_names=(
        ('omllm.core.processes.types.options', 'Rlimit'),
    ),
)
def _process_dataclass__bed9a923e60938e1d1a9800af51f05a3932cd149():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('mode',)), EqPlan(fields=('mode',)), FrozenPlan(fields=('mode',), allow_dynamic_du"
        "nder_attrs=False), HashPlan(action='add', fields=('mode',), cache=False), InitPlan(fields=(InitPlan.Field(name"
        "='mode', annotation=OpRef(name='init.fields.0.annotation'), default=OpRef(name='init.fields.0.default'), defau"
        "lt_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_t"
        "ype=None),), self_param='self', std_params=(), kw_only_params=('mode',), frozen=True, slots=False, post_init_p"
        "arams=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='mode', kw_only=True, fn=None)"
        ",), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='f859ffc2dfca90e93be51212a949ea05f29b9fcb',
    cls_names=(
        ('omllm.core.processes.types.options', 'SessionMode'),
    ),
)
def _process_dataclass__f859ffc2dfca90e93be51212a949ea05f29b9fcb():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__default,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('memory_cap', 'spill', 'keep_spill')), EqPlan(fields=('memory_cap', 'spill', 'keep"
        "_spill')), FrozenPlan(fields=('memory_cap', 'spill', 'keep_spill'), allow_dynamic_dunder_attrs=False), HashPla"
        "n(action='add', fields=('memory_cap', 'spill', 'keep_spill'), cache=False), InitPlan(fields=(InitPlan.Field(na"
        "me='memory_cap', annotation=OpRef(name='init.fields.0.annotation'), default=OpRef(name='init.fields.0.default'"
        "), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None,"
        " check_type=None), InitPlan.Field(name='spill', annotation=OpRef(name='init.fields.1.annotation'), default=OpR"
        "ef(name='init.fields.1.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTAN"
        "CE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='keep_spill', annotation=OpRef(name='ini"
        "t.fields.2.annotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, overrid"
        "e=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_"
        "params=(), kw_only_params=('memory_cap', 'spill', 'keep_spill'), frozen=True, slots=False, post_init_params=()"
        ", init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='memory_cap', kw_only=True, fn=None), Re"
        "prPlan.Field(name='spill', kw_only=True, fn=None), ReprPlan.Field(name='keep_spill', kw_only=True, fn=None)), "
        "id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='3e8f2806e53c97d9f43c388d53ab6bd07936070c',
    cls_names=(
        ('omllm.core.processes.types.options', 'SpoolPolicy'),
    ),
)
def _process_dataclass__3e8f2806e53c97d9f43c388d53ab6bd07936070c():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__default,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('signal', 'grace_s', 'kill_s', 'close_stdin', 'process_group', 'drain_s', 'on_stuc"
        "k')), EqPlan(fields=('signal', 'grace_s', 'kill_s', 'close_stdin', 'process_group', 'drain_s', 'on_stuck')), F"
        "rozenPlan(fields=('signal', 'grace_s', 'kill_s', 'close_stdin', 'process_group', 'drain_s', 'on_stuck'), allow"
        "_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('signal', 'grace_s', 'kill_s', 'close_stdin', 'pr"
        "ocess_group', 'drain_s', 'on_stuck'), cache=False), InitPlan(fields=(InitPlan.Field(name='signal', annotation="
        "OpRef(name='init.fields.0.annotation'), default=OpRef(name='init.fields.0.default'), default_factory=None, ini"
        "t=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan."
        "Field(name='grace_s', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.def"
        "ault'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate="
        "None, check_type=None), InitPlan.Field(name='kill_s', annotation=OpRef(name='init.fields.2.annotation'), defau"
        "lt=OpRef(name='init.fields.2.default'), default_factory=None, init=True, override=False, field_type=FieldType."
        "INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='close_stdin', annotation=OpRef(na"
        "me='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default'), default_factory=None, init=True, "
        "override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(na"
        "me='process_group', annotation=OpRef(name='init.fields.4.annotation'), default=OpRef(name='init.fields.4.defau"
        "lt'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=No"
        "ne, check_type=None), InitPlan.Field(name='drain_s', annotation=OpRef(name='init.fields.5.annotation'), defaul"
        "t=OpRef(name='init.fields.5.default'), default_factory=None, init=True, override=False, field_type=FieldType.I"
        "NSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='on_stuck', annotation=OpRef(name='"
        "init.fields.6.annotation'), default=OpRef(name='init.fields.6.default'), default_factory=None, init=True, over"
        "ride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', s"
        "td_params=(), kw_only_params=('signal', 'grace_s', 'kill_s', 'close_stdin', 'process_group', 'drain_s', 'on_st"
        "uck'), frozen=True, slots=False, post_init_params=(), init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan"
        ".Field(name='signal', kw_only=True, fn=None), ReprPlan.Field(name='grace_s', kw_only=True, fn=None), ReprPlan."
        "Field(name='kill_s', kw_only=True, fn=None), ReprPlan.Field(name='close_stdin', kw_only=True, fn=None), ReprPl"
        "an.Field(name='process_group', kw_only=True, fn=None), ReprPlan.Field(name='drain_s', kw_only=True, fn=None), "
        "ReprPlan.Field(name='on_stuck', kw_only=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='db8dac790a688cd409e8f7ca1e590d14cd2551f4',
    cls_names=(
        ('omllm.core.processes.types.options', 'TerminationPolicy'),
    ),
)
def _process_dataclass__db8dac790a688cd409e8f7ca1e590d14cd2551f4():
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('argv', 'cwd', 'env', 'stdio', 'name')), EqPlan(fields=('argv', 'cwd', 'env', 'std"
        "io', 'name')), FrozenPlan(fields=('argv', 'cwd', 'env', 'stdio', 'name'), allow_dynamic_dunder_attrs=False), H"
        "ashPlan(action='add', fields=('argv', 'cwd', 'env', 'stdio', 'name'), cache=True), InitPlan(fields=(InitPlan.F"
        "ield(name='argv', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init="
        "True, override=False, field_type=FieldType.INSTANCE, coerce=OpRef(name='init.fields.0.coerce'), validate=None,"
        " check_type=None), InitPlan.Field(name='cwd', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef"
        "(name='init.fields.1.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE"
        ", coerce=None, validate=None, check_type=None), InitPlan.Field(name='env', annotation=OpRef(name='init.fields."
        "2.annotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, override=False, "
        "field_type=FieldType.INSTANCE, coerce=OpRef(name='init.fields.2.coerce'), validate=None, check_type=None), Ini"
        "tPlan.Field(name='stdio', annotation=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.fields.3"
        ".default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, valid"
        "ate=None, check_type=None), InitPlan.Field(name='name', annotation=OpRef(name='init.fields.4.annotation'), def"
        "ault=OpRef(name='init.fields.4.default'), default_factory=None, init=True, override=False, field_type=FieldTyp"
        "e.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('argv',), kw_only_pa"
        "rams=('cwd', 'env', 'stdio', 'name'), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_f"
        "ns=()), ReprPlan(fields=(ReprPlan.Field(name='argv', kw_only=False, fn=None), ReprPlan.Field(name='cwd', kw_on"
        "ly=True, fn=None), ReprPlan.Field(name='env', kw_only=True, fn=None), ReprPlan.Field(name='stdio', kw_only=Tru"
        "e, fn=None), ReprPlan.Field(name='name', kw_only=True, fn=None)), id=False, terse=False, default_fn=OpRef(name"
        "='repr.default_fn'))))"
    ),
    plan_repr_sha1='4275b9ae709f9a70a1b3fa94d8805a71cc20b675',
    cls_names=(
        ('omllm.core.processes.types.specs', 'ProcessSpec'),
    ),
)
def _process_dataclass__4275b9ae709f9a70a1b3fa94d8805a71cc20b675():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__coerce,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__coerce,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('stdin', 'stdout', 'stderr')), EqPlan(fields=('stdin', 'stdout', 'stderr')), Froze"
        "nPlan(fields=('stdin', 'stdout', 'stderr'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=("
        "'stdin', 'stdout', 'stderr'), cache=True), InitPlan(fields=(InitPlan.Field(name='stdin', annotation=OpRef(name"
        "='init.fields.0.annotation'), default=OpRef(name='init.fields.0.default'), default_factory=None, init=True, ov"
        "erride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name"
        "='stdout', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), def"
        "ault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check"
        "_type=None), InitPlan.Field(name='stderr', annotation=OpRef(name='init.fields.2.annotation'), default=OpRef(na"
        "me='init.fields.2.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, c"
        "oerce=None, validate=None, check_type=None)), self_param='self', std_params=(), kw_only_params=('stdin', 'stdo"
        "ut', 'stderr'), frozen=True, slots=False, post_init_params=(), init_fns=(), validate_fns=()), ReprPlan(fields="
        "(ReprPlan.Field(name='stdin', kw_only=True, fn=None), ReprPlan.Field(name='stdout', kw_only=True, fn=None), Re"
        "prPlan.Field(name='stderr', kw_only=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='3b70cd4f03cfd37d11ef93c4fcce8732a9f97263',
    cls_names=(
        ('omllm.core.processes.types.specs', 'ProcessStdio'),
    ),
)
def _process_dataclass__3b70cd4f03cfd37d11ef93c4fcce8732a9f97263():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__default,
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
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('rows', 'cols', 'term')), EqPlan(fields=('rows', 'cols', 'term')), FrozenPlan(fiel"
        "ds=('rows', 'cols', 'term'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('rows', 'cols',"
        " 'term'), cache=True), InitPlan(fields=(InitPlan.Field(name='rows', annotation=OpRef(name='init.fields.0.annot"
        "ation'), default=OpRef(name='init.fields.0.default'), default_factory=None, init=True, override=False, field_t"
        "ype=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='cols', annotation=O"
        "pRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init"
        "=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.F"
        "ield(name='term', annotation=OpRef(name='init.fields.2.annotation'), default=OpRef(name='init.fields.2.default"
        "'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None"
        ", check_type=None)), self_param='self', std_params=(), kw_only_params=('rows', 'cols', 'term'), frozen=True, s"
        "lots=False, post_init_params=(), init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='rows', k"
        "w_only=True, fn=None), ReprPlan.Field(name='cols', kw_only=True, fn=None), ReprPlan.Field(name='term', kw_only"
        "=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='8e0cbaf421c3b71ad9ae0cbdcfc78c820f4b35d7',
    cls_names=(
        ('omllm.core.processes.types.specs', 'PtyStdio'),
    ),
)
def _process_dataclass__8e0cbaf421c3b71ad9ae0cbdcfc78c820f4b35d7():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__0__default,
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
