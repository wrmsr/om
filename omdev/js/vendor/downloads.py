import base64
import hashlib
import os
import tempfile
import urllib.request

from .models import DownloadedPackage
from .models import DownloadRequest
from .models import ResolvedPackage


##


class ArchiveIntegrityError(ValueError):
    pass


def _cache_name(request: DownloadRequest) -> str:
    package = request.package
    return package.name.replace('/', '__').replace('@', '') + '-' + package.version + '.tgz'


def _verify_integrity(package: ResolvedPackage, data: bytes, /) -> None:
    algorithm, encoded_digest = package.integrity.split('-', 1)
    if algorithm != 'sha512':
        raise ValueError(f'Unsupported integrity algorithm for {package.name}: {algorithm}')

    actual = base64.b64encode(hashlib.sha512(data).digest()).decode('ascii')
    if actual != encoded_digest:
        raise ArchiveIntegrityError(f'Archive integrity mismatch for {package.name}')


def _read_cache(package: ResolvedPackage, cache_path: str, /) -> bytes | None:
    try:
        with open(cache_path, 'rb') as file:
            data = file.read()
    except FileNotFoundError:
        return None

    try:
        _verify_integrity(package, data)
    except ArchiveIntegrityError:
        # A corrupt or truncated cache entry would otherwise fail every later run until removed by hand.
        os.unlink(cache_path)
        return None

    return data


def _write_cache(cache_path: str, data: bytes, /) -> None:
    directory = os.path.dirname(cache_path)
    os.makedirs(directory, exist_ok=True)

    descriptor, temporary = tempfile.mkstemp(prefix=f'.{os.path.basename(cache_path)}.', dir=directory)
    try:
        file = os.fdopen(descriptor, 'wb')
        descriptor = -1
        with file:
            file.write(data)
        os.replace(temporary, cache_path)
    except BaseException:
        if descriptor >= 0:
            os.close(descriptor)
        if os.path.exists(temporary):
            os.unlink(temporary)
        raise


def _fetch(package: ResolvedPackage, /) -> bytes:
    http_request = urllib.request.Request(package.url, headers={'User-Agent': 'jsvendor/1'})  # noqa: S310
    with urllib.request.urlopen(http_request, timeout=60) as response:  # noqa: S310
        return response.read()


def download(request: DownloadRequest, /) -> DownloadedPackage:
    package = request.package
    cache_path = os.path.join(request.cache_directory, _cache_name(request))

    data = _read_cache(package, cache_path)
    if data is None:
        data = _fetch(package)

        # Only an archive which has passed verification is ever cached.
        _verify_integrity(package, data)
        _write_cache(cache_path, data)

    return DownloadedPackage(
        package=package,
        data=data,
    )
