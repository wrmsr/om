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
    def add_rule(self, rule: PermissionRule) -> None:
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

    def add_rule(self, rule: PermissionRule) -> None:
        self._rules = PermissionRules([*self._rules, rule])

    def match(self, ctx: PermissionMatchContext) -> PermissionRule | None:
        for r in self._rules:
            if r.matcher.match(ctx):
                return r
        return None
