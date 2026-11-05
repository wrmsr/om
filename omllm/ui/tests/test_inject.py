from ..agent.inject.inject import bind_agent
from ..config import UiConfig


def test_inject():
    els = bind_agent(UiConfig())
    ana = els.analyze()
    deps = ana.known_dependencies_by_key()
    unk = {
        k
        for ks in deps.values()
        if ks
        for k in ks.required
        if k not in deps
    }
    print(unk)
