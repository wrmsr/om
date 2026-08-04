import os
import os.path
import subprocess

import pytest

from omcore.subprocesses.wrap import subprocess_maybe_shell_wrap_exec

from ..aborting import GitVendorAborter
from ..diffing import GitVendorDiffer
from ..errors import GitVendorDirtyError
from ..errors import GitVendorNoMergeInProgressError
from ..journals import GitVendorFileDisposition as D  # noqa
from ..pulling import GitVendorPuller
from ..specs import GitVendorSpec
from ..specs import load_vendor_spec
from ..specs import save_vendor_spec


##


A_BASE = (
    'int a(void) {\n'
    '    return 1;\n'
    '}\n'
    '\n'
    'int pad1(void) { return 0; }\n'
    'int pad2(void) { return 0; }\n'
    'int pad3(void) { return 0; }\n'
    'int pad4(void) { return 0; }\n'
    'int pad5(void) { return 0; }\n'
    'int pad6(void) { return 0; }\n'
    '\n'
    'int z(void) {\n'
    '    return 26;\n'
    '}\n'
)

A_UPSTREAM_V2 = A_BASE.replace('return 26;', 'return 260;')
A_UPSTREAM_V3 = A_UPSTREAM_V2.replace('return 1;', 'return 3;')

B_BASE = '#define B 1\n'

VENDOR_DIR = 'vnd/x'

SPEC_FILES = [
    'LICENSE',
    'a.c',
    'b.h',
    'new.c',
    'sub/util.h',
]


def _run(cwd, *cmd, check=True, input=None):  # noqa
    proc = subprocess.run(  # noqa
        subprocess_maybe_shell_wrap_exec(*cmd),
        cwd=cwd,
        input=input,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )
    return proc


def _git(cwd, *args, **kwargs):
    return _run(cwd, 'git', *args, **kwargs).stdout.decode()


def _write(dir, name, content):  # noqa
    path = os.path.join(dir, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)


def _read(dir, name):  # noqa
    with open(os.path.join(dir, name)) as f:
        return f.read()


def _init_repo(dir):  # noqa
    os.makedirs(dir, exist_ok=True)
    _git(dir, 'init', '-q')
    _git(dir, 'config', 'user.email', 'you@example.com')
    _git(dir, 'config', 'user.name', 'Your Name')


def _make_upstream(dir):  # noqa
    _init_repo(dir)

    _write(dir, 'a.c', A_BASE)
    _write(dir, 'b.h', B_BASE)
    _write(dir, 'LICENSE', 'MIT or whatever\n')
    _write(dir, 'sub/util.h', '#define U 1\n')
    _git(dir, 'add', '-A')
    _git(dir, 'commit', '-q', '-m', 'v1')
    _git(dir, 'tag', 'v1')

    _write(dir, 'a.c', A_UPSTREAM_V2)
    _git(dir, 'rm', '-q', 'b.h')
    _write(dir, 'new.c', 'int n;\n')
    _git(dir, 'add', '-A')
    _git(dir, 'commit', '-q', '-m', 'v2')
    _git(dir, 'tag', 'v2')

    _write(dir, 'a.c', A_UPSTREAM_V3)
    _git(dir, 'add', '-A')
    _git(dir, 'commit', '-q', '-m', 'v3')
    _git(dir, 'tag', 'v3')

    return dir


def _make_mono(dir, upstream):  # noqa
    _init_repo(dir)

    _write(dir, 'other.txt', 'hello\n')
    vendor_abs = os.path.join(dir, VENDOR_DIR)
    os.makedirs(vendor_abs)
    save_vendor_spec(vendor_abs, GitVendorSpec(url=upstream, files=SPEC_FILES))
    _git(dir, 'add', '-A')
    _git(dir, 'commit', '-q', '-m', 'init')

    return dir


def _setup(tmp_path):
    upstream = _make_upstream(str(tmp_path / 'upstream'))
    mono = _make_mono(str(tmp_path / 'mono'), upstream)

    journal = GitVendorPuller(mono, VENDOR_DIR, rev='v1', from_path=upstream).pull()
    _git(mono, 'commit', '-q', '-m', 'vendor v1')

    return upstream, mono, journal


def _dispositions(journal):
    return {e.path: e.disposition for e in journal.entries}


def _unmerged_paths(mono):
    return sorted({l.split('\t')[1] for l in _git(mono, 'ls-files', '-u').splitlines()})


##


def test_initial_pull(tmp_path):
    upstream, mono, journal = _setup(tmp_path)

    assert _dispositions(journal) == {
        'LICENSE': D.ADDED,
        'a.c': D.ADDED,
        'b.h': D.ADDED,
        'new.c': D.UNCHANGED,  # does not exist at v1
        'sub/util.h': D.ADDED,
    }

    assert _read(mono, f'{VENDOR_DIR}/a.c') == A_BASE
    assert _read(mono, f'{VENDOR_DIR}/sub/util.h') == '#define U 1\n'
    assert _git(mono, 'status', '--porcelain') == ''

    spec = load_vendor_spec(os.path.join(mono, VENDOR_DIR))
    assert spec.rev == _git(upstream, 'rev-parse', 'v1^{commit}').strip()
    assert spec.ref == 'v1'


