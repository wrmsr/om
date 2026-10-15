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
        parts = [
            ps
            for pc in self._contributors or []
            for p in pc.get_system_prompt_parts() or []
            if (ps := p.text.strip())
        ]

        return '\n\n'.join(parts)
