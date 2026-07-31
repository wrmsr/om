import dataclasses as dc

import pytest

from ..loading import ManifestLoader
from ..types import Manifest


@dc.dataclass(frozen=True)
class Thing:
    value: int


@dc.dataclass(frozen=True)
class _PrivateThing:
    value: int


def test_config():
    with pytest.raises(TypeError):
        ManifestLoader.Config(package_scan_root_dirs='root')

    with pytest.raises(TypeError):
        ManifestLoader.Config(discover_packages_fallback_scan_root_dirs='root')

    left = ManifestLoader.Config(
        package_scan_root_dirs=['left'],
        module_remap={'old': 'older'},
    )
    right = ManifestLoader.Config(
        package_scan_root_dirs=['right'],
        discover_packages=True,
        module_remap={'old': 'new'},
    )

    assert left | right == ManifestLoader.Config(
        package_scan_root_dirs=['left', 'right'],
        discover_packages=True,
        module_remap={'old': 'new'},
    )


def test_load():
    package_name = 'omcore.manifests'
    manifest = Manifest(
        module='.tests.test_loading',
        attr=None,
        file=__file__,
        line=1,
        value={
            '!.tests.test_loading.Thing': {
                'value': 42,
            },
        },
    )

    class TestLoader(ManifestLoader):
        @classmethod
        def _read_package_raw_manifests(cls, package_name_arg):
            assert package_name_arg == package_name
            return [manifest]

    calls = []

    def instantiate(cls, **kwargs):
        calls.append((cls, kwargs))
        return cls(**kwargs)

    loader = TestLoader(ManifestLoader.Config(value_instantiator=instantiate))
    [loaded] = loader.load(packages=[package_name], classes=[Thing])

    assert loaded.package.name == package_name
    assert loaded.module == 'omcore.manifests.tests.test_loading'
    assert loaded.class_key == f'!{Thing.__module__}.{Thing.__qualname__}'
    assert loaded.manifest is manifest
    assert loaded.loader is loader

    assert loaded.value() == Thing(42)
    assert loaded.value() == Thing(42)
    assert calls == [(Thing, {'value': 42})]


def test_load_class():
    loader = ManifestLoader(ManifestLoader.Config())

    key = loader.get_class_key(_PrivateThing)
    assert loader._load_class(key) is _PrivateThing  # noqa

    with pytest.raises(ManifestLoader.ClassKeyError):
        loader._load_class('!lowercase.module')  # noqa

    with pytest.raises(ManifestLoader.ClassKeyError):
        loader._load_class('!Thing')  # noqa
