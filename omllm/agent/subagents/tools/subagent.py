import typing as ta

from omcore import dataclasses as dc

from .... import llm
from ...permissions.types import PermissionDecider
from ...permissions.types import PermissionRequest
from ...permissions.types import PermissionRequestor
from ...tools.classes import ToolClass
from ...types.tools import ToolContext
from ...types.tools import ToolDescription
from ...types.tools import ToolResult
from ...types.turns import AgentEndReason
from ..errors import UnknownSubagentProfileError
from ..permissions import SubagentPermissionTarget
from ..profiles import SubagentProfile
from ..profiles import SubagentProfiles
from ..types import SubagentRunner
from ..types import SubagentRunParams
from ..types import SubagentRunResult
from .details import SubagentToolResultDetails


##


@dc.dataclass(frozen=True)
class SubagentToolParams:
    prompt: str

    _: dc.KW_ONLY

    profile: str | None = None

    description: str | None = None


class SubagentTool(ToolClass[SubagentToolParams]):
    name: ta.Final = 'subagent'

    params_cls: ta.Final = SubagentToolParams

    def __init__(
            self,
            *,
            permissions: PermissionDecider,
            runner: SubagentRunner,
            profiles: SubagentProfiles,
    ) -> None:
        super().__init__()

        self._permissions = permissions
        self._runner = runner
        self._profiles = profiles

    #

    _DESCRIPTION: ta.ClassVar[str] = """
        Delegates a self-contained task to a subagent and waits for it to finish. The subagent is a fresh agent with
        its own empty context and its own tools, run to completion on your prompt; only its final message comes back
        to you, as this tool's result. Use it to keep large explorations, searches, and side tasks out of your own
        context, or to work on independent tasks at once by calling it several times in one message.

        The subagent knows nothing of this conversation: give it a complete, standalone prompt with every detail it
        needs, and say exactly what it should report back.
    """

    @property
    def description(self) -> ToolDescription:
        profiles = self._profiles

        return ToolDescription(
            '\n\n'.join([
                self._DESCRIPTION,
                'Profiles:\n' + '\n'.join(f'- {p.name}: {p.description}' for p in profiles),
            ]),
            dict(
                prompt='The complete, standalone task for the subagent, including what to report back.',
                profile=(
                    f'Which profile of subagent to run, one of: {", ".join(p.name for p in profiles)}. '
                    f'Defaults to {profiles.default.name}.'
                ),
                description='A few words naming the task, shown to the user beside the subagent while it runs.',
            ),
        )

    #

    def _lookup_profile(self, name: str | None) -> SubagentProfile:
        if name is None:
            return self._profiles.default

        try:
            return self._profiles.by_name[name]
        except KeyError:
            raise UnknownSubagentProfileError(name, [p.name for p in self._profiles]) from None

    def summarize(self, ctx: ToolContext, params: SubagentToolParams) -> str:
        profile = params.profile if params.profile is not None else self._profiles.default.name
        return f'{profile}: {params.description if params.description is not None else params.prompt}'

    #

    _END_REASON_NOTES: ta.ClassVar[ta.Mapping[AgentEndReason, str]] = {
        AgentEndReason.MAX_TURNS: 'the subagent reached its turn limit before finishing',
        AgentEndReason.LENGTH: "the subagent's output was cut off by the token limit",
        AgentEndReason.CONTEXT_LENGTH: 'the subagent stopped at its context window limit',
    }

    def _build_result_text(self, result: SubagentRunResult) -> str:
        text = result.text.strip()

        if result.reason is AgentEndReason.FAILED:
            lines = [f'The subagent failed: {result.error!r}']
            if text:
                lines.extend(['', 'Its last message before failing:', '', text])
            return '\n'.join(lines)

        if (note := self._END_REASON_NOTES.get(result.reason)) is not None:
            return '\n\n'.join([
                text or '(The subagent left no final message.)',
                f'[Note: {note}.]',
            ])

        return text or '(The subagent finished without a final message.)'

    async def execute(self, ctx: ToolContext, params: SubagentToolParams) -> ToolResult:
        profile = self._lookup_profile(params.profile)

        await self._permissions.check_allowed(PermissionRequest(
            PermissionRequestor(tool_context=ctx),
            SubagentPermissionTarget(profile.name),
        ))

        result = await self._runner.run_subagent(SubagentRunParams(
            profile=profile,
            prompt=params.prompt,
            env=ctx.env,
            progress=ctx.progress,
        ))

        return ToolResult(
            content=llm.TextContent(self._build_result_text(result)),
            error=result.error if result.reason is AgentEndReason.FAILED else None,
            details=SubagentToolResultDetails(
                run_id=result.run_id,
                profile=profile.name,
                reason=result.reason,
                num_turns=result.num_turns,
                usage=result.usage,
                messages=result.messages,
            ),
        )
