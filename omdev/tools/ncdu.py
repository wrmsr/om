"""
pyncdu: a self-contained, standard-library disk-usage browser for macOS and Linux.

    python3 pyncdu.py /some/directory
    python3 pyncdu.py -x --exclude '.git' --exclude 'node_modules' .
    python3 pyncdu.py --scan-only --export usage.jsonl /some/directory
    python3 pyncdu.py --import usage.jsonl

Python 3.11+ with curses for the TUI; developed for CPython 3.14, including free-threaded builds. Only the scanner
touches the filesystem during live browsing. The UI owns the tree and caches subtree totals, directory orderings, and
rendered lines. Cached totals are observations, not a filesystem snapshot: use r to rescan after external changes. An
exported snapshot is explicitly historical and can be browsed offline. Directory mtimes are never used to assume
children are unchanged.

Sizes include directory metadata. Hard links are charged to their first encountered name by default. Symlinks are
measured without following their targets, even when passed as the root argument. Allocated bytes come from st_blocks *
512, not st_blksize. Filesystem compression, copy-on-write clones, and snapshots mean this is not necessarily the amount
of storage deleting a pathname would reclaim. Deletion is opt-in (--allow-delete), requires a completed live scan, and
asks for typed confirmation.

Controls are documented by --help and the ? key. No third-party modules or subprocess tools are used.
"""
import argparse
import collections
import dataclasses as dc
import errno
import fnmatch
import functools
import json
import locale
import math
import os
import queue
import shutil
import stat
import sys
import tempfile
import threading
import time
import typing as ta
import unicodedata


curses: ta.Any
try:
    import curses
except ImportError:
    curses = None


##


@dc.dataclass(frozen=True, slots=True, kw_only=True)
class ScanOptions:
    one_file_system: bool = False
    count_links: bool = False
    exclude: tuple[str, ...] = ()
    retain_identity: bool = False


@dc.dataclass(frozen=True, slots=True, kw_only=True)
class ScanEntry:
    id: int
    name: str
    kind: str
    own_allocated: int = 0
    own_apparent: int = 0
    raw_allocated: int = 0
    raw_apparent: int = 0
    error: str | None = None
    skipped: str | None = None
    duplicate: bool = False
    identity: tuple[int, int] | None = None


@dc.dataclass(frozen=True, slots=True, kw_only=True)
class RootEvent:
    entry: ScanEntry


@dc.dataclass(frozen=True, slots=True, kw_only=True)
class EntriesEvent:
    parent_id: int
    entries: tuple[ScanEntry, ...]


@dc.dataclass(frozen=True, slots=True, kw_only=True)
class DirDoneEvent:
    node_id: int
    error: str | None = None


@dc.dataclass(frozen=True, slots=True, kw_only=True)
class FinishEvent:
    cancelled: bool = False
    error: str | None = None


ScanEvent: ta.TypeAlias = RootEvent | EntriesEvent | DirDoneEvent | FinishEvent


##


@dc.dataclass(slots=True, eq=False, kw_only=True)
class Node:
    id: int
    parent_id: int | None
    name: str
    kind: str
    own_allocated: int = 0
    own_apparent: int = 0
    raw_allocated: int = 0
    raw_apparent: int = 0
    allocated: int = 0
    apparent: int = 0
    items: int = 0
    children: list[int] | None = None
    error: str | None = None
    skipped: str | None = None
    duplicate: bool = False
    identity: tuple[int, int] | None = None
    complete: bool = False
    revision: int = 0
    listed: bool = False
    pending_children: int = 0


class TreeModel:
    """One thread owns these mutable records; completed trees may be shared for reading."""

    def __init__(self, root_path: str) -> None:
        super().__init__()

        self.root_path: str = root_path
        self.nodes: dict[int, Node] = {
            0: Node(
                id=0,
                parent_id=None,
                name=os.path.basename(root_path.rstrip(os.sep)) or root_path,
                kind='dir',
                children=[],
            ),
        }
        self.revision: int = 0
        self.complete: bool = False
        self.cancelled: bool = False
        self.error: str | None = None
        self.errors: int = 0
        self.started_at: float = time.monotonic()
        self.ended_at: float | None = None
        self.scanned_entries: int = 0

    @staticmethod
    def _make_node(entry: ScanEntry, *, parent_id: int | None) -> Node:
        complete = entry.kind != 'dir' or entry.error is not None or entry.skipped is not None
        return Node(
            id=entry.id,
            parent_id=parent_id,
            name=entry.name,
            kind=entry.kind,
            own_allocated=entry.own_allocated,
            own_apparent=entry.own_apparent,
            raw_allocated=entry.raw_allocated,
            raw_apparent=entry.raw_apparent,
            allocated=entry.own_allocated,
            apparent=entry.own_apparent,
            children=[] if entry.kind == 'dir' else None,
            error=entry.error,
            skipped=entry.skipped,
            duplicate=entry.duplicate,
            identity=entry.identity,
            complete=complete,
            listed=complete,
        )

    def _add_totals(
            self,
            node_id: int | None,
            *,
            allocated: int,
            apparent: int,
            items: int,
    ) -> None:
        # A batch pays the ancestor-walk cost once, rather than once per file.
        while node_id is not None:
            node = self.nodes[node_id]
            node.allocated += allocated
            node.apparent += apparent
            node.items += items
            node.revision += 1
            node_id = node.parent_id
        self.revision += 1

    def _finish_directory(self, node_id: int) -> None:
        node = self.nodes[node_id]
        node.revision += 1
        while node.listed and not node.pending_children and not node.complete:
            node.complete = True
            if node.parent_id is None:
                break
            node = self.nodes[node.parent_id]
            node.pending_children -= 1
            node.revision += 1

    def apply(self, event: ScanEvent) -> None:
        if isinstance(event, RootEvent):
            self.nodes[0] = self._make_node(event.entry, parent_id=None)
            self.errors += event.entry.error is not None
            self.revision += 1

        elif isinstance(event, EntriesEvent):
            parent = self.nodes[event.parent_id]
            if parent.children is None:
                raise ValueError('entries received for a non-directory')

            allocated = 0
            apparent = 0
            for entry in event.entries:
                node = self._make_node(entry, parent_id=parent.id)
                self.nodes[node.id] = node
                parent.children.append(node.id)
                if not node.complete:
                    parent.pending_children += 1
                allocated += node.allocated
                apparent += node.apparent
                self.errors += node.error is not None

            self.scanned_entries += len(event.entries)
            self._add_totals(
                parent.id,
                allocated=allocated,
                apparent=apparent,
                items=len(event.entries),
            )

        elif isinstance(event, DirDoneEvent):
            node = self.nodes[event.node_id]
            node.listed = True
            if event.error is not None:
                if node.error is None:
                    self.errors += 1
                node.error = event.error
            self._finish_directory(node.id)
            self.revision += 1

        elif isinstance(event, FinishEvent):
            self.complete = True
            self.cancelled = event.cancelled
            self.error = event.error
            self.ended_at = time.monotonic()
            self.revision += 1

        else:
            raise TypeError(event)

    def get_path(self, node_id: int) -> str:
        parts: list[str] = []
        node = self.nodes[node_id]
        while node.parent_id is not None:
            parts.append(node.name)
            node = self.nodes[node.parent_id]
        return os.path.join(self.root_path, *reversed(parts))

    def get_children(self, node_id: int) -> ta.Sequence[int]:
        children = self.nodes[node_id].children
        return children if children is not None else ()


##


@dc.dataclass(frozen=True, slots=True, kw_only=True)
class _ScanDirectory:
    id: int
    name: str
    parent: ta.Self | None
    device: int
    inode: int


