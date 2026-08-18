# ruff: noqa: UP006 UP007 UP045
import argparse
import base64
import json
import os
import sys
import typing as ta
import urllib.parse

from omcore.io.fdio.pollers import FdioPoller
from omcore.lite.inject import inj

from .configs.compiling import SystevisorConfigCompiler
from .configs.compiling import SystevisorConfigCompileResult
from .configs.models import SystevisorUnitKind
from .control.client import SystevisorApiClient
from .control.client import SystevisorApiEndpoint
from .control.configs import SystevisorConfigController
from .control.configs import SystevisorConfigControllerResult
from .control.inject import SystevisorControlBootstrapConfig
from .control.inject import systevisor_bind_control
from .control.jsoncodec import SystevisorJsonCodec
from .control.manager import SystevisorManagerConfigParticipant
from .control.operations import SystevisorOperationStore
from .control.plane import SystevisorControlPlane
from .control.service import SystevisorControlService
from .core.identities import SystevisorCollectionName
from .core.inputs import SystevisorShutdownCommand
from .core.states import SystevisorCollectionStatus
from .platforms.inject import systevisor_bind_platforms
from .platforms.runtime import SystevisorManagerRuntime
from .platforms.services import SystevisorServiceTemplateConfig
from .platforms.services import systevisor_render_launchd_plist
from .platforms.services import systevisor_render_systemd_service
from .resources.cgroups import SystevisorCgroupManager
from .resources.inject import systevisor_bind_resources
from .resources.runtime import SystevisorResourceObserver
from .resources.sockets import SystevisorInheritedSocketRegistry
from .runtime.coordinator import SystevisorRuntimeCoordinator
from .runtime.inject import systevisor_bind_runtime
from .runtime.processes import SystevisorProcessManager
from .scheduling.runtime import SystevisorScheduler
from .selfupdate.codec import systevisor_handoff_manifest_from_obj
from .selfupdate.codec import systevisor_self_update_read_json
from .selfupdate.inject import systevisor_bind_self_update
from .selfupdate.restore import SystevisorDecodedHandoff
from .selfupdate.restore import systevisor_cleanup_handoff_files
from .selfupdate.restore import systevisor_decode_handoff
from .selfupdate.restore import systevisor_restore_handoff_cloexec
from .selfupdate.restore import systevisor_rollback_handoff
from .selfupdate.runtime import SystevisorSelfUpdateError
from .selfupdate.runtime import SystevisorSelfUpdateManager
from .selfupdate.runtime import systevisor_run_self_update_probe


_SYSTEVISOR_MAIN_DEFAULT_ENDPOINT = 'unix:/tmp/systevisor.sock'


class SystevisorNdjsonConsumer:
    def __init__(self, callback: ta.Callable[[bytes], None]) -> None:
        self._callback = callback
        self._buffer = bytearray()

    def feed(self, data: bytes) -> None:
        self._buffer.extend(data)
        while True:
            newline = self._buffer.find(b'\n')
            if newline < 0:
                return
            line = bytes(self._buffer[:newline])
            del self._buffer[:newline + 1]
            if line:
                self._callback(line)

    def finish(self) -> None:
        if self._buffer:
            self._callback(bytes(self._buffer))
            self._buffer.clear()


def _systevisor_main_write(fd: int, data: bytes) -> None:
    offset = 0
    while offset < len(data):
        offset += os.write(fd, data[offset:])


def _systevisor_main_print_json(value: ta.Any, codec: SystevisorJsonCodec, fd: int = 1) -> None:
    _systevisor_main_write(fd, codec.dumps(value, pretty=True))


def _systevisor_main_config_check(args: argparse.Namespace) -> int:
    codec = SystevisorJsonCodec()
    result = SystevisorConfigCompiler().compile(args.config, recursive=args.recursive)
    _systevisor_main_print_json(result, codec, 1 if result.is_valid else 2)
    return 0 if result.is_valid else 2


