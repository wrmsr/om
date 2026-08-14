from .... import collections as col
from .impls import IMPLEMENTATIONS
from .interfaces import SUITES
from .interfaces import BenchmarkContext
from .interfaces import BenchmarkData
from .interfaces import resolve_suites
from .workloads import WORKLOADS
from .workloads import prepare_trial


def test_public_btree_exports():
    assert col.BtreeMap.__name__ == 'BtreeMap'
    assert col.BtreeSeq.__name__ == 'BtreeSeq'
    assert callable(col.new_btree_map)
    assert callable(col.new_btree_seq)


def test_interface_hierarchy():
    assert resolve_suites(('sorted_mutable_mapping',)) == (
        'collection',
        'mapping',
        'sorted_mapping',
        'mutable_mapping',
        'sorted_mutable_mapping',
    )
    assert resolve_suites(('persistent_mapping',)) == (
        'collection',
        'mapping',
        'persistent_mapping',
    )


def test_registrations_smoke():
    names = [implementation.name for implementation in IMPLEMENTATIONS]
    assert len(names) == len(set(names))
    assert all(suite in SUITES for implementation in IMPLEMENTATIONS for suite in implementation.suites)
    assert all(workload.suite in SUITES for workload in WORKLOADS)

    data = BenchmarkData.make(10)
    for implementation in IMPLEMENTATIONS:
        if not implementation.available:
            continue
        context = BenchmarkContext(implementation, data)
        supported = set(implementation.resolved_suites)
        for workload in WORKLOADS:
            if workload.suite not in supported:
                continue
            result = prepare_trial(context, workload, 1).run()
            del result
