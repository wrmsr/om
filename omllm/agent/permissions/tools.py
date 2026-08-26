import typing as ta

from omcore import dataclasses as dc
from omcore import lang
from omcore import marshal as msh

from ...core import fieldhash as fh
from .types import PermissionMatchContext
from .types import PermissionMatcher


##


# @om-manifest omcore.marshal.SubtypeManifest(base='$.agent.permissions.types.PermissionMatcher')
@ta.final
@dc.dataclass(frozen=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class ToolPermissionMatcher(PermissionMatcher, lang.Final):
    tool: str
    child: PermissionMatcher | None = dc.xfield(None) | msh.dc_field_options(omit_if=lang.is_none)

    @lang.cached_function
    def _field_hash(self) -> fh.FieldHashValue:
        return fh.FieldHashObject('tool', (
            fh.FieldHashField('tool', self.tool),
        ))

    def match(self, ctx: PermissionMatchContext) -> bool:
        if ctx.requestor is None or (tx := ctx.requestor.tool_context) is None:
            return False

        if (tool := tx.tool) is None or tool.name != self.tool:
            return False

        if self.child is not None and not self.child.match(ctx):
            return False

        return True
