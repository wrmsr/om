import os.path
import subprocess
import sys

from omcore.os.temp import temp_dir_context

from ..lite import LiteSourceMirror


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


def test_lite_source_mirror_nested_root():
    with temp_dir_context() as src_dir, temp_dir_context() as dst_dir:
        _build_src_tree(src_dir)

        mirror = LiteSourceMirror(
            ['root/pkg'],
            LITE_FILES,
            src_dir=src_dir,
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
