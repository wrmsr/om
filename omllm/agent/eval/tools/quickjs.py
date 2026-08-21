import typing as ta

from omcore import dataclasses as dc
from omcore import lang
from omcore.formats.json import all as json

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
    ) -> None:
        super().__init__()

        self._permissions = permissions

    async def execute(self, ctx: ToolContext, params: QuickjsToolParams) -> str:
        await self._permissions.check_allowed(
            PermissionRequestor(tool_context=ctx),
            EvalPermissionTarget(
                language=EvalLanguage.JS,
                code=params.code,
            ),
        )

        js_ctx = quickjs.Context()
        if params.timeout_s is not None:
            js_ctx.set_time_limit(params.timeout_s)
        result = js_ctx.eval(params.code)
        return json.dumps(result)
