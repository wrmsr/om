import hashlib
import os
import posixpath
import stat
import tempfile
import typing as ta

from omcore.formats.json import all as json

from .models import OutputBuildRequest
from .models import ResolvedPackage
from .models import VendorLock


##


def write_file(root: str, relative: str, data: bytes) -> None:
    if (
            not relative or
            relative.startswith('/') or
            '\\' in relative or
            relative != posixpath.normpath(relative) or
            any(part in ('', '.', '..') for part in relative.split('/'))
    ):
        raise ValueError(f'Unsafe vendor output path: {relative}')
    destination = os.path.join(root, *relative.split('/'))
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    with open(destination, 'wb') as file:
        file.write(data)


def write_path(path: str, data: bytes, /) -> None:
    directory = os.path.abspath(os.path.dirname(path) or '.')
    os.makedirs(directory, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f'.{os.path.basename(path)}.', dir=directory)
    try:
        mode = stat.S_IMODE(os.stat(path).st_mode) if os.path.exists(path) else 0o644
        os.fchmod(descriptor, mode)
        file = os.fdopen(descriptor, 'wb')
        descriptor = -1
        with file:
            file.write(data)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    except BaseException:
        if descriptor >= 0:
            os.close(descriptor)
        if os.path.exists(temporary):
            os.unlink(temporary)
        raise


def count_files(root: str, /) -> int:
    return sum(len(names) for _, _, names in os.walk(root))


def build_lock(request: OutputBuildRequest, /) -> bytes:
    files: dict[str, str] = {}
    for directory, _, names in os.walk(request.root):
        for name in names:
            if name == 'lock.json':
                continue

            path = os.path.join(directory, name)
            relative = os.path.relpath(path, request.root).replace(os.sep, '/')
            with open(path, 'rb') as file:
                files[relative] = hashlib.sha256(file.read()).hexdigest()

    return render_lock(VendorLock(
        format_version=2,
        roots=request.lock.roots,
        packages=request.lock.packages,
        files=dict(sorted(files.items())),
    ))


def _render_package(package: ResolvedPackage, /) -> dict[str, ta.Any]:
    value = {
        'name': package.name,
        'version': package.version,
        'license': package.license,
        'integrity': package.integrity,
        'url': package.url,
        'dependencies': package.dependencies,
        'peer_dependencies': package.peer_dependencies,
    }
    if package.optional_peer_dependencies:
        value['optional_peer_dependencies'] = sorted(package.optional_peer_dependencies)
    return value


def render_lock(lock: VendorLock, /) -> bytes:
    value = {
        'format_version': lock.format_version,
        'roots': [
            {
                'name': root.name,
                'version': root.version,
            }
            for root in lock.roots
        ],
        'packages': [_render_package(package) for package in lock.packages],
        'files': lock.files,
    }
    return (json.dumps_pretty(value) + '\n').encode()


def build_notices(lock: VendorLock, /) -> bytes:
    lines = [
        '# Third-party JavaScript',
        '',
        'The following runtime packages are vendored from their pinned npm registry archives. Every package is used',
        'under its included permissive license, listed below; its original license text is retained beside the ',
        'normalized ESM.',
        '',
        '| Package | Version | License |',
        '|---|---:|---|',
    ]
    lines.extend(f'| `{spec.name}` | {spec.version} | {spec.license} |' for spec in lock.packages)

    # Version-one output retains this footer so extraction does not churn committed vendor trees.
    lines.extend(['', f'Files under `packages/` are generated. Update them only through `{__package__}`.', ''])
    return '\n'.join(lines).encode()
