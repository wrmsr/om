"""
Pure functions between blob-level calls and S3 request / response shapes. No IO, and no provider-specific branching: any
difference between S3 implementations arrives as an explicit parameter.
"""
import datetime
import email.utils
import logging
import re
import typing as ta
import urllib.parse

from omcore import check
from omcore import dataclasses as dc
from ominfra.clouds.aws import auth as aws_auth
from ominfra.clouds.aws.models.services import s3

from ... import blobs
from .errors import S3ResponseError


log = logging.getLogger(__name__)

T = ta.TypeVar('T')
U = ta.TypeVar('U')


##


def _opt(fn: ta.Callable[[T], U], v: T | None) -> U | None:
    return fn(v) if v is not None else None


def normalize_etag(etag: str) -> blobs.BlobVersion:
    e = etag.strip()
    if not e.startswith(('"', 'W/"')):
        e = f'"{e}"'
    return blobs.BlobVersion(e)


def parse_http_date(s: str) -> datetime.datetime:
    dt = email.utils.parsedate_to_datetime(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.UTC)
    return dt.astimezone(datetime.UTC)


def parse_iso_timestamp(s: str) -> datetime.datetime:
    dt = datetime.datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.UTC)
    return dt.astimezone(datetime.UTC)


def range_header(byte_range: blobs.BlobRange | None) -> str | None:
    match byte_range:
        case None | blobs.OffsetBlobRange(start=0, stop=None):
            return None
        case blobs.OffsetBlobRange(start=start, stop=None):
            return f'bytes={start}-'
        case blobs.OffsetBlobRange(start=start, stop=stop):
            return f'bytes={start}-{check.not_none(stop) - 1}'
        case blobs.SuffixBlobRange(length=length):
            return f'bytes=-{length}'
        case _:
            raise TypeError(byte_range)


_CONTENT_RANGE_PAT = re.compile(r'bytes\s+(?:(\d+)-(\d+)|\*)/(\d+|\*)')


def parse_content_range(s: str) -> tuple[int | None, int | None, int | None]:
    """Returns (first, last, total) - any of which may be None."""

    if (m := _CONTENT_RANGE_PAT.fullmatch(s.strip())) is None:
        raise ValueError(f'bad Content-Range: {s!r}')
    first, last, total = m.groups()
    return (
        int(first) if first is not None else None,
        int(last) if last is not None else None,
        int(total) if total not in (None, '*') else None,
    )


def clamp_range(size: int, byte_range: blobs.BlobRange | None) -> tuple[int, int]:
    match byte_range:
        case None:
            return 0, size
        case blobs.OffsetBlobRange(start=start, stop=stop):
            s = min(start, size)
            e = size if stop is None else min(stop, size)
            return s, max(s, e)
        case blobs.SuffixBlobRange(length=length):
            return max(0, size - length), size
        case _:
            raise TypeError(byte_range)


def read_precondition(cond: blobs.BlobReadPrecondition | None) -> tuple[str | None, str | None]:
    """Returns (If-Match, If-None-Match)."""

    match cond:
        case None:
            return None, None
        case blobs.IfMatch(version=v):
            return v.etag, None
        case blobs.IfNoneMatch(version=v):
            return None, v.etag
        case _:
            raise TypeError(cond)


def write_precondition(cond: blobs.BlobWritePrecondition | None) -> tuple[str | None, str | None]:
    """Returns (If-Match, If-None-Match)."""

    match cond:
        case None:
            return None, None
        case blobs.IfMatch(version=v):
            return v.etag, None
        case blobs.IfAbsent():
            return None, '*'
        case _:
            raise TypeError(cond)


##


def build_head(bucket: str, key: str, cond: blobs.BlobReadPrecondition | None) -> s3.HeadObjectRequest:
    im, inm = read_precondition(cond)
    return s3.HeadObjectRequest(
        bucket=s3.BucketName(bucket),
        key=s3.ObjectKey(key),
        if_match=_opt(s3.IfMatch, im),
        if_none_match=_opt(s3.IfNoneMatch, inm),
    )


def info_from_head(key: str, out: s3.HeadObjectOutput) -> blobs.BlobInfo:
    return blobs.BlobInfo(
        key=key,
        size=check.not_none(out.content_length),
        version=normalize_etag(check.not_none(out.etag)),
        last_modified=parse_http_date(check.not_none(out.last_modified)),
    )


def build_get(
        bucket: str,
        key: str,
        byte_range: blobs.BlobRange | None,
        cond: blobs.BlobReadPrecondition | None,
) -> s3.GetObjectRequest:
    im, inm = read_precondition(cond)
    return s3.GetObjectRequest(
        bucket=s3.BucketName(bucket),
        key=s3.ObjectKey(key),
        range=_opt(s3.Range, range_header(byte_range)),
        if_match=_opt(s3.IfMatch, im),
        if_none_match=_opt(s3.IfNoneMatch, inm),
    )


