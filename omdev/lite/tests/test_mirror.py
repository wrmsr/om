import os.path
import subprocess
import sys

import pytest

from omcore.os.temp import temp_dir_context

from ..mirror import LiteSourceMirror


NON_LITE_SRC = "raise RuntimeError('non-lite code executed')\n"

LITE_FILES = frozenset([
    'root/pkg/litemod.py',
    'root/pkg/litepkg/__init__.py',
])


def _write(fp, src=''):
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'w') as f:
        f.write(src)


def _build_src_tree(src_dir):
    def j(*ps):
        return os.path.join(src_dir, *ps)

    # A root with lite files somewhere beneath it.
    _write(j('root', '__init__.py'), NON_LITE_SRC)

    # A package with no lite files at all.
    _write(j('root', 'plain', '__init__.py'), NON_LITE_SRC)
    _write(j('root', 'plain', 'a.py'))

    # A non-lite package containing lite files.
    _write(j('root', 'pkg', '__init__.py'), NON_LITE_SRC)
    _write(j('root', 'pkg', 'litemod.py'), '# @om-lite\nLITEMOD = 1\n')
    _write(j('root', 'pkg', 'other.py'), NON_LITE_SRC)
    _write(j('root', 'pkg', '__pycache__', 'junk.pyc'))

    # A lite package, whose __init__ is itself lite and has content lite code relies on.
    _write(j('root', 'pkg', 'litepkg', '__init__.py'), '# @om-lite\nLITEPKG = 1\n')
    _write(j('root', 'pkg', 'litepkg', 'x.py'), 'from . import LITEPKG  # noqa\n')

    # A non-lite package with no lite files, nested inside a materialized one.
    _write(j('root', 'pkg', 'deep', '__init__.py'), NON_LITE_SRC)
    _write(j('root', 'pkg', 'deep', 'b.py'))

    # A root with no lite files at all.
    _write(j('other', '__init__.py'), NON_LITE_SRC)


def test_lite_source_mirror():
    with temp_dir_context() as src_dir, temp_dir_context() as dst_dir:
        _build_src_tree(src_dir)

        mirror = LiteSourceMirror(
            ['root', 'other'],
            LITE_FILES,
            src_dir=src_dir,
        )

        assert set(mirror.lite_package_dirs) == {'root/pkg/litepkg'}
        assert set(mirror.materialized_dirs) == {'root', 'root/pkg'}

        mirror.build(dst_dir)

        def s(*ps):
            return os.path.join(src_dir, *ps)

        def d(*ps):
            return os.path.join(dst_dir, *ps)

        def is_empty_file(fp):
            return os.path.isfile(fp) and not os.path.islink(fp) and not os.path.getsize(fp)

        def is_real_dir(fp):
            return os.path.isdir(fp) and not os.path.islink(fp)

        def is_link_to(fp, tgt):
            return os.path.islink(fp) and os.readlink(fp) == tgt

        # Roots without lite files are symlinked wholesale.
        assert is_link_to(d('other'), s('other'))

        # Materialized dirs get an empty __init__ and symlinked entries.
        assert is_real_dir(d('root'))
        assert is_empty_file(d('root', '__init__.py'))
        assert is_link_to(d('root', 'plain'), s('root', 'plain'))

        assert is_real_dir(d('root', 'pkg'))
        assert is_empty_file(d('root', 'pkg', '__init__.py'))
        assert is_link_to(d('root', 'pkg', 'litemod.py'), s('root', 'pkg', 'litemod.py'))
        assert is_link_to(d('root', 'pkg', 'other.py'), s('root', 'pkg', 'other.py'))
        assert not os.path.lexists(d('root', 'pkg', '__pycache__'))

        # Lite packages and lite-free dirs beneath a materialized dir are symlinked wholesale.
        assert is_link_to(d('root', 'pkg', 'litepkg'), s('root', 'pkg', 'litepkg'))
        assert is_link_to(d('root', 'pkg', 'deep'), s('root', 'pkg', 'deep'))

        # Lite modules import through the mirror without executing the non-lite inits above them.
        for mod in [
            'root.pkg.litemod',
            'root.pkg.litepkg',
            'root.pkg.litepkg.x',
        ]:
            subprocess.run(
                [sys.executable, '-B', '-c', f'import {mod}'],
                cwd=dst_dir,
                check=True,
            )

        # Non-lite modules still execute for real, so a lite module depending on one would still fail.
        proc = subprocess.run(
            [sys.executable, '-B', '-c', 'import root.pkg.other'],
            cwd=dst_dir,
            capture_output=True,
            check=False,
        )
        assert proc.returncode != 0
        assert b'non-lite code executed' in proc.stderr


