import typing as ta

from omcore import inject as inj
from omcore import lang

from .... import agent as agn
from ..config import AgentConfig
from ..systemprompt import CwdSystemPromptContributor
from ..systemprompt import ExtraSystemPromptContributor
from ..systemprompt import StandardSystemPromptContributor


##


@lang.cached_function
def system_prompt_contributors_binder() -> inj.ItemsBinderHelper[agn.SystemPromptContributor]:
    return inj.items_binder_helper[agn.SystemPromptContributor](agn.SystemPromptContributors)


##


def _provide_standard_system_prompt_contributor(config: AgentConfig) -> StandardSystemPromptContributor:
    return StandardSystemPromptContributor(text=config.system_prompt)


def _provide_extra_system_prompt_contributor(config: AgentConfig) -> ExtraSystemPromptContributor:
    return ExtraSystemPromptContributor(text=config.extra_system_prompt)


##


def _bind_system_prompt_contributor_singleton(cls: ta.Any, **kwargs: ta.Any) -> inj.Elemental:
    return inj.as_elements(
        inj.bind(cls, singleton=True, **kwargs),
        system_prompt_contributors_binder().bind_item(to_key=cls),
    )


def bind_system_prompt(config: AgentConfig) -> inj.Elements:
    lst: list[inj.Elemental] = []

    lst.extend([
        _bind_system_prompt_contributor_singleton(
            StandardSystemPromptContributor,
            to_fn=_provide_standard_system_prompt_contributor,
        ),

        _bind_system_prompt_contributor_singleton(
            ExtraSystemPromptContributor,
            to_fn=_provide_extra_system_prompt_contributor,
        ),

        _bind_system_prompt_contributor_singleton(CwdSystemPromptContributor),
    ])

    lst.extend([
        system_prompt_contributors_binder().bind_items_provider(singleton=True),

        inj.bind(agn.SystemPromptManager, singleton=True),
    ])

    return inj.as_elements(*lst)
