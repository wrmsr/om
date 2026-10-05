import difflib
import typing as ta


##


class OverrideError(Exception):
    pass


class OverrideSyntaxError(OverrideError):
    """An override statement, path, or value literal could not be parsed."""


class OverridePathError(OverrideError):
    """A path could not be resolved against the tree or its shape."""


class OverrideValueError(OverrideError):
    """A value could not be resolved for the shape of its target."""


class OverrideOpError(OverrideError):
    """An op is not applicable to its target."""


class OverrideFileError(OverrideError):
    """A file referenced by an override could not be loaded."""


class OverrideJqError(OverrideError):
    """A jq op failed or did not produce exactly one output."""


class UnhandledOverrideShapeError(OverrideError):
    """A value would have to be guessed for a shape which is not understood, and guessing was not permitted."""


##


def render_suggestion(name: str, candidates: ta.Iterable[str]) -> str:
    if not (ms := difflib.get_close_matches(name, list(candidates), n=3)):
        return ''
    return f' - did you mean {" or ".join(repr(m) for m in ms)}?'
