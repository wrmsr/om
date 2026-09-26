import typing as ta

from omcore import check
from omcore import collections as col
from omcore import dataclasses as dc


##


@dc.dataclass(frozen=True, kw_only=True)
class Skill:
    name: str
    description: str
    directory: str


@dc.dataclass(frozen=True)
class SkillDiagnostic:
    path: str
    message: str


class SkillNotFoundError(Exception):
    pass


class SkillCatalog:
    def __init__(
            self,
            skills: ta.Sequence[Skill] = (),
            *,
            diagnostics: ta.Sequence[SkillDiagnostic] = (),
    ) -> None:
        super().__init__()

        self._skills = tuple(sorted(skills, key=lambda s: s.name))
        self._by_name = col.make_map(((s.name, s) for s in self._skills), strict=True)
        self._diagnostics = tuple(diagnostics)

    @property
    def skills(self) -> ta.Sequence[Skill]:
        return self._skills

    @property
    def diagnostics(self) -> ta.Sequence[SkillDiagnostic]:
        return self._diagnostics

    def get(self, name: str) -> Skill:
        if (skill := self._by_name.get(check.non_empty_str(name))) is None:
            raise SkillNotFoundError(name)
        return skill
