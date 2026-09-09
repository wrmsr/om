import typing as ta

from .models import ResolvedPackage


##


ALLOWED_LICENSES = frozenset({
    'MIT',
    'BSD-2-Clause',
    'BSD-3-Clause',
    '0BSD',
    'ISC',
    'Zlib',
    'CC0-1.0',
    'Unlicense',
})


def normalize_license(value: ta.Any, /) -> str | None:
    """
    Returns the SPDX identifier of a package.json `license` field, accepting the legacy `{"type": ...}` object form.
    """

    if isinstance(value, str):
        return value

    if isinstance(value, dict):
        license_type = value.get('type')
        if isinstance(license_type, str):
            return license_type

    return None


def validate_license(
        package: ResolvedPackage,
        metadata: ta.Mapping[str, ta.Any],
        files: ta.Mapping[str, bytes],
) -> None:
    if normalize_license(metadata.get('license')) != package.license or package.license not in ALLOWED_LICENSES:
        raise ValueError(f'Unapproved license for {package.name}: {metadata.get("license")}')
    if not any(name.lower().startswith(('license', 'licence')) for name in files):
        raise ValueError(f'Package contains no license file: {package.name}')