class SystevisorMainServerContext:
    def __init__(self, args: argparse.Namespace) -> None:
        bootstrap = SystevisorControlBootstrapConfig(
            paths=tuple(args.config),
            recursive=args.recursive,
            state_directory=args.state_directory,
        )
        self._injector = inj.create_injector(
            systevisor_bind_platforms(),
            systevisor_bind_resources(),
            systevisor_bind_runtime(),
            systevisor_bind_self_update(),
            systevisor_bind_control(bootstrap),
        )
        self._state_directory = args.state_directory
        self.codec = self._injector.provide(SystevisorJsonCodec)
        self.coordinator: ta.Optional[SystevisorRuntimeCoordinator] = None
        self.controller: ta.Optional[SystevisorConfigController] = None
        self.control: ta.Optional[SystevisorControlService] = None
        self.control_plane: ta.Optional[SystevisorControlPlane] = None
        self.poller: ta.Optional[FdioPoller] = None
        self.manager_runtime: ta.Optional[SystevisorManagerRuntime] = None
        self.scheduler: ta.Optional[SystevisorScheduler] = None
        self.resource_observer: ta.Optional[SystevisorResourceObserver] = None
        self.inherited_sockets: ta.Optional[SystevisorInheritedSocketRegistry] = None
        self.self_update: ta.Optional[SystevisorSelfUpdateManager] = None

    def compile(self) -> SystevisorConfigCompileResult:
        bootstrap = self._injector.provide(SystevisorControlBootstrapConfig)
        return self._injector.provide(SystevisorConfigCompiler).compile(
            bootstrap.paths,
            recursive=bootstrap.recursive,
        )

    def start(
            self,
            compiled: SystevisorConfigCompileResult,
            startup_collection: ta.Optional[SystevisorCollectionName] = None,
    ) -> SystevisorConfigControllerResult:
        if compiled.snapshot is not None:
            self.inherited_sockets = self._injector.provide(SystevisorInheritedSocketRegistry)
            manager_runtime = self._injector.provide(SystevisorManagerRuntime)
            manager_runtime.setup(compiled.snapshot.config.manager)
            self.manager_runtime = manager_runtime

        coordinator = self._injector.provide(SystevisorRuntimeCoordinator)
        if compiled.snapshot is not None:
            coordinator.log_manager.configure_manager(compiled.snapshot.config.manager, cleanup=True)
        controller = self._injector.provide(SystevisorConfigController)
        self.coordinator = coordinator
        self.controller = controller
        self.poller = self._injector.provide(FdioPoller)
        if compiled.snapshot is not None:
            self._injector.provide(SystevisorManagerConfigParticipant)
            self.control = self._injector.provide(SystevisorControlService)
            self.scheduler = self._injector.provide(SystevisorScheduler)
            self.scheduler.set_state_directory_override(self._state_directory)
            self.resource_observer = self._injector.provide(SystevisorResourceObserver)
            self.self_update = self._injector.provide(SystevisorSelfUpdateManager)
            self.self_update.configure_mode(
                'run' if startup_collection is not None else 'serve',
                None if startup_collection is None else str(startup_collection),
                os.path.realpath(sys.argv[0]),
            )
            self.control_plane = self._injector.provide(SystevisorControlPlane)
            coordinator.engine.state.startup_collection = startup_collection

        result = controller.apply_compiled(compiled, initial=True)
        if result.attempt.applied:
            controller.install_signal_reload()
            coordinator.install_signal_handler()
            ta.cast(SystevisorManagerRuntime, self.manager_runtime).ready()
        return result

    def resume(
            self,
            handoff: SystevisorDecodedHandoff,
            *,
            completion_error: ta.Optional[str] = None,
    ) -> None:
        manifest = handoff.manifest
        inherited_sockets = self._injector.provide(SystevisorInheritedSocketRegistry)
        inherited_sockets.rehydrate(handoff.inherited_sockets)
        self.inherited_sockets = inherited_sockets

        manager_runtime = self._injector.provide(SystevisorManagerRuntime)
        manager_runtime.rehydrate(handoff.manager_runtime, handoff.pid_file_fd)
        self.manager_runtime = manager_runtime

        coordinator = self._injector.provide(SystevisorRuntimeCoordinator)
        self.coordinator = coordinator
        coordinator.event_bus.rehydrate(handoff.event_bus)
        coordinator.log_manager.configure_manager(handoff.snapshot.config.manager, cleanup=False)
        coordinator.log_manager.rehydrate(handoff.logs)
        coordinator.engine.rehydrate(handoff.engine)
        process_manager = self._injector.provide(SystevisorProcessManager)
        process_manager.rehydrate(handoff.processes, handoff.engine)

        controller = self._injector.provide(SystevisorConfigController)
        self.controller = controller
        self.poller = self._injector.provide(FdioPoller)
        operations = self._injector.provide(SystevisorOperationStore)
        operations.rehydrate(handoff.operations)
        self._injector.provide(SystevisorManagerConfigParticipant)
        self.control = self._injector.provide(SystevisorControlService)
        self.scheduler = self._injector.provide(SystevisorScheduler)
        self.scheduler.set_state_directory_override(self._state_directory)
        self.resource_observer = self._injector.provide(SystevisorResourceObserver)
        self.self_update = self._injector.provide(SystevisorSelfUpdateManager)
        self.self_update.configure_mode(
            manifest.mode,
            manifest.startup_collection,
            os.path.realpath(sys.argv[0]),
        )
        self.control_plane = self._injector.provide(SystevisorControlPlane)

        controller.rehydrate(handoff.snapshot)
        self._injector.provide(SystevisorCgroupManager).rehydrate(
            handoff.cgroups,
            process_manager.child_contexts(),
        )
        coordinator.rehydrate_process_runtime(handoff.output_fds)
        controller.install_signal_reload()
        coordinator.install_signal_handler()
        systevisor_restore_handoff_cloexec(handoff)
        manager_runtime.ready()
        if completion_error is None:
            self.self_update.complete_resume(manifest.operation_id, manifest.source_sha256)
        else:
            self.self_update.fail_resume(manifest.operation_id, completion_error)

    def note_stopping(self) -> None:
        if self.manager_runtime is not None:
            self.manager_runtime.stopping()

    def close(self) -> None:
        if self.self_update is not None:
            self.self_update.close()
        if self.resource_observer is not None:
            self.resource_observer.close()
        if self.scheduler is not None:
            self.scheduler.close()
        if self.control_plane is not None:
            self.control_plane.close()
        if self.control is not None:
            self.control.close()
        if self.controller is not None:
            self.controller.close()
        if self.coordinator is not None:
            self.coordinator.close()
        if self.poller is not None:
            self.poller.close()
        if self.manager_runtime is not None:
            self.manager_runtime.close()
        if self.inherited_sockets is not None:
            self.inherited_sockets.close()