class ScanWorker:
    """A single producer publishes immutable, bounded batches without calling curses."""

    _BATCH_SIZE: ta.ClassVar[int] = 256
    _BATCH_SECONDS: ta.ClassVar[float] = 0.04
    _QUEUE_SIZE: ta.ClassVar[int] = 16

    def __init__(self, path: str, *, options: ScanOptions = ScanOptions()) -> None:
        super().__init__()

        self._path: str = path
        self._options: ScanOptions = options
        self._events: queue.Queue[ScanEvent] = queue.Queue(maxsize=self._QUEUE_SIZE)
        self._cancel: threading.Event = threading.Event()
        self._finished: threading.Event = threading.Event()
        self._thread: threading.Thread | None = None
        self._result: FinishEvent | None = None
        self._result_delivered: bool = False
        self._next_id: int = 1
        self._root_device: int = 0
        self._seen_links: set[tuple[int, int]] = set()
        self._seen_directories: set[tuple[int, int]] = set()

    def cancel(self) -> None:
        self._cancel.set()

    def poll(self, *, max_batches: int = 16) -> list[ScanEvent]:
        events: list[ScanEvent] = []
        for _ in range(max_batches):
            try:
                events.append(self._events.get_nowait())
            except queue.Empty:
                break

        # The terminal event has a reserved slot: cancellation cannot strand the UI behind a full queue. All published
        # entry batches are delivered before it.
        if (
                len(events) < max_batches and
                self._finished.is_set() and
                not self._result_delivered and
                self._events.empty()
        ):
            result = self._result
            if result is not None:
                events.append(result)
                self._result_delivered = True
        return events

    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def finished(self) -> threading.Event:
        return self._finished

    def _publish(self, event: ScanEvent) -> bool:
        while not self._cancel.is_set():
            try:
                self._events.put(event, timeout=0.05)
            except queue.Full:
                continue
            return True

        return False

    @staticmethod
    def _error_text(error: OSError) -> str:
        return f'{type(error).__name__}: {error.strerror or str(error)}'

    def _entry_from_stat(self, node_id: int, name: str, info: os.stat_result) -> ScanEntry:
        if stat.S_ISDIR(info.st_mode):
            kind = 'dir'
        elif stat.S_ISREG(info.st_mode):
            kind = 'file'
        elif stat.S_ISLNK(info.st_mode):
            kind = 'link'
        else:
            kind = 'other'

        raw_apparent = max(0, info.st_size)
        blocks = getattr(info, 'st_blocks', None)
        raw_allocated = max(0, blocks * 512) if blocks is not None else raw_apparent
        allocated = raw_allocated
        apparent = raw_apparent
        duplicate = False
        skipped: str | None = None
        identity = (info.st_dev, info.st_ino)

        if kind == 'dir':
            if node_id and self._options.one_file_system and info.st_dev != self._root_device:
                skipped = 'different filesystem'
            elif identity in self._seen_directories:
                skipped = 'directory already visited'
            else:
                self._seen_directories.add(identity)
            if skipped is not None:
                allocated = apparent = 0

        elif info.st_nlink > 1 and not self._options.count_links:
            if identity in self._seen_links:
                allocated = apparent = 0
                duplicate = True
            else:
                self._seen_links.add(identity)

        return ScanEntry(
            id=node_id,
            name=name,
            kind=kind,
            own_allocated=allocated,
            own_apparent=apparent,
            raw_allocated=raw_allocated,
            raw_apparent=raw_apparent,
            skipped=skipped,
            duplicate=duplicate,
            identity=identity if self._options.retain_identity else None,
        )

    def _is_excluded(self, name: str, *, relative: str) -> bool:
        if not self._options.exclude:
            return False
        path = f'{relative}/{name}' if relative else name
        return any(
            fnmatch.fnmatchcase(name, pattern) or fnmatch.fnmatchcase(path, pattern)
            for pattern in self._options.exclude
        )

    def _scan_directory(self, directory: _ScanDirectory, pending: list[_ScanDirectory]) -> None:
        parts: list[str] = []
        ancestor = directory
        while ancestor.parent is not None:
            parts.append(ancestor.name)
            ancestor = ancestor.parent
        parts.reverse()
        path = os.path.join(self._path, *parts)
        relative = '/'.join(parts)

        batch: list[ScanEntry] = []
        error: str | None = None
        fd: int | None = None
        last_flush = time.monotonic()
        try:
            # Verify queued directories at use time. A renamed/replaced directory must not turn into traversal of an
            # unrelated tree or a followed symlink.
            flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, 'O_CLOEXEC', 0)
            fd = os.open(path, flags)
            current = os.fstat(fd)
            if (current.st_dev, current.st_ino) != (directory.device, directory.inode):
                raise OSError(errno.ESTALE, 'directory changed during scan')

            # scandir owns its own descriptor. Both descriptors close before descent, so neither Python recursion nor
            # one open descriptor per depth is needed.
            with os.scandir(fd) as entries:
                for entry in entries:
                    if self._cancel.is_set():
                        return

                    node_id = self._next_id
                    self._next_id += 1
                    if self._is_excluded(entry.name, relative=relative):
                        record = ScanEntry(id=node_id, name=entry.name, kind='other', skipped='excluded')
                    else:
                        try:
                            entry_stat = entry.stat(follow_symlinks=False)
                        except OSError as exc:
                            record = ScanEntry(
                                id=node_id,
                                name=entry.name,
                                kind='error',
                                error=self._error_text(exc),
                            )
                        else:
                            record = self._entry_from_stat(node_id, entry.name, entry_stat)
                            if record.kind == 'dir' and record.skipped is None:
                                pending.append(_ScanDirectory(
                                    id=node_id,
                                    name=entry.name,
                                    parent=directory,
                                    device=entry_stat.st_dev,
                                    inode=entry_stat.st_ino,
                                ))

                    batch.append(record)
                    now = time.monotonic()
                    if len(batch) >= self._BATCH_SIZE or now - last_flush >= self._BATCH_SECONDS:
                        if not self._publish(EntriesEvent(parent_id=directory.id, entries=tuple(batch))):
                            return
                        batch.clear()
                        last_flush = time.monotonic()

        except OSError as exc:
            error = self._error_text(exc)
        finally:
            if fd is not None:
                os.close(fd)

        if batch:
            if not self._publish(EntriesEvent(parent_id=directory.id, entries=tuple(batch))):
                return
        self._publish(DirDoneEvent(node_id=directory.id, error=error))

    def _scan(self) -> str | None:
        if self._cancel.is_set():
            return None
        root_name = os.path.basename(self._path.rstrip(os.sep)) or self._path
        try:
            root_stat = os.lstat(self._path)
        except OSError as exc:
            error = self._error_text(exc)
            self._publish(RootEvent(entry=ScanEntry(id=0, name=root_name, kind='error', error=error)))
            return error

        self._root_device = root_stat.st_dev
        root_entry = self._entry_from_stat(0, root_name, root_stat)
        if not self._publish(RootEvent(entry=root_entry)) or root_entry.kind != 'dir':
            return None

        pending = [
            _ScanDirectory(
                id=0,
                name='',
                parent=None,
                device=root_stat.st_dev,
                inode=root_stat.st_ino,
            ),
        ]
        while pending and not self._cancel.is_set():
            self._scan_directory(pending.pop(), pending)
        return None

    def _run(self) -> None:
        error: str | None = None
        try:
            error = self._scan()
        except Exception as exc:  # noqa
            # Report unexpected scanner failures inside the UI.
            error = f'{type(exc).__name__}: {exc}'
        finally:
            self._seen_links.clear()
            self._seen_directories.clear()
            self._result = FinishEvent(cancelled=self._cancel.is_set(), error=error)
            self._finished.set()

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError('scan worker already started')
        self._thread = threading.Thread(target=self._run, name='pyncdu-scan', daemon=True)
        self._thread.start()


##
# Snapshots


class SnapshotError(Exception):
    pass


