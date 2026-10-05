import typing as ta
import uuid

from omcore import lang
from omcore.docker.all import get_compose_port
from omcore.docker.all import is_likely_in_docker
from omcore.docker.tests.services import ComposeServices
from omcore.http import all as http
from omcore.os.environ import EnvVar
from omcore.testing.pytest import inject as pti
from ominfra.clouds.aws import auth as aws_auth
from ominfra.clouds.aws.models.services import s3

from ..endpoints import S3Endpoint
from ..errors import S3ResponseError
from ..stores import S3_MOCK_CONFIG
from ..stores import S3BlobStore


##


# FIXME: this env var override is a temporary codestyle violation, to support ~/scripts/run-s3mock in agent sandboxes
#  (e.g. OM_TEST_S3_URL=http://127.0.0.1:9090). Drop it once the harness supports that natively.
S3_URL_ENV_VAR = EnvVar('OM_TEST_S3_URL')

S3MOCK_REGION = 'us-east-1'
S3MOCK_CREDENTIALS = aws_auth.AwsSigner.Credentials('test', 'test')  # s3mock accepts any


@pti.bind('session')
class HarnessS3:
    def __init__(self, compose_services: ComposeServices) -> None:
        super().__init__()

        self._compose_services = compose_services

    @lang.cached_function
    def endpoint(self) -> S3Endpoint:
        if url := S3_URL_ENV_VAR.get(None):
            return S3Endpoint(url=url, region=S3MOCK_REGION)
        svc = self._compose_services.config().get_services()['s3']
        if is_likely_in_docker():
            url = f'http://{self._compose_services.prefix}s3:9090'
        else:
            url = f'http://127.0.0.1:{get_compose_port(svc, 9090)}'
        return S3Endpoint(url=url, region=S3MOCK_REGION)

    @property
    def credentials(self) -> aws_auth.AwsSigner.Credentials:
        return S3MOCK_CREDENTIALS

    @lang.cached_function
    def bucket(self) -> str:
        """One bucket per session, created on first use - s3mock is started with none."""

        name = f'om-blobs-test-{uuid.uuid7().hex[:16]}'
        store = S3BlobStore(
            bucket=name,
            endpoint=self.endpoint(),
            credentials=self.credentials,
            config=S3_MOCK_CONFIG,
            http_client=http.SyncAsyncHttpClient(http.client()),
        )
        try:
            lang.sync_await(store._transport.execute(  # noqa
                s3.CREATE_BUCKET,
                s3.CreateBucketRequest(bucket=s3.BucketName(name)),
            ))
        except S3ResponseError as e:
            if e.code != 'BucketAlreadyOwnedByYou':
                raise
        return name

    def store(self, **kwargs: ta.Any) -> S3BlobStore:
        return S3BlobStore(
            bucket=self.bucket(),
            endpoint=self.endpoint(),
            credentials=self.credentials,
            **{'config': S3_MOCK_CONFIG, **kwargs},
        )
