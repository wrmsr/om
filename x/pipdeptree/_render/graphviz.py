import collections
import json
import math
import re
import subprocess
import sys
import tempfile
import typing as ta
import webbrowser

from omcore import check

from .._models import DistPackage
from .._models import ReqPackage


if ta.TYPE_CHECKING:
    from .._cli import RenderContext
    from .._models import PackageDAG


##


_BARE_ID = re.compile(r'[A-Za-z_][A-Za-z_0-9]*\Z')


class GraphvizError(Exception):
    """The Graphviz command could not render the requested format."""


def _quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _id(value: str) -> str:
    return value if _BARE_ID.fullmatch(value) else _quote(value)


def _node(key: str, label: str, *, missing: bool = False) -> str:
    style = ', style=dashed' if missing else ''
    return f'\t{_id(key)} [label={_quote(label)}{style}]\n'


def _edge(parent: str, child: str, *, label: str = '', missing: bool = False) -> str:
    if missing:
        attributes = ' [style=dashed]'
    elif label:
        attributes = f' [label={_quote(label)}]'
    else:
        attributes = ''
    return f'\t{_id(parent)} -> {_id(child)}{attributes}\n'


def render_graphviz(
    tree: PackageDAG,
    *,
    output_format: str,
    reverse: bool,
    max_depth: float = math.inf,
    context: RenderContext | None = None,
) -> None:
    output = dump_graphviz(tree, output_format=output_format, is_reverse=reverse, max_depth=max_depth, context=context)
    print_graphviz(output, output_format=output_format)


def dump_graphviz(
    tree: PackageDAG,
    output_format: str = 'dot',
    is_reverse: bool = False,  # noqa: FBT001, FBT002
    max_depth: float = math.inf,
    context: RenderContext | None = None,
) -> str | bytes:
    """Build DOT source and optionally render it with the Graphviz `dot` command."""

    body: list[str] = []
    if is_reverse:
        _build_reverse_graph(tree, body, max_depth, context)
    else:
        _build_forward_graph(tree, body, max_depth, context)
    source = 'digraph {\n' + ''.join(sorted(body)) + '}\n'
    if output_format == 'dot':
        return source

    try:
        result = subprocess.run(
            ['dot', f'-T{output_format}'],
            input=source.encode('utf-8'),
            capture_output=True,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GraphvizError(f'cannot run Graphviz dot: {exc}') from exc
    if result.returncode:
        message = result.stderr.decode('utf-8', errors='replace').strip()
        raise GraphvizError(message or f'Graphviz dot exited with status {result.returncode}')
    try:
        return result.stdout.decode('utf-8')
    except UnicodeDecodeError:
        return result.stdout


def print_graphviz(dump_output: str | bytes, *, output_format: str = 'dot') -> None:
    """Write graph output to stdout, or open binary output when attached to a terminal."""

    if isinstance(dump_output, str):
        print(dump_output, end='')  # noqa: T201
        return

    if sys.stdout.isatty():
        with tempfile.NamedTemporaryFile(suffix=f'.{output_format}', delete=False) as temp_file:
            temp_file.write(dump_output)
            temp_path = temp_file.name
        print(f'Binary output file written to: {temp_path}', file=sys.stderr)  # noqa: T201
        if not webbrowser.open(temp_path):
            print('Could not open file with default application. Please open it manually.', file=sys.stderr)  # noqa: T201
        return

    sys.stdout.buffer.write(dump_output)


def _build_reverse_graph(
    tree: PackageDAG,
    body: list[str],
    max_depth: float,
    context: RenderContext | None,
) -> None:
    """Build Graphviz nodes and edges for a reversed dependency tree."""

    visited = _compute_reachable_depths(tree, _get_root_keys(tree), max_depth)
    for dep_rev, parents in tree.items():
        if visited is not None and dep_rev.key not in visited:
            continue
        dep_rev_rp = check.isinstance(dep_rev, ReqPackage)
        label = f'{dep_rev_rp.project_name}\n{dep_rev_rp.installed_version}'
        if context and (extra := context.build_node_extra_label(dep_rev_rp.key, tree, '\n')):
            label += f'\n{extra}'
        body.append(_node(dep_rev_rp.key, label))
        if visited is None or visited[dep_rev_rp.key] < max_depth:
            for parent in parents:
                parent_dp = check.isinstance(parent, DistPackage)
                if visited is not None and parent_dp.key not in visited:
                    continue
                body.append(_edge(dep_rev_rp.key, parent_dp.key, label=parent_dp.edge_label))


def _build_forward_graph(
    tree: PackageDAG,
    body: list[str],
    max_depth: float,
    context: RenderContext | None,
) -> None:
    """Build Graphviz nodes and edges for a forward dependency tree."""

    visited = _compute_reachable_depths(tree, _get_root_keys(tree), max_depth)
    for pkg, deps in tree.items():
        if visited is not None and pkg.key not in visited:
            continue
        label = f'{pkg.project_name}\n{pkg.version}'
        if context and (extra := context.build_node_extra_label(pkg.key, tree, '\n')):
            label += f'\n{extra}'
        body.append(_node(pkg.key, label))
        if visited is None or visited[pkg.key] < max_depth:
            for dep in deps:
                if visited is not None and dep.key not in visited:
                    continue
                if dep.is_missing:
                    body.append(_node(dep.key, f'{dep.project_name}\n(missing)', missing=True))
                    body.append(_edge(pkg.key, dep.key, missing=True))
                else:
                    body.append(_edge(pkg.key, dep.key, label=dep.edge_label))


def _compute_reachable_depths(tree: PackageDAG, root_keys: set[str], max_depth: float) -> dict[str, int] | None:
    """Find the nodes reachable from roots within the requested depth."""

    if max_depth == math.inf:
        return None
    visited: dict[str, int] = {}
    queue: collections.deque[tuple[str, int]] = collections.deque((key, 0) for key in root_keys)
    while queue:
        key, depth = queue.popleft()
        if key in visited:
            continue
        visited[key] = depth
        if depth < max_depth:
            for child in tree.get_children(key):
                if child.key not in visited:
                    queue.append((child.key, depth + 1))
    return visited


def _get_root_keys(tree: PackageDAG) -> set[str]:
    """Return package keys that are not dependencies of another package."""

    dep_keys = {dep.key for deps in tree.values() for dep in deps}
    roots = {str(pkg.key) for pkg in tree if pkg.key not in dep_keys}
    return roots or {str(pkg.key) for pkg in tree}
