from ...cexts.configs import CextConfig
from ..pkg import _PyprojectCextPackageGenerator


class _TestCextPackageGenerator(_PyprojectCextPackageGenerator):
    def build_specs(self):
        return self.Specs(
            pyproject={
                'name': 'sample',
                'version': '1.0',
            },
            setuptools={},
        )

    def find_cext_srcs(self):
        return ['sample/foo/_foo.c']

    def _get_ext_file_config(self, src_file):
        return CextConfig(
            extra_sources=['foo-amalg.c'],
            extra_headers=['foo.h'],
        )


def test_cext_package_extra_source_paths():
    gen = _TestCextPackageGenerator('sample', '.pkg-test', pkg_suffix='-cext')

    assert """sources=[
                'sample/foo/_foo.c',
                'sample/foo/foo-amalg.c',
            ],""" in gen.file_contents().setup_py
    assert 'foo.h' not in gen.file_contents().setup_py
