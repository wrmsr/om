import contextlib
import datetime
import heapq
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore.http import all as http
from ominfra.clouds.aws import auth as aws_auth
from ominfra.clouds.aws.models.services import s3

from ... import blobs
from . import ops
from .endpoints import S3Endpoint
from .endpoints import check_bucket_addressable
from .errors import S3ResponseError
from .retries import S3RetryPolicy
from .signing import S3RequestSigner
from .streaming import HttpClientStreamingSender
from .streaming import S3StreamBody
from .streaming import S3StreamingSender
from .transport import S3Transport
from .writers import S3BlobWriter
from .writers import S3MultipartOps


##


MIN_PART_SIZE = 5 * 1024 * 1024
MAX_SINGLE_PUT_SIZE = 5 * 1024 * 1024 * 1024

_DEFAULT_CAPABILITIES = (
    blobs.BlobCapability.PUT_IF_ABSENT |
    blobs.BlobCapability.PUT_IF_MATCH |
    blobs.BlobCapability.DELETE_IF_MATCH
)


def _raise_mapped(op: str, e: S3ResponseError, *, key: str, cond: blobs.BlobPrecondition | None) -> ta.NoReturn:
    if (m := ops.map_error(op, e, key=key, cond=cond)) is e:
        raise e
    raise m from e


