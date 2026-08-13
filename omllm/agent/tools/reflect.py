import collections.abc
import inspect
import typing as ta
import weakref

from omcore import check
from omcore import contextual as cxl
from omcore import dataclasses as dc
from omcore import reflect as rfl
from omcore.lite.reflect import get_optional_alias_arg
from omcore.lite.reflect import is_generic_alias
from omcore.lite.reflect import is_optional_alias

from ... import llm
from ..types.tools import Tool
from ..types.tools import ToolContext
from ..types.tools import ToolDescription
from ..types.tools import ToolResult


##


def instantiate_tool_params[T](
        params_cls: type[T],
        llm_tool_params: ta.Sequence[llm.ToolParam],
        ctx: ToolContext,
) -> T:
    params_kwargs: dict[str, ta.Any] = {}

    args = dict(ctx.args)
    missing: list[str] = []
    for tp in llm_tool_params:
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

    return params_cls(**params_kwargs)


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
        params: ta.Any = instantiate_tool_params(
            self.params_cls,
            self.llm_tool.params,
            ctx,
        )

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

_JSONSCHEMA_SEQUENCE_TYPES: ta.Container[type] = frozenset([
    collections.abc.Sequence,
    list,
])

_JSONSCHEMA_MAPPING_TYPES: ta.Container[type] = frozenset([
    collections.abc.Mapping,
    dict,
])


def _reflect_type(ty: object) -> llm.ToolParamType:
    rty = rfl.reflect_type(ty)

    if not isinstance(rty, rfl.Instance):
        raise TypeError(rty)

    rt_ty = check.isinstance(rty.type.runtime_object, type)

    if not rty.args:
        try:
            return _JSONSCHEMA_TYPES[rt_ty]
        except KeyError:
            raise TypeError(ty) from None

    if rt_ty in _JSONSCHEMA_SEQUENCE_TYPES:
        a_rty = check.single(rty.args)
        return {
            'type': 'array',
            'items': _reflect_type(a_rty),
        }

    if rt_ty in _JSONSCHEMA_MAPPING_TYPES:
        k_rty, v_rty = rty.args
        return {
            'type': 'object',
            'additionalProperties': _reflect_type(v_rty),  # FIXME: k_rty
        }

    raise TypeError(ty)


#


_TOOL_PARAMS_DC_RFL_CACHE: ta.MutableMapping[type, dc.ClassReflection] = weakref.WeakKeyDictionary()


def reflect_tool_params(
        params_cls: type,
        *,
        description: ToolDescription | None = None,
) -> ta.Sequence[llm.ToolParam]:
    check.arg(dc.is_dataclass(check.isinstance(params_cls, type)))

    try:
        dc_rfl = _TOOL_PARAMS_DC_RFL_CACHE[params_cls]
    except KeyError:
        dc_rfl = _TOOL_PARAMS_DC_RFL_CACHE[params_cls] = dc.reflect(params_cls)

    param_descs: dict[str, str] = {}
    if description is not None:
        param_descs = dict(description.params or {})

    tps: list[llm.ToolParam] = []
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

    return tps


#


def reflect_tool_fn(
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

    tps = reflect_tool_params(
        params_cls,
        description=description,
    )

    return_type: llm.ToolParamType | None = None
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
