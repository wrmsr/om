import abc
import enum
import typing as ta

from omcore import dataclasses as dc
from omcore import lang


SystemPromptParts: ta.TypeAlias = ta.Sequence['SystemPromptPart'] | None


##


class SystemPromptPriority(enum.IntEnum):
    FIRST = enum.auto()

    MISSION = enum.auto()

    USER = enum.auto()

    TOOLS = enum.auto()

    ENVIRONMENT = enum.auto()

    LAST = enum.auto()


@dc.dataclass(frozen=True)
class SystemPromptPart:
    priority: SystemPromptPriority
    text: str


##


class SystemPromptContributor(lang.Abstract):
    @abc.abstractmethod
    def get_system_prompt_parts(self) -> SystemPromptParts | ta.Awaitable[SystemPromptParts]:
        """
        The parts outright, or an awaitable of them: a contributor which has to look at something to say its part
        does so when the prompt is built, which is at an agent's setup.
        """

        raise NotImplementedError


SystemPromptContributors = ta.NewType('SystemPromptContributors', ta.Sequence[SystemPromptContributor])
