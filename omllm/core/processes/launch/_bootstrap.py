import typing as ta

from omcore import lang

from ._shim import MAX_FDS_PER_MESSAGE


##


SHIM_MODULE_NAME: ta.Final[str] = '__procs_shim__'


class _BootstrapConsts(lang.Namespace):
    SHIM_MODULE_NAME = SHIM_MODULE_NAME
    MAX_FDS_PER_MESSAGE = MAX_FDS_PER_MESSAGE


# Mirrors `_shim.receive_control` - the one piece of shim logic that has to exist before the shim source has arrived.
def _bootstrap_body() -> None:
    import array, json, os, socket, sys, types  # noqa

    s = socket.socket(fileno=int(sys.argv[1]))
    b = b''
    n = None
    fds = array.array('i')
    while n is None or len(fds) < n:
        m, a, _f, _a = s.recvmsg(4096, socket.CMSG_SPACE(_BootstrapConsts.MAX_FDS_PER_MESSAGE * fds.itemsize))
        if not m and not a:
            raise EOFError('control socket closed during handshake')
        for l, t, d in a:
            if l == socket.SOL_SOCKET and t == socket.SCM_RIGHTS:
                fds.frombytes(d[:len(d) - len(d) % fds.itemsize])  # noqa
        if n is None:
            b += m
            if b'\n' in b:
                n = int(json.loads(b.split(b'\n', 1)[0])['n'])
    s.detach()

    f = os.fdopen(fds[0], 'r', encoding='utf-8')
    p = json.loads(f.readline())
    src = f.read()
    f.close()

    mod = types.ModuleType(_BootstrapConsts.SHIM_MODULE_NAME)
    sys.modules[mod.__name__] = mod
    exec(compile(src, '<processes-shim>', 'exec'), mod.__dict__)
    mod.main(mod.ShimPayload(**p), list(fds[1:]))
