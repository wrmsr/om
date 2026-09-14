"""Load a source package's compiled modules from an in-memory pyc zip."""


##


class _PyczError(ImportError):
    pass


class _PyczArchive:
    def __init__(self, path: str) -> None:
        super().__init__()

        self._path = path
        with open(path, 'rb') as f:
            self._data = f.read()
        self._entries = self._parse_entries(self._data)

    @staticmethod
    def _uint(data: bytes, offset: int, size: int) -> int:
        end = offset + size
        if end > len(data):
            raise _PyczError('Truncated pycz archive')
        return int.from_bytes(data[offset:end], 'little')

    @classmethod
    def _parse_entries(cls, data: bytes) -> dict[str, tuple[int, int]]:
        eocd_offset = data.rfind(b'PK\x05\x06', max(0, len(data) - (65535 + 22)))
        if eocd_offset < 0 or eocd_offset + 22 > len(data):
            raise _PyczError('Invalid pycz end record')

        disk_number = cls._uint(data, eocd_offset + 4, 2)
        central_disk_number = cls._uint(data, eocd_offset + 6, 2)
        disk_entry_count = cls._uint(data, eocd_offset + 8, 2)
        entry_count = cls._uint(data, eocd_offset + 10, 2)
        central_size = cls._uint(data, eocd_offset + 12, 4)
        central_offset = cls._uint(data, eocd_offset + 16, 4)
        comment_size = cls._uint(data, eocd_offset + 20, 2)

        if (
                disk_number or
                central_disk_number or
                disk_entry_count != entry_count or
                entry_count == 0xffff or
                central_size == 0xffffffff or
                central_offset == 0xffffffff
        ):
            raise _PyczError('Unsupported multi-disk or ZIP64 pycz archive')
        if eocd_offset + 22 + comment_size != len(data):
            raise _PyczError('Invalid pycz archive comment')
        if central_offset + central_size != eocd_offset:
            raise _PyczError('Invalid pycz central directory')

        entries: dict[str, tuple[int, int]] = {}
        offset = central_offset
        for _ in range(entry_count):
            if data[offset:offset + 4] != b'PK\x01\x02' or offset + 46 > eocd_offset:
                raise _PyczError('Invalid pycz central directory entry')

            flags = cls._uint(data, offset + 8, 2)
            compression = cls._uint(data, offset + 10, 2)
            compressed_size = cls._uint(data, offset + 20, 4)
            uncompressed_size = cls._uint(data, offset + 24, 4)
            name_size = cls._uint(data, offset + 28, 2)
            extra_size = cls._uint(data, offset + 30, 2)
            entry_comment_size = cls._uint(data, offset + 32, 2)
            entry_disk_number = cls._uint(data, offset + 34, 2)
            local_offset = cls._uint(data, offset + 42, 4)
            entry_end = offset + 46 + name_size + extra_size + entry_comment_size
            if entry_end > eocd_offset:
                raise _PyczError('Truncated pycz central directory entry')
            if flags & 1 or compression != 0 or compressed_size != uncompressed_size or entry_disk_number:
                raise _PyczError('Pycz entries must be unencrypted, uncompressed, and on one disk')

            name_data = data[offset + 46:offset + 46 + name_size]
            name = name_data.decode('utf-8' if flags & 0x800 else 'cp437')
            if name in entries:
                raise _PyczError(f'Duplicate pycz entry: {name!r}')

            if data[local_offset:local_offset + 4] != b'PK\x03\x04' or local_offset + 30 > central_offset:
                raise _PyczError(f'Invalid local pycz entry: {name!r}')
            local_flags = cls._uint(data, local_offset + 6, 2)
            local_compression = cls._uint(data, local_offset + 8, 2)
            local_name_size = cls._uint(data, local_offset + 26, 2)
            local_extra_size = cls._uint(data, local_offset + 28, 2)
            local_name = data[local_offset + 30:local_offset + 30 + local_name_size]
            data_offset = local_offset + 30 + local_name_size + local_extra_size
            if local_flags != flags or local_compression != compression or local_name != name_data:
                raise _PyczError(f'Mismatched local pycz entry: {name!r}')
            if data_offset + uncompressed_size > central_offset:
                raise _PyczError(f'Truncated local pycz entry: {name!r}')

            entries[name] = (data_offset, uncompressed_size)
            offset = entry_end

        if offset != eocd_offset:
            raise _PyczError('Invalid pycz central directory size')
        return entries

    @property
    def path(self) -> str:
        return self._path

    def has(self, name: str) -> bool:
        return name in self._entries

    def read(self, name: str) -> bytes:
        try:
            offset, size = self._entries[name]
        except KeyError:
            raise ImportError(f'Pycz entry not found: {name!r}') from None
        return self._data[offset:offset + size]


