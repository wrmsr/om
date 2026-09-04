import typing as ta

from omcore import dataclasses as dc
from omcore import lang
from omcore.formats.json import all as json

from ....core.asyncs.base import AsyncJob
from ....core.asyncs.base import AsyncJobRunner
from ....core.asyncs.base import AsyncJobTimeoutError
from ...permissions.types import PermissionDecider
from ...permissions.types import PermissionRequestor
from ...tools.classes import ToolClass
from ...types.tools import ToolContext
from ...types.tools import ToolDescription
from ..permissions import EvalLanguage
from ..permissions import EvalPermissionTarget


with lang.auto_proxy_import(globals()):
    from omdev.js import quickjs


##


@dc.dataclass(frozen=True)
class QuickjsToolParams:
    code: str

    _: dc.KW_ONLY

    timeout_s: float | None = None


class _QuickjsEvalJob(AsyncJob[ta.Any]):
    """An eval off the loop: the engine releases the GIL while it runs, and its interrupt flag is thread-safe."""

    def __init__(self, context: quickjs.Context, code: str) -> None:
        super().__init__()

        self._context = context
        self._code = code

    def run(self) -> ta.Any:
        return self._context.eval(self._code)

    def interrupt(self) -> None:
        self._context.interrupt()


class QuickjsTool(ToolClass[QuickjsToolParams]):
    name: ta.Final = 'quickjs'

    params_cls: ta.Final = QuickjsToolParams

    description: ta.Final = ToolDescription(
        'Evaluates javascript code using the quickjs engine.',
        dict(
            code='The js code to evaluate.',
            timeout_s='An optional timeout in seconds.',
        ),
    )

    def __init__(
            self,
            *,
            permissions: PermissionDecider,
            job_runner: AsyncJobRunner,
    ) -> None:
        super().__init__()

        self._permissions = permissions
        self._job_runner = job_runner

    async def execute(self, ctx: ToolContext, params: QuickjsToolParams) -> str:
        await self._permissions.check_allowed(
            PermissionRequestor(tool_context=ctx),
            EvalPermissionTarget(
                language=EvalLanguage.JS,
                code=params.code,
            ),
        )

        # The timeout is the runner's to keep, not the engine's: its interruption reaches the same engine hook a time
        # limit would, and a cancellation of the call reaches it the same way.
        try:
            result = await self._job_runner.run(
                _QuickjsEvalJob(quickjs.Context(), params.code),
                timeout=params.timeout_s,
            )
        except AsyncJobTimeoutError:
            raise ValueError(f'Evaluation timed out after {params.timeout_s}s') from None

        if isinstance(result, quickjs.Object):
            # An object or array is stringified by the engine itself; what has no JSON form (a function) is undefined.
            return text if (text := result.json()) is not None else 'undefined'

        return json.dumps(result)
