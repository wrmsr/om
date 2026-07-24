import typing as ta

from .text import _render_text_simple
from .text import get_top_level_nodes


if ta.TYPE_CHECKING:
    from .._models.dag import PackageDAG


##


def render_freeze(tree: PackageDAG, *, max_depth: float, list_all: bool = True) -> None:
    nodes = get_top_level_nodes(tree, list_all=list_all)
    _render_text_simple(tree, nodes, max_depth, context=None, frozen=True, bullet='')