@pytest.mark.parametrize('lite_only', [False, True])
def test_lite_source_mirror_nested_root(lite_only):
    with temp_dir_context() as src_dir, temp_dir_context() as dst_dir:
        _build_src_tree(src_dir)

        mirror = LiteSourceMirror(
            ['root/pkg'],
            LITE_FILES,
            src_dir=src_dir,
            lite_only=lite_only,
        )

        mirror.build(dst_dir)

        def d(*ps):
            return os.path.join(dst_dir, *ps)

        assert os.path.isdir(d('root')) and not os.path.islink(d('root'))
        assert os.path.isfile(d('root', '__init__.py')) and not os.path.getsize(d('root', '__init__.py'))
        assert not os.path.lexists(d('root', 'plain'))
        assert os.path.isdir(d('root', 'pkg')) and not os.path.islink(d('root', 'pkg'))
        assert os.path.islink(d('root', 'pkg', 'litemod.py'))

        subprocess.run(
            [sys.executable, '-B', '-c', 'import root.pkg.litemod'],
            cwd=dst_dir,
            check=True,
        )


def test_lite_source_mirror_lite_only():
    with temp_dir_context() as src_dir, temp_dir_context() as dst_dir:
        _build_src_tree(src_dir)

        test_src = (
            'import unittest\n'
            'class TestLite(unittest.TestCase):\n'
            '    def test_lite(self):\n'
            '        assert True\n'
        )
        _write(os.path.join(src_dir, 'root/pkg/test_lite.py'), '# @om-lite\n' + test_src)
        _write(os.path.join(src_dir, 'root/pkg/litepkg/test_inherited.py'), test_src)
        _write(os.path.join(src_dir, 'root/pkg/litepkg/data.txt'), 'lite package resource\n')
        _write(os.path.join(src_dir, 'root/pkg/data.txt'), 'non-lite resource\n')
        for rel in ['root/test_nonlite.py', 'root/pkg/test_nonlite.py', 'root/plain/test_nonlite.py']:
            _write(os.path.join(src_dir, rel), NON_LITE_SRC)

        LiteSourceMirror(
            ['root', 'other'],
            [*LITE_FILES, 'root/pkg/test_lite.py'],
            src_dir=src_dir,
            lite_only=True,
        ).build(dst_dir)

        def d(rel):
            return os.path.join(dst_dir, rel)

        assert set(os.listdir(dst_dir)) == {'root'}
        assert set(os.listdir(d('root'))) == {'__init__.py', 'pkg'}
        assert set(os.listdir(d('root/pkg'))) == {'__init__.py', 'litemod.py', 'test_lite.py', 'litepkg'}
        for rel in ['root/__init__.py', 'root/pkg/__init__.py']:
            assert not os.path.islink(d(rel))
            assert os.path.getsize(d(rel)) == 0
        for rel in ['root/pkg/litemod.py', 'root/pkg/test_lite.py', 'root/pkg/litepkg']:
            assert os.path.islink(d(rel))
            assert os.readlink(d(rel)) == os.path.join(src_dir, rel)
        with open(d('root/pkg/litepkg/data.txt')) as f:
            assert f.read() == 'lite package resource\n'

        proc = subprocess.run(
            [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'root', '-t', '.', '-v'],
            cwd=dst_dir,
            capture_output=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr.decode()
        assert b'Ran 2 tests' in proc.stderr
        assert b'root.pkg.test_lite' in proc.stderr
        assert b'root.pkg.litepkg.test_inherited' in proc.stderr


@pytest.mark.parametrize('discover', [False, True])
@pytest.mark.parametrize('lite_only', [False, True])
def test_lite_source_mirror_cli(discover, lite_only):
    with temp_dir_context() as src_dir, temp_dir_context() as dst_dir:
        _build_src_tree(src_dir)
        _write(os.path.join(src_dir, 'root/pkg/explicit.py'), 'EXPLICIT = 1\n')
        repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
        env = dict(os.environ, PYTHONPATH=os.pathsep.join([repo_dir, os.environ.get('PYTHONPATH', '')]))
        args = [sys.executable, '-B', '-m', 'omdev.lite.mirror']
        if discover:
            args.append('--discover')
        else:
            for fp in sorted([*LITE_FILES, 'root/pkg/explicit.py']):
                args.extend(['--lite-file', fp])
        if lite_only:
            args.append('--lite-only')
        args.extend([dst_dir, 'root', 'other'])

        proc = subprocess.run(args, cwd=src_dir, env=env, capture_output=True, check=False)
        assert proc.returncode == 0, proc.stderr.decode()

        for rel in ['root/pkg/litemod.py', 'root/pkg/litepkg']:
            dst = os.path.join(dst_dir, rel)
            assert os.path.islink(dst)
            assert os.readlink(dst) == os.path.join(src_dir, rel)
        assert os.path.lexists(os.path.join(dst_dir, 'root/pkg/explicit.py')) == (not discover or not lite_only)
        for rel in ['root/plain', 'root/pkg/other.py', 'root/pkg/deep', 'other']:
            assert os.path.lexists(os.path.join(dst_dir, rel)) == (not lite_only)
        for rel in ['root/__init__.py', 'root/pkg/__init__.py']:
            dst = os.path.join(dst_dir, rel)
            assert not os.path.islink(dst)
            assert os.path.getsize(dst) == 0
