"""
The ui's contributions to the agent's system prompt: what the agent is and how it is to behave, whatever the user adds
to that, and what it is told of its surroundings. The injector wiring over these is in `inject/systemprompt.py`.
"""
import datetime
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ... import agent as agn


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


_CONTAINER_RUNTIME_NAMES: ta.Mapping[str, str] = {
    'docker': 'Docker',
    'podman': 'Podman',
}

REMOTE_ENVIRONMENT_SYSTEM_PROMPT: str = (
    "Your tools run in this environment rather than on the user's own machine: the files, commands, and processes you "
    "work with are its own, not the user's."
)


def render_environment_system_prompt(
        info: agn.EnvironmentInfo,
        *,
        start_date: datetime.date,
) -> str:
    """One block of the facts of the environment, as they stood when it was asked."""

    lines = [
        'Environment at startup:',
        f'- Platform: {info.system} {info.release}, {info.machine}',
    ]

    host = f'- Host: {info.hostname}'
    if (container := info.container) is not None:
        host += f' (a {_CONTAINER_RUNTIME_NAMES.get(container, container)} container)'
    lines.append(host)

    if (user := info.user) is not None:
        user_line = ''
        if (name := user.name) is not None:
            user_line += f'- User: {name}'
        if (shell := user.shell) is not None:
            user_line += f', shell {shell}'
        if (home := user.home) is not None:
            user_line += f', home {home}'
        if user_line:
            lines.append(user_line)

    lines.extend([
        f'- Working directory: {info.cwd}',
        f"- Start date: {start_date.isoformat()}, the user's local date",
    ])

    text = '\n'.join(lines)

    if info.remote:
        text = '\n\n'.join([text, REMOTE_ENVIRONMENT_SYSTEM_PROMPT])

    return text


@dc.dataclass(frozen=True)
class EnvironmentSystemPromptContributor(agn.SystemPromptContributor):
    """
    What the agent is told of its surroundings: the environment is asked when the prompt is built - at the agent's setup
    - and the start date is that moment's. Baked into the context from then on, not kept up to date.
    """

    environment_info: agn.EnvironmentInfoGetter

    async def get_system_prompt_parts(self) -> ta.Sequence[agn.SystemPromptPart] | None:
        info = await self.environment_info()

        return [
            agn.SystemPromptPart(
                agn.SystemPromptPriority.ENVIRONMENT,
                render_environment_system_prompt(
                    info,
                    start_date=lang.localnow().date(),
                ),
            ),
        ]
