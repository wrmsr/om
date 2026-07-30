import typing as ta

from omcore import check
from omcore import collections as col
from omcore import dataclasses as dc
from omcore import lang
from omcore.algorithm.prefixes import MinUniquePrefixNode
from omcore.algorithm.prefixes import build_min_unique_prefix_tree

from ...core import fieldhash as fh
from .types import PermissionRule


##


@ta.final
@dc.dataclass(frozen=True)
class PermissionRules(fh.FieldHashable, lang.Final):
    rules: ta.Sequence[PermissionRule] = dc.xfield(coerce=tuple)

    def _field_hash(self) -> fh.FieldHashValue:
        return fh.FieldHashObject('rules', (
            fh.FieldHashField('rules', check.isinstance(self.rules, tuple)),
        ))

    #

    @lang.cached_property
    def by_digest(self) -> ta.Mapping[str, PermissionRule]:
        return col.make_map((
            (check.inline(d := fh.digest_field_hash(r), len(d) == fh.FIELD_HASH_DIGEST_LEN), r)
            for r in self.rules
        ), strict=True)

    #

    @lang.cached_function
    def _mup(self) -> MinUniquePrefixNode:
        return build_min_unique_prefix_tree(list(self.by_digest))

    MIN_MIN_DIGEST_LEN: ta.ClassVar[int] = 3

    @lang.cached_property
    def min_digest_len(self) -> int:
        return max(self._mup().min_unique_prefix_len, self.MIN_MIN_DIGEST_LEN)

    @lang.cached_property
    def by_min_digest(self) -> ta.Mapping[str, PermissionRule]:
        mdl = self.min_digest_len
        return col.make_map(((k[:mdl], v) for k, v in self.by_digest.items()), strict=True)

    @lang.cached_property
    def min_digests(self) -> ta.Mapping[PermissionRule, str]:
        return {v: k for k, v in self.by_min_digest.items()}

    #

    def __len__(self) -> int:
        return len(self.rules)

    def __iter__(self) -> ta.Iterator[PermissionRule]:
        return iter(self.rules)

    @ta.overload
    def __getitem__(self, key: int) -> PermissionRule: ...

    @ta.overload
    def __getitem__(self, key: slice) -> ta.Sequence[PermissionRule]: ...

    @ta.overload
    def __getitem__(self, key: str) -> PermissionRule: ...

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self.rules[key]
        elif isinstance(key, str):
            if (kl := len(key)) < fh.FIELD_HASH_DIGEST_LEN:
                if kl < self.min_digest_len:
                    raise KeyError(key)
                key = self._mup().lookup(key)
            return self.by_digest[key]
        else:
            raise TypeError(key)

    def __contains__(self, key: str) -> bool:
        return key in self.by_digest

    @ta.overload
    def get(self, key: str, default: None = None) -> PermissionRule | None: ...

    @ta.overload
    def get(self, key: str, default: PermissionRule) -> PermissionRule: ...

    def get(self, key, default=None):
        return self.by_digest.get(key, default)
