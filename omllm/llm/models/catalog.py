import abc
import importlib
import typing as ta

from omcore import cached
from omcore import check
from omcore import collections as col
from omcore import lang

from ..types.models import Model
from ..types.models import ModelKey
from ..types.models import ModelShortIds
from .defaults import DEFAULT_MODEL_SHORT_ID
from .manifests import ModelsModuleManifest
from .manifests import ModuleManifestModel


##


class ModelCatalog:
    def __init__(
            self,
            items: ta.Iterable[Model | ModelsModuleManifest],
            *,
            platform: str | None = None,
    ) -> None:
        super().__init__()

        self._platform = platform

        lst: list[ModelCatalog.Entry] = []
        by_key: dict[ModelKey, ModelCatalog.Entry] = {}
        by_short_id: dict[str, ModelCatalog.Entry] = {}

        def add_entry(e: ModelCatalog.Entry) -> None:  # noqa
            check.not_in(e.key, by_key)
            lst.append(e)
            by_key[e.key] = e

            for sid in ModelShortIds.iter(e.short_ids, platform=platform):
                check.not_in(sid, by_short_id)
                by_short_id[sid] = e

        for m in items:
            if isinstance(m, Model):
                add_entry(ModelCatalog._ModelEntry(m))

            elif isinstance(m, ModelsModuleManifest):
                mo = ModelCatalog._ManifestModule(m.module)
                for mm in m.models:
                    add_entry(ModelCatalog._ManifestEntry(mo, mm))

            else:
                raise TypeError(m)

        self._lst = lst
        self._by_key = by_key
        self._by_short_id = by_short_id

    #

    class Entry(lang.Abstract, lang.Sealed):
        @property
        @abc.abstractmethod
        def key(self) -> ModelKey:
            raise NotImplementedError

        @property
        @abc.abstractmethod
        def short_ids(self) -> ModelShortIds | None:
            raise NotImplementedError

        @abc.abstractmethod
        def model(self) -> Model:
            raise NotImplementedError

        def __repr__(self) -> str:
            return f'ModelCatalog.Entry({self.key!r})'

    #

    @ta.final
    class _ModelEntry(Entry):
        def __init__(self, model: Model) -> None:
            check.not_none(model.key)
            self._model = model

        @property
        def key(self) -> ModelKey:
            return self._model.key_

        @property
        def short_ids(self) -> ModelShortIds | None:
            return self._model.short_ids

        def model(self) -> Model:
            return self._model

    #

    @ta.final
    class _ManifestModule:
        def __init__(self, name: str) -> None:
            self.name = name

        @cached.function
        def imported_module(self) -> ta.Any:
            return importlib.import_module(self.name)

        @cached.function
        def imported_models(self) -> ta.Mapping[ModelKey, Model]:
            attr = getattr(self.imported_module(), 'MODELS')

            if isinstance(attr, ta.Mapping):
                return {
                    check.isinstance(mk, ModelKey): check.isinstance(m, Model)
                    for m, mk in attr.items()
                }

            elif isinstance(attr, ta.Sequence):
                return col.make_map((
                    (check.isinstance(m.key, ModelKey), check.isinstance(m, Model))
                    for m in attr
                ), strict=True)

            else:
                raise TypeError(attr)

    @ta.final
    class _ManifestEntry(Entry):
        def __init__(self, module: ModelCatalog._ManifestModule, manifest: ModuleManifestModel) -> None:
            self._module = module
            self._manifest = manifest

        @property
        def key(self) -> ModelKey:
            return self._manifest.key

        @property
        def short_ids(self) -> ModelShortIds | None:
            return self._manifest.short_ids

        @cached.function
        def model(self) -> Model:
            return self._module.imported_models()[self._manifest.key]

    #

    @property
    def seq(self) -> ta.Sequence[Entry]:
        return self._lst

    @property
    def by_key(self) -> ta.Mapping[ModelKey, Entry]:
        return self._by_key

    @property
    def by_short_id(self) -> ta.Mapping[str, Entry]:
        return self._by_short_id

    #

    @cached.function
    def all(self) -> ta.Sequence[Model]:
        return [e.model() for e in self._lst]

    #

    def __len__(self) -> int:
        return len(self._by_key)

    def __iter__(self) -> ta.Iterator[Entry]:
        return iter(self._by_key.values())

    def __contains__(self, key: ModelKey) -> bool:
        return check.isinstance(key, ModelKey) in self._by_key

    def __getitem__(self, key: ModelKey, /) -> Entry:
        return self._by_key[check.isinstance(key, ModelKey)]


##


@cached.function(lock=True)
def _models_module_manifests() -> ta.Sequence[ModelsModuleManifest]:
    from omcore.manifests.globals import GlobalManifestLoader

    return GlobalManifestLoader.load_values(classes=[ModelsModuleManifest])


@cached.function(lock=True)
def manifest_model_catalog() -> ModelCatalog:
    return ModelCatalog(_models_module_manifests())


#


@cached.function
def default_model() -> Model:
    return manifest_model_catalog().by_short_id[DEFAULT_MODEL_SHORT_ID].model()
