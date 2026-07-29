from ..cli import wrap_cli_text


def test_docstring_bug():
    in_txt = '''\
"""
I am a test string. I am a test string. I am a test string. I am a test string. I am a test string. I am a test string.
I am a test string. I am a test string. I am a test string.
"""

abcd
'''

    for kw in [
        dict(
            start_line=2,
            start_col=1,
            end_line=3,
            end_col=60,
        ),
        dict(
            start_line=2,
            start_col=1,
            end_line=4,
            end_col=1,
        ),
    ]:
        out_txt = wrap_cli_text(
            in_txt,
            width=120,
            **kw,
        )

        print(out_txt)
        assert out_txt == in_txt
