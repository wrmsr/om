import pytest

from ..models import PackageArgument
from ..models import RemoveRequest
from ..models import RootPackage
from ..models import VendorManifest
from ..operations import parse_package_argument
from ..operations import remove


##


@pytest.mark.parametrize(('value', 'expected'), [
    ('crelt', PackageArgument(name='crelt')),
    ('crelt@^1.0.0', PackageArgument(name='crelt', version='^1.0.0')),
    ('@codemirror/state', PackageArgument(name='@codemirror/state')),
    ('@codemirror/state@latest', PackageArgument(name='@codemirror/state', version='latest')),
])
def test_parse_package_argument(value: str, expected: PackageArgument) -> None:
    assert parse_package_argument(value) == expected


@pytest.mark.parametrize('value', ['', '@scope', 'crelt@', '@codemirror/state@'])
def test_parse_package_argument_rejects_invalid_value(value: str) -> None:
    with pytest.raises(ValueError, match='Invalid package argument'):
        parse_package_argument(value)


def test_remove_last_root_resolves_empty_manifest_without_registry() -> None:
    manifest = VendorManifest(
        format_version=2,
        roots=(RootPackage(name='example', version='1.0.0'),),
    )

    result = remove(RemoveRequest(manifest=manifest, packages=('example',)))

    assert result.manifest.roots == ()
    assert result.lock.roots == ()
    assert result.lock.packages == ()
    assert result.lock.files == {}
