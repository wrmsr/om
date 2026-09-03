import abc
import typing as ta

from omcore import lang

from ... import llm
from ..types.tools import Tool
from ..types.tools import ToolContext
from ..types.tools import ToolDescription
from ..types.tools import ToolResult
from .reflect import instantiate_tool_params
from .reflect import reflect_tool_params


P = ta.TypeVar('P')


##


class ToolClass(lang.Abstract, ta.Generic[P]):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def params_cls(self) -> type[P]:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def description(self) -> ToolDescription:
        raise NotImplementedError

    @lang.cached_function
    def llm_tool(self) -> llm.Tool:
        return llm.Tool(
            name=self.name,
            description=(description := self.description).description,
            params=reflect_tool_params(
                self.params_cls,
                description=description,
            ),
            return_type=llm.ToolDtype.of(str),
        )

    @lang.cached_function
    def tool(self) -> Tool:
        return Tool(
            llm_tool=self.llm_tool(),
            executor=self.execute_context,
        )

    #

    def _build_result(self, out: str) -> ToolResult:
        return ToolResult(
            content=llm.TextContent(out),
        )

    _error_exception_types: tuple[type[BaseException], ...] = (
        Exception,
    )

    def _build_error_result(self, e: BaseException) -> ToolResult:
        return ToolResult.of_error(e)

    async def execute_context(self, ctx: ToolContext) -> ToolResult:
        # Argument binding is inside the try: the model sending malformed or missing arguments is an error result for
        # it to correct, not a fault in the loop.
        try:
            params = instantiate_tool_params(
                self.params_cls,
                self.llm_tool().params,
                ctx,
            )

            out = await self.execute(ctx, params)

        except self._error_exception_types as e:
            return self._build_error_result(e)

        else:
            return self._build_result(out)

    @abc.abstractmethod
    async def execute(self, ctx: ToolContext, params: P) -> str:
        raise NotImplementedError
