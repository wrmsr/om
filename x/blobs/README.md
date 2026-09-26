# x.blobs

A small blob store abstraction: a flat keyspace of immutable, atomically replaced objects with optional preconditions,
over an in-memory dict, a local filesystem, and S3-compatible object stores (AWS S3, Cloudflare R2, s3mock). Modeled on
Rust's `object_store` rather than on file-like APIs: what matters most is preconditions on object versions, which make
optimistic concurrency - such as LSM manifest commits - possible directly on object storage.

Temporarily lives in `x/`. Core is headed for `omcore/blobs`, `aws/` for `ominfra/blobs/aws`, and `aws/restxml.py` for
`ominfra/clouds/aws`.

## Semantics

- **Keys** are what S3, R2, a POSIX filesystem and XML 1.0 can all represent: non-empty, at most 1024 UTF-8 bytes, no
  control or XML-invalid characters, and `/`-separated segments that are neither empty nor `.` or `..`. `/` means
  nothing except to `list_shallow`.
- **Versions** (`BlobVersion`) are opaque etags. They change whenever content changes, but may recur when identical
  content is rewritten (an S3 single-part etag is the MD5 of the content), so never use `IfMatch` as a fencing token
  over content that can repeat.
- **Preconditions:**
  - `IfAbsent` (writes only), `IfMatch(version)` (reads and writes), and `IfNoneMatch(version)` (reads only).
  - `IfMatch` against a missing key is always `BlobPreconditionFailedError`, never `BlobNotFoundError`.
  - `IfNoneMatch` of the current version raises `BlobNotModifiedError`.
- **Ranges** (`OffsetBlobRange`, `SuffixBlobRange`) clamp like Python slices, on every backend. `BlobInfo.size` is
  always the whole object's size.
- **Listings** are in code point order (which is UTF-8 byte order, as S3 and R2 use), and are not snapshots.
- **Writers** publish nothing until `commit()`, which applies the precondition. Leaving the context without committing
  discards everything, on a normal exit too. `put_stream` evaluates its precondition at the end in the same way, and
  raises `BlobStreamLengthError` (publishing nothing) if a declared length doesn't match.
- `delete` of a missing key is a no-op. `delete_many` is unconditional and non-atomic, and raises
  `BlobDeleteManyError` carrying per-key failures after attempting every key.
- `copy(k, k)` raises `ValueError`.
- **Checks before IO.** Key validation, capability checks, and other static argument checks happen before any IO.
- **Indeterminacy:**
  - `BlobIndeterminateError` means a mutation may or may not have taken effect: a timeout, a dropped connection, or a
    5xx after the body was sent.
  - A conditional write is never blindly retried past that point, because a retry of a write that did land would fail
    its precondition against itself.
  - `ManifestStore` shows how to resolve it: numbered manifests published with `IfAbsent`, each with a unique body,
    are read back after an indeterminate failure.
- `BlobConflictError` means nothing was written, and `BlobTransportError` means retrying is safe.
  `BlobThrottledError` (a `BlobIndeterminateError`) means the backend asked us to slow down and nothing retried.

## Sync and async

- There are two interfaces: `BlobStore` / `BlobWriter` (sync) and `AsyncBlobStore` / `AsyncBlobWriter`.
- Each backend implements exactly one of them:
  - `DictBlobStore` is sync; it is pure.
  - `LocalBlobStore` is sync, deliberately, with blocking filesystem calls.
  - `S3BlobStore` is async.
- Higher-level helpers are async-only: `ManifestStore`, `PrefixedBlobStore`, the readers, the parallel plans, and the
  LSM.
- Crossing sides is done only by explicit composition. There are deliberately no convenience constructors - in real
  code the dependency injector wires these:
  - `SyncToAsyncBlobStore(store)` runs a sync store inline under the async interface. A blocking store blocks the event
    loop for the duration of each call.
  - `AsyncToSyncBlobStore(store)` drives an async store with `lang.sync_await`. This is only valid when the async
    store never actually suspends: for example an `S3BlobStore` given an `http.SyncAsyncHttpClient` over a sync client.
- For example, the LSM (async) runs over `SyncToAsyncBlobStore(DictBlobStore())`. A sync caller of S3 uses
  `AsyncToSyncBlobStore(S3BlobStore(..., http_client=http.SyncAsyncHttpClient(http.client())))`.

## Capabilities

Optional precondition support is runtime data (`BlobCapability`), checked before IO. Using an unsupported one raises
`UnsupportedBlobOperationError`.

