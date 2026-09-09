"""Audited JavaScript dependency vendoring."""
# fmt: off
# ruff: noqa: I001
from omcore import dataclasses as _dc  # noqa


_dc.init_package(
    globals(),
    codegen=True,
)


##


from omcore import lang as _lang  # noqa


with _lang.auto_proxy_init(globals()):
    ##

    from .generation import (  # noqa
        vendor,
    )

    from .exports import (  # noqa
        output_module_path,
        output_package_exports,
        read_package_exports,
        resolve_package_export,
    )

    from .manifests import (  # noqa
        load_lock,
        load_manifest,
        render_manifest,
        validate_lock,
        validate_manifest,
    )

    from .models import (  # noqa
        AddRequest,
        ManifestUpdateResult,
        ModuleParseResult,
        ModuleSpecifier,
        OutdatedPackage,
        OutdatedRequest,
        OutdatedResult,
        PackageExports,
        PackageArgument,
        RegistryConfig,
        RegistryPackage,
        RegistryPackageRequest,
        RegistryPackageVersion,
        RegistryVersionRequest,
        RemoveRequest,
        ResolvedPackage,
        ResolveRequest,
        ResolveResult,
        RootPackage,
        UpdateRequest,
        VendorLock,
        VendorManifest,
        VendorRequest,
        VendorResult,
        VerifyRequest,
        VerifyResult,
        VersionResolveRequest,
        VersionResolveResult,
    )

    from .operations import (  # noqa
        add,
        outdated,
        parse_package_argument,
        remove,
        update,
    )

    from .parsing import (  # noqa
        parse_module,
    )

    from .registry import (  # noqa
        fetch_package,
        fetch_version,
    )

    from .outputs import (  # noqa
        render_lock,
    )

    from .resolution import (  # noqa
        resolve,
        resolve_versions,
    )

    from .verification import (  # noqa
        verify,
    )
