# ruff: noqa: SLF001
import os
import shutil
import subprocess
import sys
import zipfile

from ..pycz import _MmapPyczArchive


##


def test_pycz_install_and_load(tmp_path):
    source_dir = tmp_path / 'source'
    package_dir = source_dir / 'fixturepkg'
    package_dir.mkdir(parents=True)
    (package_dir / '__init__.py').write_text('from .mod import VALUE\n')
    module_path = package_dir / 'mod.py'
    module_path.write_text('VALUE = 1\n')
    (package_dir / 'data.txt').write_text('resource data\n')

    site_dir = tmp_path / 'site-packages'
    env = dict(os.environ)
    env['PYTHONPATH'] = os.pathsep.join([str(source_dir), os.getcwd()])
    install = subprocess.run(
        [
            sys.executable,
            '-m',
            'x.pycz',
            'fixturepkg',
            '--site-dir',
            str(site_dir),
        ],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    assert 'Wrote 2 modules' in install.stdout
    assert (site_dir / 'fixturepkg.pycz').is_file()
    assert (site_dir / '_pycz.py').is_file()
    assert (site_dir / '___pycz-fixturepkg.pth').is_file()
    with zipfile.ZipFile(site_dir / 'fixturepkg.pycz') as zf:
        assert zf.namelist() == ['fixturepkg/__init__.pyc', 'fixturepkg/mod.pyc']

    archive = _MmapPyczArchive(str(site_dir / 'fixturepkg.pycz'))
    try:
        assert set(archive._central_entries) == {'fixturepkg/__init__.pyc', 'fixturepkg/mod.pyc'}
        assert archive._local_entries == {}
        assert archive.has('fixturepkg/mod.pyc')
        assert archive._local_entries == {}
        assert archive.read('fixturepkg/mod.pyc')
        assert set(archive._local_entries) == {'fixturepkg/mod.pyc'}
    finally:
        archive.close()

    module_path.write_text('VALUE = 2\n')
    shutil.rmtree(package_dir / '__pycache__')

    loaded = subprocess.run(
        [
            sys.executable,
            '-c',
            (
                'import importlib.resources, inspect, pkgutil, site; '
                f'site.addsitedir({str(site_dir)!r}); '
                'import fixturepkg.mod; '
                'print(fixturepkg.mod.VALUE); '
                'print(type(fixturepkg.mod.__loader__).__name__); '
                'print(inspect.getsource(fixturepkg.mod).strip()); '
                "print(importlib.resources.files(fixturepkg).joinpath('data.txt').read_text().strip()); "
                "print(pkgutil.get_data('fixturepkg', 'data.txt').decode().strip())"
            ),
        ],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    assert loaded.stdout.splitlines() == ['1', '_PyczLoader', 'VALUE = 2', 'resource data', 'resource data']
