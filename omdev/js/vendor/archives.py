import io
import posixpath
import tarfile
import typing as ta

from omcore.formats.json import all as json

from .exports import output_module_path
from .exports import output_package_exports
from .exports import read_package_exports
from .licenses import validate_license
from .models import DownloadedPackage
from .models import ExtractedPackage
from .modules import iter_import_specifiers


##


def _relative_target(
        files: ta.Mapping[str, bytes],
        source_path: str,
        specifier: str,
        /,
) -> str:
    path = specifier.split('?', 1)[0].split('#', 1)[0]
    target = posixpath.normpath(posixpath.join(posixpath.dirname(source_path), path))

    if target.startswith(('../', '/')) or target in ('.', '..'):
        raise ValueError(f'Import escapes package: {source_path} -> {specifier}')

    if target not in files:
        raise ValueError(f'Relative import target does not exist: {source_path} -> {specifier}')

    return target


def _validate_root_closure(
        files: ta.Mapping[str, bytes],
        root_entry: str,
        package: str,
        /,
) -> None:
    """
    Every package root is materialized unconditionally, so its relative closure is checked here where the failure can
    name the package. Subpath exports are resolved lazily by generation, only once something imports them, because
    export maps routinely name Node CLIs, stylesheets, metadata, or unbundled sources which are not browser ESM.
    """

    if root_entry not in files or not root_entry.endswith(('.js', '.mjs')):
        raise ValueError(f'Browser export target does not exist for {package}: {root_entry}')

    seen: set[str] = set()
    pending = [root_entry]

    while pending:
        source_path = pending.pop()
        if source_path in seen:
            continue

        seen.add(source_path)

        source = files[source_path].decode('utf-8')

        for specifier in iter_import_specifiers(source):
            if not specifier.startswith('.'):
                continue

            pending.append(_relative_target(files, source_path, specifier))


def read_archive(downloaded: DownloadedPackage, /) -> ExtractedPackage:
    package = downloaded.package
    files: dict[str, bytes] = {}

    with tarfile.open(fileobj=io.BytesIO(downloaded.data), mode='r:gz') as archive:
        for member in archive.getmembers():
            if not member.isfile() or not member.name.startswith('package/'):
                continue

            relative = member.name.removeprefix('package/')
            if (
                    not relative or
                    relative.startswith('/') or
                    '\\' in relative or
                    relative != posixpath.normpath(relative) or
                    any(part in ('', '.', '..') for part in relative.split('/'))
            ):
                raise ValueError(f'Unsafe archive member in {package.name}: {member.name}')

            if (
                    relative == 'package.json' or
                    relative.lower().startswith(('license', 'licence')) or
                    relative.endswith(('.js', '.mjs'))
            ):
                extracted = archive.extractfile(member)
                if extracted is not None:
                    if relative in files:
                        raise ValueError(f'Duplicate archive member in {package.name}: {member.name}')
                    files[relative] = extracted.read()

    try:
        metadata = json.loads(files['package.json'])
    except (KeyError, json.DecodeError) as exc:
        raise ValueError(f'Invalid package metadata for {package.name}') from exc

    if (
            not isinstance(metadata, dict) or
            metadata.get('name') != package.name or
            metadata.get('version') != package.version
    ):
        raise ValueError(f'Package identity mismatch for {package.name}')
    validate_license(package, metadata, files)

    archive_exports = read_package_exports(metadata, package.name)
    root_entry = archive_exports.entries.get('.')
    if root_entry is not None:
        _validate_root_closure(files, root_entry, package.name)

    module_origins = {name: name for name in files if name.endswith(('.js', '.mjs'))}

    root_alias = root_entry is not None
    if root_entry is not None and output_module_path(root_entry) != 'index.js':
        files['dist/index.js'] = files[root_entry]
        module_origins['dist/index.js'] = root_entry

    return ExtractedPackage(
        package=package,
        files=files,
        metadata=metadata,
        exports=output_package_exports(archive_exports, root_alias=root_alias),
        module_origins=module_origins,
    )
