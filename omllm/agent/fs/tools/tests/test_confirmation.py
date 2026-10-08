"""
Writes are asked for with the change in hand: the fs tools read what they are about to change - having been allowed to
read it - and ask to write with a preview of exactly what will be written, which the result then displays.
"""
import os.path

from omcore import lang

from .....core import ui
from ....permissions.types import PermissionDecider
from ....permissions.types import PermissionDeniedError
from ....permissions.types import PermissionState
from ....types.tools import ToolContext
from ....types.tools import ToolEnvironment
from ...ops import LocalFsOps
from ..details import WriteToolResultDetails
from ..edit import EditTool
from ..write import WriteTool


##


class _LoggingFsOps(LocalFsOps):
    def __init__(self, log):
        super().__init__()

        self._log = log

    async def read_file(self, path):
        self._log.append(('read', path))
        return await super().read_file(path)

    async def write_file(self, path, content, **kwargs):
        self._log.append(('write', path))
        return await super().write_file(path, content, **kwargs)


class _Decider(PermissionDecider):
    """Allows what it is not told to deny, recording each request - and running `on_write` while a write is asked."""

    def __init__(self, log, *, deny=(), on_write=None):
        super().__init__()

        self._log = log
        self._deny = deny
        self._on_write = on_write

        self.requests = []

    async def decide(self, request):
        mode = request.target.mode
        self._log.append(('ask', mode))
        self.requests.append(request)

        if mode == 'w' and self._on_write is not None:
            self._on_write()

        return PermissionState.DENY if mode in self._deny else PermissionState.ALLOW


def _write_local(path, data):
    with open(path, 'wb') as f:
        f.write(data)


def _read_local(path):
    with open(path, 'rb') as f:
        return f.read()


def _call(tool, cwd, args):
    return lang.sync_await(tool.execute_context(ToolContext(
        args=args,
        env=ToolEnvironment(cwd=cwd),
    )))


def _setup(tmp_path, **kwargs):
    root = os.path.realpath(tmp_path)
    log: list = []
    return root, log, _Decider(log, **kwargs), _LoggingFsOps(log)


##


def test_edit_reads_only_once_allowed_and_asks_to_write_with_the_diff(tmp_path):
    root, log, perms, fs = _setup(tmp_path)
    path = os.path.join(root, 'f.py')
    _write_local(path, b'a\nb\nc\n')

    result = _call(EditTool(permissions=perms, fs=fs), root, {
        'file_path': path,
        'old_string': 'b\n',
        'new_string': 'B\n',
    })
    assert result.error is None, result.content.text

    assert log == [('ask', 'r'), ('read', path), ('ask', 'w'), ('write', path)]

    read_request, write_request = perms.requests
    assert read_request.preview is None
    assert write_request.preview == ui.DiffText(old='a\nb\nc\n', new='a\nB\nc\n', path=path)

    # The result shows the user what was asked - the same change, now made.
    assert result.display is write_request.preview
    assert _read_local(path) == b'a\nB\nc\n'


def test_edit_refused_a_read_never_reads(tmp_path):
    root, log, perms, fs = _setup(tmp_path, deny=('r',))
    path = os.path.join(root, 'f.py')
    _write_local(path, b'a\n')

    result = _call(EditTool(permissions=perms, fs=fs), root, {
        'file_path': path,
        'old_string': 'a',
        'new_string': 'b',
    })

    assert isinstance(result.error, PermissionDeniedError)
    assert log == [('ask', 'r')]


def test_edit_refused_a_write_leaves_the_file_alone(tmp_path):
    root, log, perms, fs = _setup(tmp_path, deny=('w',))
    path = os.path.join(root, 'f.py')
    _write_local(path, b'a\n')

    result = _call(EditTool(permissions=perms, fs=fs), root, {
        'file_path': path,
        'old_string': 'a',
        'new_string': 'b',
    })

    assert isinstance(result.error, PermissionDeniedError)
    assert result.display is None
    assert perms.requests[-1].preview == ui.DiffText(old='a\n', new='b\n', path=path)
    assert ('write', path) not in log
    assert _read_local(path) == b'a\n'


