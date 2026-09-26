import os.path

from omcore import inject as inj
from omdev.home.paths import get_home_paths

from .... import agent as agn
from ....core.asyncs.base import AsyncJobRunner
from ....harness.commands.skills import SkillsCommand
from ....harness.skills.catalogs import SkillCatalog
from ....harness.skills.loading import LoadSkillsJob
from ....harness.skills.loading import LocalSkillLoader
from ....harness.skills.prompts import SkillsPromptContributor
from ....harness.skills.reading import SkillReader
from ....harness.skills.tools import ReadSkillTool
from ..config import Config
from .commands import harness_commands
from .prompts import prompt_contributors
from .tools import agent_tool_sets


##


async def _provide_catalog(config: Config, job_runner: AsyncJobRunner) -> SkillCatalog:
    if config.no_skills:
        return SkillCatalog()
    directories = config.skills_dirs
    if directories is None:
        directories = [os.path.join(get_home_paths().config_dir, 'llm', 'skills')]
    loader = LocalSkillLoader(LocalSkillLoader.Config(
        directories=list(directories),
        ignore_missing=config.skills_dirs is None,
    ))
    return await job_runner.run(LoadSkillsJob(loader), timeout=30.)


def _provide_skill_tools(catalog: SkillCatalog, tool: ReadSkillTool) -> agn.ToolSet:
    return agn.ToolSet([tool.tool()] if catalog.skills else [])


def bind_skills(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = [
        inj.bind(SkillCatalog, singleton=True, to_async_fn=_provide_catalog),
        inj.bind(SkillReader, singleton=True),

        inj.bind(SkillsCommand, singleton=True),
        harness_commands().bind_item(to_key=SkillsCommand),

        inj.bind(SkillsPromptContributor, singleton=True),
        prompt_contributors().bind_item(to_key=SkillsPromptContributor),
    ]

    if not config.no_skills:
        lst.extend([
            inj.bind(ReadSkillTool, singleton=True),
            agent_tool_sets().bind_item(to_fn=_provide_skill_tools),
        ])

    return inj.as_elements(*lst)
