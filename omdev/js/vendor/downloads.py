import base64
import hashlib
import os
import urllib.request

from .models import DownloadedPackage
from .models import DownloadRequest


##


def _cache_name(request: DownloadRequest) -> str:
    package = request.package
    return package.name.replace('/', '__').replace('@', '') + '-' + package.version + '.tgz'


def download(request: DownloadRequest, /) -> DownloadedPackage:
    package = request.package
    cache_path = os.path.join(request.cache_directory, _cache_name(request))

    try:
        with open(cache_path, 'rb') as file:
            data = file.read()

    except FileNotFoundError:
        http_request = urllib.request.Request(package.url, headers={'User-Agent': 'jsvendor/1'})  # noqa: S310
        with urllib.request.urlopen(http_request, timeout=60) as response:  # noqa: S310
            data = response.read()

        os.makedirs(request.cache_directory, exist_ok=True)
        with open(cache_path, 'wb') as file:
            file.write(data)

    algorithm, encoded_digest = package.integrity.split('-', 1)
    if algorithm != 'sha512':
        raise ValueError(f'Unsupported integrity algorithm for {package.name}: {algorithm}')

    actual = base64.b64encode(hashlib.sha512(data).digest()).decode('ascii')
    if actual != encoded_digest:
        raise ValueError(f'Archive integrity mismatch for {package.name}')

    return DownloadedPackage(
        package=package,
        data=data,
    )
