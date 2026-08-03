import os.path
import shutil
import subprocess
import sys

import pytest

from ..cmake import CmakeProjectGen
from ..configs import resolve_cext_config_file


def test_resolve_cext_config_file():
    assert resolve_cext_config_file('omxtra/foo/_foo.c', 'foo-amalg.c') == os.path.join(
        'omxtra',
        'foo',
        'foo-amalg.c',
    )
    assert resolve_cext_config_file('omxtra/foo/_foo.c', '../common.c') == os.path.join(
        'omxtra',
        'common.c',
    )

    with pytest.raises(ValueError, match='foo-amalg'):
        resolve_cext_config_file('omxtra/foo/_foo.c', '../../foo-amalg.c')


def test_cmake_project_gen_cext_config(tmp_path):
    prj_root = str(tmp_path)
    package_dir = os.path.join(prj_root, 'sample')
    ext_dir = os.path.join(package_dir, 'foo')
    os.makedirs(ext_dir)

    with open(os.path.join(prj_root, 'pyproject.toml'), 'w') as f:
        f.write('')
    with open(os.path.join(prj_root, '.clang-tidy'), 'w') as f:
        f.write('')

    ext_src = os.path.join(ext_dir, '_foo.c')
    platform_library = 'm' if sys.platform == 'linux' else 'z'
    with open(ext_src, 'w') as f:
        f.write(f"""// @om-cext {{
//   "extra_sources": ["foo-amalg.c"],
//   "extra_headers": ["foo.h"],
//   "extra_compile_args": ["-Wextra"],
//   "extra_link_args": ["-g"],
//   "define_macros": {{"_GNU_SOURCE": "1"}},
//   "libraries": [
//     "${{CMAKE_DL_LIBS}}",
//     ["{platform_library}", "{sys.platform}"],
//     ["other-platform", "not-{sys.platform}"]
//   ]
// }}
#include "foo.h"

#ifndef _GNU_SOURCE
#error _GNU_SOURCE is not defined
#endif

int extra_value(void);

int configured_value(void)
{{
    return FOO_VALUE + extra_value();
}}
""")

    with open(os.path.join(ext_dir, 'foo-amalg.c'), 'w') as f:
        f.write('int extra_value(void) { return 1; }\n')
    with open(os.path.join(ext_dir, 'foo.h'), 'w') as f:
        f.write('#define FOO_VALUE 2\n')

    gen = CmakeProjectGen([package_dir], prj_root)
    gen.run()

    cmake_dir = os.path.join(prj_root, 'cmake', os.path.basename(prj_root))
    linked_files = [
        os.path.join('sample', 'foo', '_foo.c'),
        os.path.join('sample', 'foo', 'foo-amalg.c'),
        os.path.join('sample', 'foo', 'foo.h'),
    ]
    for linked_file in linked_files:
        link_file = os.path.join(cmake_dir, linked_file)
        assert os.path.islink(link_file)
        assert os.path.samefile(link_file, os.path.join(prj_root, linked_file))

    with open(os.path.join(cmake_dir, 'CMakeLists.txt')) as f:
        cmake_lists = f.read()

    for linked_file in linked_files:
        assert os.path.join(cmake_dir, linked_file) in cmake_lists

    assert 'target_compile_definitions(sample__foo___foo PRIVATE\n    _GNU_SOURCE=1\n)' in cmake_lists
    assert '    -Wextra\n' in cmake_lists
    assert 'target_link_options(sample__foo___foo PRIVATE\n    -g\n)' in cmake_lists
    assert '    ${CMAKE_DL_LIBS}\n' in cmake_lists
    assert f'    {platform_library}\n' in cmake_lists
    assert 'other-platform' not in cmake_lists

    cmake_exe = shutil.which('cmake')
    if cmake_exe is None:
        pytest.skip('cmake is not installed')

    build_dir = os.path.join(cmake_dir, 'build')
    subprocess.run([cmake_exe, '-S', cmake_dir, '-B', build_dir], check=True)
    subprocess.run([cmake_exe, '--build', build_dir], check=True)