class S3BlobStore(blobs.AsyncBlobStore, S3MultipartOps):
    """
    A blob store over the S3 API - AWS S3 by default, and other implementations (R2, s3mock) via Config. Async-only: to
    use it from sync code, give it a SyncAsyncHttpClient and wrap it in an AsyncToSyncBlobStore.

    If no http client is given, each request uses a fresh default client from http.manage_async_client.
    """

    @dc.dataclass(frozen=True, kw_only=True)
    class Config:
        # AWS S3 as of 2026-09. The copy capabilities are off: botocore's model lists If-Match / If-None-Match on
        # CopyObject, but that is unverified live, and s3mock silently ignores them. Enable after the live conformance
        # run passes with them claimed.
        capabilities: blobs.BlobCapability = _DEFAULT_CAPABILITIES

        # The headers carrying CopyObject destination preconditions.
        copy_dst_if_none_match_header: str = 'If-None-Match'
        copy_dst_if_match_header: str = 'If-Match'

        # Don't request encoding-type=url when listing.
        no_list_url_encoding: bool = False

        # Send UNSIGNED-PAYLOAD rather than hashing request bodies (https only).
        unsigned_payload: bool = False

        # Send put_stream bodies of known length as aws-chunked streams rather than buffering them.
        streamed_uploads: bool = False

        part_size: int = 8 * 1024 * 1024
        streaming_chunk_size: int = 64 * 1024
        list_page_size: int = 1000
        delete_batch_size: int = 1000
        request_timeout_s: float = 60. * 60.  # omcore.http timeouts are absolute deadlines including the body

    def __init__(
            self,
            *,
            bucket: str,
            endpoint: S3Endpoint,
            credentials: aws_auth.AwsSigner.Credentials,
            config: Config | None = None,
            http_client: http.AsyncHttpClient | None = None,
            retry_policy: S3RetryPolicy | None = None,
            streaming_sender: S3StreamingSender | None = None,
            clock: ta.Callable[[], datetime.datetime] | None = None,
    ) -> None:
        super().__init__()

        if config is None:
            config = S3BlobStore.Config()

        check_bucket_addressable(endpoint, bucket)
        if config.part_size < MIN_PART_SIZE:
            raise ValueError(f'part size must be at least {MIN_PART_SIZE}: {config.part_size}')

        self._bucket = bucket
        self._config = config

        self._transport = S3Transport(
            bucket=bucket,
            endpoint=endpoint,
            signer=S3RequestSigner(credentials, endpoint.region, clock=clock),
            http_client=http_client,
            retry_policy=retry_policy,
            streaming_sender=streaming_sender if streaming_sender is not None else HttpClientStreamingSender(),
            timeout_s=config.request_timeout_s,
            unsigned_payload=config.unsigned_payload,
            streaming_chunk_size=config.streaming_chunk_size,
        )

    @property
    def bucket(self) -> str:
        return self._bucket

    @property
    def config(self) -> Config:
        return self._config

    def capabilities(self) -> blobs.BlobCapability:
        return self._config.capabilities

    ## Reads

    async def head(self, key: str, *, cond: blobs.BlobReadPrecondition | None = None) -> blobs.BlobInfo:
        blobs.check_blob_key(key)
        try:
            _, out = await self._transport.execute(
                s3.HEAD_OBJECT,
                ops.build_head(self._bucket, key, cond),
                read=True,
            )
        except S3ResponseError as e:
            _raise_mapped('head', e, key=key, cond=cond)
        return ops.info_from_head(key, out)

    async def get(
            self,
            key: str,
            *,
            byte_range: blobs.BlobRange | None = None,
            cond: blobs.BlobReadPrecondition | None = None,
    ) -> blobs.Blob:
        blobs.check_blob_key(key)
        try:
            resp, out = await self._transport.execute(
                s3.GET_OBJECT,
                ops.build_get(self._bucket, key, byte_range, cond),
                read=True,
                no_decompress=True,
            )
        except S3ResponseError as e:
            if e.status == 416:
                # Unsatisfiable - including any range on an empty object. Python slice semantics make that empty.
                return blobs.Blob(info=await self.head(key, cond=cond), data=b'')
            _raise_mapped('get', e, key=key, cond=cond)
        return ops.blob_from_get(key, resp.status, out, byte_range)

    async def _list_pages(
            self,
            *,
            prefix: str,
            start_after: str | None,
            delimiter: str | None,
    ) -> ta.AsyncIterator[ops.ListPage]:
        token: str | None = None
        while True:
            _, out = await self._transport.execute(
                s3.LIST_OBJECTS_V2,
                ops.build_list(
                    self._bucket,
                    prefix=prefix,
                    start_after=start_after,
                    continuation_token=token,
                    delimiter=delimiter,
                    max_keys=self._config.list_page_size,
                    no_url_encoding=self._config.no_list_url_encoding,
                ),
                read=True,
            )
            page = ops.page_from_list(out)
            yield page
            if (token := page.next_token) is None:
                return

    async def list(self, *, prefix: str = '', start_after: str | None = None) -> ta.AsyncIterator[blobs.BlobInfo]:
        async for page in self._list_pages(prefix=prefix, start_after=start_after, delimiter=None):
            for info in page.infos:
                yield info

    async def list_shallow(
            self,
            *,
            prefix: str = '',
            delimiter: str = '/',
    ) -> ta.AsyncIterator[blobs.BlobInfo | blobs.BlobPrefix]:
        check.non_empty_str(delimiter)
        last_prefix: str | None = None
        async for page in self._list_pages(prefix=prefix, start_after=None, delimiter=delimiter):
            merged: ta.Iterable[tuple[str, blobs.BlobInfo | blobs.BlobPrefix]] = heapq.merge(
                ((i.key, i) for i in page.infos),
                ((p, blobs.BlobPrefix(p)) for p in page.prefixes),
                key=lambda t: t[0],
            )
            for k, e in merged:
                if isinstance(e, blobs.BlobPrefix):
                    if k == last_prefix:
                        continue
                    last_prefix = k
                yield e

    ## Writes

    def _check_put(self, key: str, cond: blobs.BlobWritePrecondition | None) -> None:
        blobs.check_blob_key(key)
        blobs.check_blob_capabilities(self.capabilities(), blobs.put_capability(cond))

    async def put(self, key: str, data: bytes, *, cond: blobs.BlobWritePrecondition | None = None) -> blobs.BlobVersion:
        self._check_put(key, cond)
        try:
            _, out = await self._transport.execute(
                s3.PUT_OBJECT,
                ops.build_put(self._bucket, key, data, cond),
                conditional=cond is not None,
            )
        except S3ResponseError as e:
            _raise_mapped('put', e, key=key, cond=cond)
        return ops.normalize_etag(check.not_none(out.etag))

    async def _put_streamed(
            self,
            key: str,
            source: ta.AsyncIterable[bytes],
            *,
            length: int,
            cond: blobs.BlobWritePrecondition | None,
    ) -> blobs.BlobVersion:
        if length <= self._config.part_size:
            try:
                _, out = await self._transport.execute(
                    s3.PUT_OBJECT,
                    ops.build_put(self._bucket, key, b'', cond),
                    conditional=cond is not None,
                    stream_body=S3StreamBody(source, length),
                )
            except S3ResponseError as e:
                _raise_mapped('put', e, key=key, cond=cond)
            return ops.normalize_etag(check.not_none(out.etag))

        ps = self._config.part_size
        upload_id = await self.create_multipart_upload(key)
        try:
            it = aiter(source)
            buf = bytearray()
            parts: list[tuple[int, str]] = []
            remaining = length
            n = 0
            while remaining > 0:
                n += 1
                plen = min(ps, remaining)
                remaining -= plen

                async def part_source(plen: int = plen) -> ta.AsyncIterator[bytes]:
                    # Re-slices the source into exactly plen bytes, carrying any overflow into the next part.
                    got = 0
                    while got < plen:
                        if buf:
                            take = bytes(buf[:plen - got])
                            del buf[:len(take)]
                        else:
                            try:
                                chunk = await anext(it)
                            except StopAsyncIteration:
                                raise blobs.BlobStreamLengthError(f'source ended early for {key!r}') from None
                            take = chunk[:plen - got]
                            buf.extend(chunk[len(take):])
                        got += len(take)
                        if take:
                            yield take

                parts.append((n, await self.upload_part(key, upload_id, n, S3StreamBody(part_source(), plen))))
            extra: bytes | None = await anext(it, None)
            if buf or extra:
                raise blobs.BlobStreamLengthError(f'source exceeded its declared length for {key!r}')
            return await self.complete_multipart_upload(key, upload_id, parts, cond=cond)
        except BaseException:
            try:
                await self.abort_multipart_upload(key, upload_id)
            except Exception:  # noqa
                pass
            raise

    async def put_stream(
            self,
            key: str,
            source: ta.AsyncIterable[bytes],
            *,
            length: int | None = None,
            cond: blobs.BlobWritePrecondition | None = None,
    ) -> blobs.BlobVersion:
        self._check_put(key, cond)
        if self._config.streamed_uploads and length is not None:
            return await self._put_streamed(key, source, length=length, cond=cond)
        async with self.open_writer(key, cond=cond) as w:
            n = 0
            async for chunk in source:
                n += len(chunk)
                if length is not None and n > length:
                    break
                await w.write(chunk)
            blobs.check_blob_stream_length(n, length)
            return await w.commit()

    @contextlib.asynccontextmanager
    async def open_writer(
            self,
            key: str,
            *,
            cond: blobs.BlobWritePrecondition | None = None,
    ) -> ta.AsyncIterator[blobs.AsyncBlobWriter]:
        self._check_put(key, cond)
        w = S3BlobWriter(self, key=key, cond=cond, part_size=self._config.part_size)
        try:
            yield w
        finally:
            await w.close()

    async def copy(self, src: str, dst: str, *, cond: blobs.BlobWritePrecondition | None = None) -> blobs.BlobVersion:
        blobs.check_blob_copy_keys(src, dst)
        blobs.check_blob_capabilities(self.capabilities(), blobs.copy_capability(cond))
        req, extra = ops.build_copy(
            self._bucket,
            src,
            dst,
            cond,
            dst_if_none_match_header=self._config.copy_dst_if_none_match_header,
            dst_if_match_header=self._config.copy_dst_if_match_header,
        )
        try:
            _, out = await self._transport.execute(
                s3.COPY_OBJECT,
                req,
                conditional=cond is not None,
                extra_headers=extra,
                error_200=True,
            )
        except S3ResponseError as e:
            if e.status == 404 and e.code in ('NoSuchKey', None):
                if isinstance(cond, blobs.IfMatch):
                    # Ambiguous: a missing source, or a missing destination failing IfMatch.
                    try:
                        await self.head(src)
                    except blobs.BlobNotFoundError:
                        raise blobs.BlobNotFoundError(src) from e
                    raise blobs.BlobPreconditionFailedError(dst) from e
                raise blobs.BlobNotFoundError(src) from e
            _raise_mapped('copy', e, key=dst, cond=cond)
            # TODO: sources over 5GiB need UploadPartCopy - S3 rejects them with InvalidRequest.
        return ops.version_from_copy(out)

    async def delete(self, key: str, *, cond: blobs.IfMatch | None = None) -> None:
        blobs.check_blob_key(key)
        blobs.check_blob_capabilities(self.capabilities(), blobs.delete_capability(cond))
        try:
            await self._transport.execute(
                s3.DELETE_OBJECT,
                ops.build_delete(self._bucket, key, cond),
                conditional=cond is not None,
            )
        except S3ResponseError as e:
            _raise_mapped('delete', e, key=key, cond=cond)

    async def delete_many(self, keys: ta.Iterable[str]) -> None:
        ks = [blobs.check_blob_key(k) for k in keys]
        errors: dict[str, blobs.BlobStoreError] = {}
        bs = self._config.delete_batch_size
        for i in range(0, len(ks), bs):
            batch = ks[i:i + bs]
            try:
                _, out = await self._transport.execute(
                    s3.DELETE_OBJECTS,
                    ops.build_delete_objects(self._bucket, batch),
                    xml_body=True,
                    content_md5=True,
                )
            except blobs.BlobStoreError as e:
                errors.update({k: e for k in batch})
                continue
            errors.update(ops.errors_from_delete_objects(out))
        if errors:
            raise blobs.BlobDeleteManyError(errors)

    ## Multipart

    async def create_multipart_upload(self, key: str) -> str:
        blobs.check_blob_key(key)
        _, out = await self._transport.execute(
            s3.CREATE_MULTIPART_UPLOAD,
            ops.build_create_multipart(self._bucket, key),
        )
        return check.non_empty_str(out.upload_id)

    async def upload_part(self, key: str, upload_id: str, part_number: int, body: bytes | S3StreamBody) -> str:
        if isinstance(body, S3StreamBody):
            _, out = await self._transport.execute(
                s3.UPLOAD_PART,
                ops.build_upload_part(self._bucket, key, upload_id, part_number, b''),
                stream_body=body,
            )
        else:
            _, out = await self._transport.execute(
                s3.UPLOAD_PART,
                ops.build_upload_part(self._bucket, key, upload_id, part_number, body),
            )
        return check.non_empty_str(out.etag)

    async def complete_multipart_upload(
            self,
            key: str,
            upload_id: str,
            parts: ta.Sequence[tuple[int, str]],
            *,
            cond: blobs.BlobWritePrecondition | None = None,
    ) -> blobs.BlobVersion:
        try:
            _, out = await self._transport.execute(
                s3.COMPLETE_MULTIPART_UPLOAD,
                ops.build_complete_multipart(self._bucket, key, upload_id, parts, cond),
                conditional=cond is not None,
                xml_body=True,
                error_200=True,
            )
        except S3ResponseError as e:
            if e.code == 'NoSuchUpload' and e.after_ambiguous:
                raise blobs.BlobIndeterminateError(key) from e
            _raise_mapped('complete', e, key=key, cond=cond)
        return ops.normalize_etag(check.not_none(out.etag))

    async def abort_multipart_upload(self, key: str, upload_id: str) -> None:
        await self._transport.execute(
            s3.ABORT_MULTIPART_UPLOAD,
            ops.build_abort_multipart(self._bucket, key, upload_id),
        )

    async def abort_stale_uploads(
            self,
            *,
            prefix: str = '',
            older_than: datetime.timedelta,
            now: datetime.datetime | None = None,
    ) -> int:
        """
        Aborts multipart uploads begun longer ago than older_than, which crashed writers leave behind. A bucket
        lifecycle rule (AbortIncompleteMultipartUpload) is the real backstop.
        """

        if now is None:
            now = datetime.datetime.now(tz=datetime.UTC)
        cutoff = now - older_than
        key_marker: str | None = None
        upload_id_marker: str | None = None
        n = 0
        while True:
            _, out = await self._transport.execute(
                s3.LIST_MULTIPART_UPLOADS,
                ops.build_list_multipart_uploads(
                    self._bucket,
                    prefix=prefix,
                    key_marker=key_marker,
                    upload_id_marker=upload_id_marker,
                    max_uploads=self._config.list_page_size,
                ),
                read=True,
            )
            for u in out.uploads or []:
                if u.initiated is not None and ops.parse_iso_timestamp(u.initiated) < cutoff:
                    await self.abort_multipart_upload(check.not_none(u.key), check.not_none(u.upload_id))
                    n += 1
            if not out.is_truncated:
                return n
            key_marker, upload_id_marker = out.next_key_marker, out.next_upload_id_marker


##


# Cloudflare R2. Endpoint: https://<account_id>.r2.cloudflarestorage.com, or
# https://<account_id>.<jurisdiction>.r2.cloudflarestorage.com (e.g. 'eu'), with region 'auto' and path-style
# addressing. R2 requires uniform part sizes, which the writer always produces. Conditional deletes are unverified, so
# off; so is aws-chunked streaming support, so don't enable streamed_uploads without checking.
R2_CONFIG = S3BlobStore.Config(
    capabilities=(
        blobs.BlobCapability.PUT_IF_ABSENT |
        blobs.BlobCapability.PUT_IF_MATCH |
        blobs.BlobCapability.COPY_IF_ABSENT |
        blobs.BlobCapability.COPY_IF_MATCH
    ),
    copy_dst_if_none_match_header='cf-copy-destination-if-none-match',
    copy_dst_if_match_header='cf-copy-destination-if-match',
)

# adobe/s3mock (5.2.3). Never claims the copy capabilities: s3mock silently ignores CopyObject destination
# preconditions. Separate from the default so that enabling them for AWS doesn't enable them here.
S3_MOCK_CONFIG = S3BlobStore.Config(
    capabilities=_DEFAULT_CAPABILITIES,
)
