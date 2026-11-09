# ruff: noqa: PYI034 PYI036 S603 S607 UP006 UP007 UP037 UP045
import collections
import dataclasses as dc
import json
import os
import os.path
import select
import shutil
import subprocess
import tempfile
import time
import typing as ta
import uuid


_SYSTEVISOR_DOCKER_HARNESS_ROOT = os.path.dirname(os.path.dirname(__file__))
_SYSTEVISOR_DOCKER_HARNESS_ARTIFACT = os.path.join(
    _SYSTEVISOR_DOCKER_HARNESS_ROOT,
    '_bin',
    'systevisor.py',
)
_SYSTEVISOR_DOCKER_HARNESS_CONTAINER_ROOT = '/systevisor'


@dc.dataclass(frozen=True)
class SystevisorDockerHarnessSpec:
    command: ta.Sequence[str]
    files: ta.Mapping[str, ta.Union[str, bytes]] = dc.field(default_factory=dict)
    image: str = 'python:3.8-slim'
    environment: ta.Mapping[str, str] = dc.field(default_factory=dict)
    network: str = 'none'


@dc.dataclass(frozen=True)
class SystevisorDockerCheckpoint:
    name: str
    data: ta.Mapping[str, ta.Any]


class SystevisorDockerHarnessError(Exception):
    pass


