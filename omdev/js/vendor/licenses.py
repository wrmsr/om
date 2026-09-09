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


def validate_license(
        package: ResolvedPackage,
        metadata: ta.Mapping[str, ta.Any],
        files: ta.Mapping[str, bytes],
) -> None:
    if metadata.get('license') != package.license or package.license not in ALLOWED_LICENSES:
        raise ValueError(f'Unapproved license for {package.name}: {metadata.get("license")}')
    if not any(name.lower().startswith(('license', 'licence')) for name in files):
        raise ValueError(f'Package contains no license file: {package.name}')