| Capability | dict | local | AWS S3 | R2 | s3mock 5.2.3 |
| --- | --- | --- | --- | --- | --- |
| `PUT_IF_ABSENT` | yes | yes (`os.link`) | yes | yes | yes, but not atomic under races |
| `PUT_IF_MATCH` | yes | yes (flock) | yes | yes | yes, but not atomic under races |
| `DELETE_IF_MATCH` | yes | yes (flock) | yes | unverified: off | yes |
| `COPY_IF_ABSENT` | yes | yes | unverified: off | yes (`cf-` headers) | silently ignored: off |
| `COPY_IF_MATCH` | yes | yes | unverified: off | yes (`cf-` headers) | silently ignored: off |

"Unverified" cells should be settled with the capability probe (`./python -m x.blobs.aws.tests.probe ...`) and the
live conformance tier, and then flipped in the relevant `Config`.

## Backends

### Local (`x.blobs.local.LocalBlobStore`)

- **Layout:**
  - Every key segment but the last is a `<enc>.dir` directory, and the last is a `<enc>.file` file, so `a/b` and
    `a/b/c` coexist.
  - Segment names are escaped unconditionally to pure lowercase ASCII, so case- and normalization-insensitive
    filesystems (macOS) can't merge distinct keys.
  - Anything else in the tree is ignored.
  - An encoded segment must fit in 255 bytes.
- **Writes:**
  - A write goes to a tmp file under `.tmp/`, which is stamped with a full-precision mtime, fsync'd, and then
    committed.
  - `IfAbsent` commits with an unlocked `os.link`, an atomic create-if-absent.
  - Every other mutation holds the key's striped flock under `.locks/`.
  - Readers never lock.
- **Requirements:** a local filesystem (flock is unreliable over NFS) with nanosecond timestamps, because versions are
  `<inode>-<mtime_ns>-<size>`.
- `remove_stale_tmp_files` cleans up after crashed writers.

### S3 (`x.blobs.aws.S3BlobStore`)

- It uses only the internal SigV4 signer, the generated AWS models, and the REST-XML serde, over any
  `omcore.http.AsyncHttpClient`: the pipeline clients, urllib or httpx.
- With no client given, each request uses a fresh default from `http.manage_async_client`.
- **`S3BlobStore.Config`:**
  - It has one field per behavioral difference, named for what it does. Defaults are AWS's.
  - `R2_CONFIG` and `S3_MOCK_CONFIG` are the presets.
  - R2 is reached at `https://<account_id>.r2.cloudflarestorage.com` with region `auto` and path-style addressing (the
    `S3Endpoint` default).
- **Retries:**
  - The store never retries or sleeps by default.
  - `SimpleS3RetryPolicy(sleeps: asl.Sleeps, ...)` retries whatever it is offered, with full-jitter backoff.
  - Ambiguous failures of conditional writes are never offered to any policy.
- **Writers:**
  - Writers buffer per part: an object smaller than `part_size` (at least 5 MiB) is a single PutObject; anything
    larger is a multipart upload with uniform parts.
  - An uncommitted writer aborts its upload.
  - `abort_stale_uploads` cleans up after crashed writers. A bucket lifecycle rule `AbortIncompleteMultipartUpload`
    is the real backstop.
- **Streamed uploads** (`Config.streamed_uploads`) send known-length `put_stream` bodies as aws-chunked streams with
  per-chunk SigV4 signatures.
  - omcore.http request bodies can't stream yet, so the default `S3StreamingSender` raises `NotImplementedError`.
  - When `HttpClientRequest.data` accepts an async iterable of bytes, it becomes a one-liner.
  - The writer's own streaming variant additionally needs a task-spawning primitive; see `aws/writers.py`.
- **Parallel transfers:** `plans.plan_parallel_get` (any store) and `aws.uploads` (S3) split a transfer into
  independent operations to run concurrently and then finalize.

## The LSM

`x/blobs/tests/lsm/` holds a deliberately simple LSM, written as an integration test of the abstraction and due to be
promoted. It is async-only and IO-pure over any `AsyncBlobStore`:
- SSTs are opened with one suffix-ranged get, with IfMatch-pinned block reads.
- Numbered manifests use epoch fencing.
- There are snapshot readers, and grace-period garbage collection.
- There is no WAL: only flushed data is durable.

## Testing

- `tests/conformance.py` is the behavioral spec every backend runs, written once against `AsyncBlobStore`:
  - it runs through `SyncToAsyncBlobStore` for the sync stores
  - it runs against s3mock on the sync pipelines, urllib and httpx clients, and the asyncio pipelines and async httpx
    clients
- s3mock tests are marked `integration`. They use the `om-s3` compose service, or `OM_TEST_S3_URL`, e.g.
  `http://127.0.0.1:9090` for `~/scripts/run-s3mock`.
- Live AWS/R2 tests are marked `online` and skip without their secrets (see `aws/tests/test_live.py`).