def write_snapshot(path: str, model: TreeModel, *, options: ScanOptions) -> str:
    """Write an explicitly requested, complete historical snapshot using atomic replacement."""

    if not model.complete or model.cancelled or model.error is not None:
        raise SnapshotError('cannot save an unfinished or failed scan')

    destination = os.path.abspath(os.path.expanduser(path))
    parent = os.path.dirname(destination)
    fd, temporary = tempfile.mkstemp(prefix='.pyncdu-', suffix='.tmp', dir=parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as output:
            header = {
                'pyncdu': 1,
                'root': model.root_path,
                'created': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'options': {
                    'one_file_system': options.one_file_system,
                    'count_links': options.count_links,
                    'exclude': options.exclude,
                },
            }
            output.write(json.dumps(header, ensure_ascii=True, separators=(',', ':')) + '\n')
            for node in model.nodes.values():
                record = [
                    node.id,
                    node.parent_id,
                    node.name,
                    node.kind,
                    node.own_allocated,
                    node.own_apparent,
                    node.raw_allocated,
                    node.raw_apparent,
                    node.error,
                    node.skipped,
                    node.duplicate,
                ]
                output.write(json.dumps(record, ensure_ascii=True, separators=(',', ':')) + '\n')
            output.write(json.dumps({'done': len(model.nodes)}) + '\n')
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, destination)

    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise

    return destination


def _check_snapshot_integer(value: ta.Any, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise SnapshotError('expected a nonnegative integer')
    return value


def _parse_snapshot_record(record: ta.Any) -> tuple[ScanEntry, int | None]:
    if not isinstance(record, list) or len(record) != 11:
        raise SnapshotError('invalid entry record')

    node_id = _check_snapshot_integer(record[0])
    parent_id = None if record[1] is None else _check_snapshot_integer(record[1])
    name = record[2]
    if not isinstance(name, str) or not name or '\x00' in name:
        raise SnapshotError('invalid entry name')
    if node_id and (os.sep in name or name in ('.', '..')):
        raise SnapshotError('entry name is not a single path component')
    kind = record[3]
    if kind not in ('dir', 'file', 'link', 'other', 'error'):
        raise SnapshotError('invalid entry kind')
    own_allocated, own_apparent, raw_allocated, raw_apparent = map(_check_snapshot_integer, record[4:8])
    error, skipped, duplicate = record[8:]
    if error is not None and not isinstance(error, str):
        raise SnapshotError('invalid entry error')
    if skipped is not None and not isinstance(skipped, str):
        raise SnapshotError('invalid exclusion reason')
    if type(duplicate) is not bool:
        raise SnapshotError('invalid hard-link flag')
    if (skipped or duplicate) and (own_allocated or own_apparent):
        raise SnapshotError('excluded or duplicate entries cannot contribute bytes')
    if own_allocated > raw_allocated or own_apparent > raw_apparent:
        raise SnapshotError('contributed size exceeds raw size')

    return (ScanEntry(
        id=node_id,
        name=name,
        kind=kind,
        own_allocated=own_allocated,
        own_apparent=own_apparent,
        raw_allocated=raw_allocated,
        raw_apparent=raw_apparent,
        error=error,
        skipped=skipped,
        duplicate=duplicate,
    ), parent_id)


def read_snapshot(path: str) -> tuple[TreeModel, ScanOptions]:
    """Read flat JSON records without opening any path described by the snapshot."""

    with open(os.path.expanduser(path), encoding='utf-8') as source:
        header = json.loads(source.readline(1_048_577))
        if not isinstance(header, dict) or type(header.get('pyncdu')) is not int or header['pyncdu'] != 1:
            raise SnapshotError('not a supported pyncdu snapshot')
        root_path = header.get('root')
        if not isinstance(root_path, str) or not os.path.isabs(root_path) or '\x00' in root_path:
            raise SnapshotError('snapshot root must be an absolute path')
        settings = header.get('options')
        if not isinstance(settings, dict):
            raise SnapshotError('invalid scan options')
        for name in ('one_file_system', 'count_links'):
            if type(settings.get(name)) is not bool:
                raise SnapshotError(f'invalid scan option: {name}')
        exclude = settings.get('exclude')
        if not isinstance(exclude, list) or any(not isinstance(item, str) for item in exclude):
            raise SnapshotError('invalid exclusion patterns')

        options = ScanOptions(
            one_file_system=settings['one_file_system'],
            count_links=settings['count_links'],
            exclude=tuple(exclude),
        )
        model = TreeModel(root_path)
        count = 0
        ended = False
        line_number = 1
        while True:
            line = source.readline(1_048_577)
            if not line:
                break
            line_number += 1
            if len(line) > 1_048_576:
                raise SnapshotError(f'oversized record at line {line_number}')
            record = json.loads(line)
            if isinstance(record, dict):
                if set(record) != {'done'} or _check_snapshot_integer(record['done']) != count:
                    raise SnapshotError('invalid snapshot footer')
                if source.read(1):
                    raise SnapshotError('unexpected data after snapshot footer')
                ended = True
                break

            entry, parent_id = _parse_snapshot_record(record)
            if count and entry.id in model.nodes:
                raise SnapshotError('duplicate entry id')
            if count == 0:
                if entry.id != 0 or parent_id is not None:
                    raise SnapshotError('first entry must be the root')
            else:
                if parent_id is None or parent_id not in model.nodes:
                    raise SnapshotError('parent must precede child')
                parent = model.nodes[parent_id]
                if parent.children is None or parent.skipped is not None:
                    raise SnapshotError('child has an invalid parent')
                parent.children.append(entry.id)
            model.nodes[entry.id] = model._make_node(entry, parent_id=parent_id)  # noqa
            model.errors += entry.error is not None
            count += 1

        if not ended or not count:
            raise SnapshotError('snapshot is truncated or empty')

        # The file is topological, so one bottom-up pass computes all aggregates. Replaying live ancestor updates here
        # would make deep snapshots quadratic.
        for node in reversed(model.nodes.values()):
            node.complete = True
            node.listed = True
            node.revision = 1
            if node.parent_id is not None:
                parent = model.nodes[node.parent_id]
                parent.allocated += node.allocated
                parent.apparent += node.apparent
                parent.items += node.items + 1
        model.scanned_entries = count - 1
        model.apply(FinishEvent())
        return (model, options)


##
# Deletion


class DeletionError(Exception):
    pass


def delete_entry(model: TreeModel, node_id: int) -> None:
    """Delete only explicitly enabled, freshly scanned entries, anchored to a verified parent descriptor."""

    if node_id == 0 or not model.complete or model.cancelled or model.error is not None:
        raise DeletionError('a completed live scan and a non-root selection are required')
    node = model.nodes[node_id]
    if node.identity is None or node.parent_id is None:
        raise DeletionError('entry identity is unavailable; rescan with --allow-delete')
    parent = model.nodes[node.parent_id]
    if parent.identity is None:
        raise DeletionError('parent identity is unavailable')
    if node.identity[0] != parent.identity[0]:
        raise DeletionError('refusing to delete a filesystem mount point')

    pending = [node_id]
    while pending:
        descendant = model.nodes[pending.pop()]
        if descendant.error or descendant.skipped:
            raise DeletionError('the selection contains unreadable or excluded entries')
        if descendant.identity is None or descendant.identity[0] != node.identity[0]:
            raise DeletionError('the selection crosses a filesystem boundary')
        pending.extend(descendant.children or ())

    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, 'O_CLOEXEC', 0)
    parent_fd = os.open(model.get_path(parent.id), flags)
    try:
        parent_stat = os.fstat(parent_fd)
        if (parent_stat.st_dev, parent_stat.st_ino) != parent.identity:
            raise DeletionError('parent directory changed since the scan; rescan first')
        current = os.stat(node.name, dir_fd=parent_fd, follow_symlinks=False)
        if (current.st_dev, current.st_ino) != node.identity:
            raise DeletionError('entry changed since the scan; rescan first')
        if stat.S_ISDIR(current.st_mode):
            if not shutil.rmtree.avoids_symlink_attacks:
                raise DeletionError('this Python build lacks descriptor-based recursive deletion')
            shutil.rmtree(node.name, dir_fd=parent_fd)
        else:
            os.unlink(node.name, dir_fd=parent_fd)
    finally:
        os.close(parent_fd)


##
# Display


