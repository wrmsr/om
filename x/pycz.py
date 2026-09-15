"""Load a source package's compiled modules from an in-memory pyc zip."""


##


class _PyczError(ImportError):
    pass


class _PyczArchive:
    def __init__(
            self,
            path: str,
            data=None,  # type: bytes | None
    ) -> None:
        super().__init__()

        self._path = path

        if data is None:
            with open(path, 'rb') as f:
                data = f.read()
        self._data = data

        self._central_offset = 0
        self._central_entries = self._parse_central_entries(self._data)
        self._local_entries: dict[str, tuple[int, int]] = {}

    def close(self) -> None:
        pass

    def _parse_central_entries(self, data: bytes) -> dict[
        str,
        tuple[
            int,
            int,
            int,
            int,
            bytes,
        ],
    ]:
        data_len = len(data)
        int_from_bytes = int.from_bytes

        eocd_offset = data.rfind(b'PK\x05\x06', max(0, data_len - (65535 + 22)))
        if eocd_offset < 0:
            raise _PyczError('Invalid pycz eocd.signature')

        if (end := eocd_offset + 6) > data_len:
            raise _PyczError('Truncated pycz eocd.disk_number')
        disk_number = int_from_bytes(data[eocd_offset + 4:end], 'little')
        if (end := eocd_offset + 8) > data_len:
            raise _PyczError('Truncated pycz eocd.central_disk_number')
        central_disk_number = int_from_bytes(data[eocd_offset + 6:end], 'little')
        if (end := eocd_offset + 10) > data_len:
            raise _PyczError('Truncated pycz eocd.disk_entry_count')
        disk_entry_count = int_from_bytes(data[eocd_offset + 8:end], 'little')
        if (end := eocd_offset + 12) > data_len:
            raise _PyczError('Truncated pycz eocd.entry_count')
        entry_count = int_from_bytes(data[eocd_offset + 10:end], 'little')
        if (end := eocd_offset + 16) > data_len:
            raise _PyczError('Truncated pycz eocd.central_size')
        central_size = int_from_bytes(data[eocd_offset + 12:end], 'little')
        if (end := eocd_offset + 20) > data_len:
            raise _PyczError('Truncated pycz eocd.central_offset')
        central_offset = int_from_bytes(data[eocd_offset + 16:end], 'little')
        if (end := eocd_offset + 22) > data_len:
            raise _PyczError('Truncated pycz eocd.comment_size')
        comment_size = int_from_bytes(data[eocd_offset + 20:end], 'little')

        if disk_number:
            raise _PyczError('Unsupported pycz eocd.disk_number')
        if central_disk_number:
            raise _PyczError('Unsupported pycz eocd.central_disk_number')
        if disk_entry_count != entry_count:
            raise _PyczError('Mismatched pycz eocd.disk_entry_count/entry_count')
        if entry_count == 0xffff:
            raise _PyczError('Unsupported ZIP64 pycz eocd.entry_count')
        if central_size == 0xffffffff:
            raise _PyczError('Unsupported ZIP64 pycz eocd.central_size')
        if central_offset == 0xffffffff:
            raise _PyczError('Unsupported ZIP64 pycz eocd.central_offset')
        if eocd_offset + 22 + comment_size != data_len:
            raise _PyczError('Invalid pycz eocd.comment_size')
        if central_offset + central_size != eocd_offset:
            raise _PyczError('Mismatched pycz eocd.central_offset/central_size')

        entries: dict[
            str,
            tuple[
                int,
                int,
                int,
                int,
                bytes,
            ],
        ] = {}

        offset = central_offset
        for i in range(entry_count):
            if data[offset:offset + 4] != b'PK\x01\x02':
                raise _PyczError(f'Invalid pycz central[{i}].signature')
            if offset + 46 > eocd_offset:
                raise _PyczError(f'Invalid pycz central[{i}].header_size')

            if (end := offset + 10) > data_len:
                raise _PyczError(f'Truncated pycz central[{i}].flags')
            flags = int_from_bytes(data[offset + 8:end], 'little')
            if (end := offset + 12) > data_len:
                raise _PyczError(f'Truncated pycz central[{i}].compression')
            compression = int_from_bytes(data[offset + 10:end], 'little')
            if (end := offset + 24) > data_len:
                raise _PyczError(f'Truncated pycz central[{i}].compressed_size')
            compressed_size = int_from_bytes(data[offset + 20:end], 'little')
            if (end := offset + 28) > data_len:
                raise _PyczError(f'Truncated pycz central[{i}].uncompressed_size')
            uncompressed_size = int_from_bytes(data[offset + 24:end], 'little')
            if (end := offset + 30) > data_len:
                raise _PyczError(f'Truncated pycz central[{i}].name_size')
            name_size = int_from_bytes(data[offset + 28:end], 'little')
            if (end := offset + 32) > data_len:
                raise _PyczError(f'Truncated pycz central[{i}].extra_size')
            extra_size = int_from_bytes(data[offset + 30:end], 'little')
            if (end := offset + 34) > data_len:
                raise _PyczError(f'Truncated pycz central[{i}].comment_size')
            entry_comment_size = int_from_bytes(data[offset + 32:end], 'little')
            if (end := offset + 36) > data_len:
                raise _PyczError(f'Truncated pycz central[{i}].disk_number')
            entry_disk_number = int_from_bytes(data[offset + 34:end], 'little')
            if (end := offset + 46) > data_len:
                raise _PyczError(f'Truncated pycz central[{i}].local_offset')
            local_offset = int_from_bytes(data[offset + 42:end], 'little')
            entry_end = offset + 46 + name_size + extra_size + entry_comment_size
            if entry_end > eocd_offset:
                raise _PyczError(f'Invalid pycz central[{i}].name_size/extra_size/comment_size')
            if flags & 1:
                raise _PyczError(f'Unsupported encryption in pycz central[{i}].flags')
            if compression != 0:
                raise _PyczError(f'Unsupported pycz central[{i}].compression')
            if compressed_size != uncompressed_size:
                raise _PyczError(f'Mismatched pycz central[{i}].compressed_size/uncompressed_size')
            if entry_disk_number:
                raise _PyczError(f'Unsupported pycz central[{i}].disk_number')

            name_data = data[offset + 46:offset + 46 + name_size]
            try:
                name = name_data.decode('utf-8' if flags & 0x800 else 'cp437')
            except UnicodeDecodeError as exc:
                raise _PyczError(f'Invalid pycz central[{i}].name') from exc
            if name in entries:
                raise _PyczError(f'Duplicate pycz central[{i}].name: {name!r}')

            entries[name] = (i, flags, uncompressed_size, local_offset, name_data)
            offset = entry_end

        if offset != eocd_offset:
            raise _PyczError('Mismatched pycz eocd.central_size/central entries')
        self._central_offset = central_offset
        return entries

    def _parse_local_entry(self, name: str) -> tuple[int, int]:
        try:
            i, flags, uncompressed_size, local_offset, name_data = self._central_entries[name]
        except KeyError:
            raise ImportError(f'Pycz central entry not found: {name!r}') from None

        data = self._data
        data_len = len(data)
        int_from_bytes = int.from_bytes

        if data[local_offset:local_offset + 4] != b'PK\x03\x04':
            raise _PyczError(f'Invalid pycz local[{i}].signature: {name!r}')
        if local_offset + 30 > self._central_offset:
            raise _PyczError(f'Invalid pycz local[{i}].header_size: {name!r}')
        if (end := local_offset + 8) > data_len:
            raise _PyczError(f'Truncated pycz local[{i}].flags: {name!r}')
        local_flags = int_from_bytes(data[local_offset + 6:end], 'little')
        if (end := local_offset + 10) > data_len:
            raise _PyczError(f'Truncated pycz local[{i}].compression: {name!r}')
        local_compression = int_from_bytes(data[local_offset + 8:end], 'little')
        if (end := local_offset + 28) > data_len:
            raise _PyczError(f'Truncated pycz local[{i}].name_size: {name!r}')
        local_name_size = int_from_bytes(data[local_offset + 26:end], 'little')
        if (end := local_offset + 30) > data_len:
            raise _PyczError(f'Truncated pycz local[{i}].extra_size: {name!r}')
        local_extra_size = int_from_bytes(data[local_offset + 28:end], 'little')
        local_name = data[local_offset + 30:local_offset + 30 + local_name_size]
        data_offset = local_offset + 30 + local_name_size + local_extra_size
        if local_flags != flags:
            raise _PyczError(f'Mismatched pycz local[{i}].flags: {name!r}')
        if local_compression != 0:
            raise _PyczError(f'Mismatched pycz local[{i}].compression: {name!r}')
        if local_name != name_data:
            raise _PyczError(f'Mismatched pycz local[{i}].name: {name!r}')
        if data_offset + uncompressed_size > self._central_offset:
            raise _PyczError(f'Invalid pycz local[{i}].extra_size/central[{i}].uncompressed_size: {name!r}')
        return data_offset, uncompressed_size

    def _get_local_entry(self, name: str) -> tuple[int, int]:
        entry = self._local_entries.get(name)
        if entry is None:
            entry = self._parse_local_entry(name)
            self._local_entries[name] = entry
        return entry

    @property
    def path(self) -> str:
        return self._path

    def has(self, name: str) -> bool:
        return name in self._central_entries

    def read(self, name: str) -> bytes:
        offset, size = self._get_local_entry(name)
        return self._data[offset:offset + size]


