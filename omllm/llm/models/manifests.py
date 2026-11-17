import dataclasses as dc
import typing as ta

from omcore import cached

from ..types.models import Model
from ..types.models import ModelKey


##


@dc.dataclass(frozen=True, kw_only=True)
class ModuleManifestModel:
    provider: str
    id: str

    @cached.property
    def key(self) -> ModelKey:
        return ModelKey(self.provider, self.id)

    name: str | None = None

    backend: str

    #

    short_id: str | None = None
    short_id_aliases: ta.Sequence[str] | None = None

    include_platforms: ta.AbstractSet[str] | None = None
    exclude_platforms: ta.AbstractSet[str] | None = None


@dc.dataclass(frozen=True, kw_only=True)
class ModelsModuleManifest:
    models: ta.Sequence[ModuleManifestModel]

    @classmethod
    def of(cls, models: ta.Sequence[Model]) -> ModelsModuleManifest:
        return ModelsModuleManifest(
            models=[
                ModuleManifestModel(
                    provider=m.key_.provider,
                    id=m.key_.id,

                    name=m.name,

                    backend=m.backend_,

                    #

                    short_id=m.short_id,
                    short_id_aliases=tuple(m.short_id_aliases) if m.short_id_aliases else None,

                    include_platforms=frozenset(m.include_platforms) if m.include_platforms else None,
                    exclude_platforms=frozenset(m.exclude_platforms) if m.exclude_platforms else None,
                )
                for m in models
            ],
        )
