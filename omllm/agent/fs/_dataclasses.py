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
        "Plans(tup=(CopyPlan(fields=('name', 'path', 'is_dir', 'is_file', 'is_symlink')), EqPlan(fields=('name', 'path'"
        ", 'is_dir', 'is_file', 'is_symlink')), FrozenPlan(fields=('name', 'path', 'is_dir', 'is_file', 'is_symlink'), "
        "allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('name', 'path', 'is_dir', 'is_file', 'is_sym"
        "link'), cache=False), InitPlan(fields=(InitPlan.Field(name='name', annotation=OpRef(name='init.fields.0.annota"
        "tion'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=N"
        "one, validate=None, check_type=None), InitPlan.Field(name='path', annotation=OpRef(name='init.fields.1.annotat"
        "ion'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=No"
        "ne, validate=None, check_type=None), InitPlan.Field(name='is_dir', annotation=OpRef(name='init.fields.2.annota"
        "tion'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=N"
        "one, validate=None, check_type=None), InitPlan.Field(name='is_file', annotation=OpRef(name='init.fields.3.anno"
        "tation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce"
        "=None, validate=None, check_type=None), InitPlan.Field(name='is_symlink', annotation=OpRef(name='init.fields.4"
        ".annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, c"
        "oerce=None, validate=None, check_type=None)), self_param='self', std_params=(), kw_only_params=('name', 'path'"
        ", 'is_dir', 'is_file', 'is_symlink'), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_f"
        "ns=()), ReprPlan(fields=(ReprPlan.Field(name='name', kw_only=True, fn=None), ReprPlan.Field(name='path', kw_on"
        "ly=True, fn=None), ReprPlan.Field(name='is_dir', kw_only=True, fn=None), ReprPlan.Field(name='is_file', kw_onl"
        "y=True, fn=None), ReprPlan.Field(name='is_symlink', kw_only=True, fn=None)), id=False, terse=False, default_fn"
        "=None)))"
    ),
    plan_repr_sha1='666c61aa6fb778a93f81977413f971db33a9db69',
    cls_names=(
        ('omllm.agent.fs.ops', 'FsDirEntry'),
    ),
)
def _process_dataclass__666c61aa6fb778a93f81977413f971db33a9db69():
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
                name=self.name,
                path=self.path,
                is_dir=self.is_dir,
                is_file=self.is_file,
                is_symlink=self.is_symlink,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.path == other.path and
                self.is_dir == other.is_dir and
                self.is_file == other.is_file and
                self.is_symlink == other.is_symlink
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'path',
            'is_dir',
            'is_file',
            'is_symlink',
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
                self.path,
                self.is_dir,
                self.is_file,
                self.is_symlink,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            name: __dataclass__init__fields__0__annotation,
            path: __dataclass__init__fields__1__annotation,
            is_dir: __dataclass__init__fields__2__annotation,
            is_file: __dataclass__init__fields__3__annotation,
            is_symlink: __dataclass__init__fields__4__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'path', path)
            __dataclass__object_setattr(self, 'is_dir', is_dir)
            __dataclass__object_setattr(self, 'is_file', is_file)
            __dataclass__object_setattr(self, 'is_symlink', is_symlink)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"path={self.path!r}")
            parts.append(f"is_dir={self.is_dir!r}")
            parts.append(f"is_file={self.is_file!r}")
            parts.append(f"is_symlink={self.is_symlink!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('path', 'mode')), EqPlan(fields=('path', 'mode')), FrozenPlan(fields=('path', 'mod"
        "e'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('path', 'mode'), cache=False), InitPlan"
        "(fields=(InitPlan.Field(name='path', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_"
        "factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type"
        "=None), InitPlan.Field(name='mode', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_f"
        "actory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type="
        "None)), self_param='self', std_params=('path', 'mode'), kw_only_params=(), frozen=True, slots=False, post_init"
        "_params=None, init_fns=(), validate_fns=(InitPlan.ValidateFnWithParams(fn=OpRef(name='init.validate_fns.0'), p"
        "arams=('self',)),)), ReprPlan(fields=(ReprPlan.Field(name='path', kw_only=False, fn=None), ReprPlan.Field(name"
        "='mode', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='dd41662175f25f58af6e728e4ddbd4349af9c8d1',
    cls_names=(
        ('omllm.agent.fs.permissions', 'FsPermissionTarget'),
    ),
)
def _process_dataclass__dd41662175f25f58af6e728e4ddbd4349af9c8d1():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__validate_fns__0,
        __dataclass__FnValidationError,  # noqa
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
                path=self.path,
                mode=self.mode,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.path == other.path and
                self.mode == other.mode
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'path',
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
                self.path,
                self.mode,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            path: __dataclass__init__fields__0__annotation,
            mode: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'path', path)
            __dataclass__object_setattr(self, 'mode', mode)
            if not __dataclass__init__validate_fns__0(
                self,
            ):
                raise __dataclass__FnValidationError(
                    obj=self,
                    fn=__dataclass__init__validate_fns__0,
                )

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"path={self.path!r}")
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
        "Plans(tup=(CopyPlan(fields=('glob', 'modes')), EqPlan(fields=('glob', 'modes')), FrozenPlan(fields=('glob', 'm"
        "odes'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('glob', 'modes'), cache=False), Init"
        "Plan(fields=(InitPlan.Field(name='glob', annotation=OpRef(name='init.fields.0.annotation'), default=None, defa"
        "ult_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_"
        "type=None), InitPlan.Field(name='modes', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name"
        "='init.fields.1.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coe"
        "rce=OpRef(name='init.fields.1.coerce'), validate=None, check_type=None)), self_param='self', std_params=('glob"
        "', 'modes'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=())"
        ", ReprPlan(fields=(ReprPlan.Field(name='glob', kw_only=False, fn=None), ReprPlan.Field(name='modes', kw_only=F"
        "alse, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='9361562d73fccc08c989ef1ca23e3893b758987d',
    cls_names=(
        ('omllm.agent.fs.permissions', 'GlobFsPermissionMatcher'),
    ),
)
def _process_dataclass__9361562d73fccc08c989ef1ca23e3893b758987d():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__coerce,
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
                glob=self.glob,
                modes=self.modes,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.glob == other.glob and
                self.modes == other.modes
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'glob',
            'modes',
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
                self.glob,
                self.modes,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            glob: __dataclass__init__fields__0__annotation,
            modes: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            modes = __dataclass__init__fields__1__coerce(modes)
            __dataclass__object_setattr(self, 'glob', glob)
            __dataclass__object_setattr(self, 'modes', modes)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"glob={self.glob!r}")
            parts.append(f"modes={self.modes!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('path', 'diff')), EqPlan(fields=('path', 'diff')), FrozenPlan(fields=('path', 'dif"
        "f'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('path', 'diff'), cache=False), InitPlan"
        "(fields=(InitPlan.Field(name='path', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_"
        "factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type"
        "=None), InitPlan.Field(name='diff', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_f"
        "actory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type="
        "None)), self_param='self', std_params=(), kw_only_params=('path', 'diff'), frozen=True, slots=False, post_init"
        "_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='path', kw_only=True, fn=Non"
        "e), ReprPlan.Field(name='diff', kw_only=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='a4209b0f41bbecf4b6ef227f7d42fa67555c4334',
    cls_names=(
        ('omllm.agent.fs.tools.details', 'EditToolResultDetails'),
    ),
)
def _process_dataclass__a4209b0f41bbecf4b6ef227f7d42fa67555c4334():
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
                path=self.path,
                diff=self.diff,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.path == other.path and
                self.diff == other.diff
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'path',
            'diff',
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
                self.path,
                self.diff,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            path: __dataclass__init__fields__0__annotation,
            diff: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'path', path)
            __dataclass__object_setattr(self, 'diff', diff)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"path={self.path!r}")
            parts.append(f"diff={self.diff!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('path', 'line_offset', 'num_lines', 'has_more')), EqPlan(fields=('path', 'line_off"
        "set', 'num_lines', 'has_more')), FrozenPlan(fields=('path', 'line_offset', 'num_lines', 'has_more'), allow_dyn"
        "amic_dunder_attrs=False), HashPlan(action='add', fields=('path', 'line_offset', 'num_lines', 'has_more'), cach"
        "e=False), InitPlan(fields=(InitPlan.Field(name='path', annotation=OpRef(name='init.fields.0.annotation'), defa"
        "ult=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validat"
        "e=None, check_type=None), InitPlan.Field(name='line_offset', annotation=OpRef(name='init.fields.1.annotation')"
        ", default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, v"
        "alidate=None, check_type=None), InitPlan.Field(name='num_lines', annotation=OpRef(name='init.fields.2.annotati"
        "on'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=Non"
        "e, validate=None, check_type=None), InitPlan.Field(name='has_more', annotation=OpRef(name='init.fields.3.annot"
        "ation'), default=OpRef(name='init.fields.3.default'), default_factory=None, init=True, override=False, field_t"
        "ype=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=(), kw_on"
        "ly_params=('path', 'line_offset', 'num_lines', 'has_more'), frozen=True, slots=False, post_init_params=None, i"
        "nit_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='path', kw_only=True, fn=None), ReprPlan.Fi"
        "eld(name='line_offset', kw_only=True, fn=None), ReprPlan.Field(name='num_lines', kw_only=True, fn=None), ReprP"
        "lan.Field(name='has_more', kw_only=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='62a495a61ef2d40424778f7db8256108c109536d',
    cls_names=(
        ('omllm.agent.fs.tools.details', 'ReadToolResultDetails'),
    ),
)
def _process_dataclass__62a495a61ef2d40424778f7db8256108c109536d():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
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
                path=self.path,
                line_offset=self.line_offset,
                num_lines=self.num_lines,
                has_more=self.has_more,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.path == other.path and
                self.line_offset == other.line_offset and
                self.num_lines == other.num_lines and
                self.has_more == other.has_more
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'path',
            'line_offset',
            'num_lines',
            'has_more',
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
                self.path,
                self.line_offset,
                self.num_lines,
                self.has_more,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            path: __dataclass__init__fields__0__annotation,
            line_offset: __dataclass__init__fields__1__annotation,
            num_lines: __dataclass__init__fields__2__annotation,
            has_more: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'path', path)
            __dataclass__object_setattr(self, 'line_offset', line_offset)
            __dataclass__object_setattr(self, 'num_lines', num_lines)
            __dataclass__object_setattr(self, 'has_more', has_more)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"path={self.path!r}")
            parts.append(f"line_offset={self.line_offset!r}")
            parts.append(f"num_lines={self.num_lines!r}")
            parts.append(f"has_more={self.has_more!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('path', 'num_bytes', 'created')), EqPlan(fields=('path', 'num_bytes', 'created')),"
        " FrozenPlan(fields=('path', 'num_bytes', 'created'), allow_dynamic_dunder_attrs=False), HashPlan(action='add',"
        " fields=('path', 'num_bytes', 'created'), cache=False), InitPlan(fields=(InitPlan.Field(name='path', annotatio"
        "n=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field"
        "_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='num_bytes', annot"
        "ation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, f"
        "ield_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='created', ann"
        "otation=OpRef(name='init.fields.2.annotation'), default=OpRef(name='init.fields.2.default'), default_factory=N"
        "one, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), "
        "self_param='self', std_params=(), kw_only_params=('path', 'num_bytes', 'created'), frozen=True, slots=False, p"
        "ost_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='path', kw_only=True"
        ", fn=None), ReprPlan.Field(name='num_bytes', kw_only=True, fn=None), ReprPlan.Field(name='created', kw_only=Tr"
        "ue, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='eb0c6cbbad2e7c1dd421cdf205089d6efdf3d2f8',
    cls_names=(
        ('omllm.agent.fs.tools.details', 'WriteToolResultDetails'),
    ),
)
def _process_dataclass__eb0c6cbbad2e7c1dd421cdf205089d6efdf3d2f8():
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
                path=self.path,
                num_bytes=self.num_bytes,
                created=self.created,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.path == other.path and
                self.num_bytes == other.num_bytes and
                self.created == other.created
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'path',
            'num_bytes',
            'created',
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
                self.path,
                self.num_bytes,
                self.created,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            path: __dataclass__init__fields__0__annotation,
            num_bytes: __dataclass__init__fields__1__annotation,
            created: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'path', path)
            __dataclass__object_setattr(self, 'num_bytes', num_bytes)
            __dataclass__object_setattr(self, 'created', created)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"path={self.path!r}")
            parts.append(f"num_bytes={self.num_bytes!r}")
            parts.append(f"created={self.created!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('file_path', 'old_string', 'new_string', 'replace_all')), EqPlan(fields=('file_pat"
        "h', 'old_string', 'new_string', 'replace_all')), FrozenPlan(fields=('file_path', 'old_string', 'new_string', '"
        "replace_all'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('file_path', 'old_string', 'n"
        "ew_string', 'replace_all'), cache=False), InitPlan(fields=(InitPlan.Field(name='file_path', annotation=OpRef(n"
        "ame='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=Fie"
        "ldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='old_string', annotation=Op"
        "Ref(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, field_typ"
        "e=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='new_string', annotati"
        "on=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=False, fiel"
        "d_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='replace_all', an"
        "notation=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default'), default_factory="
        "None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)),"
        " self_param='self', std_params=('file_path', 'old_string', 'new_string'), kw_only_params=('replace_all',), fro"
        "zen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(n"
        "ame='file_path', kw_only=False, fn=None), ReprPlan.Field(name='old_string', kw_only=False, fn=None), ReprPlan."
        "Field(name='new_string', kw_only=False, fn=None), ReprPlan.Field(name='replace_all', kw_only=True, fn=None)), "
        "id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='6bb5155e2a9ee0e5fe7294f7c726ce7735685111',
    cls_names=(
        ('omllm.agent.fs.tools.edit', 'EditToolParams'),
    ),
)
def _process_dataclass__6bb5155e2a9ee0e5fe7294f7c726ce7735685111():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
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
                file_path=self.file_path,
                old_string=self.old_string,
                new_string=self.new_string,
                replace_all=self.replace_all,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.file_path == other.file_path and
                self.old_string == other.old_string and
                self.new_string == other.new_string and
                self.replace_all == other.replace_all
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'file_path',
            'old_string',
            'new_string',
            'replace_all',
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
                self.file_path,
                self.old_string,
                self.new_string,
                self.replace_all,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            file_path: __dataclass__init__fields__0__annotation,
            old_string: __dataclass__init__fields__1__annotation,
            new_string: __dataclass__init__fields__2__annotation,
            *,
            replace_all: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'file_path', file_path)
            __dataclass__object_setattr(self, 'old_string', old_string)
            __dataclass__object_setattr(self, 'new_string', new_string)
            __dataclass__object_setattr(self, 'replace_all', replace_all)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"file_path={self.file_path!r}")
            parts.append(f"old_string={self.old_string!r}")
            parts.append(f"new_string={self.new_string!r}")
            parts.append(f"replace_all={self.replace_all!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('dir_path',)), EqPlan(fields=('dir_path',)), FrozenPlan(fields=('dir_path',), allo"
        "w_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('dir_path',), cache=False), InitPlan(fields=(Ini"
        "tPlan.Field(name='dir_path', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory="
        "None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),)"
        ", self_param='self', std_params=('dir_path',), kw_only_params=(), frozen=True, slots=False, post_init_params=N"
        "one, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='dir_path', kw_only=False, fn=None),)"
        ", id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='27abe82e33810aeaddffd47d7c0a415d1b79550d',
    cls_names=(
        ('omllm.agent.fs.tools.ls', 'LsToolParams'),
    ),
)
def _process_dataclass__27abe82e33810aeaddffd47d7c0a415d1b79550d():
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
                dir_path=self.dir_path,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.dir_path == other.dir_path
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'dir_path',
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
                self.dir_path,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            dir_path: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'dir_path', dir_path)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"dir_path={self.dir_path!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('file_path', 'line_offset', 'num_lines')), EqPlan(fields=('file_path', 'line_offse"
        "t', 'num_lines')), FrozenPlan(fields=('file_path', 'line_offset', 'num_lines'), allow_dynamic_dunder_attrs=Fal"
        "se), HashPlan(action='add', fields=('file_path', 'line_offset', 'num_lines'), cache=False), InitPlan(fields=(I"
        "nitPlan.Field(name='file_path', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_facto"
        "ry=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None"
        "), InitPlan.Field(name='line_offset', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='i"
        "nit.fields.1.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce"
        "=None, validate=None, check_type=None), InitPlan.Field(name='num_lines', annotation=OpRef(name='init.fields.2."
        "annotation'), default=OpRef(name='init.fields.2.default'), default_factory=None, init=True, override=False, fi"
        "eld_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('fi"
        "le_path',), kw_only_params=('line_offset', 'num_lines'), frozen=True, slots=False, post_init_params=None, init"
        "_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='file_path', kw_only=False, fn=None), ReprPlan"
        ".Field(name='line_offset', kw_only=True, fn=None), ReprPlan.Field(name='num_lines', kw_only=True, fn=None)), i"
        "d=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='c126660dd7e0a754a0ea97d31b0e819a7c894928',
    cls_names=(
        ('omllm.agent.fs.tools.read', 'ReadToolParams'),
    ),
)
def _process_dataclass__c126660dd7e0a754a0ea97d31b0e819a7c894928():
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
                file_path=self.file_path,
                line_offset=self.line_offset,
                num_lines=self.num_lines,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.file_path == other.file_path and
                self.line_offset == other.line_offset and
                self.num_lines == other.num_lines
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'file_path',
            'line_offset',
            'num_lines',
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
                self.file_path,
                self.line_offset,
                self.num_lines,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            file_path: __dataclass__init__fields__0__annotation,
            *,
            line_offset: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            num_lines: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'file_path', file_path)
            __dataclass__object_setattr(self, 'line_offset', line_offset)
            __dataclass__object_setattr(self, 'num_lines', num_lines)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"file_path={self.file_path!r}")
            parts.append(f"line_offset={self.line_offset!r}")
            parts.append(f"num_lines={self.num_lines!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('file_path', 'contents', 'overwrite')), EqPlan(fields=('file_path', 'contents', 'o"
        "verwrite')), FrozenPlan(fields=('file_path', 'contents', 'overwrite'), allow_dynamic_dunder_attrs=False), Hash"
        "Plan(action='add', fields=('file_path', 'contents', 'overwrite'), cache=False), InitPlan(fields=(InitPlan.Fiel"
        "d(name='file_path', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, ini"
        "t=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan."
        "Field(name='contents', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, "
        "init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPl"
        "an.Field(name='overwrite', annotation=OpRef(name='init.fields.2.annotation'), default=OpRef(name='init.fields."
        "2.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, vali"
        "date=None, check_type=None)), self_param='self', std_params=('file_path', 'contents'), kw_only_params=('overwr"
        "ite',), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprP"
        "lan.Field(name='file_path', kw_only=False, fn=None), ReprPlan.Field(name='contents', kw_only=False, fn=None), "
        "ReprPlan.Field(name='overwrite', kw_only=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='bf4ba2344c06b183bc9ffaa16e21241a3195847e',
    cls_names=(
        ('omllm.agent.fs.tools.write', 'WriteToolParams'),
    ),
)
def _process_dataclass__bf4ba2344c06b183bc9ffaa16e21241a3195847e():
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
                file_path=self.file_path,
                contents=self.contents,
                overwrite=self.overwrite,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.file_path == other.file_path and
                self.contents == other.contents and
                self.overwrite == other.overwrite
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'file_path',
            'contents',
            'overwrite',
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
                self.file_path,
                self.contents,
                self.overwrite,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            file_path: __dataclass__init__fields__0__annotation,
            contents: __dataclass__init__fields__1__annotation,
            *,
            overwrite: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'file_path', file_path)
            __dataclass__object_setattr(self, 'contents', contents)
            __dataclass__object_setattr(self, 'overwrite', overwrite)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"file_path={self.file_path!r}")
            parts.append(f"contents={self.contents!r}")
            parts.append(f"overwrite={self.overwrite!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
