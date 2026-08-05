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
        return ['omdev/js/quickjs/_pyqjsng.c']

    def _get_ext_file_config(self, src_file):
        return CextConfig(
            extra_sources=['*.c', './*.c', '_quickjs/quickjs.c'],
            extra_headers=['**/quickjs*.h'],
        )


def test_cext_package_extra_source_paths():
    gen = _TestCextPackageGenerator('omdev', '.pkg-test', pkg_suffix='-cext')

    assert """sources=[
                'omdev/js/quickjs/_pyqjsng.c',
                'omdev/js/quickjs/_quickjs/quickjs.c',
            ],""" in gen.file_contents().setup_py
    assert gen.file_contents().setup_py.count("'omdev/js/quickjs/_pyqjsng.c',") == 1
    assert 'quickjs*' not in gen.file_contents().setup_py
    assert 'include omdev/js/quickjs/_quickjs/quickjs.h' in (gen.file_contents().manifest_in or [])