def test_edit_fails_rather_than_clobber_a_file_changed_while_asking(tmp_path):
    root = os.path.realpath(tmp_path)
    path = os.path.join(root, 'f.py')
    _write_local(path, b'a\n')

    _, log, perms, fs = _setup(tmp_path, on_write=lambda: _write_local(path, b'meanwhile\n'))

    result = _call(EditTool(permissions=perms, fs=fs), root, {
        'file_path': path,
        'old_string': 'a',
        'new_string': 'b',
    })

    assert isinstance(result.error, ValueError)
    assert 'changed' in str(result.error)
    assert _read_local(path) == b'meanwhile\n'


##


def test_write_of_a_new_file_shows_it_all_added_without_reading(tmp_path):
    root, log, perms, fs = _setup(tmp_path)
    path = os.path.join(root, 'new.py')

    result = _call(WriteTool(permissions=perms, fs=fs), root, {
        'file_path': path,
        'contents': 'x\ny\n',
        'overwrite': True,
    })
    assert result.error is None, result.content.text

    assert log == [('ask', 'w'), ('write', path)]
    assert perms.requests[0].preview == ui.DiffText(old='', new='x\ny\n', path=path)
    assert result.display == perms.requests[0].preview
    assert isinstance(result.details, WriteToolResultDetails)
    assert result.details.created


def test_write_over_a_file_shows_the_diff_against_what_it_replaces(tmp_path):
    root, log, perms, fs = _setup(tmp_path)
    path = os.path.join(root, 'f.py')
    _write_local(path, b'old\n')

    result = _call(WriteTool(permissions=perms, fs=fs), root, {
        'file_path': path,
        'contents': 'new\n',
        'overwrite': True,
    })
    assert result.error is None, result.content.text

    assert log == [('ask', 'r'), ('read', path), ('ask', 'w'), ('write', path)]
    assert perms.requests[-1].preview == ui.DiffText(old='old\n', new='new\n', path=path)
    assert not result.details.created
    assert _read_local(path) == b'new\n'


def test_write_refuses_an_existing_file_without_overwrite_before_asking(tmp_path):
    root, log, perms, fs = _setup(tmp_path)
    path = os.path.join(root, 'f.py')
    _write_local(path, b'old\n')

    result = _call(WriteTool(permissions=perms, fs=fs), root, {
        'file_path': path,
        'contents': 'new\n',
    })

    assert isinstance(result.error, ValueError)
    assert str(result.error) == 'Path already exists'
    assert log == []


def test_write_fails_rather_than_clobber_a_file_created_while_asking(tmp_path):
    root = os.path.realpath(tmp_path)
    path = os.path.join(root, 'f.py')

    _, log, perms, fs = _setup(tmp_path, on_write=lambda: _write_local(path, b'meanwhile\n'))

    result = _call(WriteTool(permissions=perms, fs=fs), root, {
        'file_path': path,
        'contents': 'new\n',
        'overwrite': True,
    })

    # It was shown as a new file, so it is only ever written as one.
    assert isinstance(result.error, ValueError)
    assert _read_local(path) == b'meanwhile\n'


def test_write_over_non_text_says_so_rather_than_diffing(tmp_path):
    root, log, perms, fs = _setup(tmp_path)
    path = os.path.join(root, 'f.bin')
    _write_local(path, b'\xff\xfe')

    result = _call(WriteTool(permissions=perms, fs=fs), root, {
        'file_path': path,
        'contents': 'text\n',
        'overwrite': True,
    })
    assert result.error is None, result.content.text

    preview = perms.requests[-1].preview
    assert not isinstance(preview, ui.DiffText)
    assert '2 bytes of non-text content' in str(preview)
    assert result.display == preview
