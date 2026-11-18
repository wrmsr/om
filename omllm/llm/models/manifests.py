import dataclasses as dc
import typing as ta

from omcore import cached
from omcore import check

from ..types.models import Model
from ..types.models import ModelKey
from ..types.models import ModelShortIds


##


@dc.dataclass(frozen=True, kw_only=True)
class ModuleManifestModel:
    provider: str
    id: str

    @cached.property
    def key(self) -> ModelKey:
        return ModelKey(self.provider, self.id)

    backend: str

    #

    name: str | None = None

    #

    short_id: str | None = None
    short_id_aliases: ta.Sequence[str] | None = None

    include_platforms: ta.AbstractSet[str] | None = None
    exclude_platforms: ta.AbstractSet[str] | None = None

    @cached.property
    def short_ids(self) -> ModelShortIds:
        return ModelShortIds(
            short_id=self.short_id,
            short_id_aliases=ta.cast(ta.Any, self.short_id_aliases),

            include_platforms=self.include_platforms,
            exclude_platforms=self.exclude_platforms,
        )


@dc.dataclass(frozen=True, kw_only=True)
class ModelsModuleManifest:
    module: str
    models: ta.Sequence[ModuleManifestModel]

    @classmethod
    def of(cls, module: str, models: ta.Mapping[ModelKey, Model] | ta.Iterable[Model]) -> ModelsModuleManifest:
        lst: list[ModuleManifestModel] = []

        for e in (models.items() if isinstance(models, ta.Mapping) else models):
            if isinstance(e, Model):
                mk, m = e.key_, e
            else:
                mk, m = e
                check.arg(mk == m.key_)

            lst.append(ModuleManifestModel(
                provider=m.key_.provider,
                id=m.key_.id,

                name=m.name,

                backend=m.backend_,

                #

                short_id=msi.short_id if (msi := m.short_ids) else None,
                short_id_aliases=tuple(msi.short_id_aliases) if msi and msi.short_id_aliases else None,

                include_platforms=frozenset(msi.include_platforms) if msi and msi.include_platforms else None,
                exclude_platforms=frozenset(msi.exclude_platforms) if msi and msi.exclude_platforms else None,
            ))

        return ModelsModuleManifest(
            module=module,
            models=lst,
        )
