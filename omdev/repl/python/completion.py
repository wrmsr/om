"""
Name completion over a namespace, with no help from readline or rlcompleter: importing the latter installs itself as
readline's completer - a process-wide side effect an embedded repl must not have - and evaluates the expression before
the dot, calls and all. This walks attributes of dotted names only.
"""
import builtins
import keyword
import typing as ta

from ..interpreters import Completion


##


_DELIMITERS: ta.AbstractSet[str] = frozenset(' \t\n`~!@#$%^&*()-=+[{]}\\|;:\'",<>/?')

_MISSING = object()


def extract_stem(text: str, cursor: int) -> str:
    """The word being completed: back from `cursor` to a delimiter. Dots are part of it."""

    p = cursor - 1
    while p >= 0 and text[p] not in _DELIMITERS:
        p -= 1
    return text[p + 1:cursor]


def _builtin_names(namespace: ta.Mapping[str, ta.Any]) -> ta.AbstractSet[str]:
    b = namespace.get('__builtins__', builtins)
    return set(b) if isinstance(b, ta.Mapping) else set(dir(b))


def _resolve(namespace: ta.Mapping[str, ta.Any], dotted: str) -> ta.Any:
    parts = dotted.split('.')
    if not all(part.isidentifier() for part in parts):
        return _MISSING

    head = parts[0]
    if head in namespace:
        obj = namespace[head]
    else:
        b = namespace.get('__builtins__', builtins)
        if isinstance(b, ta.Mapping):
            if head not in b:
                return _MISSING
            obj = b[head]
        elif hasattr(b, head):
            obj = getattr(b, head)
        else:
            return _MISSING

    for part in parts[1:]:
        try:
            obj = getattr(obj, part)
        except Exception:  # noqa: BLE001
            return _MISSING
    return obj


def _matching(names: ta.Iterable[str], prefix: str) -> list[str]:
    # Private names only when asked for, as rlcompleter does.
    return sorted({
        n for n in names
        if n.startswith(prefix) and (prefix.startswith('_') or not n.startswith('_'))
    })


def complete_python(namespace: ta.Mapping[str, ta.Any], source: str, cursor: int) -> list[Completion]:
    stem = extract_stem(source, cursor)
    if not stem:
        return []

    if '.' in stem:
        base, _, attr = stem.rpartition('.')
        obj = _resolve(namespace, base)
        if obj is _MISSING:
            return []
        try:
            names = dir(obj)
        except Exception:  # noqa: BLE001
            return []
        return [Completion(f'{base}.{n}') for n in _matching(names, attr)]

    candidates: set[str] = set(keyword.kwlist)
    candidates.update(keyword.softkwlist)
    candidates.update(namespace)
    candidates.update(_builtin_names(namespace))
    candidates.discard('__builtins__')
    return [Completion(n) for n in _matching(candidates, stem)]
