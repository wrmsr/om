"""
Reproduces a race in adobe/s3mock in which a GetObject racing a PutObject overwrite of the same key intermittently
fails. Observed with s3mock 5.2.3, the version pinned in docker/compose.yml.

Real S3 overwrites are atomic: a GetObject concurrent with one returns either the old or the new object in full, and
never an error. s3mock however resolves the object in its request handler but only opens the object's on-disk
`binaryData` file afterwards, while streaming the response body - and a PutObject of an existing key replaces that file
non-atomically. A GetObject landing in that window fails in one of two ways:

 - Usually the file momentarily does not exist, and the client receives a 500 with a generic `<Map>...<error>Internal
   Server Error</error>...</Map>` body rather than an S3 `<Error>` document. s3mock logs:

       java.nio.file.NoSuchFileException: <root>/<bucket>/<object uuid>/binaryData
           ...
           at java.base/java.nio.file.Files.newInputStream(Files.java:154)
           at com.adobe.testing.s3mock.s3.controller.ObjectController.getObject$lambda$2(ObjectController.kt:363)
           at org.springframework...StreamingResponseBodyReturnValueHandler$StreamingResponseBodyTask.call(...)
           ...

 - Less often the client receives a 200 with the right Content-Length but no body at all before the connection is
   closed, which urllib raises as `http.client.IncompleteRead(0 bytes read, 4096 more expected)`. s3mock logs nothing.
   Presumably the file had by then been recreated, but not yet written.

Either way the object itself is unaffected, and simply retrying the GetObject succeeds, but a client which does not
retry sees a spurious read failure. A 200 with a complete but wrong body was never observed. In omxtra.blobs both
surface as a BlobTransportError, which the s3mock conformance tests tolerate via
BlobStoreConformance.transient_read_errors.

This script creates a scratch bucket, then has a few threads repeatedly overwrite a single key while several others
repeatedly get it, until any request returns anything but a 200 or the deadline passes. It exits 0 if a failure was
reproduced, and 1 if not. The hit rate varies a lot, and seemed to fall the longer s3mock had been running: against a
freshly started one it reproduced within a fraction of a second, later it could take half a minute or more. A single
writer (`--writers 1`) also reproduces it, only less often.

It needs a running s3mock, such as from `docker run --rm -p 9090:9090 adobe/s3mock:5.2.3`:

    ./python -m x.s3mockrepro --url http://127.0.0.1:9090

It uses only the standard library, and its requests are unsigned as s3mock does not check signatures.
"""
import argparse
import collections
import dataclasses as dc
import http.client
import secrets
import sys
import threading
import time
import typing as ta
import urllib.error
import urllib.request


##


@dc.dataclass(frozen=True, kw_only=True)
class Response:
    status: int
    body: bytes


def send(method: str, url: str, *, body: bytes | None = None, timeout_s: float) -> Response:
    req = urllib.request.Request(url, data=body, method=method)  # noqa: S310
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # noqa: S310
            return Response(status=resp.status, body=resp.read())
    except urllib.error.HTTPError as e:
        with e:
            return Response(status=e.code, body=e.read())


##


@dc.dataclass(frozen=True, kw_only=True)
class Anomaly:
    outcome: str
    detail: str


@dc.dataclass(frozen=True, kw_only=True)
class ReproResult:
    outcomes: ta.Mapping[str, int]
    anomalies: ta.Sequence[Anomaly]
    elapsed_s: float


class SetupError(Exception):
    pass


