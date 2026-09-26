# x/blobs: follow-up implementation plan

This is a work plan for a coding agent: follow it top to bottom. Each phase lists its goal, concrete steps, tests, and
a "done when" checklist. The phases are ordered so each one builds on ground the previous ones already tested. Finish
each phase green (tests, ruff, mypy) before starting the next. Tick the checkboxes in this file as you go, and add
anything you couldn't verify to [Handoff notes](#handoff-notes) at the bottom.

This plan has been through review with the user, and the decisions in [0.4](#04-decisions-settled-in-review) are
settled. If one turns out to be impossible, don't quietly redesign: pick the closest option, and write down what
happened and why in the handoff notes.

## Contents

- [0. Orientation](#0-orientation)
- [Phase 1: Core interfaces, adapters and contract](#phase-1-core-interfaces-adapters-and-contract)
- [Phase 2: Test support and the conformance suite](#phase-2-test-support-and-the-conformance-suite)
- [Phase 3: Local filesystem backend](#phase-3-local-filesystem-backend)
- [Phase 4: The LSM (async, over dict and local)](#phase-4-the-lsm-async-over-dict-and-local)
- [Phase 5: omcore prerequisites](#phase-5-omcore-prerequisites)
- [Phase 6: SigV4 signer fixes and streaming chunk signing](#phase-6-sigv4-signer-fixes-and-streaming-chunk-signing)
- [Phase 7: AWS model codegen: wire metadata](#phase-7-aws-model-codegen-wire-metadata)
- [Phase 8: REST-XML protocol module](#phase-8-rest-xml-protocol-module)
- [Phase 9: S3 request layer (sans-IO)](#phase-9-s3-request-layer-sans-io)
- [Phase 10: S3BlobStore](#phase-10-s3blobstore)
- [Phase 11: S3 test tiers](#phase-11-s3-test-tiers)
- [Phase 12: Cloudflare R2](#phase-12-cloudflare-r2)
- [Phase 13: Streamed uploads, up to the HTTP seam](#phase-13-streamed-uploads-up-to-the-http-seam)
- [Phase 14: Parallel transfer plans](#phase-14-parallel-transfer-plans)
- [Phase 15: Wrap-up](#phase-15-wrap-up)
- [Appendix A: S3 response to blob error mapping](#appendix-a-s3-response-to-blob-error-mapping)
- [Appendix B: Conformance checklist](#appendix-b-conformance-checklist)
- [Appendix C: References](#appendix-c-references)
- [Handoff notes](#handoff-notes)


## 0. Orientation

### 0.1 What exists

In `x/blobs/` (commit `7d10d35c1`):

| Module | Contents |
| --- | --- |
| `types.py` | `BlobVersion`, `BlobInfo`, `BlobPrefix`, `Blob`, ranges, preconditions (`IfAbsent`, `IfMatch`, ...) |
| `caps.py` | `BlobCapability` flags, `check_blob_capabilities`, per-op capability helpers |
| `errors.py` | the `BlobStoreError` hierarchy, including `BlobIndeterminateError` and `BlobConflictError` |
| `keys.py` | `check_blob_key` |
| `stores.py` | the sync `BlobStore` and `BlobWriter` interfaces |
| `dicts.py` | `DictBlobStore`: the reference semantics and the test double |
| `manifests.py` | `ManifestStore`: numbered `IfAbsent` manifests with indeterminate-write resolution (sync, for now) |
| `tests/` | `test_dicts.py`, `test_manifests.py` |

Outside `x/blobs/`:

- `ominfra/clouds/aws/auth.py` is **`@om-lite`**: it runs in production on a 3.8 interpreter. It contains
  `AwsSigner` and `V4AwsSigner`, and is amalgamated into `ominfra/scripts/journald2aws.py`. The generated model code
  under `ominfra/clouds/aws/models/` is **not** lite.
- `ominfra/clouds/aws/models/` is botocore-driven codegen:
  - `gen/gen.py` and `gen/cli.py` do the generation. `make gen-aws` runs
    `-m ominfra.clouds.aws.models.gen gen-services`.
  - `base/base.py` holds `Shape`, `ShapeInfo`, `Operation` and the field metadata markers.
  - `services/services.toml` lists the operations to generate. `services/s3/__init__.py` is the generated S3 module.
  - Generated fields carry `member_name`, `serialization_name`, `value_type` and `shape_name`, but no HTTP location,
    and `Operation` has no HTTP method or request URI. botocore's model has both; see phase 7.
- `omcore/http/clients/` (**`@om-lite`**, except `httpx.py`) holds the client layer.
  - Types and implementations:
    - `HttpClientRequest(url, method, headers, data: bytes | str | None, timeout_s)`
    - sync `HttpClient` and async `AsyncHttpClient`
    - `SyncAsyncHttpClient`, an async interface over a sync client
    - `UrllibHttpClient`, `HttpxHttpClient`, `HttpxAsyncHttpClient`
    - the pipeline clients `IoPipelineHttpClient` (sync) and `AsyncioIoPipelineAsyncHttpClient`
  - Behaviour:
    - Non-2xx responses are returned, not raised.
    - Transport failures raise `HttpClientError`. urllib and httpx don't yet wrap errors raised during body reads;
      see phase 5.
    - `http.manage_async_client(client)` yields `client`, or a fresh default client if `client` is None.
    - No client can stream a request body yet. The user says that support is coming soon. Build as if it exists, and
      stop at one seam (phase 13).
- `omcore/asyncs/asynclite/` is a small async abstraction with sync, asyncio and anyio backends; `all as asl`. The
  sync backend's lock has two bugs (phase 5).
- `omcore/lite/asyncs.py` provides `sync_await`, `sync_aiter`, `SyncToAsyncContextManager` and friends.
  `lang.sync_await` is the same function.
- s3mock:
  - `docker/compose.yml` runs `om-s3` from `adobe/s3mock:5.2.3`, with container port 9090 mapped to host port 35226.
  - In the sandbox, `~/scripts/run-s3mock` runs the same version in the **foreground**; start it as a background
    task. It serves http on `127.0.0.1:9090` (https on 9191).
- Models for test harnesses:
  - `omcore/sql/tests/harness.py` resolves a compose service, with an env var override and a check for running
    inside docker.
  - `omcore/secrets/tests/harness.py` provides `HarnessSecrets.get_or_skip(key)`.
- Models for the async-first pattern:
  - `omcore/inject/impl/sync.py`: `InjectorImpl` delegates every call to `AsyncInjectorImpl` through
    `lang.sync_await`.
  - `omcore/sql/api/asyncs.py`: `Db`/`AsyncDb`, and `SyncToAsyncDb`.
  - `omllm/llm/backends/anthropic/messages/stream.py`: `http.manage_async_client(self._http_client)`. Only the
    client management is relevant; ignore its error translation and `omcore.resources` use.

### 0.2 Target layout

```
x/blobs/
  __init__.py              core public surface; never imports aws/
  stores.py                BlobStore, BlobWriter (sync)                                    existing, extended
  asyncs.py                AsyncBlobStore, AsyncBlobWriter                                 phase 1
  adapters.py              SyncToAsyncBlobStore, AsyncToSyncBlobStore                      phase 1
  caps.py dicts.py errors.py keys.py types.py                                              existing
  listings.py              shallow_list helper                                             phase 1
  manifests.py             ManifestStore (async-only)                                      phase 1
  prefixes.py              PrefixedBlobStore (async)                                       phase 1
  readers.py               BlobReader, open_blob_reader, iter_blob_chunks (async)          phase 1
  plans.py                 parallel ranged-get plan                                        phase 14
  local/                   LocalBlobStore (sync)                                           phase 3
    __init__.py paths.py locks.py fsyncs.py writers.py listings.py stores.py
    tests/ __init__.py test_paths.py test_locks.py test_local.py test_conformance.py
  aws/                     S3BlobStore (async); later ominfra/blobs/aws
    __init__.py
    restxml.py             generic REST-XML serde; later ominfra/clouds/aws                phase 8
    endpoints.py signing.py ops.py errors.py retries.py                                    phase 9
    transport.py writers.py stores.py                                                      phase 10
    streaming.py           aws-chunked body encoding + the streaming-request seam           phase 13
    uploads.py             S3 parallel upload plan                                         phase 14
    tests/
      harness.py           s3mock harness                                                  phase 11
      clients.py           HTTP client matrix + test-only store factories                  phase 11
      faults.py            FaultInjectingAsyncHttpClient                                   phase 11
      recording.py         RecordingAsyncHttpClient                                        phase 11
      streaming.py         BufferingStreamingSender                                        phase 13
      probe.py             capability probe entrypoint                                     phase 11
      test_*.py
  tests/
    runners.py             ScenarioRunner: sync_await+threads and asyncio flavours         phase 2
    conformance.py         BlobStoreConformance                                            phase 2
    faults.py              FaultInjectingBlobStore (async)                                 phase 2
    recording.py           RecordingBlobStore (async)                                      phase 2
    test_*.py
    lsm/                   the LSM, as test-support code (async-only)                      phase 4
      __init__.py varints.py records.py blocks.py ssts.py memtables.py iterators.py
      manifests.py options.py errors.py dbs.py readers.py gc.py scenarios.py
      tests/ __init__.py test_varints.py test_ssts.py test_iterators.py test_lsm.py test_gc.py
```

### 0.3 Ground rules

- Read `AGENTS.md`, `README.md` and `CODESTYLE.md` first. The rules that bite most here:
  - one import per line, and `from omcore import dataclasses as dc`
  - `lang.Abstract` rather than `abc.ABC`, and `check` rather than `assert` outside tests
  - a blank line after every docstring, and no em dashes
  - module names are single lowercase words
  - `tests` packages sit nearest the code they test
  - working implementations over mocks, no monkeypatching, and no sleeps in tests
- **Commands.** `x/` is **not** covered by `make fix check`. For everything under `x/blobs`, run:
  - `./python -m ruff check x/blobs` (add `--fix` for autofixes)
  - `./python -m mypy x/blobs`
  - `./python -m pytest x/blobs`
  
  For changes under `ominfra/` or `omcore/`, run `make fix check` and the relevant pytests. Before any commit, run
  `make fix gen check`.
- **Lite code:**
  - The lite modules touched here are `ominfra/clouds/aws/auth.py`, `omcore/http/clients/**` (except `httpx.py`) and
    `omcore/asyncs/asynclite/**` (except `anyio/`).
  - They need Python 3.8 syntax and typing (`ta.Optional`, `ta.List`, no `match`), may import only lite code, and
    their tests use unittest.
  - Never remove the marker.
  - After editing lite modules, run `make gen-amalg`: the scripts embed them.
  - Sanity-check imports under the 3.8 venv, e.g.
    `PYTHONPATH=. .venvs/8/bin/python -c 'import ominfra.clouds.aws.auth'`.
- **Codegen.** After touching `services.toml` or the codegen, run `make gen-aws` then `make gen-dataclass`. Never
  hand-edit generated modules, and never read `_dataclasses.py` files.
- **Which side each piece lives on:**
  - Pure backends are sync: `DictBlobStore`.
  - IO backends are async: `S3BlobStore`, which has no `Async` prefix because it has no sync twin.
  - `LocalBlobStore` is the deliberate exception: it is sync, with blocking filesystem calls. Don't use the in-tree
    async filesystem adapter.
  - Higher-level helpers are **async-only**: `ManifestStore`, `PrefixedBlobStore`, the readers, the plans, and the LSM.
  - **Never write sync/async pairs.** Crossing sides is done only with the two adapters
    (`SyncToAsyncBlobStore`, `AsyncToSyncBlobStore`) and `SyncAsyncHttpClient`.
- **No public convenience constructors** that do this wrapping, such as a function returning "a sync S3 store".
  Users compose the pieces themselves; in real code the dependency injector does it. Test-only factories under
  `tests/` are fine.
- **No asyncio in non-test code**, neither in interfaces nor implementations. Where an async primitive is needed, use
  `asynclite` (`from omcore.asyncs.asynclite import all as asl`). Only `SimpleS3RetryPolicy`'s sleeping needs one.
  Tests may use asyncio freely.
- **Async signatures.** Abstract async methods are declared `def f(...) -> ta.Awaitable[T]`. Async iterators are
  `-> ta.AsyncIterator[T]`, and async context managers are `-> ta.AsyncContextManager[T]`.
- **Layering.** The code will be promoted: core to `omcore/blobs`, `aws/` to `ominfra/blobs/aws`, and `restxml.py` to
  `ominfra/clouds/aws`. So:
  - Core (`x/blobs/*.py`, `x/blobs/local/**`) uses only the stdlib and omcore.
  - `x/blobs/aws/**` imports core as a package, `from ... import blobs`, and then uses `blobs.AsyncBlobStore`, etc.
    After the move that line becomes `from omcore import blobs`.
  - `x/blobs/aws/restxml.py` imports only the stdlib, omcore, `ominfra.clouds.aws.models.base` and `auth.py`. It never
    imports `x.blobs` and contains nothing S3-specific.
  - The LSM imports core relatively (`from ...asyncs import AsyncBlobStore`) and never imports `aws/`.
  - Core tests never import `x.blobs.aws`. S3 runs of shared scenarios live under `x/blobs/aws/tests/` and import the
    shared support modules.
- **Naming gotcha.** The store interfaces have a method named `list`. In any class body after `def list`, the bare
  name `list` means that method, including in later annotations. Use `ta.Sequence[...]` / `builtins.list` there.
- **Tests:**
  - Inject every `clock`, sleep and `random.Random`, and never sleep for real.
  - Line up races with barriers and events.
  - Keep each test well under the 60s pytest timeout, and mark heavy randomized variants `@pytest.mark.slow`.
  - Async code without real async machinery is tested with sync tests driven by `sync_await`, per the codestyle. See
    the runners in 2.1.
- **Sandbox:**
  - Start `~/scripts/run-s3mock` as a background task.
  - Point the harness at it with `OM_TEST_S3_URL=http://127.0.0.1:9090` (11.1).
  - s3mock tests are marked `integration` and fail, rather than skip, when s3mock isn't reachable, like the Postgres
    tests.
  - Live AWS/R2 tests skip when their secrets are missing; there are none in the sandbox.

### 0.4 Decisions (settled in review)

**Scope and structure**
- **S3 client:** only the internal client. boto is never used; botocore appears only in codegen and cross-validation
  tests.
- **Where things live:**
  - The AWS backend lives in `x/blobs/aws/`, with the class `x.blobs.aws.S3BlobStore`.
  - The REST-XML layer is its own module there, not in ominfra yet.
  - `ominfra.clouds.aws` may be expanded as needed: the signer, codegen metadata and `services.toml`.
- **`services.toml`:** add `UploadPart` (needed for multipart), plus `CreateBucket` and `DeleteBucket` (test setup).
- **Codegen** emits wire metadata (HTTP locations, method, request URI, XML traits), so the REST-XML module is generic
  rather than hand-mapped.

**Interfaces and async**
- **Interfaces:**
  - `BlobStore` / `BlobWriter` (sync) and `AsyncBlobStore` / `AsyncBlobWriter`.
  - Adapters `SyncToAsyncBlobStore` and `AsyncToSyncBlobStore`.
  - `DictBlobStore` and `LocalBlobStore` are sync, and `S3BlobStore` is async.
- **The LSM** is async-only and IO-pure: it only calls an `AsyncBlobStore`, and must work over
  `SyncToAsyncBlobStore(DictBlobStore())`.
- **Contract additions:** `delete_many`, and a pull-based `put_stream`, on both interfaces.
- **Local names:** the local backend escapes on-disk names unconditionally, never probing for case sensitivity. It
  uses `.file` / `.dir` suffixes.

**S3 behaviour**
- **Streamed uploads** are fully built but default off (`Config.streamed_uploads`). The one call that would send a
  streamed body to the HTTP client raises `NotImplementedError`, with a TODO and a sketch. Tests replace it with a
  buffering sender. The body API to assume is that `HttpClientRequest.data` also accepts an iterable or async iterable
  of bytes, `Content-Length` must be set, and chunked transfer encoding is never used.
- **`open_writer` buffers per part for now.** Keep that path isolated, because it has to change as soon as real
  streaming lands. A streaming writer will also need task spawning, which `asynclite` doesn't have yet.
- **Retries:** the store never sleeps or retries by default. There's an injectable `S3RetryPolicy`, and a simple
  implementation that takes `asl.Sleeps`. An ambiguous failure of a conditional write is never offered to the policy.
  A 503 SlowDown that isn't retried raises `BlobThrottledError`, a subclass of `BlobIndeterminateError`.
- **`S3BlobStore.Config`** has one field per behavioural axis:
  - Fields are named for what they do, never for a provider.
  - Defaults are AWS's, and are zero values where possible.
  - `R2_CONFIG` and `S3_MOCK_CONFIG` presets live next to the class.
  - Nowhere in the implementation does anything check `if backend == ...`.
- **Conditional copy** is off by default, with a comment explaining why. botocore's model lists it for AWS but it's
  unverified, and s3mock ignores it. Enabling it later is a one-line change to `capabilities`.
- **`S3BlobStore` takes `http_client: AsyncHttpClient | None = None`**, with no default set in `__init__`, and uses
  `async with http.manage_async_client(self._http_client)` per request.

**Testing**
- **No S3 emulator.** s3mock is a black box, like Postgres/MySQL. Transport faults are injected by wrapping the real
  HTTP client, and pure functions get canned-response unit tests.
- **The conformance suite is written once**, against `AsyncBlobStore`. S3 runs against s3mock on five real clients:
  sync pipelines, urllib and httpx, each through `SyncAsyncHttpClient`; and asyncio pipelines and async httpx.

**omcore and parallel plans**
- **omcore fixes:**
  - the two `asynclite` sync-lock bugs
  - `no_decompress` on **`HttpClientRequest`**, honoured by every client
  - wrapping body-read errors in `HttpClientError`: `TimeoutError`, `ConnectionError` and `http.client.IncompleteRead`
    for urllib, and `httpx.TransportError` for httpx
- **Parallel plans are side helpers**, not interface methods:
  - a generic ranged-get plan in core
  - an S3-only upload plan in `aws/`, with no generic upload fallback (the default; the user didn't object)

### 0.5 s3mock 5.2.3 behaviour (verified with curl, 2026-09-24)

**Behaves like AWS:**
- Conditional PutObject:
  - `If-None-Match: *` on an existing key gives 412.
  - A stale `If-Match` gives 412.
  - `If-Match` on a missing key gives **404 `NoSuchKey`**.
- Conditional GET and HEAD:
  - A stale `If-Match` gives 412, and `If-Match` on a missing key gives 404.
  - `If-None-Match` equal to the current version gives 304.
- DeleteObject `If-Match`: stale gives 412, missing gives 404.
- CompleteMultipartUpload honours both `If-None-Match: *` and `If-Match` (412).
- Ranges:
  - Any unsatisfiable range, including **any** range on an empty object, gives 416 `InvalidRange`.
  - A suffix longer than the object gives 206 with the whole object.
  - A range whose end is past the object's end is clamped (206).

**Differs from AWS; test against these on purpose:**
- **CopyObject silently ignores destination `If-None-Match` / `If-Match`.** It returns 200 and overwrites.
  `S3_MOCK_CONFIG` must never claim the copy capabilities.
- **Listings sort by UTF-16 code units**, so U+1F600 comes before U+E000. Xfail the astral-plane ordering test for
  s3mock only.
- **XML request bodies must carry `Content-Type: application/xml`**, otherwise it returns 400. Always send it.
- **`encoding-type=url` encodes a space as `%20`** where AWS uses `+`. Decoding with `unquote_plus` handles both.
- **More lenient than AWS**, so these paths are only really verified live:
  - DeleteObjects without `Content-MD5` is accepted.
  - `Transfer-Encoding: chunked` PUTs are accepted.
  - Signatures are never checked.
  - A repeated CompleteMultipartUpload after success returns 200.
- **It decodes `Content-Encoding: aws-chunked` bodies**, without checking their signatures, which is what makes the
  streaming tests in phase 13 possible.
- **Found during implementation:**
  - Its preconditions are **not atomic under racing writers**. Concurrent `If-None-Match: *` or same-etag `If-Match`
    PUTs can both succeed (reproduced with raw curl). The conformance race cases are xfailed for s3mock.
  - It enforces the 5 MiB minimum part size (`EntityTooSmall`), so S3 tests use 5 MiB parts.


## Phase 1: Core interfaces, adapters and contract

**Goal:** both interfaces, the two adapters, the contract fixes, and the async-only helpers, all tested over
`DictBlobStore`.

### 1.1 Interfaces

- [x] **`stores.py` (sync):** add to `BlobStore`:
  - `put_stream(key, source: ta.Iterable[bytes], *, length: int | None = None, cond=None) -> BlobVersion`
  - `delete_many(keys: ta.Iterable[str]) -> None`
- [x] **`asyncs.py`:** `AsyncBlobWriter` and `AsyncBlobStore`, mirroring the sync interfaces:
  - `capabilities() -> BlobCapability`, which stays sync because it does no IO
  - `head(...) -> ta.Awaitable[BlobInfo]` and `get(...) -> ta.Awaitable[Blob]`
  - `list(...) -> ta.AsyncIterator[BlobInfo]` and `list_shallow(...) -> ta.AsyncIterator[BlobInfo | BlobPrefix]`
  - `put(...) -> ta.Awaitable[BlobVersion]`
  - `put_stream(key, source: ta.AsyncIterable[bytes], *, length=None, cond=None) -> ta.Awaitable[BlobVersion]`
  - `open_writer(key, *, cond=None) -> ta.AsyncContextManager[AsyncBlobWriter]`
  - `copy(...) -> ta.Awaitable[BlobVersion]`
  - `delete(...) -> ta.Awaitable[None]`
  - `delete_many(keys: ta.Iterable[str]) -> ta.Awaitable[None]`
  
  `AsyncBlobWriter` has `write(data) -> ta.Awaitable[None]` and `commit() -> ta.Awaitable[BlobVersion]`.
- [x] **`put_stream` semantics (both interfaces):**
  - It consumes the whole source.
  - If `length` is given and doesn't match the byte total, it raises `ValueError` and publishes nothing.
  - The precondition is evaluated at the end, as `open_writer`'s commit does.
  - `DictBlobStore` buffers the source.

### 1.2 Adapters (`adapters.py`)

- [x] **`SyncToAsyncBlobStore(store: BlobStore)`** is an `AsyncBlobStore` that calls the sync store inline.
  - Listings are async generators over the sync iterator.
  - `open_writer` wraps the sync context manager and writer; use `SyncToAsyncContextManager` where it fits.
  - `put_stream` drains the async source into the sync store's `open_writer`.
  - A blocking store (`LocalBlobStore`) blocks the event loop for the duration of each call. That's intended for now;
    document it.
- [x] **`AsyncToSyncBlobStore(store: AsyncBlobStore)`** is a `BlobStore` built on `lang.sync_await`.
  - Listings use `lang.sync_aiter`, wrapped so that abandoning the sync iterator still closes the async generator
    (`sync_await(agen.aclose())` in a `finally`).
  - `open_writer` returns a sync context manager with a sync writer adapter.
  - `put_stream` wraps the sync iterable in an async generator that never suspends.
  - It only works when the wrapped store never actually suspends, e.g. an `S3BlobStore` given a
    `SyncAsyncHttpClient` (and a retry policy using the sync `asynclite` backend, if any). Otherwise `sync_await`
    raises `SyncAwaitCoroutineNotTerminatedError`. Document this; don't defend against it.
- [x] No convenience factories (0.3).

### 1.3 Fixes

- [x] **`DictBlobStore.open_writer`:** the yielded writer is still usable after the `with` exits. Mark it closed on
  exit. After that, `write` / `commit` on a closed or already-committed writer raise (`check.state`).
- [x] **`check_blob_key`:** also reject U+FFFE and U+FFFF, which are not XML 1.0 characters. Update the docstring:
  keys are what S3, R2, a POSIX filesystem **and XML 1.0** can all represent.
- [x] **Docstrings:**
  - `BlobVersion`: versions change when content changes, but may recur when identical content is rewritten; S3's
    single-part etag is the MD5 of the content. Never use `IfMatch` as a fencing token over content that can repeat.
  - `BlobInfo.last_modified`: always UTC-aware; its precision depends on the backend.
  - The store interfaces:
    - Listings are not snapshots.
    - Stores are thread-safe and writers are not.
    - Capability checks, key validation and preconditions' static checks all happen before any IO.

### 1.4 Contract additions

- [x] **`copy(src, dst)` with `src == dst`:** raise `ValueError` before any IO, on every backend.
- [x] **`errors.py`:**
  - `BlobTransportError(BlobStoreError)`: a read, or a request known not to have been applied, failed. Retrying is
    safe.
  - `BlobThrottledError(BlobIndeterminateError)`: the backend asked us to slow down and nothing retried.
  - `BlobDeleteManyError(BlobStoreError)`, with `errors: ta.Mapping[str, BlobStoreError]`.
- [x] **`delete_many`:**
  - It is unconditional, ignores missing keys, is not atomic, and makes no promise about order.
  - All keys are validated before any IO.
  - It attempts every key, then raises `BlobDeleteManyError` if any failed.
- [x] **`listings.py`:** move `DictBlobStore.list_shallow`'s algorithm into
  `shallow_list(infos, *, prefix, delimiter) -> ta.Iterator[BlobInfo | BlobPrefix]`, with
  `check.non_empty_str(delimiter)`.
- [x] **`DictBlobStore`:** implement `put_stream` and `delete_many`, and use `shallow_list`.

### 1.5 Async-only helpers

- [x] **`manifests.py`:** `ManifestStore(store: AsyncBlobStore, *, prefix, max_attempts=8)`, with every method async.
  - `iter_ids(*, after=None) -> ta.AsyncIterator[int]` (ascending); build `find_latest` on it.
  - `read(id)`, `commit(id, data)`, and `delete_ids(ids)` (via `delete_many`).
  - In `iter_ids`, use `s.isascii() and s.isdigit()`.
  - Validate the prefix at construction with `check_blob_key(self._key(0))`.
- [x] **`prefixes.py`:** `PrefixedBlobStore(store: AsyncBlobStore, prefix: str)`.
  - `prefix` must end with `/` and be a valid key prefix.
  - It maps keys in, strips the prefix from `BlobInfo.key` and `BlobPrefix.prefix` on the way out, and passes
    everything else through.
- [x] **`readers.py`:**
  - `open_blob_reader(store, key, *, version=None, block_size=1 << 20) -> ta.Awaitable[BlobReader]`.
    - It does the first ranged `get` immediately: `OffsetBlobRange(0, block_size)`, with `IfMatch(version)` if a
      version is given.
    - That response supplies `info`, so no HEAD is needed.
    - Every later get is pinned with `IfMatch(info.version)`, so a concurrent replace raises
      `BlobPreconditionFailedError` instead of producing a torn read.
  - `BlobReader`:
    - `read(n=-1) -> ta.Awaitable[bytes]`
    - `seek(pos, whence=0) -> int` and `tell() -> int`, both sync with no IO
    - an `info` property
  - `iter_blob_chunks(store, key, *, chunk_size, version=None) -> ta.AsyncIterator[bytes]`.
- [x] Update `__init__.py` exports.

### 1.6 Tests

Drive async code with `sync_await` over `SyncToAsyncBlobStore(DictBlobStore())`.

- [x] `test_adapters.py`:
  - both directions, and the round trip `SyncToAsyncBlobStore(AsyncToSyncBlobStore(SyncToAsyncBlobStore(dict)))`
  - abandoning a listing closes the async generator
  - writer semantics hold through both adapters
  - `put_stream` works through both, including a `length` mismatch
- [x] `test_listings.py`:
  - nested prefixes
  - a prefix without the delimiter
  - a non-`/` delimiter
  - a prefix that is itself a key
- [x] `test_prefixes.py`, `test_readers.py`:
  - sequential reads, `seek`/`tell`, and reads past the end
  - an empty object
  - a concurrent replace between blocks raises
  - the first read costs exactly one get
- [x] **`test_manifests.py`:** convert it to the async `ManifestStore`. Its `_TimeoutBlobStore` can stay for now,
  wrapped in `SyncToAsyncBlobStore`; phase 2 replaces it.
- [x] Extend `test_dicts.py` for the writer fix, `copy(k, k)`, `put_stream`, `delete_many` and the new invalid keys.

**Done when:** all `x/blobs` tests pass and ruff and mypy are clean on `x/blobs`.


## Phase 2: Test support and the conformance suite

**Goal:** one behavioural spec, written once against `AsyncBlobStore`, that every backend must pass, plus reusable
fault injection.

### 2.1 Runners (`x/blobs/tests/runners.py`)

- [x] `ScenarioRunner` is an interface, and must not be named `Test*`, or pytest will collect it:
  - `run(fn: ta.Callable[[], ta.Awaitable[T]]) -> T` drives one scenario to completion.
  - `gather(fns) -> ta.Awaitable[list[T | BaseException]]` is awaited *inside* a scenario to run operations
    concurrently.
- [x] `SyncAwaitScenarioRunner`:
  - `run` is `sync_await(fn())`.
  - `gather` starts one thread per function, each running `sync_await(fn())`, joins them, and returns the results in
    order. Blocking inside a coroutine is fine under `sync_await`.
  - Use it for sync-backed stores and for `SyncAsyncHttpClient`-backed S3.
- [x] `AsyncioScenarioRunner` (test-only asyncio):
  - `run` is `asyncio.run(fn())`, and `gather` is `asyncio.gather(..., return_exceptions=True)`.
  - Use it for real-loop clients.

### 2.2 `x/blobs/tests/faults.py`

- [x] `FaultInjectingBlobStore(AsyncBlobStore)` wraps a delegate by composition. Faults are scripted rules:

  ```python
  @dc.dataclass(frozen=True, kw_only=True)
  class BlobFault:
      op: str                                  # put, put_stream, get, head, list, copy, delete, delete_many, commit
      key: str | re.Pattern[str] | None = None  # None matches any key
      nth: int = 0                             # fire on the nth matching call
      after: bool = False                      # False: delegate not called; True: called, result discarded
      side_effect: ta.Callable[[AsyncBlobStore], ta.Awaitable[None]] | None = None  # e.g. a rival write, run first
      error: ta.Callable[[str], BaseException] = BlobIndeterminateError
  ```

  - Each fault fires once, and faults can be added mid-test.
  - `open_writer` wraps the delegate's writer so `commit` can be faulted.
  - The wrapper reports the delegate's capabilities.
- [x] Rewrite `test_manifests.py` in terms of it, replacing `_TimeoutBlobStore`:
  - "ours" = `after=True`
  - "nothing" = `after=False`
  - "theirs" = `after=False` with a `side_effect` that does a rival put

### 2.3 `x/blobs/tests/recording.py`

- [x] `RecordingBlobStore(AsyncBlobStore)` records `(op, key, byte_range, cond)` calls, for asserting request counts.

### 2.4 `x/blobs/tests/conformance.py`

- [x] `class BlobStoreConformance` is a plain base class, which pytest doesn't collect.
  - Each case is an `async def _scenario_*(self, store, runner)` plus a thin sync `test_*` that calls
    `runner.run(...)`.
  - Subclasses provide `store` and `runner` fixtures, where `store` is an **empty** `AsyncBlobStore` (a fresh instance,
    or a `PrefixedBlobStore` on a unique prefix).
  - Optional class attributes:
    - `concurrency = 8`
    - `large_size` (at least 2x the writer part size for S3)
    - `xfail_astral_ordering = False`
- [x] Capability-gated cases read `store.capabilities()`. A missing capability means skip, and using it must raise
  `UnsupportedBlobOperationError`.
- [x] **Enforcement cases** are the most valuable part. For every capability a backend claims, prove the backend
  actually rejects: two `IfAbsent` puts, a stale `IfMatch`, and so on. Fail with a clear message, e.g.
  `"backend claims PUT_IF_ABSENT but accepted a second IfAbsent put"`.
- [x] Race cases use `runner.gather`:
  - **IfAbsent race:** exactly one winner.
  - **CAS counter:** N workers each do M read-increment-`put(IfMatch)` loops, retrying on precondition or conflict
    errors. The final value is exactly N*M.
- [x] The full list of cases is in [Appendix B](#appendix-b-conformance-checklist).

### 2.5 Dict runs (`x/blobs/tests/test_conformance_dict.py`)

- [x] Run `SyncToAsyncBlobStore(DictBlobStore())` with `SyncAwaitScenarioRunner`, plus these variants:
  - restricted capabilities: `BlobCapability(0)` and `PUT_IF_ABSENT` only
  - over a `PrefixedBlobStore`
  - through the adapter round trip
  - under `AsyncioScenarioRunner`, which proves the adapter on a real loop

**Done when:** every dict variant passes the whole suite, and the manifest tests use `faults.py`.


## Phase 3: Local filesystem backend

**Goal:** `x.blobs.local.LocalBlobStore`, a **sync** `BlobStore` using blocking filesystem calls, with all the known
gotchas fixed. It runs the conformance suite through `SyncToAsyncBlobStore`.

### 3.1 On-disk layout (`paths.py`)

```
<root>/
  .tmp/                 in-flight writes: <uuid7 hex>.tmp        (never listed)
  .locks/               striped lock files: 00.lock .. ff.lock   (never listed, never deleted)
  <seg>.dir/            a key prefix segment
    <seg>.file          an object
```

- [x] Every key segment except the last becomes `<enc(seg)>.dir`, and the last becomes `<enc(seg)>.file`.
  - Keys `a/b` and `a/b/c` coexist as `a.dir/b.file` and `a.dir/b.dir/c.file`.
  - Decoding strips exactly one suffix, so no key needs rejecting. A segment like `x.file` becomes `x.file.file`.
  - Every read path ignores names that end in neither suffix.
- [x] **Segment encoding** `enc`, **unconditional**, with no probing for case sensitivity:
  - ASCII printable characters pass through, except `%` and `A`-`Z`.
  - Those, and every non-ASCII character, become lowercase `%xx` of their UTF-8 bytes.
  - The encoded name is pure lowercase ASCII, so it stays injective on case- and normalization-insensitive
    filesystems.
  - Decoding rejects malformed escapes and uppercase hex; such names are ignored as foreign.
- [x] **Limits:**
  - An encoded segment plus its suffix must fit in `NAME_MAX` (255 bytes). A longer one raises `InvalidBlobKeyError`
    before any IO.
  - `ENAMETOOLONG` from the OS also becomes `InvalidBlobKeyError`.
- [x] **API:** `encode_segment`, `decode_name(name) -> tuple[str, bool] | None` (segment, is_dir), and
  `key_to_path(key) -> tuple[ta.Sequence[str], str]`.
- [x] **Tests (`test_paths.py`):**
  - a seeded random unicode round trip
  - case-distinct keys map to distinct names
  - suffix-looking and escape-looking segments
  - the length limits
  - foreign names are ignored

### 3.2 Versions

- [x] The etag is `f'{st_ino:x}-{st_mtime_ns:x}-{st_size:x}'`, always taken from `fstat` of the fd actually read or
  written.
- [x] Inode numbers are reused and kernel timestamps are coarse. Before commit, stamp the tmp file with
  `os.utime(fd, ns=(t, t))`, where `t = time.time_ns()`. This requires a filesystem with nanosecond timestamps;
  document that.
- [x] `last_modified` is `st_mtime_ns` as a UTC datetime.
- [x] **Test:** rewrite one key with same-size content 1000 times. Every version is distinct, and each stale `IfMatch`
  fails.

### 3.3 Locks (`locks.py`)

- [x] `StripedFileLocks(dir_path, *, stripes=256)`:
  - `stripe = zlib.crc32(key.encode()) % stripes`, never `hash()`, since str hashing is randomized per process.
  - Lock files are created lazily and never deleted.
  - Acquire by opening the stripe file afresh and calling `fcntl.flock(fd, LOCK_EX)`; release by closing it. A fresh
    open per acquisition means flock excludes threads of the same process too.
- [x] Document that the root must be on a local filesystem, not NFS.
- [x] **Tests (`test_locks.py`):**
  - thread contention, shown with `LOCK_NB` probes plus an Event handshake
  - a subprocess holds a stripe, and the parent's non-blocking acquire fails until the child releases it

### 3.4 Writes

Put, `put_stream`, `open_writer` and copy share one commit path.

1. Create `<root>/.tmp/<uuid7 hex>.tmp` with `O_CREAT|O_EXCL|O_WRONLY|O_CLOEXEC`, and write the data into it.
   `put_stream` and the writer stream into it, so there's no buffering in memory.
2. At commit: stamp the mtime, `fsync` (unless `no_fsync`; use `F_FULLFSYNC` on darwin if `full_fsync`), and keep
   the fd open.
3. Ensure the parent `.dir`s exist with `os.mkdir` (`EEXIST` is fine), fsyncing each new directory's parent. Retry
   the ensure-and-commit on `ENOENT`, bounded to about 8 attempts, because a concurrent delete may prune a directory.
4. Commit according to the precondition:
   - `IfAbsent()`: `os.link(tmp, final)`. `EEXIST` raises `BlobAlreadyExistsError`. Take **no lock**: `link` is an
     atomic create-if-absent.
     - If hard links aren't supported (`EPERM` / `ENOTSUP`), fall back to: take the stripe lock, `lstat` the final
       path (it must be absent), then `os.replace`.
   - `None`: take the stripe lock, then `os.replace(tmp, final)`.
   - `IfMatch(v)`: take the stripe lock, open and `fstat` the final path (missing raises
     `BlobPreconditionFailedError`), compare etags, then `os.replace`.
   - Unconditional writes lock too. Otherwise an unconditional replace could land between an `IfMatch` writer's
     check and its replace.
5. `fsync` the parent directory, unlink the tmp name on the link path, and return the version from the tmp fd's
   `fstat`.
6. On any failure, unlink the tmp file (best-effort) and close the fd.

- [x] **Delete:**
  - Take the stripe lock.
  - For `IfMatch`, stat and compare; a missing key raises `BlobPreconditionFailedError`.
  - `os.unlink` (`ENOENT` is fine when unconditional), release the lock, and fsync the directory.
  - Then prune empty ancestor `.dir`s with `os.rmdir` up to the root, stopping at `ENOTEMPTY` / `ENOENT`.
- [x] **Copy:** open the source (missing raises `BlobNotFoundError(src)`), copy its bytes into a tmp file, and commit
  to `dst`. Never hard-link.
- [x] **`open_writer`:**
  - The tmp file is created at open.
  - `commit` runs steps 2-5.
  - Leaving the context without committing, or with an exception, unlinks the tmp file.
  - Calling `write` / `commit` after commit or after exit raises.
- [x] **`put_stream`:** stream into the tmp file, check `length`, then commit.
- [x] **`delete_many`:** a loop that collects errors.
- [x] **`remove_stale_tmp_files(*, older_than: datetime.timedelta, now: datetime.datetime | None = None) -> int`.**

### 3.5 Reads

- [x] Open with `os.open(final, O_RDONLY|O_CLOEXEC|O_NOFOLLOW)`:
  - `ENOENT` / `ENOTDIR` mean not found, or precondition failed under `IfMatch`.
  - Use `fstat` for `info` and precondition checks, and `os.pread` for (clamped) ranges.
- [x] Readers never lock. The fd pins the inode.

### 3.6 Listing (`local/listings.py`)

- [x] Start at the deepest directory fully determined by `prefix`, and filter the first level by the rest of the
  prefix.
- [x] Within each directory:
  - Map each entry to a sort key: files contribute `seg` and directories contribute `seg + '/'`.
  - Sort by that key and recurse in that order. This gives global code point order (`a` < `a-c` < `a/b`).
- [x] **`start_after`:**
  - Skip files whose key is `<= start_after`.
  - Skip a directory subtree with key prefix `d` when `start_after > d` and not `start_after.startswith(d)`.
- [x] **`list_shallow`:**
  - With `delimiter == '/'`, it is native. A directory yields a `BlobPrefix` only if its subtree contains at least one
    `.file`, found by a lazy walk.
  - With any other delimiter, use `shallow_list(self.list(...))`.

### 3.7 Class and config

```python
class LocalBlobStore(BlobStore):
    @dc.dataclass(frozen=True, kw_only=True)
    class Config:
        no_fsync: bool = False    # tests only
        full_fsync: bool = False  # darwin: F_FULLFSYNC
        lock_stripes: int = 256

    def __init__(self, root: str, *, config: Config | None = None) -> None: ...
```

- [x] No IO in `__init__`. The root must already exist, and `.tmp/` / `.locks/` are created lazily.
- [x] `capabilities()` is `ALL_BLOB_CAPABILITIES`.
- [x] The store is thread-safe. Put fsync helpers in `fsyncs.py`, and export `LocalBlobStore`.

### 3.8 Tests

- [x] `test_conformance.py`: `SyncToAsyncBlobStore(LocalBlobStore(tmp_path))` with `SyncAwaitScenarioRunner`, so
  races run as real threads against one store. Add a `no_fsync=True` variant.
- [x] `test_local.py`:
  - the exact on-disk layout
  - `a` and `a/b` coexist
  - `A` vs `a` stay distinct
  - stray files are ignored
  - empty directories are pruned and never reported
  - no tmp files remain after an abort
  - `remove_stale_tmp_files`
  - the version-churn loop
  - a reader holding an fd across a replace sees the old, consistent content
  - cross-process `IfAbsent` and CAS races with `multiprocessing` (spawn context; `slow` if needed)

**Done when:** local passes the full conformance suite plus its own tests.


## Phase 4: The LSM (async, over dict and local)

**Goal:** a deliberately simple LSM that works the blob abstraction the way real use will. It is **async-only and
IO-pure**: its only IO is calls on an `AsyncBlobStore`. It lives in `x/blobs/tests/lsm/` as test-support code, with
tests in `x/blobs/tests/lsm/tests/`. Keep it production-shaped, since it will be promoted soon.

**Scope:**
- one writer with fencing, and any number of snapshot readers
- `bytes` keys and values
- two levels: L0 (overlapping, newest first) and L1 (a single sorted, non-overlapping run)
- full compaction only

**Non-goals:**
- a WAL (only flushed data is durable, and `close()` flushes)
- bloom filters, and caching beyond a tiny block LRU
- background tasks

### 4.1 Blob layout under a db prefix `p`

- `p/manifest/<20-digit id>` via `ManifestStore(store, prefix=f'{p}/manifest')`
- `p/sst/<uuid7 hex>.sst`, written with `open_writer(key, cond=IfAbsent())`

### 4.2 SST format (`varints.py`, `records.py`, `blocks.py`, `ssts.py`)

- [x] **Varints:** unsigned LEB128.
- [x] **Record:** `varint(len(key)) key kind:u8 [varint(len(value)) value]`, where kind 0 is a put and 1 is a
  tombstone.
- [x] **Data block:** records in strictly increasing key order, up to about `block_size` (4 KiB by default; tests use
  about 64 bytes), followed by a `crc32` (u32 LE). An oversized record gets a block to itself.
- [x] **Index:** one entry per block, `varint(len(last_key)) last_key varint(offset) varint(length)`, followed by a
  `crc32`.
- [x] **Footer:** 40 bytes, `struct.Struct('<8sIQQQI')`: magic `b'OMLSMSST'`, version `1`, index offset, index length,
  entry count, and a `crc32` of the preceding 36 bytes.
- [x] **`SstWriter`:** it streams blocks into an `AsyncBlobWriter`, and `finish()` returns an `SstRef`. It never writes
  an empty SST.
- [x] **`SstReader.open(store, key, *, prefetch=64 * 1024)`:**
  - It does **one** `get(key, byte_range=SuffixBlobRange(prefetch))`. `info.size` locates the footer and index. If
    the index doesn't fit in the prefetched tail, it does exactly one more ranged get.
  - Every later block read is `IfMatch`-pinned.
  - `get(key)` bisects the index and reads one block.
  - `scan(start, end) -> ta.AsyncIterator` reads lazily, block by block.
  - It keeps a tiny decoded-block LRU.
- [x] A CRC mismatch or bad magic raises `LsmCorruptionError` (`errors.py`).

### 4.3 Manifest (`manifests.py`)

```python
@dc.dataclass(frozen=True, kw_only=True)
class SstRef:
    key: str
    min_key: bytes
    max_key: bytes
    size: int
    entries: int


@dc.dataclass(frozen=True, kw_only=True)
class LsmManifest:
    writer_id: str            # uuid7 hex, one per LsmDb instance
    epoch: int                # bumped when a writer takes over
    nonce: str                # uuid7 hex per commit: unique bodies, as ManifestStore's read-back requires
    l0: ta.Sequence[SstRef]   # newest first
    l1: ta.Sequence[SstRef]   # sorted, non-overlapping
```

- [x] Encode it as JSON with stdlib `json`, with explicit to/from-dict functions, base64 for `bytes`, and a
  `format: 1` field.

### 4.4 Writer (`dbs.py`, `memtables.py`, `iterators.py`, `options.py`)

- [x] **`LsmOptions`:** `memtable_max_bytes`, `block_size`, `sst_target_size`, `l0_compaction_trigger`,
  `prefetch_bytes`, `commit_conflict_retries`.
- [x] **`await LsmDb.open(store: AsyncBlobStore, prefix, *, options=None, clock=None)`:**
  - `ManifestStore` checks for `PUT_IF_ABSENT`.
  - With no manifests, bootstrap id 1 at epoch 1.
  - Otherwise take over by committing `latest + 1` with the same levels and `epoch + 1`, which fences any older writer.
  - On `ManifestConflictError`, retry, bounded.
- [x] **API**, every call async:
  - `put`, `delete`
  - `get -> bytes | None`
  - `scan(start=None, end=None) -> ta.AsyncIterator[tuple[bytes, bytes]]`, with `end` exclusive
  - `flush`, `compact`, and `close` (which flushes)
  - it is an async context manager
  
  It flushes automatically above `memtable_max_bytes`, and compacts automatically at `l0_compaction_trigger`.
- [x] **Commit protocol:** `ManifestStore.commit(self._manifest_id + 1, body)`.
  - `ManifestConflictError`: read the latest manifest. If it isn't ours, mark the db fenced and raise
    `LsmFencedError`, now and on every later call.
  - `BlobConflictError`: retry up to `commit_conflict_retries` times.
  - `BlobIndeterminateError`: mark the db broken. Every later call raises `LsmBrokenError`.
  - SSTs from a failed commit are orphans that GC collects after the grace period.
- [x] **Flush:** write the memtable as one L0 SST, commit with it prepended to `l0`, then clear the memtable.
- [x] **Compact:** merge L0 (newest first) with L1, keep the newest version of each key, drop tombstones, split into
  SSTs of about `sst_target_size`, then commit `l0=[]` with the new `l1`.
- [x] **Reads:**
  - `get` checks the memtable, then L0 in order, then L1 (bisect on `max_key`).
  - `scan` is an async k-way merge (`iterators.merge_newest_wins`) keeping the newest entry per key and dropping
    tombstones.

### 4.5 Readers (`readers.py`)

- [x] `await LsmReader.open(store, prefix, *, manifest_id=None)` has async `get`, `scan` and `refresh()`. A GC'd SST
  raises `LsmSnapshotExpiredError`.

### 4.6 GC (`gc.py`)

- [x] `await collect_garbage(store, prefix, *, keep_manifests: int, sst_grace: datetime.timedelta, now:
  datetime.datetime) -> GcStats` runs these steps in order:
  1. Retain the newest `keep_manifests` ids (at least 1).
  2. The referenced set is the SST keys of every retained manifest.
  3. `delete_ids` every older manifest.
  4. `delete_many` every SST under `p/sst/` that is unreferenced **and** has `last_modified < now - sst_grace`.
- [x] Document why the grace period matters (writers upload SSTs before their commit lands) and that readers must
  refresh within the retention window.

### 4.7 Scenarios and tests

- [x] `x/blobs/tests/lsm/scenarios.py` is a seeded, model-based scenario runner parameterized by a store factory and a
  `ScenarioRunner`:
  - It checks `LsmDb` and `LsmReader` against a dict model.
  - Operations: put, delete, get, scan over a random range, flush, compact, reopen, open a reader, check a reader.
  - It uses small sizes to force many SSTs and compactions.
  - `aws/tests/` reuses it.
- [x] `test_varints.py`, `test_iterators.py`, `test_ssts.py`:
  - round-trips across block boundaries
  - oversized values
  - opening costs one get, or two when the index doesn't fit the prefetch (via `RecordingBlobStore`)
  - corruption is detected
  - every block read is `IfMatch`-pinned
- [x] `test_lsm.py` runs over `SyncToAsyncBlobStore(DictBlobStore())` and
  `SyncToAsyncBlobStore(LocalBlobStore(tmp_path, no_fsync))`, with `SyncAwaitScenarioRunner`:
  - [x] **Model test:** a handful of seeds by a few hundred ops each, plus a `slow` variant.
  - [x] **Fencing:**
    - A opens, then B takes over.
    - A's next flush raises `LsmFencedError`.
    - B sees none of A's unflushed data.
    - A's orphan SST is collected, but only after the grace period.
  - [x] **Indeterminate commits:** use `FaultInjectingBlobStore` on the manifest key with the ours / nothing / theirs
    cases. Reopening always yields exactly the last acknowledged flush.
  - [x] **Crash between SST upload and commit:** the data is absent after reopening, and the SST is an orphan that is
    collected only after the grace period.
  - [x] **Snapshot isolation:** a pinned reader keeps returning old values while the writer flushes and compacts. After
    GC plus the grace period, it raises `LsmSnapshotExpiredError`.
  - [x] **Capabilities:** `SyncToAsyncBlobStore(DictBlobStore(capabilities=BlobCapability(0)))` fails at open.
  - [x] **Concurrency smoke test:**
    - Readers scan while the writer flushes and compacts and GC runs.
    - Run it both with threads and on a real loop (`AsyncioScenarioRunner` over `SyncToAsyncBlobStore(dict)`).
    - Every scan result equals some committed state.
- [x] `test_gc.py`:
  - exact grace boundaries with a fake clock
  - SSTs of retained manifests are never deleted
  - `keep_manifests=1`
  - an empty prefix is a no-op

**Done when:** the LSM passes over dict and local on both runners, and the `slow` variant passes when run alone.


## Phase 5: omcore prerequisites

**Goal:** the small omcore fixes and additions the S3 work depends on. All of this is lite code apart from
`httpx.py`: keep 3.8 compatibility, use unittest for lite tests, and run `make gen-amalg`, `make fix check` and the
3.8 import check afterwards.

### 5.1 `asynclite` sync lock bugs (`omcore/asyncs/asynclite/sync/locks.py`)

- [x] `acquire(timeout=<positive>)` calls `self._u.acquire(blocking=False, timeout=...)`, which always raises
  `ValueError`. Fix it.
- [x] `acquire(timeout=0)` falls into the blocking branch and waits forever. It must be a single non-blocking attempt
  that raises `TimeoutError` on failure. Match the asyncio backend, which uses `wait_for`.
- [x] Semantics: `None` waits forever; `<= 0` is one non-blocking attempt; a positive value waits up to that long.
  Anything that fails raises `TimeoutError`.
- [x] Add cases to `omcore/asyncs/asynclite/sync/tests/test_locks.py` (`SyncIsolatedAsyncTestCase`): a held lock with
  timeout 0, a small positive timeout, and an uncontended acquire with a timeout. Keep other `asynclite` changes to
  zero.

### 5.2 `HttpClientRequest.no_decompress`

- [x] Add `no_decompress: bool = False` as a trailing field on `HttpClientRequest`, and include it in the `AttrOps`
  repr. When set, the client must hand back the response body exactly as received, with no `Content-Encoding`
  decoding.
- [x] **Pipeline clients** build a pipeline per request, so omit `IoPipelineHttpResponseDecompressor` from that
  request's pipeline spec. This covers both the sync and the asyncio client, via `pipelines/base.py`.
- [x] **httpx:** read with `resp.iter_raw()` / `resp.aiter_raw()` instead of `iter_bytes()` / `aiter_bytes()` when the
  flag is set. No constructor flag is needed.
- [x] **urllib** never decodes, so the flag is already honoured. Note that in a comment.
- [x] The redirect middleware uses `dc.replace`, which keeps the field. Add a test proving that.
- [x] **Tests:** a loopback server returning a gzip body with `Content-Encoding: gzip`. For each client, with the flag
  the raw gzip bytes come back; without it, the decoded bytes come back (except urllib, which always returns raw).
  Model the server on `ResettingLoopbackHttpServer` in `omcore/http/clients/pipelines/tests/test_transport_errors.py`.

### 5.3 Body-read error wrapping

- [x] **urllib:** wrap the response stream's reads so that `TimeoutError`, `ConnectionError` and
  `http.client.IncompleteRead` raised during a body read become `HttpClientError` (`raise ... from e`). Catch exactly
  that whitelist, never a blanket `except Exception`.
- [x] **httpx, sync and async:** wrap `httpx.TransportError`, httpx's own base class for timeouts, network errors and
  protocol errors, raised while iterating the body, the same way.
- [x] **Tests:** extend the mid-body reset tests to urllib and httpx. Non-lite httpx tests go in
  `omcore/http/clients/tests/`.

**Done when:** the new omcore tests pass, `make gen-amalg` has been run, `make fix check` is clean, and the 3.8 import
check passes.


## Phase 6: SigV4 signer fixes and streaming chunk signing

**Goal:** make `ominfra/clouds/aws/auth.py` correct for S3 and plug the streaming TODO. It is **lite**. Keep `logs.py`
/ `journald2aws` and the existing `test_auth.py` expectations working. Both existing cases use path `/` and at most one
query parameter, so they must not change.

### 6.1 Canonicalization

- [x] Add `aws_uri_encode(s: str, *, encode_slash: bool) -> str`, AWS's `UriEncode`:
  - Leave unreserved `A-Za-z0-9-_.~` alone, and uppercase the hex in everything else.
  - It is a public helper: `restxml.py` and `endpoints.py` must build URLs with exactly this encoding.
- [x] **Canonical URI:**
  - An empty path becomes `/`.
  - Split on `/`, `urllib.parse.unquote` each segment, then `aws_uri_encode(seg, encode_slash=True)` it.
  - **S3** encodes once and never normalizes. Other services encode the already-encoded path again.
- [x] **Canonical query** (the `!!` TODO):
  - Split on `&`, dropping empty parts, and partition each on `=`. A valueless key becomes `key=`.
  - Decode with `unquote`, **never** `unquote_plus` or `parse_qsl`.
  - Re-encode name and value with `aws_uri_encode(..., encode_slash=True)`, and sort by `(name, value)`.
- [x] **Header values:** trim them and collapse internal runs of spaces when canonicalizing.

### 6.2 Payload hash modes and session tokens

- [x] Add constants `UNSIGNED_PAYLOAD = 'UNSIGNED-PAYLOAD'` and
  `STREAMING_PAYLOAD = 'STREAMING-AWS4-HMAC-SHA256-PAYLOAD'`.
- [x] Add `sign(..., payload_hash: ta.Optional[str] = None)`. It overrides the computed hash, and signs and returns
  `x-amz-content-sha256`.
- [x] Add `AwsSigner.Credentials.session_token: ta.Optional[str] = dc.field(default=None, repr=False)`. When set,
  `x-amz-security-token` is signed and returned.
- [x] Refactor so the signing key, scope, timestamp and signature come from an internal helper the chunk signer can use.

### 6.3 Streaming (aws-chunked) chunk signing

- [x] **`V4AwsSigner.sign_streaming(req, *, decoded_length, chunk_size, utcnow=None) -> tuple[headers,
  V4AwsChunkSigner]`.** `req.payload` must be empty. It signs the seed request with:
  - `payload_hash=STREAMING_PAYLOAD`
  - `Content-Encoding: aws-chunked`
  - `x-amz-decoded-content-length`
  - `Content-Length`: the encoded length
- [x] **`V4AwsChunkSigner`:**
  - `sign_chunk(data) -> bytes` returns the framed chunk `hex(len);chunk-signature=<sig>\r\n<data>\r\n`.
    - Its string-to-sign is `AWS4-HMAC-SHA256-PAYLOAD\n<ts>\n<scope>\n<prev_sig>\n<sha256('')>\n<sha256(data)>`.
    - The previous signature starts as the seed signature.
  - `final_chunk() -> bytes` is `0;chunk-signature=<sig>\r\n\r\n`.
  - It enforces that every chunk except the last is at least 8 KiB, and that the byte total equals `decoded_length`.
- [x] Add `aws_chunked_encoded_length(decoded_length, chunk_size) -> int`: each n-byte chunk costs
  `len(f'{n:x}') + 17 + 64 + 4 + n`, and the final chunk adds 86.
- [x] Add `aws_chunked_encode(data, *, signer, chunk_size) -> bytes` for tests and small bodies. The async streaming
  encoder lives in `x/blobs/aws/streaming.py` (phase 13).

### 6.4 Tests

- [x] Keep `test_auth.py` passing unchanged.
- [x] **botocore cross-validation** (skipped if botocore can't be imported):
  - Build matching `AWSRequest`s, set `request.context['timestamp']`, add the headers botocore would add yourself
    (don't monkeypatch its clock), and compare against `S3SigV4Auth` and `SigV4Auth` via their public
    `canonical_request` / `string_to_sign` / `signature` methods. Compare canonical requests first.
  - Cover:
    - awkward keys (space, `+`, `%`, `~`, `!*'()`, `=`, `&`, `#`, `?`, unicode, `%2F`, trailing `/`)
    - unsorted, repeated and valueless query params
    - a continuation token containing `+`, `/` and `=`
    - header whitespace
    - `UNSIGNED-PAYLOAD`
    - a session token
- [x] **Official streaming vector:** transcribe the worked "PUT Object" example from the AWS
  [sigv4-streaming](https://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-streaming.html) page: the seed signature and
  every chunk signature. Never invent values. If the page can't be fetched, skip the test with a clear reason and
  record it in handoff notes.
- [x] `aws_chunked_encoded_length` equals `len(aws_chunked_encode(...))` around the chunk boundaries.
- [x] Run `make gen-amalg`, check the 3.8 import, then `make fix check`.

**Done when:** every signer test passes, the amalgamated scripts are regenerated, and `make fix check` is clean.


## Phase 7: AWS model codegen: wire metadata

### 7.1 `services.toml`

- [x] Add `UploadPart`, `CreateBucket` and `DeleteBucket` to `[services.s3]`.

### 7.2 Runtime metadata (`models/base/base.py`)

- [x] Add field markers, and the matching `field_metadata(...)` kwargs, emitted only when present:
  - `LOCATION`: `'uri' | 'querystring' | 'header' | 'headers' | 'statusCode'`. Absent means the body.
  - `XML_NAMESPACE`, `XML_FLATTENED`, `XML_ATTRIBUTE`
  - `LIST_MEMBER_NAME`: the item element name of a non-flattened list
  - `TIMESTAMP_FORMAT`
  - `STREAMING`
- [x] Add shape-level `payload_member` (a member name) through `Shape.__init_subclass__` / `shape_metadata`, and a
  `ShapeInfo.payload_field` property.
- [x] Add optional fields to `Operation`: `http_method`, `http_request_uri` and `http_response_code`.

### 7.3 Generator (`models/gen/gen.py`)

- [x] Emit all of the above from botocore's `member.serialization`, `shape.serialization['payload']` and
  `operation.http`.
- [x] Fix the map value-type bug: `shape.key.name` is used where `shape.value.name` is meant. It currently produces
  `Metadata: ... Mapping[MetadataKey, MetadataKey]`.
- [x] Regenerate with `make gen-aws` then `make gen-dataclass`. Check that `ominfra/clouds/aws/instancetypes` still
  unmarshals.

### 7.4 Tests

- [x] Add `ominfra/clouds/aws/models/services/tests/test_s3_metadata.py`, skipped without botocore. For every S3 shape
  field and every S3 operation, assert that the emitted metadata equals botocore's model.

**Done when:** `make gen` produces the metadata, the cross-check passes, and `make fix check` is clean.


## Phase 8: REST-XML protocol module

**Goal:** `x/blobs/aws/restxml.py`, a generic, sans-IO REST-XML serde driven entirely by the phase 7 metadata. It
imports only the stdlib, omcore, `ominfra.clouds.aws.models.base` and `auth.aws_uri_encode`, and contains nothing
S3-specific.

### 8.1 API

```python
@dc.dataclass(frozen=True, kw_only=True)
class RestXmlRequest:
    method: str
    path: str                                       # percent-encoded, starts with '/', uri labels expanded
    query: ta.Sequence[tuple[str, str | None]]      # decoded pairs; None value = valueless key ('uploads')
    headers: ta.Sequence[tuple[str, str]]
    body: bytes | None


@dc.dataclass(frozen=True, kw_only=True)
class RestXmlError:
    status: int
    code: str | None
    message: str | None
    request_id: str | None
    host_id: str | None
    raw: bytes


def serialize_rest_xml_request(op: Operation, req: Shape) -> RestXmlRequest: ...
def deserialize_rest_xml_response(op: Operation, *, status: int, headers: HttpHeaders, body: bytes) -> Shape: ...
def parse_rest_xml_error(*, status: int, headers: HttpHeaders, body: bytes) -> RestXmlError: ...
```

A streamed payload never passes through here. The S3 layer sends the payload body itself, and `serialize` leaves
`body=None` when the blob payload field is None.

### 8.2 Serialization

- [x] **URI labels:**
  - `{Name}` becomes `aws_uri_encode(v, encode_slash=True)`.
  - The greedy `{Name+}` becomes `aws_uri_encode(v, encode_slash=False)`.
  - The request URI's static query is merged into `query`.
- [x] **querystring members:** scalars are stringified, `bool` becomes `'true'`/`'false'`, lists repeat the key, and
  maps become pairs.
- [x] **header members:** the same scalar rules. `headers` maps emit `<prefix><key>`. Timestamps are generated as
  `str`, so pass them through verbatim.
- [x] **Payload:**
  - A blob payload is the raw body.
  - A structure payload becomes XML: the root is the member's serialization name (or its shape name), with `xmlns`
    when a namespace is set.
  - Flattened lists repeat the element; wrapped lists use `LIST_MEMBER_NAME` (default `member`).
- [x] Raise `NotImplementedError` for non-payload body members, which S3 doesn't use.

### 8.3 Deserialization

- [x] Fill header members, `headers` prefix maps and `statusCode` members.
- [x] A payload member is either a blob (the whole body) or a structure (parse the root as that shape). Otherwise
  parse the XML root's children into the output shape. An empty body gives an output built from headers only.
- [x] **Types:**
  - Resolve field types via `omcore.reflect`, as `models/base/_marshal.py` does, caching per shape.
  - Unwrap `NewType` and `Optional`.
  - Handle scalars, nested shapes, and flattened or wrapped lists.
  - Timestamps stay `str`.
  - Unknown elements are ignored.
- [x] Use `xml.etree.ElementTree` and strip namespaces. `parse_rest_xml_error` reads
  `<Error><Code/><Message/><RequestId/><HostId/>`.

### 8.4 Tests (`aws/tests/test_restxml.py`)

- [x] **botocore cross-validation of serialization:**
  - Use `create_serializer('rest-xml', include_validation=False).serialize_to_request(params, op_model)`.
  - Cover every S3 operation in `ALL_OPERATIONS` with representative params.
  - Compare the XML semantically.
- [x] **botocore cross-validation of parsing:** `create_parser('rest-xml').parse(...)` on canned responses. Use the
  AWS docs' example bodies for ListObjectsV2 (with and without CommonPrefixes), CopyObject, CreateMultipartUpload,
  CompleteMultipartUpload, DeleteObjects (with errors) and ListMultipartUploads, plus header-only responses.
- [x] Golden tests for errors: an XML error body, an empty-body 404, and a body that isn't XML.

**Done when:** cross-validation passes for every S3 operation.


## Phase 9: S3 request layer (sans-IO)

**Goal:** everything between "a blob call" and "an HTTP request or response", as pure functions. There's no IO and
no `Config` object here: the functions take explicit parameters, and `S3BlobStore` passes its config values in.

### 9.1 Endpoints (`endpoints.py`)

```python
@dc.dataclass(frozen=True, kw_only=True)
class S3Endpoint:
    url: str                    # scheme://host[:port], no path
    region: str
    virtual_hosted: bool = False
```

- [x] `build_url(endpoint, bucket, rx: RestXmlRequest) -> tuple[str, str]` returns the url and the Host header.
  - **Path style** is `url + rx.path`.
  - **Virtual style** puts the bucket in the host and strips the leading `/{bucket}` (keeping at least `/`). It is
    valid only for DNS-compatible bucket names without dots over https; otherwise raise at construction.
  - The query is encoded with `aws_uri_encode`, sorted like the signer sorts it, with valueless keys emitted bare.
- [x] Always compute an explicit `Host`: the signer signs it and the client sends it.
- [x] Path style is the default because it works on AWS, R2 and s3mock alike.

### 9.2 Signing (`signing.py`)

- [x] `S3RequestSigner(credentials, region, *, clock)` wraps `V4AwsSigner(creds, region, 's3')`. It turns a
  `RestXmlRequest`, url, host and body into an `HttpClientRequest`:
  - `method` is always explicit.
  - `Host` is set explicitly.
  - `Content-Length` is always set for PUT and POST, including `0`.
  - `Content-Type: application/xml` goes on XML bodies; s3mock requires it.
  - `Content-MD5` goes on DeleteObjects.
  - `x-amz-content-sha256` is the real hash, or `UNSIGNED-PAYLOAD` when `unsigned_payload` is set and the scheme is
    https.
  - Extra headers are signed like any other.
- [x] GETs of object data set `no_decompress=True`.

### 9.3 Operations (`ops.py`)

- [x] For each blob operation, write a pure **build** function (blob arguments to generated request shape plus extra
  headers) and a pure **interpret** function (output shape or error to blob result or blob error). One per operation:
  head, get, list page, put, create/upload/complete/abort multipart, copy, delete, delete-many batch, list multipart
  uploads page.
- [x] **Ranges:**
  - `OffsetBlobRange(a, b)` becomes `bytes=a-(b-1)`, and `OffsetBlobRange(a)` becomes `bytes=a-`.
  - `OffsetBlobRange(0)` sends no Range header.
  - `SuffixBlobRange(n)` becomes `bytes=-n`.
- [x] **Range responses:** a 206 takes its size from `Content-Range`. A 200 to a ranged request means the server
  ignored the Range, so slice locally.
- [x] **ETags** are opaque but normalized to the quoted form. Send them back verbatim.
- [x] **Timestamps:** the `Last-Modified` header goes through `email.utils.parsedate_to_datetime`, and XML goes through
  `datetime.fromisoformat`. Both become UTC.
- [x] **Listing keys:**
  - Unless `no_list_url_encoding` is set, request `encoding-type=url` and decode `Key`, `Prefix`, `StartAfter` and
    `Delimiter` with `unquote_plus`.
  - Skip, with a debug log, any key that fails `check_blob_key`.
- [x] **Copy destination conditions** use whatever header names the caller passes in (from config), so there's no
  provider branching here.

### 9.4 Errors (`errors.py`)

- [x] `S3ResponseError(blobs.BlobStoreError)` has `status`, `code`, `message`, `request_id` and `host_id`.
- [x] **200-with-error:** CopyObject, CompleteMultipartUpload and UploadPartCopy can return 200 with an `<Error>` body.
  Check the root element, and treat it like the equivalent error status.
- [x] `classify_failure(...) -> S3FailureKind`:
  - `READ_FAILED`
  - `NOT_APPLIED`: 409 `ConditionalRequestConflict`, a refused connection or DNS failure
  - `THROTTLED`: 503 `SlowDown`
  - `AMBIGUOUS`: timeouts after connecting, dropped connections, other 5xx
  - `TERMINAL`: everything else

### 9.5 Retry policy (`retries.py`)

- [x] The interface, and the failure record it receives:

  ```python
  @dc.dataclass(frozen=True, kw_only=True)
  class S3Failure:
      op: str
      attempt: int                 # 1-based
      kind: S3FailureKind
      conditional: bool
      status: int | None
      code: str | None
      cause: BaseException | None


  class S3RetryPolicy(lang.Abstract):
      @abc.abstractmethod
      def should_retry(self, failure: S3Failure) -> ta.Awaitable[bool]:
          """May sleep before returning True."""

          raise NotImplementedError
  ```

- [x] **The invariant, enforced by the store and not the policy:** `AMBIGUOUS` failures of conditional writes are
  **never** offered; they always raise `BlobIndeterminateError`. `TERMINAL` failures are never offered either.
- [x] `SimpleS3RetryPolicy(sleeps: asl.Sleeps, *, max_attempts: int = 5, base_delay_s: float = .05, max_delay_s:
  float = 2., rng: random.Random | None = None, no_throttled: bool = False)` retries everything it's offered, using
  full-jitter exponential backoff.
- [x] With no policy (the default), the store never retries or sleeps. On the first failure:
  - `READ_FAILED` raises `BlobTransportError`.
  - `NOT_APPLIED` raises `BlobConflictError` for a 409, and `BlobTransportError` otherwise.
  - `THROTTLED` raises `BlobThrottledError`.
  - An `AMBIGUOUS` unconditional write raises `BlobIndeterminateError`.

### 9.6 Tests

- [x] `test_endpoints.py`:
  - both addressing styles
  - host with and without port
  - bucket-name validation
  - awkward keys
- [x] `test_signing.py`: golden `HttpClientRequest`s per operation with a fixed clock, cross-checked against
  botocore's `S3SigV4Auth` `Authorization` header.
- [x] `test_ops.py`: interpret functions over canned responses, one per row of Appendix A.
- [x] `test_retries.py`: `SimpleS3RetryPolicy` backoff sequences, using a recording fake `asl.Sleeps` that never really
  sleeps; exhaustion; and `no_throttled`.

**Done when:** every build, interpret and retry path is covered, with no IO anywhere in this phase.


## Phase 10: S3BlobStore

**Goal:** `x.blobs.aws.S3BlobStore`, an **async** `AsyncBlobStore` driving the phase 9 functions over a
caller-provided `AsyncHttpClient`. Its behaviour tests run against s3mock (phase 11). This phase adds the code and its
unit-level tests.

### 10.1 Construction and config (`stores.py`)

```python
class S3BlobStore(blobs.AsyncBlobStore):
    @dc.dataclass(frozen=True, kw_only=True)
    class Config:
        # AWS S3 as of 2026-09. The copy capabilities are off: botocore's model lists If-Match / If-None-Match on
        # CopyObject, but it's unverified live, and s3mock ignores them. Enable after the live conformance run passes.
        capabilities: blobs.BlobCapability = (
            blobs.BlobCapability.PUT_IF_ABSENT |
            blobs.BlobCapability.PUT_IF_MATCH |
            blobs.BlobCapability.DELETE_IF_MATCH
        )

        copy_dst_if_none_match_header: str = 'If-None-Match'
        copy_dst_if_match_header: str = 'If-Match'

        no_list_url_encoding: bool = False
        unsigned_payload: bool = False
        streamed_uploads: bool = False             # phase 13

        part_size: int = 8 * 1024 * 1024
        streaming_chunk_size: int = 64 * 1024
        list_page_size: int = 1000
        delete_batch_size: int = 1000
        request_timeout_s: float = 60. * 60.      # omcore.http: an absolute deadline, including the body

    def __init__(
            self,
            *,
            bucket: str,
            endpoint: S3Endpoint,
            credentials: AwsSigner.Credentials,
            config: Config | None = None,
            http_client: AsyncHttpClient | None = None,
            retry_policy: S3RetryPolicy | None = None,
            streaming_sender: S3StreamingSender | None = None,   # phase 13
            clock: ta.Callable[[], datetime.datetime] | None = None,
    ) -> None: ...


# Below the class:
R2_CONFIG = S3BlobStore.Config(...)       # phase 12
S3_MOCK_CONFIG = S3BlobStore.Config(...)  # never the copy capabilities; see 0.5
```

- [x] `if config is None: config = self.Config()`. The default config is AWS S3.
- [x] Don't set a default HTTP client. Every request does
  `async with http.manage_async_client(self._http_client) as cli:`. Don't defend against callers who pass nothing
  outside an event loop.
- [x] Validate `part_size` (at least 5 MiB) and the part-count limit (10,000; `write` raises past it).
- [x] Nothing in the implementation branches on which provider it is talking to. Every difference is a `Config` field.

### 10.2 Transport (`transport.py`)

- [x] `S3Transport.execute(op, request_shape, *, conditional: bool, read: bool, body=..., extra_headers=()) -> output
  shape`. It builds and signs the request, sends it through the managed client, parses 200-with-error bodies,
  classifies failures (9.4), and consults the retry policy (9.5).
- [x] Treat `HttpClientError` as a transport failure. Use its `.cause` to tell a refused connection or DNS failure
  (`NOT_APPLIED`) from everything else (`AMBIGUOUS`). Check how each client surfaces connect-phase timeouts.
- [x] A 501 `NotImplemented` for a conditional header raises `blobs.UnsupportedBlobOperationError`.
- [x] Every request sets `timeout_s=config.request_timeout_s`.

### 10.3 Methods

Run capability checks, key validation and the `copy(k, k)` rejection before any IO.

- [x] **head / get:**
  - Send conditions as headers.
  - A 416 on get becomes a HEAD with the same condition, returning `Blob(info, b'')`.
  - The size comes from `Content-Range` or `Content-Length`.
- [x] **list / list_shallow:**
  - Paginate lazily as an async generator. Send `start-after` on the first page only, then `continuation-token`.
  - For `list_shallow`, merge `Contents` and `CommonPrefixes` per page with `heapq.merge`, and drop a prefix repeated
    across pages.
- [x] **put:**
  - PutObject. `IfAbsent` sends `If-None-Match: *`, and `IfMatch` sends `If-Match: <etag>`.
  - The version comes from the response `ETag`.
- [x] **put_stream** (immediate mode):
  - Read the source up to `part_size`. If it runs out first, do one put with the condition.
  - Otherwise use the same buffered multipart path as the writer.
  - Check `length` if given.
  - Streamed mode is phase 13.
- [x] **copy:**
  - CopyObject with `x-amz-copy-source: /{bucket}/{aws_uri_encode(src, encode_slash=False)}`.
  - Destination conditions go in `config.copy_dst_if_none_match_header` / `config.copy_dst_if_match_header`.
  - The version comes from `CopyObjectResult/ETag`.
  - With an `IfMatch` destination condition, a 404 is ambiguous. HEAD the source to tell a missing source from a
    missing destination.
  - Sources over 5 GiB raise `UnsupportedBlobOperationError`, with a TODO.
- [x] **delete:** DeleteObject with an optional `If-Match`. 204 means success.
- [x] **delete_many:** DeleteObjects in batches of `delete_batch_size`, in quiet mode, collecting per-key errors into
  `BlobDeleteManyError`.
- [x] **Maintenance:** `abort_stale_uploads(*, prefix='', older_than: datetime.timedelta) -> ta.Awaitable[int]` pages
  through ListMultipartUploads and aborts old uploads. The README should recommend the bucket lifecycle rule
  `AbortIncompleteMultipartUpload` as the real backstop.

### 10.4 Writer (`writers.py`)

- [x] **Buffered per part, for now.**
  - Buffer up to `part_size`.
  - Start the multipart upload lazily, only once the first full part exists, then send each full part with
    UploadPart. Parts are always exactly `part_size` except the last, which satisfies R2's uniform-size rule
    automatically.
  - On `commit()`:
    - If no upload was started, do a single PutObject with the precondition.
    - Otherwise upload the final part (never an empty one) and send CompleteMultipartUpload with the precondition
      headers.
  - Leaving the context without a commit, or after an error, aborts the upload best-effort: failures are logged, not
    raised.
  - After an ambiguous Complete failure, raise `BlobIndeterminateError` (the invariant).
- [x] **Streaming carve-out.** All part transmission goes through one internal method,
  `_send_part(number, body: bytes | S3StreamBody)`, and the buffering is confined to one small class.
  - Put a `TODO` comment block there sketching the streaming writer: open the part request on the first `write`, feed
    its body from a queue, and complete it at the part boundary.
  - Note in that comment that it needs a background task running the in-flight request, which `asynclite` can't spawn
    yet, and that `AsyncToSyncBlobStore` callers can never use it.

### 10.5 Unit tests

- [x] `test_transport.py` uses a tiny test-support `AsyncHttpClient` returning canned responses:
  - classification of every failure kind
  - the invariant: an ambiguous conditional write is never offered to the policy, and sends no second request
  - retries only when the policy says so
  - 200-with-error bodies
- [x] `test_config.py`:
  - the default config equals AWS
  - `S3_MOCK_CONFIG` has no copy capabilities
  - nothing in `aws/` (outside `stores.py`'s preset definitions and tests) mentions `r2`, `s3mock` or `aws` in a
    branch (a grep-style test over the source)

**Done when:** the unit tests pass, and ruff and mypy are clean. Behaviour is proven in phase 11.


## Phase 11: S3 test tiers

**Goal:** prove `S3BlobStore` against s3mock across every HTTP client, prove the retry and indeterminacy logic with
injected transport faults, run the LSM over S3, and have live tiers ready for AWS and R2.

### 11.1 s3mock harness (`aws/tests/harness.py`)

- [x] Model it on `omcore/sql/tests/harness.py`:

  ```python
  # FIXME: env var override is a temporary codestyle violation to support ~/scripts/run-s3mock in agent sandboxes.
  S3_URL_ENV_VAR = EnvVar('OM_TEST_S3_URL')

  @pti.bind('session')
  class HarnessS3:
      def __init__(self, compose_services: ComposeServices) -> None: ...
      def endpoint(self) -> S3Endpoint: ...
      def bucket(self) -> str: ...
  ```

  - **Endpoint resolution:** the env var if set. Otherwise, inside docker, `http://om-s3:9090`, else
    `http://127.0.0.1:<get_compose_port(svc, 9090)>`. The region is `us-east-1`, with dummy credentials.
  - **Bucket:** one per session, `om-blobs-test-<uuid7>`, created once with the generated `CreateBucket` operation
    over a plain request.
  - Tests isolate themselves with `PrefixedBlobStore(store, f'{uuid7}/')`, so they're safe under xdist.
- [x] Mark every module that uses it `pytestmark = pytest.mark.integration`.

### 11.2 Client matrix (`aws/tests/clients.py`)

- [x] Test-only factories, each yielding `(S3BlobStore, ScenarioRunner)` for one client configuration:

  | Id | HTTP client | Runner |
  | --- | --- | --- |
  | `pipelines-sync` | `SyncAsyncHttpClient(IoPipelineHttpClient())` | `SyncAwaitScenarioRunner` |
  | `urllib` | `SyncAsyncHttpClient(UrllibHttpClient())` | `SyncAwaitScenarioRunner` |
  | `httpx-sync` | `SyncAsyncHttpClient(HttpxHttpClient())` | `SyncAwaitScenarioRunner` |
  | `pipelines-asyncio` | `AsyncioIoPipelineAsyncHttpClient()` | `AsyncioScenarioRunner` |
  | `httpx-asyncio` | `HttpxAsyncHttpClient()` | `AsyncioScenarioRunner` |

  - The httpx rows skip if httpx can't be imported.
  - The stores use `S3_MOCK_CONFIG`, with small `list_page_size` and `delete_batch_size` values so paging is exercised.
  - This is also a real integration test of the omcore HTTP clients: record any client bugs found in handoff notes and
    fix them in omcore.
- [x] One more configuration wraps the `pipelines-sync` store in `AsyncToSyncBlobStore` and then
  `SyncToAsyncBlobStore`, proving the sync-facade path end to end.

### 11.3 Transport fault injection and recording (`aws/tests/faults.py`, `aws/tests/recording.py`)

- [x] `FaultInjectingAsyncHttpClient(inner: AsyncHttpClient, faults)` wraps the **real** s3mock-backed client.
  - It matches on method, path, and an S3 operation hint derived from the query, plus `nth`.
  - Each rule fires once. Actions:
    - `raise_before`: raise `HttpClientError` caused by `TimeoutError`, without sending
    - `raise_after`: send to s3mock, discard the response, then raise the same way
    - `refuse`: raise `HttpClientError` caused by `ConnectionRefusedError`, without sending
    - `respond(status, code)`: return a synthesized XML error response without sending, e.g. 503 SlowDown, 409
      ConditionalRequestConflict or 500 InternalError
  - No S3 behaviour is emulated: it only fails transport or substitutes an error status.
- [x] `RecordingAsyncHttpClient` records method, URL and headers, for asserting request sequences.

### 11.4 Tests against s3mock

- [x] `test_conformance_s3mock.py`: the full `BlobStoreConformance` for every row of the client matrix, plus the
  adapter round trip.
  - Set `xfail_astral_ordering = True` (0.5).
  - Set `large_size` to about 11 MiB, with a 5 MiB `part_size`.
- [x] `test_stores_s3mock.py`, using the recording client:
  - a lazy multipart with no Create for small objects
  - the 416 → HEAD fallback
  - copy 404 disambiguation
  - an abort on exit without commit
  - `start-after` sent on the first page only
  - `no_decompress` set on data GETs
- [x] `test_faults_s3mock.py`, one rule per case:
  - a read with `raise_after` raises `BlobTransportError` with no policy, and succeeds with
    `SimpleS3RetryPolicy(sync sleeps)`
  - a conditional put with `raise_after` raises `BlobIndeterminateError`, the recording shows no second request, and
    the object did land in s3mock
  - 409 retries under the policy, and raises `BlobConflictError` without one
  - 503 raises `BlobThrottledError` by default, and is retried under the policy
  - `refuse` retries under the policy
  - `ManifestStore.commit` with `raise_after` on the manifest put resolves through read-back
- [x] `test_lsm_s3mock.py` runs `scenarios.py`, fencing, indeterminate commits and GC over `S3BlobStore`. Use at least
  `pipelines-asyncio` and `pipelines-sync`.

### 11.5 Capability probe (`aws/tests/probe.py`)

- [x] `probe_s3_capabilities(store: S3BlobStore) -> BlobCapability` uses a scratch prefix it cleans up. It claims each
  capability in turn and reports whether it is enforced, silently ignored, or rejected with 501. Copy conditions are
  tried under both header conventions.
- [x] Add a `_main()` entrypoint (`./python -m x.blobs.aws.tests.probe ...`) that builds stores from `HarnessS3` or
  from secrets, prints a table, and suggests `Config` capabilities. It's for the user to run against AWS and R2.

### 11.6 Live tests (`aws/tests/test_live.py`)

- [x] `pytestmark = pytest.mark.online`. There are two targets, built as if credentials exist, each skipped via
  `harness[HarnessSecrets].get_or_skip(...)`:
  - **AWS:** `blobs_test_aws_s3_bucket`, `blobs_test_aws_s3_region`, `aws_access_key_id`, `aws_secret_access_key`.
    It uses the default `Config()`.
  - **R2:** `blobs_test_r2_account_id`, `blobs_test_r2_bucket`, `blobs_test_r2_access_key_id`,
    `blobs_test_r2_secret_access_key`. It uses `R2_CONFIG`.
- [x] Run the conformance suite, including races, on a unique prefix on `pipelines-asyncio`. Clean up with
  `delete_many`.
- [x] Add a docstring note: the R2 race tests are the check on whether R2 evaluates conditional-put predicates
  atomically. Don't trust R2 for manifest commits until they pass. Likewise, AWS conditional copy is only enabled
  after this suite passes with it claimed.

**Done when:** every s3mock tier is green in the sandbox (with run-s3mock), and the live tier collects cleanly and
skips without secrets.


## Phase 12: Cloudflare R2

R2 speaks the S3 API. Its differences are config values and nothing else. It isn't integration tested; s3mock can't
behave like R2, and the live target in 11.6 is optional.

- [x] Define `R2_CONFIG` below `S3BlobStore`:
  - `capabilities = PUT_IF_ABSENT | PUT_IF_MATCH | COPY_IF_ABSENT | COPY_IF_MATCH`. `DELETE_IF_MATCH` is off until
    verified; comment why.
  - `copy_dst_if_none_match_header = 'cf-copy-destination-if-none-match'`
  - `copy_dst_if_match_header = 'cf-copy-destination-if-match'`
- [x] Document next to it, with no helper functions:
  - the endpoint URL format `https://<account_id>.r2.cloudflarestorage.com`, or
    `https://<account_id>.<jurisdiction>.r2.cloudflarestorage.com`
  - region `auto`
  - path-style addressing
  - uniform part sizes, which the writer already guarantees
  - that aws-chunked support on R2 is unverified
- [x] `test_r2.py`: golden requests built with `R2_CONFIG`:
  - `auto` in the credential scope
  - the `cf-*` destination headers present on CopyObject, and AWS's `If-*` absent there
  - uniform part sizes in a multipart sequence (via the recording client against s3mock with `R2_CONFIG` minus the copy
    capabilities, or a canned client)


## Phase 13: Streamed uploads, up to the HTTP seam

**Goal:** the complete streamed-upload machinery (aws-chunked bodies with per-chunk SigV4, known-length streamed
PutObject and UploadPart), stopping at exactly one call that would send a streaming body through omcore.http. It is
tested end to end against s3mock through a buffering stand-in for that call.

- [x] **`aws/streaming.py`:**
  - `S3StreamBody(source: ta.AsyncIterable[bytes], length: int)`.
  - `aws_chunked_body(source, *, chunk_signer, chunk_size, decoded_length) -> ta.AsyncIterator[bytes]`:
    - It re-blocks the source into `chunk_size` pieces and yields framed, signed chunks followed by the final chunk.
    - It raises if the source yields more or fewer than `decoded_length` bytes.
- [x] **The seam** is an `S3StreamingSender` interface:

  ```python
  class S3StreamingSender(lang.Abstract):
      @abc.abstractmethod
      def send(
              self,
              client: AsyncHttpClient,
              request: HttpClientRequest,       # data=None; Content-Length and aws-chunked headers already set
              body: ta.AsyncIterable[bytes],
      ) -> ta.Awaitable[HttpClientResponse]:
          raise NotImplementedError
  ```

  - `HttpClientStreamingSender` is the default. It raises `NotImplementedError`, with a TODO block containing the
    one-line implementation that will work once omcore.http lands streaming bodies:
    `await client.request(dc.replace(request, data=body))`, where `data` accepts an `AsyncIterable[bytes]`,
    `Content-Length` is required, and chunked transfer encoding is never used.
  - `S3BlobStore` uses `streaming_sender or HttpClientStreamingSender()`.
- [x] **Streamed mode** (`Config.streamed_uploads=True`) applies only to `put_stream`:
  - Known `length <= part_size`: one streamed PutObject.
  - Known `length > part_size`: multipart, with each UploadPart streamed from a part-sized slice of the source,
    sequentially.
  - `length=None`: the immediate path, since aws-chunked needs the decoded length up front.
  - `put(bytes)` and `open_writer` stay immediate (10.4).
- [x] **Tests:**
  - `aws/tests/streaming.py` provides `BufferingStreamingSender`: it drains the body to bytes and sends it with a
    normal `client.request(dc.replace(request, data=buf))`, keeping the aws-chunked headers. s3mock decodes it.
  - `test_streaming.py`:
    - the default sender raises `NotImplementedError`
    - encoder output matches `aws_chunked_encode` and the phase 6 AWS vector
    - `put_stream` round-trips through s3mock in streamed mode across the client matrix, for single and multipart
      sizes
    - a length mismatch publishes nothing
  - Add a streamed-mode variant to the live AWS target, noting that R2's aws-chunked support is unverified.


## Phase 14: Parallel transfer plans

**Goal:** sans-IO side helpers that turn one large transfer into independent operations a caller can run
concurrently, in any order, and then finalize. They are not part of any store interface. Buffered per-part uploads
already make each part an independent request; these helpers expose that as data.

### 14.1 Parallel ranged get (`x/blobs/plans.py`, core)

- [x] `plan_parallel_get(info: BlobInfo, *, part_size: int) -> ParallelGetPlan` is pure. The caller supplies `info`
  from a head or a first ranged get.
- [x] `ParallelGetPlan(key, version, size, parts: ta.Sequence[ParallelGetPart(index, byte_range)])`.
- [x] `get_part(store: AsyncBlobStore, plan, part) -> ta.Awaitable[Blob]` does `store.get(key, byte_range=...,
  cond=IfMatch(plan.version))`.
- [x] `finish_parallel_get(plan, blobs: ta.Mapping[int, Blob]) -> bytes` checks that every part is present with the
  right length and version, and assembles them.
- [x] **Tests:**
  - Over `SyncToAsyncBlobStore(DictBlobStore())`: shuffle the parts, run each with `sync_await`, and finalize.
  - A replace mid-plan fails with a precondition error.
  - Empty objects, and sizes that are exact multiples of `part_size`.
  - A real-loop variant with `asyncio.gather` against s3mock.

### 14.2 Parallel upload (`x/blobs/aws/uploads.py`, S3-only)

- [x] `begin_parallel_upload(store: S3BlobStore, key, *, size: int, cond=None) -> ta.Awaitable[S3ParallelUploadPlan]`:
  - The plan holds `key`, `upload_id | None`, `cond`, and `parts: ta.Sequence[S3UploadPart(number, byte_range)]`,
    with uniform part sizes.
  - A size up to `part_size` gives a single-part plan with no upload id (no IO at begin). Its finish is one PutObject
    with `cond`.
- [x] `upload_part(store, plan, part, data: bytes) -> ta.Awaitable[S3UploadedPart]` checks the data length. It is
  idempotent, so a failed part can simply be re-run.
- [x] `finish_parallel_upload(store, plan, uploaded: ta.Iterable[S3UploadedPart]) -> ta.Awaitable[BlobVersion]`
  completes with `cond`, following the same indeterminacy rules as the writer.
- [x] `abort_parallel_upload(store, plan) -> ta.Awaitable[None]`.
- [x] Use store internals (the transport and ops); nothing new goes on the interface.
- [x] **Tests (s3mock):**
  - on `pipelines-sync` via `sync_await`: parts in random order, then finish
  - on `pipelines-asyncio` via `asyncio.gather`
  - a missing part at finish raises
  - `cond=IfAbsent()` loses to a rival write
  - abort leaves no upload in ListMultipartUploads


## Phase 15: Wrap-up

- [x] `x/blobs/README.md` covering:
  - semantics: preconditions, ranges, listing order, versions and ABA, indeterminacy, throttling
  - the sync/async model and the adapters, with composition examples in prose rather than helper functions
  - the capability table for AWS, R2, s3mock and local, marking unverified cells
  - the `Config` axes and presets
  - retry policies
  - streamed-upload status: the seam, and what omcore.http needs
  - operational notes: the multipart lifecycle rule, `remove_stale_tmp_files`, `abort_stale_uploads`
  - the LSM's status
- [x] Final `__init__.py` exports for core and for `aws/`.
- [x] Run `./python -m ruff check x/blobs`, `./python -m mypy x/blobs` and `./python -m pytest x/blobs` (with
  run-s3mock up and `OM_TEST_S3_URL` set). Then `make fix gen check`, plus the ominfra/omcore pytests touched.
- [ ] Promotion checklist (for later; don't do it now):
  - core → `omcore/blobs`
  - `aws/` → `ominfra/blobs/aws`, changing `from ... import blobs` to `from omcore import blobs`
  - `restxml.py` → `ominfra/clouds/aws`
  - the LSM → wherever it is promoted to
  - drop the `OM_TEST_S3_URL` override once the harness supports run-s3mock natively
- [x] Fill in [Handoff notes](#handoff-notes).


## Appendix A: S3 response to blob error mapping

"cond" is the operation's precondition, and "policy" means the injected `S3RetryPolicy` is consulted first; with no
policy, the error is raised immediately. Rows are checked in order; the first match wins.

| Operation | Response | Result |
| --- | --- | --- |
| any | 503 `SlowDown` | policy (`THROTTLED`); else `BlobThrottledError` |
| any | 301 / 307 redirect | `S3ResponseError` (wrong region or endpoint) |
| any | 403 (`AccessDenied`, `SignatureDoesNotMatch`, ...) | `S3ResponseError` |
| any | 404 `NoSuchBucket` | `S3ResponseError`: configuration, never NotFound |
| any conditional write | 501 `NotImplemented` | `UnsupportedBlobOperationError` |
| HEAD / GET | 304 | `BlobNotModifiedError` |
| HEAD / GET | 412 | `BlobPreconditionFailedError` |
| HEAD / GET | 404 (`NoSuchKey`, or HEAD without a body), cond `IfMatch` | `BlobPreconditionFailedError` |
| HEAD / GET | 404, other cond | `BlobNotFoundError` |
| GET | 416 `InvalidRange` | HEAD with the same cond, then `Blob(info, b'')` |
| GET | 200 to a ranged request | slice locally; size = `Content-Length` |
| PUT / Complete | 412, cond `IfAbsent` | `BlobAlreadyExistsError` |
| PUT / Complete | 412, cond `IfMatch` | `BlobPreconditionFailedError` |
| PUT / Complete | 404 `NoSuchKey`, cond `IfMatch` | `BlobPreconditionFailedError` |
| PUT / Complete / Copy | 409 `ConditionalRequestConflict` | policy (`NOT_APPLIED`); else `BlobConflictError` |
| Complete | 404 `NoSuchUpload` after an ambiguous attempt | `BlobIndeterminateError` |
| Complete | 404 `NoSuchUpload` otherwise | `S3ResponseError` |
| Copy / Complete | 200 with an `<Error>` body | as that error's status (e.g. `InternalError` = 500) |
| Copy | 404 `NoSuchKey`, cond not `IfMatch` | `BlobNotFoundError(src)` |
| Copy | 404 `NoSuchKey`, cond `IfMatch` | HEAD src; missing: `BlobNotFoundError(src)`, else precondition failed |
| Copy | 412 | as PUT, by cond |
| DELETE | 204 | success, including a missing key without a cond |
| DELETE | 412, or 404 with cond `IfMatch` | `BlobPreconditionFailedError` |
| DeleteObjects | per-key `<Error>` | collected into `BlobDeleteManyError` |
| reads | transport error / 5xx | policy (`READ_FAILED`); else `BlobTransportError` |
| any | refused connection / DNS failure | policy (`NOT_APPLIED`); else `BlobTransportError` |
| unconditional writes | other transport error / 5xx | policy (`AMBIGUOUS`); else `BlobIndeterminateError` |
| conditional writes | other transport error / 5xx | `BlobIndeterminateError` immediately; **never** offered |
| any | anything else | `S3ResponseError` |

s3mock confirms the 404-vs-412 rows for PUT, GET/HEAD, DELETE and Complete, and the 416 rows (0.5). The live AWS tier
must confirm the rest, especially conditional CopyObject: record the results in handoff notes.


## Appendix B: Conformance checklist

Each bullet is at least one scenario on `BlobStoreConformance`.

**Basics**
- [x] put, get and head round-trip, and `size` / `version` / `last_modified` (UTC-aware) are consistent
- [x] an empty object
- [x] an object larger than the writer part size (`large_size`)
- [x] overwriting changes the version, and the version agrees across put, put_stream, head, get, list, copy and writer
  commit
- [x] get and head of a missing key raise `BlobNotFoundError`
- [x] awkward keys round-trip through put, get, list, copy and delete: space, `+`, `%`, `#`, `?`, `&`, `=`, `~`, `*`,
  quotes, a trailing `.`, and non-ASCII (BMP and astral)
- [x] `A` and `a` are distinct keys
- [x] `a` and `a/b` coexist, and deleting one leaves the other
- [x] suffix-looking (`x.file`, `x.dir`) and escape-looking (`%41`) segments
- [x] long keys: 1000+ bytes across segments of at most 200 bytes
- [x] invalid keys raise `InvalidBlobKeyError` before any IO

**Ranges**
- [x] offset, open-ended offset, and a stop past the end (clamped)
- [x] `start == size` and `start > size` both return empty data with the full `info`
- [x] a suffix, and a suffix longer than the object
- [x] ranges on an empty object
- [x] `info.size` is always the whole object's size
- [x] a range combined with `IfMatch`

**Read preconditions**
- [x] `IfMatch`: current passes; stale or missing raises `BlobPreconditionFailedError`
- [x] `IfNoneMatch`: current raises `BlobNotModifiedError`; stale passes; missing raises `BlobNotFoundError`

**Write preconditions** (each gated by its capability, and each with an enforcement case)
- [x] put and put_stream `IfAbsent`: an absent key succeeds; a present key raises `BlobAlreadyExistsError`
- [x] put and put_stream `IfMatch`: current succeeds; stale or missing raises `BlobPreconditionFailedError`
- [x] delete `IfMatch`: current succeeds; stale or missing raises `BlobPreconditionFailedError`. An unconditional delete
  of a missing key is a no-op
- [x] copy `IfAbsent` / `IfMatch` apply to the destination. A missing source raises `BlobNotFoundError`, and
  `copy(k, k)` raises `ValueError`
- [x] a missing capability raises `UnsupportedBlobOperationError` before any IO, and the store is unchanged

**Writers and put_stream**
- [x] nothing is visible without `commit`, on a normal exit or an exception
- [x] `commit` publishes and returns the version
- [x] the precondition is evaluated at commit, not at open (a rival create in between makes the commit fail)
- [x] `write` after commit, a second `commit`, and use after exit all raise
- [x] many small writes and a few huge writes produce identical results
- [x] a `put_stream` `length` mismatch raises `ValueError` and publishes nothing
- [x] `put_stream` over empty, small and multipart-sized sources

**Listing**
- [x] code point order, including `a` < `a-c` < `a/b`, non-ASCII, and astral characters (xfail-able)
- [x] `prefix`, including a prefix that is itself a key and a prefix with no delimiter
- [x] `start_after` before the prefix, inside it, equal to a key, after everything, and between keys
- [x] paging: more keys than the page size
- [x] abandoning a listing midway leaks nothing and doesn't break later operations
- [x] `list_shallow`:
  - nesting
  - a prefix ending in the delimiter
  - a non-`/` delimiter
  - each common prefix appears once
  - emptied "directories" don't appear
  - prefixes interleave correctly with objects

**delete_many**
- [x] a mix of existing and missing keys
- [x] more keys than the batch size
- [x] an empty iterable
- [x] invalid keys are rejected before any IO

**Concurrency** (via `runner.gather`)
- [x] the `IfAbsent` race: exactly one winner
- [x] the CAS counter: exactly N*M
- [x] readers during overwrites always see a complete old or new object whose data matches its version


## Appendix C: References

- SigV4: <https://docs.aws.amazon.com/IAM/latest/UserGuide/create-signed-request.html>,
  <https://docs.aws.amazon.com/AmazonS3/latest/API/sig-v4-header-based-auth.html>
- Streaming SigV4 (aws-chunked): <https://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-streaming.html>
- S3 conditional requests and writes: <https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-requests.html>
- CompleteMultipartUpload (200 with an error body):
  <https://docs.aws.amazon.com/AmazonS3/latest/API/API_CompleteMultipartUpload.html>
- CopyObject: <https://docs.aws.amazon.com/AmazonS3/latest/API/API_CopyObject.html>
- DeleteObjects (Content-MD5 required): <https://docs.aws.amazon.com/AmazonS3/latest/API/API_DeleteObjects.html>
- R2 S3 compatibility: <https://developers.cloudflare.com/r2/api/s3/api/>; R2 extensions (`cf-*` headers):
  <https://developers.cloudflare.com/r2/api/s3/extensions/>
- s3mock: <https://github.com/adobe/S3Mock>
- Design references: Rust `object_store` (<https://docs.rs/object_store>), SlateDB (<https://slatedb.io>)
- In repo:
  - the async-first pattern: `omcore/inject/impl/sync.py`, `omcore/sql/api/asyncs.py`
  - client management: `omllm/llm/backends/anthropic/messages/stream.py`, `omcore/http/clients/default.py`
    (`manage_async_client`)
  - helpers: `omcore/lite/asyncs.py` (`sync_await`, `sync_aiter`, context manager adapters) and
    `omcore/asyncs/asynclite/`
  - harness patterns: `omcore/sql/tests/harness.py`, `omcore/secrets/tests/harness.py`
  - loopback test servers: `omcore/http/clients/pipelines/tests/test_transport_errors.py`
  - `omcore/os/atomics.py`: not reused, because it doesn't fsync and can't do link-based commits


## Handoff notes

Add to this list as you go: anything assumed but not verified, anything only a real endpoint can confirm, bugs found
in omcore (especially in the HTTP clients during phase 11), and every deviation from this plan with its reason.

**Status (2026-09-25):**
- Every phase is implemented.
- `./python -m pytest x/blobs` passes with `OM_TEST_S3_URL=http://127.0.0.1:9090` and `~/scripts/run-s3mock`: 793
  passed, and it also passes under xdist. Core, local, and the S3 sync-pipelines tiers also pass under free-threaded
  3.14 (`.venvs/14t`).
- `make fix gen check` is clean.

**Only a real endpoint can confirm these.** Run the probe
(`./python -m x.blobs.aws.tests.probe aws|r2 --bucket ...`) and `aws/tests/test_live.py` with the secrets listed
there:
- AWS conditional CopyObject: `COPY_IF_*` is off in the default Config.
- R2 `DELETE_IF_MATCH` (off) and R2 aws-chunked support.
- Whether AWS and R2 evaluate conditional writes atomically under races (the live race cases).
- AWS's 404-vs-412 for `If-Match` on a missing key for DeleteObject and CopyObject.
- AWS's 416 on empty objects, and CompleteMultipartUpload idempotency.

**The streaming SigV4 test vector.** The AWS sigv4-streaming page no longer renders: it redirects to the API landing
page, including through the China mirror. Instead:
- Web search confirmed that the expected values appear on that official page: the seed signature, all three chunk
  signatures, and `Content-Length: 66824`.
- The implementation reproduces all four signatures from the example's inputs. Those inputs are recalled from the doc,
  but any error in them would change every signature.

**s3mock deviations** are listed in 0.5: non-atomic races, ignored copy preconditions, UTF-16 listing order, and the
required `Content-Type: application/xml`.

**Pre-existing and unrelated:** `./python -m ominfra.clouds.aws.instancetypes dump -m` fails on master too.
`'metal-compatibility'` is not a valid `SupportedAdditionalProcessorFeature`: the cached data is newer than the model.

**Deviations from the plan:**
- **LSM:** added `x/blobs/tests/lsm/views.py`, a read view over one manifest's SSTs shared by the writer and readers.
  `LsmOptions` also gained `open_retries` and `block_cache_size`.
- **Errors:** a `put_stream` length mismatch raises `BlobStreamLengthError(BlobStoreError, ValueError)` rather than a
  bare `ValueError`. `plans.py` adds `BlobPlanError`.
- **`restxml`** marks field types it can't handle (e.g. the base `Tag` type in `CreateBucketConfiguration`) as
  `UNSUPPORTED`, failing only if such a value is actually present.
- **S3 part size:** the 5 MiB minimum is a module constant (`MIN_PART_SIZE`) validated at construction, not a Config
  field.
- **S3 multipart:** `S3BlobStore` exposes its multipart primitives publicly (through `S3MultipartOps` in
  `aws/writers.py`), used by the writer and by `aws/uploads.py`.
- **Transport** catches `(HttpClientError, TimeoutError, ConnectionError)`, since raw errors can still leak from under
  some clients.
- **Tests:**
  - The LSM-over-S3 tier imports the core LSM test functions into `test_lsm_s3mock.py`, run over the sync pipelines
    client, plus a model scenario on a real asyncio loop. It isn't every scenario on every client.
  - The s3mock harness's `store()` defaults to no http client, meaning a fresh default asyncio client per request.
    Sync-driven tests must pass a `SyncAsyncHttpClient`.

**Next steps:**
- **Streaming uploads:** add streaming request bodies to omcore.http, then turn `HttpClientStreamingSender` into the
  one-liner in its TODO.
- **Streaming writer:** add task spawning to asynclite, then write the streaming `open_writer` sketched in
  `aws/writers.py`.
- **Large copies:** UploadPartCopy, for copies of sources over 5 GiB.
- **Performance:** keep-alive and pooling in the pipeline clients. They open a new connection per request, which adds
  up for S3.
