import typing as ta

from omcore import inject as inj
from omcore import lang

from .... import agent as agn
from ..config import AgentConfig
from ..systemprompt import EnvironmentSystemPromptContributor
from ..systemprompt import ExtraSystemPromptContributor
from ..systemprompt import StandardSystemPromptContributor


##


@lang.cached_function
def system_prompt_contributors_binder() -> inj.ItemsBinderHelper[agn.SystemPromptContributor]:
    return inj.items_binder_helper[agn.SystemPromptContributor](agn.SystemPromptContributors)


##


def _bind_system_prompt_contributor_singleton(cls: ta.Any, **kwargs: ta.Any) -> inj.Elemental:
    return inj.as_elements(
        inj.bind(cls, singleton=True, **kwargs),
        system_prompt_contributors_binder().bind_item(to_key=cls),
    )


def bind_system_prompt_infrastructure(config: AgentConfig) -> inj.Elements:
    """
    Host-level system prompt contributors shared across agents (root and subagents alike). Each agent injector builds
    its own `SystemPromptContributors` collection and `SystemPromptManager`, referencing these as needed.
    """

    lst: list[inj.Elemental] = [
        inj.bind(EnvironmentSystemPromptContributor, singleton=True),
    ]

    if config.fs:
        lst.append(inj.bind(agn.FsSystemPromptContributor, singleton=True))

    return inj.as_elements(*lst)


def bind_root_system_prompt(config: AgentConfig) -> inj.Elements:
    """Root-agent system prompt contributor bindings."""

    lst: list[inj.Elemental] = [
        _bind_system_prompt_contributor_singleton(
            StandardSystemPromptContributor,
            to_const=StandardSystemPromptContributor(text=config.system_prompt),
        ),

        _bind_system_prompt_contributor_singleton(
            ExtraSystemPromptContributor,
            to_const=ExtraSystemPromptContributor(text=config.extra_system_prompt),
        ),

        system_prompt_contributors_binder().bind_item(to_key=EnvironmentSystemPromptContributor),
    ]

    if config.fs:
        lst.append(system_prompt_contributors_binder().bind_item(to_key=agn.FsSystemPromptContributor))

    return inj.as_elements(*lst)
