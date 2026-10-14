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
    installer_sha1='a657c43da77c4eceb41c9dd2b33ccfe41a35be62',
    spec_keys=(
        (
            "(((True, True, True, False, False, True, True, True, False, False, False, False, False, False, False, Fals"
            "e, False, False, False), ((('file_path', True, True, None, True, True, False, None), 'instance', 'missing'"
            ", None, False, False, False), (('mode', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('immutable', True, True, None, True, True, False, None), 'instance', 'value',"
            " None, False, False, False), (('query_only', True, True, None, True, True, False, None), 'instance', 'valu"
            "e', None, False, False, False), (('busy_timeout_s', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, False, False, False), (('foreign_keys', True, True, None, True, True, False, None), 'inst"
            "ance', 'value', None, False, False, False), (('synchronous', True, True, None, True, True, False, None), '"
            "instance', 'value', None, False, False, False), (('fullfsync', True, True, None, True, True, False, None),"
            " 'instance', 'value', None, False, False, False), (('checkpoint_fullfsync', True, True, None, True, True, "
            "False, None), 'instance', 'value', None, False, False, False), (('journal_size_limit', True, True, None, T"
            "rue, True, False, None), 'instance', 'value', None, False, False, False), (('wal_autocheckpoint_pages', Tr"
            "ue, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('mmap_size', "
            "True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('cache_size"
            "_kib', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('tem"
            "p_store', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, False), (('"
            "trusted_schema', True, True, None, True, True, False, None), 'instance', 'value', None, False, False, Fals"
            "e), (('double_quoted_strings', True, True, None, True, True, False, None), 'instance', 'value', None, Fals"
            "e, False, False), (('defensive', True, True, None, True, True, False, None), 'instance', 'value', None, Fa"
            "lse, False, False), (('journal_mode', True, True, None, True, True, False, None), 'instance', 'value', Non"
            "e, False, False, False), (('page_size', True, True, None, True, True, False, None), 'instance', 'value', N"
            "one, False, False, False), (('auto_vacuum', True, True, None, True, True, False, None), 'instance', 'value"
            "', None, False, False, False), (('application_id', True, True, None, True, True, False, None), 'instance',"
            " 'value', None, False, False, False), (('optimize', True, True, None, True, True, False, None), 'instance'"
            ", 'value', None, False, False, False), (('analysis_limit', True, True, None, True, True, False, None), 'in"
            "stance', 'value', None, False, False, False), (('checkpoint_on_close', True, True, None, True, True, False"
            ", None), 'instance', 'value', None, False, False, False), (('min_sqlite_version', True, True, None, True, "
            "True, False, None), 'instance', 'value', None, False, False, False), (('READONLY', True, True, None, True,"
            " None, False, None), 'class_var', 'missing', None, False, False, False)), False, 0, ()), ((False,), (False"
            ",), (), (False,), (False, False, ()), ((),), (), (False,)))"
        ),
    ),
    cls_names=(
        ('omcore.sql.backends.sqlite.connecting', 'SqliteDbConfig'),
    ),
)
def _process_dataclass__a657c43da77c4eceb41c9dd2b33ccfe41a35be62():
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
        __dataclass__init__fields__20__annotation = __dataclass__spec.fields[20].annotation
        __dataclass__init__fields__20__default = __dataclass__spec.fields[20].default.must()
        __dataclass__init__fields__21__annotation = __dataclass__spec.fields[21].annotation
        __dataclass__init__fields__21__default = __dataclass__spec.fields[21].default.must()
        __dataclass__init__fields__22__annotation = __dataclass__spec.fields[22].annotation
        __dataclass__init__fields__22__default = __dataclass__spec.fields[22].default.must()
        __dataclass__init__fields__23__annotation = __dataclass__spec.fields[23].annotation
        __dataclass__init__fields__23__default = __dataclass__spec.fields[23].default.must()
        __dataclass__init__fields__24__annotation = __dataclass__spec.fields[24].annotation
        __dataclass__init__fields__24__default = __dataclass__spec.fields[24].default.must()
        __dataclass__init__fields__25__annotation = __dataclass__spec.fields[25].annotation
        __dataclass__FrozenInstanceError = __dataclass__globals['__dataclass__FrozenInstanceError']
        __dataclass__None = __dataclass__globals['__dataclass__None']
        __dataclass___recursive_repr = __dataclass__globals['__dataclass___recursive_repr']
        __dataclass__object_setattr = __dataclass__globals['__dataclass__object_setattr']
        __dataclass__set_cls_attr = __dataclass__globals['__dataclass__set_cls_attr']

        def __copy__(self):
            if self.__class__ is not __class__:
                raise TypeError(self)
            return __class__(  # noqa
                file_path=self.file_path,
                mode=self.mode,
                immutable=self.immutable,
                query_only=self.query_only,
                busy_timeout_s=self.busy_timeout_s,
                foreign_keys=self.foreign_keys,
                synchronous=self.synchronous,
                fullfsync=self.fullfsync,
                checkpoint_fullfsync=self.checkpoint_fullfsync,
                journal_size_limit=self.journal_size_limit,
                wal_autocheckpoint_pages=self.wal_autocheckpoint_pages,
                mmap_size=self.mmap_size,
                cache_size_kib=self.cache_size_kib,
                temp_store=self.temp_store,
                trusted_schema=self.trusted_schema,
                double_quoted_strings=self.double_quoted_strings,
                defensive=self.defensive,
                journal_mode=self.journal_mode,
                page_size=self.page_size,
                auto_vacuum=self.auto_vacuum,
                application_id=self.application_id,
                optimize=self.optimize,
                analysis_limit=self.analysis_limit,
                checkpoint_on_close=self.checkpoint_on_close,
                min_sqlite_version=self.min_sqlite_version,
            )

        __dataclass__set_cls_attr(__class__, '__copy__', __copy__, 'raise', set_qualname=True)

        def __eq__(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return NotImplemented
            return (
                self.file_path == other.file_path and
                self.mode == other.mode and
                self.immutable == other.immutable and
                self.query_only == other.query_only and
                self.busy_timeout_s == other.busy_timeout_s and
                self.foreign_keys == other.foreign_keys and
                self.synchronous == other.synchronous and
                self.fullfsync == other.fullfsync and
                self.checkpoint_fullfsync == other.checkpoint_fullfsync and
                self.journal_size_limit == other.journal_size_limit and
                self.wal_autocheckpoint_pages == other.wal_autocheckpoint_pages and
                self.mmap_size == other.mmap_size and
                self.cache_size_kib == other.cache_size_kib and
                self.temp_store == other.temp_store and
                self.trusted_schema == other.trusted_schema and
                self.double_quoted_strings == other.double_quoted_strings and
                self.defensive == other.defensive and
                self.journal_mode == other.journal_mode and
                self.page_size == other.page_size and
                self.auto_vacuum == other.auto_vacuum and
                self.application_id == other.application_id and
                self.optimize == other.optimize and
                self.analysis_limit == other.analysis_limit and
                self.checkpoint_on_close == other.checkpoint_on_close and
                self.min_sqlite_version == other.min_sqlite_version
            )

        __dataclass__set_cls_attr(__class__, '__eq__', __eq__, 'raise', set_qualname=True)

        __dataclass___frozen_fields = {
            'file_path',
            'mode',
            'immutable',
            'query_only',
            'busy_timeout_s',
            'foreign_keys',
            'synchronous',
            'fullfsync',
            'checkpoint_fullfsync',
            'journal_size_limit',
            'wal_autocheckpoint_pages',
            'mmap_size',
            'cache_size_kib',
            'temp_store',
            'trusted_schema',
            'double_quoted_strings',
            'defensive',
            'journal_mode',
            'page_size',
            'auto_vacuum',
            'application_id',
            'optimize',
            'analysis_limit',
            'checkpoint_on_close',
            'min_sqlite_version',
            'READONLY',
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
                self.mode,
                self.immutable,
                self.query_only,
                self.busy_timeout_s,
                self.foreign_keys,
                self.synchronous,
                self.fullfsync,
                self.checkpoint_fullfsync,
                self.journal_size_limit,
                self.wal_autocheckpoint_pages,
                self.mmap_size,
                self.cache_size_kib,
                self.temp_store,
                self.trusted_schema,
                self.double_quoted_strings,
                self.defensive,
                self.journal_mode,
                self.page_size,
                self.auto_vacuum,
                self.application_id,
                self.optimize,
                self.analysis_limit,
                self.checkpoint_on_close,
                self.min_sqlite_version,
            ))

        __dataclass__set_cls_attr(__class__, '__hash__', __hash__, 'replace', set_qualname=True)

        def __init__(
            self,
            *,
            file_path: __dataclass__init__fields__00__annotation,
            mode: __dataclass__init__fields__01__annotation = __dataclass__init__fields__01__default,
            immutable: __dataclass__init__fields__02__annotation = __dataclass__init__fields__02__default,
            query_only: __dataclass__init__fields__03__annotation = __dataclass__init__fields__03__default,
            busy_timeout_s: __dataclass__init__fields__04__annotation = __dataclass__init__fields__04__default,
            foreign_keys: __dataclass__init__fields__05__annotation = __dataclass__init__fields__05__default,
            synchronous: __dataclass__init__fields__06__annotation = __dataclass__init__fields__06__default,
            fullfsync: __dataclass__init__fields__07__annotation = __dataclass__init__fields__07__default,
            checkpoint_fullfsync: __dataclass__init__fields__08__annotation = __dataclass__init__fields__08__default,
            journal_size_limit: __dataclass__init__fields__09__annotation = __dataclass__init__fields__09__default,
            wal_autocheckpoint_pages: __dataclass__init__fields__10__annotation = __dataclass__init__fields__10__default,
            mmap_size: __dataclass__init__fields__11__annotation = __dataclass__init__fields__11__default,
            cache_size_kib: __dataclass__init__fields__12__annotation = __dataclass__init__fields__12__default,
            temp_store: __dataclass__init__fields__13__annotation = __dataclass__init__fields__13__default,
            trusted_schema: __dataclass__init__fields__14__annotation = __dataclass__init__fields__14__default,
            double_quoted_strings: __dataclass__init__fields__15__annotation = __dataclass__init__fields__15__default,
            defensive: __dataclass__init__fields__16__annotation = __dataclass__init__fields__16__default,
            journal_mode: __dataclass__init__fields__17__annotation = __dataclass__init__fields__17__default,
            page_size: __dataclass__init__fields__18__annotation = __dataclass__init__fields__18__default,
            auto_vacuum: __dataclass__init__fields__19__annotation = __dataclass__init__fields__19__default,
            application_id: __dataclass__init__fields__20__annotation = __dataclass__init__fields__20__default,
            optimize: __dataclass__init__fields__21__annotation = __dataclass__init__fields__21__default,
            analysis_limit: __dataclass__init__fields__22__annotation = __dataclass__init__fields__22__default,
            checkpoint_on_close: __dataclass__init__fields__23__annotation = __dataclass__init__fields__23__default,
            min_sqlite_version: __dataclass__init__fields__24__annotation = __dataclass__init__fields__24__default,
        ) -> __dataclass__None:
            __dataclass__object_setattr(self, 'file_path', file_path)
            __dataclass__object_setattr(self, 'mode', mode)
            __dataclass__object_setattr(self, 'immutable', immutable)
            __dataclass__object_setattr(self, 'query_only', query_only)
            __dataclass__object_setattr(self, 'busy_timeout_s', busy_timeout_s)
            __dataclass__object_setattr(self, 'foreign_keys', foreign_keys)
            __dataclass__object_setattr(self, 'synchronous', synchronous)
            __dataclass__object_setattr(self, 'fullfsync', fullfsync)
            __dataclass__object_setattr(self, 'checkpoint_fullfsync', checkpoint_fullfsync)
            __dataclass__object_setattr(self, 'journal_size_limit', journal_size_limit)
            __dataclass__object_setattr(self, 'wal_autocheckpoint_pages', wal_autocheckpoint_pages)
            __dataclass__object_setattr(self, 'mmap_size', mmap_size)
            __dataclass__object_setattr(self, 'cache_size_kib', cache_size_kib)
            __dataclass__object_setattr(self, 'temp_store', temp_store)
            __dataclass__object_setattr(self, 'trusted_schema', trusted_schema)
            __dataclass__object_setattr(self, 'double_quoted_strings', double_quoted_strings)
            __dataclass__object_setattr(self, 'defensive', defensive)
            __dataclass__object_setattr(self, 'journal_mode', journal_mode)
            __dataclass__object_setattr(self, 'page_size', page_size)
            __dataclass__object_setattr(self, 'auto_vacuum', auto_vacuum)
            __dataclass__object_setattr(self, 'application_id', application_id)
            __dataclass__object_setattr(self, 'optimize', optimize)
            __dataclass__object_setattr(self, 'analysis_limit', analysis_limit)
            __dataclass__object_setattr(self, 'checkpoint_on_close', checkpoint_on_close)
            __dataclass__object_setattr(self, 'min_sqlite_version', min_sqlite_version)

        __dataclass__set_cls_attr(__class__, '__init__', __init__, 'raise', set_qualname=True)

        @__dataclass___recursive_repr()
        def __repr__(self):
            parts = []
            parts.append(f"file_path={self.file_path!r}")
            parts.append(f"mode={self.mode!r}")
            parts.append(f"immutable={self.immutable!r}")
            parts.append(f"query_only={self.query_only!r}")
            parts.append(f"busy_timeout_s={self.busy_timeout_s!r}")
            parts.append(f"foreign_keys={self.foreign_keys!r}")
            parts.append(f"synchronous={self.synchronous!r}")
            parts.append(f"fullfsync={self.fullfsync!r}")
            parts.append(f"checkpoint_fullfsync={self.checkpoint_fullfsync!r}")
            parts.append(f"journal_size_limit={self.journal_size_limit!r}")
            parts.append(f"wal_autocheckpoint_pages={self.wal_autocheckpoint_pages!r}")
            parts.append(f"mmap_size={self.mmap_size!r}")
            parts.append(f"cache_size_kib={self.cache_size_kib!r}")
            parts.append(f"temp_store={self.temp_store!r}")
            parts.append(f"trusted_schema={self.trusted_schema!r}")
            parts.append(f"double_quoted_strings={self.double_quoted_strings!r}")
            parts.append(f"defensive={self.defensive!r}")
            parts.append(f"journal_mode={self.journal_mode!r}")
            parts.append(f"page_size={self.page_size!r}")
            parts.append(f"auto_vacuum={self.auto_vacuum!r}")
            parts.append(f"application_id={self.application_id!r}")
            parts.append(f"optimize={self.optimize!r}")
            parts.append(f"analysis_limit={self.analysis_limit!r}")
            parts.append(f"checkpoint_on_close={self.checkpoint_on_close!r}")
            parts.append(f"min_sqlite_version={self.min_sqlite_version!r}")
            return (
                f"{self.__class__.__qualname__}("
                f"{', '.join(parts)}"
                f")"
            )

        __dataclass__set_cls_attr(__class__, '__repr__', __repr__, 'raise', set_qualname=True)

    return _process_dataclass