def test_initial_pull_via_clone(tmp_path):
    upstream = _make_upstream(str(tmp_path / 'upstream'))
    mono = _make_mono(str(tmp_path / 'mono'), upstream)

    journal = GitVendorPuller(mono, VENDOR_DIR, rev='v1').pull()  # no from_path - clones the url

    assert _dispositions(journal)['a.c'] == D.ADDED
    assert _read(mono, f'{VENDOR_DIR}/a.c') == A_BASE


def test_clean_update(tmp_path):
    upstream, mono, _ = _setup(tmp_path)

    journal = GitVendorPuller(mono, VENDOR_DIR, rev='v2', from_path=upstream).pull()

    assert _dispositions(journal) == {
        'LICENSE': D.UNCHANGED,
        'a.c': D.FAST_FORWARDED,
        'b.h': D.DELETED,
        'new.c': D.ADDED,
        'sub/util.h': D.UNCHANGED,
    }

    _git(mono, 'commit', '-q', '-m', 'vendor v2')

    assert _read(mono, f'{VENDOR_DIR}/a.c') == A_UPSTREAM_V2
    assert not os.path.exists(os.path.join(mono, VENDOR_DIR, 'b.h'))
    assert _read(mono, f'{VENDOR_DIR}/new.c') == 'int n;\n'
    assert _git(mono, 'status', '--porcelain') == ''


def test_noop_pull(tmp_path):
    upstream, mono, _ = _setup(tmp_path)

    journal = GitVendorPuller(mono, VENDOR_DIR, rev='v1', from_path=upstream).pull()

    assert all(d is D.UNCHANGED for d in _dispositions(journal).values())
    assert _git(mono, 'status', '--porcelain') == ''

    # No journal was persisted - a subsequent pull needs no cleanup.
    with pytest.raises(GitVendorNoMergeInProgressError):
        GitVendorAborter(mono, VENDOR_DIR).abort()


def test_auto_merge(tmp_path):
    upstream, mono, _ = _setup(tmp_path)

    _write(mono, f'{VENDOR_DIR}/a.c', A_BASE.replace('return 1;', 'return 100;'))
    _git(mono, 'commit', '-q', '-a', '-m', 'local patch')

    journal = GitVendorPuller(mono, VENDOR_DIR, rev='v2', from_path=upstream).pull()

    assert _dispositions(journal)['a.c'] == D.AUTO_MERGED
    assert _read(mono, f'{VENDOR_DIR}/a.c') == A_UPSTREAM_V2.replace('return 1;', 'return 100;')
    assert _unmerged_paths(mono) == []

    _git(mono, 'commit', '-q', '-m', 'vendor v2')
    assert _git(mono, 'status', '--porcelain') == ''


def test_conflict_and_resolve(tmp_path):
    upstream, mono, _ = _setup(tmp_path)

    _write(mono, f'{VENDOR_DIR}/a.c', A_BASE.replace('return 1;', 'return 100;'))
    _git(mono, 'commit', '-q', '-a', '-m', 'local patch')

    journal = GitVendorPuller(mono, VENDOR_DIR, rev='v3', from_path=upstream).pull()

    assert _dispositions(journal)['a.c'] == D.CONFLICTED
    assert _unmerged_paths(mono) == [f'{VENDOR_DIR}/a.c']
    assert len(_git(mono, 'ls-files', '-u').splitlines()) == 3

    content = _read(mono, f'{VENDOR_DIR}/a.c')
    assert '<<<<<<<' in content
    assert 'return 100;' in content
    assert 'return 3;' in content

    # Committing is blocked while unresolved. (Note `commit -a` would NOT be blocked - like `git add`, it stages the
    # marker-bearing worktree content as the resolution - exactly as in a real git merge.)
    assert _run(mono, 'git', 'commit', '-m', 'nope', check=False).returncode != 0

    _write(mono, f'{VENDOR_DIR}/a.c', A_UPSTREAM_V3.replace('return 3;', 'return 300;'))
    _git(mono, 'add', f'{VENDOR_DIR}/a.c')
    assert _unmerged_paths(mono) == []
    _git(mono, 'commit', '-q', '-m', 'vendor v3 resolved')

    # The consumed journal is not cleaned up by resolution - the next pull detects it as stale and proceeds.
    journal = GitVendorPuller(mono, VENDOR_DIR, rev='v3', from_path=upstream).pull()
    assert all(d in (D.UNCHANGED, D.LOCAL_ONLY) for d in _dispositions(journal).values())


