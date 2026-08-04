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
        return ['omxtra/js/quickjs/_pyqjsng.c']

    def _get_ext_file_config(self, src_file):
        return CextConfig(
            extra_sources=['*.c', './*.c', '_quickjs/quickjs.c'],
            extra_headers=['**/quickjs*.h'],
        )


def test_cext_package_extra_source_paths():
    gen = _TestCextPackageGenerator('omxtra', '.pkg-test', pkg_suffix='-cext')

    assert """sources=[
                'omxtra/js/quickjs/_pyqjsng.c',
                'omxtra/js/quickjs/_quickjs/quickjs.c',
            ],""" in gen.file_contents().setup_py
    assert gen.file_contents().setup_py.count("'omxtra/js/quickjs/_pyqjsng.c',") == 1
    assert 'quickjs*' not in gen.file_contents().setup_py
    assert 'include omxtra/js/quickjs/_quickjs/quickjs.h' in (gen.file_contents().manifest_in or [])
