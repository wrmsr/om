# ruff: noqa: UP006 UP045
# @om-lite
import dataclasses as dc
import glob
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


def resolve_cext_config_file(ext_src: str, config_file: str) -> str:
    if os.path.isabs(config_file):
        raise ValueError(config_file)

    ext_src = os.path.normpath(ext_src)
    package_dir = ext_src.partition(os.sep)[0]
    resolved_file = os.path.normpath(os.path.join(os.path.dirname(ext_src), config_file))
    if os.path.commonpath([package_dir, resolved_file]) != package_dir:
        raise ValueError(config_file)

    return resolved_file


def expand_cext_config_files(
        ext_src: str,
        config_files: ta.Sequence[str],
        *,
        exclude_files: ta.Sequence[str] = (),
        root_dir: ta.Optional[str] = None,
) -> ta.List[str]:
    if root_dir is None:
        root_dir = os.getcwd()
    root_dir = os.path.abspath(root_dir)

    out: ta.Set[str] = set()
    for config_file in config_files:
        resolved_pattern = resolve_cext_config_file(ext_src, config_file)
        matched_files = [
            matched_file
            for matched_file in glob.glob(os.path.join(root_dir, resolved_pattern), recursive=True)
            if os.path.isfile(matched_file)
        ]
        if not matched_files:
            raise FileNotFoundError(resolved_pattern)

        out.update(os.path.relpath(matched_file, root_dir) for matched_file in matched_files)

    out.difference_update(os.path.normpath(exclude_file) for exclude_file in exclude_files)

    return sorted(out)
