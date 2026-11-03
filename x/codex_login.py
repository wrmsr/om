# ruff: noqa: S310
import abc
import base64
import dataclasses as dc
import datetime
import os.path
import time
import typing as ta
import urllib.error
import urllib.parse
import urllib.request

from omcore import check
from omcore import lang
from omcore import marshal as msh
from omcore.asyncs.asynclite import all as asl
from omcore.formats.json import all as json
from omcore.http import all as http
from omcore.secrets import all as sec
from omdev.home.paths import get_home_paths


##


@dc.dataclass(frozen=True, kw_only=True)
class OpenaiOauthTokens:
    access_token: str
    id_token: str


@dc.dataclass(frozen=True, kw_only=True)
@msh.update_field_options(omit_if=lang.is_none)
class OpenaiOauthEnvelope:
    tokens: OpenaiOauthTokens

    created_at: datetime.datetime  # FIXME: all utc
    expires_at: datetime.datetime | None = None

    refresh_token: str | None = None
    earliest_refresh_at: datetime.datetime | None = None
    refreshed_at: datetime.datetime | None = None


##


class OpenaiOauthConsts(lang.Namespace):
    AUTH_BASE_URL = 'https://auth.openai.com'

    CLIENT_ID = 'app_EMoamEEZ73f0CkXaXp7hrann'

    USER_AGENT = 'omcore-http-client/0.1'

    #

    POST_TOKEN_URL = f'{AUTH_BASE_URL}/oauth/token'

    #

    DEVICE_AUTH_USER_CODE_URL = f'{AUTH_BASE_URL}/api/accounts/deviceauth/usercode'
    DEVICE_AUTH_TOKEN_URL = f'{AUTH_BASE_URL}/api/accounts/deviceauth/token'
    DEVICE_AUTH_REDIRECT_URL = f'{AUTH_BASE_URL}/deviceauth/callback'

    DEVICE_AUTH_VERIFY_URL = f'{AUTH_BASE_URL}/codex/device'

    DEVICE_AUTH_POLL_TIMEOUT_S = 15 * 60

    #

    ACCOUNT_ID_JWT_CLAIM_KEY = 'chatgpt_account_id'
    AUTH_NS_JWT_CLAIM_KEY = 'https://api.openai.com/auth'


##


class DeviceCodeOpenaiOauthLogin(lang.Abstract):
    @dc.dataclass(frozen=True, kw_only=True)
    class UserCode:
        user_code: str
        verify_url: str

    @abc.abstractmethod
    def device_auth(
            self,
            *,
            display_user_code: ta.Callable[[UserCode], ta.Awaitable[None]] | None = None,
    ) -> ta.Awaitable[OpenaiOauthEnvelope]:
        raise NotImplementedError


#