def _systevisor_main_serve(args: argparse.Namespace) -> int:
    context = SystevisorMainServerContext(args)
    try:
        result = context.start(context.compile())
        if not result.attempt.applied or result.snapshot is None:
            _systevisor_main_print_json(result.attempt, context.codec, 2)
            return 2
        coordinator = ta.cast(SystevisorRuntimeCoordinator, context.coordinator)

        stopping_noted = False
        while True:
            coordinator.poll()
            self_update = ta.cast(SystevisorSelfUpdateManager, context.self_update)
            if self_update.ready_to_exec():
                try:
                    self_update.execute_prepared()
                except SystevisorSelfUpdateError:
                    pass
            state = coordinator.engine.state
            if state.shutting_down and not stopping_noted:
                context.note_stopping()
                stopping_noted = True
            if state.shutting_down and all(instance.run_id is None for instance in state.instances.values()):
                break
        return 0
    except Exception as exc:  # noqa: BLE001
        _systevisor_main_print_json({
            'error': 'startup_failed',
            'message': f'{type(exc).__name__}: {exc}',
        }, context.codec, 2)
        return 2
    finally:
        context.close()


def _systevisor_main_run(args: argparse.Namespace) -> int:
    context = SystevisorMainServerContext(args)
    collection_name = SystevisorCollectionName(args.collection)
    try:
        result = context.start(context.compile(), collection_name)
        if not result.attempt.applied or result.snapshot is None:
            _systevisor_main_print_json(result.attempt, context.codec, 2)
            return 2
        coordinator = ta.cast(SystevisorRuntimeCoordinator, context.coordinator)
        collection_config = result.snapshot.config.collections.get(collection_name)
        collection = coordinator.engine.state.collections.get(collection_name)
        if collection_config is None or collection is None:
            _systevisor_main_print_json({
                'error': 'unknown_collection',
                'collection': collection_name,
            }, context.codec, 2)
            return 2

        exit_code = 0
        shutdown_requested = False
        stopping_noted = False
        while True:
            coordinator.poll()
            self_update = ta.cast(SystevisorSelfUpdateManager, context.self_update)
            if self_update.ready_to_exec():
                try:
                    self_update.execute_prepared()
                except SystevisorSelfUpdateError:
                    pass
            state = coordinator.engine.state
            collection = state.collections.get(collection_name)
            current_collection_config = (
                None if state.snapshot is None else
                state.snapshot.config.collections.get(collection_name)
            )
            if not state.shutting_down and not shutdown_requested:
                if collection is None or current_collection_config is None:
                    exit_code = 2
                    shutdown_requested = True
                elif collection.status is SystevisorCollectionStatus.FAILED:
                    exit_code = 1
                    shutdown_requested = True
                elif collection.status is SystevisorCollectionStatus.INACTIVE:
                    shutdown_requested = True
                elif collection.status is SystevisorCollectionStatus.READY and all(
                        state.snapshot is not None and
                        state.snapshot.config.units[unit_name].kind is SystevisorUnitKind.ONESHOT
                        for unit_name in current_collection_config.units
                ):
                    shutdown_requested = True
                elif collection.status is SystevisorCollectionStatus.DEGRADED and all(
                        instance.run_id is None
                        for instance in state.instances.values()
                        if instance.unit_name in current_collection_config.units
                ):
                    exit_code = 1
                    shutdown_requested = True
                if shutdown_requested:
                    coordinator.submit(SystevisorShutdownCommand())
            if state.shutting_down and not stopping_noted:
                context.note_stopping()
                stopping_noted = True
            if state.shutting_down and all(instance.run_id is None for instance in state.instances.values()):
                break
        return exit_code
    except Exception as exc:  # noqa: BLE001
        _systevisor_main_print_json({
            'error': 'startup_failed',
            'message': f'{type(exc).__name__}: {exc}',
        }, context.codec, 2)
        return 2
    finally:
        context.close()


