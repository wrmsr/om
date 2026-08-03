# ruff: noqa: UP045
# @om-lite
import dataclasses as dc
import typing as ta


##


@dc.dataclass(frozen=True)
class CextConfig:
    extra_sources: ta.Optional[ta.Sequence[str]] = None
    extra_headers: ta.Optional[ta.Sequence[str]] = None

    extra_compile_args: ta.Optional[ta.Sequence[str]] = None
    extra_link_args: ta.Optional[ta.Sequence[str]] = None

    define_macros: ta.Optional[ta.Mapping[str, str]] = None

    libraries: ta.Optional[ta.Sequence[ta.Any]] = None  # list[str | tuple[str, str]] | None
