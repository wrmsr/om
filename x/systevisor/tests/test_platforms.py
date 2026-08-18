# ruff: noqa: LOG001 PTH100 PTH118 PTH123 PT009 UP006 UP007 UP045
import dataclasses as dc
import logging
import os
import os.path
import plistlib
import socket
import tempfile
import typing as ta
import unittest

from x.systevisor.configs.models import SystevisorManagerConfig
from x.systevisor.configs.models import SystevisorManagerLogConfig
from x.systevisor.platforms.runtime import SystevisorManagerLogging
from x.systevisor.platforms.runtime import SystevisorManagerRuntime
from x.systevisor.platforms.runtime import SystevisorPidFileManager
from x.systevisor.platforms.runtime import SystevisorPlatformError
from x.systevisor.platforms.runtime import SystevisorProcessBootstrap
from x.systevisor.platforms.runtime import SystevisorProcessBootstrapState
from x.systevisor.platforms.runtime import SystevisorServiceNotifier
from x.systevisor.platforms.runtime import SystevisorSystemdServiceNotifier
from x.systevisor.platforms.services import SystevisorServiceTemplateConfig
from x.systevisor.platforms.services import systevisor_render_launchd_plist
from x.systevisor.platforms.services import systevisor_render_systemd_service


class SystevisorTestProcessBootstrap(SystevisorProcessBootstrap):
    def __init__(self) -> None:
        self.config: ta.Optional[SystevisorManagerConfig] = None

    def bootstrap(self, config: SystevisorManagerConfig) -> SystevisorProcessBootstrapState:
        self.config = config
        return SystevisorProcessBootstrapState(
            pid=123,
            is_pid_one=False,
            subreaper_enabled=False,
            systemd_notify=False,
            launchd_job=False,
        )


class SystevisorTestServiceNotifier(SystevisorServiceNotifier):
    def __init__(self) -> None:
        self.messages: ta.List[str] = []

    def notify(self, message: str) -> bool:
        self.messages.append(message)
        return True


class TestSystevisorPlatforms(unittest.TestCase):
    def test_pidfile_is_locked_and_replacement_is_not_unlinked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, 'systevisor.pid')
            first = SystevisorPidFileManager()
            second = SystevisorPidFileManager()
            first.acquire(path)
            self.addCleanup(first.close)

            with self.assertRaises(SystevisorPlatformError):
                second.acquire(path)

            moved_path = os.path.join(temp_dir, 'original.pid')
            os.rename(path, moved_path)
            with open(path, 'w') as replacement_file:
                replacement_file.write('replacement\n')
            first.close()

            with open(path) as replacement_file:
                self.assertEqual(replacement_file.read(), 'replacement\n')

    def test_manager_logging_owns_only_its_handlers_and_reconfigures(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, 'manager.log')
            target = logging.Logger('systevisor-platform-test')
            unrelated = logging.NullHandler()
            target.addHandler(unrelated)
            manager_logging = SystevisorManagerLogging(target)
            self.addCleanup(manager_logging.close)
            manager_logging.configure(SystevisorManagerLogConfig(
                level='INFO',
                stderr=False,
                file=path,
                max_bytes=1024,
                backups=1,
            ))
            target.info('first-message')
            for handler in target.handlers:
                handler.flush()

            manager_logging.configure(SystevisorManagerLogConfig(level='ERROR', stderr=False))

            self.assertIn(unrelated, target.handlers)
            self.assertEqual(target.level, logging.ERROR)
            with open(path) as log_file:
                self.assertIn('first-message', log_file.read())

    def test_manager_runtime_reloads_only_live_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bootstrap = SystevisorTestProcessBootstrap()
            notifier = SystevisorTestServiceNotifier()
            logging_manager = SystevisorManagerLogging(logging.Logger('systevisor-runtime-test'))
            pid_file_manager = SystevisorPidFileManager()
            runtime = SystevisorManagerRuntime(bootstrap, logging_manager, pid_file_manager, notifier)
            config = SystevisorManagerConfig(
                process_title=None,
                pid_file=os.path.join(temp_dir, 'systevisor.pid'),
                log=SystevisorManagerLogConfig(stderr=False),
            )
            runtime.setup(config)
            self.addCleanup(runtime.close)
            runtime.ready()

            changed = dc.replace(
                config,
                strip_ansi=True,
                log=SystevisorManagerLogConfig(level='DEBUG', stderr=False),
            )
            runtime.prepare(changed).commit()

            assert runtime.state is not None
            self.assertEqual(runtime.state.config, changed)
            self.assertTrue(runtime.state.ready)
            self.assertTrue(any(message.startswith('READY=1') for message in notifier.messages))
            with self.assertRaises(SystevisorPlatformError):
                runtime.prepare(dc.replace(changed, pid_file=os.path.join(temp_dir, 'other.pid')))

    def test_systemd_notifier_uses_notify_socket_protocol(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, 'notify.sock')
            with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as server:
                server.bind(path)
                server.settimeout(2.)
                notifier = SystevisorSystemdServiceNotifier(path)

                self.assertTrue(notifier.notify('READY=1\nSTATUS=ready'))
                self.assertEqual(server.recv(4096), b'READY=1\nSTATUS=ready')

    def test_service_templates_are_direct_exec_and_opaque(self) -> None:
        config = SystevisorServiceTemplateConfig(
            executable='/opt/systevisor/systevisor.py',
            config_paths=('/etc/systevisor/config %.yml',),
            identifier='com.example.systevisor',
            recursive=True,
        )

        systemd = systevisor_render_systemd_service(config)
        self.assertIn('Type=notify', systemd)
        self.assertIn('KillMode=process', systemd)
        self.assertIn('config %%.yml', systemd)
        plist = plistlib.loads(systevisor_render_launchd_plist(config).encode('utf-8'))
        self.assertEqual(plist['Label'], 'com.example.systevisor')
        self.assertEqual(plist['ProgramArguments'][0], '/opt/systevisor/systevisor.py')
        self.assertIn('/etc/systevisor/config %.yml', plist['ProgramArguments'])
