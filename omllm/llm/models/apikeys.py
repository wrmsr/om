import abc
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import dispatch
from omcore import lang
from omcore.secrets import all as sec


##


@dc.dataclass(frozen=True, kw_only=True)
class ApiKey(lang.Abstract, lang.Sealed):
    pass


@ta.final
@dc.dataclass(frozen=True)
class SecretApiKey(ApiKey):
    name: str


@ta.final
@dc.dataclass(frozen=True)
class EnvVarApiKey(ApiKey):
    name: str


##


def secret_or_env_var_api_key(secret_name: str) -> ta.Sequence[ApiKey]:
    check.non_empty_str(secret_name)
    check.equal(secret_name, secret_name.lower())

    return (
        SecretApiKey(secret_name),
        EnvVarApiKey(secret_name.upper()),
    )


##


class ApiKeyResolver(lang.Abstract):
    @abc.abstractmethod
    def resolve_api_key(self, key: ApiKey) -> sec.Secret | None:
        raise NotImplementedError

    def resolve_first_api_key(self, keys: ta.Sequence[ApiKey]) -> sec.Secret | None:
        for key in keys:
            if (ret := self.resolve_api_key(key)) is not None:
                return ret
        return None


#


class ApiKeyResolverImpl(ApiKeyResolver):
    class Environ(ta.Protocol):
        def __getitem__(self, key: str) -> str: ...

    def __init__(
            self,
            *,
            secrets: sec.Secrets | None = None,
            environ: Environ | None = None,
    ) -> None:
        super().__init__()

        self._secrets = secrets
        self._environ = environ

    @dispatch.method()
    def resolve_api_key(self, key: ApiKey) -> sec.Secret | None:
        raise TypeError(key)

    @resolve_api_key.register
    def _resolve_secret_api_key(self, key: SecretApiKey) -> sec.Secret | None:
        if self._secrets is None:
            return None
        return self._secrets.get(key.name)

    @resolve_api_key.register
    def _resolve_env_var_api_key(self, key: EnvVarApiKey) -> sec.Secret | None:
        if self._environ is None:
            return None
        try:
            return sec.Secret(key=key.name, value=self._environ[key.name])
        except KeyError:
            return None
