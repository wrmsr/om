import base64
import hashlib
import os

import pytest

from ..downloads import ArchiveIntegrityError
from ..downloads import download
from ..models import DownloadRequest
from ..models import ResolvedPackage
from .support import serve_directory


##


def _integrity(data: bytes) -> str:
    return 'sha512-' + base64.b64encode(hashlib.sha512(data).digest()).decode('ascii')


def _package(url: str, data: bytes) -> ResolvedPackage:
    return ResolvedPackage(
        name='example',
        version='1.2.3',
        license='MIT',
        integrity=_integrity(data),
        url=url,
        dependencies={},
        peer_dependencies={},
        optional_peer_dependencies=frozenset(),
    )


def test_download_uses_a_valid_cache_entry_without_fetching(tmp_path) -> None:
    data = b'archive'
    cache_directory = os.path.join(tmp_path, 'cache')
    os.makedirs(cache_directory)
    with open(os.path.join(cache_directory, 'example-1.2.3.tgz'), 'wb') as file:
        file.write(data)

    # An unroutable URL proves the cache satisfied the request.
    downloaded = download(DownloadRequest(
        package=_package('http://127.0.0.1:1/example.tgz', data),
        cache_directory=cache_directory,
    ))

    assert downloaded.data == data


def test_download_evicts_a_corrupt_cache_entry_and_refetches(tmp_path) -> None:
    data = b'archive'
    served = os.path.join(tmp_path, 'served')
    os.makedirs(served)
    with open(os.path.join(served, 'example.tgz'), 'wb') as file:
        file.write(data)

    cache_directory = os.path.join(tmp_path, 'cache')
    os.makedirs(cache_directory)
    cache_path = os.path.join(cache_directory, 'example-1.2.3.tgz')
    with open(cache_path, 'wb') as file:
        file.write(b'truncated')

    with serve_directory(served) as base_url:
        downloaded = download(DownloadRequest(
            package=_package(f'{base_url}/example.tgz', data),
            cache_directory=cache_directory,
        ))

    assert downloaded.data == data
    with open(cache_path, 'rb') as file:
        assert file.read() == data
    assert os.listdir(cache_directory) == ['example-1.2.3.tgz']


def test_download_does_not_cache_an_archive_which_fails_integrity(tmp_path) -> None:
    served = os.path.join(tmp_path, 'served')
    os.makedirs(served)
    with open(os.path.join(served, 'example.tgz'), 'wb') as file:
        file.write(b'tampered')

    cache_directory = os.path.join(tmp_path, 'cache')

    with serve_directory(served) as base_url:
        with pytest.raises(ArchiveIntegrityError, match='integrity mismatch'):
            download(DownloadRequest(
                package=_package(f'{base_url}/example.tgz', b'expected'),
                cache_directory=cache_directory,
            ))

    assert not os.path.exists(cache_directory) or os.listdir(cache_directory) == []


def test_download_caches_a_verified_archive(tmp_path) -> None:
    data = b'archive'
    served = os.path.join(tmp_path, 'served')
    os.makedirs(served)
    with open(os.path.join(served, 'example.tgz'), 'wb') as file:
        file.write(data)

    cache_directory = os.path.join(tmp_path, 'cache')

    with serve_directory(served) as base_url:
        downloaded = download(DownloadRequest(
            package=_package(f'{base_url}/example.tgz', data),
            cache_directory=cache_directory,
        ))

    assert downloaded.data == data
    assert os.listdir(cache_directory) == ['example-1.2.3.tgz']
    with open(os.path.join(cache_directory, 'example-1.2.3.tgz'), 'rb') as file:
        assert file.read() == data
