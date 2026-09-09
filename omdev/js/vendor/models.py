import typing as ta

from omcore import dataclasses as dc


##


@dc.dataclass(frozen=True)
class RootPackage:
    name: str
    version: str


@dc.dataclass(frozen=True)
class ResolvedPackage:
    name: str
    version: str
    license: str
    integrity: str
    url: str
    dependencies: ta.Mapping[str, str]
    peer_dependencies: ta.Mapping[str, str]
    optional_peer_dependencies: ta.AbstractSet[str]


@dc.dataclass(frozen=True)
class VendorManifest:
    format_version: int
    roots: tuple[RootPackage, ...]


@dc.dataclass(frozen=True)
class VendorLock:
    format_version: int
    roots: tuple[RootPackage, ...]
    packages: tuple[ResolvedPackage, ...]
    files: ta.Mapping[str, str]


@dc.dataclass(frozen=True)
class RegistryConfig:
    url: str = 'https://registry.npmjs.org'
    timeout: float = 60.0


@dc.dataclass(frozen=True)
class RegistryPackageRequest:
    name: str
    config: RegistryConfig


@dc.dataclass(frozen=True)
class RegistryVersionRequest:
    name: str
    version: str
    config: RegistryConfig


@dc.dataclass(frozen=True)
class RegistryPackageVersion:
    name: str
    version: str
    dependencies: ta.Mapping[str, str]
    peer_dependencies: ta.Mapping[str, str]
    optional_peer_dependencies: ta.AbstractSet[str]


@dc.dataclass(frozen=True)
class RegistryPackage:
    name: str
    versions: tuple[RegistryPackageVersion, ...]
    tags: ta.Mapping[str, str] = dc.field(default_factory=dict)


@dc.dataclass(frozen=True)
class VersionResolveRequest:
    manifest: VendorManifest
    packages: ta.Mapping[str, RegistryPackage]


@dc.dataclass(frozen=True)
class VersionResolveResult:
    packages: tuple[RegistryPackageVersion, ...]


@dc.dataclass(frozen=True)
class ResolveRequest:
    manifest: VendorManifest
    registry: RegistryConfig = dc.field(default_factory=RegistryConfig)


@dc.dataclass(frozen=True)
class ResolveResult:
    lock: VendorLock


@dc.dataclass(frozen=True)
class PackageArgument:
    name: str
    version: str | None = None


@dc.dataclass(frozen=True)
class AddRequest:
    manifest: VendorManifest
    packages: tuple[PackageArgument, ...]
    registry: RegistryConfig = dc.field(default_factory=RegistryConfig)


@dc.dataclass(frozen=True)
class UpdateRequest:
    manifest: VendorManifest
    packages: tuple[PackageArgument, ...] = ()
    registry: RegistryConfig = dc.field(default_factory=RegistryConfig)


@dc.dataclass(frozen=True)
class RemoveRequest:
    manifest: VendorManifest
    packages: tuple[str, ...]
    registry: RegistryConfig = dc.field(default_factory=RegistryConfig)


@dc.dataclass(frozen=True)
class ManifestUpdateResult:
    manifest: VendorManifest
    lock: VendorLock


@dc.dataclass(frozen=True)
class OutdatedRequest:
    manifest: VendorManifest
    lock: VendorLock
    packages: tuple[str, ...] = ()
    registry: RegistryConfig = dc.field(default_factory=RegistryConfig)


@dc.dataclass(frozen=True)
class OutdatedPackage:
    name: str
    requirement: str
    current: str
    wanted: str
    latest: str


@dc.dataclass(frozen=True)
class OutdatedResult:
    packages: tuple[OutdatedPackage, ...]


@dc.dataclass(frozen=True)
class DownloadRequest:
    package: ResolvedPackage
    cache_directory: str


@dc.dataclass(frozen=True)
class DownloadedPackage:
    package: ResolvedPackage
    data: bytes


@dc.dataclass(frozen=True)
class PackageExports:
    """
    Export keys map to package-relative module paths. A key with a `None` target is blocked: it matched no browser
    condition or was explicitly `null`, and as in Node it shadows any broader pattern instead of falling through.
    """

    entries: ta.Mapping[str, str | None]
    restricted: bool


@dc.dataclass(frozen=True)
class ExtractedPackage:
    package: ResolvedPackage
    files: ta.Mapping[str, bytes]
    metadata: ta.Mapping[str, ta.Any]
    exports: PackageExports
    module_origins: ta.Mapping[str, str]


@dc.dataclass(frozen=True)
class ModuleSpecifier:
    value: str
    start: int
    end: int


@dc.dataclass(frozen=True)
class ModuleParseResult:
    specifiers: tuple[ModuleSpecifier, ...]
    dynamic_import: bool


@dc.dataclass(frozen=True)
class RewriteRequest:
    source: str
    source_path: str
    package_names: ta.AbstractSet[str]
    package_exports: ta.Mapping[str, PackageExports] = dc.field(default_factory=dict)
    source_origin: str | None = None


@dc.dataclass(frozen=True)
class RewriteResult:
    source: str


@dc.dataclass(frozen=True)
class GraphVerifyRequest:
    root: str


@dc.dataclass(frozen=True)
class GraphVerifyResult:
    module_count: int
    import_count: int


@dc.dataclass(frozen=True)
class OutputBuildRequest:
    root: str
    lock: VendorLock


@dc.dataclass(frozen=True)
class VendorRequest:
    manifest: VendorManifest
    lock: VendorLock
    destination: str
    cache_directory: str


@dc.dataclass(frozen=True)
class VendorResult:
    destination: str
    package_count: int
    file_count: int


@dc.dataclass(frozen=True)
class VerifyRequest:
    manifest: VendorManifest
    lock: VendorLock
    destination: str


@dc.dataclass(frozen=True)
class VerifyResult:
    destination: str
    package_count: int
    file_count: int
    module_count: int
    import_count: int
