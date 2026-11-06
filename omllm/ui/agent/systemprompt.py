"""
The ui's contributions to the agent's system prompt: what the agent is and how it is to behave, whatever the user adds
to that, and what it is told of its surroundings. The injector wiring over these is in `inject/systemprompt.py`.
"""
import typing as ta

from omcore import dataclasses as dc

from ... import agent as agn
from ..types import TargetCwd


##


DEFAULT_SYSTEM_PROMPT: str = """
You are an AI assistant in an interactive terminal chat harness, working directly with one user on their own machine.
Most of what you are asked will be software engineering work in and around the user's working directory: reading,
writing, debugging, and explaining code, running commands, and answering questions about the system. But you may be
asked for help with anything at all, and should help just as readily. When you have tools, use them to look at the
actual state of things rather than guessing, and act on the request rather than only describing what could be done. When
you lack the means to do something, say so plainly. Be direct and concise: lead with the answer or the outcome, keep
explanations in proportion to the question, and write in simple markdown, which is rendered in the terminal. Take care
with anything destructive or hard to reverse, and check with the user first unless they have already told you to go
ahead.
""".strip()


@dc.dataclass(frozen=True)
class StandardSystemPromptContributor(agn.SystemPromptContributor):
    """
    The mission part of the system prompt. With no text given it is the default above; given any text it is that text
    alone, so an empty string is the way to have no mission part at all.
    """

    text: str | None = None

    def get_system_prompt_parts(self) -> ta.Sequence[agn.SystemPromptPart] | None:
        if (text := self.text) is None:
            text = DEFAULT_SYSTEM_PROMPT

        return [
            agn.SystemPromptPart(
                agn.SystemPromptPriority.MISSION,
                text,
            ),
        ]


@dc.dataclass(frozen=True)
class ExtraSystemPromptContributor(agn.SystemPromptContributor):
    """The user's own standing instructions: after the mission, ahead of anything about the environment."""

    text: str | None = None

    def get_system_prompt_parts(self) -> ta.Sequence[agn.SystemPromptPart] | None:
        if self.text is None:
            return None

        return [
            agn.SystemPromptPart(
                agn.SystemPromptPriority.USER,
                self.text,
            ),
        ]


##


@dc.dataclass(frozen=True)
class CwdSystemPromptContributor(agn.SystemPromptContributor):
    cwd: TargetCwd | None = None

    def get_system_prompt_parts(self) -> ta.Sequence[agn.SystemPromptPart] | None:
        if self.cwd is None:
            return None

        return [
            agn.SystemPromptPart(
                agn.SystemPromptPriority.ENVIRONMENT,
                f'Current working directory: {self.cwd.v}',
            ),
        ]