def test_delete_conflict(tmp_path):
    upstream, mono, _ = _setup(tmp_path)

    _write(mono, f'{VENDOR_DIR}/b.h', '#define B 2\n')
    _git(mono, 'commit', '-q', '-a', '-m', 'local b patch')

    journal = GitVendorPuller(mono, VENDOR_DIR, rev='v2', from_path=upstream).pull()

    assert _dispositions(journal)['b.h'] == D.DELETE_CONFLICTED
    assert _unmerged_paths(mono) == [f'{VENDOR_DIR}/b.h']
    assert len(_git(mono, 'ls-files', '-u').splitlines()) == 2  # stages 1 and 2 - 'deleted by them'
    assert _read(mono, f'{VENDOR_DIR}/b.h') == '#define B 2\n'

    _git(mono, 'rm', '-q', '-f', f'{VENDOR_DIR}/b.h')
    _git(mono, 'commit', '-q', '-m', 'vendor v2 resolved')
    assert _git(mono, 'status', '--porcelain') == ''


def test_abort(tmp_path):
    upstream, mono, _ = _setup(tmp_path)

    _write(mono, f'{VENDOR_DIR}/a.c', A_BASE.replace('return 1;', 'return 100;'))
    _git(mono, 'commit', '-q', '-a', '-m', 'local patch')
    pre_spec = _read(mono, f'{VENDOR_DIR}/.om-vendor.json')

    GitVendorPuller(mono, VENDOR_DIR, rev='v3', from_path=upstream).pull()
    assert _unmerged_paths(mono) != []

    # The user forgets the merge is in progress and edits other stuff.
    _write(mono, 'other.txt', 'edited while merging\n')
    _write(mono, 'scratch.txt', 'untracked scratch\n')
    # And leaves a mergetool-style backup file in the vendor dir.
    _write(mono, f'{VENDOR_DIR}/a.c.orig', 'backup\n')

    GitVendorAborter(mono, VENDOR_DIR).abort()

    # The vendor dir is fully restored...
    assert _read(mono, f'{VENDOR_DIR}/a.c') == A_BASE.replace('return 1;', 'return 100;')
    assert _read(mono, f'{VENDOR_DIR}/b.h') == B_BASE
    assert not os.path.exists(os.path.join(mono, VENDOR_DIR, 'new.c'))
    assert not os.path.exists(os.path.join(mono, VENDOR_DIR, 'a.c.orig'))
    assert _read(mono, f'{VENDOR_DIR}/.om-vendor.json') == pre_spec
    assert _unmerged_paths(mono) == []

    # ...while edits elsewhere survive.
    assert _read(mono, 'other.txt') == 'edited while merging\n'
    assert _read(mono, 'scratch.txt') == 'untracked scratch\n'

    st = sorted(l[3:] for l in _git(mono, 'status', '--porcelain').splitlines())
    assert st == ['other.txt', 'scratch.txt']

    with pytest.raises(GitVendorNoMergeInProgressError):
        GitVendorAborter(mono, VENDOR_DIR).abort()


def test_abort_after_commit(tmp_path):
    upstream, mono, _ = _setup(tmp_path)

    GitVendorPuller(mono, VENDOR_DIR, rev='v2', from_path=upstream).pull()
    _git(mono, 'commit', '-q', '-m', 'vendor v2')

    # A committed pull is no longer in progress - its journal is stale, not abortable.
    with pytest.raises(GitVendorNoMergeInProgressError):
        GitVendorAborter(mono, VENDOR_DIR).abort()

    assert _read(mono, f'{VENDOR_DIR}/a.c') == A_UPSTREAM_V2


def test_dirty_gate(tmp_path):
    upstream, mono, _ = _setup(tmp_path)

    _write(mono, f'{VENDOR_DIR}/a.c', 'dirty\n')
    with pytest.raises(GitVendorDirtyError):
        GitVendorPuller(mono, VENDOR_DIR, rev='v2', from_path=upstream).pull()

    _git(mono, 'checkout', '--', f'{VENDOR_DIR}/a.c')
    _write(mono, 'other.txt', 'dirty\n')
    with pytest.raises(GitVendorDirtyError):
        GitVendorPuller(mono, VENDOR_DIR, rev='v2', from_path=upstream).pull()

    # Untracked files outside the vendor dir don't block.
    _git(mono, 'checkout', '--', 'other.txt')
    _write(mono, 'scratch.txt', 'untracked\n')
    journal = GitVendorPuller(mono, VENDOR_DIR, rev='v2', from_path=upstream).pull()
    assert _dispositions(journal)['a.c'] == D.FAST_FORWARDED


def test_diff(tmp_path):
    upstream, mono, _ = _setup(tmp_path)

    _write(mono, f'{VENDOR_DIR}/a.c', A_BASE.replace('return 1;', 'return 100;'))
    _git(mono, 'commit', '-q', '-a', '-m', 'local patch')

    out = GitVendorDiffer(mono, VENDOR_DIR, from_path=upstream).diff()

    assert '--- a/a.c' in out
    assert '+++ b/a.c' in out
    assert '-    return 1;' in out
    assert '+    return 100;' in out
    assert 'b.h' not in out
