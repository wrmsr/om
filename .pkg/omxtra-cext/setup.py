import setuptools as st


st.setup(
    ext_modules=[

        st.Extension(
            name='omxtra.text.pcre2._pcre2',
            sources=[
                'omxtra/text/pcre2/_pcre2.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_auto_possess.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_chartables.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_chkdint.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_compile.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_compile_cgroup.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_compile_class.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_config.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_context.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_error.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_extuni.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_find_bracket.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_match.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_match_data.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_match_next.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_newline.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_ord2utf.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_pattern_info.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_script_run.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_string_utils.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_study.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_substitute.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_substring.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_tables.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_ucd.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_valid_utf.c',
                'omxtra/text/pcre2/_pcre2_/src/pcre2_xclass.c',
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

    ],
)