class _PyczLoader:
    def __init__(
            self,
            archive: _PyczArchive,
            fullname: str,
            entry_name: str,
            source_path: str,
            is_package: bool,
    ) -> None:
        super().__init__()

        self._archive = archive
        self._fullname = fullname
        self._entry_name = entry_name
        self._source_path = source_path
        self._is_package = is_package
        self.path = source_path

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._fullname!r}, {self._archive.path!r})'

    def create_module(self, spec):
        return None

    def get_code(self, fullname):
        import importlib.util
        import marshal
        import types

        if fullname != self._fullname:
            raise ImportError(f'Loader for {self._fullname!r} cannot load {fullname!r}')

        data = self._archive.read(self._entry_name)
        if len(data) < 16 or data[:4] != importlib.util.MAGIC_NUMBER:
            raise ImportError(f'Invalid or incompatible pyc for {fullname!r} in {self._archive.path!r}')
        flags = int.from_bytes(data[4:8], 'little')
        if flags & ~3:
            raise ImportError(f'Invalid pyc flags for {fullname!r} in {self._archive.path!r}')

        try:
            code = marshal.loads(data[16:])  # noqa: S302
        except (EOFError, ValueError, TypeError) as exc:
            raise ImportError(f'Invalid pyc payload for {fullname!r} in {self._archive.path!r}') from exc
        if not isinstance(code, types.CodeType):
            raise ImportError(f'Pyc payload for {fullname!r} is not code')  # noqa: TRY004
        return code

    def get_data(self, path: str) -> bytes:
        with open(path, 'rb') as f:
            return f.read()

    def get_filename(self, fullname: str) -> str:
        if fullname != self._fullname:
            raise ImportError(f'Loader for {self._fullname!r} cannot load {fullname!r}')
        return self._source_path

    def get_resource_reader(self, fullname: str) -> object | None:
        if fullname != self._fullname or not self._is_package:
            return None

        import importlib.readers
        return importlib.readers.FileReader(self)  # type: ignore[arg-type]

    def get_source(self, fullname: str) -> str:
        if fullname != self._fullname:
            raise ImportError(f'Loader for {self._fullname!r} cannot load {fullname!r}')

        import tokenize
        try:
            with tokenize.open(self._source_path) as f:
                return f.read()
        except OSError as exc:
            raise ImportError(f'Source for {fullname!r} is unavailable at {self._source_path!r}') from exc

    def is_package(self, fullname: str) -> bool:
        if fullname != self._fullname:
            raise ImportError(f'Loader for {self._fullname!r} cannot load {fullname!r}')
        return self._is_package

    def exec_module(self, module):
        code = self.get_code(self._fullname)
        exec(code, module.__dict__)


