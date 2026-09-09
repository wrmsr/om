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
        "Plans(tup=(CopyPlan(fields=('model', 'cwd', 'eval', 'exec', 'allow_ripgrep_execs', 'fs', 'allow_fs_reads', 'we"
        "b', 'url', 'in_memory', 'autoexec', 'immediate', 'verbose')), EqPlan(fields=('model', 'cwd', 'eval', 'exec', '"
        "allow_ripgrep_execs', 'fs', 'allow_fs_reads', 'web', 'url', 'in_memory', 'autoexec', 'immediate', 'verbose')),"
        " FrozenPlan(fields=('model', 'cwd', 'eval', 'exec', 'allow_ripgrep_execs', 'fs', 'allow_fs_reads', 'web', 'url"
        "', 'in_memory', 'autoexec', 'immediate', 'verbose'), allow_dynamic_dunder_attrs=False), HashPlan(action='add',"
        " fields=('model', 'cwd', 'eval', 'exec', 'allow_ripgrep_execs', 'fs', 'allow_fs_reads', 'web', 'url', 'in_memo"
        "ry', 'autoexec', 'immediate', 'verbose'), cache=False), InitPlan(fields=(InitPlan.Field(name='model', annotati"
        "on=OpRef(name='init.fields.00.annotation'), default=OpRef(name='init.fields.00.default'), default_factory=None"
        ", init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), Init"
        "Plan.Field(name='cwd', annotation=OpRef(name='init.fields.01.annotation'), default=OpRef(name='init.fields.01."
        "default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, valida"
        "te=None, check_type=None), InitPlan.Field(name='eval', annotation=OpRef(name='init.fields.02.annotation'), def"
        "ault=OpRef(name='init.fields.02.default'), default_factory=None, init=True, override=False, field_type=FieldTy"
        "pe.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='exec', annotation=OpRef(name='"
        "init.fields.03.annotation'), default=OpRef(name='init.fields.03.default'), default_factory=None, init=True, ov"
        "erride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name"
        "='allow_ripgrep_execs', annotation=OpRef(name='init.fields.04.annotation'), default=OpRef(name='init.fields.04"
        ".default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, valid"
        "ate=None, check_type=None), InitPlan.Field(name='fs', annotation=OpRef(name='init.fields.05.annotation'), defa"
        "ult=OpRef(name='init.fields.05.default'), default_factory=None, init=True, override=False, field_type=FieldTyp"
        "e.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='allow_fs_reads', annotation=OpR"
        "ef(name='init.fields.06.annotation'), default=OpRef(name='init.fields.06.default'), default_factory=None, init"
        "=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.F"
        "ield(name='web', annotation=OpRef(name='init.fields.07.annotation'), default=OpRef(name='init.fields.07.defaul"
        "t'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=Non"
        "e, check_type=None), InitPlan.Field(name='url', annotation=OpRef(name='init.fields.08.annotation'), default=Op"
        "Ref(name='init.fields.08.default'), default_factory=None, init=True, override=False, field_type=FieldType.INST"
        "ANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='in_memory', annotation=OpRef(name='in"
        "it.fields.09.annotation'), default=OpRef(name='init.fields.09.default'), default_factory=None, init=True, over"
        "ride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='"
        "autoexec', annotation=OpRef(name='init.fields.10.annotation'), default=OpRef(name='init.fields.10.default'), d"
        "efault_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, che"
        "ck_type=None), InitPlan.Field(name='immediate', annotation=OpRef(name='init.fields.11.annotation'), default=Op"
        "Ref(name='init.fields.11.default'), default_factory=None, init=True, override=False, field_type=FieldType.INST"
        "ANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='verbose', annotation=OpRef(name='init"
        ".fields.12.annotation'), default=OpRef(name='init.fields.12.default'), default_factory=None, init=True, overri"
        "de=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self_param='self', std"
        "_params=(), kw_only_params=('model', 'cwd', 'eval', 'exec', 'allow_ripgrep_execs', 'fs', 'allow_fs_reads', 'we"
        "b', 'url', 'in_memory', 'autoexec', 'immediate', 'verbose'), frozen=True, slots=False, post_init_params=None, "
        "init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.Field(name='model', kw_only=True, fn=None), ReprPlan."
        "Field(name='cwd', kw_only=True, fn=None), ReprPlan.Field(name='eval', kw_only=True, fn=None), ReprPlan.Field(n"
        "ame='exec', kw_only=True, fn=None), ReprPlan.Field(name='allow_ripgrep_execs', kw_only=True, fn=None), ReprPla"
        "n.Field(name='fs', kw_only=True, fn=None), ReprPlan.Field(name='allow_fs_reads', kw_only=True, fn=None), ReprP"
        "lan.Field(name='web', kw_only=True, fn=None), ReprPlan.Field(name='url', kw_only=True, fn=None), ReprPlan.Fiel"
        "d(name='in_memory', kw_only=True, fn=None), ReprPlan.Field(name='autoexec', kw_only=True, fn=None), ReprPlan.F"
        "ield(name='immediate', kw_only=True, fn=None), ReprPlan.Field(name='verbose', kw_only=True, fn=None)), id=Fals"
        "e, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='f81bba624b361d08c053854a4fa921d145292cc3',
    cls_names=(
        ('omllm.ui.tui.config', 'Config'),
    ),
)
def _process_dataclass__f81bba624b361d08c053854a4fa921d145292cc3():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__00__annotation,
        __dataclass__init__fields__00__default,
        __dataclass__init__fields__01__annotation,
        __dataclass__init__fields__01__default,
        __dataclass__init__fields__02__annotation,
        __dataclass__init__fields__02__default,
        __dataclass__init__fields__03__annotation,
        __dataclass__init__fields__03__default,
        __dataclass__init__fields__04__annotation,
        __dataclass__init__fields__04__default,
        __dataclass__init__fields__05__annotation,
        __dataclass__init__fields__05__default,
        __dataclass__init__fields__06__annotation,
        __dataclass__init__fields__06__default,
        __dataclass__init__fields__07__annotation,
        __dataclass__init__fields__07__default,
        __dataclass__init__fields__08__annotation,
        __dataclass__init__fields__08__default,
        __dataclass__init__fields__09__annotation,
        __dataclass__init__fields__09__default,
        __dataclass__init__fields__10__annotation,
        __dataclass__init__fields__10__default,
        __dataclass__init__fields__11__annotation,
        __dataclass__init__fields__11__default,
        __dataclass__init__fields__12__annotation,
        __dataclass__init__fields__12__default,
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
                model=self.model,
                cwd=self.cwd,
                eval=self.eval,
                exec=self.exec,
                allow_ripgrep_execs=self.allow_ripgrep_execs,
                fs=self.fs,
                allow_fs_reads=self.allow_fs_reads,
                web=self.web,
                url=self.url,
                in_memory=self.in_memory,
                autoexec=self.autoexec,
                immediate=self.immediate,
                verbose=self.verbose,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.model == other.model and
                self.cwd == other.cwd and
                self.eval == other.eval and
                self.exec == other.exec and
                self.allow_ripgrep_execs == other.allow_ripgrep_execs and
                self.fs == other.fs and
                self.allow_fs_reads == other.allow_fs_reads and
                self.web == other.web and
                self.url == other.url and
                self.in_memory == other.in_memory and
                self.autoexec == other.autoexec and
                self.immediate == other.immediate and
                self.verbose == other.verbose
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'model',
            'cwd',
            'eval',
            'exec',
            'allow_ripgrep_execs',
            'fs',
            'allow_fs_reads',
            'web',
            'url',
            'in_memory',
            'autoexec',
            'immediate',
            'verbose',
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
                self.cwd,
                self.eval,
                self.exec,
                self.allow_ripgrep_execs,
                self.fs,
                self.allow_fs_reads,
                self.web,
                self.url,
                self.in_memory,
                self.autoexec,
                self.immediate,
                self.verbose,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            model: __dataclass__init__fields__00__annotation = __dataclass__init__fields__00__default,
            cwd: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            eval: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            exec: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            allow_ripgrep_execs: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            fs: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            allow_fs_reads: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            web: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            url: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            in_memory: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            autoexec: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            immediate: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            verbose: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'model', model)
            __dataclass__object_setattr(self, 'cwd', cwd)
            __dataclass__object_setattr(self, 'eval', eval)
            __dataclass__object_setattr(self, 'exec', exec)
            __dataclass__object_setattr(self, 'allow_ripgrep_execs', allow_ripgrep_execs)
            __dataclass__object_setattr(self, 'fs', fs)
            __dataclass__object_setattr(self, 'allow_fs_reads', allow_fs_reads)
            __dataclass__object_setattr(self, 'web', web)
            __dataclass__object_setattr(self, 'url', url)
            __dataclass__object_setattr(self, 'in_memory', in_memory)
            __dataclass__object_setattr(self, 'autoexec', autoexec)
            __dataclass__object_setattr(self, 'immediate', immediate)
            __dataclass__object_setattr(self, 'verbose', verbose)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"model={self.model!r}")
            parts.append(f"cwd={self.cwd!r}")
            parts.append(f"eval={self.eval!r}")
            parts.append(f"exec={self.exec!r}")
            parts.append(f"allow_ripgrep_execs={self.allow_ripgrep_execs!r}")
            parts.append(f"fs={self.fs!r}")
            parts.append(f"allow_fs_reads={self.allow_fs_reads!r}")
            parts.append(f"web={self.web!r}")
            parts.append(f"url={self.url!r}")
            parts.append(f"in_memory={self.in_memory!r}")
            parts.append(f"autoexec={self.autoexec!r}")
            parts.append(f"immediate={self.immediate!r}")
            parts.append(f"verbose={self.verbose!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('name', 'aliases', 'key', 'api_key_name', 'include_platforms', 'exclude_platforms'"
        ")), EqPlan(fields=('name', 'aliases', 'key', 'api_key_name', 'include_platforms', 'exclude_platforms')), Froze"
        "nPlan(fields=('name', 'aliases', 'key', 'api_key_name', 'include_platforms', 'exclude_platforms'), allow_dynam"
        "ic_dunder_attrs=False), HashPlan(action='add', fields=('name', 'aliases', 'key', 'api_key_name', 'include_plat"
        "forms', 'exclude_platforms'), cache=False), InitPlan(fields=(InitPlan.Field(name='name', annotation=OpRef(name"
        "='init.fields.0.annotation'), default=None, default_factory=None, init=True, override=False, field_type=FieldT"
        "ype.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='aliases', annotation=OpRef(na"
        "me='init.fields.1.annotation'), default=OpRef(name='init.fields.1.default'), default_factory=None, init=True, "
        "override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(na"
        "me='key', annotation=OpRef(name='init.fields.2.annotation'), default=None, default_factory=None, init=True, ov"
        "erride=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name"
        "='api_key_name', annotation=OpRef(name='init.fields.3.annotation'), default=OpRef(name='init.fields.3.default'"
        "), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None,"
        " check_type=None), InitPlan.Field(name='include_platforms', annotation=OpRef(name='init.fields.4.annotation'),"
        " default=OpRef(name='init.fields.4.default'), default_factory=None, init=True, override=False, field_type=Fiel"
        "dType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='exclude_platforms', annotat"
        "ion=OpRef(name='init.fields.5.annotation'), default=OpRef(name='init.fields.5.default'), default_factory=None,"
        " init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None)), self"
        "_param='self', std_params=(), kw_only_params=('name', 'aliases', 'key', 'api_key_name', 'include_platforms', '"
        "exclude_platforms'), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan("
        "fields=(ReprPlan.Field(name='name', kw_only=True, fn=None), ReprPlan.Field(name='aliases', kw_only=True, fn=No"
        "ne), ReprPlan.Field(name='key', kw_only=True, fn=None), ReprPlan.Field(name='api_key_name', kw_only=True, fn=N"
        "one), ReprPlan.Field(name='include_platforms', kw_only=True, fn=None), ReprPlan.Field(name='exclude_platforms'"
        ", kw_only=True, fn=None)), id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='9bfe42cfeab864b121f43977f81d2f85588f6ad3',
    cls_names=(
        ('omllm.ui.tui.models', 'Model'),
    ),
)
def _process_dataclass__9bfe42cfeab864b121f43977f81d2f85588f6ad3():
    def _process_dataclass(
        *,
        __class__,
        __dataclass__init__fields__0__annotation,
        __dataclass__init__fields__1__annotation,
        __dataclass__init__fields__1__default,
        __dataclass__init__fields__2__annotation,
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
                name=self.name,
                aliases=self.aliases,
                key=self.key,
                api_key_name=self.api_key_name,
                include_platforms=self.include_platforms,
                exclude_platforms=self.exclude_platforms,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.name == other.name and
                self.aliases == other.aliases and
                self.key == other.key and
                self.api_key_name == other.api_key_name and
                self.include_platforms == other.include_platforms and
                self.exclude_platforms == other.exclude_platforms
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'name',
            'aliases',
            'key',
            'api_key_name',
            'include_platforms',
            'exclude_platforms',
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
                self.aliases,
                self.key,
                self.api_key_name,
                self.include_platforms,
                self.exclude_platforms,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            name: __dataclass__init__fields__0__annotation,
            aliases: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            key: __dataclass__init__fields__2__annotation,
            api_key_name: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            include_platforms: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            exclude_platforms: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'name', name)
            __dataclass__object_setattr(self, 'aliases', aliases)
            __dataclass__object_setattr(self, 'key', key)
            __dataclass__object_setattr(self, 'api_key_name', api_key_name)
            __dataclass__object_setattr(self, 'include_platforms', include_platforms)
            __dataclass__object_setattr(self, 'exclude_platforms', exclude_platforms)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"name={self.name!r}")
            parts.append(f"aliases={self.aliases!r}")
            parts.append(f"key={self.key!r}")
            parts.append(f"api_key_name={self.api_key_name!r}")
            parts.append(f"include_platforms={self.include_platforms!r}")
            parts.append(f"exclude_platforms={self.exclude_platforms!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
