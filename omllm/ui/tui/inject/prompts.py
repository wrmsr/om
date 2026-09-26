from omcore import inject as inj
from omcore import lang

from ....harness.prompts.base import PromptContributor
from ....harness.prompts.base import PromptContributors
from ....harness.prompts.builders import PromptBuilder
from ....harness.prompts.standard import CodingPromptContributor
from ....harness.prompts.standard import TextPromptContributor
from ....harness.prompts.standard import ToolsPromptContributor
from ..config import Config


##


@lang.cached_function
def prompt_contributors() -> inj.ItemsBinderHelper[PromptContributor]:
    return inj.items_binder_helper[PromptContributor](PromptContributors)


def bind_prompts(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = [
        inj.bind(CodingPromptContributor, singleton=True),
        prompt_contributors().bind_item(to_key=CodingPromptContributor),

        inj.bind(ToolsPromptContributor, singleton=True),
        prompt_contributors().bind_item(to_key=ToolsPromptContributor),

        prompt_contributors().bind_items_provider(singleton=True),
        inj.bind(PromptBuilder, singleton=True),
    ]

    if config.system_prompt is not None:
        lst.append(prompt_contributors().bind_item(to_const=TextPromptContributor('custom', config.system_prompt)))

    return inj.as_elements(*lst)
