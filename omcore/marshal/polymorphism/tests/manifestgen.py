"""
Reusable test helpers for real, end-to-end manifest generation against checked-in fixture packages whose
`@om-manifest` magics are mangled (so the repo's own manifest gen never picks them up): copy the fixture to a temp
dir, unmangle the magics, run the actual omdev manifest builder on it (dump subprocess and all), and load the
resulting `.om-manifests.json` back through the real loader.

Deliberately self-contained so it can be lifted wholesale into omdev.
"""
import asyncio
import contextlib
import os.path
import shutil
import sys
import typing as ta

from omdev.manifests.building import ManifestBuilder

from ....lite.marshal import unmarshal_obj
from ....manifests.loading import ManifestLoader


T = ta.TypeVar('T')


##


MANIFEST_MAGIC = '@om-manifest'
MANGLED_MANIFEST_MAGIC = '!NOT-@om-manifest'


def gen_mangled_manifest_package(
        src_dir: str,
        dst_root_dir: str,
        *,
        mangled_magic: str = MANGLED_MANIFEST_MAGIC,
) -> str:
    """
    Copies the fixture package at src_dir under dst_root_dir, unmangles its manifest magics, and runs real manifest
    gen on it (writing its .om-manifests.json). Returns the copied package dir.
    """

    pkg_name = os.path.basename(src_dir.rstrip(os.sep))
    pkg_dir = os.path.join(dst_root_dir, pkg_name)
    shutil.copytree(src_dir, pkg_dir)

    for dp, _, fns in os.walk(pkg_dir):
        for fn in fns:
            if not fn.endswith('.py'):
                continue
            fp = os.path.join(dp, fn)
            with open(fp, encoding='utf-8') as f:
                src = f.read()
            if mangled_magic in src:
                with open(fp, 'w', encoding='utf-8') as f:
                    f.write(src.replace(mangled_magic, MANIFEST_MAGIC))

    # The dump subprocess must be able to import both the copied package and this repo's packages.
    env = dict(os.environ)
    env['PYTHONPATH'] = os.pathsep.join([
        dst_root_dir,
        *sys.path,
    ])

    builder = ManifestBuilder(
        dst_root_dir,
        subprocess_kwargs=dict(env=env),
    )
    asyncio.run(builder.build_package_manifests(pkg_name, write=True))

    return pkg_dir


@contextlib.contextmanager
def added_sys_path(dir: str) -> ta.Iterator[None]:  # noqa
    sys.path.insert(0, dir)
    try:
        yield
    finally:
        sys.path.remove(dir)


def load_package_manifest_values(
        root_dir: str,
        package_name: str,
        cls: type[T],
) -> ta.Sequence[T]:
    """Loads generated manifest values of the given class from a package under root_dir via the real loader."""

    loader = ManifestLoader(ManifestLoader.Config(
        package_scan_root_dirs=[root_dir],
        value_instantiator=lambda value_cls, **kwargs: unmarshal_obj(kwargs, value_cls),
    ))

    with added_sys_path(root_dir):
        return loader.load_values_of(cls, packages=[package_name])