@functools.lru_cache(maxsize=4096)
def format_size(value: int) -> str:
    if value < 1024:
        return f'{value} B'

    amount = float(value)
    for unit in ('KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB'):
        amount /= 1024
        if amount < 1024 or unit == 'EiB':
            return f'{amount:.1f} {unit}'

    raise RuntimeError(value)


@functools.lru_cache(maxsize=4096)
def escape_text(value: str, *, ascii_only: bool = False) -> str:
    result: list[str] = []
    for ch in value:
        number = ord(ch)
        if ch == '\\':
            result.append('\\\\')
        elif ch == '\n':
            result.append('\\n')
        elif ch == '\r':
            result.append('\\r')
        elif ch == '\t':
            result.append('\\t')
        elif 0xdc80 <= number <= 0xdcff:
            result.append(f'\\x{number - 0xdc00:02x}')
        elif not ch.isprintable() or (ascii_only and number > 127):
            if number <= 0xff:
                result.append(f'\\x{number:02x}')
            elif number <= 0xffff:
                result.append(f'\\u{number:04x}')
            else:
                result.append(f'\\U{number:08x}')
        else:
            result.append(ch)

    return ''.join(result)


@functools.lru_cache(maxsize=4096)
def measure_char(ch: str) -> int:
    if unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1


def measure_text(value: str) -> int:
    if value.isascii():
        return len(value)
    return sum(map(measure_char, value))


def clip_text(value: str, width: int, *, from_left: bool = False) -> str:
    if width <= 0:
        return ''
    if value.isascii():
        if len(value) <= width:
            return value
        return ('...' + value[-(width - 3):]) if from_left and width > 3 else value[:width]

    if measure_text(value) <= width:
        return value

    if from_left and width > 3:
        result: list[str] = []
        available = width - 3
        for ch in reversed(value):
            size = measure_char(ch)
            if size > available:
                break
            result.append(ch)
            available -= size
        return '...' + ''.join(reversed(result))

    result = []
    available = width
    for ch in value:
        size = measure_char(ch)
        if size > available:
            break
        if size or result:
            result.append(ch)
        available -= size
    return ''.join(result)


@dc.dataclass(frozen=True, slots=True)
class ViewOptions:
    sort: str = 'size'
    apparent: bool = False
    reverse: bool = False
    directories_first: bool = False
    query: str = ''
    hide_hidden: bool = False


@dc.dataclass(frozen=True, slots=True)
class DirectoryOrder:
    ids: tuple[int, ...]
    revision: int
    built_at: float
    rebuild_delay: float


class ViewCache:
    def __init__(self) -> None:
        super().__init__()

        self._orders: collections.OrderedDict[tuple[int, ViewOptions], DirectoryOrder] = collections.OrderedDict()
        self._rows: int = 0

    def clear(self) -> None:
        self._orders.clear()
        self._rows = 0

    def get_order(
            self,
            model: TreeModel,
            node_id: int,
            options: ViewOptions,
            *,
            force: bool = False,
    ) -> DirectoryOrder:
        key = (node_id, options)
        node = model.nodes[node_id]
        now = time.monotonic()
        previous = self._orders.get(key)
        if previous is not None:
            self._orders.move_to_end(key)
            if previous.revision == node.revision:
                return previous
            if not force and not model.complete and (now - previous.built_at < previous.rebuild_delay):
                return previous

        query = options.query.casefold()
        ids = [
            child_id
            for child_id in model.get_children(node_id)
            if (
                (not options.hide_hidden or not model.nodes[child_id].name.startswith('.')) and
                (not query or query in model.nodes[child_id].name.casefold())
            )
        ]

        def make_key(child_id: int) -> tuple[int, int | str, str, int]:
            child = model.nodes[child_id]
            group = -int(child.kind == 'dir') if options.directories_first else 0
            name = child.name.casefold()
            if options.sort == 'name':
                return (group, name, child.name, child_id)

            if options.sort == 'items':
                value = child.items
            else:
                value = child.apparent if options.apparent else child.allocated
            return (group, value if options.reverse else -value, name, child_id)

        ids.sort(key=make_key, reverse=options.sort == 'name' and options.reverse)
        if options.sort == 'name' and options.reverse and options.directories_first:
            ids.sort(key=lambda child_id: model.nodes[child_id].kind != 'dir')

        result = DirectoryOrder(
            ids=tuple(ids),
            revision=node.revision,
            built_at=time.monotonic(),
            rebuild_delay=max(0.35, min(3.0, (time.monotonic() - now) * 10)),
        )
        if previous is not None:
            self._rows -= len(previous.ids)
        self._orders[key] = result
        self._rows += len(result.ids)
        while len(self._orders) > 1 and (len(self._orders) > 32 or self._rows > 200_000):
            _, expired = self._orders.popitem(last=False)
            self._rows -= len(expired.ids)
        return result


class ScreenPainter:
    def __init__(self, screen: ta.Any, *, no_color: bool = False) -> None:
        super().__init__()

        self._screen: ta.Any = screen
        self._previous: list[tuple[str, int]] = []
        self._dimensions: tuple[int, int] = (0, 0)
        self.normal: int = curses.A_NORMAL
        self.heading: int = curses.A_BOLD
        self.directory: int = curses.A_BOLD
        self.error: int = curses.A_BOLD
        self.muted: int = curses.A_DIM
        self.selected: int = curses.A_REVERSE | curses.A_BOLD

        if not no_color and curses.has_colors():
            try:
                curses.start_color()
                try:
                    curses.use_default_colors()
                    background = -1
                except curses.error:
                    background = curses.COLOR_BLACK
                curses.init_pair(1, curses.COLOR_CYAN, background)
                curses.init_pair(2, curses.COLOR_YELLOW, background)
                curses.init_pair(3, curses.COLOR_RED, background)
                self.heading = curses.color_pair(1) | curses.A_BOLD
                self.directory = curses.color_pair(1)
                self.error = curses.color_pair(3) | curses.A_BOLD
            except curses.error:
                pass

    def invalidate(self) -> None:
        self._previous.clear()

    def draw(self, lines: ta.Sequence[tuple[str, int]]) -> None:
        height, width = self._screen.getmaxyx()
        dimensions = (height, width)
        if dimensions != self._dimensions:
            self._dimensions = dimensions
            self._previous.clear()
            self._screen.erase()

        current: list[tuple[str, int]] = []
        changed = False
        for row in range(height):
            text, attribute = lines[row] if row < len(lines) else ('', self.normal)
            text = clip_text(text, max(0, width - 1))
            line = (text, attribute)
            current.append(line)
            if row < len(self._previous) and self._previous[row] == line:
                continue

            changed = True
            try:
                self._screen.move(row, 0)
                self._screen.clrtoeol()
                if text:
                    self._screen.addstr(row, 0, text, attribute)
            except curses.error:
                # A resize may race the dimensions check; the next frame repairs the row.
                self._previous.clear()
                return

        self._previous = current
        if changed:
            self._screen.noutrefresh()
            curses.doupdate()


##
# Interface


@dc.dataclass(frozen=True, slots=True)
class UiOptions:
    apparent: bool = False
    no_mouse: bool = False
    no_color: bool = False
    ascii_only: bool = False
    allow_delete: bool = False
    refresh_interval: float = 0.1
    export_path: str | None = None
    import_path: str | None = None


@dc.dataclass(frozen=True, slots=True)
class NavigationPosition:
    selected_id: int | None
    offset: int


@dc.dataclass(frozen=True, slots=True)
class TaskResult:
    operation: str
    value: ta.Any = None
    error: str | None = None


class BackgroundTask:
    def __init__(self, operation: str, function: ta.Callable[[], ta.Any]) -> None:
        super().__init__()

        self.operation: str = operation
        self._function: ta.Callable[[], ta.Any] = function
        self._results: queue.Queue[TaskResult] = queue.Queue(maxsize=1)
        self._thread: threading.Thread = threading.Thread(target=self._run, name=f'pyncdu-{operation}', daemon=True)

    def _run(self) -> None:
        try:
            value = self._function()
        except Exception as error:  # noqa
            self._results.put(TaskResult(self.operation, error=f'{type(error).__name__}: {error}'))
        else:
            self._results.put(TaskResult(self.operation, value=value))

    def poll(self) -> TaskResult | None:
        try:
            return self._results.get_nowait()
        except queue.Empty:
            return None

    def start(self) -> None:
        self._thread.start()