class DeviceCodeOpenaiOauthLoginImpl(DeviceCodeOpenaiOauthLogin):
    def __init__(
            self,
            *,
            http_client: http.AsyncHttpClient | None = None,
            sleeps: asl.Sleeps,
    ) -> None:
        super().__init__()

        self._http_client = http_client
        self._sleeps = sleeps

    #

    async def _post_json(
            self,
            url: str,
            obj: ta.Any,
            *,
            headers: ta.Mapping[str, str] | None = None,
    ) -> http.HttpClientResponse:
        return await http.async_request(
            url,
            'POST',
            data=json.dumps(obj).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'User-Agent': OpenaiOauthConsts.USER_AGENT,
                **(headers or {}),
            },
            client=self._http_client,
        )

    async def _post_form(
            self,
            url: str,
            fields: ta.Mapping[str, ta.Any],
            *,
            headers: ta.Mapping[str, str] | None = None,
    ) -> http.HttpClientResponse:
        return await http.async_request(
            url,
            'POST',
            data=urllib.parse.urlencode(fields).encode('utf-8'),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': OpenaiOauthConsts.USER_AGENT,
                **(headers or {}),
            },
            client=self._http_client,
        )

    #

    @dc.dataclass(frozen=True, kw_only=True)
    class _DeviceAuthUserCode:
        device_auth_id: str  # deviceauth_0123abcd...
        user_code: str  # ABCD-EFGHI
        interval: int | float
        expires_at: datetime.datetime  # 2026-11-02T21:27:42.011383+00:00

    async def _get_device_auth_user_code(self) -> _DeviceAuthUserCode:
        resp = await self._post_json(
            OpenaiOauthConsts.DEVICE_AUTH_USER_CODE_URL,
            {
                'client_id': OpenaiOauthConsts.CLIENT_ID,
            },
        )

        check.state(resp.status == 200)
        obj = json.loads(check.not_none(resp.data).decode('utf-8'))

        return self._DeviceAuthUserCode(
            device_auth_id=check.non_empty_str(obj['device_auth_id']),
            user_code=check.non_empty_str(obj['user_code']),
            interval=float(obj['interval']),
            expires_at=datetime.datetime.fromisoformat(check.non_empty_str(obj['expires_at'])),
        )

    #

    @dc.dataclass(frozen=True, kw_only=True)
    class _PollDeviceAuthTokenResult:
        status: str  # 'success'
        user_code: str  # ABCD-EFGHI
        user_code_expiration: datetime.datetime  # 2026-11-02T21:42:24.971193+00:00
        authorization_code: str
        code_challenge: str
        code_verifier: str

    async def _poll_device_auth_token(self, user_code: _DeviceAuthUserCode) -> _PollDeviceAuthTokenResult:
        deadline = time.time() + OpenaiOauthConsts.DEVICE_AUTH_POLL_TIMEOUT_S
        while True:
            resp = await self._post_json(
                OpenaiOauthConsts.DEVICE_AUTH_TOKEN_URL,
                {
                    'device_auth_id': user_code.device_auth_id,
                    'user_code': user_code.user_code,
                },
            )

            if resp.status not in (403, 404):
                break

            remaining = deadline - time.time()
            check.state(remaining > 0)
            time.sleep(min(user_code.interval, remaining))

        check.state(resp.status == 200)
        obj = json.loads(check.not_none(resp.data).decode('utf-8'))

        return self._PollDeviceAuthTokenResult(
            status=check.non_empty_str(obj['status']),
            user_code=check.non_empty_str(obj['user_code']),
            user_code_expiration=datetime.datetime.fromisoformat(check.non_empty_str(obj['user_code_expiration'])),
            authorization_code=check.non_empty_str(obj['authorization_code']),
            code_challenge=check.non_empty_str(obj['code_challenge']),
            code_verifier=check.non_empty_str(obj['code_verifier']),
        )

    #

    @dc.dataclass(frozen=True, kw_only=True)
    class _PostAuthTokenResult:
        access_token: str
        token_type: str  # "Bearer"
        expires_in: int | float  # 864000 (10 days)
        scope: str  # "openid profile email offline_access"
        id_token: str
        earliest_refresh_at: int | float  # 1794433452 (+3 days)
        refresh_token: str

    async def _post_auth_token(
            self,
            *,
            code: str,
            code_verifier: str,
            redirect_uri: str,
    ) -> _PostAuthTokenResult:
        resp = await self._post_form(
            OpenaiOauthConsts.POST_TOKEN_URL,
            {
                'client_id': OpenaiOauthConsts.CLIENT_ID,
                'grant_type': 'authorization_code',
                'code': code,
                'code_verifier': code_verifier,
                'redirect_uri': redirect_uri,
            },
        )

        check.state(resp.status == 200)
        obj = json.loads(check.not_none(resp.data).decode('utf-8'))

        return self._PostAuthTokenResult(
            access_token=check.non_empty_str(obj['access_token']),
            token_type=check.non_empty_str(obj['token_type']),
            expires_in=float(obj['expires_in']),
            scope=check.non_empty_str(obj['scope']),
            id_token=check.non_empty_str(obj['id_token']),
            earliest_refresh_at=float(obj['earliest_refresh_at']),
            refresh_token=check.non_empty_str(obj['refresh_token']),
        )

    #

    def _build_auth_envelope(self, post_result: _PostAuthTokenResult) -> OpenaiOauthEnvelope:
        return OpenaiOauthEnvelope(
            tokens=OpenaiOauthTokens(
                access_token=check.non_empty_str(post_result.access_token),
                id_token=check.non_empty_str(post_result.id_token),
            ),

            created_at=lang.utcnow(),
            expires_at=lang.utcnow() + datetime.timedelta(seconds=post_result.expires_in),

            refresh_token=check.non_empty_str(post_result.refresh_token),
            earliest_refresh_at=lang.utcfromtimestamp(post_result.earliest_refresh_at),
        )

    #

    async def device_auth(
            self,
            *,
            display_user_code: ta.Callable[[DeviceCodeOpenaiOauthLogin.UserCode], ta.Awaitable[None]] | None = None,
    ) -> OpenaiOauthEnvelope:
        user_code = await self._get_device_auth_user_code()

        if display_user_code is not None:
            await display_user_code(self.UserCode(
                user_code=user_code.user_code,
                verify_url=OpenaiOauthConsts.DEVICE_AUTH_VERIFY_URL,
            ))

        poll_result = await self._poll_device_auth_token(user_code)

        post_result = await self._post_auth_token(
            code=poll_result.authorization_code,
            code_verifier=poll_result.code_verifier,
            redirect_uri=OpenaiOauthConsts.DEVICE_AUTH_REDIRECT_URL,
        )

        auth = self._build_auth_envelope(post_result)

        return auth


