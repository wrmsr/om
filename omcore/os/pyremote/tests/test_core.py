# ruff: noqa: PT009 UP045
# @om-lite
import asyncio
import io
import json
import os.path
import struct
import subprocess
import sys
import typing as ta
import unittest

from ....lite.check import check
from ....subprocesses.wrap import subprocess_maybe_shell_wrap_exec
from .. import core


class TestPyremote(unittest.TestCase):
    @staticmethod
    def _build_driver_input(pid: int) -> bytes:
        env_info_json = json.dumps(
            core._get_pyremote_env_info().to_dict(),  # noqa
            indent=None,
            separators=(',', ':'),
        ).encode('utf-8')
        return b''.join([
            core._PyremoteBootstrapConsts.ACK0,  # noqa
            struct.pack('<Q', pid),
            core._PyremoteBootstrapConsts.ACK1,  # noqa
            core._PyremoteBootstrapConsts.ACK2,  # noqa
            struct.pack('<I', len(env_info_json)),
            env_info_json,
            core._PyremoteBootstrapConsts.ACK3,  # noqa
        ])

    def _run_test(self, opts: core.PyremoteBootstrapOptions) -> None:
        with open(os.path.join(os.path.dirname(__file__), '..', 'core.py')) as f:
            pyr_src = f.read()

        payload_src = '\n'.join([
            pyr_src,
            'rt = pyremote_bootstrap_finalize()',
            'b = rt.input.read()',
            'rt.output.write(b"!" + b + b"!")',
        ])

        #

        proc = subprocess.Popen(
            subprocess_maybe_shell_wrap_exec(
                sys.executable,
                '-c',
                core.pyremote_build_bootstrap_source('test'),
            ),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

        stdin = check.not_none(proc.stdin)
        stdout = check.not_none(proc.stdout)

        res = core.PyremoteBootstrapDriver(
            payload_src,
            opts,
        ).run(stdout, stdin)
        self.assertEqual(res.pid, proc.pid)
        self.assertEqual(res.env_info.sys.executable, sys.executable)

        stdin.write(b'foo')
        try:
            stdin.close()
        except BrokenPipeError:
            pass

        out = stdout.read()
        self.assertEqual(out, b'!foo!')

    def test_normal(self) -> None:
        self._run_test(core.PyremoteBootstrapOptions())

    def test_debug(self) -> None:
        self._run_test(core.PyremoteBootstrapOptions(debug=True))

    def test_driver_sync_fragmented_reads(self) -> None:
        class FragmentedReader(io.BytesIO):
            def read(self, size: ta.Optional[int] = -1) -> bytes:
                return super().read(min(size, 1) if size is not None and size >= 0 else 1)

        pid = 123
        result = core.PyremoteBootstrapDriver('pass').run(
            FragmentedReader(self._build_driver_input(pid)),
            io.BytesIO(),
        )
        self.assertEqual(result.pid, pid)

    def test_driver_async_uses_readexactly(self) -> None:
        class FragmentedReader:
            def __init__(self, data: bytes) -> None:
                self._bio = io.BytesIO(data)

            async def read(self, size: int) -> bytes:
                return self._bio.read(min(size, 1))

            async def readexactly(self, size: int) -> bytes:
                data = self._bio.read(size)
                if len(data) != size:
                    raise asyncio.IncompleteReadError(data, size)
                return data

        class Writer:
            def __init__(self) -> None:
                self._bio = io.BytesIO()

            def write(self, data: bytes) -> None:
                self._bio.write(data)

            async def drain(self) -> None:
                pass

        pid = 456
        result = asyncio.run(core.PyremoteBootstrapDriver('pass').async_run(
            FragmentedReader(self._build_driver_input(pid)),
            Writer(),
        ))
        self.assertEqual(result.pid, pid)
