import setuptools as st


st.setup(
    ext_modules=[

        st.Extension(
            name='omcore._check',
            sources=[
                'omcore/_check.cc',
            ],
            extra_compile_args=[
                '-std=c++20',
            ],
        ),

        st.Extension(
            name='omcore.collections.btreemap._btreemap',
            sources=[
                'omcore/collections/btreemap/_btreemap.cc',
            ],
            extra_compile_args=[
                '-std=c++20',
            ],
        ),

        st.Extension(
            name='omcore.collections.btreeseq._btreeseq',
            sources=[
                'omcore/collections/btreeseq/_btreeseq.cc',
            ],
            extra_compile_args=[
                '-std=c++20',
            ],
        ),

        st.Extension(
            name='omcore.collections.fixedmap._fixedmap',
            sources=[
                'omcore/collections/fixedmap/_fixedmap.cc',
            ],
            extra_compile_args=[
                '-std=c++20',
            ],
        ),

        st.Extension(
            name='omcore.collections.hamt._hamt',
            sources=[
                'omcore/collections/hamt/_hamt.c',
            ],
            extra_compile_args=[
                '-std=c11',
            ],
        ),

        st.Extension(
            name='omcore.collections.stl._stl',
            sources=[
                'omcore/collections/stl/_stl.cc',
                'omcore/collections/stl/tlx/tlx/die/core.cpp',
            ],
            extra_compile_args=[
                '-std=c++20',
                '-fvisibility=hidden',
                '-g0',
            ],
        ),

        st.Extension(
            name='omcore.collections.treap._treap',
            sources=[
                'omcore/collections/treap/_treap.cc',
            ],
            extra_compile_args=[
                '-std=c++20',
            ],
        ),

        st.Extension(
            name='omcore.dispatch._dispatch',
            sources=[
                'omcore/dispatch/_dispatch.cc',
            ],
            extra_compile_args=[
                '-std=c++20',
            ],
        ),

        st.Extension(
            name='omcore.dispatch._methods',
            sources=[
                'omcore/dispatch/_methods.cc',
            ],
            extra_compile_args=[
                '-std=c++20',
            ],
        ),

        st.Extension(
            name='omcore.lang._asyncs',
            sources=[
                'omcore/lang/_asyncs.cc',
            ],
            extra_compile_args=[
                '-std=c++20',
            ],
        ),

        st.Extension(
            name='omcore.lang._comparison',
            sources=[
                'omcore/lang/_comparison.cc',
            ],
            extra_compile_args=[
                '-std=c++20',
            ],
        ),

        st.Extension(
            name='omcore.lang._functions',
            sources=[
                'omcore/lang/_functions.cc',
            ],
            extra_compile_args=[
                '-std=c++20',
            ],
        ),

        st.Extension(
            name='omcore.lang.cached._hash',
            sources=[
                'omcore/lang/cached/_hash.cc',
            ],
            extra_compile_args=[
                '-std=c++20',
            ],
        ),

        st.Extension(
            name='omcore.lang.imports._capture',
            sources=[
                'omcore/lang/imports/_capture.cc',
            ],
            extra_compile_args=[
                '-std=c++20',
            ],
        ),

        st.Extension(
            name='omcore.text.pcre2._pcre2',
            sources=[
                'omcore/text/pcre2/_pcre2.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_auto_possess.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_chartables.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_chkdint.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_compile.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_compile_cgroup.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_compile_class.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_config.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_context.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_dfa_match.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_error.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_extuni.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_find_bracket.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_match.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_match_data.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_match_next.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_newline.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_ord2utf.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_pattern_info.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_script_run.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_string_utils.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_study.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_substitute.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_substring.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_tables.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_ucd.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_valid_utf.c',
                'omcore/text/pcre2/_pcre2_/src/pcre2_xclass.c',
            ],
            extra_compile_args=[
                '-std=c11',
                '-fvisibility=hidden',
                '-g0',
            ],
            define_macros=[
                ('PCRE2_CODE_UNIT_WIDTH', '8'),
                ('PCRE2_STATIC', '1'),
                ('PCRE2_EXPORT', ''),
                ('SUPPORT_UNICODE', '1'),
                ('SUPPORT_PCRE2_8', '1'),
                ('LINK_SIZE', '2'),
                ('HEAP_LIMIT', '20000000'),
                ('MATCH_LIMIT', '10000000'),
                ('MATCH_LIMIT_DEPTH', '10000000'),
                ('MAX_NAME_COUNT', '10000'),
                ('MAX_NAME_SIZE', '128'),
                ('MAX_VARLOOKBEHIND', '255'),
                ('NEWLINE_DEFAULT', '2'),
                ('PARENS_NEST_LIMIT', '250'),
            ],
        ),

        st.Extension(
            name='omcore.typedvalues._collection',
            sources=[
                'omcore/typedvalues/_collection.cc',
            ],
            extra_compile_args=[
                '-std=c++20',
            ],
        ),

    ],
)
