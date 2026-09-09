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
        "Plans(tup=(CopyPlan(fields=('manifest', 'packages', 'registry')), EqPlan(fields=('manifest', 'packages', 'regi"
        "stry')), FrozenPlan(fields=('manifest', 'packages', 'registry'), allow_dynamic_dunder_attrs=False), HashPlan(a"
        "ction='add', fields=('manifest', 'packages', 'registry'), cache=False), InitPlan(fields=(InitPlan.Field(name='"
        "manifest', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, o"
        "verride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(nam"
        "e='packages', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True"
        ", override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field("
        "name='registry', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=OpRef(name='"
        "init.fields.2.default_factory'), init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, valida"
        "te=None, check_type=None)), self_param='self', std_params=('manifest', 'packages', 'registry'), kw_only_params"
        "=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan"
        ".Field(name='manifest', kw_only=False, fn=None), ReprPlan.Field(name='packages', kw_only=False, fn=None), Repr"
        "Plan.Field(name='registry', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='b8f8d1fb23b6dafb472faf7bd10d7bd13cd0b408',
    cls_names=(
        ('omdev.js.vendor.models', 'AddRequest'),
        ('omdev.js.vendor.models', 'RemoveRequest'),
    ),
)
def _process_dataclass__b8f8d1fb23b6dafb472faf7bd10d7bd13cd0b408():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default_factory,
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
                manifest=self.manifest,
                packages=self.packages,
                registry=self.registry,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.manifest == other.manifest and
                self.packages == other.packages and
                self.registry == other.registry
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'manifest',
            'packages',
            'registry',
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
                self.manifest,
                self.packages,
                self.registry,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            manifest: __dataclass__init__fields__0__annotation,
            packages: __dataclass__init__fields__1__annotation,
            registry: __dataclass__init__fields__2__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if registry is __dataclass__HAS_DEFAULT_FACTORY:
                registry = __dataclass__init__fields__2__default_factory()
            __dataclass__object_setattr(self, 'manifest', manifest)
            __dataclass__object_setattr(self, 'packages', packages)
            __dataclass__object_setattr(self, 'registry', registry)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"manifest={self.manifest!r}")
            parts.append(f"packages={self.packages!r}")
            parts.append(f"registry={self.registry!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('package', 'cache_directory')), EqPlan(fields=('package', 'cache_directory')), Fro"
        "zenPlan(fields=('package', 'cache_directory'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', field"
        "s=('package', 'cache_directory'), cache=False), InitPlan(fields=(InitPlan.Field(name='package', annotation=OpR"
        "ef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type"
        "=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='cache_directory', anno"
        "tation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, "
        "field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('"
        "package', 'cache_directory'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(),"
        " validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='package', kw_only=False, fn=None), ReprPlan.Field(nam"
        "e='cache_directory', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='6941c5a21807fb2748c35eded2a6aefc271860c7',
    cls_names=(
        ('omdev.js.vendor.models', 'DownloadRequest'),
    ),
)
def _process_dataclass__6941c5a21807fb2748c35eded2a6aefc271860c7():
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
                package=self.package,
                cache_directory=self.cache_directory,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.package == other.package and
                self.cache_directory == other.cache_directory
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'package',
            'cache_directory',
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
                self.package,
                self.cache_directory,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            package: __dataclass__init__fields__0__annotation,
            cache_directory: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'package', package)
            __dataclass__object_setattr(self, 'cache_directory', cache_directory)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"package={self.package!r}")
            parts.append(f"cache_directory={self.cache_directory!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('package', 'data')), EqPlan(fields=('package', 'data')), FrozenPlan(fields=('packa"
        "ge', 'data'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('package', 'data'), cache=Fals"
        "e), InitPlan(fields=(InitPlan.Field(name='package', annotation=OpRef(name='init.fields.0.annotation'), default"
        "=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=N"
        "one, check_type=None), InitPlan.Field(name='data', annotation=OpRef(name='init.fields.1.annotation'), default="
        "None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=No"
        "ne, check_type=None)), self_param='self', std_params=('package', 'data'), kw_only_params=(), frozen=True, slot"
        "s=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='package',"
        " kw_only=False, fn=None), ReprPlan.Field(name='data', kw_only=False, fn=None)), id=False, terse=False, default"
        "_fn=None)))"
    ),
    plan_repr_sha1='db866e3024fc162ea19e5c281d1fedc6f1645165',
    cls_names=(
        ('omdev.js.vendor.models', 'DownloadedPackage'),
    ),
)
def _process_dataclass__db866e3024fc162ea19e5c281d1fedc6f1645165():
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
                package=self.package,
                data=self.data,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.package == other.package and
                self.data == other.data
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'package',
            'data',
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
                self.package,
                self.data,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            package: __dataclass__init__fields__0__annotation,
            data: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'package', package)
            __dataclass__object_setattr(self, 'data', data)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"package={self.package!r}")
            parts.append(f"data={self.data!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('package', 'files', 'metadata', 'exports', 'module_origins')), EqPlan(fields=('pac"
        "kage', 'files', 'metadata', 'exports', 'module_origins')), FrozenPlan(fields=('package', 'files', 'metadata', "
        "'exports', 'module_origins'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('package', 'fi"
        "les', 'metadata', 'exports', 'module_origins'), cache=False), InitPlan(fields=(InitPlan.Field(name='package', "
        "annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=Fal"
        "se, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='files', "
        "annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override=Fal"
        "se, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='metadata"
        "', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override="
        "False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='expor"
        "ts', annotation=OpRef(name='init.fields.3.annotation'), default=None, default_factory=None, init=True, overrid"
        "e=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='mod"
        "ule_origins', annotation=OpRef(name='init.fields.4.annotation'), default=None, default_factory=None, init=True"
        ", override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='se"
        "lf', std_params=('package', 'files', 'metadata', 'exports', 'module_origins'), kw_only_params=(), frozen=True,"
        " slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='pack"
        "age', kw_only=False, fn=None), ReprPlan.Field(name='files', kw_only=False, fn=None), ReprPlan.Field(name='meta"
        "data', kw_only=False, fn=None), ReprPlan.Field(name='exports', kw_only=False, fn=None), ReprPlan.Field(name='m"
        "odule_origins', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='83a30d8ae8f40a705f69e766c3c0fb4db8994103',
    cls_names=(
        ('omdev.js.vendor.models', 'ExtractedPackage'),
    ),
)
def _process_dataclass__83a30d8ae8f40a705f69e766c3c0fb4db8994103():
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
                package=self.package,
                files=self.files,
                metadata=self.metadata,
                exports=self.exports,
                module_origins=self.module_origins,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.package == other.package and
                self.files == other.files and
                self.metadata == other.metadata and
                self.exports == other.exports and
                self.module_origins == other.module_origins
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'package',
            'files',
            'metadata',
            'exports',
            'module_origins',
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
                self.package,
                self.files,
                self.metadata,
                self.exports,
                self.module_origins,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            package: __dataclass__init__fields__0__annotation,
            files: __dataclass__init__fields__1__annotation,
            metadata: __dataclass__init__fields__2__annotation,
            exports: __dataclass__init__fields__3__annotation,
            module_origins: __dataclass__init__fields__4__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'package', package)
            __dataclass__object_setattr(self, 'files', files)
            __dataclass__object_setattr(self, 'metadata', metadata)
            __dataclass__object_setattr(self, 'exports', exports)
            __dataclass__object_setattr(self, 'module_origins', module_origins)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"package={self.package!r}")
            parts.append(f"files={self.files!r}")
            parts.append(f"metadata={self.metadata!r}")
            parts.append(f"exports={self.exports!r}")
            parts.append(f"module_origins={self.module_origins!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('root',)), EqPlan(fields=('root',)), FrozenPlan(fields=('root',), allow_dynamic_du"
        "nder_attrs=False), HashPlan(action='add', fields=('root',), cache=False), InitPlan(fields=(InitPlan.Field(name"
        "='root', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, ove"
        "rride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='self',"
        " std_params=('root',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), valida"
        "te_fns=()), ReprPlan(fields=(ReprPlan.Field(name='root', kw_only=False, fn=None),), id=False, terse=False, def"
        "ault_fn=None)))"
    ),
    plan_repr_sha1='924cd9e6e063511324065384baa210fdb5d205c6',
    cls_names=(
        ('omdev.js.vendor.models', 'GraphVerifyRequest'),
    ),
)
def _process_dataclass__924cd9e6e063511324065384baa210fdb5d205c6():
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
                root=self.root,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.root == other.root
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'root',
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
                self.root,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            root: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'root', root)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"root={self.root!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('module_count', 'import_count')), EqPlan(fields=('module_count', 'import_count')),"
        " FrozenPlan(fields=('module_count', 'import_count'), allow_dynamic_dunder_attrs=False), HashPlan(action='add',"
        " fields=('module_count', 'import_count'), cache=False), InitPlan(fields=(InitPlan.Field(name='module_count', a"
        "nnotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=Fals"
        "e, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='import_co"
        "unt', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, overri"
        "de=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std"
        "_params=('module_count', 'import_count'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, "
        "init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='module_count', kw_only=False, fn=None), R"
        "eprPlan.Field(name='import_count', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='c178cbd5a7d6c74df0ed38f60496965111b039f4',
    cls_names=(
        ('omdev.js.vendor.models', 'GraphVerifyResult'),
    ),
)
def _process_dataclass__c178cbd5a7d6c74df0ed38f60496965111b039f4():
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
                module_count=self.module_count,
                import_count=self.import_count,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.module_count == other.module_count and
                self.import_count == other.import_count
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'module_count',
            'import_count',
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
                self.module_count,
                self.import_count,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            module_count: __dataclass__init__fields__0__annotation,
            import_count: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'module_count', module_count)
            __dataclass__object_setattr(self, 'import_count', import_count)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"module_count={self.module_count!r}")
            parts.append(f"import_count={self.import_count!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('manifest', 'lock')), EqPlan(fields=('manifest', 'lock')), FrozenPlan(fields=('man"
        "ifest', 'lock'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('manifest', 'lock'), cache="
        "False), InitPlan(fields=(InitPlan.Field(name='manifest', annotation=OpRef(name='init.fields.0.annotation'), de"
        "fault=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, valid"
        "ate=None, check_type=None), InitPlan.Field(name='lock', annotation=OpRef(name='init.fields.1.annotation'), def"
        "ault=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, valida"
        "te=None, check_type=None)), self_param='self', std_params=('manifest', 'lock'), kw_only_params=(), frozen=True"
        ", slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='man"
        "ifest', kw_only=False, fn=None), ReprPlan.Field(name='lock', kw_only=False, fn=None)), id=False, terse=False, "
        "default_fn=None)))"
    ),
    plan_repr_sha1='9eb6e0923fcc85804853d777438420a0303a98fe',
    cls_names=(
        ('omdev.js.vendor.models', 'ManifestUpdateResult'),
    ),
)
def _process_dataclass__9eb6e0923fcc85804853d777438420a0303a98fe():
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
                manifest=self.manifest,
                lock=self.lock,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.manifest == other.manifest and
                self.lock == other.lock
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'manifest',
            'lock',
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
                self.manifest,
                self.lock,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            manifest: __dataclass__init__fields__0__annotation,
            lock: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'manifest', manifest)
            __dataclass__object_setattr(self, 'lock', lock)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"manifest={self.manifest!r}")
            parts.append(f"lock={self.lock!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('specifiers', 'dynamic_import')), EqPlan(fields=('specifiers', 'dynamic_import')),"
        " FrozenPlan(fields=('specifiers', 'dynamic_import'), allow_dynamic_dunder_attrs=False), HashPlan(action='add',"
        " fields=('specifiers', 'dynamic_import'), cache=False), InitPlan(fields=(InitPlan.Field(name='specifiers', ann"
        "otation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False,"
        " field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='dynamic_imp"
        "ort', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, overri"
        "de=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std"
        "_params=('specifiers', 'dynamic_import'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, "
        "init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='specifiers', kw_only=False, fn=None), Rep"
        "rPlan.Field(name='dynamic_import', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='670ce1bb93a2529d4f173f848608497155273a87',
    cls_names=(
        ('omdev.js.vendor.models', 'ModuleParseResult'),
    ),
)
def _process_dataclass__670ce1bb93a2529d4f173f848608497155273a87():
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
                specifiers=self.specifiers,
                dynamic_import=self.dynamic_import,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.specifiers == other.specifiers and
                self.dynamic_import == other.dynamic_import
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'specifiers',
            'dynamic_import',
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
                self.specifiers,
                self.dynamic_import,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            specifiers: __dataclass__init__fields__0__annotation,
            dynamic_import: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'specifiers', specifiers)
            __dataclass__object_setattr(self, 'dynamic_import', dynamic_import)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"specifiers={self.specifiers!r}")
            parts.append(f"dynamic_import={self.dynamic_import!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('value', 'start', 'end')), EqPlan(fields=('value', 'start', 'end')), FrozenPlan(fi"
        "elds=('value', 'start', 'end'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('value', 'st"
        "art', 'end'), cache=False), InitPlan(fields=(InitPlan.Field(name='value', annotation=OpRef(name='init.fields.0"
        ".annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, c"
        "oerce=None, validate=None, check_type=None), InitPlan.Field(name='start', annotation=OpRef(name='init.fields.1"
        ".annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, c"
        "oerce=None, validate=None, check_type=None), InitPlan.Field(name='end', annotation=OpRef(name='init.fields.2.a"
        "nnotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coe"
        "rce=None, validate=None, check_type=None)), self_param='self', std_params=('value', 'start', 'end'), kw_only_p"
        "arams=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(Rep"
        "rPlan.Field(name='value', kw_only=False, fn=None), ReprPlan.Field(name='start', kw_only=False, fn=None), ReprP"
        "lan.Field(name='end', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='9e9491ef70560ebc75a6944f1773db8660712131',
    cls_names=(
        ('omdev.js.vendor.models', 'ModuleSpecifier'),
    ),
)
def _process_dataclass__9e9491ef70560ebc75a6944f1773db8660712131():
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
                value=self.value,
                start=self.start,
                end=self.end,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.value == other.value and
                self.start == other.start and
                self.end == other.end
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'value',
            'start',
            'end',
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
                self.value,
                self.start,
                self.end,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            value: __dataclass__init__fields__0__annotation,
            start: __dataclass__init__fields__1__annotation,
            end: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'value', value)
            __dataclass__object_setattr(self, 'start', start)
            __dataclass__object_setattr(self, 'end', end)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"value={self.value!r}")
            parts.append(f"start={self.start!r}")
            parts.append(f"end={self.end!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('name', 'requirement', 'current', 'wanted', 'latest')), EqPlan(fields=('name', 're"
        "quirement', 'current', 'wanted', 'latest')), FrozenPlan(fields=('name', 'requirement', 'current', 'wanted', 'l"
        "atest'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('name', 'requirement', 'current', '"
        "wanted', 'latest'), cache=False), InitPlan(fields=(InitPlan.Field(name='name', annotation=OpRef(name='init.fie"
        "lds.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTAN"
        "CE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='requirement', annotation=OpRef(name='in"
        "it.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType."
        "INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='current', annotation=OpRef(name='"
        "init.fields.2.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldTyp"
        "e.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='wanted', annotation=OpRef(name="
        "'init.fields.3.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldTy"
        "pe.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='latest', annotation=OpRef(name"
        "='init.fields.4.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldT"
        "ype.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('name', 'requireme"
        "nt', 'current', 'wanted', 'latest'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_"
        "fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='name', kw_only=False, fn=None), ReprPlan.Field"
        "(name='requirement', kw_only=False, fn=None), ReprPlan.Field(name='current', kw_only=False, fn=None), ReprPlan"
        ".Field(name='wanted', kw_only=False, fn=None), ReprPlan.Field(name='latest', kw_only=False, fn=None)), id=Fals"
        "e, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='5941254ce2ea8a2ff6c20eb763dbfb06dca57f26',
    cls_names=(
        ('omdev.js.vendor.models', 'OutdatedPackage'),
    ),
)
def _process_dataclass__5941254ce2ea8a2ff6c20eb763dbfb06dca57f26():
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
                requirement=self.requirement,
                current=self.current,
                wanted=self.wanted,
                latest=self.latest,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.requirement == other.requirement and
                self.current == other.current and
                self.wanted == other.wanted and
                self.latest == other.latest
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'requirement',
            'current',
            'wanted',
            'latest',
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
                self.requirement,
                self.current,
                self.wanted,
                self.latest,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
            requirement: __dataclass__init__fields__1__annotation,
            current: __dataclass__init__fields__2__annotation,
            wanted: __dataclass__init__fields__3__annotation,
            latest: __dataclass__init__fields__4__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'requirement', requirement)
            __dataclass__object_setattr(self, 'current', current)
            __dataclass__object_setattr(self, 'wanted', wanted)
            __dataclass__object_setattr(self, 'latest', latest)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"requirement={self.requirement!r}")
            parts.append(f"current={self.current!r}")
            parts.append(f"wanted={self.wanted!r}")
            parts.append(f"latest={self.latest!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('manifest', 'lock', 'packages', 'registry')), EqPlan(fields=('manifest', 'lock', '"
        "packages', 'registry')), FrozenPlan(fields=('manifest', 'lock', 'packages', 'registry'), allow_dynamic_dunder_"
        "attrs=False), HashPlan(action='add', fields=('manifest', 'lock', 'packages', 'registry'), cache=False), InitPl"
        "an(fields=(InitPlan.Field(name='manifest', annotation=OpRef(name='init.fields.0.annotation'), default=None, de"
        "fault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, chec"
        "k_type=None), InitPlan.Field(name='lock', annotation=OpRef(name='init.fields.1.annotation'), default=None, def"
        "ault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check"
        "_type=None), InitPlan.Field(name='packages', annotation=OpRef(name='init.fields.2.annotation'), default=OpRef("
        "name='init.fields.2.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE,"
        " coerce=None, validate=None, check_type=None), InitPlan.Field(name='registry', annotation=OpRef(name='init.fie"
        "lds.3.annotation'), default=None, default_factory=OpRef(name='init.fields.3.default_factory'), init=True, over"
        "ride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', s"
        "td_params=('manifest', 'lock', 'packages', 'registry'), kw_only_params=(), frozen=True, slots=False, post_init"
        "_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='manifest', kw_only=False, f"
        "n=None), ReprPlan.Field(name='lock', kw_only=False, fn=None), ReprPlan.Field(name='packages', kw_only=False, f"
        "n=None), ReprPlan.Field(name='registry', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='68ed795e2ca1a8814cad3ce112b88d27ff4bd310',
    cls_names=(
        ('omdev.js.vendor.models', 'OutdatedRequest'),
    ),
)
def _process_dataclass__68ed795e2ca1a8814cad3ce112b88d27ff4bd310():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__3__default_factory,
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
                manifest=self.manifest,
                lock=self.lock,
                packages=self.packages,
                registry=self.registry,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.manifest == other.manifest and
                self.lock == other.lock and
                self.packages == other.packages and
                self.registry == other.registry
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'manifest',
            'lock',
            'packages',
            'registry',
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
                self.manifest,
                self.lock,
                self.packages,
                self.registry,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            manifest: __dataclass__init__fields__0__annotation,
            lock: __dataclass__init__fields__1__annotation,
            packages: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            registry: __dataclass__init__fields__3__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if registry is __dataclass__HAS_DEFAULT_FACTORY:
                registry = __dataclass__init__fields__3__default_factory()
            __dataclass__object_setattr(self, 'manifest', manifest)
            __dataclass__object_setattr(self, 'lock', lock)
            __dataclass__object_setattr(self, 'packages', packages)
            __dataclass__object_setattr(self, 'registry', registry)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"manifest={self.manifest!r}")
            parts.append(f"lock={self.lock!r}")
            parts.append(f"packages={self.packages!r}")
            parts.append(f"registry={self.registry!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('packages',)), EqPlan(fields=('packages',)), FrozenPlan(fields=('packages',), allo"
        "w_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('packages',), cache=False), InitPlan(fields=(Ini"
        "tPlan.Field(name='packages', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory="
        "None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),)"
        ", self_param='self', std_params=('packages',), kw_only_params=(), frozen=True, slots=False, post_init_params=N"
        "one, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='packages', kw_only=False, fn=None),)"
        ", id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='af7a912471cab43c868d457c81c6448fe26de90e',
    cls_names=(
        ('omdev.js.vendor.models', 'OutdatedResult'),
        ('omdev.js.vendor.models', 'VersionResolveResult'),
    ),
)
def _process_dataclass__af7a912471cab43c868d457c81c6448fe26de90e():
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
                packages=self.packages,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.packages == other.packages
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'packages',
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
                self.packages,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            packages: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'packages', packages)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"packages={self.packages!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('root', 'lock')), EqPlan(fields=('root', 'lock')), FrozenPlan(fields=('root', 'loc"
        "k'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('root', 'lock'), cache=False), InitPlan"
        "(fields=(InitPlan.Field(name='root', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_"
        "factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type"
        "=None), InitPlan.Field(name='lock', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_f"
        "actory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type="
        "None)), self_param='self', std_params=('root', 'lock'), kw_only_params=(), frozen=True, slots=False, post_init"
        "_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='root', kw_only=False, fn=No"
        "ne), ReprPlan.Field(name='lock', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='760d5e839456fd68373c3628a72e4aecabc5040a',
    cls_names=(
        ('omdev.js.vendor.models', 'OutputBuildRequest'),
    ),
)
def _process_dataclass__760d5e839456fd68373c3628a72e4aecabc5040a():
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
                root=self.root,
                lock=self.lock,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.root == other.root and
                self.lock == other.lock
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'root',
            'lock',
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
                self.root,
                self.lock,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            root: __dataclass__init__fields__0__annotation,
            lock: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'root', root)
            __dataclass__object_setattr(self, 'lock', lock)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"root={self.root!r}")
            parts.append(f"lock={self.lock!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('name', 'version')), EqPlan(fields=('name', 'version')), FrozenPlan(fields=('name'"
        ", 'version'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('name', 'version'), cache=Fals"
        "e), InitPlan(fields=(InitPlan.Field(name='name', annotation=OpRef(name='init.fields.0.annotation'), default=No"
        "ne, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None"
        ", check_type=None), InitPlan.Field(name='version', annotation=OpRef(name='init.fields.1.annotation'), default="
        "OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False, field_type=FieldType.INS"
        "TANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('name', 'version'), kw_on"
        "ly_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields="
        "(ReprPlan.Field(name='name', kw_only=False, fn=None), ReprPlan.Field(name='version', kw_only=False, fn=None)),"
        " id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='db3eee374e93a77b5d3c0df8fb72dd02bd521e32',
    cls_names=(
        ('omdev.js.vendor.models', 'PackageArgument'),
    ),
)
def _process_dataclass__db3eee374e93a77b5d3c0df8fb72dd02bd521e32():
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
                name=self.name,
                version=self.version,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.version == other.version
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'version',
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
                self.version,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
            version: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'version', version)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"version={self.version!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('entries', 'restricted')), EqPlan(fields=('entries', 'restricted')), FrozenPlan(fi"
        "elds=('entries', 'restricted'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('entries', '"
        "restricted'), cache=False), InitPlan(fields=(InitPlan.Field(name='entries', annotation=OpRef(name='init.fields"
        ".0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE,"
        " coerce=None, validate=None, check_type=None), InitPlan.Field(name='restricted', annotation=OpRef(name='init.f"
        "ields.1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INST"
        "ANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('entries', 'restricted'), "
        "kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fi"
        "elds=(ReprPlan.Field(name='entries', kw_only=False, fn=None), ReprPlan.Field(name='restricted', kw_only=False,"
        " fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='3380e68412df6b1671d06b04ba6f6d218c37560c',
    cls_names=(
        ('omdev.js.vendor.models', 'PackageExports'),
    ),
)
def _process_dataclass__3380e68412df6b1671d06b04ba6f6d218c37560c():
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
                entries=self.entries,
                restricted=self.restricted,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.entries == other.entries and
                self.restricted == other.restricted
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'entries',
            'restricted',
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
                self.entries,
                self.restricted,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            entries: __dataclass__init__fields__0__annotation,
            restricted: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'entries', entries)
            __dataclass__object_setattr(self, 'restricted', restricted)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"entries={self.entries!r}")
            parts.append(f"restricted={self.restricted!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('url', 'timeout')), EqPlan(fields=('url', 'timeout')), FrozenPlan(fields=('url', '"
        "timeout'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('url', 'timeout'), cache=False), "
        "InitPlan(fields=(InitPlan.Field(name='url', annotation=OpRef(name='init.fields.0.annotation'), default=OpRef(n"
        "ame='init.fields.0.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, "
        "coerce=None, validate=None, check_type=None), InitPlan.Field(name='timeout', annotation=OpRef(name='init.field"
        "s.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, override=False"
        ", field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params="
        "('url', 'timeout'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_"
        "fns=()), ReprPlan(fields=(ReprPlan.Field(name='url', kw_only=False, fn=None), ReprPlan.Field(name='timeout', k"
        "w_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='f03935f16c820c480210f8e7e488add5283f6b7f',
    cls_names=(
        ('omdev.js.vendor.models', 'RegistryConfig'),
    ),
)
def _process_dataclass__f03935f16c820c480210f8e7e488add5283f6b7f():
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
                url=self.url,
                timeout=self.timeout,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.url == other.url and
                self.timeout == other.timeout
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'url',
            'timeout',
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
                self.url,
                self.timeout,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            url: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            timeout: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'url', url)
            __dataclass__object_setattr(self, 'timeout', timeout)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"url={self.url!r}")
            parts.append(f"timeout={self.timeout!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('name', 'versions', 'tags')), EqPlan(fields=('name', 'versions', 'tags')), FrozenP"
        "lan(fields=('name', 'versions', 'tags'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('na"
        "me', 'versions', 'tags'), cache=False), InitPlan(fields=(InitPlan.Field(name='name', annotation=OpRef(name='in"
        "it.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType."
        "INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='versions', annotation=OpRef(name="
        "'init.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldTy"
        "pe.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='tags', annotation=OpRef(name='"
        "init.fields.2.annotation'), default=None, default_factory=OpRef(name='init.fields.2.default_factory'), init=Tr"
        "ue, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='"
        "self', std_params=('name', 'versions', 'tags'), kw_only_params=(), frozen=True, slots=False, post_init_params="
        "None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='name', kw_only=False, fn=None), Rep"
        "rPlan.Field(name='versions', kw_only=False, fn=None), ReprPlan.Field(name='tags', kw_only=False, fn=None)), id"
        "=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='279cdcf36f2774e2fc5be84cf1c7a557370791c1',
    cls_names=(
        ('omdev.js.vendor.models', 'RegistryPackage'),
    ),
)
def _process_dataclass__279cdcf36f2774e2fc5be84cf1c7a557370791c1():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default_factory,
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
                name=self.name,
                versions=self.versions,
                tags=self.tags,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.versions == other.versions and
                self.tags == other.tags
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'versions',
            'tags',
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
                self.versions,
                self.tags,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
            versions: __dataclass__init__fields__1__annotation,
            tags: __dataclass__init__fields__2__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if tags is __dataclass__HAS_DEFAULT_FACTORY:
                tags = __dataclass__init__fields__2__default_factory()
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'versions', versions)
            __dataclass__object_setattr(self, 'tags', tags)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"versions={self.versions!r}")
            parts.append(f"tags={self.tags!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('name', 'config')), EqPlan(fields=('name', 'config')), FrozenPlan(fields=('name', "
        "'config'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('name', 'config'), cache=False), "
        "InitPlan(fields=(InitPlan.Field(name='name', annotation=OpRef(name='init.fields.0.annotation'), default=None, "
        "default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, ch"
        "eck_type=None), InitPlan.Field(name='config', annotation=OpRef(name='init.fields.1.annotation'), default=None,"
        " default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, c"
        "heck_type=None)), self_param='self', std_params=('name', 'config'), kw_only_params=(), frozen=True, slots=Fals"
        "e, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='name', kw_only="
        "False, fn=None), ReprPlan.Field(name='config', kw_only=False, fn=None)), id=False, terse=False, default_fn=Non"
        "e)))"
    ),
    plan_repr_sha1='83d27623869e5aa54bd96ec842afbceac0a697ec',
    cls_names=(
        ('omdev.js.vendor.models', 'RegistryPackageRequest'),
    ),
)
def _process_dataclass__83d27623869e5aa54bd96ec842afbceac0a697ec():
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
                name=self.name,
                config=self.config,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.config == other.config
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'config',
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
                self.config,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
            config: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'config', config)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"config={self.config!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('name', 'version', 'dependencies', 'peer_dependencies', 'optional_peer_dependencie"
        "s')), EqPlan(fields=('name', 'version', 'dependencies', 'peer_dependencies', 'optional_peer_dependencies')), F"
        "rozenPlan(fields=('name', 'version', 'dependencies', 'peer_dependencies', 'optional_peer_dependencies'), allow"
        "_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('name', 'version', 'dependencies', 'peer_dependen"
        "cies', 'optional_peer_dependencies'), cache=False), InitPlan(fields=(InitPlan.Field(name='name', annotation=Op"
        "Ref(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_typ"
        "e=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='version', annotation="
        "OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, field_t"
        "ype=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='dependencies', anno"
        "tation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=False, "
        "field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='peer_depende"
        "ncies', annotation=OpRef(name='init.fields.3.annotation'), default=None, default_factory=None, init=True, over"
        "ride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='"
        "optional_peer_dependencies', annotation=OpRef(name='init.fields.4.annotation'), default=None, default_factory="
        "None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)),"
        " self_param='self', std_params=('name', 'version', 'dependencies', 'peer_dependencies', 'optional_peer_depende"
        "ncies'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), Re"
        "prPlan(fields=(ReprPlan.Field(name='name', kw_only=False, fn=None), ReprPlan.Field(name='version', kw_only=Fal"
        "se, fn=None), ReprPlan.Field(name='dependencies', kw_only=False, fn=None), ReprPlan.Field(name='peer_dependenc"
        "ies', kw_only=False, fn=None), ReprPlan.Field(name='optional_peer_dependencies', kw_only=False, fn=None)), id="
        "False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='b4ed5502d591e593584688c43a616ed1d2a256d8',
    cls_names=(
        ('omdev.js.vendor.models', 'RegistryPackageVersion'),
    ),
)
def _process_dataclass__b4ed5502d591e593584688c43a616ed1d2a256d8():
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
                version=self.version,
                dependencies=self.dependencies,
                peer_dependencies=self.peer_dependencies,
                optional_peer_dependencies=self.optional_peer_dependencies,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.version == other.version and
                self.dependencies == other.dependencies and
                self.peer_dependencies == other.peer_dependencies and
                self.optional_peer_dependencies == other.optional_peer_dependencies
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'version',
            'dependencies',
            'peer_dependencies',
            'optional_peer_dependencies',
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
                self.version,
                self.dependencies,
                self.peer_dependencies,
                self.optional_peer_dependencies,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
            version: __dataclass__init__fields__1__annotation,
            dependencies: __dataclass__init__fields__2__annotation,
            peer_dependencies: __dataclass__init__fields__3__annotation,
            optional_peer_dependencies: __dataclass__init__fields__4__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'version', version)
            __dataclass__object_setattr(self, 'dependencies', dependencies)
            __dataclass__object_setattr(self, 'peer_dependencies', peer_dependencies)
            __dataclass__object_setattr(self, 'optional_peer_dependencies', optional_peer_dependencies)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"version={self.version!r}")
            parts.append(f"dependencies={self.dependencies!r}")
            parts.append(f"peer_dependencies={self.peer_dependencies!r}")
            parts.append(f"optional_peer_dependencies={self.optional_peer_dependencies!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('name', 'version', 'config')), EqPlan(fields=('name', 'version', 'config')), Froze"
        "nPlan(fields=('name', 'version', 'config'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=("
        "'name', 'version', 'config'), cache=False), InitPlan(fields=(InitPlan.Field(name='name', annotation=OpRef(name"
        "='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldT"
        "ype.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='version', annotation=OpRef(na"
        "me='init.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=Fiel"
        "dType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='config', annotation=OpRef(n"
        "ame='init.fields.2.annotation'), default=None, default_factory=None, init=True, override=False, field_type=Fie"
        "ldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('name', 'versio"
        "n', 'config'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=("
        ")), ReprPlan(fields=(ReprPlan.Field(name='name', kw_only=False, fn=None), ReprPlan.Field(name='version', kw_on"
        "ly=False, fn=None), ReprPlan.Field(name='config', kw_only=False, fn=None)), id=False, terse=False, default_fn="
        "None)))"
    ),
    plan_repr_sha1='93f955e2eab04996f1cc60c9decb53c923c8b537',
    cls_names=(
        ('omdev.js.vendor.models', 'RegistryVersionRequest'),
    ),
)
def _process_dataclass__93f955e2eab04996f1cc60c9decb53c923c8b537():
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
                name=self.name,
                version=self.version,
                config=self.config,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.version == other.version and
                self.config == other.config
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'version',
            'config',
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
                self.version,
                self.config,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
            version: __dataclass__init__fields__1__annotation,
            config: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'version', version)
            __dataclass__object_setattr(self, 'config', config)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"version={self.version!r}")
            parts.append(f"config={self.config!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('manifest', 'registry')), EqPlan(fields=('manifest', 'registry')), FrozenPlan(fiel"
        "ds=('manifest', 'registry'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('manifest', 're"
        "gistry'), cache=False), InitPlan(fields=(InitPlan.Field(name='manifest', annotation=OpRef(name='init.fields.0."
        "annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, co"
        "erce=None, validate=None, check_type=None), InitPlan.Field(name='registry', annotation=OpRef(name='init.fields"
        ".1.annotation'), default=None, default_factory=OpRef(name='init.fields.1.default_factory'), init=True, overrid"
        "e=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_"
        "params=('manifest', 'registry'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns="
        "(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='manifest', kw_only=False, fn=None), ReprPlan.Field"
        "(name='registry', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='f99f222058760c6340265c009f519db75dcb2a66',
    cls_names=(
        ('omdev.js.vendor.models', 'ResolveRequest'),
    ),
)
def _process_dataclass__f99f222058760c6340265c009f519db75dcb2a66():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default_factory,
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
                manifest=self.manifest,
                registry=self.registry,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.manifest == other.manifest and
                self.registry == other.registry
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'manifest',
            'registry',
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
                self.manifest,
                self.registry,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            manifest: __dataclass__init__fields__0__annotation,
            registry: __dataclass__init__fields__1__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if registry is __dataclass__HAS_DEFAULT_FACTORY:
                registry = __dataclass__init__fields__1__default_factory()
            __dataclass__object_setattr(self, 'manifest', manifest)
            __dataclass__object_setattr(self, 'registry', registry)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"manifest={self.manifest!r}")
            parts.append(f"registry={self.registry!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('lock',)), EqPlan(fields=('lock',)), FrozenPlan(fields=('lock',), allow_dynamic_du"
        "nder_attrs=False), HashPlan(action='add', fields=('lock',), cache=False), InitPlan(fields=(InitPlan.Field(name"
        "='lock', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, ove"
        "rride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_param='self',"
        " std_params=('lock',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), valida"
        "te_fns=()), ReprPlan(fields=(ReprPlan.Field(name='lock', kw_only=False, fn=None),), id=False, terse=False, def"
        "ault_fn=None)))"
    ),
    plan_repr_sha1='cc994e2fb14a235cc7a2a3159080c5775d7acf7b',
    cls_names=(
        ('omdev.js.vendor.models', 'ResolveResult'),
    ),
)
def _process_dataclass__cc994e2fb14a235cc7a2a3159080c5775d7acf7b():
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
                lock=self.lock,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.lock == other.lock
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'lock',
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
                self.lock,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            lock: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'lock', lock)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"lock={self.lock!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('name', 'version', 'license', 'integrity', 'url', 'dependencies', 'peer_dependenci"
        "es', 'optional_peer_dependencies')), EqPlan(fields=('name', 'version', 'license', 'integrity', 'url', 'depende"
        "ncies', 'peer_dependencies', 'optional_peer_dependencies')), FrozenPlan(fields=('name', 'version', 'license', "
        "'integrity', 'url', 'dependencies', 'peer_dependencies', 'optional_peer_dependencies'), allow_dynamic_dunder_a"
        "ttrs=False), HashPlan(action='add', fields=('name', 'version', 'license', 'integrity', 'url', 'dependencies', "
        "'peer_dependencies', 'optional_peer_dependencies'), cache=False), InitPlan(fields=(InitPlan.Field(name='name',"
        " annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=Fa"
        "lse, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='version"
        "', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, override="
        "False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='licen"
        "se', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, overrid"
        "e=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='int"
        "egrity', annotation=OpRef(name='init.fields.3.annotation'), default=None, default_factory=None, init=True, ove"
        "rride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name="
        "'url', annotation=OpRef(name='init.fields.4.annotation'), default=None, default_factory=None, init=True, overr"
        "ide=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='d"
        "ependencies', annotation=OpRef(name='init.fields.5.annotation'), default=None, default_factory=None, init=True"
        ", override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field("
        "name='peer_dependencies', annotation=OpRef(name='init.fields.6.annotation'), default=None, default_factory=Non"
        "e, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), Ini"
        "tPlan.Field(name='optional_peer_dependencies', annotation=OpRef(name='init.fields.7.annotation'), default=None"
        ", default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, "
        "check_type=None)), self_param='self', std_params=('name', 'version', 'license', 'integrity', 'url', 'dependenc"
        "ies', 'peer_dependencies', 'optional_peer_dependencies'), kw_only_params=(), frozen=True, slots=False, post_in"
        "it_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='name', kw_only=False, fn="
        "None), ReprPlan.Field(name='version', kw_only=False, fn=None), ReprPlan.Field(name='license', kw_only=False, f"
        "n=None), ReprPlan.Field(name='integrity', kw_only=False, fn=None), ReprPlan.Field(name='url', kw_only=False, f"
        "n=None), ReprPlan.Field(name='dependencies', kw_only=False, fn=None), ReprPlan.Field(name='peer_dependencies',"
        " kw_only=False, fn=None), ReprPlan.Field(name='optional_peer_dependencies', kw_only=False, fn=None)), id=False"
        ", terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='024bde5ff632f6ec537e7b0372e36e4e36fec43f',
    cls_names=(
        ('omdev.js.vendor.models', 'ResolvedPackage'),
    ),
)
def _process_dataclass__024bde5ff632f6ec537e7b0372e36e4e36fec43f():
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
                version=self.version,
                license=self.license,
                integrity=self.integrity,
                url=self.url,
                dependencies=self.dependencies,
                peer_dependencies=self.peer_dependencies,
                optional_peer_dependencies=self.optional_peer_dependencies,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.version == other.version and
                self.license == other.license and
                self.integrity == other.integrity and
                self.url == other.url and
                self.dependencies == other.dependencies and
                self.peer_dependencies == other.peer_dependencies and
                self.optional_peer_dependencies == other.optional_peer_dependencies
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'version',
            'license',
            'integrity',
            'url',
            'dependencies',
            'peer_dependencies',
            'optional_peer_dependencies',
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
                self.version,
                self.license,
                self.integrity,
                self.url,
                self.dependencies,
                self.peer_dependencies,
                self.optional_peer_dependencies,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
            version: __dataclass__init__fields__1__annotation,
            license: __dataclass__init__fields__2__annotation,
            integrity: __dataclass__init__fields__3__annotation,
            url: __dataclass__init__fields__4__annotation,
            dependencies: __dataclass__init__fields__5__annotation,
            peer_dependencies: __dataclass__init__fields__6__annotation,
            optional_peer_dependencies: __dataclass__init__fields__7__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'version', version)
            __dataclass__object_setattr(self, 'license', license)
            __dataclass__object_setattr(self, 'integrity', integrity)
            __dataclass__object_setattr(self, 'url', url)
            __dataclass__object_setattr(self, 'dependencies', dependencies)
            __dataclass__object_setattr(self, 'peer_dependencies', peer_dependencies)
            __dataclass__object_setattr(self, 'optional_peer_dependencies', optional_peer_dependencies)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"version={self.version!r}")
            parts.append(f"license={self.license!r}")
            parts.append(f"integrity={self.integrity!r}")
            parts.append(f"url={self.url!r}")
            parts.append(f"dependencies={self.dependencies!r}")
            parts.append(f"peer_dependencies={self.peer_dependencies!r}")
            parts.append(f"optional_peer_dependencies={self.optional_peer_dependencies!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('source', 'source_path', 'package_names', 'package_exports', 'source_origin')), Eq"
        "Plan(fields=('source', 'source_path', 'package_names', 'package_exports', 'source_origin')), FrozenPlan(fields"
        "=('source', 'source_path', 'package_names', 'package_exports', 'source_origin'), allow_dynamic_dunder_attrs=Fa"
        "lse), HashPlan(action='add', fields=('source', 'source_path', 'package_names', 'package_exports', 'source_orig"
        "in'), cache=False), InitPlan(fields=(InitPlan.Field(name='source', annotation=OpRef(name='init.fields.0.annota"
        "tion'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=N"
        "one, validate=None, check_type=None), InitPlan.Field(name='source_path', annotation=OpRef(name='init.fields.1."
        "annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, co"
        "erce=None, validate=None, check_type=None), InitPlan.Field(name='package_names', annotation=OpRef(name='init.f"
        "ields.2.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INST"
        "ANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='package_exports', annotation=OpRef(na"
        "me='init.fields.3.annotation'), default=None, default_factory=OpRef(name='init.fields.3.default_factory'), ini"
        "t=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan."
        "Field(name='source_origin', annotation=OpRef(name='init.fields.4.annotation'), default=OpRef(name='init.fields"
        ".4.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, val"
        "idate=None, check_type=None)), self_param='self', std_params=('source', 'source_path', 'package_names', 'packa"
        "ge_exports', 'source_origin'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=()"
        ", validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='source', kw_only=False, fn=None), ReprPlan.Field(nam"
        "e='source_path', kw_only=False, fn=None), ReprPlan.Field(name='package_names', kw_only=False, fn=None), ReprPl"
        "an.Field(name='package_exports', kw_only=False, fn=None), ReprPlan.Field(name='source_origin', kw_only=False, "
        "fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='a8dbe97c9efebad066406d1e028af312f1348615',
    cls_names=(
        ('omdev.js.vendor.models', 'RewriteRequest'),
    ),
)
def _process_dataclass__a8dbe97c9efebad066406d1e028af312f1348615():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__3__annotation,
        __dataclass__init__fields__3__default_factory,
        __dataclass__init__fields__4__annotation,
        __dataclass__init__fields__4__default,
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
                source=self.source,
                source_path=self.source_path,
                package_names=self.package_names,
                package_exports=self.package_exports,
                source_origin=self.source_origin,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.source == other.source and
                self.source_path == other.source_path and
                self.package_names == other.package_names and
                self.package_exports == other.package_exports and
                self.source_origin == other.source_origin
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'source',
            'source_path',
            'package_names',
            'package_exports',
            'source_origin',
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
                self.source,
                self.source_path,
                self.package_names,
                self.package_exports,
                self.source_origin,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            source: __dataclass__init__fields__0__annotation,
            source_path: __dataclass__init__fields__1__annotation,
            package_names: __dataclass__init__fields__2__annotation,
            package_exports: __dataclass__init__fields__3__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            source_origin: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            if package_exports is __dataclass__HAS_DEFAULT_FACTORY:
                package_exports = __dataclass__init__fields__3__default_factory()
            __dataclass__object_setattr(self, 'source', source)
            __dataclass__object_setattr(self, 'source_path', source_path)
            __dataclass__object_setattr(self, 'package_names', package_names)
            __dataclass__object_setattr(self, 'package_exports', package_exports)
            __dataclass__object_setattr(self, 'source_origin', source_origin)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"source={self.source!r}")
            parts.append(f"source_path={self.source_path!r}")
            parts.append(f"package_names={self.package_names!r}")
            parts.append(f"package_exports={self.package_exports!r}")
            parts.append(f"source_origin={self.source_origin!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('source',)), EqPlan(fields=('source',)), FrozenPlan(fields=('source',), allow_dyna"
        "mic_dunder_attrs=False), HashPlan(action='add', fields=('source',), cache=False), InitPlan(fields=(InitPlan.Fi"
        "eld(name='source', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init"
        "=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None),), self_par"
        "am='self', std_params=('source',), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fn"
        "s=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='source', kw_only=False, fn=None),), id=False, te"
        "rse=False, default_fn=None)))"
    ),
    plan_repr_sha1='dcd8ef6daf591f79b2063b08958297724da93d59',
    cls_names=(
        ('omdev.js.vendor.models', 'RewriteResult'),
    ),
)
def _process_dataclass__dcd8ef6daf591f79b2063b08958297724da93d59():
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
                source=self.source,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.source == other.source
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'source',
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
                self.source,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            source: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'source', source)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"source={self.source!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('name', 'version')), EqPlan(fields=('name', 'version')), FrozenPlan(fields=('name'"
        ", 'version'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('name', 'version'), cache=Fals"
        "e), InitPlan(fields=(InitPlan.Field(name='name', annotation=OpRef(name='init.fields.0.annotation'), default=No"
        "ne, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None"
        ", check_type=None), InitPlan.Field(name='version', annotation=OpRef(name='init.fields.1.annotation'), default="
        "None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=No"
        "ne, check_type=None)), self_param='self', std_params=('name', 'version'), kw_only_params=(), frozen=True, slot"
        "s=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='name', kw"
        "_only=False, fn=None), ReprPlan.Field(name='version', kw_only=False, fn=None)), id=False, terse=False, default"
        "_fn=None)))"
    ),
    plan_repr_sha1='92b47fb609290ba0232ec446215ac6fcdf6c4283',
    cls_names=(
        ('omdev.js.vendor.models', 'RootPackage'),
    ),
)
def _process_dataclass__92b47fb609290ba0232ec446215ac6fcdf6c4283():
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
                name=self.name,
                version=self.version,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.version == other.version
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'version',
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
                self.version,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            name: __dataclass__init__fields__0__annotation,
            version: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'version', version)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"version={self.version!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('manifest', 'packages', 'registry')), EqPlan(fields=('manifest', 'packages', 'regi"
        "stry')), FrozenPlan(fields=('manifest', 'packages', 'registry'), allow_dynamic_dunder_attrs=False), HashPlan(a"
        "ction='add', fields=('manifest', 'packages', 'registry'), cache=False), InitPlan(fields=(InitPlan.Field(name='"
        "manifest', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, o"
        "verride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(nam"
        "e='packages', annotation=OpRef(name='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), "
        "default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, ch"
        "eck_type=None), InitPlan.Field(name='registry', annotation=OpRef(name='init.fields.2.annotation'), default=Non"
        "e, default_factory=OpRef(name='init.fields.2.default_factory'), init=True, override=False, field_type=FieldTyp"
        "e.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('manifest', 'package"
        "s', 'registry'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns"
        "=()), ReprPlan(fields=(ReprPlan.Field(name='manifest', kw_only=False, fn=None), ReprPlan.Field(name='packages'"
        ", kw_only=False, fn=None), ReprPlan.Field(name='registry', kw_only=False, fn=None)), id=False, terse=False, de"
        "fault_fn=None)))"
    ),
    plan_repr_sha1='247a561f8229cf564d9d668b721735327198a57d',
    cls_names=(
        ('omdev.js.vendor.models', 'UpdateRequest'),
    ),
)
def _process_dataclass__247a561f8229cf564d9d668b721735327198a57d():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
        __dataclass__init__fields__2__annotation,
        __dataclass__init__fields__2__default_factory,
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
                manifest=self.manifest,
                packages=self.packages,
                registry=self.registry,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.manifest == other.manifest and
                self.packages == other.packages and
                self.registry == other.registry
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'manifest',
            'packages',
            'registry',
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
                self.manifest,
                self.packages,
                self.registry,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            manifest: __dataclass__init__fields__0__annotation,
            packages: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            registry: __dataclass__init__fields__2__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if registry is __dataclass__HAS_DEFAULT_FACTORY:
                registry = __dataclass__init__fields__2__default_factory()
            __dataclass__object_setattr(self, 'manifest', manifest)
            __dataclass__object_setattr(self, 'packages', packages)
            __dataclass__object_setattr(self, 'registry', registry)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"manifest={self.manifest!r}")
            parts.append(f"packages={self.packages!r}")
            parts.append(f"registry={self.registry!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('format_version', 'roots', 'packages', 'files')), EqPlan(fields=('format_version',"
        " 'roots', 'packages', 'files')), FrozenPlan(fields=('format_version', 'roots', 'packages', 'files'), allow_dyn"
        "amic_dunder_attrs=False), HashPlan(action='add', fields=('format_version', 'roots', 'packages', 'files'), cach"
        "e=False), InitPlan(fields=(InitPlan.Field(name='format_version', annotation=OpRef(name='init.fields.0.annotati"
        "on'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=Non"
        "e, validate=None, check_type=None), InitPlan.Field(name='roots', annotation=OpRef(name='init.fields.1.annotati"
        "on'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=Non"
        "e, validate=None, check_type=None), InitPlan.Field(name='packages', annotation=OpRef(name='init.fields.2.annot"
        "ation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce="
        "None, validate=None, check_type=None), InitPlan.Field(name='files', annotation=OpRef(name='init.fields.3.annot"
        "ation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce="
        "None, validate=None, check_type=None)), self_param='self', std_params=('format_version', 'roots', 'packages', "
        "'files'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), R"
        "eprPlan(fields=(ReprPlan.Field(name='format_version', kw_only=False, fn=None), ReprPlan.Field(name='roots', kw"
        "_only=False, fn=None), ReprPlan.Field(name='packages', kw_only=False, fn=None), ReprPlan.Field(name='files', k"
        "w_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='ebc226cea868fdf108b27b290f271d3a4bae1202',
    cls_names=(
        ('omdev.js.vendor.models', 'VendorLock'),
    ),
)
def _process_dataclass__ebc226cea868fdf108b27b290f271d3a4bae1202():
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
                format_version=self.format_version,
                roots=self.roots,
                packages=self.packages,
                files=self.files,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.format_version == other.format_version and
                self.roots == other.roots and
                self.packages == other.packages and
                self.files == other.files
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'format_version',
            'roots',
            'packages',
            'files',
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
                self.format_version,
                self.roots,
                self.packages,
                self.files,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            format_version: __dataclass__init__fields__0__annotation,
            roots: __dataclass__init__fields__1__annotation,
            packages: __dataclass__init__fields__2__annotation,
            files: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'format_version', format_version)
            __dataclass__object_setattr(self, 'roots', roots)
            __dataclass__object_setattr(self, 'packages', packages)
            __dataclass__object_setattr(self, 'files', files)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"format_version={self.format_version!r}")
            parts.append(f"roots={self.roots!r}")
            parts.append(f"packages={self.packages!r}")
            parts.append(f"files={self.files!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('format_version', 'roots')), EqPlan(fields=('format_version', 'roots')), FrozenPla"
        "n(fields=('format_version', 'roots'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('forma"
        "t_version', 'roots'), cache=False), InitPlan(fields=(InitPlan.Field(name='format_version', annotation=OpRef(na"
        "me='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=Fiel"
        "dType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='roots', annotation=OpRef(na"
        "me='init.fields.1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=Fiel"
        "dType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('format_version'"
        ", 'roots'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()),"
        " ReprPlan(fields=(ReprPlan.Field(name='format_version', kw_only=False, fn=None), ReprPlan.Field(name='roots', "
        "kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='ee2c90a52f82cb4f54eee0157de234f1608b0951',
    cls_names=(
        ('omdev.js.vendor.models', 'VendorManifest'),
    ),
)
def _process_dataclass__ee2c90a52f82cb4f54eee0157de234f1608b0951():
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
                format_version=self.format_version,
                roots=self.roots,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.format_version == other.format_version and
                self.roots == other.roots
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'format_version',
            'roots',
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
                self.format_version,
                self.roots,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            format_version: __dataclass__init__fields__0__annotation,
            roots: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'format_version', format_version)
            __dataclass__object_setattr(self, 'roots', roots)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"format_version={self.format_version!r}")
            parts.append(f"roots={self.roots!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('manifest', 'lock', 'destination', 'cache_directory')), EqPlan(fields=('manifest',"
        " 'lock', 'destination', 'cache_directory')), FrozenPlan(fields=('manifest', 'lock', 'destination', 'cache_dire"
        "ctory'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('manifest', 'lock', 'destination', "
        "'cache_directory'), cache=False), InitPlan(fields=(InitPlan.Field(name='manifest', annotation=OpRef(name='init"
        ".fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.IN"
        "STANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='lock', annotation=OpRef(name='init."
        "fields.1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INS"
        "TANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='destination', annotation=OpRef(name="
        "'init.fields.2.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldTy"
        "pe.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='cache_directory', annotation=O"
        "pRef(name='init.fields.3.annotation'), default=None, default_factory=None, init=True, override=False, field_ty"
        "pe=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('manifest"
        "', 'lock', 'destination', 'cache_directory'), kw_only_params=(), frozen=True, slots=False, post_init_params=No"
        "ne, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='manifest', kw_only=False, fn=None), R"
        "eprPlan.Field(name='lock', kw_only=False, fn=None), ReprPlan.Field(name='destination', kw_only=False, fn=None)"
        ", ReprPlan.Field(name='cache_directory', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='4abf99bfbf995fc0c52ee77e4817ce866250bb74',
    cls_names=(
        ('omdev.js.vendor.models', 'VendorRequest'),
    ),
)
def _process_dataclass__4abf99bfbf995fc0c52ee77e4817ce866250bb74():
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
                manifest=self.manifest,
                lock=self.lock,
                destination=self.destination,
                cache_directory=self.cache_directory,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.manifest == other.manifest and
                self.lock == other.lock and
                self.destination == other.destination and
                self.cache_directory == other.cache_directory
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'manifest',
            'lock',
            'destination',
            'cache_directory',
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
                self.manifest,
                self.lock,
                self.destination,
                self.cache_directory,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            manifest: __dataclass__init__fields__0__annotation,
            lock: __dataclass__init__fields__1__annotation,
            destination: __dataclass__init__fields__2__annotation,
            cache_directory: __dataclass__init__fields__3__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'manifest', manifest)
            __dataclass__object_setattr(self, 'lock', lock)
            __dataclass__object_setattr(self, 'destination', destination)
            __dataclass__object_setattr(self, 'cache_directory', cache_directory)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"manifest={self.manifest!r}")
            parts.append(f"lock={self.lock!r}")
            parts.append(f"destination={self.destination!r}")
            parts.append(f"cache_directory={self.cache_directory!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('destination', 'package_count', 'file_count')), EqPlan(fields=('destination', 'pac"
        "kage_count', 'file_count')), FrozenPlan(fields=('destination', 'package_count', 'file_count'), allow_dynamic_d"
        "under_attrs=False), HashPlan(action='add', fields=('destination', 'package_count', 'file_count'), cache=False)"
        ", InitPlan(fields=(InitPlan.Field(name='destination', annotation=OpRef(name='init.fields.0.annotation'), defau"
        "lt=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate"
        "=None, check_type=None), InitPlan.Field(name='package_count', annotation=OpRef(name='init.fields.1.annotation'"
        "), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, "
        "validate=None, check_type=None), InitPlan.Field(name='file_count', annotation=OpRef(name='init.fields.2.annota"
        "tion'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=N"
        "one, validate=None, check_type=None)), self_param='self', std_params=('destination', 'package_count', 'file_co"
        "unt'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), Repr"
        "Plan(fields=(ReprPlan.Field(name='destination', kw_only=False, fn=None), ReprPlan.Field(name='package_count', "
        "kw_only=False, fn=None), ReprPlan.Field(name='file_count', kw_only=False, fn=None)), id=False, terse=False, de"
        "fault_fn=None)))"
    ),
    plan_repr_sha1='87d4cc03060a728104c526ffee0cc21ff3235af4',
    cls_names=(
        ('omdev.js.vendor.models', 'VendorResult'),
    ),
)
def _process_dataclass__87d4cc03060a728104c526ffee0cc21ff3235af4():
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
                destination=self.destination,
                package_count=self.package_count,
                file_count=self.file_count,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.destination == other.destination and
                self.package_count == other.package_count and
                self.file_count == other.file_count
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'destination',
            'package_count',
            'file_count',
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
                self.destination,
                self.package_count,
                self.file_count,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            destination: __dataclass__init__fields__0__annotation,
            package_count: __dataclass__init__fields__1__annotation,
            file_count: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'destination', destination)
            __dataclass__object_setattr(self, 'package_count', package_count)
            __dataclass__object_setattr(self, 'file_count', file_count)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"destination={self.destination!r}")
            parts.append(f"package_count={self.package_count!r}")
            parts.append(f"file_count={self.file_count!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('manifest', 'lock', 'destination')), EqPlan(fields=('manifest', 'lock', 'destinati"
        "on')), FrozenPlan(fields=('manifest', 'lock', 'destination'), allow_dynamic_dunder_attrs=False), HashPlan(acti"
        "on='add', fields=('manifest', 'lock', 'destination'), cache=False), InitPlan(fields=(InitPlan.Field(name='mani"
        "fest', annotation=OpRef(name='init.fields.0.annotation'), default=None, default_factory=None, init=True, overr"
        "ide=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='l"
        "ock', annotation=OpRef(name='init.fields.1.annotation'), default=None, default_factory=None, init=True, overri"
        "de=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='de"
        "stination', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, "
        "override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self"
        "', std_params=('manifest', 'lock', 'destination'), kw_only_params=(), frozen=True, slots=False, post_init_para"
        "ms=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='manifest', kw_only=False, fn=Non"
        "e), ReprPlan.Field(name='lock', kw_only=False, fn=None), ReprPlan.Field(name='destination', kw_only=False, fn="
        "None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='cd432edce27d444c15aa95d80e67f06736a99e70',
    cls_names=(
        ('omdev.js.vendor.models', 'VerifyRequest'),
    ),
)
def _process_dataclass__cd432edce27d444c15aa95d80e67f06736a99e70():
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
                manifest=self.manifest,
                lock=self.lock,
                destination=self.destination,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.manifest == other.manifest and
                self.lock == other.lock and
                self.destination == other.destination
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'manifest',
            'lock',
            'destination',
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
                self.manifest,
                self.lock,
                self.destination,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            manifest: __dataclass__init__fields__0__annotation,
            lock: __dataclass__init__fields__1__annotation,
            destination: __dataclass__init__fields__2__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'manifest', manifest)
            __dataclass__object_setattr(self, 'lock', lock)
            __dataclass__object_setattr(self, 'destination', destination)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"manifest={self.manifest!r}")
            parts.append(f"lock={self.lock!r}")
            parts.append(f"destination={self.destination!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('destination', 'package_count', 'file_count', 'module_count', 'import_count')), Eq"
        "Plan(fields=('destination', 'package_count', 'file_count', 'module_count', 'import_count')), FrozenPlan(fields"
        "=('destination', 'package_count', 'file_count', 'module_count', 'import_count'), allow_dynamic_dunder_attrs=Fa"
        "lse), HashPlan(action='add', fields=('destination', 'package_count', 'file_count', 'module_count', 'import_cou"
        "nt'), cache=False), InitPlan(fields=(InitPlan.Field(name='destination', annotation=OpRef(name='init.fields.0.a"
        "nnotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coe"
        "rce=None, validate=None, check_type=None), InitPlan.Field(name='package_count', annotation=OpRef(name='init.fi"
        "elds.1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTA"
        "NCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='file_count', annotation=OpRef(name='in"
        "it.fields.2.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType."
        "INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='module_count', annotation=OpRef(n"
        "ame='init.fields.3.annotation'), default=None, default_factory=None, init=True, override=False, field_type=Fie"
        "ldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='import_count', annotation="
        "OpRef(name='init.fields.4.annotation'), default=None, default_factory=None, init=True, override=False, field_t"
        "ype=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std_params=('destina"
        "tion', 'package_count', 'file_count', 'module_count', 'import_count'), kw_only_params=(), frozen=True, slots=F"
        "alse, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='destination'"
        ", kw_only=False, fn=None), ReprPlan.Field(name='package_count', kw_only=False, fn=None), ReprPlan.Field(name='"
        "file_count', kw_only=False, fn=None), ReprPlan.Field(name='module_count', kw_only=False, fn=None), ReprPlan.Fi"
        "eld(name='import_count', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='6f8db8778c90ae8ad1f173b0e8b14f0685f9fb53',
    cls_names=(
        ('omdev.js.vendor.models', 'VerifyResult'),
    ),
)
def _process_dataclass__6f8db8778c90ae8ad1f173b0e8b14f0685f9fb53():
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
                destination=self.destination,
                package_count=self.package_count,
                file_count=self.file_count,
                module_count=self.module_count,
                import_count=self.import_count,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.destination == other.destination and
                self.package_count == other.package_count and
                self.file_count == other.file_count and
                self.module_count == other.module_count and
                self.import_count == other.import_count
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'destination',
            'package_count',
            'file_count',
            'module_count',
            'import_count',
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
                self.destination,
                self.package_count,
                self.file_count,
                self.module_count,
                self.import_count,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            destination: __dataclass__init__fields__0__annotation,
            package_count: __dataclass__init__fields__1__annotation,
            file_count: __dataclass__init__fields__2__annotation,
            module_count: __dataclass__init__fields__3__annotation,
            import_count: __dataclass__init__fields__4__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'destination', destination)
            __dataclass__object_setattr(self, 'package_count', package_count)
            __dataclass__object_setattr(self, 'file_count', file_count)
            __dataclass__object_setattr(self, 'module_count', module_count)
            __dataclass__object_setattr(self, 'import_count', import_count)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"destination={self.destination!r}")
            parts.append(f"package_count={self.package_count!r}")
            parts.append(f"file_count={self.file_count!r}")
            parts.append(f"module_count={self.module_count!r}")
            parts.append(f"import_count={self.import_count!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('manifest', 'packages')), EqPlan(fields=('manifest', 'packages')), FrozenPlan(fiel"
        "ds=('manifest', 'packages'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('manifest', 'pa"
        "ckages'), cache=False), InitPlan(fields=(InitPlan.Field(name='manifest', annotation=OpRef(name='init.fields.0."
        "annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, co"
        "erce=None, validate=None, check_type=None), InitPlan.Field(name='packages', annotation=OpRef(name='init.fields"
        ".1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE,"
        " coerce=None, validate=None, check_type=None)), self_param='self', std_params=('manifest', 'packages'), kw_onl"
        "y_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=("
        "ReprPlan.Field(name='manifest', kw_only=False, fn=None), ReprPlan.Field(name='packages', kw_only=False, fn=Non"
        "e)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='c2c753db529a03784edeeda20f91380db86c2254',
    cls_names=(
        ('omdev.js.vendor.models', 'VersionResolveRequest'),
    ),
)
def _process_dataclass__c2c753db529a03784edeeda20f91380db86c2254():
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
                manifest=self.manifest,
                packages=self.packages,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.manifest == other.manifest and
                self.packages == other.packages
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'manifest',
            'packages',
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
                self.manifest,
                self.packages,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            manifest: __dataclass__init__fields__0__annotation,
            packages: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'manifest', manifest)
            __dataclass__object_setattr(self, 'packages', packages)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"manifest={self.manifest!r}")
            parts.append(f"packages={self.packages!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('kind', 'value', 'start', 'end', 'embedded')), EqPlan(fields=('kind', 'value', 'st"
        "art', 'end', 'embedded')), FrozenPlan(fields=('kind', 'value', 'start', 'end', 'embedded'), allow_dynamic_dund"
        "er_attrs=False), HashPlan(action='add', fields=('kind', 'value', 'start', 'end', 'embedded'), cache=False), In"
        "itPlan(fields=(InitPlan.Field(name='kind', annotation=OpRef(name='init.fields.0.annotation'), default=None, de"
        "fault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, chec"
        "k_type=None), InitPlan.Field(name='value', annotation=OpRef(name='init.fields.1.annotation'), default=None, de"
        "fault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, chec"
        "k_type=None), InitPlan.Field(name='start', annotation=OpRef(name='init.fields.2.annotation'), default=None, de"
        "fault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, chec"
        "k_type=None), InitPlan.Field(name='end', annotation=OpRef(name='init.fields.3.annotation'), default=None, defa"
        "ult_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_"
        "type=None), InitPlan.Field(name='embedded', annotation=OpRef(name='init.fields.4.annotation'), default=None, d"
        "efault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, che"
        "ck_type=None)), self_param='self', std_params=('kind', 'value', 'start', 'end', 'embedded'), kw_only_params=()"
        ", frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Fi"
        "eld(name='kind', kw_only=False, fn=None), ReprPlan.Field(name='value', kw_only=False, fn=None), ReprPlan.Field"
        "(name='start', kw_only=False, fn=None), ReprPlan.Field(name='end', kw_only=False, fn=None), ReprPlan.Field(nam"
        "e='embedded', kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='f93ca8aee3e814dc76bbe8d6e7bcd984bf6469e4',
    cls_names=(
        ('omdev.js.vendor.parsing', '_Token'),
    ),
)
def _process_dataclass__f93ca8aee3e814dc76bbe8d6e7bcd984bf6469e4():
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
                kind=self.kind,
                value=self.value,
                start=self.start,
                end=self.end,
                embedded=self.embedded,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.kind == other.kind and
                self.value == other.value and
                self.start == other.start and
                self.end == other.end and
                self.embedded == other.embedded
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'kind',
            'value',
            'start',
            'end',
            'embedded',
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
                self.kind,
                self.value,
                self.start,
                self.end,
                self.embedded,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            kind: __dataclass__init__fields__0__annotation,
            value: __dataclass__init__fields__1__annotation,
            start: __dataclass__init__fields__2__annotation,
            end: __dataclass__init__fields__3__annotation,
            embedded: __dataclass__init__fields__4__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'kind', kind)
            __dataclass__object_setattr(self, 'value', value)
            __dataclass__object_setattr(self, 'start', start)
            __dataclass__object_setattr(self, 'end', end)
            __dataclass__object_setattr(self, 'embedded', embedded)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"kind={self.kind!r}")
            parts.append(f"value={self.value!r}")
            parts.append(f"start={self.start!r}")
            parts.append(f"end={self.end!r}")
            parts.append(f"embedded={self.embedded!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('expression', 'source')), EqPlan(fields=('expression', 'source')), FrozenPlan(fiel"
        "ds=('expression', 'source'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('expression', '"
        "source'), cache=False), InitPlan(fields=(InitPlan.Field(name='expression', annotation=OpRef(name='init.fields."
        "0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, "
        "coerce=None, validate=None, check_type=None), InitPlan.Field(name='source', annotation=OpRef(name='init.fields"
        ".1.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE,"
        " coerce=None, validate=None, check_type=None)), self_param='self', std_params=('expression', 'source'), kw_onl"
        "y_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=("
        "ReprPlan.Field(name='expression', kw_only=False, fn=None), ReprPlan.Field(name='source', kw_only=False, fn=Non"
        "e)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='03f1bc2d0ef6cab6591db730b0742873e7e33aa7',
    cls_names=(
        ('omdev.js.vendor.resolution', '_Constraint'),
    ),
)
def _process_dataclass__03f1bc2d0ef6cab6591db730b0742873e7e33aa7():
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
                expression=self.expression,
                source=self.source,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.expression == other.expression and
                self.source == other.source
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'expression',
            'source',
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
                self.expression,
                self.source,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            expression: __dataclass__init__fields__0__annotation,
            source: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'expression', expression)
            __dataclass__object_setattr(self, 'source', source)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"expression={self.expression!r}")
            parts.append(f"source={self.source!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('major', 'minor', 'patch', 'prerelease', 'build')), EqPlan(fields=('major', 'minor"
        "', 'patch', 'prerelease', 'build')), FrozenPlan(fields=('major', 'minor', 'patch', 'prerelease', 'build'), all"
        "ow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('major', 'minor', 'patch', 'prerelease', 'build"
        "'), cache=False), InitPlan(fields=(InitPlan.Field(name='major', annotation=OpRef(name='init.fields.0.annotatio"
        "n'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None"
        ", validate=None, check_type=None), InitPlan.Field(name='minor', annotation=OpRef(name='init.fields.1.annotatio"
        "n'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None"
        ", validate=None, check_type=None), InitPlan.Field(name='patch', annotation=OpRef(name='init.fields.2.annotatio"
        "n'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None"
        ", validate=None, check_type=None), InitPlan.Field(name='prerelease', annotation=OpRef(name='init.fields.3.anno"
        "tation'), default=OpRef(name='init.fields.3.default'), default_factory=None, init=True, override=False, field_"
        "type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='build', annotation"
        "=OpRef(name='init.fields.4.annotation'), default=OpRef(name='init.fields.4.default'), default_factory=None, in"
        "it=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_pa"
        "ram='self', std_params=('major', 'minor', 'patch', 'prerelease', 'build'), kw_only_params=(), frozen=True, slo"
        "ts=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='major', "
        "kw_only=False, fn=None), ReprPlan.Field(name='minor', kw_only=False, fn=None), ReprPlan.Field(name='patch', kw"
        "_only=False, fn=None), ReprPlan.Field(name='prerelease', kw_only=False, fn=None), ReprPlan.Field(name='build',"
        " kw_only=False, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='a0fe772b2d75896a8104c85cc3c3e72a73c375c4',
    cls_names=(
        ('omdev.js.vendor.semver', 'Version'),
    ),
)
def _process_dataclass__a0fe772b2d75896a8104c85cc3c3e72a73c375c4():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__2__annotation,
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
                major=self.major,
                minor=self.minor,
                patch=self.patch,
                prerelease=self.prerelease,
                build=self.build,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.major == other.major and
                self.minor == other.minor and
                self.patch == other.patch and
                self.prerelease == other.prerelease and
                self.build == other.build
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'major',
            'minor',
            'patch',
            'prerelease',
            'build',
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
                self.major,
                self.minor,
                self.patch,
                self.prerelease,
                self.build,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            major: __dataclass__init__fields__0__annotation,
            minor: __dataclass__init__fields__1__annotation,
            patch: __dataclass__init__fields__2__annotation,
            prerelease: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            build: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'major', major)
            __dataclass__object_setattr(self, 'minor', minor)
            __dataclass__object_setattr(self, 'patch', patch)
            __dataclass__object_setattr(self, 'prerelease', prerelease)
            __dataclass__object_setattr(self, 'build', build)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"major={self.major!r}")
            parts.append(f"minor={self.minor!r}")
            parts.append(f"patch={self.patch!r}")
            parts.append(f"prerelease={self.prerelease!r}")
            parts.append(f"build={self.build!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('operator', 'version')), EqPlan(fields=('operator', 'version')), FrozenPlan(fields"
        "=('operator', 'version'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('operator', 'versi"
        "on'), cache=False), InitPlan(fields=(InitPlan.Field(name='operator', annotation=OpRef(name='init.fields.0.anno"
        "tation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce"
        "=None, validate=None, check_type=None), InitPlan.Field(name='version', annotation=OpRef(name='init.fields.1.an"
        "notation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coer"
        "ce=None, validate=None, check_type=None)), self_param='self', std_params=('operator', 'version'), kw_only_para"
        "ms=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPl"
        "an.Field(name='operator', kw_only=False, fn=None), ReprPlan.Field(name='version', kw_only=False, fn=None)), id"
        "=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='54925802936476d26e2862bc26ba3f8933a563bf',
    cls_names=(
        ('omdev.js.vendor.semver', '_Comparator'),
    ),
)
def _process_dataclass__54925802936476d26e2862bc26ba3f8933a563bf():
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
                operator=self.operator,
                version=self.version,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.operator == other.operator and
                self.version == other.version
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'operator',
            'version',
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
                self.operator,
                self.version,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            operator: __dataclass__init__fields__0__annotation,
            version: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'operator', operator)
            __dataclass__object_setattr(self, 'version', version)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"operator={self.operator!r}")
            parts.append(f"version={self.version!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('major', 'minor', 'patch', 'prerelease', 'build')), EqPlan(fields=('major', 'minor"
        "', 'patch', 'prerelease', 'build')), FrozenPlan(fields=('major', 'minor', 'patch', 'prerelease', 'build'), all"
        "ow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('major', 'minor', 'patch', 'prerelease', 'build"
        "'), cache=False), InitPlan(fields=(InitPlan.Field(name='major', annotation=OpRef(name='init.fields.0.annotatio"
        "n'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None"
        ", validate=None, check_type=None), InitPlan.Field(name='minor', annotation=OpRef(name='init.fields.1.annotatio"
        "n'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None"
        ", validate=None, check_type=None), InitPlan.Field(name='patch', annotation=OpRef(name='init.fields.2.annotatio"
        "n'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None"
        ", validate=None, check_type=None), InitPlan.Field(name='prerelease', annotation=OpRef(name='init.fields.3.anno"
        "tation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce"
        "=None, validate=None, check_type=None), InitPlan.Field(name='build', annotation=OpRef(name='init.fields.4.anno"
        "tation'), default=None, default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce"
        "=None, validate=None, check_type=None)), self_param='self', std_params=('major', 'minor', 'patch', 'prerelease"
        "', 'build'), kw_only_params=(), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=())"
        ", ReprPlan(fields=(ReprPlan.Field(name='major', kw_only=False, fn=None), ReprPlan.Field(name='minor', kw_only="
        "False, fn=None), ReprPlan.Field(name='patch', kw_only=False, fn=None), ReprPlan.Field(name='prerelease', kw_on"
        "ly=False, fn=None), ReprPlan.Field(name='build', kw_only=False, fn=None)), id=False, terse=False, default_fn=N"
        "one)))"
    ),
    plan_repr_sha1='fea238ddfd33c457390fe11e7ae7af09bb20fda8',
    cls_names=(
        ('omdev.js.vendor.semver', '_PartialVersion'),
    ),
)
def _process_dataclass__fea238ddfd33c457390fe11e7ae7af09bb20fda8():
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
                major=self.major,
                minor=self.minor,
                patch=self.patch,
                prerelease=self.prerelease,
                build=self.build,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.major == other.major and
                self.minor == other.minor and
                self.patch == other.patch and
                self.prerelease == other.prerelease and
                self.build == other.build
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'major',
            'minor',
            'patch',
            'prerelease',
            'build',
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
                self.major,
                self.minor,
                self.patch,
                self.prerelease,
                self.build,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            major: __dataclass__init__fields__0__annotation,
            minor: __dataclass__init__fields__1__annotation,
            patch: __dataclass__init__fields__2__annotation,
            prerelease: __dataclass__init__fields__3__annotation,
            build: __dataclass__init__fields__4__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'major', major)
            __dataclass__object_setattr(self, 'minor', minor)
            __dataclass__object_setattr(self, 'patch', patch)
            __dataclass__object_setattr(self, 'prerelease', prerelease)
            __dataclass__object_setattr(self, 'build', build)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"major={self.major!r}")
            parts.append(f"minor={self.minor!r}")
            parts.append(f"patch={self.patch!r}")
            parts.append(f"prerelease={self.prerelease!r}")
            parts.append(f"build={self.build!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
