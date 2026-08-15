"""
Key-sequence to command matching.

A `Keymap` maps key sequences to *command objects* - whatever typed values the consumer dispatches on; nothing here is
stringly-dispatched. Matching is a trie walk with explicit prefix state and the classic `timeoutlen` semantics: when a
pressed sequence is both a bound chord and a prefix of a longer one, the matcher waits (reporting `pending_timeout_s`)
and resolves to the shorter binding if nothing else arrives in time. Unmatched sequences are handed back verbatim so
the consumer can route them elsewhere (e.g. self-insert).

This is deliberately separate from the escape-sequence parser's timeout (`ttimeoutlen`) - conflating the two is the
classic bug.
"""
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang

from .keys import Key
from .keys import parse_key


##


DEFAULT_CHORD_TIMEOUT_S = 1.


@dc.dataclass(frozen=True)
class KeymapMatch(lang.Final):
    """The result of pushing one key (or flushing): resolved commands and/or keys nothing matched."""

    commands: ta.Sequence[ta.Any] = ()
    unmatched: ta.Sequence[Key] = ()

    @property
    def is_pending(self) -> bool:
        return not self.commands and not self.unmatched


class _TrieNode:
    def __init__(self) -> None:
        super().__init__()

        self.children: dict[Key, _TrieNode] = {}
        self.command: ta.Any = None
        self.bound = False


class Keymap:
    def __init__(
            self,
            bindings: ta.Mapping[str | ta.Sequence[Key], ta.Any] | None = None,
    ) -> None:
        super().__init__()

        self._root = _TrieNode()
        for spec, command in (bindings or {}).items():
            self.bind(spec, command)

    def bind(self, spec: str | ta.Sequence[Key], command: ta.Any) -> None:
        """Bind a key sequence to a command. String specs are space-separated: 'ctrl+x ctrl+u'."""

        if isinstance(spec, str):
            keys: ta.Sequence[Key] = [parse_key(part) for part in spec.split()]
        else:
            keys = spec
        check.arg(len(keys) > 0)

        node = self._root
        for key in keys:
            node = node.children.setdefault(key, _TrieNode())
        node.command = command
        node.bound = True

    def lookup(self, keys: ta.Sequence[Key]) -> _TrieNode | None:
        node = self._root
        for key in keys:
            if (node := node.children.get(key)) is None:  # type: ignore[assignment]
                return None
        return node


class KeymapMatcher:
    """Stateful matcher over one Keymap. Not thread-safe; one per input consumer."""

    def __init__(
            self,
            keymap: Keymap,
            *,
            chord_timeout_s: float = DEFAULT_CHORD_TIMEOUT_S,
    ) -> None:
        super().__init__()

        self._keymap = keymap
        self._chord_timeout_s = chord_timeout_s

        self._prefix: list[Key] = []

    @property
    def pending_timeout_s(self) -> float | None:
        """When a prefix is held, how long to wait before flushing it. None when idle."""

        if self._prefix:
            return self._chord_timeout_s
        return None

    def _take_prefix(self) -> list[Key]:
        prefix = self._prefix
        self._prefix = []
        return prefix

    def flush(self) -> KeymapMatch:
        """Resolve a held prefix: its own binding if it has one, otherwise hand its keys back unmatched."""

        if not (prefix := self._take_prefix()):
            return KeymapMatch()
        node = self._keymap.lookup(prefix)
        if node is not None and node.bound:
            return KeymapMatch(commands=(node.command,))
        return KeymapMatch(unmatched=tuple(prefix))

    def push(self, key: Key) -> KeymapMatch:
        candidate = [*self._prefix, key]
        node = self._keymap.lookup(candidate)

        if node is None:
            # The extended sequence matches nothing: resolve what was held, then retry the new key alone.
            flushed = self.flush()
            if flushed.commands or flushed.unmatched:
                retry = self.push(key)
                return KeymapMatch(
                    commands=(*flushed.commands, *retry.commands),
                    unmatched=(*flushed.unmatched, *retry.unmatched),
                )
            return KeymapMatch(unmatched=(key,))

        if node.bound and not node.children:
            # Unambiguous terminal binding.
            self._prefix = []
            return KeymapMatch(commands=(node.command,))

        # Either a pure prefix, or a binding that is also a prefix of longer ones - hold and wait.
        self._prefix = candidate
        return KeymapMatch()