##


def get_auth_file_path() -> str:
    return os.path.join(get_home_paths().state_dir, 'llm', 'codex-auth.json')


def write_auth(auth: OpenaiOauthEnvelope) -> None:
    auth_file_path = get_auth_file_path()
    os.makedirs(os.path.dirname(auth_file_path), exist_ok=True)
    with open(auth_file_path, 'w') as f:
        os.chmod(auth_file_path, 0o640)
        f.write(json.dumps_pretty(msh.marshal(auth)))


def read_auth() -> OpenaiOauthEnvelope | None:
    auth_file_path = get_auth_file_path()
    try:
        with open(auth_file_path) as f:
            src = f.read()
    except FileNotFoundError:
        return None
    return msh.unmarshal(json.loads(src), OpenaiOauthEnvelope)


##


def _jwt_claims(token: str) -> dict:
    payload = token.split('.')[1]
    payload += '=' * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


def _account_id(id_token: str) -> str | None:
    claims = _jwt_claims(id_token)

    try:
        return claims[OpenaiOauthConsts.ACCOUNT_ID_JWT_CLAIM_KEY]
    except KeyError:
        pass

    if isinstance(ns := claims.get(OpenaiOauthConsts.AUTH_NS_JWT_CLAIM_KEY), ta.Mapping):
        try:
            return ns[OpenaiOauthConsts.ACCOUNT_ID_JWT_CLAIM_KEY]
        except KeyError:
            pass

    return None


##


from omllm import llm  # noqa


def do_request(
        auth_tokens: OpenaiOauthTokens,
        context: llm.Context,
        options: llm.Options | None = None,
) -> llm.AiMessage:

    be = llm.OpenaiResponsesStreamBackend(
        model=llm.provider_model_catalog()[llm.default_models_by_name()['luna'].key],
        oauth_tokens=llm.OpenaiResponsesImmediateBackend.OauthTokens(
            access_token=sec.Secret(value=auth_tokens.access_token),
            account_id=sec.Secret(value=check.not_none(_account_id(auth_tokens.id_token))),
            originator='pi',
        ),
        http_client=http.SyncAsyncHttpClient(http.client()),
        base_url='https://chatgpt.com/backend-api/codex',
    )

    return lang.sync_await(be.immediate(context, options))


##


# DO_LOGIN = False
DO_LOGIN = True


def _main() -> None:
    if DO_LOGIN:
        def print_user_code(uc: DeviceCodeOpenaiOauthLogin.UserCode) -> None:
            print(uc.verify_url)
            print(uc.user_code)

        auth = lang.sync_await(DeviceCodeOpenaiOauthLoginImpl(
            http_client=http.SyncAsyncHttpClient(http.client()),
            sleeps=asl.sync.Sleeps(),
        ).device_auth(
            display_user_code=lang.as_async(print_user_code),
        ))

        write_auth(auth)

    auth = check.not_none(read_auth())

    resp = do_request(
        auth.tokens,
        llm.Context(
            messages=[
                llm.UserMessage('hi!'),
            ],
        )
    )
    print(resp)


if __name__ == '__main__':
    _main()
