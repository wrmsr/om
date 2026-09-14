"""
A process that allocates a sandbox and then dies without cleaning up, exactly like a test runner that got killed. Its
arguments are the backend name, the sandbox config as json, and the backend's connection details; it prints the name it
leaked.
"""
import os
import sys

from ..... import marshal as msh
from .....formats.json import all as json
from ....dbs import HostDbLoc
from ..backend import SandboxBackend
from ..backends.mysql import MysqlSandboxBackend
from ..backends.postgres import PostgresSandboxBackend
from ..backends.sqlite import SqliteSandboxBackend
from ..config import SandboxesConfig
from ..sandboxes import SandboxAllocator


##


def _make_backend(kind: str, cfg: SandboxesConfig, args: list[str]) -> SandboxBackend:
    if kind == 'postgres':
        host, port, password = args
        return PostgresSandboxBackend(cfg, HostDbLoc(host, int(port), username=cfg.role, password=password))

    elif kind == 'mysql':
        host, port, password = args
        return MysqlSandboxBackend(cfg, HostDbLoc(host, int(port), username=cfg.role, password=password))

    elif kind == 'sqlite':
        [base_dir] = args
        return SqliteSandboxBackend(cfg, base_dir=base_dir)

    else:
        raise ValueError(kind)


def _main() -> None:
    kind, cfg_json, *args = sys.argv[1:]
    cfg = msh.unmarshal(json.loads(cfg_json), SandboxesConfig)

    alloc = SandboxAllocator(_make_backend(kind, cfg, args), no_reap_on_open=True)
    alloc.__enter__()  # noqa
    sb = alloc.allocate()

    print(sb.name, flush=True)

    os._exit(0)  # noqa


if __name__ == '__main__':
    _main()
