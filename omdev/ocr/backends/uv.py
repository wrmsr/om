"""
Standalone, source-extracted workers: PNG on stdin, keyword arguments in JSON, UTF-8 text in a result file. The child
never imports or installs omdev. Its stdout and stderr are diagnostics, not a result protocol.
"""
import abc
import inspect
import json
import os
import os.path
import shutil
import signal
import subprocess
import tempfile
import textwrap
import typing as ta

from omcore import lang

from ..images import get_image_png_bytes
from ..subprocesses import ProcessError
from ..types import OcrBackend


with lang.auto_proxy_import(globals()):
    from PIL import Image


##


DEFAULT_UV_PYTHON = 'cpython@3.12'
DEFAULT_UV_TIMEOUT = 600.


def _uv_main(worker):
    import json
    import sys

    with open(sys.argv[1], encoding='utf-8') as f:
        kwargs = json.load(f)
    result = worker(sys.stdin.buffer.read(), **kwargs)
    if not isinstance(result, str):
        raise TypeError(type(result))
    with open(sys.argv[2], 'w', encoding='utf-8', newline='') as f:
        f.write(result)


def _make_worker_script(worker: ta.Callable[..., str]) -> str:
    # Workers must be undecorated, self-contained free functions with inner imports and no enclosing-scope references.
    worker_source = textwrap.dedent(inspect.getsource(worker))

    main_source = inspect.getsource(_uv_main)

    return '\n'.join([
        'from __future__ import annotations',
        '',
        worker_source,
        '',
        main_source,
        '',
        f'_uv_main({worker.__name__})',
    ])


def _run_worker_process(cmd: ta.Sequence[str], data: bytes, *, timeout: float) -> None:
    # Keep model diagnostics off the caller's stdout. A separate process group lets timeout/interrupt kill the worker as
    # well as uv, rather than leaving model execution running after its temporary directory has been removed.
    with subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
    ) as proc:
        try:
            stdout, stderr = proc.communicate(data, timeout=timeout)
        except BaseException:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
            raise

        if proc.returncode:
            raise ProcessError(
                proc.returncode,
                cmd,
                stdout,
                stderr.decode(),  # noqa
            )


def _run_uv_ocr(
        worker: ta.Callable[..., str],
        png: bytes,
        *,
        requirements: ta.Sequence[str],
        kwargs: ta.Mapping[str, ta.Any],
        uv: str = 'uv',
        python: str = DEFAULT_UV_PYTHON,
        timeout: float = DEFAULT_UV_TIMEOUT,
) -> str:
    with tempfile.TemporaryDirectory(prefix='om-ocr-') as tmp:
        script = os.path.join(tmp, 'worker.py')
        options = os.path.join(tmp, 'options.json')
        result = os.path.join(tmp, 'result.txt')

        with open(script, 'w', encoding='utf-8') as f:
            f.write(_make_worker_script(worker))
        with open(options, 'w', encoding='utf-8') as f:
            json.dump(dict(kwargs), f)

        cmd = [
            uv,
            'run',
            '--no-project',
            '--isolated',
            '--no-config',
            '--python', python,
        ]
        for requirement in requirements:
            cmd.extend(['--with', requirement])
        cmd.extend([
            '--',
            'python',
            '-I',
            script,
            options,
            result,
        ])

        _run_worker_process(cmd, png, timeout=timeout)

        with open(result, encoding='utf-8', newline='') as f:
            return f.read()


##


class UvOcrBackend(OcrBackend, lang.Abstract):
    def __init__(
            self,
            *,
            requirements: ta.Sequence[str],
            kwargs: ta.Mapping[str, ta.Any],
            uv: str = 'uv',
            python: str = DEFAULT_UV_PYTHON,
            timeout: float = DEFAULT_UV_TIMEOUT,
    ) -> None:
        super().__init__()

        if timeout <= 0:
            raise ValueError(timeout)
        self._requirements = tuple(requirements)
        self._kwargs = dict(kwargs)
        self._uv = uv
        self._python = python
        self._timeout = timeout

    @abc.abstractmethod
    def _get_worker(self) -> ta.Callable[..., str]:
        raise NotImplementedError

    def is_available(self) -> bool:
        return shutil.which(self._uv) is not None

    def ocr(self, image: Image.Image) -> str:
        return _run_uv_ocr(
            self._get_worker(),
            get_image_png_bytes(image),
            requirements=self._requirements,
            kwargs=self._kwargs,
            uv=self._uv,
            python=self._python,
            timeout=self._timeout,
        )
