# @om-lite
# ruff: noqa: UP006 UP007 UP045
import abc
import ctypes
import dataclasses as dc
import enum
import os
import sys
import typing as ta

from omcore.lite.abstract import Abstract

from ..runtime.processes import SystevisorOwnedProcessState


class SystevisorResourceSamplingError(Exception):
    pass


class SystevisorResourceIdentityError(SystevisorResourceSamplingError):
    pass


class SystevisorResourceSampleSource(enum.Enum):
    LINUX_PROCFS = 'linux_procfs'
    DARWIN_LIBPROC = 'darwin_libproc'


@dc.dataclass(frozen=True)
class SystevisorProcessResourceCounters:
    source: SystevisorResourceSampleSource
    birth_identity: ta.Optional[str]
    cpu_user_secs: ta.Optional[float] = None
    cpu_system_secs: ta.Optional[float] = None
    memory_rss_bytes: ta.Optional[int] = None
    memory_virtual_bytes: ta.Optional[int] = None
    thread_count: ta.Optional[int] = None
    minor_faults: ta.Optional[int] = None
    major_faults: ta.Optional[int] = None
    read_bytes: ta.Optional[int] = None
    write_bytes: ta.Optional[int] = None
    read_operations: ta.Optional[int] = None
    write_operations: ta.Optional[int] = None
    voluntary_context_switches: ta.Optional[int] = None
    involuntary_context_switches: ta.Optional[int] = None


class SystevisorProcessResourceSampler(Abstract):
    @abc.abstractmethod
    def sample(self, process: SystevisorOwnedProcessState) -> SystevisorProcessResourceCounters:
        raise NotImplementedError


@dc.dataclass(frozen=True)
class SystevisorLinuxProcStat:
    birth_identity: str
    cpu_user_ticks: int
    cpu_system_ticks: int
    rss_pages: int
    virtual_bytes: int
    thread_count: int
    minor_faults: int
    major_faults: int


def systevisor_parse_linux_proc_stat(value: str, pid: int) -> SystevisorLinuxProcStat:
    close_paren = value.rfind(')')
    if close_paren < 0:
        raise SystevisorResourceSamplingError(f'malformed procfs stat for pid {pid}')
    fields = value[close_paren + 2:].split()
    if len(fields) <= 21:
        raise SystevisorResourceSamplingError(f'truncated procfs stat for pid {pid}')
    try:
        return SystevisorLinuxProcStat(
            birth_identity=fields[19],
            cpu_user_ticks=int(fields[11]),
            cpu_system_ticks=int(fields[12]),
            rss_pages=int(fields[21]),
            virtual_bytes=int(fields[20]),
            thread_count=int(fields[17]),
            minor_faults=int(fields[7]),
            major_faults=int(fields[9]),
        )
    except (IndexError, ValueError) as exc:
        raise SystevisorResourceSamplingError(f'invalid procfs stat values for pid {pid}') from exc


def _systevisor_resource_linux_proc_stat(pid: int) -> SystevisorLinuxProcStat:
    try:
        with open(f'/proc/{pid}/stat') as stat_file:
            value = stat_file.read()
    except OSError as exc:
        raise SystevisorResourceSamplingError(f'cannot read procfs stat for pid {pid}: {exc}') from exc
    return systevisor_parse_linux_proc_stat(value, pid)


def _systevisor_resource_linux_key_values(path: str, separator: str = ':') -> ta.Mapping[str, str]:
    try:
        with open(path) as input_file:
            lines = input_file.readlines()
    except OSError:
        return {}
    values: ta.Dict[str, str] = {}
    for line in lines:
        key, found, value = line.partition(separator)
        if found:
            values[key.strip()] = value.strip()
    return values


def _systevisor_resource_optional_int(values: ta.Mapping[str, str], name: str) -> ta.Optional[int]:
    value = values.get(name)
    if value is None:
        return None
    try:
        return int(value.split()[0])
    except (IndexError, ValueError):
        return None


