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


@dc.dataclass(frozen=True, kw_only=True)
class ModelsModuleManifest:
    models: ta.Sequence[ModuleManifestModel]

    @classmethod
    def of(cls, models: ta.Sequence[Model]) -> ModelsModuleManifest:
        return ModelsModuleManifest(
            models=[
                ModuleManifestModel(
                    provider=m.key.provider,
                    id=m.key.id,

                    name=m.name,

                    backend=m.backend,
                )
                for m in models
            ],
        )
