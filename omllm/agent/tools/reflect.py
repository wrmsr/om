import collections.abc
import inspect
import typing as ta

from omcore import check
from omcore import lang
from omcore.lite.reflect import get_optional_alias_arg
from omcore.lite.reflect import is_generic_alias
from omcore.lite.reflect import is_optional_alias

from ... import llm
from ..types.tools import Tool
from ..types.tools import ToolContext
from ..types.tools import ToolResult


with lang.auto_proxy_import(globals()):
    from omdev.py import docstrings


##


class _ReflectedToolExecutor:
    def __init__(
            self,
            fn: ta.Callable,
            llm_tool: llm.Tool,
            *,
            ctx_param: str | None = None,
    ) -> None:
        super().__init__()

        self._fn = fn
        self._llm_tool = llm_tool
        self._ctx_param = ctx_param

    async def __call__(self, ctx: ToolContext) -> ToolResult:
        kwargs: dict[str, ta.Any] = {}

        if self._ctx_param is not None:
            kwargs[self._ctx_param] = ctx

        args = dict(ctx.args)
        missing: list[str] = []
        for tp in self._llm_tool.params:
            try:
                av = args.pop(tp.name)
            except KeyError:
                if not tp.optional:
                    missing.append(tp.name)
                continue
            kwargs[tp.name] = av

        if missing:
            raise TypeError(f'Missing arguments: {missing}!r')

        if (unexpected := list(args)):
            raise TypeError(f'Unexpected arguments: {unexpected}!r')

        rv = await self._fn(**kwargs)

        return ToolResult(
            content=llm.TextContent(
                check.isinstance(rv, str),  # FIXME: lol
            ),
        )


##


_JSONSCHEMA_TYPES: ta.Mapping[type, str] = {
    int: 'integer',
    float: 'number',
    str: 'string',
    bool: 'boolean',
}


def _reflect_type(ty: ta.Any) -> str:
    return _JSONSCHEMA_TYPES[ty]


def reflect_tool(
        fn: ta.Callable,
        *,
        name: str | None = None,
        description: str | None = None,
) -> Tool:
    if name is None:
        name = fn.__name__

    dsps: dict[str, docstrings.DocstringParam] = {}
    if (doc := inspect.getdoc(fn)) is not None:
        ds = docstrings.parse(doc)

        dsps.update({dsp.arg_name: dsp for dsp in ds.params})

        if description is None:
            description = ds.description

    sig = inspect.signature(fn)
    th = ta.get_type_hints(fn)

    tps: list[llm.ToolParam] = []
    ctx_param: str | None = None
    for sp in sig.parameters.values():
        ty = th[sp.name]

        if ty == ToolContext:
            check.none(ctx_param)
            ctx_param = sp.name
            continue

        optional = False
        if sp.default is not inspect.Signature.empty:
            optional = True
            if is_optional_alias(ty):
                ty = get_optional_alias_arg(ty)
        else:
            check.arg(not is_optional_alias(ty))

        tp_desc: str | None = None
        if (dsp := dsps.get(sp.name)) is not None:
            tp_desc = dsp.description

        tps.append(llm.ToolParam(
            name=sp.name,
            description=tp_desc,
            type=_reflect_type(ty),
            optional=optional,
        ))

    return_type: str | None = None
    if 'return' in th:
        ret_ty = th['return']
        if is_generic_alias(ret_ty) and ta.get_origin(ret_ty) is collections.abc.Awaitable:
            [ret_ty] = ta.get_args(ret_ty)
        return_type = _reflect_type(ret_ty)

    return Tool(
        llm_tool=(llm_tool := llm.Tool(
            name=name,
            description=description,
            params=tps,
            type=return_type,
        )),
        executor=_ReflectedToolExecutor(
            fn,
            llm_tool,
            ctx_param=ctx_param,
        ),
    )
