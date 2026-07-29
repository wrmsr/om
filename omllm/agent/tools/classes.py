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
            type='string',
        )

    @lang.cached_function
    def tool(self) -> Tool:
        return Tool(
            llm_tool=self.llm_tool(),
            executor=self.execute_context,
        )

    async def execute_context(self, ctx: ToolContext) -> ToolResult:
        params = instantiate_tool_params(
            self.params_cls,
            self.llm_tool().params,
            ctx,
        )

        out = await self.execute(ctx, params)

        return ToolResult(
            content=llm.TextContent(out),
        )

    @abc.abstractmethod
    async def execute(self, ctx: ToolContext, params: P) -> str:
        raise NotImplementedError
