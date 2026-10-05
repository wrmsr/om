"""
Probes which conditional operations an S3 endpoint actually enforces - as opposed to silently ignoring - to settle the
capabilities of a Config preset. Writes to a scratch prefix, which it cleans up.

    ./python -m x.blobs.aws.tests.probe s3mock --url http://127.0.0.1:9090 --bucket my-bucket
    ./python -m x.blobs.aws.tests.probe aws --region us-west-2 --bucket my-bucket
    ./python -m x.blobs.aws.tests.probe r2 --account-id abc123 --bucket my-bucket

AWS and R2 credentials come from the home secrets file: aws_access_key_id / aws_secret_access_key, and
blobs_test_r2_access_key_id / blobs_test_r2_secret_access_key.
"""
import argparse
import typing as ta
import uuid

from omcore import dataclasses as dc
from omcore import lang
from omcore.http import all as http
from ominfra.clouds.aws import auth as aws_auth

from .... import blobs
from ..endpoints import S3Endpoint
from ..stores import R2_CONFIG
from ..stores import S3_MOCK_CONFIG
from ..stores import S3BlobStore


with lang.auto_proxy_import(globals()):
    from omdev.home import secrets as home_secrets


##


@dc.dataclass(frozen=True, kw_only=True)
class ProbeResult:
    capability: str
    outcome: str  # 'enforced', 'ignored', 'unsupported', or 'error: ...'


async def _probe_one(fn: ta.Callable[[], ta.Awaitable[ta.Any]], expected: type[BaseException]) -> str:
    try:
        await fn()
    except expected:
        return 'enforced'
    except blobs.UnsupportedBlobOperationError:
        return 'unsupported'
    except Exception as e:  # noqa
        return f'error: {e!r}'
    return 'ignored'


async def probe_s3_capabilities(make_store: ta.Callable[[S3BlobStore.Config], S3BlobStore]) -> list[ProbeResult]:
    all_caps = blobs.ALL_BLOB_CAPABILITIES
    st = make_store(S3BlobStore.Config(capabilities=all_caps))
    r2ish = make_store(dc.replace(R2_CONFIG, capabilities=all_caps))
    p = f'blobs-probe/{uuid.uuid7().hex}/'
    stale = blobs.IfMatch(blobs.BlobVersion('"00000000000000000000000000000000"'))
    out: list[ProbeResult] = []

    try:
        await st.put(p + 'k', b'1')
        await st.put(p + 'src', b's')
        await st.put(p + 'dst', b'd')

        out.append(ProbeResult(capability='PUT_IF_ABSENT', outcome=await _probe_one(
            lambda: st.put(p + 'k', b'2', cond=blobs.IfAbsent()),
            blobs.BlobAlreadyExistsError,
        )))
        out.append(ProbeResult(capability='PUT_IF_MATCH', outcome=await _probe_one(
            lambda: st.put(p + 'k', b'3', cond=stale),
            blobs.BlobPreconditionFailedError,
        )))
        for name, s in [('aws headers', st), ('cf- headers', r2ish)]:
            out.append(ProbeResult(capability=f'COPY_IF_ABSENT ({name})', outcome=await _probe_one(
                lambda s=s: s.copy(p + 'src', p + 'dst', cond=blobs.IfAbsent()),  # type: ignore[misc]
                blobs.BlobAlreadyExistsError,
            )))
            await st.put(p + 'dst', b'd')
            out.append(ProbeResult(capability=f'COPY_IF_MATCH ({name})', outcome=await _probe_one(
                lambda s=s: s.copy(p + 'src', p + 'dst', cond=stale),  # type: ignore[misc]
                blobs.BlobPreconditionFailedError,
            )))
            await st.put(p + 'dst', b'd')
        out.append(ProbeResult(capability='DELETE_IF_MATCH', outcome=await _probe_one(
            lambda: st.delete(p + 'k', cond=stale),
            blobs.BlobPreconditionFailedError,
        )))

    finally:
        await st.delete_many([i.key async for i in st.list(prefix=p)])

    return out


##


def _secret(key: str) -> str:
    return home_secrets.load_secrets().get(key).reveal()


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('target', choices=['s3mock', 'aws', 'r2'])
    parser.add_argument('--bucket', required=True)
    parser.add_argument('--url')
    parser.add_argument('--region')
    parser.add_argument('--account-id')
    args = parser.parse_args()

    if args.target == 's3mock':
        endpoint = S3Endpoint(url=args.url or 'http://127.0.0.1:9090', region='us-east-1')
        creds = aws_auth.AwsSigner.Credentials('test', 'test')
        base = S3_MOCK_CONFIG
    elif args.target == 'aws':
        endpoint = S3Endpoint(url=f'https://s3.{args.region}.amazonaws.com', region=args.region)
        creds = aws_auth.AwsSigner.Credentials(_secret('aws_access_key_id'), _secret('aws_secret_access_key'))
        base = S3BlobStore.Config()
    else:
        endpoint = S3Endpoint(url=f'https://{args.account_id}.r2.cloudflarestorage.com', region='auto')
        creds = aws_auth.AwsSigner.Credentials(
            _secret('blobs_test_r2_access_key_id'),
            _secret('blobs_test_r2_secret_access_key'),
        )
        base = R2_CONFIG

    def make_store(config: S3BlobStore.Config) -> S3BlobStore:
        return S3BlobStore(
            bucket=args.bucket,
            endpoint=endpoint,
            credentials=creds,
            config=config,
            http_client=http.SyncAsyncHttpClient(http.client()),
        )

    results = lang.sync_await(probe_s3_capabilities(make_store))
    width = max(len(r.capability) for r in results)
    for r in results:
        print(f'{r.capability:<{width}}  {r.outcome}')
    print(f'\ncurrent preset for {args.target}: {base.capabilities!r}')


if __name__ == '__main__':
    _main()
