# ruff: noqa: UP006 UP007 UP045
import dataclasses as dc
import typing as ta

from .diagnostics import SystevisorConfigDiagnostic
from .diagnostics import SystevisorConfigDiagnosticSeverity
from .diagnostics import SystevisorConfigDiagnosticStage
from .marshal import systevisor_unmarshal_config
from .models import SystevisorConfig
from .snapshots import SystevisorConfigSnapshot
from .snapshots import systevisor_build_config_snapshot
from .sources import SystevisorConfigMergeError
from .sources import SystevisorConfigSourceDocument
from .sources import SystevisorConfigSourceError
from .sources import systevisor_discover_config_files
from .sources import systevisor_load_config_document
from .sources import systevisor_merge_config_documents
from .validation import systevisor_validate_config


@dc.dataclass(frozen=True)
class SystevisorConfigCompileResult:
    snapshot: ta.Optional[SystevisorConfigSnapshot]
    diagnostics: ta.Sequence[SystevisorConfigDiagnostic]
    discovered_paths: ta.Sequence[str]

    @property
    def is_valid(self) -> bool:
        return self.snapshot is not None


class SystevisorConfigCompiler:
    def compile(self, paths: ta.Iterable[str], *, recursive: bool = False) -> SystevisorConfigCompileResult:
        diagnostics: ta.List[SystevisorConfigDiagnostic] = []
        try:
            discovered_paths = systevisor_discover_config_files(paths, recursive=recursive)
        except SystevisorConfigSourceError as exc:
            diagnostics.append(SystevisorConfigDiagnostic(
                severity=SystevisorConfigDiagnosticSeverity.ERROR,
                stage=SystevisorConfigDiagnosticStage.DISCOVERY,
                code='source_not_found',
                message=exc.message,
                source=exc.path,
            ))
            return SystevisorConfigCompileResult(snapshot=None, diagnostics=tuple(diagnostics), discovered_paths=())

        documents: ta.List[SystevisorConfigSourceDocument] = []
        for discovered_path in discovered_paths:
            try:
                documents.append(systevisor_load_config_document(discovered_path))
            except SystevisorConfigSourceError as exc:
                diagnostics.append(SystevisorConfigDiagnostic(
                    severity=SystevisorConfigDiagnosticSeverity.ERROR,
                    stage=SystevisorConfigDiagnosticStage.PARSE,
                    code='parse_error',
                    message=exc.message,
                    source=exc.path,
                ))
        if diagnostics:
            return SystevisorConfigCompileResult(
                snapshot=None,
                diagnostics=tuple(diagnostics),
                discovered_paths=discovered_paths,
            )

        try:
            merged, provenance = systevisor_merge_config_documents(documents)
        except SystevisorConfigMergeError as exc:
            diagnostics.append(SystevisorConfigDiagnostic(
                severity=SystevisorConfigDiagnosticSeverity.ERROR,
                stage=SystevisorConfigDiagnosticStage.MERGE,
                code='duplicate_definition',
                message=f'configuration value was defined by both {exc.first_source!r} and {exc.second_source!r}',
                source=exc.second_source,
                object_path=exc.object_path,
            ))
            return SystevisorConfigCompileResult(
                snapshot=None,
                diagnostics=tuple(diagnostics),
                discovered_paths=discovered_paths,
            )
        except (TypeError, ValueError) as exc:
            diagnostics.append(SystevisorConfigDiagnostic(
                severity=SystevisorConfigDiagnosticSeverity.ERROR,
                stage=SystevisorConfigDiagnosticStage.MERGE,
                code='invalid_mapping',
                message=str(exc),
            ))
            return SystevisorConfigCompileResult(
                snapshot=None,
                diagnostics=tuple(diagnostics),
                discovered_paths=discovered_paths,
            )

        try:
            config: SystevisorConfig = systevisor_unmarshal_config(merged, SystevisorConfig)
        except Exception as exc:  # noqa: BLE001
            diagnostics.append(SystevisorConfigDiagnostic(
                severity=SystevisorConfigDiagnosticSeverity.ERROR,
                stage=SystevisorConfigDiagnosticStage.UNMARSHAL,
                code='invalid_shape',
                message=f'{type(exc).__name__}: {exc}',
            ))
            return SystevisorConfigCompileResult(
                snapshot=None,
                diagnostics=tuple(diagnostics),
                discovered_paths=discovered_paths,
            )

        diagnostics.extend(systevisor_validate_config(config))
        if diagnostics:
            return SystevisorConfigCompileResult(
                snapshot=None,
                diagnostics=tuple(diagnostics),
                discovered_paths=discovered_paths,
            )

        return SystevisorConfigCompileResult(
            snapshot=systevisor_build_config_snapshot(config, discovered_paths, provenance),
            diagnostics=(),
            discovered_paths=discovered_paths,
        )
