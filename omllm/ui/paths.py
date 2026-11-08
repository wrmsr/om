"""The agent's working directory as its state has it, and paths shown relative to it."""
from omcore import dataclasses as dc

from .. import agent as agn
from ..core import ui


##


def get_agent_cwd(agent: agn.Agent) -> str | None:
    """The agent's working directory, which its setup resolved; None until then."""

    if (env := agent.state.tool_env) is None:
        return None
    return env.cwd


@dc.dataclass(frozen=True)
class AgentCwdDisplayPathResolver(ui.DisplayPathResolver):
    """
    Paths beneath the agent's working directory shown relative to it. Asked each time, so it follows the state: the
    directory is known only once the agent is set up, after the frontend's renderers are built.
    """

    agent: agn.Agent

    def resolve_display_path(self, path: str) -> str:
        if (cwd := get_agent_cwd(self.agent)) is None:
            return path
        return ui.CwdDisplayPathResolver(cwd).resolve_display_path(path)
