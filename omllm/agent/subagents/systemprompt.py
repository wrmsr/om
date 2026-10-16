import typing as ta

from ..systemprompt.types import SystemPromptContributor
from ..systemprompt.types import SystemPromptPart
from ..systemprompt.types import SystemPromptPriority
from .profiles import SubagentProfile


##


SUBAGENT_SYSTEM_PROMPT: str = """
You are a subagent: an agent spawned by another agent to carry out one task on its behalf. You have no history with the
user and will not be spoken to again - the task you were given is your whole input, and your final message is the only
thing that reaches the agent which spawned you. Do not ask questions; make reasonable assumptions and say what they
were. Work until the task is done or you cannot proceed, then end with a complete, self-contained report.
""".strip()


class SubagentProfileSystemPromptContributor(SystemPromptContributor):
    """What every subagent is told, then what its profile adds."""

    def __init__(
            self,
            *,
            profile: SubagentProfile,
    ) -> None:
        super().__init__()

        self._profile = profile

    def get_system_prompt_parts(self) -> ta.Sequence[SystemPromptPart] | None:
        parts = [
            SystemPromptPart(SystemPromptPriority.DEFAULT, SUBAGENT_SYSTEM_PROMPT),
        ]

        if (profile_prompt := self._profile.system_prompt) is not None:
            parts.append(SystemPromptPart(SystemPromptPriority.DEFAULT, profile_prompt))

        return parts
