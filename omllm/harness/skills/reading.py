from omcore import dataclasses as dc

from ...core.asyncs.base import AsyncJob
from ...core.asyncs.base import AsyncJobRunner
from .catalogs import Skill
from .catalogs import SkillCatalog
from .files import read_skill_file


##


@dc.dataclass(frozen=True)
class _ReadSkillJob(AsyncJob[str]):
    skill: Skill
    path: str

    def run(self) -> str:
        return read_skill_file(self.skill.directory, self.path)


class SkillReader:
    def __init__(self, *, catalog: SkillCatalog, job_runner: AsyncJobRunner) -> None:
        super().__init__()

        self._catalog = catalog
        self._job_runner = job_runner

    async def read(self, name: str, path: str = 'SKILL.md') -> str:
        return await self._job_runner.run(_ReadSkillJob(self._catalog.get(name), path), timeout=30.)
