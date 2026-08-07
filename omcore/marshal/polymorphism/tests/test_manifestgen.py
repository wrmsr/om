import os.path

from .manifestgen import gen_mangled_manifest_package


def test_manifest_gen_and_load(tmp_path):
    src_dir = os.path.join(os.path.dirname(__file__), 'manifesttest')

    pkg_dir = gen_mangled_manifest_package(src_dir, str(tmp_path))
    assert os.path.isfile(os.path.join(pkg_dir, '.om-manifests.json'))

    # FIXME: need to run in a subprocess with a separate PYTHONPATH or something..
    # vs = load_package_manifest_values(str(tmp_path), 'manifesttest', SubtypeManifest)
    # assert len(vs) == 2
    #
    # by_attr = {v.attr: v for v in vs}
    #
    # v1 = by_attr['FirstThing']
    # assert v1.module == 'manifesttest.impl1'
    # assert v1.base == '$.base.Thing'
    # assert v1.tag is None
    # assert v1.alts is None
    # assert v1.resolve_base_path() == 'manifesttest.base.Thing'
    #
    # v2 = by_attr['SecondThing']
    # assert v2.module == 'manifesttest.foo.impl2'
    # assert v2.resolve_base_path() == 'manifesttest.base.Thing'
    # assert v2.tag == 'second'
    # assert tuple(v2.alts or ()) == ('2nd',)
    #
    # import manifesttest.base  # type: ignore[import-not-found]  # noqa
    #
    # thing_cls = manifesttest.base.Thing
    # assert set(match_subtype_manifests(thing_cls, vs)) == set(vs)
    #
    # r1 = v1.resolve()
    # assert r1.__name__ == 'FirstThing'
    # assert issubclass(r1, thing_cls)
    #
    # r2 = v2.resolve()
    # assert r2.__name__ == 'SecondThing'
    # assert issubclass(r2, thing_cls)
