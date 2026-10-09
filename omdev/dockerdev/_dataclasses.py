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
    installer_sha1='ffbc7d6b1d8496146fa0fcaa533c7844a7f7fc77',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('base_image', True, True, None, True, False, False, None), 'instance', 'missi"
            "ng', None, False, False, False), (('base_image_id', True, True, None, True, False, False, None), 'instance"
            "', 'value', None, False, False, False), (('uid', True, True, None, True, False, False, None), 'instance', "
            "'value', None, False, False, False), (('gid', True, True, None, True, False, False, None), 'instance', 'va"
            "lue', None, False, False, False), (('workdir', True, True, None, True, False, False, None), 'instance', 'v"
            "alue', None, False, False, False), (('dep_sets', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False), (('cuda_version', True, True, None, True, True, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('jdks', True, True, None, True, True, False, None), 'instance',"
            " 'value', None, False, False, False), (('nvm_versions', True, True, None, True, True, False, None), 'insta"
            "nce', 'value', None, False, False, False), (('rbenv_versions', True, True, None, True, True, False, None),"
            " 'instance', 'value', None, False, False, False), (('uv_python_versions', True, True, None, True, True, Fa"
            "lse, None), 'instance', 'value', None, False, False, False), (('pyenv_version_keys', True, True, None, Tru"
            "e, True, False, None), 'instance', 'value', None, False, False, False), (('cache_mounts', True, True, None"
            ", True, True, False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (F"
            "alse,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.dockerdev.config', 'Config'),
    ),
)
def _process_dataclass__ffbc7d6b1d8496146fa0fcaa533c7844a7f7fc77():
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
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                base_image=self.base_image,
                base_image_id=self.base_image_id,
                uid=self.uid,
                gid=self.gid,
                workdir=self.workdir,
                dep_sets=self.dep_sets,
                cuda_version=self.cuda_version,
                jdks=self.jdks,
                nvm_versions=self.nvm_versions,
                rbenv_versions=self.rbenv_versions,
                uv_python_versions=self.uv_python_versions,
                pyenv_version_keys=self.pyenv_version_keys,
                cache_mounts=self.cache_mounts,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.base_image == other.base_image and
                self.base_image_id == other.base_image_id and
                self.uid == other.uid and
                self.gid == other.gid and
                self.workdir == other.workdir and
                self.dep_sets == other.dep_sets and
                self.cuda_version == other.cuda_version and
                self.jdks == other.jdks and
                self.nvm_versions == other.nvm_versions and
                self.rbenv_versions == other.rbenv_versions and
                self.uv_python_versions == other.uv_python_versions and
                self.pyenv_version_keys == other.pyenv_version_keys and
                self.cache_mounts == other.cache_mounts
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'base_image',
            'base_image_id',
            'uid',
            'gid',
            'workdir',
            'dep_sets',
            'cuda_version',
            'jdks',
            'nvm_versions',
            'rbenv_versions',
            'uv_python_versions',
            'pyenv_version_keys',
            'cache_mounts',
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
                self.base_image,
                self.base_image_id,
                self.uid,
                self.gid,
                self.workdir,
                self.dep_sets,
                self.cuda_version,
                self.jdks,
                self.nvm_versions,
                self.rbenv_versions,
                self.uv_python_versions,
                self.pyenv_version_keys,
                self.cache_mounts,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            base_image: __dataclass__init__fields__00__annotation,
            base_image_id: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            uid: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            gid: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            workdir: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            *,
            dep_sets: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            cuda_version: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            jdks: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            nvm_versions: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            rbenv_versions: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            uv_python_versions: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            pyenv_version_keys: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            cache_mounts: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'base_image', base_image)
            __dataclass__object_setattr(self, 'base_image_id', base_image_id)
            __dataclass__object_setattr(self, 'uid', uid)
            __dataclass__object_setattr(self, 'gid', gid)
            __dataclass__object_setattr(self, 'workdir', workdir)
            __dataclass__object_setattr(self, 'dep_sets', dep_sets)
            __dataclass__object_setattr(self, 'cuda_version', cuda_version)
            __dataclass__object_setattr(self, 'jdks', jdks)
            __dataclass__object_setattr(self, 'nvm_versions', nvm_versions)
            __dataclass__object_setattr(self, 'rbenv_versions', rbenv_versions)
            __dataclass__object_setattr(self, 'uv_python_versions', uv_python_versions)
            __dataclass__object_setattr(self, 'pyenv_version_keys', pyenv_version_keys)
            __dataclass__object_setattr(self, 'cache_mounts', cache_mounts)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"base_image={self.base_image!r}")
            parts.append(f"base_image_id={self.base_image_id!r}")
            parts.append(f"uid={self.uid!r}")
            parts.append(f"gid={self.gid!r}")
            parts.append(f"workdir={self.workdir!r}")
            parts.append(f"dep_sets={self.dep_sets!r}")
            parts.append(f"cuda_version={self.cuda_version!r}")
            parts.append(f"jdks={self.jdks!r}")
            parts.append(f"nvm_versions={self.nvm_versions!r}")
            parts.append(f"rbenv_versions={self.rbenv_versions!r}")
            parts.append(f"uv_python_versions={self.uv_python_versions!r}")
            parts.append(f"pyenv_version_keys={self.pyenv_version_keys!r}")
            parts.append(f"cache_mounts={self.cache_mounts!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='c8880e8511382bcc92b796853813d2b74426b00f',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('fn', True, True, None, True, False, False, None), 'instance', 'missing', Non"
            "e, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.dockerdev.content', 'LazyContent'),
    ),
)
def _process_dataclass__c8880e8511382bcc92b796853813d2b74426b00f():
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
                fn=self.fn,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.fn == other.fn
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'fn',
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
                self.fn,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            fn: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'fn', fn)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"fn={self.fn!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='625ac4c0cda0f5424cbc5679f0df980830a6c7ce',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('path', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.dockerdev.content', 'Resource'),
        ('omdev.dockerdev.ops', 'Workdir'),
    ),
)
def _process_dataclass__625ac4c0cda0f5424cbc5679f0df980830a6c7ce():
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
                path=self.path,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.path == other.path
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'path',
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
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            path: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'path', path)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"path={self.path!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='78c90d35d12237d630ba8c805ecd2dec24722e5b',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('body', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('env', True, True, None, True, False, False, None), 'instance', 'missing', No"
            "ne, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), ()"
            ", (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.dockerdev.content', 'WithStaticEnv'),
    ),
)
def _process_dataclass__78c90d35d12237d630ba8c805ecd2dec24722e5b():
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
                body=self.body,
                env=self.env,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.body == other.body and
                self.env == other.env
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'body',
            'env',
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
                self.body,
                self.env,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            body: __dataclass__init__fields__0__annotation,
            env: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'body', body)
            __dataclass__object_setattr(self, 'env', env)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"body={self.body!r}")
            parts.append(f"env={self.env!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='74b2c68182e0ad15821fe3bc390648b9e1f938db',
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
        ('omdev.dockerdev.db', 'OrmRun'),
    ),
)
def _process_dataclass__74b2c68182e0ad15821fe3bc390648b9e1f938db():
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
    installer_sha1='47f85b0ab6a8e89b7246ab4b503f246904d768f1',
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
        ('omdev.dockerdev.db', 'Run'),
    ),
)
def _process_dataclass__47f85b0ab6a8e89b7246ab4b503f246904d768f1():
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
    installer_sha1='b967490ad672a18e651f717554f233aa5f5d647b',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('parts', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.dockerdev.ops', 'Cmd'),
        ('omdev.dockerdev.ops', 'Entrypoint'),
        ('omdev.dockerdev.ops', 'Shell'),
    ),
)
def _process_dataclass__b967490ad672a18e651f717554f233aa5f5d647b():
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
                parts=self.parts,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.parts == other.parts
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'parts',
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
                self.parts,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            parts: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'parts', parts)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"parts={self.parts!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='13b9cdba740f6eef18e22a716c2437094cb63e8b',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('src', True, True, None, True, True, False, None), 'instance', 'missing', None"
            ", False, False, False), (('dst', True, True, None, True, True, False, None), 'instance', 'missing', None, "
            "False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (F"
            "alse,)))"
        ),
    ),
    cls_names=(
        ('omdev.dockerdev.ops', 'Copy'),
    ),
)
def _process_dataclass__13b9cdba740f6eef18e22a716c2437094cb63e8b():
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
                src=self.src,
                dst=self.dst,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.src == other.src and
                self.dst == other.dst
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'src',
            'dst',
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
                self.src,
                self.dst,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            src: __dataclass__init__fields__0__annotation,
            dst: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'src', src)
            __dataclass__object_setattr(self, 'dst', dst)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"src={self.src!r}")
            parts.append(f"dst={self.dst!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='717c4fd1a4c856256a000b7ec7acc6a8cd24336e',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('items', True, True, None, True, False, False, None), 'instance', 'missing', "
            "None, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.dockerdev.ops', 'Env'),
    ),
)
def _process_dataclass__717c4fd1a4c856256a000b7ec7acc6a8cd24336e():
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
                items=self.items,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.items == other.items
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'items',
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
                self.items,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            items: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'items', items)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"items={self.items!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='377ce9ccb7a74d95dcbd5f2f742ff49f7fb93001',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('spec', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.dockerdev.ops', 'From'),
    ),
)
def _process_dataclass__377ce9ccb7a74d95dcbd5f2f742ff49f7fb93001():
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
                spec=self.spec,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.spec == other.spec
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'spec',
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
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            spec: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'spec', spec)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"spec={self.spec!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='342176ad783f8229d17dfc256efa694e3eb198a9',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('body', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('cache_mounts', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('cache_mount_args', True, True, None, True, True, False, None), 'instanc"
            "e', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False,"
            " ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.dockerdev.ops', 'Run'),
    ),
)
def _process_dataclass__342176ad783f8229d17dfc256efa694e3eb198a9():
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
                body=self.body,
                cache_mounts=self.cache_mounts,
                cache_mount_args=self.cache_mount_args,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.body == other.body and
                self.cache_mounts == other.cache_mounts and
                self.cache_mount_args == other.cache_mount_args
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'body',
            'cache_mounts',
            'cache_mount_args',
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
                self.body,
                self.cache_mounts,
                self.cache_mount_args,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            body: __dataclass__init__fields__0__annotation,
            *,
            cache_mounts: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
            cache_mount_args: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'body', body)
            __dataclass__object_setattr(self, 'cache_mounts', cache_mounts)
            __dataclass__object_setattr(self, 'cache_mount_args', cache_mount_args)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"body={self.body!r}")
            parts.append(f"cache_mounts={self.cache_mounts!r}")
            parts.append(f"cache_mount_args={self.cache_mount_args!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='2f2600fcda63cbda0cf6cb04e907d1234ed9e510',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('header', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False), (('body', True, True, None, True, False, False, None), 'instance', 'missing',"
            " None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.dockerdev.ops', 'Section'),
    ),
)
def _process_dataclass__2f2600fcda63cbda0cf6cb04e907d1234ed9e510():
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
                header=self.header,
                body=self.body,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.header == other.header and
                self.body == other.body
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'header',
            'body',
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
                self.header,
                self.body,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            header: __dataclass__init__fields__0__annotation,
            body: __dataclass__init__fields__1__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'header', header)
            __dataclass__object_setattr(self, 'body', body)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"header={self.header!r}")
            parts.append(f"body={self.body!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='390292bd4766147442c143de8a1a98733c85e4a4',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('user', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False),), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), "
            "(), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.dockerdev.ops', 'User'),
    ),
)
def _process_dataclass__390292bd4766147442c143de8a1a98733c85e4a4():
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
                user=self.user,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.user == other.user
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'user',
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
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            user: __dataclass__init__fields__0__annotation,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'user', user)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"user={self.user!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='a4be24dd66014f5f0d21f21646ad35282ff3a74f',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('path', True, True, None, True, False, False, None), 'instance', 'missing', N"
            "one, False, False, False), (('content', True, True, None, True, False, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('append', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),),"
            " (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.dockerdev.ops', 'Write'),
    ),
)
def _process_dataclass__a4be24dd66014f5f0d21f21646ad35282ff3a74f():
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
                path=self.path,
                content=self.content,
                append=self.append,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.path == other.path and
                self.content == other.content and
                self.append == other.append
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'path',
            'content',
            'append',
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
                self.content,
                self.append,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            path: __dataclass__init__fields__0__annotation,
            content: __dataclass__init__fields__1__annotation,
            *,
            append: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'path', path)
            __dataclass__object_setattr(self, 'content', content)
            __dataclass__object_setattr(self, 'append', append)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"path={self.path!r}")
            parts.append(f"content={self.content!r}")
            parts.append(f"append={self.append!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='d6bee31b801e5a122d6639c34c2a6b3e54047ca2',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('resource_preambles', True, True, None, True, True, False, None), 'instance', "
            "'value', None, False, False, False), (('write_chmod', True, True, None, True, True, False, None), 'instanc"
            "e', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (False, False,"
            " ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.dockerdev.rendering', 'RenderContext'),
    ),
)
def _process_dataclass__d6bee31b801e5a122d6639c34c2a6b3e54047ca2():
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
                resource_preambles=self.resource_preambles,
                write_chmod=self.write_chmod,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.resource_preambles == other.resource_preambles and
                self.write_chmod == other.write_chmod
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'resource_preambles',
            'write_chmod',
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
                self.resource_preambles,
                self.write_chmod,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            resource_preambles: __dataclass__init__fields__0__annotation = __dataclass__init__fields__0__default,
            write_chmod: __dataclass__init__fields__1__annotation = __dataclass__init__fields__1__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'resource_preambles', resource_preambles)
            __dataclass__object_setattr(self, 'write_chmod', write_chmod)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"resource_preambles={self.resource_preambles!r}")
            parts.append(f"write_chmod={self.write_chmod!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='12ca4d1260a3c17c0b1366d05f55524950502f14',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('id', True, True, None, True, False, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('args', True, True, None, True, False, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('env', True, True, None, True, True, False, None), 'instance', 'value', None, F"
            "alse, False, False)), True, 0, ()), ((False,), (False,), (), (False,), (False, False, ()), ((),), (), (Fal"
            "se,)))"
        ),
    ),
    cls_names=(
        ('omdev.dockerdev.run', 'ProcessedRunArgs'),
    ),
)
def _process_dataclass__12ca4d1260a3c17c0b1366d05f55524950502f14():
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
                self.env == other.env
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'id',
            'args',
            'env',
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
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            id: __dataclass__init__fields__0__annotation,
            args: __dataclass__init__fields__1__annotation,
            *,
            env: __dataclass__init__fields__2__annotation = __dataclass__init__fields__2__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'id', id)
            __dataclass__object_setattr(self, 'args', args)
            __dataclass__object_setattr(self, 'env', env)

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
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='2bc0c20d93befe3a91eee50bbccf82c4c8f4fe05',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('verbose', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('no_rm', True, True, None, True, True, False, None), 'instance', 'value', None"
            ", False, False, False), (('no_it', True, True, None, True, True, False, None), 'instance', 'value', None, "
            "False, False, False), (('mounts', True, True, None, True, True, False, None), 'instance', 'value', None, F"
            "alse, False, False), (('mount_caches', True, True, None, True, True, False, None), 'instance', 'value', No"
            "ne, False, False, False), (('mount_docker_sock', True, True, None, True, True, False, None), 'instance', '"
            "value', None, False, False, False), (('mount_git', True, True, None, True, True, False, None), 'instance',"
            " 'value', None, False, False, False), (('clone_mount_git', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('privileged', True, True, None, True, True, False, None), "
            "'instance', 'value', None, False, False, False), (('cuda', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('offline', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('no_host_platform', True, True, None, True, True, False, N"
            "one), 'instance', 'value', None, False, False, False), (('autoexecs', True, True, None, True, True, False,"
            " None), 'instance', 'value', None, False, False, False), (('x11', True, True, None, True, True, False, Non"
            "e), 'instance', 'value', None, False, False, False), (('id', True, True, None, True, True, False, None), '"
            "instance', 'value', None, False, False, False), (('no_id_label', True, True, None, True, True, False, None"
            "), 'instance', 'value', None, False, False, False), (('inject_secrets_pats', True, True, None, True, True,"
            " False, None), 'instance', 'value', None, False, False, False), (('shift_uid', True, True, None, True, Tru"
            "e, False, None), 'instance', 'value', None, False, False, False), (('unknown_args', True, True, None, True"
            ", True, False, None), 'instance', 'value', None, False, False, False), (('extra_args', True, True, None, T"
            "rue, True, False, None), 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (Fals"
            "e,), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.dockerdev.run', 'RunArgs'),
    ),
)
def _process_dataclass__2bc0c20d93befe3a91eee50bbccf82c4c8f4fe05():
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
        __dataclass__init__fields__18__annotation = __dataclass__spec.fields[18].annotation
        __dataclass__init__fields__18__default = __dataclass__spec.fields[18].default.must()
        __dataclass__init__fields__19__annotation = __dataclass__spec.fields[19].annotation
        __dataclass__init__fields__19__default = __dataclass__spec.fields[19].default.must()
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                verbose=self.verbose,
                no_rm=self.no_rm,
                no_it=self.no_it,
                mounts=self.mounts,
                mount_caches=self.mount_caches,
                mount_docker_sock=self.mount_docker_sock,
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
                inject_secrets_pats=self.inject_secrets_pats,
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
                self.verbose == other.verbose and
                self.no_rm == other.no_rm and
                self.no_it == other.no_it and
                self.mounts == other.mounts and
                self.mount_caches == other.mount_caches and
                self.mount_docker_sock == other.mount_docker_sock and
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
                self.inject_secrets_pats == other.inject_secrets_pats and
                self.shift_uid == other.shift_uid and
                self.unknown_args == other.unknown_args and
                self.extra_args == other.extra_args
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'verbose',
            'no_rm',
            'no_it',
            'mounts',
            'mount_caches',
            'mount_docker_sock',
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
            'inject_secrets_pats',
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
                self.verbose,
                self.no_rm,
                self.no_it,
                self.mounts,
                self.mount_caches,
                self.mount_docker_sock,
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
                self.inject_secrets_pats,
                self.shift_uid,
                self.unknown_args,
                self.extra_args,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            verbose: __dataclass__init__fields__00__annotation = __dataclass__init__fields__00__default,
            no_rm: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            no_it: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            mounts: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            mount_caches: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            mount_docker_sock: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            mount_git: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            clone_mount_git: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            privileged: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            cuda: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            offline: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            no_host_platform: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            autoexecs: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            x11: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            id: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            no_id_label: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            inject_secrets_pats: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            shift_uid: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
            unknown_args: __dataclass__init__fields__18__annotation = __dataclass__init__fields__18__default,
            extra_args: __dataclass__init__fields__19__annotation = __dataclass__init__fields__19__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'verbose', verbose)
            __dataclass__object_setattr(self, 'no_rm', no_rm)
            __dataclass__object_setattr(self, 'no_it', no_it)
            __dataclass__object_setattr(self, 'mounts', mounts)
            __dataclass__object_setattr(self, 'mount_caches', mount_caches)
            __dataclass__object_setattr(self, 'mount_docker_sock', mount_docker_sock)
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
            __dataclass__object_setattr(self, 'inject_secrets_pats', inject_secrets_pats)
            __dataclass__object_setattr(self, 'shift_uid', shift_uid)
            __dataclass__object_setattr(self, 'unknown_args', unknown_args)
            __dataclass__object_setattr(self, 'extra_args', extra_args)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"verbose={self.verbose!r}")
            parts.append(f"no_rm={self.no_rm!r}")
            parts.append(f"no_it={self.no_it!r}")
            parts.append(f"mounts={self.mounts!r}")
            parts.append(f"mount_caches={self.mount_caches!r}")
            parts.append(f"mount_docker_sock={self.mount_docker_sock!r}")
            parts.append(f"mount_git={self.mount_git!r}")
            parts.append(f"clone_mount_git={self.clone_mount_git!r}")
            parts.append(f"privileged={self.privileged!r}")
            parts.append(f"cuda={self.cuda!r}")
            parts.append(f"offline={self.offline!r}")
            parts.append(f"no_host_platform={self.no_host_platform!r}")
            parts.append(f"autoexecs={self.autoexecs!r}")
            parts.append(f"x11={self.x11!r}")
            parts.append(f"id={self.id!r}")
            parts.append(f"no_id_label={self.no_id_label!r}")
            parts.append(f"inject_secrets_pats={self.inject_secrets_pats!r}")
            parts.append(f"shift_uid={self.shift_uid!r}")
            parts.append(f"unknown_args={self.unknown_args!r}")
            parts.append(f"extra_args={self.extra_args!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass


@_register(
    installer_sha1='e927e66b9fece0583302921d79b7bb580afaf6d0',
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
        ('omdev.dockerdev.run', 'RunHost'),
    ),
)
def _process_dataclass__e927e66b9fece0583302921d79b7bb580afaf6d0():
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
    installer_sha1='f995dd443af9e88c644b3b484e0ef5575e8bc5c8',
    spec_keys=(
        (
            "(((True, True, True, False, False, False, True, True, False, False, False, False, False, False, False, Fal"
            "se, False, False, False), ((('cfg', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('args', True, True, None, True, True, False, None), 'instance', 'missing', None"
            ", False, False, False), (('run_id', True, True, None, True, True, False, None), 'instance', 'missing', Non"
            "e, False, False, False), (('host', True, True, None, True, True, False, None), 'instance', 'missing', None"
            ", False, False, False), (('options', True, True, None, True, True, False, None), 'instance', 'factory', No"
            "ne, False, False, False), (('autoexec_lines', True, True, None, True, True, False, None), 'instance', 'fac"
            "tory', None, False, False, False), (('exec_env', True, True, None, True, True, False, None), 'instance', '"
            "factory', None, False, False, False), (('entrypoint', True, True, None, True, True, False, None), 'instanc"
            "e', 'value', None, False, False, False), (('client_env', True, True, None, True, True, False, None), 'inst"
            "ance', 'factory', None, False, False, False), (('staging_dir', True, True, None, True, True, False, None),"
            " 'instance', 'value', None, False, False, False)), False, 0, ()), ((False,), (False,), (), (False,), (Fals"
            "e, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omdev.dockerdev.run', 'RunPlan'),
    ),
)
def _process_dataclass__f995dd443af9e88c644b3b484e0ef5575e8bc5c8():
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
                exec_env=self.exec_env,
                entrypoint=self.entrypoint,
                client_env=self.client_env,
                staging_dir=self.staging_dir,
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
                self.exec_env == other.exec_env and
                self.entrypoint == other.entrypoint and
                self.client_env == other.client_env and
                self.staging_dir == other.staging_dir
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
            exec_env: __dataclass__init__fields__06__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            entrypoint: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            client_env: __dataclass__init__fields__08__annotation = __dataclass__HAS_DEFAULT_FACTORY,
            staging_dir: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
        ) -> __dataclass__None:
            if options is __dataclass__HAS_DEFAULT_FACTORY:
                options = __dataclass__init__fields__04__default_factory()
            if autoexec_lines is __dataclass__HAS_DEFAULT_FACTORY:
                autoexec_lines = __dataclass__init__fields__05__default_factory()
            if exec_env is __dataclass__HAS_DEFAULT_FACTORY:
                exec_env = __dataclass__init__fields__06__default_factory()
            if client_env is __dataclass__HAS_DEFAULT_FACTORY:
                client_env = __dataclass__init__fields__08__default_factory()
            self.cfg = cfg
            self.args = args
            self.run_id = run_id
            self.host = host
            self.options = options
            self.autoexec_lines = autoexec_lines
            self.exec_env = exec_env
            self.entrypoint = entrypoint
            self.client_env = client_env
            self.staging_dir = staging_dir

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
            parts.append(f"exec_env={self.exec_env!r}")
            parts.append(f"entrypoint={self.entrypoint!r}")
            parts.append(f"client_env={self.client_env!r}")
            parts.append(f"staging_dir={self.staging_dir!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
