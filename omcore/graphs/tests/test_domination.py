from .. import domination


def test_dom():
    g = domination.ListDictDirectedGraph([
        (0, [1, 2]),
        (1, [4]),
        (2, [3]),
        (3, [4]),
        (4, []),
    ])

    d = domination.DominatorTree(g, 0)

    assert d.immediate_dominators == {1: 0, 2: 0, 3: 2, 4: 0}
    assert d.dominator_tree == {0: {1, 2, 4}, 2: {3}}
    assert d.deep_dominated == {0: {1, 2, 3, 4}, 2: {3}}
    assert d.dominance_frontiers == {1: {4}, 2: {4}, 3: {4}}


def test_depth_first_cycle_yields_each_vertex_once():
    g = domination.ListDictDirectedGraph([
        (0, [1]),
        (1, [0]),
    ])

    assert list(g.yield_depth_first(0)) == [0, 1]


def test_dominators_with_cross_edge_between_siblings():
    g = domination.ListDictDirectedGraph([
        (0, [1, 2]),
        (1, []),
        (2, [1]),
    ])

    d = domination.DominatorTree(g, 0)

    assert d.immediate_dominators == {1: 0, 2: 0}


def test_dominance_frontiers_with_root_cycle():
    g = domination.ListDictDirectedGraph([
        (0, [1]),
        (1, [0]),
    ])

    d = domination.DominatorTree(g, 0)

    assert d.dominance_frontiers == {0: {0}, 1: {0}}