class DiskUsageUi:
    def __init__(
            self,
            screen: ta.Any,
            path: str,
            *,
            scan_options: ScanOptions,
            ui_options: UiOptions,
    ) -> None:
        super().__init__()

        self._screen: ta.Any = screen
        self._path: str = path
        self._scan_options: ScanOptions = scan_options
        self._options: UiOptions = ui_options
        self._painter: ScreenPainter = ScreenPainter(screen, no_color=ui_options.no_color)
        self._model: TreeModel = TreeModel(path)
        self._worker: ScanWorker | None = None
        self._task: BackgroundTask | None = None
        self._cache: ViewCache = ViewCache()
        self._paths: collections.OrderedDict[int, str] = collections.OrderedDict()
        self._path_characters: int = 0
        self._view: ViewOptions = ViewOptions(apparent=ui_options.apparent)
        self._directory_id: int = 0
        self._order: DirectoryOrder | None = None
        self._rows: tuple[int, ...] = ()
        self._cursor: int = 0
        self._offset: int = 0
        self._history: dict[int, NavigationPosition] = {}
        self._dialog: str | None = None
        self._dialog_offset: int = 0
        self._editing_filter: bool = False
        self._filter_before: str = ''
        self._message: str = ''
        self._message_until: float = 0
        self._quit: bool = False
        self._quit_after_task: bool = False
        self._restart_pending: bool = False
        self._exported: bool = False
        self._snapshot: bool = bool(ui_options.import_path)
        self._dirty: bool = True
        self._last_draw: float = 0
        self._last_dimensions: tuple[int, int] = (0, 0)
        self._last_click: tuple[int, int, float] | None = None
        self._delete_id: int | None = None
        self._confirmation: str = ''

    def _escape(self, value: str) -> str:
        return escape_text(value, ascii_only=self._options.ascii_only)

    def _get_path(self, node_id: int) -> str:
        previous = self._paths.get(node_id)
        if previous is not None:
            self._paths.move_to_end(node_id)
            return previous

        path = self._model.get_path(node_id)
        self._paths[node_id] = path
        self._path_characters += len(path)
        while len(self._paths) > 1 and (len(self._paths) > 256 or self._path_characters > 262_144):
            _, expired = self._paths.popitem(last=False)
            self._path_characters -= len(expired)
        return path

    def _set_message(self, value: str) -> None:
        self._message = value
        self._message_until = time.monotonic() + 5
        self._dirty = True

    def _selected_id(self) -> int | None:
        return self._rows[self._cursor] if 0 <= self._cursor < len(self._rows) else None

    def _body_height(self) -> int:
        return max(1, self._screen.getmaxyx()[0] - 7)

    def _keep_visible(self) -> None:
        self._cursor = min(max(0, self._cursor), max(0, len(self._rows) - 1))
        height = self._body_height()
        self._offset = min(self._offset, max(0, len(self._rows) - height))
        if self._cursor < self._offset:
            self._offset = self._cursor
        elif self._cursor >= self._offset + height:
            self._offset = self._cursor - height + 1

    def _refresh_order(self, *, force: bool = False) -> None:
        selected = self._selected_id()
        order = self._cache.get_order(self._model, self._directory_id, self._view, force=force)
        if order is self._order:
            return

        self._order = order
        self._rows = ((-1,) if self._directory_id else ()) + order.ids
        if selected in self._rows:
            self._cursor = self._rows.index(selected)
        self._keep_visible()
        self._dirty = True

    def _navigate(self, node_id: int, *, select_id: int | None = None) -> None:
        node = self._model.nodes[node_id]
        if node.kind != 'dir':
            self._dialog = 'info'
            self._dialog_offset = 0
            self._dirty = True
            return

        self._history[self._directory_id] = NavigationPosition(self._selected_id(), self._offset)
        self._directory_id = node_id
        self._order = None
        self._rows = ta.cast('tuple[int, ...]', ())
        self._cursor = 0
        self._offset = 0
        self._view = dc.replace(self._view, query='')
        self._refresh_order(force=True)

        position = self._history.get(node_id)
        selected = select_id if select_id is not None else position.selected_id if position is not None else None
        if selected in self._rows:
            self._cursor = self._rows.index(selected)
            self._offset = position.offset if position is not None else 0
        elif node_id and len(self._rows) > 1:
            self._cursor = 1
        self._keep_visible()

    def _go_up(self) -> None:
        if self._directory_id:
            node_id = self._directory_id
            parent_id = self._model.nodes[node_id].parent_id
            if parent_id is not None:
                self._navigate(parent_id, select_id=node_id)

    def _enter(self) -> None:
        selected = self._selected_id()
        if selected == -1:
            self._go_up()
        elif selected is not None:
            self._navigate(selected)

    def _start_scan(self) -> None:
        self._model = TreeModel(self._path)
        self._worker = ScanWorker(self._path, options=self._scan_options)
        self._directory_id = 0
        self._cursor = 0
        self._offset = 0
        self._history.clear()
        self._cache.clear()
        self._paths.clear()
        self._path_characters = 0
        self._order = None
        self._rows = ()
        self._snapshot = False
        self._exported = False
        self._restart_pending = False
        self._worker.start()
        self._dirty = True

    def _request_rescan(self) -> None:
        if self._task is not None:
            self._set_message(f'Wait for {self._task.operation} to finish.')
        elif self._worker is not None and self._worker.is_alive():
            self._worker.cancel()
            self._restart_pending = True
            self._set_message('Stopping the old scan before restarting; q still exits immediately.')
        else:
            self._start_scan()

    def _start_export(self) -> None:
        if not self._options.export_path:
            self._set_message('Supply --export FILE to enable saving a snapshot with w.')
        elif not self._model.complete or self._model.cancelled:
            self._set_message('Wait for a complete scan before saving.')
        elif self._task is not None:
            self._set_message(f'Wait for {self._task.operation} to finish.')
        else:
            model = self._model
            options = self._scan_options
            path = self._options.export_path
            self._task = BackgroundTask('save', lambda: write_snapshot(path, model, options=options))
            self._task.start()
            self._exported = True
            self._set_message('Saving snapshot...')

    def _request_delete(self) -> None:
        selected = self._selected_id()
        if not self._options.allow_delete:
            self._set_message('Deletion is disabled. Start with --allow-delete to enable d.')
        elif self._snapshot:
            self._set_message('Rescan with r before deleting from a saved snapshot.')
        elif not self._model.complete or self._model.cancelled:
            self._set_message('Wait for a complete scan before deleting.')
        elif self._task is not None:
            self._set_message(f'Wait for {self._task.operation} to finish.')
        elif selected is None or selected < 1:
            self._set_message('Select a file or subdirectory.')
        else:
            node = self._model.nodes[selected]
            if node.skipped or node.error:
                self._set_message('Cannot delete an excluded, unreadable, or changed entry. Rescan first.')
                return

            self._delete_id = selected
            self._confirmation = ''
            self._dialog = 'delete'
            self._dialog_offset = 0
            self._dirty = True

    def _confirm_delete(self) -> None:
        if self._delete_id is None:
            return
        model = self._model
        node_id = self._delete_id
        self._task = BackgroundTask('delete', lambda: delete_entry(model, node_id))
        self._task.start()
        self._dialog = None
        self._delete_id = None
        self._set_message('Deleting; a fresh scan will follow.')

    def _poll(self) -> None:
        if self._worker is not None:
            deadline = time.monotonic() + 0.012
            for _ in range(16):
                events = self._worker.poll(max_batches=1)
                if not events:
                    break
                self._model.apply(events[0])
                self._dirty = True
                if time.monotonic() >= deadline:
                    break

        if self._task is not None:
            result = self._task.poll()
            if result is not None:
                self._task = None
                if result.error:
                    self._quit_after_task = False
                    if result.operation == 'load':
                        self._model.apply(FinishEvent(error=result.error))
                    elif result.operation == 'delete':
                        self._start_scan()
                    self._set_message(f'{result.operation} failed: {result.error}')
                elif result.operation == 'load':
                    self._model, self._scan_options = result.value
                    self._scan_options = dc.replace(self._scan_options, retain_identity=self._options.allow_delete)
                    self._path = self._model.root_path
                    self._cache.clear()
                    self._paths.clear()
                    self._path_characters = 0
                    self._order = None
                    self._set_message('Saved snapshot loaded; r performs a fresh scan.')
                elif result.operation == 'save':
                    self._set_message(f'Saved snapshot: {result.value}')
                elif result.operation == 'delete':
                    if not self._quit_after_task:
                        self._start_scan()
                        self._set_message('Deleted. Rescanning to update sizes and hard-link accounting.')
                if self._quit_after_task:
                    self._quit = True
                self._dirty = True

        if self._restart_pending and (self._worker is None or not self._worker.is_alive()):
            self._start_scan()

        if (
                self._options.export_path and
                not self._snapshot and
                not self._exported and
                self._model.complete and
                self._model.error is None and
                not self._model.cancelled and
                self._task is None
        ):
            self._start_export()

        self._refresh_order()

    def _format_node(self, node_id: int, width: int) -> str:
        node = self._model.nodes[node_id]
        parent = self._model.nodes[self._directory_id]
        size = node.apparent if self._view.apparent else node.allocated
        total = parent.apparent if self._view.apparent else parent.allocated
        fraction = min(1.0, size / total) if total else 0.0
        if node.error:
            flag = '!'
        elif node.skipped:
            flag = '-'
        elif node.duplicate:
            flag = 'H'
        elif not node.complete:
            flag = '~'
        else:
            flag = ' '

        suffix = '/' if node.kind == 'dir' else '@' if node.kind == 'link' else ''
        name = self._escape(node.name) + suffix
        size_text = format_size(size)
        if node.skipped:
            size_text = '--'
        count = f'{node.items:,}' if node.kind == 'dir' else ''
        if width >= 90:
            bar = '#' * round(fraction * 10)
            return f'{size_text:>10} {fraction:>6.1%} [{bar:<10}] {count:>9} {flag} {name}'
        if width >= 64:
            return f'{size_text:>10} {fraction:>6.1%} {count:>9} {flag} {name}'
        return f'{size_text:>10} {flag} {name}'

    def _make_info(self) -> list[str]:
        selected = self._selected_id()
        node_id = selected if selected is not None and selected >= 0 else self._directory_id
        node = self._model.nodes[node_id]
        lines = [
            'Entry details',
            '',
            f'Path: {self._escape(self._get_path(node_id))}',
            f'Type: {node.kind}',
            f'Allocated total: {node.allocated:,} bytes ({format_size(node.allocated)})',
            f'Apparent total:  {node.apparent:,} bytes ({format_size(node.apparent)})',
            f'Descendant entries: {node.items:,}',
            f'State: {"complete" if node.complete else "partial / still scanning"}',
        ]
        if node.duplicate:
            lines.extend((
                '',
                'This inode was already counted through another pathname.',
                'This name contributes zero bytes.',
                f'Its raw allocated size is {node.raw_allocated:,} bytes.',
                f'Its raw apparent size is {node.raw_apparent:,} bytes.',
            ))
        if node.skipped:
            lines.append(f'Skipped: {self._escape(node.skipped)}')
        if node.error:
            lines.append(f'Error: {self._escape(node.error)}')
        lines.extend(('', 'Directory totals include the directory itself.', 'Symlink targets are never traversed.'))
        return lines

    def _make_dialog(self) -> list[str]:
        if self._dialog == 'info':
            return self._make_info()
        if self._dialog == 'delete':
            path = self._get_path(self._delete_id) if self._delete_id is not None else ''
            return [
                'Delete permanently',
                '',
                self._escape(path),
                '',
                'Directories and their contents will be removed.',
                'Type DELETE and press Enter to confirm; Esc cancels.',
                '',
                f'Confirm: {self._confirmation}',
            ]
        return [
            'pyncdu controls',
            '',
            'Up / Down, j / k     Move selection',
            'Enter / Right / l    Open directory or entry details',
            'Left / Backspace / h Go to parent directory',
            'Home / g, End / G    First / last entry',
            'PgUp / PgDn          Move one page',
            '/                    Filter current directory by substring',
            'Esc                  Cancel input, close dialog, clear filter',
            '.                    Show / hide dotfiles (display only)',
            'a                    Allocated / apparent size',
            's                    Sort: size, name, descendant count',
            'n / c                Sort by name / descendant count',
            'S                    Reverse sort direction',
            't                    Toggle directories first',
            'i                    Entry details',
            'r                    Fresh scan of the original root',
            'x                    Stop scan and keep partial results',
            'w                    Save snapshot (requires --export FILE)',
            'd                    Delete selected entry (--allow-delete)',
            '? / F1               Help',
            'q / Ctrl-C           Quit',
            '',
            'Mouse: click selects; double-click opens; wheel scrolls.',
            'Right-click goes to parent; click column headers to sort.',
            '',
            'Markers: ~ partial, ! error, - excluded, H hard-link duplicate.',
            'Percentages use the current directory total, including hidden',
            'or filtered entries and directory metadata. Counts include',
            'descendant names, including hard-link duplicates.',
            '',
            'Everything shown comes from the in-memory scan cache.',
            'Use r to see filesystem changes. A saved snapshot is historical.',
            'Hard links are charged to the first encountered pathname unless',
            '--count-links is used. This can shift sizes between siblings.',
            '',
            'Use --ascii if your terminal mismeasures Unicode filenames.',
        ]

    def _draw(self) -> None:
        height, width = self._screen.getmaxyx()
        normal = self._painter.normal
        lines: list[tuple[str, int]] = [('', normal) for _ in range(height)]
        if height < 9 or width < 28:
            if height:
                lines[0] = ('pyncdu: enlarge terminal; q quits', self._painter.heading)
            self._painter.draw(lines)
            return

        directory = self._model.nodes[self._directory_id]
        root = self._model.nodes[0]
        total = directory.apparent if self._view.apparent else directory.allocated
        metric = 'apparent' if self._view.apparent else 'allocated'
        if self._snapshot:
            status = 'SNAPSHOT'
        elif self._model.cancelled:
            status = 'STOPPED'
        elif self._model.error:
            status = 'ERROR'
        elif self._model.complete:
            status = 'DONE'
        else:
            status = 'SCANNING'
        if self._task is not None:
            status = self._task.operation.upper()
        direction = 'reversed' if self._view.reverse else 'normal'
        flags = ' dirs-first' if self._view.directories_first else ''
        title = f' pyncdu  |  {status}  |  {metric}  |  sort: {self._view.sort} {direction}{flags}'
        lines[0] = (title, self._painter.heading)
        path = self._escape(self._get_path(self._directory_id))
        lines[1] = (' ' + clip_text(path, width - 3, from_left=True), normal)
        lines[2] = (
            (
                f' Total: {format_size(total)}  |  {directory.items:,} entries  |  '
                f'{len(self._order.ids) if self._order is not None else 0:,} shown  |  errors: {self._model.errors:,}'
            ),
            normal,
        )
        if width >= 90:
            heading = '      Size      % [relative  ]     Items   Name'
        elif width >= 64:
            heading = '      Size      %       Items   Name'
        else:
            heading = '      Size   Name'
        if self._view.query:
            heading += '  [filter: ' + self._escape(self._view.query) + ']'
        lines[3] = (heading, self._painter.muted)

        self._keep_visible()
        for relative in range(self._body_height()):
            index = self._offset + relative
            if index >= len(self._rows):
                break
            node_id = self._rows[index]
            if node_id == -1:
                text = '           .. (parent directory)'
                attribute = self._painter.directory
            else:
                node = self._model.nodes[node_id]
                text = self._format_node(node_id, width)
                if node.error:
                    attribute = self._painter.error
                elif node.kind == 'dir':
                    attribute = self._painter.directory
                else:
                    attribute = normal
            if index == self._cursor:
                attribute = self._painter.selected
            lines[4 + relative] = (text, attribute)

        if not self._rows:
            if self._view.query:
                text = ' No matching entries.'
            elif directory.complete:
                text = ' Empty directory.'
            else:
                text = ' Reading directory...'
            if directory.error:
                text = ' ' + self._escape(directory.error)
            elif directory.skipped:
                text = ' ' + self._escape(directory.skipped)
            lines[4] = (text, self._painter.muted)

        end = self._model.ended_at if self._model.ended_at is not None else time.monotonic()
        elapsed = max(0.0, end - self._model.started_at)
        rate = self._model.scanned_entries / elapsed if elapsed > 0 else 0.0
        scanned_total = root.apparent if self._view.apparent else root.allocated
        progress = f' Root: {format_size(scanned_total)}  |  {self._model.scanned_entries:,} entries  |  {elapsed:.1f}s'
        if not self._model.complete:
            progress += f'  |  {rate:,.0f}/s'
        if self._model.error:
            progress = ' ' + self._escape(self._model.error)
        elif self._restart_pending:
            progress = ' Waiting for the old scan to stop; q exits immediately.'
        lines[height - 3] = (progress, self._painter.error if self._model.error else self._painter.muted)

        selected = self._selected_id()
        if self._editing_filter:
            detail = ' /' + self._escape(self._view.query) + '_  [Enter accepts; Esc restores]'
        elif time.monotonic() < self._message_until:
            detail = ' ' + self._escape(self._message)
        elif selected is not None and selected >= 0:
            node = self._model.nodes[selected]
            detail = ' ' + self._escape(node.error or node.skipped or self._get_path(selected))
        else:
            detail = ' Browse while scanning. ~ means the total is still partial.'
        lines[height - 2] = (detail, normal)
        lines[height - 1] = (' q Quit  ? Help  Enter Open  a Size  s Sort  / Filter  r Rescan', self._painter.heading)

        if self._dialog is not None:
            dialog_lines = self._make_dialog()
            available = height - 2
            self._dialog_offset = max(0, min(self._dialog_offset, len(dialog_lines) - available))
            lines = [('', normal) for _ in range(height)]
            for row, text in enumerate(dialog_lines[self._dialog_offset:self._dialog_offset + available]):
                lines[row] = (' ' + text, self._painter.heading if row == 0 else normal)
            lines[height - 1] = (' Esc Close  Up/Down/PgUp/PgDn Scroll', self._painter.heading)

        self._painter.draw(lines)

    def _handle_filter(self, key: str | int) -> None:
        if key in ('\n', '\r', curses.KEY_ENTER):
            self._editing_filter = False
        elif key == '\x1b':
            self._view = dc.replace(self._view, query=self._filter_before)
            self._editing_filter = False
        elif key in ('\b', '\x7f', curses.KEY_BACKSPACE):
            self._view = dc.replace(self._view, query=self._view.query[:-1])
        elif key == '\x15':
            self._view = dc.replace(self._view, query='')
        elif isinstance(key, str) and key.isprintable():
            self._view = dc.replace(self._view, query=self._view.query + key)
        self._refresh_order(force=True)
        self._dirty = True

    def _handle_dialog(self, key: str | int) -> None:
        if key == '\x1b' or (self._dialog != 'delete' and key in ('q', '?', 'i', '\n', '\r')):
            self._dialog = None
        elif self._dialog == 'delete':
            if key in ('\n', '\r', curses.KEY_ENTER) and self._confirmation == 'DELETE':
                self._confirm_delete()
            elif key in ('\b', '\x7f', curses.KEY_BACKSPACE):
                self._confirmation = self._confirmation[:-1]
            elif isinstance(key, str) and key.isprintable() and len(self._confirmation) < 20:
                self._confirmation += key
        elif key in (curses.KEY_DOWN, 'j'):
            self._dialog_offset += 1
        elif key in (curses.KEY_UP, 'k'):
            self._dialog_offset = max(0, self._dialog_offset - 1)
        elif key == curses.KEY_NPAGE:
            self._dialog_offset += self._screen.getmaxyx()[0] - 3
        elif key == curses.KEY_PPAGE:
            self._dialog_offset = max(0, self._dialog_offset - self._screen.getmaxyx()[0] + 3)
        self._dirty = True

    def _handle_mouse(self) -> None:
        try:
            _, x, y, _, buttons = curses.getmouse()
        except curses.error:
            return

        up = getattr(curses, 'BUTTON4_PRESSED', 0)
        down = getattr(curses, 'BUTTON5_PRESSED', 0)
        if buttons & (up | down):
            amount = -3 if buttons & up else 3
            if self._dialog is not None:
                self._dialog_offset = max(0, self._dialog_offset + amount)
            else:
                self._cursor += amount
                self._keep_visible()
            self._dirty = True
            return

        if self._dialog is not None or self._editing_filter:
            return
        if buttons & (getattr(curses, 'BUTTON3_PRESSED', 0) | getattr(curses, 'BUTTON3_CLICKED', 0)):
            self._go_up()
            return

        pressed = getattr(curses, 'BUTTON1_PRESSED', 0) | getattr(curses, 'BUTTON1_CLICKED', 0)
        doubled = getattr(curses, 'BUTTON1_DOUBLE_CLICKED', 0)
        if not buttons & (pressed | doubled):
            return

        if y == 3:
            width = self._screen.getmaxyx()[1]
            if x < 18:
                sort = 'size'
            elif (width >= 90 and x < 42) or (64 <= width < 90 and x < 29):
                sort = 'items'
            else:
                sort = 'name'
            self._view = dc.replace(self._view, sort=sort)
            self._refresh_order(force=True)
            return

        index = self._offset + y - 4
        if not (4 <= y < 4 + self._body_height() and 0 <= index < len(self._rows)):
            return
        self._cursor = index
        now = time.monotonic()
        node_id = self._rows[index]
        previous = self._last_click
        double = bool(buttons & doubled) or (
            previous is not None and
            previous[0] == self._directory_id and
            previous[1] == node_id and
            now - previous[2] < 0.4
        )
        self._last_click = None if double else (self._directory_id, node_id, now)
        self._dirty = True
        if double:
            self._enter()

    def _handle_key(self, key: str | int) -> None:
        previous_view = self._view
        if key == '\x03':
            self._quit = True
        elif key == curses.KEY_RESIZE:
            self._painter.invalidate()
            self._dirty = True
        elif key == curses.KEY_MOUSE:
            self._handle_mouse()
        elif self._dialog is not None:
            self._handle_dialog(key)
        elif self._editing_filter:
            self._handle_filter(key)
        elif key in ('q', 'Q'):
            if self._task is not None and self._task.operation in ('save', 'delete'):
                self._quit_after_task = True
                self._set_message(f'Will quit when {self._task.operation} finishes.')
            else:
                self._quit = True
        elif key in (curses.KEY_DOWN, 'j'):
            self._cursor += 1
        elif key in (curses.KEY_UP, 'k'):
            self._cursor -= 1
        elif key in (curses.KEY_NPAGE, '\x06'):
            self._cursor += self._body_height()
        elif key in (curses.KEY_PPAGE, '\x02'):
            self._cursor -= self._body_height()
        elif key in (curses.KEY_HOME, 'g'):
            self._cursor = 0
        elif key in (curses.KEY_END, 'G'):
            self._cursor = len(self._rows) - 1
        elif key in ('\n', '\r', curses.KEY_ENTER, curses.KEY_RIGHT, 'l'):
            self._enter()
        elif key in (curses.KEY_LEFT, curses.KEY_BACKSPACE, '\x7f', '\b', 'h'):
            self._go_up()
        elif key == '/':
            self._filter_before = self._view.query
            self._editing_filter = True
        elif key == '\x1b':
            self._view = dc.replace(self._view, query='')
        elif key == '.':
            self._view = dc.replace(self._view, hide_hidden=not self._view.hide_hidden)
        elif key == 'a':
            self._view = dc.replace(self._view, apparent=not self._view.apparent)
        elif key == 's':
            modes = ('size', 'name', 'items')
            self._view = dc.replace(self._view, sort=modes[(modes.index(self._view.sort) + 1) % len(modes)])
        elif key in ('n', 'c'):
            self._view = dc.replace(self._view, sort='name' if key == 'n' else 'items')
        elif key == 'S':
            self._view = dc.replace(self._view, reverse=not self._view.reverse)
        elif key == 't':
            self._view = dc.replace(self._view, directories_first=not self._view.directories_first)
        elif key == 'i':
            self._dialog = 'info'
            self._dialog_offset = 0
        elif key in ('?', curses.KEY_F1):
            self._dialog = 'help'
            self._dialog_offset = 0
        elif key == 'r':
            self._request_rescan()
        elif key == 'x' and self._worker is not None and not self._model.complete:
            self._worker.cancel()
            self._set_message('Stopping scan; partial results remain browsable.')
        elif key == 'w':
            self._start_export()
        elif key == 'd':
            self._request_delete()
        elif key == '\x0c':
            self._screen.clearok(True)
            self._painter.invalidate()

        self._keep_visible()
        self._refresh_order(force=self._view != previous_view)
        self._dirty = True

    def run(self) -> None:
        self._screen.keypad(True)
        self._screen.timeout(40)

        try:
            curses.curs_set(0)
        except curses.error:
            pass

        try:
            curses.set_escdelay(25)
        except (AttributeError, curses.error):
            pass

        if not self._options.no_mouse:
            try:
                curses.mouseinterval(0)
                curses.mousemask(curses.ALL_MOUSE_EVENTS)
            except curses.error:
                pass

        if self._options.import_path is not None:
            path = self._options.import_path
            self._task = BackgroundTask('load', lambda: read_snapshot(path))
            self._task.start()
        else:
            self._start_scan()

        try:
            while not self._quit:
                self._poll()
                dimensions = self._screen.getmaxyx()
                if dimensions != self._last_dimensions:
                    self._last_dimensions = dimensions
                    self._dirty = True
                now = time.monotonic()
                if now - self._last_draw >= self._options.refresh_interval:
                    if self._dirty or not self._model.complete or self._message:
                        self._draw()
                        self._last_draw = now
                        self._dirty = False

                try:
                    key = self._screen.get_wch()
                except curses.error:
                    continue
                self._handle_key(key)
                self._draw()
                self._last_draw = time.monotonic()
                self._dirty = False

        finally:
            if self._worker is not None:
                self._worker.cancel()


