import os.path

from omcore import check
from omcore import lang
from omcore import marshal as msh
from omcore.asyncs.asynclite import all as asl
from omcore.formats.json import all as json
from omcore.http import all as http
from omcore.secrets import all as sec
from omdev.home.paths import get_home_paths

from ...... import llm
from ...oauth import DeviceCodeOpenaiOauthLogin
from ...oauth import DeviceCodeOpenaiOauthLoginImpl
from ...oauth import OpenaiOauthEnvelope
from ...oauth import OpenaiOauthTokens


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


def do_request(
        auth_tokens: OpenaiOauthTokens,
        context: llm.Context,
        options: llm.Options | None = None,
) -> llm.AiMessage:

    be = llm.OpenaiResponsesStreamBackend(
        model=llm.provider_model_catalog()[llm.default_models_by_name()['luna'].key],
        oauth_tokens=llm.OpenaiResponsesImmediateBackend.OauthTokens(
            access_token=sec.Secret(value=auth_tokens.access_token),
            account_id=sec.Secret(value=check.not_none(auth_tokens.account_id())),
            originator='pi',
        ),
        http_client=http.SyncAsyncHttpClient(http.client()),
        base_url='https://chatgpt.com/backend-api/codex',
    )

    return lang.sync_await(be.immediate(context, options))


##


DO_LOGIN = False
# DO_LOGIN = True


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
        ),
    )
    print(resp)


if __name__ == '__main__':
    _main()
