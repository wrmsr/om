# @om-generated
# type: ignore
# ruff: noqa
# flake8: noqa
import dataclasses
import reprlib
import types


##


REGISTRY_BY_PLAN_REPR = {}
REGISTRY_BY_CLS_NAME = {}


def _register(**kwargs):
    def inner(fn):
        REGISTRY_BY_PLAN_REPR[kwargs['plan_repr']] = (kwargs, fn)
        REGISTRY_BY_CLS_NAME.update({cn: (kwargs, fn) for cn in kwargs['cls_names']})
        return fn
    return inner


##


@_register(
    plan_repr=(
        "Plans(tup=(CopyPlan(fields=('model', 'cwd', 'eval', 'exec', 'allow_ripgrep_execs', 'fs', 'allow_fs_reads', 'we"
        "b', 'url', 'in_memory', 'autoexec', 'immediate', 'verbose', 'browse_type_returns')), EqPlan(fields=('model', '"
        "cwd', 'eval', 'exec', 'allow_ripgrep_execs', 'fs', 'allow_fs_reads', 'web', 'url', 'in_memory', 'autoexec', 'i"
        "mmediate', 'verbose', 'browse_type_returns')), FrozenPlan(fields=('model', 'cwd', 'eval', 'exec', 'allow_ripgr"
        "ep_execs', 'fs', 'allow_fs_reads', 'web', 'url', 'in_memory', 'autoexec', 'immediate', 'verbose', 'browse_type"
        "_returns'), allow_dynamic_dunder_attrs=False), HashPlan(action='add', fields=('model', 'cwd', 'eval', 'exec', "
        "'allow_ripgrep_execs', 'fs', 'allow_fs_reads', 'web', 'url', 'in_memory', 'autoexec', 'immediate', 'verbose', "
        "'browse_type_returns'), cache=False), InitPlan(fields=(InitPlan.Field(name='model', annotation=OpRef(name='ini"
        "t.fields.00.annotation'), default=OpRef(name='init.fields.00.default'), default_factory=None, init=True, overr"
        "ide=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='c"
        "wd', annotation=OpRef(name='init.fields.01.annotation'), default=OpRef(name='init.fields.01.default'), default"
        "_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_typ"
        "e=None), InitPlan.Field(name='eval', annotation=OpRef(name='init.fields.02.annotation'), default=OpRef(name='i"
        "nit.fields.02.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerc"
        "e=None, validate=None, check_type=None), InitPlan.Field(name='exec', annotation=OpRef(name='init.fields.03.ann"
        "otation'), default=OpRef(name='init.fields.03.default'), default_factory=None, init=True, override=False, fiel"
        "d_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='allow_ripgrep_ex"
        "ecs', annotation=OpRef(name='init.fields.04.annotation'), default=OpRef(name='init.fields.04.default'), defaul"
        "t_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_ty"
        "pe=None), InitPlan.Field(name='fs', annotation=OpRef(name='init.fields.05.annotation'), default=OpRef(name='in"
        "it.fields.05.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce"
        "=None, validate=None, check_type=None), InitPlan.Field(name='allow_fs_reads', annotation=OpRef(name='init.fiel"
        "ds.06.annotation'), default=OpRef(name='init.fields.06.default'), default_factory=None, init=True, override=Fa"
        "lse, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='web', a"
        "nnotation=OpRef(name='init.fields.07.annotation'), default=OpRef(name='init.fields.07.default'), default_facto"
        "ry=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None"
        "), InitPlan.Field(name='url', annotation=OpRef(name='init.fields.08.annotation'), default=OpRef(name='init.fie"
        "lds.08.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None,"
        " validate=None, check_type=None), InitPlan.Field(name='in_memory', annotation=OpRef(name='init.fields.09.annot"
        "ation'), default=OpRef(name='init.fields.09.default'), default_factory=None, init=True, override=False, field_"
        "type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='autoexec', annotat"
        "ion=OpRef(name='init.fields.10.annotation'), default=OpRef(name='init.fields.10.default'), default_factory=Non"
        "e, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), Ini"
        "tPlan.Field(name='immediate', annotation=OpRef(name='init.fields.11.annotation'), default=OpRef(name='init.fie"
        "lds.11.default'), default_factory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None,"
        " validate=None, check_type=None), InitPlan.Field(name='verbose', annotation=OpRef(name='init.fields.12.annotat"
        "ion'), default=OpRef(name='init.fields.12.default'), default_factory=None, init=True, override=False, field_ty"
        "pe=FieldType.INSTANCE, coerce=None, validate=None, check_type=None), InitPlan.Field(name='browse_type_returns'"
        ", annotation=OpRef(name='init.fields.13.annotation'), default=OpRef(name='init.fields.13.default'), default_fa"
        "ctory=None, init=True, override=False, field_type=FieldType.INSTANCE, coerce=None, validate=None, check_type=N"
        "one)), self_param='self', std_params=(), kw_only_params=('model', 'cwd', 'eval', 'exec', 'allow_ripgrep_execs'"
        ", 'fs', 'allow_fs_reads', 'web', 'url', 'in_memory', 'autoexec', 'immediate', 'verbose', 'browse_type_returns'"
        "), frozen=True, slots=False, post_init_params=None, init_fns=(), validate_fns=()), ReprPlan(fields=(ReprPlan.F"
        "ield(name='model', kw_only=True, fn=None), ReprPlan.Field(name='cwd', kw_only=True, fn=None), ReprPlan.Field(n"
        "ame='eval', kw_only=True, fn=None), ReprPlan.Field(name='exec', kw_only=True, fn=None), ReprPlan.Field(name='a"
        "llow_ripgrep_execs', kw_only=True, fn=None), ReprPlan.Field(name='fs', kw_only=True, fn=None), ReprPlan.Field("
        "name='allow_fs_reads', kw_only=True, fn=None), ReprPlan.Field(name='web', kw_only=True, fn=None), ReprPlan.Fie"
        "ld(name='url', kw_only=True, fn=None), ReprPlan.Field(name='in_memory', kw_only=True, fn=None), ReprPlan.Field"
        "(name='autoexec', kw_only=True, fn=None), ReprPlan.Field(name='immediate', kw_only=True, fn=None), ReprPlan.Fi"
        "eld(name='verbose', kw_only=True, fn=None), ReprPlan.Field(name='browse_type_returns', kw_only=True, fn=None))"
        ", id=False, terse=False, default_fn=None)))"
    ),
    plan_repr_sha1='9d3c1acf31fa45b2a091624c1a791aead21f6b39',
    cls_names=(
        ('omllm.ui.tui.config', 'Config'),
    ),
)
def _process_dataclass__9d3c1acf31fa45b2a091624c1a791aead21f6b39():
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
        __dataclass__init__fields__13__annotation,
        __dataclass__init__fields__13__default,
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
                browse_type_returns=self.browse_type_returns,
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
                self.verbose == other.verbose and
                self.browse_type_returns == other.browse_type_returns
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
            'browse_type_returns',
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
                self.browse_type_returns,
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
            browse_type_returns: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
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
            __dataclass__object_setattr(self, 'browse_type_returns', browse_type_returns)

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
            parts.append(f"browse_type_returns={self.browse_type_returns!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
