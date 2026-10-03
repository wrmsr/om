import abc
import typing as ta

from omcore import dataclasses as dc
from omcore import lang


##


@dc.dataclass(frozen=True, kw_only=True)
class PromptContext:
    tool_names: ta.AbstractSet[str] = frozenset()


class PromptContributor(lang.Abstract):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    def order(self) -> int:
        return 0

    @abc.abstractmethod
    def render(self, context: PromptContext) -> str | None:
        raise NotImplementedError


PromptContributors = ta.NewType('PromptContributors', ta.Sequence[PromptContributor])
