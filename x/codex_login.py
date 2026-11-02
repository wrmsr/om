# ruff: noqa: S310
import dataclasses as dc
import json
import time
import typing as ta
import urllib.error
import urllib.parse
import urllib.request

from omcore import check
from omcore import lang


##


class Consts(lang.Namespace):
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



##


@dc.dataclass(frozen=True)
class _UrlResponse:
    status: int
    data: bytes

    @lang.cached_function
    def text(self) -> str:
        return self.data.decode('utf-8')

    @lang.cached_function
    def json(self) -> ta.Any:
        return json.loads(self.text())


def _url_request(req: urllib.request.Request) -> _UrlResponse:
    try:
        with urllib.request.urlopen(req) as r:
            return _UrlResponse(r.status, r.read())
    except urllib.error.HTTPError as e:
        return _UrlResponse(e.code, e.read())


def _post_json(
        url: str,
        obj: ta.Any,
        *,
        headers: ta.Mapping[str, str] | None = None,
) -> _UrlResponse:
    return _url_request(urllib.request.Request(
        url,
        data=json.dumps(obj).encode('utf-8'),  # noqa
        headers={
            'Content-Type': 'application/json',
            'User-Agent': Consts.USER_AGENT,
            **(headers or {}),
        },
    ))


def _post_form(
        url: str,
        fields: ta.Mapping[str, ta.Any],
        *,
        headers: ta.Mapping[str, str] | None = None,
) -> _UrlResponse:
    return _url_request(urllib.request.Request(
        url,
        data=urllib.parse.urlencode(fields).encode('utf-8'),  # noqa
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': Consts.USER_AGENT,
            **(headers or {}),
        },
    ))


##


@dc.dataclass(frozen=True, kw_only=True)
class _PostAuthTokenResult:
    access_token: str
    token_type: str  # "Bearer"
    expires_in: int | float  # 864000
    scope: str  # "openid profile email offline_access"
    id_token: str
    earliest_refresh_at: int | float  # 1794433452
    refresh_token: str


def _post_auth_token(
        *,
        code: str,
        code_verifier: str,
        redirect_uri: str,
) -> _PostAuthTokenResult:
    resp = _post_form(
        Consts.POST_TOKEN_URL,
        {
            'client_id': Consts.CLIENT_ID,
            'grant_type': 'authorization_code',
            'code': code,
            'code_verifier': code_verifier,
            'redirect_uri': redirect_uri,
        },
    )

    check.state(resp.status == 200)
    obj = resp.json()

    return _PostAuthTokenResult(
        access_token=check.non_empty_str(obj['access_token']),
        token_type=check.non_empty_str(obj['token_type']),
        expires_in=float(obj['expires_in']),
        scope=check.non_empty_str(obj['scope']),
        id_token=check.non_empty_str(obj['id_token']),
        earliest_refresh_at=float(obj['earliest_refresh_at']),
        refresh_token=check.non_empty_str(obj['refresh_token']),
    )


@dc.dataclass(frozen=True, kw_only=True)
class AuthTokens:
    access_token: str
    id_token: str
    refresh_token: str


def _build_auth_tokens(post_result: _PostAuthTokenResult) -> AuthTokens:
    return AuthTokens(
        access_token=check.non_empty_str(post_result.access_token),
        id_token=check.non_empty_str(post_result.id_token),
        refresh_token=check.non_empty_str(post_result.refresh_token),
    )


##


@dc.dataclass(frozen=True, kw_only=True)
class _DeviceAuthUserCode:
    device_auth_id: str  # deviceauth_0123abcd...
    user_code: str  # ABCD-EFGHI
    interval: int | float
    expires_at: str  # 2026-11-02T21:27:42.011383+00:00


def _get_device_auth_user_code() -> _DeviceAuthUserCode:
    resp = _post_json(
        Consts.DEVICE_AUTH_USER_CODE_URL,
        {
            'client_id': Consts.CLIENT_ID,
        },
    )

    check.state(resp.status == 200)
    obj = resp.json()

    return _DeviceAuthUserCode(
        device_auth_id=check.non_empty_str(obj['device_auth_id']),
        user_code=check.non_empty_str(obj['user_code']),
        interval=float(obj['interval']),
        expires_at=check.non_empty_str(obj['expires_at']),
    )


@dc.dataclass(frozen=True, kw_only=True)
class _PollDeviceAuthTokenResult:
    status: str  # 'success'
    user_code: str  # ABCD-EFGHI
    user_code_expiration: str  # 2026-11-02T21:42:24.971193+00:00
    authorization_code: str
    code_challenge: str
    code_verifier: str


def _poll_device_auth_token(user_code: _DeviceAuthUserCode) -> _PollDeviceAuthTokenResult:
    deadline = time.time() + Consts.DEVICE_AUTH_POLL_TIMEOUT_S
    while True:
        resp = _post_json(
            Consts.DEVICE_AUTH_TOKEN_URL,
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
        continue

    check.state(resp.status == 200)
    obj = resp.json()

    return _PollDeviceAuthTokenResult(
        status=check.non_empty_str(obj['status']),
        user_code=check.non_empty_str(obj['user_code']),
        user_code_expiration=check.non_empty_str(obj['user_code_expiration']),
        authorization_code=check.non_empty_str(obj['authorization_code']),
        code_challenge=check.non_empty_str(obj['code_challenge']),
        code_verifier=check.non_empty_str(obj['code_verifier']),
    )


def device_auth() -> None:
    user_code = _get_device_auth_user_code()

    print(f'{Consts.DEVICE_AUTH_VERIFY_URL}')
    print(user_code.user_code)

    poll_result = _poll_device_auth_token(user_code)

    post_result = _post_auth_token(
        code=poll_result.authorization_code,
        code_verifier=poll_result.code_verifier,
        redirect_uri=Consts.DEVICE_AUTH_REDIRECT_URL,
    )

    tokens = _build_auth_tokens(post_result)

    print(tokens)


##


def _main() -> None:
    device_auth()


if __name__ == '__main__':
    _main()
