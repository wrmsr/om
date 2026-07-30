import abc
import typing as ta

from omcore import lang

from .collection import PermissionRules
from .types import PermissionRule
from .types import PermissionTarget


##


class PermissionsManager(lang.Abstract):
    @abc.abstractmethod
    def get_rules(self) -> PermissionRules:
        raise NotImplementedError

    @abc.abstractmethod
    def add_rule(self, rule: PermissionRule) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def match_target(self, target: PermissionTarget) -> PermissionRule | None:
        raise NotImplementedError


##


class SimplePermissionsManager(PermissionsManager):
    def __init__(self, rules: ta.Sequence[PermissionRule] | None = None) -> None:
        super().__init__()

        self._rules = PermissionRules(rules or ())

    def get_rules(self) -> PermissionRules:
        return self._rules

    def add_rule(self, rule: PermissionRule) -> None:
        self._rules = PermissionRules([*self._rules, rule])

    def match_target(self, target: PermissionTarget) -> PermissionRule | None:
        for r in self._rules:
            if r.matcher.match(target):
                return r
        return None
