# ruff: noqa: UP045
# @om-lite
import dataclasses as dc
import os.path
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


def resolve_cext_config_file(package_dir: str, config_file: str) -> str:
    if os.path.isabs(config_file):
        raise ValueError(config_file)

    package_dir = os.path.normpath(package_dir)
    resolved_file = os.path.normpath(os.path.join(package_dir, config_file))
    if os.path.commonpath([package_dir, resolved_file]) != package_dir:
        raise ValueError(config_file)

    return resolved_file
