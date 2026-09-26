import os
import re
import typing as ta

from omcore import dataclasses as dc
from omcore.formats.yaml import all as yaml

from ...core.asyncs.base import AsyncJob
from .catalogs import Skill
from .catalogs import SkillCatalog
from .catalogs import SkillDiagnostic
from .files import read_skill_file


##


class LocalSkillLoader:
    """Discovers immediate child skill directories of explicit host roots. Never searches a tool workspace."""

    @dc.dataclass(frozen=True, kw_only=True)
    class Config:
        directories: ta.Sequence[str] = ()
        ignore_missing: bool = False

    def __init__(self, config: Config) -> None:
        super().__init__()

        self._config = config

    def _load_skill(self, directory: str) -> Skill:
        text = read_skill_file(directory, 'SKILL.md')
        lines = text.splitlines()
        if not lines or lines[0].strip() != '---':
            raise ValueError('SKILL.md must start with YAML frontmatter')
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == '---'), None)
        if end is None:
            raise ValueError('Unterminated skill frontmatter')
        metadata = yaml.loads('\n'.join(lines[1:end]))
        if not isinstance(metadata, dict):
            raise TypeError('Skill frontmatter must be a mapping')
        name = metadata.get('name')
        description = metadata.get('description')
        if not isinstance(name, str) or re.fullmatch(r'[a-z0-9][a-z0-9_-]*', name) is None:
            raise ValueError('Skill name must use lowercase letters, digits, hyphens, or underscores')
        if not isinstance(description, str) or not description.strip():
            raise ValueError('Skill description must be a non-empty string')
        return Skill(name=name, description=description.strip(), directory=directory)

    def load(self) -> SkillCatalog:
        skills: list[Skill] = []
        diagnostics: list[SkillDiagnostic] = []
        directories: set[str] = set()
        for given_root in self._config.directories:
            root = os.path.realpath(os.path.expanduser(given_root))
            try:
                children = sorted(os.listdir(root))
            except OSError as e:
                if not (isinstance(e, FileNotFoundError) and self._config.ignore_missing):
                    diagnostics.append(SkillDiagnostic(root, str(e)))
                continue

            for child in children:
                directory = os.path.realpath(os.path.join(root, child))
                if directory in directories or not os.path.isfile(os.path.join(directory, 'SKILL.md')):
                    continue
                directories.add(directory)
                try:
                    skills.append(self._load_skill(directory))
                except Exception as e:  # noqa: BLE001
                    diagnostics.append(SkillDiagnostic(os.path.join(directory, 'SKILL.md'), str(e)))

        # Duplicate names are ambiguous configuration, unlike an individual malformed skill which can be diagnosed
        # and skipped. The catalog rejects them rather than choosing a filesystem-dependent winner.
        return SkillCatalog(skills, diagnostics=diagnostics)


@dc.dataclass(frozen=True)
class LoadSkillsJob(AsyncJob[SkillCatalog]):
    loader: LocalSkillLoader

    def run(self) -> SkillCatalog:
        return self.loader.load()