##
# Entry point


def scan_tree(path: str, *, options: ScanOptions) -> TreeModel:
    model = TreeModel(path)
    worker = ScanWorker(path, options=options)
    worker.start()
    try:
        while not model.complete:
            events = worker.poll()
            for event in events:
                model.apply(event)
            if not events:
                worker.finished.wait(0.01)
        return model
    finally:
        worker.cancel()


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Browse disk usage while a background thread scans. Python standard library only.',
        epilog=(
            'Keys: arrows or hjkl, Enter, a size mode, s sort, / filter, r rescan, ? help, q quit. '
            'Mouse: click selects, double-click opens, wheel scrolls, right-click goes up. '
            'Symlinks are never followed, including the root argument. '
            'Snapshots are historical, not automatically validated against the filesystem.'
        ),
    )
    parser.add_argument(
        'path',
        nargs='?',
        help='directory or file to inspect (default: current directory)',
    )
    parser.add_argument(
        '-x',
        '--one-file-system',
        action='store_true',
        help='skip directories on other devices',
    )
    parser.add_argument(
        '-a',
        '--apparent-size',
        action='store_true',
        help='start with apparent size instead of allocated blocks',
    )
    parser.add_argument(
        '--count-links',
        action='store_true',
        help='charge every hard-link name instead of deduplicating inodes',
    )
    parser.add_argument(
        '--exclude',
        action='append',
        default=[],
        metavar='GLOB',
        help='skip matching basenames or relative paths; repeatable',
    )
    parser.add_argument(
        '--no-mouse',
        action='store_true',
        help='leave mouse input to the terminal',
    )
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='use monochrome attributes',
    )
    parser.add_argument(
        '--ascii',
        action='store_true',
        dest='ascii_only',
        help='escape non-ASCII filename characters',
    )
    parser.add_argument(
        '--allow-delete',
        action='store_true',
        help='enable d with a typed DELETE confirmation after scanning',
    )
    parser.add_argument(
        '--refresh-rate',
        type=float,
        default=10.0,
        metavar='FPS',
        help='maximum background redraw rate, 1-30 (default: 10)',
    )
    parser.add_argument(
        '--export',
        dest='export_path',
        metavar='FILE',
        help='atomically save a complete scan as a JSONL snapshot',
    )
    parser.add_argument(
        '--import',
        dest='import_path',
        metavar='FILE',
        help='browse an existing snapshot without scanning',
    )
    parser.add_argument(
        '--scan-only',
        action='store_true',
        help='scan without curses and print a JSON summary (useful with --export)',
    )
    return parser


