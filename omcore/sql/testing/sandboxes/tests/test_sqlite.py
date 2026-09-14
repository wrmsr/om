import os
import tempfile

import pytest

from ....api import querierfuncs as qf
from ....tests.harness import HarnessSandboxes
from ..config import SandboxesConfig
from ..errors import SandboxSafetyError
from ..sandboxes import SandboxAllocator
from ..sqlite import SqliteSandboxBackend
from .scenarios import BackendScenario
from .scenarios import check_isolation
from .scenarios import check_reaper
from .scenarios import check_reaper_after_hard_exit
from .scenarios import check_reaper_lock_contention


##


def _scenario(backend: SqliteSandboxBackend) -> BackendScenario:
    base = backend.base_dir

    def namespace_of(q, kind):
        # the sandbox's database file lives in a directory named after it
        [(_, _, path)] = [r.values for r in qf.query_all(q, 'pragma database_list') if r.values[1] == 'main']
        return os.path.basename(os.path.dirname(path))

    return BackendScenario(
        make_backend=lambda **kw: SqliteSandboxBackend(SandboxesConfig(**kw), base_dir=base),
        namespace_of=namespace_of,
        list_namespaces=lambda q: {d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))},
        plant=lambda q, name, kind: os.mkdir(os.path.join(base, name)),
        unplant=lambda q, name, kind: os.rmdir(os.path.join(base, name)),
        orphan_backend='sqlite',
        orphan_args=[base],
    )


##


def test_isolation(harness) -> None:
    alloc = harness[HarnessSandboxes].sqlite()
    check_isolation(_scenario(alloc.backend), alloc)


def test_reaper(harness) -> None:
    check_reaper(_scenario(harness[HarnessSandboxes].sqlite().backend))


def test_reaper_after_hard_exit(harness) -> None:
    check_reaper_after_hard_exit(_scenario(harness[HarnessSandboxes].sqlite().backend))


def test_reaper_lock_contention(harness) -> None:
    check_reaper_lock_contention(_scenario(harness[HarnessSandboxes].sqlite().backend))


def test_guard_refuses_unprefixed_base_dir() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        backend = SqliteSandboxBackend(SandboxesConfig(), base_dir=os.path.join(tmp, 'somewhere_else'))
        with pytest.raises(SandboxSafetyError):
            with SandboxAllocator(backend):
                pass
        # and nothing was created outside the prefix, either
        assert not os.path.exists(os.path.join(tmp, 'somewhere_else'))
