import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile

import pytest

from ...managers.spawn import send_control_fds
from .._shim import ShimPayload
from .._shim import decode_os
from .._shim import encode_error
from .._shim import encode_os
from .._shim import receive_control
from ..shim import decode_shim_status


def test_os_string_roundtrip():
    weird_bytes = b'\xff\xfe/\xed\xa0\xbd'
    weird = os.fsdecode(weird_bytes)
    assert decode_os(encode_os(weird)) == weird_bytes
    assert decode_os(encode_os(weird_bytes)) == weird_bytes
    assert decode_os(encode_os('plain')) == b'plain'
    # An unencodable str (a surrogate pair as two code points) fails here, in the parent - json would have quietly
    # collapsed it into a different, encodable string.
    with pytest.raises(UnicodeEncodeError):
        encode_os(chr(0xD83D) + chr(0xDE00))


def test_payload_json_roundtrip():
    weird = os.fsdecode(b'\xff\xfe')
    p = ShimPayload(
        argv=[encode_os('sh'), encode_os('-c'), encode_os(weird)],
        env={encode_os('A'): encode_os('b'), encode_os('W'): encode_os(weird)},
        status_fd=7,
        cwd=encode_os('/some/dir'),
        keep_fds=[5, 6],
        umask=0o22,
        rlimits=[[7, 1, 2]],
        user='nobody',
        group=0,
        extra_groups=[1, 'adm'],
        deathsig=15,
        setsid=True,
        set_ctty=True,
    )
    s = p.to_json()
    assert '\n' not in s and s.isascii()
    assert ShimPayload.from_json(s) == p
    assert ShimPayload.from_json(s.encode('ascii')) == p
    assert decode_os(ShimPayload.from_json(s).argv[2]) == b'\xff\xfe'

    # Defaults, and tuples coming back as lists are fine for everything that iterates them.
    p2 = ShimPayload(argv=[encode_os('x')], env={}, status_fd=3)
    assert ShimPayload.from_json(p2.to_json()) == p2
    assert p2.close_fds and p2.keep_fds == [] and p2.rlimits == [] and not p2.setsid


def test_status_record_roundtrip():
    exc = FileNotFoundError(2, 'No such file', os.fsdecode(b'\xff'))
    stage, err_no, msg = decode_shim_status(encode_error('exec', exc))
    assert (stage, err_no) == ('exec', 2)
    assert 'No such file' in msg
    assert decode_shim_status(encode_error('chdir', ValueError('nope'))) == ('chdir', None, 'nope')
    assert decode_shim_status(b'garbage')[0] == 'status'


def test_shim_source_is_py38_syntax():
    # The shim is shipped as text and exec'd by whatever interpreter `shim_python` is: keep it parseable by old pythons.
    # (Cheap proxy: compile it under the oldest interpreter around, if there is one.)
    src = os.path.join(os.path.dirname(os.path.dirname(__file__)), '_shim.py')
    code = 'import sys; compile(open(sys.argv[1]).read(), sys.argv[1], "exec")'
    exes = [sys.executable]
    for xn in ('python3.8', 'python3.9'):
        if (wn := shutil.which(xn)) is not None:
            exes.append(wn)
    for vn in ('8', '9', '10', '11', '12'):
        if os.path.isfile(vx := f'.venvs/{vn}/bin/python'):
            exes.append(vx)
    for exe in exes:
        r = subprocess.run([exe, '-c', code, src], capture_output=True)  # noqa
        assert r.returncode == 0, (exe, r.stderr)


def _handshake(payload, pass_fds):
    """Queues the handshake on a fresh socketpair the way the manager does; returns (parent_end, child_end)."""

    a, b = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    blob = tempfile.TemporaryFile()  # noqa: SIM115
    blob.write(payload.to_json().encode('ascii') + b'\n# (no source - already running)\n')
    blob.flush()
    blob.seek(0)
    send_control_fds(a, [blob.fileno(), *pass_fds])
    blob.close()
    return a, b


def test_receive_control_roundtrip():
    payload = ShimPayload(argv=[encode_os('x')], env={}, status_fd=3, keep_fds=[10, 11])
    r1, w1 = os.pipe()
    r2, w2 = os.pipe()
    a, b = _handshake(payload, [w1, w2])
    try:
        blob_fd, passed = receive_control(b.fileno())
        assert len(passed) == 2
        with os.fdopen(blob_fd, 'r', encoding='utf-8') as f:
            assert ShimPayload.from_json(f.readline()) == payload
        for fd, r in zip(passed, (r1, r2)):
            os.write(fd, b'ok')
            assert os.read(r, 2) == b'ok'
            os.close(fd)
    finally:
        a.close()
        b.close()  # (receive_control wrapped and detached its own socket object; `b` still owns the fd)
        for fd in (r1, w1, r2, w2):
            os.close(fd)


def test_debug_entrypoint_runs(tmp_path):
    # `python -m ...launch._shim <control_fd>` with the handshake queued on that socket execs the target, with a passed
    # fd relocated to the number the target expects.
    out = tmp_path / 'out'
    r, w = os.pipe()
    # The control socket keeps its number across `subprocess.run(pass_fds=...)`, and that number is the shim's status
    # channel, so it is known up front.
    a, b = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    ctl = b.fileno()
    payload = ShimPayload(
        argv=[encode_os(x) for x in ('sh', '-c', f'echo shimmed > {out}; echo via-passed >&9')],
        env={encode_os('PATH'): encode_os(os.environ.get('PATH', os.defpath))},
        status_fd=ctl,
        keep_fds=[9],
    )
    blob = tempfile.TemporaryFile()  # noqa: SIM115
    blob.write(payload.to_json().encode('ascii') + b'\n')
    blob.flush()
    blob.seek(0)
    send_control_fds(a, [blob.fileno(), w])
    blob.close()
    os.close(w)
    proc = subprocess.run(  # noqa
        [sys.executable, '-m', 'omllm.core.processes.launch._shim', str(ctl)],
        pass_fds=[ctl],
        capture_output=True,
    )
    b.close()
    assert proc.returncode == 0, proc.stderr
    assert a.recv(100) == b''  # EOF, no error record: exec happened
    a.close()
    assert out.read_text() == 'shimmed\n'
    assert os.read(r, 100) == b'via-passed\n'
    os.close(r)
    assert json.loads(payload.to_json())['keep_fds'] == [9]
