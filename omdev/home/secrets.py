import os.path
import typing as ta

from omcore import lang
from omcore.configs.formats import DEFAULT_CONFIG_FILE_LOADER
from omcore.os.environ import EnvVar
from omcore.secrets import all as sec

from .paths import get_home_paths


##


INJECTED_SECRETS_FILE_ENV_VAR = EnvVar('OM_SECRETS')
DEFAULT_INJECTED_SECRETS_FILE_NAME: ta.Final = 'secrets-injected.json'

USER_SECRETS_FILE_ENV_VAR = EnvVar('OM_SECRETS_INJECTED')
DEFAULT_USER_SECRETS_FILE_NAME: ta.Final = 'secrets.yml'


def _get_secrets_file_paths() -> lang.SequenceNotStr[str]:
    return [
        os.path.expanduser(p)
        for ev, dfn in [
            (INJECTED_SECRETS_FILE_ENV_VAR, DEFAULT_INJECTED_SECRETS_FILE_NAME),
            (USER_SECRETS_FILE_ENV_VAR, DEFAULT_USER_SECRETS_FILE_NAME),
        ]
        for p_ in ev.get(lambda: os.path.join(get_home_paths().config_dir, dfn)).split(os.pathsep)
        if (p := p_.strip())
    ]


def load_secrets() -> sec.Secrets:
    dct: dict[str, sec.Secret] = {}
    for fp in _get_secrets_file_paths():
        try:
            for k, v in DEFAULT_CONFIG_FILE_LOADER.load_file(fp).as_map().items():
                if isinstance(v, str):
                    dct[k] = sec.Secret(key=k, value=v)
        except FileNotFoundError:
            pass
    return sec.MappingSecrets(dct)


##


def install_env_secrets(
        *keys: str | tuple[str, str],
        secrets: sec.Secrets | None = None,
        environ: ta.MutableMapping[str, str] | None = None,
        non_strict: bool = False,
) -> None:
    """This should not be used outside of being forced to interact with external code."""

    if not keys:
        raise ValueError('Must specify keys')

    sk_ek_tups: list[tuple[str, str]] = []
    for k in keys:
        if isinstance(k, tuple):
            sk, ek = k

        elif isinstance(k, str):
            if k.lower() == k:
                sk, ek = k, k.upper()
            elif k.upper() == k:
                sk, ek = k.lower(), k
            else:
                raise ValueError(k)

        else:
            raise TypeError(k)

        sk_ek_tups.append((sk, ek))

    if secrets is None:
        secrets = load_secrets()

    if environ is None:
        environ = os.environ

    for sk, ek in sk_ek_tups:
        try:
            sv = secrets.get(sk)
        except KeyError:
            if non_strict:
                continue
            raise

        environ[ek] = sv.reveal()
