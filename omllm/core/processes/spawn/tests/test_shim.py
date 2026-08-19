import json
import os
import subprocess
import sys

from ...launch.shim import decode_shim_status
from ..shim import ShimPayload
from ..shim import encode_error


def test_payload_json_roundtrip():
    weird = os.fsdecode(b'\xff\xfe')  # undecodable bytes survive as surrogate escapes
    p = ShimPayload(
        argv=['sh', '-c', weird],
        env={'A': 'b', 'W': weird},
        status_fd=7,
        cwd='/some/dir',
        keep_fds=[5, 6],
        umask=0o22,
        rlimits=[[7, 1, 2]],
        user='nobody',
        group=0,
        extra_groups=[1, 'adm'],
        deathsig=15,
        set_ctty=True,
    )
    s = p.to_json()
    assert '\n' not in s and s.isascii()
    assert ShimPayload.from_json(s) == p
    assert ShimPayload.from_json(s.encode('ascii')) == p
    assert os.fsencode(ShimPayload.from_json(s).argv[2]) == b'\xff\xfe'

    # Defaults, and tuples coming back as lists are fine for everything that iterates them.
    p2 = ShimPayload(argv=['x'], env={}, status_fd=3)
    assert ShimPayload.from_json(p2.to_json()) == p2
    assert p2.close_fds and p2.keep_fds == [] and p2.rlimits == []


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
    src = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shim.py')
    for exe in ('python3.8', 'python3.9'):
        r = subprocess.run([exe, '-c', 'import sys; compile(open(sys.argv[1]).read(), sys.argv[1], "exec")', src], capture_output=True)  # noqa
        if r.returncode == 127 or b'No such file' in r.stderr:
            continue
        assert r.returncode == 0, r.stderr
    r = subprocess.run([sys.executable, '-c', 'import sys; compile(open(sys.argv[1]).read(), sys.argv[1], "exec")', src], capture_output=True)  # noqa
    assert r.returncode == 0, r.stderr


def test_debug_entrypoint_runs(tmp_path):
    # `python -m ...spawn.shim <fd>` with a json payload on that fd execs the target.
    status_r, status_w = os.pipe()
    pay_r, pay_w = os.pipe()
    out = tmp_path / 'out'
    payload = ShimPayload(
        argv=['sh', '-c', f'echo shimmed > {out}'],
        env={'PATH': os.environ.get('PATH', os.defpath)},
        status_fd=status_w,
    )
    os.write(pay_w, payload.to_json().encode())
    os.close(pay_w)
    r = subprocess.run(  # noqa
        [sys.executable, '-m', 'omllm.core.processes.spawn.shim', str(pay_r)],
        pass_fds=[pay_r, status_w],
        capture_output=True,
    )
    os.close(pay_r)
    os.close(status_w)
    assert r.returncode == 0, r.stderr
    assert os.read(status_r, 100) == b''  # EOF, no error record: exec happened
    os.close(status_r)
    assert out.read_text() == 'shimmed\n'
    assert json.loads(payload.to_json())['argv'][0] == 'sh'
