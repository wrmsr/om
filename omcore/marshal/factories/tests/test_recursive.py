import threading
import typing as ta

from .... import dataclasses as dc
from ...api.marshaling import SimpleMarshaling
from ...standard.factories import StandardMarshalerFactory
from ...standard.factories import StandardUnmarshalerFactory


@dc.dataclass(frozen=True)
class Node:
    name: str
    children: ta.Sequence['Node'] = ()  # noqa


def _new_marshaling():
    return SimpleMarshaling(
        marshaler_factory=StandardMarshalerFactory(),
        unmarshaler_factory=StandardUnmarshalerFactory(),
    )


def test_concurrent_first_marshal_of_recursive_type():
    # The in-progress recursive-proxy state must not leak across threads: concurrent first-time construction of a
    # marshaler for the same recursive type previously handed one thread another thread's not-yet-set proxy, raising
    # 'recursive proxy not set'.
    obj = Node('r', (Node('a', (Node('b'),)), Node('c')))
    expected = {
        'name': 'r',
        'children': [
            {'name': 'a', 'children': [{'name': 'b', 'children': []}]},
            {'name': 'c', 'children': []},
        ],
    }

    num_threads = 8

    for _ in range(20):
        m = _new_marshaling()

        barrier = threading.Barrier(num_threads)
        results: list = []
        errors: list = []

        def work(m=m, barrier=barrier, results=results, errors=errors):
            barrier.wait()
            try:
                results.append(m.marshal(obj))
            except Exception as e:  # noqa
                errors.append(e)

        threads = [threading.Thread(target=work) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert all(r == expected for r in results)


def test_concurrent_first_unmarshal_of_recursive_type():
    v = {
        'name': 'r',
        'children': [
            {'name': 'a', 'children': [{'name': 'b', 'children': []}]},
            {'name': 'c', 'children': []},
        ],
    }
    expected = Node('r', (Node('a', (Node('b'),)), Node('c')))

    num_threads = 8

    for _ in range(20):
        m = _new_marshaling()

        barrier = threading.Barrier(num_threads)
        results: list = []
        errors: list = []

        def work(m=m, barrier=barrier, results=results, errors=errors):
            barrier.wait()
            try:
                results.append(m.unmarshal(v, Node))
            except Exception as e:  # noqa
                errors.append(e)

        threads = [threading.Thread(target=work) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert all(r == expected for r in results)
