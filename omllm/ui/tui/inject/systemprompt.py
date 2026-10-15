import typing as ta

from omcore import inject as inj
from omcore import lang

from .... import agent as agn
from ..config import Config
from ..types import TargetCwd


##


class CwdSystemPromptContributor(agn.SystemPromptContributor):
    def __init__(
            self,
            *,
            cwd: TargetCwd | None = None,
    ) -> None:
        super().__init__()

        self._cwd = cwd

    def get_system_prompt_parts(self) -> ta.Sequence[agn.SystemPromptPart] | None:
        if self._cwd is None:
            return None

        return [
            agn.SystemPromptPart(
                agn.SystemPromptPriority.DEFAULT,
                f'Current working directory: {self._cwd.v}',
            ),
        ]


##


@lang.cached_function
def system_prompt_contributors_binder() -> inj.ItemsBinderHelper[agn.SystemPromptContributor]:
    return inj.items_binder_helper[agn.SystemPromptContributor](agn.SystemPromptContributors)


##


def _bind_system_prompt_contributor_singleton(cls: ta.Any) -> inj.Elemental:
    return inj.as_elements(
        inj.bind(cls, singleton=True),
        system_prompt_contributors_binder().bind_item(to_key=cls),
    )


def bind_system_prompt(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = []

    lst.extend([
        _bind_system_prompt_contributor_singleton(CwdSystemPromptContributor),
    ])

    lst.extend([
        system_prompt_contributors_binder().bind_items_provider(singleton=True),

        inj.bind(agn.SystemPromptManager, singleton=True),
    ])

    return inj.as_elements(*lst)
