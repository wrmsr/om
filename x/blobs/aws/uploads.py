"""
A sans-IO parallel upload plan for S3: begin, upload parts in any order and concurrency, then finish. Parts are
idempotent, so a failed part can simply be re-run. Not part of the store interface.
"""
import typing as ta

from omcore import dataclasses as dc

from ... import blobs
from .stores import S3BlobStore


##


@dc.dataclass(frozen=True, kw_only=True)
class S3UploadPart:
    number: int
    start: int
    stop: int

    @property
    def length(self) -> int:
        return self.stop - self.start


@dc.dataclass(frozen=True, kw_only=True)
class S3UploadedPart:
    number: int
    etag: str | None = None
    data: bytes | None = None  # carried to finish when the plan is a single PutObject


@dc.dataclass(frozen=True, kw_only=True)
class S3ParallelUploadPlan:
    key: str
    size: int
    upload_id: str | None  # None: small enough for a single PutObject at finish
    cond: blobs.BlobWritePrecondition | None
    parts: ta.Sequence[S3UploadPart]


async def begin_parallel_upload(
        store: S3BlobStore,
        key: str,
        *,
        size: int,
        cond: blobs.BlobWritePrecondition | None = None,
) -> S3ParallelUploadPlan:
    blobs.check_blob_key(key)
    blobs.check_blob_capabilities(store.capabilities(), blobs.put_capability(cond))
    ps = store.config.part_size
    if size <= ps:
        return S3ParallelUploadPlan(
            key=key,
            size=size,
            upload_id=None,
            cond=cond,
            parts=[S3UploadPart(number=1, start=0, stop=size)],
        )
    return S3ParallelUploadPlan(
        key=key,
        size=size,
        upload_id=await store.create_multipart_upload(key),
        cond=cond,
        parts=[
            S3UploadPart(number=i + 1, start=s, stop=min(size, s + ps))
            for i, s in enumerate(range(0, size, ps))
        ],
    )


async def upload_part(
        store: S3BlobStore,
        plan: S3ParallelUploadPlan,
        part: S3UploadPart,
        data: bytes,
) -> S3UploadedPart:
    if len(data) != part.length:
        raise blobs.BlobStreamLengthError(f'part {part.number} of {plan.key!r}: {len(data)} != {part.length}')
    if plan.upload_id is None:
        return S3UploadedPart(number=part.number, data=bytes(data))
    return S3UploadedPart(
        number=part.number,
        etag=await store.upload_part(plan.key, plan.upload_id, part.number, data),
    )


async def finish_parallel_upload(
        store: S3BlobStore,
        plan: S3ParallelUploadPlan,
        uploaded: ta.Iterable[S3UploadedPart],
) -> blobs.BlobVersion:
    by_number = {u.number: u for u in uploaded}
    if set(by_number) != {p.number for p in plan.parts}:
        raise blobs.BlobStoreError(f'parts mismatch for {plan.key!r}: {sorted(by_number)}')
    if plan.upload_id is None:
        return await store.put(plan.key, by_number[1].data or b'', cond=plan.cond)
    return await store.complete_multipart_upload(
        plan.key,
        plan.upload_id,
        [(n, u.etag or '') for n, u in sorted(by_number.items())],
        cond=plan.cond,
    )


async def abort_parallel_upload(store: S3BlobStore, plan: S3ParallelUploadPlan) -> None:
    if plan.upload_id is not None:
        await store.abort_multipart_upload(plan.key, plan.upload_id)
