import typing as ta

from omcore import dataclasses as dc

from ...permissions.types import PermissionDecider
from ...tools.classes import ToolClass
from ...types.tools import ToolContext
from ...types.tools import ToolDescription


##


@dc.dataclass(frozen=True)
class JsToolParams:
    src: str

    _: dc.KW_ONLY

    timeout_s: float | None = None


class JsTool(ToolClass[JsToolParams]):
    name: ta.Final = 'js'

    params_cls: ta.Final = JsToolParams

    description: ta.Final = ToolDescription(
        'Evaluates javascript code.',
        dict(
            src='The js code to evaluate.',
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

    async def execute(self, ctx: ToolContext, params: JsToolParams) -> str:
        raise NotImplementedError