def _systevisor_main_resume(args: argparse.Namespace, *, rollback: bool = False) -> int:
    context: ta.Optional[SystevisorMainServerContext] = None
    manifest = None
    try:
        manifest = systevisor_handoff_manifest_from_obj(systevisor_self_update_read_json(args.manifest))
        handoff = systevisor_decode_handoff(
            manifest,
            os.path.realpath(sys.argv[0]),
            previous_source=rollback,
        )
        completion_error: ta.Optional[str] = None
        if rollback:
            error_obj = systevisor_self_update_read_json(args.error_file)
            if not isinstance(error_obj, dict) or not isinstance(error_obj.get('message'), str):
                raise ValueError('invalid self-update rollback error document')
            completion_error = error_obj['message']
        context_args = argparse.Namespace(
            config=list(manifest.config_paths),
            recursive=manifest.recursive,
            state_directory=manifest.state_directory,
        )
        context = SystevisorMainServerContext(context_args)
        context.resume(handoff, completion_error=completion_error)
        systevisor_cleanup_handoff_files(args.manifest)

        coordinator = ta.cast(SystevisorRuntimeCoordinator, context.coordinator)
        collection_name = (
            None if manifest.startup_collection is None else
            SystevisorCollectionName(manifest.startup_collection)
        )
        exit_code = 0
        stopping_noted = False
        shutdown_requested = False
        while True:
            coordinator.poll()
            state = coordinator.engine.state
            if collection_name is not None and not state.shutting_down and not shutdown_requested:
                collection = state.collections.get(collection_name)
                collection_config = (
                    None if state.snapshot is None else
                    state.snapshot.config.collections.get(collection_name)
                )
                if collection is None or collection_config is None:
                    exit_code = 2
                    shutdown_requested = True
                elif collection.status is SystevisorCollectionStatus.FAILED:
                    exit_code = 1
                    shutdown_requested = True
                elif collection.status is SystevisorCollectionStatus.INACTIVE:
                    shutdown_requested = True
                elif collection.status is SystevisorCollectionStatus.READY and all(
                        state.snapshot is not None and
                        state.snapshot.config.units[unit_name].kind is SystevisorUnitKind.ONESHOT
                        for unit_name in collection_config.units
                ):
                    shutdown_requested = True
                elif collection.status is SystevisorCollectionStatus.DEGRADED and all(
                        instance.run_id is None
                        for instance in state.instances.values()
                        if instance.unit_name in collection_config.units
                ):
                    exit_code = 1
                    shutdown_requested = True
                if shutdown_requested:
                    coordinator.submit(SystevisorShutdownCommand())
            if state.shutting_down and not stopping_noted:
                context.note_stopping()
                stopping_noted = True
            if state.shutting_down and all(instance.run_id is None for instance in state.instances.values()):
                return exit_code
    except Exception as exc:  # noqa: BLE001
        error = 'self_update_rollback_failed' if rollback else 'self_update_resume_failed'
        message = f'{type(exc).__name__}: {exc}'
        if not rollback and manifest is not None:
            try:
                systevisor_rollback_handoff(manifest, args.manifest, message)
            except Exception as rollback_exc:  # noqa: BLE001
                error = 'self_update_rollback_failed'
                message = (
                    f'{message}; rollback exec failed: '
                    f'{type(rollback_exc).__name__}: {rollback_exc}'
                )
        _systevisor_main_print_json({
            'error': error,
            'message': message,
        }, SystevisorJsonCodec(), 2)
        return 2
    finally:
        if context is not None:
            context.close()


