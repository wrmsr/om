from omcore import collections as col

from .types import SystemPromptContributors


##


class SystemPromptManager:
    def __init__(
            self,
            contributors: SystemPromptContributors | None = None,
    ) -> None:
        super().__init__()

        self._contributors = contributors

    def build_system_prompt(self) -> str:
        tups = [
            (p, ps)
            for pc in self._contributors or []
            for p in pc.get_system_prompt_parts() or []
            if (ps := p.text.strip())
        ]

        tups.sort(key=lambda tup: (tup[0].priority, tup[1]))

        txts = col.unique(ps for _, ps in tups)

        return '\n\n'.join(txts)
