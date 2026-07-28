import collections.abc
import inspect
import typing as ta

from omcore import check
from omcore import contextual as cxl
from omcore import dataclasses as dc
from omcore.lite.reflect import get_optional_alias_arg
from omcore.lite.reflect import is_generic_alias
from omcore.lite.reflect import is_optional_alias

from ... import llm
from ..types.tools import Tool
from ..types.tools import ToolContext
from ..types.tools import ToolDescription
from ..types.tools import ToolResult


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class _ReflectedToolExecutor:
    fn: ta.Callable
    llm_tool: llm.Tool
    params_cls: type
    params_param: str
    ctx_param: str | None = None

    async def __call__(self, ctx: ToolContext) -> ToolResult:
        params_kwargs: dict[str, ta.Any] = {}

        args = dict(ctx.args)
        missing: list[str] = []
        for tp in self.llm_tool.params:
            try:
                av = args.pop(tp.name)
            except KeyError:
                if not tp.optional:
                    missing.append(tp.name)
                continue
            params_kwargs[tp.name] = av

        if missing:
            raise TypeError(f'Missing arguments: {missing}!r')

        if (unexpected := list(args)):
            raise TypeError(f'Unexpected arguments: {unexpected}!r')

        params = self.params_cls(**params_kwargs)

        kwargs: dict[str, ta.Any] = {
            self.params_param: params,
        }

        if self.ctx_param is not None:
            kwargs[self.ctx_param] = ctx

        rv = await self.fn(**kwargs)

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
        description: ToolDescription,
        fn: ta.Callable,
        *,
        name: str | None = None,
) -> Tool:
    if name is None:
        name = fn.__name__

    fn_sig = inspect.signature(fn)
    fn_th = ta.get_type_hints(fn)

    params_param: str | None = None
    params_cls: type | None = None
    ctx_param: str | None = None
    for sp in fn_sig.parameters.values():
        ty = fn_th[sp.name]

        if ty == ToolContext:
            check.state(not cxl.is_unbound_param(sp.default))
            check.none(ctx_param)
            ctx_param = sp.name
            continue

        if cxl.is_unbound_param(sp.default):
            continue

        if isinstance(ty, type) and dc.is_dataclass(ty):
            check.none(params_param)
            params_param = sp.name
            params_cls = ty
            continue

        raise TypeError(f'Unhandled parameter: {sp}')

    if params_param is None or params_cls is None:
        raise TypeError('No params param')

    param_descs = dict(description.params or {})

    tps: list[llm.ToolParam] = []
    dc_rfl = dc.reflect(check.not_none(params_cls))
    for dc_fld in dc_rfl.fields.values():
        ty = dc_fld.type

        optional = False
        if dc_fld.default is not dc.MISSING:
            optional = True
            if is_optional_alias(ty):
                ty = get_optional_alias_arg(ty)
        else:
            check.arg(not is_optional_alias(ty))

        tp_desc = param_descs.pop(dc_fld.name, None)

        tps.append(llm.ToolParam(
            name=dc_fld.name,
            description=tp_desc,
            type=_reflect_type(ty),
            optional=optional,
        ))

    if param_descs:
        raise TypeError(f'Mismatched parameter descriptions: {list(param_descs)}')

    return_type: str | None = None
    if 'return' in fn_th:
        ret_ty = fn_th['return']
        if is_generic_alias(ret_ty) and ta.get_origin(ret_ty) is collections.abc.Awaitable:
            [ret_ty] = ta.get_args(ret_ty)
        return_type = _reflect_type(ret_ty)

    return Tool(
        llm_tool=(llm_tool := llm.Tool(
            name=name,
            description=description.description,
            params=tps,
            type=return_type,
        )),
        executor=_ReflectedToolExecutor(
            fn=fn,
            llm_tool=llm_tool,
            params_cls=params_cls,
            params_param=params_param,
            ctx_param=ctx_param,
        ),
    )