class _PyczMetaFinder:
    def __init__(
            self,
            archive_path: str,
            root_package: str,
            source_root: str,
    ) -> None:
        super().__init__()

        self._archive_path = archive_path
        self._archive: _PyczArchive | None = None
        self._root_package = root_package
        self._source_root = source_root

    def _get_archive(self) -> _PyczArchive:
        archive = self._archive
        if archive is None:
            try:
                archive = self._archive = _PyczArchive(self._archive_path)
            except OSError as exc:
                raise ImportError(f'Could not read pycz archive {self._archive_path!r}') from exc
        return archive

    @property
    def archive_path(self) -> str:
        return self._archive_path

    def find_spec(self, fullname, path=None, target=None):
        if fullname != self._root_package and not fullname.startswith(self._root_package + '.'):
            return None

        archive = self._get_archive()
        module_path = fullname.replace('.', '/')
        package_entry = module_path + '/__init__.pyc'
        module_entry = module_path + '.pyc'
        if archive.has(package_entry):
            entry_name = package_entry
            is_package = True
        elif archive.has(module_entry):
            entry_name = module_entry
            is_package = False
        else:
            return None

        import importlib.util
        import os.path

        relative_parts = fullname.split('.')[1:]
        if is_package:
            source_path = os.path.join(self._source_root, *relative_parts, '__init__.py')
            submodule_locations = [os.path.dirname(source_path)]
        else:
            source_path = os.path.join(self._source_root, *relative_parts) + '.py'
            submodule_locations = None

        loader = _PyczLoader(
            archive,
            fullname,
            entry_name,
            source_path,
            is_package,
        )
        spec = importlib.util.spec_from_file_location(
            fullname,
            source_path,
            loader=loader,  # type: ignore[arg-type]
            submodule_search_locations=submodule_locations,
        )
        if spec is None:
            raise ImportError(f'Could not construct pycz spec for {fullname!r}')
        spec.cached = f'{archive.path}/{entry_name}'
        return spec


_ACTIVE_FINDERS: dict[str, _PyczMetaFinder] = {}


def _run(archive_path: str, root_package: str, source_root: str) -> bool:
    import os.path
    import sys

    archive_path = os.path.abspath(archive_path)
    if archive_path in _ACTIVE_FINDERS:
        return False

    finder = _PyczMetaFinder(
        archive_path,
        root_package,
        os.path.abspath(source_root),
    )
    sys.meta_path.insert(0, finder)
    _ACTIVE_FINDERS[archive_path] = finder
    return True


def _validate_root_package(root_package: str) -> None:
    if not root_package.isidentifier():
        raise ValueError(f'Expected one root package name, got {root_package!r}')


def _find_source_root(root_package: str) -> str:
    import importlib.util
    import os.path

    _validate_root_package(root_package)
    spec = importlib.util.find_spec(root_package)
    if spec is None or spec.submodule_search_locations is None:
        raise ValueError(f'Could not find source package {root_package!r}')

    locations = list(spec.submodule_search_locations)
    if len(locations) != 1:
        raise ValueError(f'Package {root_package!r} has {len(locations)} source roots; exactly one is required')
    source_root = os.path.abspath(locations[0])
    if not os.path.isfile(os.path.join(source_root, '__init__.py')):
        raise ValueError(f'Package {root_package!r} is not a regular source package')
    return source_root


def _source_files(source_root: str) -> list[str]:
    import os
    import os.path

    files = []
    for directory, directory_names, file_names in os.walk(source_root):
        directory_names[:] = sorted(name for name in directory_names if name != '__pycache__')
        for file_name in sorted(file_names):
            if file_name.endswith('.py'):
                files.append(os.path.join(directory, file_name))
    return files


def _pyc_path(source_path: str, optimize: int) -> str:
    import importlib.util

    if optimize < 0:
        optimization = None
    elif optimize == 0:
        optimization = ''
    else:
        optimization = str(optimize)
    return importlib.util.cache_from_source(source_path, optimization=optimization)


def _entry_name(root_package: str, source_root: str, source_path: str) -> str:
    import os
    import os.path

    relative_path = os.path.relpath(source_path, source_root)
    if relative_path == '__init__.py':
        relative_entry = '__init__.pyc'
    else:
        relative_entry = relative_path.removesuffix('.py') + '.pyc'
    return root_package + '/' + relative_entry.replace(os.sep, '/')


def _compile_package(source_root: str, optimize: int) -> list[str]:
    import compileall
    import py_compile

    if not compileall.compile_dir(
            source_root,
            force=True,
            quiet=1,
            optimize=optimize,
            invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH,
    ):
        raise RuntimeError(f'Failed to compile all sources under {source_root!r}')
    return _source_files(source_root)