def _systevisor_main_service_template(args: argparse.Namespace) -> int:
    config = SystevisorServiceTemplateConfig(
        executable=args.executable,
        config_paths=tuple(args.config),
        identifier=args.identifier,
        recursive=args.recursive,
        state_directory=args.state_directory,
    )
    rendered = (
        systevisor_render_systemd_service(config)
        if args.platform == 'systemd' else
        systevisor_render_launchd_plist(config)
    )
    _systevisor_main_write(1, rendered.encode('utf-8'))
    return 0


def _systevisor_main_client(args: argparse.Namespace) -> int:
    codec = SystevisorJsonCodec()
    client = SystevisorApiClient(
        SystevisorApiEndpoint.parse(args.endpoint),
        codec,
        timeout_secs=args.timeout,
    )

    method = 'GET'
    target = '/'
    body: ta.Optional[ta.Any] = None
    if args.command == 'status':
        target = '/'
    elif args.command == 'units':
        target = '/v1/units'
    elif args.command == 'collections':
        target = '/v1/collections'
    elif args.command == 'schedules':
        target = '/v1/schedules'
    elif args.command == 'resources':
        target = (
            '/v1/resources' if args.run_id is None else
            f'/v1/resources/{args.run_id}'
        )
    elif args.command == 'config':
        target = '/v1/config'
    elif args.command == 'operations':
        target = '/v1/operations'
    elif args.command == 'reload':
        method, target = 'POST', '/v1/config/_reload'
    elif args.command == 'check':
        method, target = 'POST', '/v1/config/_check'
    elif args.command in ('start', 'stop'):
        kind = args.kind
        target_name = urllib.parse.quote(args.target, safe='')
        method = 'POST'
        target = f'/v1/{kind}s/{target_name}/_{args.command}'
    elif args.command == 'restart':
        method = 'POST'
        target = f'/v1/instances/{urllib.parse.quote(args.instance, safe="")}/_restart'
    elif args.command == 'shutdown':
        method, target = 'POST', '/v1/_shutdown'
    elif args.command == 'self-update':
        method, target = 'POST', '/v1/_self_update'
        body = {'source': os.path.realpath(args.source)}
    elif args.command == 'events':
        query: ta.List[ta.Tuple[str, ta.Any]] = [('after', args.after)]
        query.extend(('topic', topic) for topic in args.topic)
        if args.follow:
            query.append(('follow', 'true'))
        target = '/v1/events?' + urllib.parse.urlencode(query)
        if args.follow:
            try:
                return 0 if client.stream(target, lambda data: _systevisor_main_write(1, data)) < 400 else 1
            except KeyboardInterrupt:
                return 130
    elif args.command == 'logs':
        query = [('offset', args.offset), ('limit', args.limit)]
        if args.follow:
            query.append(('follow', 'true'))
        target = (
            f'/v1/logs/{args.run_id}/{args.stream}?' +
            urllib.parse.urlencode(query)
        )
        if args.follow:
            def consume_log_line(line: bytes) -> None:
                item = json.loads(line.decode('utf-8'))
                if item.get('type') == 'log':
                    _systevisor_main_write(1, base64.b64decode(item['data_base64']))
                else:
                    _systevisor_main_write(2, line + b'\n')

            consumer = SystevisorNdjsonConsumer(consume_log_line)
            try:
                status = client.stream(target, consumer.feed)
                consumer.finish()
                return 0 if status < 400 else 1
            except KeyboardInterrupt:
                return 130

    response = client.request(method, target, body)
    try:
        value = codec.loads(response.body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        _systevisor_main_write(1 if response.status < 400 else 2, response.body)
    else:
        _systevisor_main_print_json(value, codec, 1 if response.status < 400 else 2)
    return 0 if response.status < 400 else 1


def _systevisor_main_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='systevisor')
    parser.add_argument(
        '--endpoint',
        default=os.environ.get('SYSTEVISOR_ENDPOINT', _SYSTEVISOR_MAIN_DEFAULT_ENDPOINT),
        help='Unix socket path/unix:PATH or http://HOST:PORT',
    )
    parser.add_argument('--timeout', type=float, default=10.)
    subparsers = parser.add_subparsers(dest='command', required=True)

    serve = subparsers.add_parser('serve')
    serve.add_argument('-c', '--config', action='append', required=True)
    serve.add_argument('--recursive', action='store_true')
    serve.add_argument('--state-directory')

    run = subparsers.add_parser('run')
    run.add_argument('collection')
    run.add_argument('-c', '--config', action='append', required=True)
    run.add_argument('--recursive', action='store_true')
    run.add_argument('--state-directory')

    config_check = subparsers.add_parser('config-check')
    config_check.add_argument('-c', '--config', action='append', required=True)
    config_check.add_argument('--recursive', action='store_true')

    service_template = subparsers.add_parser('service-template')
    service_template.add_argument('platform', choices=('systemd', 'launchd'))
    service_template.add_argument('--executable', required=True)
    service_template.add_argument('-c', '--config', action='append', required=True)
    service_template.add_argument('--identifier', default='systevisor')
    service_template.add_argument('--recursive', action='store_true')
    service_template.add_argument('--state-directory')

    for command in (
            'status', 'units', 'collections', 'schedules', 'config', 'operations', 'reload', 'check', 'shutdown',
    ):
        subparsers.add_parser(command)

    self_update = subparsers.add_parser('self-update')
    self_update.add_argument('source')

    self_update_probe = subparsers.add_parser('_self-update-probe', help=argparse.SUPPRESS)
    self_update_probe.add_argument('--request', required=True)
    self_update_probe.add_argument('--result', required=True)

    self_update_resume = subparsers.add_parser('_self-update-resume', help=argparse.SUPPRESS)
    self_update_resume.add_argument('--manifest', required=True)

    self_update_rollback = subparsers.add_parser('_self-update-rollback', help=argparse.SUPPRESS)
    self_update_rollback.add_argument('--manifest', required=True)
    self_update_rollback.add_argument('--error-file', required=True)

    resources = subparsers.add_parser('resources')
    resources.add_argument('run_id', type=int, nargs='?')

    for command in ('start', 'stop'):
        action = subparsers.add_parser(command)
        action.add_argument('target')
        action.add_argument('--kind', choices=('unit', 'collection', 'instance'), default='unit')

    restart = subparsers.add_parser('restart')
    restart.add_argument('instance')

    events = subparsers.add_parser('events')
    events.add_argument('--after', type=int, default=0)
    events.add_argument('--topic', action='append', default=[])
    events.add_argument('--follow', action='store_true')

    logs = subparsers.add_parser('logs')
    logs.add_argument('run_id', type=int)
    logs.add_argument('stream', choices=('stdout', 'stderr'))
    logs.add_argument('--offset', type=int, default=0)
    logs.add_argument('--limit', type=int, default=64 * 1024)
    logs.add_argument('--follow', action='store_true')

    return parser


def systevisor_main(argv: ta.Optional[ta.Sequence[str]] = None) -> int:
    args = _systevisor_main_parser().parse_args(argv)
    if args.command == 'config-check':
        return _systevisor_main_config_check(args)
    if args.command == 'service-template':
        return _systevisor_main_service_template(args)
    if args.command == 'serve':
        return _systevisor_main_serve(args)
    if args.command == 'run':
        return _systevisor_main_run(args)
    if args.command == '_self-update-probe':
        return systevisor_run_self_update_probe(args.request, args.result, os.path.realpath(sys.argv[0]))
    if args.command == '_self-update-resume':
        return _systevisor_main_resume(args)
    if args.command == '_self-update-rollback':
        return _systevisor_main_resume(args, rollback=True)
    return _systevisor_main_client(args)
