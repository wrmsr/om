"""
A process that allocates a sandbox and then dies without cleaning up, exactly like a test runner that got killed. Its
arguments are the sandbox config as json and the connection details, and it prints the name it leaked.
"""
import os
import sys

from ..... import marshal as msh
from .....formats.json import all as json
from ....dbs import HostDbLoc
from ..config import SandboxesConfig
from ..postgres import PostgresSandboxBackend
from ..sandboxes import SandboxAllocator


##


def _main() -> None:
    cfg_json, host, port, password = sys.argv[1:]
    cfg = msh.unmarshal(json.loads(cfg_json), SandboxesConfig)

    backend = PostgresSandboxBackend(cfg, HostDbLoc(host, int(port), username=cfg.role, password=password))

    alloc = SandboxAllocator(backend, no_reap_on_open=True)
    alloc.__enter__()  # noqa
    sb = alloc.allocate()

    print(sb.name, flush=True)

    os._exit(0)  # noqa


if __name__ == '__main__':
    _main()
