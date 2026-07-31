import enum
import threading
import typing as ta

from ... import dataclasses as dc
from ..api.configs import ConfigRegistry
from ..api.naming import Naming
from ..api.types import SimpleMarshaling
from ..standard.factories import new_standard_marshaler_factory
from ..standard.factories import new_standard_unmarshaler_factory


class E(enum.Enum):
    X = 'x'
    Y = 'y'


@dc.dataclass(frozen=True)
class Node:
    name: str
    children: ta.Sequence['Node'] = ()  # noqa


@dc.dataclass(frozen=True)
class Foo:
    i: int
    s: str
    e: E | None = None
    m: ta.Mapping[str, int] = dc.field(default_factory=dict)


class _Unused:
    pass


def test_concurrent_marshaling_with_config_updates():
    cfgs = ConfigRegistry()
    m = SimpleMarshaling(
        config_registry=cfgs,
        marshaler_factory=new_standard_marshaler_factory(),
        unmarshaler_factory=new_standard_unmarshaler_factory(),
    )

    cases: ta.Sequence[tuple[ta.Any, ta.Any]] = [
        (Foo(1, 'a', E.X, {'k': 2}), Foo),
        (Node('r', (Node('a'), Node('b', (Node('c'),)))), Node),
        ([1, 2, 3], list[int]),
        ({'a': 1}, dict[str, int]),
        (E.Y, E),
        (None, int | None),
        (42, int | None),
    ]

    num_workers = 6
    iters = 50

    barrier = threading.Barrier(num_workers + 1)
    errors: list = []

    def work():
        barrier.wait()
        try:
            for _ in range(iters):
                for obj, ty in cases:
                    assert m.unmarshal(m.marshal(obj, ty), ty) == obj
        except Exception as e:  # noqa
            errors.append(e)

    def churn():
        barrier.wait()
        try:
            for _ in range(iters):
                cfgs.update(_Unused, Naming.CAMEL, mode='override')
        except Exception as e:  # noqa
            errors.append(e)

    threads = [threading.Thread(target=work) for _ in range(num_workers)]
    threads.append(threading.Thread(target=churn))
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
