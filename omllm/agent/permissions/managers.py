import abc
import typing as ta

from omcore import lang

from .collection import PermissionRules
from .types import PermissionMatchContext
from .types import PermissionRule


##


class PermissionsManager(lang.Abstract):
    @abc.abstractmethod
    def get_rules(self) -> PermissionRules:
        raise NotImplementedError

    @abc.abstractmethod
    def update_rules(self, fn: ta.Callable[[PermissionRules], PermissionRules]) -> PermissionRules:
        raise NotImplementedError

    @abc.abstractmethod
    def match(self, ctx: PermissionMatchContext) -> PermissionRule | None:
        raise NotImplementedError


##


class StandardPermissionsManager(PermissionsManager):
    def __init__(self, rules: ta.Sequence[PermissionRule] | None = None) -> None:
        super().__init__()

        self._rules = PermissionRules(rules or ())

    def get_rules(self) -> PermissionRules:
        return self._rules

    def update_rules(self, fn: ta.Callable[[PermissionRules], PermissionRules]) -> PermissionRules:
        self._rules = new_rules = fn(self._rules)
        return new_rules

    def match(self, ctx: PermissionMatchContext) -> PermissionRule | None:
        for r in self._rules:
            if r.matcher.match(ctx):
                return r
        return None