def _main() -> None:
    parser = _make_parser()
    args = parser.parse_args()
    if not math.isfinite(args.refresh_rate) or not 1 <= args.refresh_rate <= 30:
        parser.error('--refresh-rate must be between 1 and 30')
    if args.import_path and args.path is not None:
        parser.error('a path and --import cannot be used together')
    if args.import_path and (args.one_file_system or args.count_links or args.exclude):
        parser.error('scan options are stored in the snapshot; omit -x, --count-links, and --exclude with --import')

    path = os.path.abspath(os.path.expanduser(args.path or '.'))
    scan_options = ScanOptions(
        one_file_system=args.one_file_system,
        count_links=args.count_links,
        exclude=tuple(args.exclude),
        retain_identity=args.allow_delete,
    )

    try:
        if args.scan_only:
            if args.import_path:
                model, scan_options = read_snapshot(args.import_path)
            else:
                model = scan_tree(path, options=scan_options)
            if args.export_path:
                write_snapshot(args.export_path, model, options=scan_options)
            root = model.nodes[0]
            print(json.dumps({
                'path': model.root_path,
                'allocated': root.allocated,
                'apparent': root.apparent,
                'entries': model.scanned_entries,
                'errors': model.errors,
                'error': model.error,
                'cancelled': model.cancelled,
                'snapshot': bool(args.import_path),
            }, ensure_ascii=True))
            if model.error is not None or model.errors or model.cancelled:
                raise SystemExit(1)
            return

        if curses is None:
            parser.error('this Python build does not include the standard-library curses module')
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            parser.error('the TUI needs a terminal; use --scan-only for redirected output')
        try:
            locale.setlocale(locale.LC_ALL, '')
        except locale.Error:
            pass

        ui_options = UiOptions(
            apparent=args.apparent_size,
            no_mouse=args.no_mouse,
            no_color=args.no_color,
            ascii_only=args.ascii_only,
            allow_delete=args.allow_delete,
            refresh_interval=1.0 / args.refresh_rate,
            export_path=args.export_path,
            import_path=args.import_path,
        )

        def run_ui(screen: ta.Any) -> None:
            DiskUsageUi(screen, path, scan_options=scan_options, ui_options=ui_options).run()

        curses.setupterm(fd=sys.stdout.fileno())
        curses.wrapper(run_ui)

    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except (OSError, SnapshotError, ValueError) as error:
        print(f'pyncdu: {escape_text(str(error), ascii_only=True)}', file=sys.stderr)
        raise SystemExit(1) from None
    except Exception as error:
        if curses is not None and isinstance(error, curses.error):
            print(f'pyncdu: terminal error: {error}', file=sys.stderr)
            raise SystemExit(1) from None
        raise


# @om-manifest omdev.cli.CliModule(['ncdu'], __name__)


if __name__ == '__main__':
    _main()