class Reproducer:
    """Single-use: writer and reader threads hammer one key until a request fails or the deadline passes."""

    def __init__(
            self,
            *,
            url: str,
            num_writers: int = 4,
            num_readers: int = 8,
            object_size: int = 4096,
            deadline_s: float = 300.,
            request_timeout_s: float = 10.,
    ) -> None:
        super().__init__()

        self._num_writers = num_writers
        self._num_readers = num_readers
        self._object_size = object_size
        self._deadline_s = deadline_s
        self._request_timeout_s = request_timeout_s

        self._bucket_url = f'{url.rstrip("/")}/s3mockrepro-{secrets.token_hex(8)}'
        self._object_url = f'{self._bucket_url}/k'

        self._stop = threading.Event()
        self._counts: list[collections.Counter[str]] = []
        self._anomalies: list[Anomaly] = []

    #

    def _content(self, i: int) -> bytes:
        return bytes([i % 256]) * self._object_size

    def _send_setup(self, method: str, url: str, *, body: bytes | None = None) -> None:
        resp = send(method, url, body=body, timeout_s=self._request_timeout_s)
        if not (200 <= resp.status < 300):
            raise SetupError(f'{method} {url}: {resp.status} {resp.body!r}')

    def _send_racing(self, method: str, counts: collections.Counter[str], *, body: bytes | None = None) -> None:
        try:
            resp = send(method, self._object_url, body=body, timeout_s=self._request_timeout_s)
        except (OSError, http.client.HTTPException) as e:
            outcome, detail = f'{method} {type(e).__name__}', repr(e)
        else:
            outcome, detail = f'{method} {resp.status}', resp.body.decode('utf-8', errors='replace')

        counts[outcome] += 1
        if not outcome.endswith(' 200'):
            self._anomalies.append(Anomaly(outcome=outcome, detail=detail))
            self._stop.set()

    #

    def _write(self) -> None:
        counts: collections.Counter[str] = collections.Counter()
        try:
            i = 0
            while not self._stop.is_set():
                i += 1
                self._send_racing('PUT', counts, body=self._content(i))
        finally:
            self._stop.set()
            self._counts.append(counts)

    def _read(self) -> None:
        counts: collections.Counter[str] = collections.Counter()
        try:
            while not self._stop.is_set():
                self._send_racing('GET', counts)
        finally:
            self._stop.set()
            self._counts.append(counts)

    #

    def run(self) -> ReproResult:
        self._send_setup('PUT', self._bucket_url)
        try:
            self._send_setup('PUT', self._object_url, body=self._content(0))

            threads = [
                *[threading.Thread(target=self._write) for _ in range(self._num_writers)],
                *[threading.Thread(target=self._read) for _ in range(self._num_readers)],
            ]
            start = time.monotonic()
            for t in threads:
                t.start()
            self._stop.wait(self._deadline_s)
            self._stop.set()
            for t in threads:
                t.join()
            elapsed_s = time.monotonic() - start

        finally:
            self._send_setup('DELETE', self._object_url)
            self._send_setup('DELETE', self._bucket_url)

        outcomes: collections.Counter[str] = collections.Counter()
        for counts in self._counts:
            outcomes.update(counts)
        return ReproResult(
            outcomes=dict(sorted(outcomes.items())),
            anomalies=list(self._anomalies),
            elapsed_s=elapsed_s,
        )


##


def _main() -> None:
    parser = argparse.ArgumentParser(description='Reproduces s3mock failing GetObjects which race an overwrite.')
    parser.add_argument('--url', default='http://127.0.0.1:9090')
    parser.add_argument('--writers', type=int, default=4)
    parser.add_argument('--readers', type=int, default=8)
    parser.add_argument('--size', type=int, default=4096)
    parser.add_argument('--deadline-s', type=float, default=300.)
    args = parser.parse_args()

    res = Reproducer(
        url=args.url,
        num_writers=args.writers,
        num_readers=args.readers,
        object_size=args.size,
        deadline_s=args.deadline_s,
    ).run()

    for outcome, n in res.outcomes.items():
        print(f'{outcome}: {n}')

    if not res.anomalies:
        print(f'not reproduced in {res.elapsed_s:.2f}s')
        sys.exit(1)

    print(f'reproduced in {res.elapsed_s:.2f}s')
    for a in res.anomalies:
        print(f'\n{a.outcome}:\n{a.detail}')


if __name__ == '__main__':
    _main()
