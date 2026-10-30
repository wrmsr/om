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
    installer_sha1='2a45ea38dc686aa20659010123b83845014d39c3',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('names', True, True, None, True, True, False, None), 'instance', 'value', 'cal"
            "lable', False, False, False), (('verbose', True, True, None, True, True, False, None), 'instance', 'value'"
            ", None, False, False, False), (('no_rm', True, True, None, True, True, False, None), 'instance', 'value', "
            "None, False, False, False), (('no_interactive', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('no_tty', True, True, None, True, True, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('detach', True, True, None, True, True, False, None), 'instance', 'val"
            "ue', None, False, False, False), (('mounts', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', 'callable', False, False, False), (('mount_docker_sock', True, True, None, True, True, False, None), '"
            "instance', 'value', None, False, False, False), (('mount_cache', True, True, None, True, True, False, None"
            "), 'instance', 'value', None, False, False, False), (('mount_persist', True, True, None, True, True, False"
            ", None), 'instance', 'value', None, False, False, False), (('mount_git', True, True, None, True, True, Fal"
            "se, None), 'instance', 'value', None, False, False, False), (('clone_mount_git', True, True, None, True, T"
            "rue, False, None), 'instance', 'value', None, False, False, False), (('privileged', True, True, None, True"
            ", True, False, None), 'instance', 'value', None, False, False, False), (('cuda', True, True, None, True, T"
            "rue, False, None), 'instance', 'value', None, False, False, False), (('offline', True, True, None, True, T"
            "rue, False, None), 'instance', 'value', None, False, False, False), (('no_host_platform', True, True, None"
            ", True, True, False, None), 'instance', 'value', None, False, False, False), (('autoexecs', True, True, No"
            "ne, True, True, False, None), 'instance', 'value', 'callable', False, False, False), (('x11', True, True, "
            "None, True, True, False, None), 'instance', 'value', None, False, False, False), (('id', True, True, None,"
            " True, True, False, None), 'instance', 'value', None, False, False, False), (('no_id_label', True, True, N"
            "one, True, True, False, None), 'instance', 'value', None, False, False, False), (('env_secrets', True, Tru"
            "e, None, True, True, False, None), 'instance', 'value', 'callable', False, False, False), (('non_strict_en"
            "v_secrets', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), ("
            "('env_secret_pats', True, True, None, True, True, False, None), 'instance', 'value', 'callable', False, Fa"
            "lse, False), (('shift_uid', True, True, None, True, True, False, None), 'instance', 'value', None, False, "
            "False, False), (('unknown_args', True, True, None, True, True, False, None), 'instance', 'value', 'callabl"
            "e', False, False, False), (('extra_args', True, True, None, True, True, False, None), 'instance', 'value',"
            " 'callable', False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ("
            "(),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.dockerdev.run.args', 'RunArgs'),
    ),
)
def _process_dataclass__2a45ea38dc686aa20659010123b83845014d39c3():
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
        __dataclass__init__fields__16__coerce = __dataclass__spec.fields[16].coerce
        __dataclass__init__fields__16__default = __dataclass__spec.fields[16].default.must()
        __dataclass__init__fields__17__annotation = __dataclass__spec.fields[17].annotation
        __dataclass__init__fields__17__default = __dataclass__spec.fields[17].default.must()
        __dataclass__init__fields__18__annotation = __dataclass__spec.fields[18].annotation
        __dataclass__init__fields__18__default = __dataclass__spec.fields[18].default.must()
        __dataclass__init__fields__19__annotation = __dataclass__spec.fields[19].annotation
        __dataclass__init__fields__19__default = __dataclass__spec.fields[19].default.must()
        __dataclass__init__fields__20__annotation = __dataclass__spec.fields[20].annotation
        __dataclass__init__fields__20__coerce = __dataclass__spec.fields[20].coerce
        __dataclass__init__fields__20__default = __dataclass__spec.fields[20].default.must()
        __dataclass__init__fields__21__annotation = __dataclass__spec.fields[21].annotation
        __dataclass__init__fields__21__default = __dataclass__spec.fields[21].default.must()
        __dataclass__init__fields__22__annotation = __dataclass__spec.fields[22].annotation
        __dataclass__init__fields__22__coerce = __dataclass__spec.fields[22].coerce
        __dataclass__init__fields__22__default = __dataclass__spec.fields[22].default.must()
        __dataclass__init__fields__23__annotation = __dataclass__spec.fields[23].annotation
        __dataclass__init__fields__23__default = __dataclass__spec.fields[23].default.must()
        __dataclass__init__fields__24__annotation = __dataclass__spec.fields[24].annotation
        __dataclass__init__fields__24__coerce = __dataclass__spec.fields[24].coerce
        __dataclass__init__fields__24__default = __dataclass__spec.fields[24].default.must()
        __dataclass__init__fields__25__annotation = __dataclass__spec.fields[25].annotation
        __dataclass__init__fields__25__coerce = __dataclass__spec.fields[25].coerce
        __dataclass__init__fields__25__default = __dataclass__spec.fields[25].default.must()
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
                names=self.names,
                verbose=self.verbose,
                no_rm=self.no_rm,
                no_interactive=self.no_interactive,
                no_tty=self.no_tty,
                detach=self.detach,
                mounts=self.mounts,
                mount_docker_sock=self.mount_docker_sock,
                mount_cache=self.mount_cache,
                mount_persist=self.mount_persist,
                mount_git=self.mount_git,
                clone_mount_git=self.clone_mount_git,
                privileged=self.privileged,
                cuda=self.cuda,
                offline=self.offline,
                no_host_platform=self.no_host_platform,
                autoexecs=self.autoexecs,
                x11=self.x11,
                id=self.id,
                no_id_label=self.no_id_label,
                env_secrets=self.env_secrets,
                non_strict_env_secrets=self.non_strict_env_secrets,
                env_secret_pats=self.env_secret_pats,
                shift_uid=self.shift_uid,
                unknown_args=self.unknown_args,
                extra_args=self.extra_args,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.names == other.names and
                self.verbose == other.verbose and
                self.no_rm == other.no_rm and
                self.no_interactive == other.no_interactive and
                self.no_tty == other.no_tty and
                self.detach == other.detach and
                self.mounts == other.mounts and
                self.mount_docker_sock == other.mount_docker_sock and
                self.mount_cache == other.mount_cache and
                self.mount_persist == other.mount_persist and
                self.mount_git == other.mount_git and
                self.clone_mount_git == other.clone_mount_git and
                self.privileged == other.privileged and
                self.cuda == other.cuda and
                self.offline == other.offline and
                self.no_host_platform == other.no_host_platform and
                self.autoexecs == other.autoexecs and
                self.x11 == other.x11 and
                self.id == other.id and
                self.no_id_label == other.no_id_label and
                self.env_secrets == other.env_secrets and
                self.non_strict_env_secrets == other.non_strict_env_secrets and
                self.env_secret_pats == other.env_secret_pats and
                self.shift_uid == other.shift_uid and
                self.unknown_args == other.unknown_args and
                self.extra_args == other.extra_args
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'names',
            'verbose',
            'no_rm',
            'no_interactive',
            'no_tty',
            'detach',
            'mounts',
            'mount_docker_sock',
            'mount_cache',
            'mount_persist',
            'mount_git',
            'clone_mount_git',
            'privileged',
            'cuda',
            'offline',
            'no_host_platform',
            'autoexecs',
            'x11',
            'id',
            'no_id_label',
            'env_secrets',
            'non_strict_env_secrets',
            'env_secret_pats',
            'shift_uid',
            'unknown_args',
            'extra_args',
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
                self.names,
                self.verbose,
                self.no_rm,
                self.no_interactive,
                self.no_tty,
                self.detach,
                self.mounts,
                self.mount_docker_sock,
                self.mount_cache,
                self.mount_persist,
                self.mount_git,
                self.clone_mount_git,
                self.privileged,
                self.cuda,
                self.offline,
                self.no_host_platform,
                self.autoexecs,
                self.x11,
                self.id,
                self.no_id_label,
                self.env_secrets,
                self.non_strict_env_secrets,
                self.env_secret_pats,
                self.shift_uid,
                self.unknown_args,
                self.extra_args,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            names: __dataclass__init__fields__00__annotation = __dataclass__init__fields__00__default,
            verbose: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            no_rm: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            no_interactive: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            no_tty: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            detach: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            mounts: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            mount_docker_sock: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            mount_cache: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            mount_persist: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            mount_git: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            clone_mount_git: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            privileged: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            cuda: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            offline: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            no_host_platform: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            autoexecs: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            x11: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
            id: __dataclass__init__fields__18__annotation = __dataclass__init__fields__18__default,
            no_id_label: __dataclass__init__fields__19__annotation = __dataclass__init__fields__19__default,
            env_secrets: __dataclass__init__fields__20__annotation = __dataclass__init__fields__20__default,
            non_strict_env_secrets: __dataclass__init__fields__21__annotation = __dataclass__init__fields__21__default,
            env_secret_pats: __dataclass__init__fields__22__annotation = __dataclass__init__fields__22__default,
            shift_uid: __dataclass__init__fields__23__annotation = __dataclass__init__fields__23__default,
            unknown_args: __dataclass__init__fields__24__annotation = __dataclass__init__fields__24__default,
            extra_args: __dataclass__init__fields__25__annotation = __dataclass__init__fields__25__default,
        ) -> __dataclass__None:
            names = __dataclass__init__fields__00__coerce(names)
            mounts = __dataclass__init__fields__06__coerce(mounts)
            autoexecs = __dataclass__init__fields__16__coerce(autoexecs)
            env_secrets = __dataclass__init__fields__20__coerce(env_secrets)
            env_secret_pats = __dataclass__init__fields__22__coerce(env_secret_pats)
            unknown_args = __dataclass__init__fields__24__coerce(unknown_args)
            extra_args = __dataclass__init__fields__25__coerce(extra_args)
            __dataclass__object_setattr(self, 'names', names)
            __dataclass__object_setattr(self, 'verbose', verbose)
            __dataclass__object_setattr(self, 'no_rm', no_rm)
            __dataclass__object_setattr(self, 'no_interactive', no_interactive)
            __dataclass__object_setattr(self, 'no_tty', no_tty)
            __dataclass__object_setattr(self, 'detach', detach)
            __dataclass__object_setattr(self, 'mounts', mounts)
            __dataclass__object_setattr(self, 'mount_docker_sock', mount_docker_sock)
            __dataclass__object_setattr(self, 'mount_cache', mount_cache)
            __dataclass__object_setattr(self, 'mount_persist', mount_persist)
            __dataclass__object_setattr(self, 'mount_git', mount_git)
            __dataclass__object_setattr(self, 'clone_mount_git', clone_mount_git)
            __dataclass__object_setattr(self, 'privileged', privileged)
            __dataclass__object_setattr(self, 'cuda', cuda)
            __dataclass__object_setattr(self, 'offline', offline)
            __dataclass__object_setattr(self, 'no_host_platform', no_host_platform)
            __dataclass__object_setattr(self, 'autoexecs', autoexecs)
            __dataclass__object_setattr(self, 'x11', x11)
            __dataclass__object_setattr(self, 'id', id)
            __dataclass__object_setattr(self, 'no_id_label', no_id_label)
            __dataclass__object_setattr(self, 'env_secrets', env_secrets)
            __dataclass__object_setattr(self, 'non_strict_env_secrets', non_strict_env_secrets)
            __dataclass__object_setattr(self, 'env_secret_pats', env_secret_pats)
            __dataclass__object_setattr(self, 'shift_uid', shift_uid)
            __dataclass__object_setattr(self, 'unknown_args', unknown_args)
            __dataclass__object_setattr(self, 'extra_args', extra_args)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.names)) is not None:
                parts.append(f"names={s}")
            if (s := __dataclass__repr__default_fn(self.verbose)) is not None:
                parts.append(f"verbose={s}")
            if (s := __dataclass__repr__default_fn(self.no_rm)) is not None:
                parts.append(f"no_rm={s}")
            if (s := __dataclass__repr__default_fn(self.no_interactive)) is not None:
                parts.append(f"no_interactive={s}")
            if (s := __dataclass__repr__default_fn(self.no_tty)) is not None:
                parts.append(f"no_tty={s}")
            if (s := __dataclass__repr__default_fn(self.detach)) is not None:
                parts.append(f"detach={s}")
            if (s := __dataclass__repr__default_fn(self.mounts)) is not None:
                parts.append(f"mounts={s}")
            if (s := __dataclass__repr__default_fn(self.mount_docker_sock)) is not None:
                parts.append(f"mount_docker_sock={s}")
            if (s := __dataclass__repr__default_fn(self.mount_cache)) is not None:
                parts.append(f"mount_cache={s}")
            if (s := __dataclass__repr__default_fn(self.mount_persist)) is not None:
                parts.append(f"mount_persist={s}")
            if (s := __dataclass__repr__default_fn(self.mount_git)) is not None:
                parts.append(f"mount_git={s}")
            if (s := __dataclass__repr__default_fn(self.clone_mount_git)) is not None:
                parts.append(f"clone_mount_git={s}")
            if (s := __dataclass__repr__default_fn(self.privileged)) is not None:
                parts.append(f"privileged={s}")
            if (s := __dataclass__repr__default_fn(self.cuda)) is not None:
                parts.append(f"cuda={s}")
            if (s := __dataclass__repr__default_fn(self.offline)) is not None:
                parts.append(f"offline={s}")
            if (s := __dataclass__repr__default_fn(self.no_host_platform)) is not None:
                parts.append(f"no_host_platform={s}")
            if (s := __dataclass__repr__default_fn(self.autoexecs)) is not None:
                parts.append(f"autoexecs={s}")
            if (s := __dataclass__repr__default_fn(self.x11)) is not None:
                parts.append(f"x11={s}")
            if (s := __dataclass__repr__default_fn(self.id)) is not None:
                parts.append(f"id={s}")
            if (s := __dataclass__repr__default_fn(self.no_id_label)) is not None:
                parts.append(f"no_id_label={s}")
            if (s := __dataclass__repr__default_fn(self.env_secrets)) is not None:
                parts.append(f"env_secrets={s}")
            if (s := __dataclass__repr__default_fn(self.non_strict_env_secrets)) is not None:
                parts.append(f"non_strict_env_secrets={s}")
            if (s := __dataclass__repr__default_fn(self.env_secret_pats)) is not None:
                parts.append(f"env_secret_pats={s}")
            if (s := __dataclass__repr__default_fn(self.shift_uid)) is not None:
                parts.append(f"shift_uid={s}")
            if (s := __dataclass__repr__default_fn(self.unknown_args)) is not None:
                parts.append(f"unknown_args={s}")
            if (s := __dataclass__repr__default_fn(self.extra_args)) is not None:
                parts.append(f"extra_args={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='5b99dd94cc312ce96be1497aceb3fda18cfdee5b',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, True, False, False, False, False, False, False, False, 'in"
            "stance', False, False, False), ((('id', True, True, None, True, True, False, None), 'instance', 'missing',"
            " None, False, False, False), (('created_at', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('updated_at', True, True, None, True, True, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('container_id', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('json', True, True, None, True, True, False, None), 'instance', "
            "'missing', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ("
            ")), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.dockerdev.run.db', 'OrmRun'),
    ),
)
def _process_dataclass__5b99dd94cc312ce96be1497aceb3fda18cfdee5b():
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
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                id=self.id,
                created_at=self.created_at,
                updated_at=self.updated_at,
                container_id=self.container_id,
                json=self.json,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.id == other.id and
                self.created_at == other.created_at and
                self.updated_at == other.updated_at and
                self.container_id == other.container_id and
                self.json == other.json
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            *,
            id: __dataclass__init__fields__0__annotation,
            created_at: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            updated_at: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            container_id: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            json: __dataclass__init__fields__4__annotation,
        ) -> __dataclass__None:
            self.id = id
            self.created_at = created_at
            self.updated_at = updated_at
            self.container_id = container_id
            self.json = json

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"id={self.id!r}")
            parts.append(f"created_at={self.created_at!r}")
            parts.append(f"updated_at={self.updated_at!r}")
            parts.append(f"container_id={self.container_id!r}")
            parts.append(f"json={self.json!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b5789bc666b7feb63876ea94973b1a86fe4605f5',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('id', True, True, None, True, False, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('container_id', True, True, None, True, False, False, None), 'instance', 'value"
            "', None, False, False, False), (('cfg', True, True, None, True, False, False, None), 'instance', 'value', "
            "None, False, False, False), (('sha', True, True, None, True, False, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('args', True, True, None, True, False, False, None), 'instance', 'value', None,"
            " False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), ("
            "False,)))"
        ),
    ),
    cls_names=(
        ('omdev.dockerdev.run.db', 'Run'),
    ),
)
def _process_dataclass__b5789bc666b7feb63876ea94973b1a86fe4605f5():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                id=self.id,
                container_id=self.container_id,
                cfg=self.cfg,
                sha=self.sha,
                args=self.args,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.id == other.id and
                self.container_id == other.container_id and
                self.cfg == other.cfg and
                self.sha == other.sha and
                self.args == other.args
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'id',
            'container_id',
            'cfg',
            'sha',
            'args',
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
                self.id,
                self.container_id,
                self.cfg,
                self.sha,
                self.args,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            id: __dataclass__init__fields__0__annotation,
            container_id: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            cfg: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            sha: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
            args: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'id', id)
            __dataclass__object_setattr(self, 'container_id', container_id)
            __dataclass__object_setattr(self, 'cfg', cfg)
            __dataclass__object_setattr(self, 'sha', sha)
            __dataclass__object_setattr(self, 'args', args)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"id={self.id!r}")
            parts.append(f"container_id={self.container_id!r}")
            parts.append(f"cfg={self.cfg!r}")
            parts.append(f"sha={self.sha!r}")
            parts.append(f"args={self.args!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='72a12bb3cd03e128c2f5d032d7ed0a5c9397a10c',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('platform_system', True, True, None, True, True, False, None), 'instance', 'mi"
            "ssing', None, False, False, False), (('sys_platform', True, True, None, True, True, False, None), 'instanc"
            "e', 'missing', None, False, False, False), (('home', True, True, None, True, True, False, None), 'instance"
            "', 'value', None, False, False, False), (('cwd', True, True, None, True, True, False, None), 'instance', '"
            "missing', None, False, False, False), (('load_secrets', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('mkdtemp', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, Fals"
            "e, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.dockerdev.run.plans', 'RunHost'),
    ),
)
def _process_dataclass__72a12bb3cd03e128c2f5d032d7ed0a5c9397a10c():
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
                platform_system=self.platform_system,
                sys_platform=self.sys_platform,
                home=self.home,
                cwd=self.cwd,
                load_secrets=self.load_secrets,
                mkdtemp=self.mkdtemp,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.platform_system == other.platform_system and
                self.sys_platform == other.sys_platform and
                self.home == other.home and
                self.cwd == other.cwd and
                self.load_secrets == other.load_secrets and
                self.mkdtemp == other.mkdtemp
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'platform_system',
            'sys_platform',
            'home',
            'cwd',
            'load_secrets',
            'mkdtemp',
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
                self.platform_system,
                self.sys_platform,
                self.home,
                self.cwd,
                self.load_secrets,
                self.mkdtemp,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            platform_system: __dataclass__init__fields__0__annotation,
            sys_platform: __dataclass__init__fields__1__annotation,
            home: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            cwd: __dataclass__init__fields__3__annotation,
            load_secrets: __dataclass__init__fields__4__annotation = __dataclass__init__fields__4__default,
            mkdtemp: __dataclass__init__fields__5__annotation = __dataclass__init__fields__5__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'platform_system', platform_system)
            __dataclass__object_setattr(self, 'sys_platform', sys_platform)
            __dataclass__object_setattr(self, 'home', home)
            __dataclass__object_setattr(self, 'cwd', cwd)
            __dataclass__object_setattr(self, 'load_secrets', load_secrets)
            __dataclass__object_setattr(self, 'mkdtemp', mkdtemp)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"platform_system={self.platform_system!r}")
            parts.append(f"sys_platform={self.sys_platform!r}")
            parts.append(f"home={self.home!r}")
            parts.append(f"cwd={self.cwd!r}")
            parts.append(f"load_secrets={self.load_secrets!r}")
            parts.append(f"mkdtemp={self.mkdtemp!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='b30b24f24e8f5bed609c5524539ee8d30dab2181',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, True, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('cfg', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('args', True, True, None, True, True, False, None), 'instance', 'missing', None"
            ", False, False, False), (('run_id', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('host', True, True, None, True, True, False, None), 'instance', 'missing', None"
            ", False, False, False), (('options', True, True, None, True, True, False, None), 'instance', 'factory', No"
            "ne, False, False, False), (('autoexec_lines', True, True, None, True, True, False, None), 'instance', 'fac"
            "tory', None, False, False, False), (('autoexec_env', True, True, None, True, True, False, None), 'instance"
            "', 'factory', None, False, False, False), (('entrypoint', True, True, None, True, True, False, None), 'ins"
            "tance', 'value', None, False, False, False), (('client_env', True, True, None, True, True, False, None), '"
            "instance', 'factory', None, False, False, False), (('staging_dir', True, True, None, True, True, False, No"
            "ne), 'instance', 'value', None, False, False, False), (('setup_runs', True, True, None, True, True, False,"
            " None), 'instance', 'factory', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False"
            ",), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.dockerdev.run.plans', 'RunPlan'),
    ),
)
def _process_dataclass__b30b24f24e8f5bed609c5524539ee8d30dab2181():
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
        __dataclass__init__fields__04__default_factory = __dataclass__spec.fields[4].default.must().fn
        __dataclass__init__fields__05__annotation = __dataclass__spec.fields[5].annotation
        __dataclass__init__fields__05__default_factory = __dataclass__spec.fields[5].default.must().fn
        __dataclass__init__fields__06__annotation = __dataclass__spec.fields[6].annotation
        __dataclass__init__fields__06__default_factory = __dataclass__spec.fields[6].default.must().fn
        __dataclass__init__fields__07__annotation = __dataclass__spec.fields[7].annotation
        __dataclass__init__fields__07__default = __dataclass__spec.fields[7].default.must()
        __dataclass__init__fields__08__annotation = __dataclass__spec.fields[8].annotation
        __dataclass__init__fields__08__default_factory = __dataclass__spec.fields[8].default.must().fn
        __dataclass__init__fields__09__annotation = __dataclass__spec.fields[9].annotation
        __dataclass__init__fields__09__default = __dataclass__spec.fields[9].default.must()
        __dataclass__init__fields__10__annotation = __dataclass__spec.fields[10].annotation
        __dataclass__init__fields__10__default_factory = __dataclass__spec.fields[10].default.must().fn
        __dataclass__HAS_DEFAULT_FACTORY = __dataclass__globals['__dataclass__HAS_DEFAULT_FACTORY']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                cfg=self.cfg,
                args=self.args,
                run_id=self.run_id,
                host=self.host,
                options=self.options,
                autoexec_lines=self.autoexec_lines,
                autoexec_env=self.autoexec_env,
                entrypoint=self.entrypoint,
                client_env=self.client_env,
                staging_dir=self.staging_dir,
                setup_runs=self.setup_runs,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.cfg == other.cfg and
                self.args == other.args and
                self.run_id == other.run_id and
                self.host == other.host and
                self.options == other.options and
                self.autoexec_lines == other.autoexec_lines and
                self.autoexec_env == other.autoexec_env and
                self.entrypoint == other.entrypoint and
                self.client_env == other.client_env and
                self.staging_dir == other.staging_dir and
                self.setup_runs == other.setup_runs
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass__set_cls_attr(__class__, '__hash__', None, 'replace')

        def __init__(
            self,
            *,
            cfg: __dataclass__init__fields__00__annotation,
            args: __dataclass__init__fields__01__annotation,
            run_id: __dataclass__init__fields__02__annotation,
            host: __dataclass__init__fields__03__annotation,
            options: __dataclass__init__fields__04__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            autoexec_lines: __dataclass__init__fields__05__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            autoexec_env: __dataclass__init__fields__06__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            entrypoint: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            client_env: __dataclass__init__fields__08__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            staging_dir: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            setup_runs: __dataclass__init__fields__10__annotation = __dataclass__HAS_DEFAULT_FACTORY,
        ) -> __dataclass__None:
            if options is __dataclass__HAS_DEFAULT_FACTORY:
                options = __dataclass__init__fields__04__default_factory()
            if autoexec_lines is __dataclass__HAS_DEFAULT_FACTORY:
                autoexec_lines = __dataclass__init__fields__05__default_factory()
            if autoexec_env is __dataclass__HAS_DEFAULT_FACTORY:
                autoexec_env = __dataclass__init__fields__06__default_factory()
            if client_env is __dataclass__HAS_DEFAULT_FACTORY:
                client_env = __dataclass__init__fields__08__default_factory()
            if setup_runs is __dataclass__HAS_DEFAULT_FACTORY:
                setup_runs = __dataclass__init__fields__10__default_factory()
            self.cfg = cfg
            self.args = args
            self.run_id = run_id
            self.host = host
            self.options = options
            self.autoexec_lines = autoexec_lines
            self.autoexec_env = autoexec_env
            self.entrypoint = entrypoint
            self.client_env = client_env
            self.staging_dir = staging_dir
            self.setup_runs = setup_runs

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"cfg={self.cfg!r}")
            parts.append(f"args={self.args!r}")
            parts.append(f"run_id={self.run_id!r}")
            parts.append(f"host={self.host!r}")
            parts.append(f"options={self.options!r}")
            parts.append(f"autoexec_lines={self.autoexec_lines!r}")
            parts.append(f"autoexec_env={self.autoexec_env!r}")
            parts.append(f"entrypoint={self.entrypoint!r}")
            parts.append(f"client_env={self.client_env!r}")
            parts.append(f"staging_dir={self.staging_dir!r}")
            parts.append(f"setup_runs={self.setup_runs!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c3f5c5200637330654e937dd6ce0d9c6ac552bb0',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('id', True, True, None, True, False, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('args', True, True, None, True, False, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('env', True, True, None, True, True, False, None), 'instance', 'value', None, F"
            "alse, False, False), (('setup_runs', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), ("
            "False,)))"
        ),
    ),
    cls_names=(
        ('omdev.dockerdev.run.run', 'ProcessedRunArgs'),
    ),
)
def _process_dataclass__c3f5c5200637330654e937dd6ce0d9c6ac552bb0():
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
                id=self.id,
                args=self.args,
                env=self.env,
                setup_runs=self.setup_runs,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.id == other.id and
                self.args == other.args and
                self.env == other.env and
                self.setup_runs == other.setup_runs
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'id',
            'args',
            'env',
            'setup_runs',
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
                self.id,
                self.args,
                self.env,
                self.setup_runs,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            id: __dataclass__init__fields__0__annotation,
            args: __dataclass__init__fields__1__annotation,
            *,
            env: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
            setup_runs: __dataclass__init__fields__3__annotation = __dataclass__init__fields__3__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'id', id)
            __dataclass__object_setattr(self, 'args', args)
            __dataclass__object_setattr(self, 'env', env)
            __dataclass__object_setattr(self, 'setup_runs', setup_runs)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            if (s := __dataclass__repr__default_fn(self.id)) is not None:
                parts.append(f"id={s}")
            if (s := __dataclass__repr__default_fn(self.args)) is not None:
                parts.append(f"args={s}")
            if (s := __dataclass__repr__default_fn(self.env)) is not None:
                parts.append(f"env={s}")
            if (s := __dataclass__repr__default_fn(self.setup_runs)) is not None:
                parts.append(f"setup_runs={s}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
