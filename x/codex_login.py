import dataclasses as dc
import json
import typing as ta
import urllib.error
import urllib.request

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
            },
            **(headers or {}),
        },
    ))


##


class Consts(lang.Namespace):
    AUTH_BASE_URL = 'https://auth.openai.com'

    CLIENT_ID = 'app_EMoamEEZ73f0CkXaXp7hrann'


##


def _main() -> None:
    resp = _post_json(
        f'{Consts.AUTH_BASE_URL}/api/accounts/deviceauth/usercode',
        {
            'client_id': Consts.CLIENT_ID,
        },
    )

    print(resp)


if __name__ == '__main__':
    _main()
