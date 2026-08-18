# @om-lite
# ruff: noqa: UP006 UP007 UP045
import abc
import ctypes
import os
import sys
import typing as ta

from omcore.lite.abstract import Abstract

from ..configs.models import SystevisorNamespaceConfig
from ..runtime.processes import SystevisorChildContext
from ..runtime.processes import SystevisorChildModifier


_SYSTEVISOR_NAMESPACE_CLONE_NEWNS = 0x00020000
_SYSTEVISOR_NAMESPACE_CLONE_NEWCGROUP = 0x02000000
_SYSTEVISOR_NAMESPACE_CLONE_NEWUTS = 0x04000000
_SYSTEVISOR_NAMESPACE_CLONE_NEWIPC = 0x08000000
_SYSTEVISOR_NAMESPACE_CLONE_NEWNET = 0x40000000

_SYSTEVISOR_NAMESPACE_MS_REC = 16384
_SYSTEVISOR_NAMESPACE_MS_PRIVATE = 1 << 18


class SystevisorNamespaceError(Exception):
    pass


class SystevisorNamespaceBackend(Abstract):
    @abc.abstractmethod
    def apply(self, flags: int, *, private_mounts: bool, hostname: ta.Optional[str]) -> None:
        raise NotImplementedError


class SystevisorLinuxNamespaceBackend(SystevisorNamespaceBackend):
    def apply(self, flags: int, *, private_mounts: bool, hostname: ta.Optional[str]) -> None:
        if sys.platform != 'linux':
            raise SystevisorNamespaceError('namespace isolation is supported only on Linux')
        libc = ctypes.CDLL(None, use_errno=True)
        libc_unshare = getattr(libc, 'unshare', None)
        if libc_unshare is None:
            raise SystevisorNamespaceError('libc does not expose unshare')
        libc_unshare.argtypes = [ctypes.c_int]
        libc_unshare.restype = ctypes.c_int
        if libc_unshare(flags) != 0:
            error_number = ctypes.get_errno()
            raise OSError(error_number, os.strerror(error_number), 'unshare')

        if private_mounts:
            libc_mount = getattr(libc, 'mount', None)
            if libc_mount is None:
                raise SystevisorNamespaceError('libc does not expose mount')
            libc_mount.argtypes = [
                ctypes.c_char_p,
                ctypes.c_char_p,
                ctypes.c_char_p,
                ctypes.c_ulong,
                ctypes.c_void_p,
            ]
            libc_mount.restype = ctypes.c_int
            if libc_mount(
                    None,
                    b'/',
                    None,
                    _SYSTEVISOR_NAMESPACE_MS_REC | _SYSTEVISOR_NAMESPACE_MS_PRIVATE,
                    None,
            ) != 0:
                error_number = ctypes.get_errno()
                raise OSError(error_number, os.strerror(error_number), 'mount-private')

        if hostname is not None:
            libc_sethostname = getattr(libc, 'sethostname', None)
            if libc_sethostname is None:
                raise SystevisorNamespaceError('libc does not expose sethostname')
            encoded = hostname.encode('utf-8')
            libc_sethostname.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
            libc_sethostname.restype = ctypes.c_int
            if libc_sethostname(encoded, len(encoded)) != 0:
                error_number = ctypes.get_errno()
                raise OSError(error_number, os.strerror(error_number), 'sethostname')


def systevisor_namespace_flags(config: SystevisorNamespaceConfig) -> int:
    flags = 0
    if config.mount:
        flags |= _SYSTEVISOR_NAMESPACE_CLONE_NEWNS
    if config.cgroup:
        flags |= _SYSTEVISOR_NAMESPACE_CLONE_NEWCGROUP
    if config.uts:
        flags |= _SYSTEVISOR_NAMESPACE_CLONE_NEWUTS
    if config.ipc:
        flags |= _SYSTEVISOR_NAMESPACE_CLONE_NEWIPC
    if config.network:
        flags |= _SYSTEVISOR_NAMESPACE_CLONE_NEWNET
    return flags


class SystevisorNamespaceChildModifier(SystevisorChildModifier):
    def __init__(self, backend: SystevisorNamespaceBackend) -> None:
        self._backend = backend

    def before_identity(self, context: SystevisorChildContext) -> None:
        if context.run_id <= 0:
            return
        config = context.spec.unit.resources.namespaces
        flags = systevisor_namespace_flags(config)
        if flags:
            self._backend.apply(flags, private_mounts=config.mount, hostname=config.hostname)

