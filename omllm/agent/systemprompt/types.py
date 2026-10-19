import abc
import enum
import typing as ta

from omcore import dataclasses as dc
from omcore import lang


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
    def get_system_prompt_parts(self) -> ta.Sequence[SystemPromptPart] | None:
        raise NotImplementedError


SystemPromptContributors = ta.NewType('SystemPromptContributors', ta.Sequence[SystemPromptContributor])
