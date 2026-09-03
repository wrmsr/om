# flake8: noqa: F401
import typing as ta

from omcore import cached
from omcore import collections as col
from omcore import dataclasses as dc

from ... import llm
from ...core import processes


##


class ToolExecutor(ta.Protocol):
    def __call__(self, ctx: ToolContext) -> ta.Awaitable[ToolResult]: ...



@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ToolEnvironment:
    cwd: str | None = None

    # The process scope tools spawn subprocesses into (foreground execs, and later background processes). Its lifetime
    # is managed by whoever set it - currently the ui, for the session.
    processes: processes.ProcessScope | None = None


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ToolContext:
    tool: Tool | None = None

    args: ta.Mapping[str, ta.Any]

    llm_tool_call: llm.ToolCall | None = None

    env: ToolEnvironment | None = None


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ToolResult:
    content: llm.TextContent

    error: BaseException | None = None

    @classmethod
    def of_error(cls, e: BaseException) -> ToolResult:
        """The result handed back to the model for a call which raised, worded so it can recover."""

        return cls(
            content=llm.TextContent(f'Error executing tool:\n\n{e!r}'),
            error=e,
        )


##


@ta.final
@dc.dataclass(frozen=True)
class ToolDescription:
    description: str

    params: ta.Mapping[str, str] | None = None


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class Tool:
    llm_tool: llm.Tool

    @property
    def name(self) -> str:
        return self.llm_tool.name

    executor: ToolExecutor


@ta.final
@dc.dataclass(frozen=True)
@dc.extra_class_params(terse_repr=True)
class ToolSet(ta.Sequence[Tool]):
    tools: ta.Sequence[Tool]

    @cached.property
    @dc.init
    def by_name(self) -> ta.Mapping[str, Tool]:
        return col.make_map(((t.name, t) for t in self.tools), strict=True)

    #

    def __iter__(self) -> ta.Iterator:
        return iter(self.tools)

    def __len__(self) -> int:
        return len(self.tools)

    @ta.overload
    def __getitem__(self, index: int | str, /) -> Tool:
        ...

    @ta.overload
    def __getitem__(self, index: slice, /) -> ta.Sequence[Tool]:  # noqa
        ...

    def __getitem__(self, index):
        if isinstance(index, str):
            return self.by_name[index]
        else:
            return self.tools[index]
