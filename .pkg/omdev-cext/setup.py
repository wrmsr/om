import sys

import setuptools as st


st.setup(
    ext_modules=[

        st.Extension(
            name='omdev.cexts._boilerplate',
            sources=[
                'omdev/cexts/_boilerplate.cc',
            ],
            extra_compile_args=[
                '-std=c++20',
            ],
        ),

        st.Extension(
            name='omdev.js.quickjs._pyqjsng',
            sources=[
                'omdev/js/quickjs/_pyqjsng.c',
                'omdev/js/quickjs/_quickjs/dtoa.c',
                'omdev/js/quickjs/_quickjs/libregexp.c',
                'omdev/js/quickjs/_quickjs/libunicode.c',
                'omdev/js/quickjs/_quickjs/quickjs-libc.c',
                'omdev/js/quickjs/_quickjs/quickjs.c',
            ],
            extra_compile_args=[
                '-std=c11',
                '-Wno-sign-compare',
                '-Wno-unreachable-code',
                '-Wno-unused-but-set-variable',
                '-Wno-unused-const-variable',
                '-Wno-unused-function',
                '-fvisibility=hidden',
                '-g0',
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
