import sys

import setuptools as st


st.setup(
    ext_modules=[
        st.Extension(
            name='omxtra.collections.stl._stl',
            sources=[
                'omxtra/collections/stl/_stl.cc',
            ],
            extra_compile_args=[
                '-std=c++20',
            ],
        ),
        st.Extension(
            name='omxtra.js.quickjs._pyqjsng',
            sources=[
                'omxtra/js/quickjs/_pyqjsng.c',
                'omxtra/js/quickjs/quickjs-amalgam.c',
            ],
            extra_compile_args=[
                '-std=c11',
            ],
            define_macros=[
                ('_GNU_SOURCE', '1'),
            ],
            libraries=[
                *(['m'] if sys.platform == 'linux' else []),
            ],
        ),
    ],
)
