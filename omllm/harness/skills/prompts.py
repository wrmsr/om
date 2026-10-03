import typing as ta

from ..prompts.base import PromptContext
from ..prompts.base import PromptContributor
from .catalogs import SkillCatalog


##


class SkillsPromptContributor(PromptContributor):
    name: ta.Final = 'skills'
    order: ta.Final = 200

    def __init__(self, *, catalog: SkillCatalog) -> None:
        super().__init__()

        self._catalog = catalog

    def render(self, context: PromptContext) -> str | None:
        if not self._catalog.skills or 'read_skill' not in context.tool_names:
            return None
        return '\n'.join([
            'Available skills:',
            (
                'When a skill matches the task, use read_skill to read its full SKILL.md before applying it; continue '
                'through every page. Read bundled text resources with the same tool, supplying a path relative to '
                'that skill. Skills live on the host; their paths do not refer to the filesystem or process tools\' '
                'working directory. Reading a script does not execute it.'
            ),
            *[f'- {s.name}: {s.description}' for s in self._catalog.skills],
        ])