def _write_archive(
        archive_path: str,
        root_package: str,
        source_root: str,
        source_files: list[str],
        optimize: int,
) -> None:
    import os
    import os.path
    import tempfile
    import zipfile

    fd, temp_path = tempfile.mkstemp(
        dir=os.path.dirname(archive_path),
        prefix='.' + os.path.basename(archive_path) + '.',
        suffix='.tmp',
    )
    os.close(fd)
    try:
        with zipfile.ZipFile(temp_path, 'w', compression=zipfile.ZIP_STORED, allowZip64=False) as zf:
            for source_path in source_files:
                pyc_path = _pyc_path(source_path, optimize)
                if not os.path.isfile(pyc_path):
                    raise RuntimeError(f'Compiled file was not produced for {source_path!r}')
                zf.write(pyc_path, _entry_name(root_package, source_root, source_path))
        os.replace(temp_path, archive_path)
    finally:
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass


def _write_file(path: str, data: bytes) -> None:
    import os
    import os.path
    import tempfile

    fd, temp_path = tempfile.mkstemp(
        dir=os.path.dirname(path),
        prefix='.' + os.path.basename(path) + '.',
        suffix='.tmp',
    )
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
        os.replace(temp_path, path)
    finally:
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass


def _bootstrap_source() -> bytes:
    import inspect
    import sys

    return inspect.getsource(sys.modules[__name__]).encode('utf-8')


def _site_dir(site_dir: str | None, no_venv: bool) -> str:
    import os.path
    import site
    import sys

    if site_dir is not None:
        return os.path.abspath(site_dir)
    if sys.prefix == sys.base_prefix and not no_venv:
        raise RuntimeError('Refusing to install outside a virtual environment; pass --no-venv to override')

    site_dirs = site.getsitepackages()
    if not site_dirs:
        raise RuntimeError('Could not find site-packages')
    return os.path.abspath(site_dirs[0])


def _install(
        root_package: str,
        *,
        site_dir: str | None = None,
        no_venv: bool = False,
        optimize: int = -1,
) -> tuple[str, str, str, int]:
    import os
    import os.path

    source_root = _find_source_root(root_package)
    install_dir = _site_dir(site_dir, no_venv)
    os.makedirs(install_dir, exist_ok=True)

    archive_path = os.path.join(install_dir, root_package + '.pycz')
    bootstrap_path = os.path.join(install_dir, '_pycz.py')
    pth_path = os.path.join(install_dir, f'___pycz-{root_package}.pth')

    source_files = _compile_package(source_root, optimize)
    _write_archive(archive_path, root_package, source_root, source_files, optimize)
    _write_file(bootstrap_path, _bootstrap_source())
    pth_source = f'import _pycz; _pycz._run({archive_path!r}, {root_package!r}, {source_root!r})\n'
    _write_file(pth_path, pth_source.encode('utf-8'))
    return archive_path, bootstrap_path, pth_path, len(source_files)


def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description='Compile a source package into an eagerly cached, unchecked pyc zip.',
    )
    parser.add_argument('root_package', help='top-level source package to compile and accelerate')
    parser.add_argument('--site-dir', help='site-packages directory (defaults to the active environment)')
    parser.add_argument('--no-venv', action='store_true', help='allow installation outside a virtual environment')
    parser.add_argument(
        '-O',
        '--optimize',
        type=int,
        choices=(-1, 0, 1, 2),
        default=-1,
        help='bytecode optimization level; -1 uses the running interpreter level',
    )
    args = parser.parse_args()

    archive_path, bootstrap_path, pth_path, count = _install(
        args.root_package,
        site_dir=args.site_dir,
        no_venv=args.no_venv,
        optimize=args.optimize,
    )
    print(f'Wrote {count} modules to {archive_path}')
    print(f'Installed loader at {bootstrap_path}')
    print(f'Installed startup hook at {pth_path}')


if __name__ == '__main__':
    _main()
