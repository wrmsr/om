from ..agent.inject.inject import bind_agent
from ..config import UiConfig


def test_inject():
    els = bind_agent(UiConfig())
    ana = els.analyze()
    deps = ana.known_dependencies_by_key()
    unk = {
        k
        for ks in deps.values()
        for k in ks or ()
        if k not in deps
    }
    print(unk)
