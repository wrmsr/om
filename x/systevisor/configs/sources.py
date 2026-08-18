# ruff: noqa: UP006 UP007 UP045
import dataclasses as dc
import os
import os.path
import typing as ta

from omcore.configs.formats import DEFAULT_CONFIG_FILE_LOADER


_SYSTEVISOR_CONFIG_SOURCE_EXTENSIONS = frozenset({'.json', '.toml', '.yaml', '.yml'})


@dc.dataclass(frozen=True)
class SystevisorConfigSourceDocument:
    path: str
    data: ta.Mapping[str, ta.Any]


@dc.dataclass(frozen=True)
class SystevisorConfigProvenance:
    object_path: ta.Sequence[str]
    source: str


class SystevisorConfigSourceError(Exception):
    def __init__(self, path: str, message: str) -> None:
        super().__init__(message)

        self.path = path
        self.message = message


class SystevisorConfigMergeError(Exception):
    def __init__(self, object_path: ta.Sequence[str], first_source: str, second_source: str) -> None:
        super().__init__('.'.join(object_path))

        self.object_path = tuple(object_path)
        self.first_source = first_source
        self.second_source = second_source


def systevisor_discover_config_files(paths: ta.Iterable[str], *, recursive: bool = False) -> ta.Sequence[str]:
    discovered: ta.List[str] = []
    seen: ta.Set[str] = set()

    for input_path in paths:
        path = os.path.abspath(input_path)
        if os.path.isfile(path):
            if os.path.splitext(path)[1].lower() not in _SYSTEVISOR_CONFIG_SOURCE_EXTENSIONS:
                raise SystevisorConfigSourceError(path, 'unsupported config source extension')
            candidates = [path]
        elif os.path.isdir(path):
            if recursive:
                candidates = []
                for directory, directory_names, file_names in os.walk(path):
                    directory_names.sort()
                    candidates.extend(os.path.join(directory, file_name) for file_name in sorted(file_names))
            else:
                candidates = [os.path.join(path, file_name) for file_name in sorted(os.listdir(path))]
        else:
            raise SystevisorConfigSourceError(path, 'config source does not exist')

        for candidate in candidates:
            if not os.path.isfile(candidate):
                continue
            if os.path.splitext(candidate)[1].lower() not in _SYSTEVISOR_CONFIG_SOURCE_EXTENSIONS:
                continue
            canonical = os.path.realpath(candidate)
            if canonical in seen:
                continue
            seen.add(canonical)
            discovered.append(candidate)

    return tuple(discovered)


def systevisor_load_config_document(path: str) -> SystevisorConfigSourceDocument:
    try:
        data = DEFAULT_CONFIG_FILE_LOADER.load_file(path).as_map()
    except Exception as exc:
        raise SystevisorConfigSourceError(path, str(exc)) from exc

    return SystevisorConfigSourceDocument(path=path, data=dict(data))


def _systevisor_config_sources_record_provenance(
        value: ta.Any,
        object_path: ta.Tuple[str, ...],
        source: str,
        provenance: ta.MutableMapping[ta.Tuple[str, ...], str],
) -> None:
    if isinstance(value, dict):
        if not value:
            provenance[object_path] = source
        for key, child in value.items():
            _systevisor_config_sources_record_provenance(child, (*object_path, str(key)), source, provenance)
    else:
        provenance[object_path] = source


def _systevisor_config_sources_merge_value(
        target: ta.MutableMapping[str, ta.Any],
        value: ta.Mapping[str, ta.Any],
        object_path: ta.Tuple[str, ...],
        source: str,
        provenance: ta.MutableMapping[ta.Tuple[str, ...], str],
) -> None:
    for key, incoming in value.items():
        if not isinstance(key, str):
            raise TypeError(f'config mapping key must be a string at {object_path!r}: {key!r}')

        child_path = (*object_path, key)
        if key not in target:
            if isinstance(incoming, dict):
                child: ta.MutableMapping[str, ta.Any] = {}
                target[key] = child
                _systevisor_config_sources_merge_value(child, incoming, child_path, source, provenance)
                if not incoming:
                    provenance[child_path] = source
            else:
                target[key] = incoming
                _systevisor_config_sources_record_provenance(incoming, child_path, source, provenance)
            continue

        current = target[key]
        if isinstance(current, dict) and isinstance(incoming, dict):
            _systevisor_config_sources_merge_value(current, incoming, child_path, source, provenance)
            continue

        first_source = provenance.get(child_path)
        if first_source is None:
            first_source = next(
                (
                    value_source
                    for value_path, value_source in provenance.items()
                    if value_path[:len(child_path)] == child_path
                ),
                '<unknown>',
            )
        raise SystevisorConfigMergeError(child_path, first_source, source)


def systevisor_merge_config_documents(
        documents: ta.Iterable[SystevisorConfigSourceDocument],
) -> ta.Tuple[ta.Mapping[str, ta.Any], ta.Sequence[SystevisorConfigProvenance]]:
    merged: ta.MutableMapping[str, ta.Any] = {}
    provenance: ta.MutableMapping[ta.Tuple[str, ...], str] = {}
    for document in documents:
        _systevisor_config_sources_merge_value(merged, document.data, (), document.path, provenance)

    return (
        dict(merged),
        tuple(
            SystevisorConfigProvenance(object_path=object_path, source=source)
            for object_path, source in sorted(provenance.items())
        ),
    )
