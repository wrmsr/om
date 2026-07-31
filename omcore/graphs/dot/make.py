import typing as ta

from .items import Edge
from .items import Graph
from .items import Node


T = ta.TypeVar('T')


##


def make_simple(graph: ta.Mapping[T, ta.Iterable[T]]) -> Graph:
    nodes = set(graph)
    edges = []
    for src, dsts in graph.items():
        for dst in dsts:
            nodes.add(dst)
            edges.append(Edge(src, dst))

    return Graph([
        *[Node(n) for n in nodes],
        *edges,
    ])