class SystevisorLinuxProcfsResourceSampler(SystevisorProcessResourceSampler):
    def __init__(self) -> None:
        self._clock_ticks = int(os.sysconf('SC_CLK_TCK'))
        self._page_size = int(os.sysconf('SC_PAGE_SIZE'))

    def sample(self, process: SystevisorOwnedProcessState) -> SystevisorProcessResourceCounters:
        first = _systevisor_resource_linux_proc_stat(process.pid)
        if process.birth_identity is not None and first.birth_identity != process.birth_identity:
            raise SystevisorResourceIdentityError(
                f'pid {process.pid} birth identity changed for run {process.run_id}',
            )
        status = _systevisor_resource_linux_key_values(f'/proc/{process.pid}/status')
        io_values = _systevisor_resource_linux_key_values(f'/proc/{process.pid}/io')
        second = _systevisor_resource_linux_proc_stat(process.pid)
        if second.birth_identity != first.birth_identity:
            raise SystevisorResourceIdentityError(
                f'pid {process.pid} changed identity while sampling run {process.run_id}',
            )
        return SystevisorProcessResourceCounters(
            source=SystevisorResourceSampleSource.LINUX_PROCFS,
            birth_identity=second.birth_identity,
            cpu_user_secs=second.cpu_user_ticks / self._clock_ticks,
            cpu_system_secs=second.cpu_system_ticks / self._clock_ticks,
            memory_rss_bytes=max(0, second.rss_pages) * self._page_size,
            memory_virtual_bytes=second.virtual_bytes,
            thread_count=second.thread_count,
            minor_faults=second.minor_faults,
            major_faults=second.major_faults,
            read_bytes=_systevisor_resource_optional_int(io_values, 'read_bytes'),
            write_bytes=_systevisor_resource_optional_int(io_values, 'write_bytes'),
            read_operations=_systevisor_resource_optional_int(io_values, 'syscr'),
            write_operations=_systevisor_resource_optional_int(io_values, 'syscw'),
            voluntary_context_switches=_systevisor_resource_optional_int(status, 'voluntary_ctxt_switches'),
            involuntary_context_switches=_systevisor_resource_optional_int(status, 'nonvoluntary_ctxt_switches'),
        )


class SystevisorDarwinProcTaskInfo(ctypes.Structure):
    _fields_ = [
        ('virtual_size', ctypes.c_uint64),
        ('resident_size', ctypes.c_uint64),
        ('total_user', ctypes.c_uint64),
        ('total_system', ctypes.c_uint64),
        ('threads_user', ctypes.c_uint64),
        ('threads_system', ctypes.c_uint64),
        ('policy', ctypes.c_int32),
        ('faults', ctypes.c_int32),
        ('pageins', ctypes.c_int32),
        ('cow_faults', ctypes.c_int32),
        ('messages_sent', ctypes.c_int32),
        ('messages_received', ctypes.c_int32),
        ('syscalls_mach', ctypes.c_int32),
        ('syscalls_unix', ctypes.c_int32),
        ('context_switches', ctypes.c_int32),
        ('thread_count', ctypes.c_int32),
        ('running_thread_count', ctypes.c_int32),
        ('priority', ctypes.c_int32),
    ]


class SystevisorDarwinLibprocResourceSampler(SystevisorProcessResourceSampler):
    def sample(self, process: SystevisorOwnedProcessState) -> SystevisorProcessResourceCounters:
        if not _systevisor_resource_is_darwin():
            raise SystevisorResourceSamplingError('Darwin libproc sampling is unavailable on this platform')
        libproc = ctypes.CDLL('/usr/lib/libproc.dylib', use_errno=True)
        proc_pidinfo = libproc.proc_pidinfo
        proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
        proc_pidinfo.restype = ctypes.c_int
        task_info = SystevisorDarwinProcTaskInfo()
        size = ctypes.sizeof(task_info)
        result = proc_pidinfo(process.pid, 4, 0, ctypes.byref(task_info), size)
        if result != size:
            error_number = ctypes.get_errno()
            if error_number:
                raise SystevisorResourceSamplingError(
                    f'proc_pidinfo failed for pid {process.pid}: {os.strerror(error_number)}',
                )
            raise SystevisorResourceSamplingError(f'proc_pidinfo returned {result} bytes; expected {size}')
        return SystevisorProcessResourceCounters(
            source=SystevisorResourceSampleSource.DARWIN_LIBPROC,
            birth_identity=process.birth_identity,
            cpu_user_secs=task_info.total_user / 1_000_000_000.,
            cpu_system_secs=task_info.total_system / 1_000_000_000.,
            memory_rss_bytes=int(task_info.resident_size),
            memory_virtual_bytes=int(task_info.virtual_size),
            thread_count=int(task_info.thread_count),
            minor_faults=int(task_info.faults),
            major_faults=int(task_info.pageins),
            voluntary_context_switches=int(task_info.context_switches),
        )


class SystevisorSystemProcessResourceSampler(SystevisorProcessResourceSampler):
    def __init__(self) -> None:
        self._sampler: ta.Optional[SystevisorProcessResourceSampler] = None

    def sample(self, process: SystevisorOwnedProcessState) -> SystevisorProcessResourceCounters:
        if self._sampler is None:
            if sys.platform == 'linux':
                self._sampler = SystevisorLinuxProcfsResourceSampler()
            elif sys.platform == 'darwin':
                self._sampler = SystevisorDarwinLibprocResourceSampler()
            else:
                raise SystevisorResourceSamplingError(f'unsupported resource sampling platform: {sys.platform}')
        return self._sampler.sample(process)


def _systevisor_resource_is_darwin() -> bool:
    return sys.platform == 'darwin'
