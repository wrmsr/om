import dataclasses as dc
import json
import typing as ta
import urllib.error
import urllib.request

from omcore import check
from omcore import lang


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
            **{
                'Content-Type': 'application/json',
                'User-Agent': Consts.USER_AGENT,
            },
            **(headers or {}),
        },
    ))


##


class Consts(lang.Namespace):
    USER_AGENT = 'omcore-http-client/0.1'

    AUTH_BASE_URL = 'https://auth.openai.com'

    CLIENT_ID = 'app_EMoamEEZ73f0CkXaXp7hrann'


##


@dc.dataclass(frozen=True, kw_only=True)
class _DeviceAuthUserCode:
    device_auth_id: str  # deviceauth_0123abcd...
    user_code: str       # ABCD-EFGHI
    interval: int | float
    expires_at: str      # 2026-11-02T21:27:42.011383+00:00


def _get_device_auth_user_code() -> _DeviceAuthUserCode:
    resp = _post_json(
        f'{Consts.AUTH_BASE_URL}/api/accounts/deviceauth/usercode',
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


##


def _main() -> None:
    resp = _get_device_auth_user_code()

    print(resp)


if __name__ == '__main__':
    _main()