class _MmapPyczArchive(_PyczArchive):
    def __init__(
            self,
            path: str,
    ) -> None:
        import mmap
        import os.path

        self._os_close = os.close

        fd = self._fd = os.open(path, os.O_RDONLY)
        os.set_inheritable(fd, True)
        st = os.fstat(fd)
        mm = self._mm = mmap.mmap(
            fd,
            length=st.st_size,
            access=mmap.ACCESS_READ,
        )

        super().__init__(
            path,
            mm,  # type: ignore[arg-type]
        )

    _fd: int | None = None
    _mm = None  # type: object | None

    def close(self) -> None:
        if (mm := self._mm) is not None:
            mm.close()  # type: ignore[attr-defined]
        self._mm = None

        if (fd := self._fd) is not None:
            self._os_close(fd)
        self._fd = None

    def __del__(self) -> None:
        self.close()


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

    def close(self) -> None:
        if (ar := self._archive) is not None:
            ar.close()
        self._archive = None

    def _get_archive(self) -> _PyczArchive:
        archive = self._archive
        if archive is None:
            try:
                archive = self._archive = _MmapPyczArchive(self._archive_path)
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


def _run(
        archive_path: str,
        root_package: str,
        source_root: str,
) -> bool:
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


##


class _PyczInstaller:
    def _validate_root_package(self, root_package: str) -> None:
        if not root_package.isidentifier():
            raise ValueError(f'Expected one root package name, got {root_package!r}')

    def _find_source_root(self, root_package: str) -> str:
        import importlib.util
        import os.path

        self._validate_root_package(root_package)
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

    def _source_files(self, source_root: str) -> list[str]:
        import os.path

        files = []
        for directory, directory_names, file_names in os.walk(source_root):
            directory_names[:] = sorted(name for name in directory_names if name != '__pycache__')
            for file_name in sorted(file_names):
                if file_name.endswith('.py'):
                    files.append(os.path.join(directory, file_name))
        return files

    def _pyc_path(self, source_path: str, optimize: int) -> str:
        import importlib.util

        if optimize < 0:
            optimization = None
        elif optimize == 0:
            optimization = ''
        else:
            optimization = str(optimize)
        return importlib.util.cache_from_source(source_path, optimization=optimization)

    def _entry_name(
            self,
            root_package: str,
            source_root: str,
            source_path: str,
    ) -> str:
        import os.path

        relative_path = os.path.relpath(source_path, source_root)
        if relative_path == '__init__.py':
            relative_entry = '__init__.pyc'
        else:
            relative_entry = relative_path.removesuffix('.py') + '.pyc'
        return root_package + '/' + relative_entry.replace(os.sep, '/')

    def _compile_package(self, source_root: str, optimize: int) -> list[str]:
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
        return self._source_files(source_root)

    def _write_archive(
            self,
            archive_path: str,
            root_package: str,
            source_root: str,
            source_files: list[str],
            optimize: int,
    ) -> None:
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
                    pyc_path = self._pyc_path(source_path, optimize)
                    if not os.path.isfile(pyc_path):
                        raise RuntimeError(f'Compiled file was not produced for {source_path!r}')
                    zf.write(pyc_path, self._entry_name(root_package, source_root, source_path))
            os.replace(temp_path, archive_path)
        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    def _write_file(self, path: str, data: bytes) -> None:
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

    def _bootstrap_source(self) -> bytes:
        import inspect
        import sys

        return inspect.getsource(sys.modules[__name__]).encode('utf-8')

    def _site_dir(self, site_dir: str | None, no_venv: bool) -> str:
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

    def install(
            self,
            root_package: str,
            *,
            site_dir: str | None = None,
            no_venv: bool = False,
            optimize: int = -1,
    ) -> tuple[
        str,
        str,
        str,
        int,
    ]:
        import os.path

        source_root = self._find_source_root(root_package)
        install_dir = self._site_dir(site_dir, no_venv)
        os.makedirs(install_dir, exist_ok=True)

        archive_path = os.path.join(install_dir, root_package + '.pycz')
        bootstrap_path = os.path.join(install_dir, '_pycz.py')
        pth_path = os.path.join(install_dir, f'___pycz-{root_package}.pth')

        source_files = self._compile_package(source_root, optimize)
        self._write_archive(archive_path, root_package, source_root, source_files, optimize)
        self._write_file(bootstrap_path, self._bootstrap_source())
        pth_source = f'import _pycz; _pycz._run({archive_path!r}, {root_package!r}, {source_root!r})\n'
        self._write_file(pth_path, pth_source.encode('utf-8'))

        return (
            archive_path,
            bootstrap_path,
            pth_path,
            len(source_files),
        )


##


def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description='Compile a source package into an eagerly cached, unchecked pyc zip.',
    )
    parser.add_argument(
        'root_package',
        help='top-level source package to compile and accelerate',
        nargs='+',
    )
    parser.add_argument(
        '--site-dir',
        help='site-packages directory (defaults to the active environment)',
    )
    parser.add_argument(
        '--no-venv',
        action='store_true',
        help='allow installation outside a virtual environment',
    )
    parser.add_argument(
        '-O',
        '--optimize',
        type=int,
        choices=(-1, 0, 1, 2),
        default=-1,
        help='bytecode optimization level; -1 uses the running interpreter level',
    )
    args = parser.parse_args()

    for root_package in args.root_package:
        (
            archive_path,
            bootstrap_path,
            pth_path,
            count,
        ) = _PyczInstaller().install(
            root_package,
            site_dir=args.site_dir,
            no_venv=args.no_venv,
            optimize=args.optimize,
        )
        print(f'Wrote {count} modules to {archive_path}')
        print(f'Installed loader at {bootstrap_path}')
        print(f'Installed startup hook at {pth_path}')


if __name__ == '__main__':
    _main()
