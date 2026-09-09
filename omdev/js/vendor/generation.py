import os
import posixpath
import shutil
import stat
import tempfile

from .archives import read_archive
from .downloads import download
from .exports import output_module_path
from .manifests import load_lock
from .manifests import validate_lock
from .models import DownloadRequest
from .models import OutputBuildRequest
from .models import RewriteRequest
from .models import VendorRequest
from .models import VendorResult
from .models import VerifyRequest
from .modules import iter_import_specifiers
from .modules import package_directory
from .modules import rewrite_module
from .outputs import build_lock
from .outputs import build_notices
from .outputs import count_files
from .outputs import write_file
from .verification import verify


##


def _replace_directory(staging: str, destination: str, /) -> None:
    if os.path.lexists(destination):
        if os.path.islink(destination) or not os.path.isdir(destination):
            raise ValueError(f'Vendor destination is not a regular directory: {destination}')
        backup = tempfile.mkdtemp(prefix=f'.{os.path.basename(destination)}.old-', dir=os.path.dirname(destination))
        os.rmdir(backup)
        os.replace(destination, backup)
        try:
            os.replace(staging, destination)
        except BaseException:
            os.replace(backup, destination)
            raise
        shutil.rmtree(backup)
    else:
        os.replace(staging, destination)


def _module_target(source_path: str, specifier: str, /) -> str:
    path = specifier.split('?', 1)[0].split('#', 1)[0]
    target = posixpath.normpath(posixpath.join(posixpath.dirname(source_path), path))
    if target.startswith(('../', '/')) or target in ('.', '..'):
        raise ValueError(f'Import escapes vendor tree: {source_path} -> {specifier}')
    return target


def vendor(request: VendorRequest, /) -> VendorResult:
    validate_lock(request.manifest, request.lock)
    names = {package.name for package in request.lock.packages}

    destination = os.path.abspath(request.destination)
    if destination == os.path.abspath(os.sep):
        raise ValueError('Vendor destination cannot be the filesystem root')
    if os.path.lexists(destination) and (os.path.islink(destination) or not os.path.isdir(destination)):
        raise ValueError(f'Vendor destination is not a regular directory: {request.destination}')

    parent = os.path.dirname(destination)
    os.makedirs(parent, exist_ok=True)

    temporary = tempfile.mkdtemp(prefix=f'.{os.path.basename(destination)}.new-', dir=parent)
    destination_mode = (
        stat.S_IMODE(os.stat(destination).st_mode)
        if os.path.isdir(destination) else
        0o755
    )
    os.chmod(temporary, destination_mode)

    try:
        extracted_packages = tuple(
            read_archive(download(DownloadRequest(
                package=package,
                cache_directory=request.cache_directory,
            )))
            for package in request.lock.packages
        )

        package_exports = {package.package.name: package.exports for package in extracted_packages}

        # Every archived module is a candidate until something reaches it, so two archive files sharing an output
        # path only conflict if that path is actually materialized.
        module_sources: dict[str, list[tuple[str, bytes]]] = {}

        for extracted in extracted_packages:
            package_root = package_directory(extracted.package.name)
            for relative, source_data in extracted.files.items():
                if not relative.endswith(('.js', '.mjs')):
                    continue

                target = posixpath.join(package_root, output_module_path(relative))
                origin = posixpath.join(package_root, output_module_path(extracted.module_origins[relative]))
                module_sources.setdefault(target, []).append((origin, source_data))

        pending = [
            posixpath.join(package_directory(name), 'index.js')
            for name, exports in package_exports.items()
            if exports.entries.get('.') is not None
        ]

        modules: dict[str, bytes] = {}
        while pending:
            target = pending.pop()
            if target in modules:
                continue

            sources = module_sources.get(target, [])
            if not sources:
                raise ValueError(f'Required browser module is not present in package archives: {target}')
            if len(sources) > 1:
                raise ValueError(f'Multiple archive files produce the same vendor path: {target}')
            origin, source_data = sources[0]

            rewritten = rewrite_module(RewriteRequest(
                source=source_data.decode('utf-8'),
                source_path=target,
                source_origin=origin,
                package_names=names,
                package_exports=package_exports,
            ))

            modules[target] = rewritten.source.encode()

            pending.extend(
                _module_target(target, specifier)
                for specifier in iter_import_specifiers(rewritten.source)
            )

        written: set[str] = set()
        for extracted in extracted_packages:
            package_root = package_directory(extracted.package.name)

            for relative, data in extracted.files.items():
                if relative.endswith(('.js', '.mjs')):
                    continue

                target = posixpath.join(package_root, relative)
                if target in written:
                    raise ValueError(f'Multiple archive files produce the same vendor path: {target}')

                written.add(target)
                write_file(temporary, target, data)

        for target, data in modules.items():
            if target in written:
                raise ValueError(f'Multiple archive files produce the same vendor path: {target}')

            written.add(target)
            write_file(temporary, target, data)

        write_file(temporary, 'THIRD_PARTY.md', build_notices(request.lock))
        write_file(temporary, 'lock.json', build_lock(OutputBuildRequest(
            root=temporary,
            lock=request.lock,
        )))

        generated_lock = load_lock(os.path.join(temporary, 'lock.json'))

        verify(VerifyRequest(
            manifest=request.manifest,
            lock=generated_lock,
            destination=temporary,
        ))

        _replace_directory(temporary, destination)

    finally:
        if os.path.exists(temporary):
            shutil.rmtree(temporary)

    return VendorResult(
        destination=request.destination,
        package_count=len(request.lock.packages),
        file_count=count_files(request.destination),
    )
