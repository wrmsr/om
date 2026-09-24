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
    installer_sha1='91680b877508bcce8412bc28c1a9fea3377090be',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('model', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('cwd', True, True, None, True, True, False, None), 'instance', 'value', None, Fa"
            "lse, False, False), (('container', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False), (('eval', True, True, None, True, True, False, None), 'instance', 'value', None, Fal"
            "se, False, False), (('exec', True, True, None, True, True, False, None), 'instance', 'value', None, False,"
            " False, False), (('allow_ripgrep_execs', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('fs', True, True, None, True, True, False, None), 'instance', 'value', None,"
            " False, False, False), (('allow_fs_reads', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('web', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('url', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False), (('backend_model_id', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False), (('in_memory', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('jsonl', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False), (('resume', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('autoexec', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False), (('immediate', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('verbose', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('yolo', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),)"
            ", (), (False,)))"
        ),
    ),
    cls_names=(
        ('omllm.ui.tui.config', 'Config'),
    ),
)
def _process_dataclass__91680b877508bcce8412bc28c1a9fea3377090be():
    def _process_dataclass(
        __class__,
        __dataclass__spec,
        __dataclass__ctx,
        __dataclass__globals,
    ):
        __dataclass__init__fields__00__annotation = __dataclass__spec.fields[0].annotation
        __dataclass__init__fields__00__default = __dataclass__spec.fields[0].default.must()
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
        __dataclass__init__fields__15__annotation = __dataclass__spec.fields[15].annotation
        __dataclass__init__fields__15__default = __dataclass__spec.fields[15].default.must()
        __dataclass__init__fields__16__annotation = __dataclass__spec.fields[16].annotation
        __dataclass__init__fields__16__default = __dataclass__spec.fields[16].default.must()
        __dataclass__init__fields__17__annotation = __dataclass__spec.fields[17].annotation
        __dataclass__init__fields__17__default = __dataclass__spec.fields[17].default.must()
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
                cwd=self.cwd,
                container=self.container,
                eval=self.eval,
                exec=self.exec,
                allow_ripgrep_execs=self.allow_ripgrep_execs,
                fs=self.fs,
                allow_fs_reads=self.allow_fs_reads,
                web=self.web,
                url=self.url,
                backend_model_id=self.backend_model_id,
                in_memory=self.in_memory,
                jsonl=self.jsonl,
                resume=self.resume,
                autoexec=self.autoexec,
                immediate=self.immediate,
                verbose=self.verbose,
                yolo=self.yolo,
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
                self.container == other.container and
                self.eval == other.eval and
                self.exec == other.exec and
                self.allow_ripgrep_execs == other.allow_ripgrep_execs and
                self.fs == other.fs and
                self.allow_fs_reads == other.allow_fs_reads and
                self.web == other.web and
                self.url == other.url and
                self.backend_model_id == other.backend_model_id and
                self.in_memory == other.in_memory and
                self.jsonl == other.jsonl and
                self.resume == other.resume and
                self.autoexec == other.autoexec and
                self.immediate == other.immediate and
                self.verbose == other.verbose and
                self.yolo == other.yolo
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'model',
            'cwd',
            'container',
            'eval',
            'exec',
            'allow_ripgrep_execs',
            'fs',
            'allow_fs_reads',
            'web',
            'url',
            'backend_model_id',
            'in_memory',
            'jsonl',
            'resume',
            'autoexec',
            'immediate',
            'verbose',
            'yolo',
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
                self.container,
                self.eval,
                self.exec,
                self.allow_ripgrep_execs,
                self.fs,
                self.allow_fs_reads,
                self.web,
                self.url,
                self.backend_model_id,
                self.in_memory,
                self.jsonl,
                self.resume,
                self.autoexec,
                self.immediate,
                self.verbose,
                self.yolo,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            model: __dataclass__init__fields__00__annotation = __dataclass__init__fields__00__default,
            cwd: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            container: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            eval: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            exec: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            allow_ripgrep_execs: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            fs: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            allow_fs_reads: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            web: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            url: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            backend_model_id: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            in_memory: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            jsonl: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            resume: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            autoexec: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            immediate: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            verbose: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            yolo: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'model', model)
            __dataclass__object_setattr(self, 'cwd', cwd)
            __dataclass__object_setattr(self, 'container', container)
            __dataclass__object_setattr(self, 'eval', eval)
            __dataclass__object_setattr(self, 'exec', exec)
            __dataclass__object_setattr(self, 'allow_ripgrep_execs', allow_ripgrep_execs)
            __dataclass__object_setattr(self, 'fs', fs)
            __dataclass__object_setattr(self, 'allow_fs_reads', allow_fs_reads)
            __dataclass__object_setattr(self, 'web', web)
            __dataclass__object_setattr(self, 'url', url)
            __dataclass__object_setattr(self, 'backend_model_id', backend_model_id)
            __dataclass__object_setattr(self, 'in_memory', in_memory)
            __dataclass__object_setattr(self, 'jsonl', jsonl)
            __dataclass__object_setattr(self, 'resume', resume)
            __dataclass__object_setattr(self, 'autoexec', autoexec)
            __dataclass__object_setattr(self, 'immediate', immediate)
            __dataclass__object_setattr(self, 'verbose', verbose)
            __dataclass__object_setattr(self, 'yolo', yolo)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"model={self.model!r}")
            parts.append(f"cwd={self.cwd!r}")
            parts.append(f"container={self.container!r}")
            parts.append(f"eval={self.eval!r}")
            parts.append(f"exec={self.exec!r}")
            parts.append(f"allow_ripgrep_execs={self.allow_ripgrep_execs!r}")
            parts.append(f"fs={self.fs!r}")
            parts.append(f"allow_fs_reads={self.allow_fs_reads!r}")
            parts.append(f"web={self.web!r}")
            parts.append(f"url={self.url!r}")
            parts.append(f"backend_model_id={self.backend_model_id!r}")
            parts.append(f"in_memory={self.in_memory!r}")
            parts.append(f"jsonl={self.jsonl!r}")
            parts.append(f"resume={self.resume!r}")
            parts.append(f"autoexec={self.autoexec!r}")
            parts.append(f"immediate={self.immediate!r}")
            parts.append(f"verbose={self.verbose!r}")
            parts.append(f"yolo={self.yolo!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='ccd7f1155fc266626a558ba7a57ab4becbe87de5',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, True, False, False, Fals"
            "e, False, True, True), ((('v', True, True, None, True, False, False, None), 'instance', 'missing', None, F"
            "alse, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, True, ()), ((),), (), (Fa"
            "lse,)))"
        ),
    ),
    cls_names=(
        ('omllm.ui.tui.config', 'TargetCwd'),
    ),
)
def _process_dataclass__ccd7f1155fc266626a558ba7a57ab4becbe87de5():
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
