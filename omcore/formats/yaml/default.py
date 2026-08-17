import typing as ta

from .backends import DEFAULT_YAML_BACKEND


##


def is_available() -> bool:
    return DEFAULT_YAML_BACKEND.INSTANCE.is_available()


def loads(s: str) -> ta.Any:
    return DEFAULT_YAML_BACKEND.INSTANCE.loads(s)


def dumps(o: ta.Any) -> str:
    return DEFAULT_YAML_BACKEND.INSTANCE.dumps(o)
