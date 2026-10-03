import typing as ta

from omcore import check
from omcore import dataclasses as dc

from ...agent.tools.classes import ToolClass
from ...agent.types.tools import ToolContext
from ...agent.types.tools import ToolDescription
from .reading import SkillReader


##


@dc.dataclass(frozen=True)
class ReadSkillToolParams:
    name: str
    path: str = 'SKILL.md'
    offset: int = 0
    limit: int = 20_000


class ReadSkillTool(ToolClass[ReadSkillToolParams]):
    name: ta.Final = 'read_skill'
    params_cls: ta.Final = ReadSkillToolParams
    description: ta.Final = ToolDescription(
        'Reads a configured host skill or one of its bundled text resources, independently of filesystem tools.',
        dict(
            name='The skill name from the available skills list.',
            path='Resource path relative to the skill directory. Defaults to SKILL.md.',
            offset='Zero-based character offset. Defaults to 0; use the next offset returned for more pages.',
            limit='Maximum characters to return, from 1 to 20000. Defaults to 20000.',
        ),
    )

    def __init__(self, *, reader: SkillReader) -> None:
        super().__init__()

        self._reader = reader

    def summarize(self, ctx: ToolContext, params: ReadSkillToolParams) -> str:
        return f'{params.name}: {params.path}'

    async def execute(self, ctx: ToolContext, params: ReadSkillToolParams) -> str:
        check.arg(params.offset >= 0, 'offset must be non-negative')
        check.arg(1 <= params.limit <= 20_000, 'limit must be between 1 and 20000')
        text = await self._reader.read(params.name, params.path)
        if params.offset == 0 and len(text) <= params.limit:
            return text

        check.arg(params.offset <= len(text), 'offset is past the end of the resource')
        end = min(params.offset + params.limit, len(text))
        more = f' Continue with offset={end}.' if end < len(text) else ' End of resource.'
        return f'Characters {params.offset}:{end} of {len(text)}.{more}\n\n{text[params.offset:end]}'