class SystevisorDockerHarness:
    def __init__(
            self,
            spec: SystevisorDockerHarnessSpec,
            *,
            docker_executable: str = 'docker',
    ) -> None:
        self._spec = spec
        self._docker_executable = docker_executable
        self._name = f'systevisor-test-{uuid.uuid4().hex}'
        self._temporary_directory: ta.Optional[tempfile.TemporaryDirectory[str]] = None
        self._checkpoint_fd: ta.Optional[int] = None
        self._checkpoint_buffer = bytearray()
        self._checkpoints: ta.Deque[SystevisorDockerCheckpoint] = collections.deque()
        self._created = False

    @staticmethod
    def available(docker_executable: str = 'docker') -> bool:
        try:
            result = subprocess.run(
                (docker_executable, 'version', '--format', '{{.Server.Version}}'),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10.,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def host_directory(self) -> str:
        if self._temporary_directory is None:
            raise SystevisorDockerHarnessError('harness is not started')
        return self._temporary_directory.name

    def _write_files(self) -> None:
        shutil.copyfile(
            _SYSTEVISOR_DOCKER_HARNESS_ARTIFACT,
            os.path.join(self.host_directory, 'systevisor.py'),
        )
        for relative_path, data in self._spec.files.items():
            if os.path.isabs(relative_path) or '..' in relative_path.split(os.sep):
                raise SystevisorDockerHarnessError(f'invalid injected path: {relative_path!r}')
            path = os.path.join(self.host_directory, relative_path)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            mode = 'wb' if isinstance(data, bytes) else 'w'
            with open(path, mode) as output_file:
                ta.cast(ta.Any, output_file).write(data)

    def start(self) -> 'SystevisorDockerHarness':
        if self._temporary_directory is not None:
            raise SystevisorDockerHarnessError('harness is already started')
        self._temporary_directory = tempfile.TemporaryDirectory(prefix='systevisor-docker-')
        checkpoint_path = os.path.join(self.host_directory, 'checkpoints.ndjson')
        os.mkfifo(checkpoint_path, 0o600)
        self._checkpoint_fd = os.open(checkpoint_path, os.O_RDWR | os.O_NONBLOCK)
        try:
            self._write_files()
            command = [
                self._docker_executable,
                'create',
                '--name',
                self._name,
                '--network',
                self._spec.network,
                '--mount',
                f'type=bind,src={self.host_directory},dst={_SYSTEVISOR_DOCKER_HARNESS_CONTAINER_ROOT}',
                '--label',
                'com.om.systevisor.test=true',
            ]
            for name, value in sorted(self._spec.environment.items()):
                command.extend(('--env', f'{name}={value}'))
            command.extend((self._spec.image, *self._spec.command))
            created = subprocess.run(command, capture_output=True, text=True, timeout=60., check=False)
            if created.returncode != 0:
                raise SystevisorDockerHarnessError(
                    f'docker create failed ({created.returncode}): {created.stderr.strip()}',
                )
            self._created = True
            started = subprocess.run(
                (self._docker_executable, 'start', self._name),
                capture_output=True,
                text=True,
                timeout=30.,
                check=False,
            )
            if started.returncode != 0:
                raise SystevisorDockerHarnessError(
                    f'docker start failed ({started.returncode}): {started.stderr.strip()}',
                )
        except BaseException:
            self.close()
            raise
        return self

    def _decode_checkpoints(self) -> None:
        while True:
            newline = self._checkpoint_buffer.find(b'\n')
            if newline < 0:
                return
            line = bytes(self._checkpoint_buffer[:newline])
            del self._checkpoint_buffer[:newline + 1]
            if not line:
                continue
            value = json.loads(line.decode('utf-8'))
            if not isinstance(value, dict) or not isinstance(value.get('name'), str):
                raise SystevisorDockerHarnessError(f'invalid checkpoint: {value!r}')
            self._checkpoints.append(SystevisorDockerCheckpoint(
                name=value['name'],
                data={key: item for key, item in value.items() if key != 'name'},
            ))

    def wait_checkpoint(self, name: str, timeout_secs: float = 30.) -> SystevisorDockerCheckpoint:
        checkpoint_fd = self._checkpoint_fd
        if checkpoint_fd is None:
            raise SystevisorDockerHarnessError('harness is not started')
        deadline = time.monotonic() + timeout_secs
        while True:
            for checkpoint in tuple(self._checkpoints):
                if checkpoint.name == name:
                    self._checkpoints.remove(checkpoint)
                    return checkpoint
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise SystevisorDockerHarnessError(
                    f'timed out waiting for checkpoint {name!r}; logs:\n{self.logs()}',
                )
            readable, _, _ = select.select((checkpoint_fd,), (), (), remaining)
            if not readable:
                continue
            data = os.read(checkpoint_fd, 64 * 1024)
            if data:
                self._checkpoint_buffer.extend(data)
                self._decode_checkpoints()

    def wait(self, timeout_secs: float = 30.) -> int:
        if not self._created:
            raise SystevisorDockerHarnessError('container was not created')
        try:
            result = subprocess.run(
                (self._docker_executable, 'wait', self._name),
                capture_output=True,
                text=True,
                timeout=timeout_secs,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise SystevisorDockerHarnessError(
                f'timed out waiting for container; logs:\n{self.logs()}',
            ) from exc
        if result.returncode != 0:
            raise SystevisorDockerHarnessError(f'docker wait failed: {result.stderr.strip()}')
        try:
            return int(result.stdout.strip())
        except ValueError as exc:
            raise SystevisorDockerHarnessError(f'invalid docker wait output: {result.stdout!r}') from exc

    def logs(self) -> str:
        if not self._created:
            return ''
        result = subprocess.run(
            (self._docker_executable, 'logs', self._name),
            capture_output=True,
            text=True,
            timeout=10.,
            check=False,
        )
        return result.stdout + result.stderr

    def close(self) -> None:
        if self._created:
            try:
                subprocess.run(
                    (self._docker_executable, 'rm', '--force', '--volumes', self._name),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=30.,
                    check=False,
                )
            finally:
                self._created = False
        if self._checkpoint_fd is not None:
            os.close(self._checkpoint_fd)
            self._checkpoint_fd = None
        if self._temporary_directory is not None:
            self._temporary_directory.cleanup()
            self._temporary_directory = None

    def __enter__(self) -> 'SystevisorDockerHarness':
        return self.start()

    def __exit__(
            self,
            exc_type: ta.Optional[ta.Type[BaseException]],
            exc_val: ta.Optional[BaseException],
            exc_tb: ta.Optional[ta.Any],
    ) -> None:
        self.close()