def blob_from_get(
        key: str,
        status: int,
        out: s3.GetObjectOutput,
        byte_range: blobs.BlobRange | None,
) -> blobs.Blob:
    data = out.body or b''
    if status == 206 and out.content_range is not None:
        total = parse_content_range(out.content_range)[2]
        size = check.not_none(total)
    else:
        size = out.content_length if out.content_length is not None else len(data)
        if range_header(byte_range) is not None:
            # The server ignored the Range - slice locally.
            s, e = clamp_range(len(data), byte_range)
            data = data[s:e]
            size = len(out.body or b'')
    return blobs.Blob(
        info=blobs.BlobInfo(
            key=key,
            size=size,
            version=normalize_etag(check.not_none(out.etag)),
            last_modified=parse_http_date(check.not_none(out.last_modified)),
        ),
        data=bytes(data),
    )


##


def build_list(
        bucket: str,
        *,
        prefix: str,
        start_after: str | None,
        continuation_token: str | None,
        delimiter: str | None,
        max_keys: int,
        no_url_encoding: bool,
) -> s3.ListObjectsV2Request:
    return s3.ListObjectsV2Request(
        bucket=s3.BucketName(bucket),
        prefix=_opt(s3.Prefix, prefix or None),
        start_after=_opt(s3.StartAfter, start_after if continuation_token is None else None),
        continuation_token=_opt(s3.Token, continuation_token),
        delimiter=_opt(s3.Delimiter, delimiter),
        max_keys=s3.MaxKeys(max_keys),
        encoding_type=None if no_url_encoding else s3.EncodingType.URL,
    )


@dc.dataclass(frozen=True, kw_only=True)
class ListPage:
    infos: ta.Sequence[blobs.BlobInfo]
    prefixes: ta.Sequence[str]
    next_token: str | None


def _decode_listed(s: str, url_encoded: bool) -> str:
    # S3 url-encodes a space as '+' (s3mock as %20) - unquote_plus handles both.
    return urllib.parse.unquote_plus(s) if url_encoded else s


def _valid_key(k: str) -> bool:
    try:
        blobs.check_blob_key(k)
    except blobs.InvalidBlobKeyError:
        log.debug('skipping listed key not addressable as a blob key: %r', k)
        return False
    return True


def page_from_list(out: s3.ListObjectsV2Output) -> ListPage:
    enc = out.encoding_type in (s3.EncodingType.URL, 'url')
    infos: list[blobs.BlobInfo] = []
    for o in out.contents or []:
        k = _decode_listed(check.not_none(o.key), enc)
        if not _valid_key(k):
            continue
        infos.append(blobs.BlobInfo(
            key=k,
            size=check.not_none(o.size),
            version=normalize_etag(check.not_none(o.etag)),
            last_modified=parse_iso_timestamp(check.not_none(o.last_modified)),
        ))
    prefixes = [_decode_listed(check.not_none(p.prefix), enc) for p in out.common_prefixes or []]
    return ListPage(
        infos=infos,
        prefixes=prefixes,
        next_token=out.next_continuation_token if out.is_truncated else None,
    )


##


def build_put(bucket: str, key: str, data: bytes, cond: blobs.BlobWritePrecondition | None) -> s3.PutObjectRequest:
    im, inm = write_precondition(cond)
    return s3.PutObjectRequest(
        bucket=s3.BucketName(bucket),
        key=s3.ObjectKey(key),
        body=s3.Body(data),
        if_match=_opt(s3.IfMatch, im),
        if_none_match=_opt(s3.IfNoneMatch, inm),
    )


def build_copy(
        bucket: str,
        src: str,
        dst: str,
        cond: blobs.BlobWritePrecondition | None,
        *,
        dst_if_none_match_header: str,
        dst_if_match_header: str,
) -> tuple[s3.CopyObjectRequest, list[tuple[str, str]]]:
    """Returns the request and the extra headers carrying destination preconditions, under the given header names."""

    im, inm = write_precondition(cond)
    extra: list[tuple[str, str]] = []
    if im is not None:
        extra.append((dst_if_match_header, im))
    if inm is not None:
        extra.append((dst_if_none_match_header, inm))
    return s3.CopyObjectRequest(
        bucket=s3.BucketName(bucket),
        key=s3.ObjectKey(dst),
        copy_source=s3.CopySource(f'/{bucket}/{aws_auth.aws_uri_encode(src, encode_slash=False)}'),
    ), extra


def version_from_copy(out: s3.CopyObjectOutput) -> blobs.BlobVersion:
    return normalize_etag(check.not_none(check.not_none(out.copy_object_result).etag))


def build_delete(bucket: str, key: str, cond: blobs.IfMatch | None) -> s3.DeleteObjectRequest:
    return s3.DeleteObjectRequest(
        bucket=s3.BucketName(bucket),
        key=s3.ObjectKey(key),
        if_match=s3.IfMatch(cond.version.etag) if cond is not None else None,
    )


