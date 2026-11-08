import typing as ta

from omcore import collections as col

from .types import SystemPromptContributors
from .types import SystemPromptPart


##


class SystemPromptManager:
    def __init__(
            self,
            contributors: SystemPromptContributors | None = None,
    ) -> None:
        super().__init__()

        self._contributors = contributors

    async def build_system_prompt(self) -> str:
        tups: list[tuple[SystemPromptPart, str]] = []
        for pc in self._contributors or []:
            out = pc.get_system_prompt_parts()
            if isinstance(out, ta.Awaitable):
                out = await out
            for p in out or []:
                if (ps := p.text.strip()):
                    tups.append((p, ps))

        tups.sort(key=lambda tup: (tup[0].priority, tup[1]))

        txts = col.unique(ps for _, ps in tups)

        return '\n\n'.join(txts)
