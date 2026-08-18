import abc
import typing as ta

from .... import check
from .... import dataclasses as dc
from .... import lang


##


@dc.dataclass(frozen=True, kw_only=True)
class SubinterpreterBootstrapInfo:
    interpreter_id: int
    gil_enabled: bool
    code_identity: str


@dc.dataclass(frozen=True, kw_only=True)
class SubinterpreterTarget:
    factory_name: str
    code_identity_name: str
    code_identity: str
    config_data: bytes

    module_search_paths: tuple[str, ...] = ()
    preload_modules: tuple[str, ...] = ()
    require_gil: bool = True
    allow_code_identity_mismatch: bool = False

    def __post_init__(self) -> None:
        check.non_empty_str(self.factory_name)
        check.non_empty_str(self.code_identity_name)
        check.non_empty_str(self.code_identity)
        check.isinstance(self.config_data, bytes)
        check.isinstance(self.module_search_paths, tuple)
        check.arg(all(isinstance(path, str) and path for path in self.module_search_paths))
        check.isinstance(self.preload_modules, tuple)
        check.arg(all(isinstance(module, str) and module for module in self.preload_modules))
        check.isinstance(self.require_gil, bool)
        check.isinstance(self.allow_code_identity_mismatch, bool)


class SubinterpreterService(lang.Abstract):
    @abc.abstractmethod
    def dispatch(
            self,
            method: str,
            args: tuple[ta.Any, ...],
            kwargs: ta.Mapping[str, ta.Any],
    ) -> ta.Any:
        raise NotImplementedError

    def close(self) -> None:
        pass


class SubinterpreterCaller(lang.Abstract):
    @property
    @abc.abstractmethod
    def bootstrap_info(self) -> SubinterpreterBootstrapInfo:
        raise NotImplementedError

    @abc.abstractmethod
    def invoke(
            self,
            method: str,
            args: tuple[ta.Any, ...] = (),
            kwargs: ta.Mapping[str, ta.Any] | None = None,
            *,
            timeout: lang.TimeoutLike = None,
    ) -> ta.Any:
        raise NotImplementedError


def validate_max_pending_calls(max_pending_calls: int) -> int:
    check.isinstance(max_pending_calls, int)
    check.arg(not isinstance(max_pending_calls, bool))
    check.arg(max_pending_calls > 0)
    return max_pending_calls