def build_delete_objects(bucket: str, keys: ta.Sequence[str]) -> s3.DeleteObjectsRequest:
    return s3.DeleteObjectsRequest(
        bucket=s3.BucketName(bucket),
        delete=s3.Delete(objects=[s3.ObjectIdentifier(key=s3.ObjectKey(k)) for k in keys], quiet=s3.Quiet(True)),
    )


def errors_from_delete_objects(out: s3.DeleteObjectsOutput) -> dict[str, blobs.BlobStoreError]:
    return {
        check.not_none(e.key): S3ResponseError(status=200, code=e.code, message=e.message, op='delete_many')
        for e in out.errors or []
    }


##


def build_create_multipart(bucket: str, key: str) -> s3.CreateMultipartUploadRequest:
    return s3.CreateMultipartUploadRequest(bucket=s3.BucketName(bucket), key=s3.ObjectKey(key))


def build_upload_part(bucket: str, key: str, upload_id: str, part_number: int, data: bytes) -> s3.UploadPartRequest:
    return s3.UploadPartRequest(
        bucket=s3.BucketName(bucket),
        key=s3.ObjectKey(key),
        upload_id=s3.MultipartUploadId(upload_id),
        part_number=s3.PartNumber(part_number),
        body=s3.Body(data),
    )


def build_complete_multipart(
        bucket: str,
        key: str,
        upload_id: str,
        parts: ta.Sequence[tuple[int, str]],
        cond: blobs.BlobWritePrecondition | None,
) -> s3.CompleteMultipartUploadRequest:
    im, inm = write_precondition(cond)
    return s3.CompleteMultipartUploadRequest(
        bucket=s3.BucketName(bucket),
        key=s3.ObjectKey(key),
        upload_id=s3.MultipartUploadId(upload_id),
        multipart_upload=s3.CompletedMultipartUpload(
            parts=[s3.CompletedPart(part_number=s3.PartNumber(n), etag=s3.ETag(e)) for n, e in sorted(parts)],
        ),
        if_match=_opt(s3.IfMatch, im),
        if_none_match=_opt(s3.IfNoneMatch, inm),
    )


def build_abort_multipart(bucket: str, key: str, upload_id: str) -> s3.AbortMultipartUploadRequest:
    return s3.AbortMultipartUploadRequest(
        bucket=s3.BucketName(bucket),
        key=s3.ObjectKey(key),
        upload_id=s3.MultipartUploadId(upload_id),
    )


def build_list_multipart_uploads(
        bucket: str,
        *,
        prefix: str,
        key_marker: str | None,
        upload_id_marker: str | None,
        max_uploads: int,
) -> s3.ListMultipartUploadsRequest:
    return s3.ListMultipartUploadsRequest(
        bucket=s3.BucketName(bucket),
        prefix=_opt(s3.Prefix, prefix or None),
        key_marker=_opt(s3.KeyMarker, key_marker),
        upload_id_marker=_opt(s3.UploadIdMarker, upload_id_marker),
        max_uploads=s3.MaxUploads(max_uploads),
    )


##


def map_error(
        op: str,
        e: S3ResponseError,
        *,
        key: str,
        cond: blobs.BlobPrecondition | None,
) -> BaseException:
    """
    Maps an S3 error response for a blob operation - 'head', 'get', 'put', 'complete', 'copy', 'delete' - to a blob
    error, or returns it unchanged. See the S3 response mapping table in FOLLOWUP.md.
    """

    status, code = e.status, e.code
    if status == 404 and code == 'NoSuchBucket':
        return e
    if status == 501 and cond is not None and op in ('put', 'complete', 'copy', 'delete'):
        return blobs.UnsupportedBlobOperationError(f'{op} precondition not implemented by the server: {code}')
    if status == 409 and code == 'ConditionalRequestConflict':
        return blobs.BlobConflictError(key)

    if op in ('head', 'get'):
        if status == 304:
            return blobs.BlobNotModifiedError(key)
        if status == 412:
            return blobs.BlobPreconditionFailedError(key)
        if status == 404:
            if isinstance(cond, blobs.IfMatch):
                return blobs.BlobPreconditionFailedError(key)
            return blobs.BlobNotFoundError(key)

    elif op in ('put', 'complete', 'copy'):
        if status == 412:
            if isinstance(cond, blobs.IfAbsent):
                return blobs.BlobAlreadyExistsError(key)
            return blobs.BlobPreconditionFailedError(key)
        if op != 'copy' and status == 404 and code in ('NoSuchKey', None) and isinstance(cond, blobs.IfMatch):
            return blobs.BlobPreconditionFailedError(key)

    elif op == 'delete':
        if status == 412:
            return blobs.BlobPreconditionFailedError(key)
        if status == 404 and isinstance(cond, blobs.IfMatch):
            return blobs.BlobPreconditionFailedError(key)

    return e
