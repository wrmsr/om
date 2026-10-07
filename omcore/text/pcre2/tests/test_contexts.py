import threading

import pytest

from .. import _pcre2 as pcre2


##


def test_newline():
    md = pcre2.MatchData.create(1)

    code = pcre2.compile(b'^b', pcre2.MULTILINE)
    assert code.pattern_info(pcre2.INFO_NEWLINE) == pcre2.config(pcre2.CONFIG_NEWLINE) == pcre2.NEWLINE_LF
    assert code.match(b'a\rb', md) == pcre2.ERROR_NOMATCH

    code = pcre2.compile(b'^b', pcre2.MULTILINE, pcre2.CompileContext.create(newline=pcre2.NEWLINE_CR))
    assert code.pattern_info(pcre2.INFO_NEWLINE) == pcre2.NEWLINE_CR
    assert code.match(b'a\rb', md) == 1
    assert md.ovector == (2, 3)


def test_bsr():
    md = pcre2.MatchData.create(1)

    code = pcre2.compile(rb'a\Rb')
    assert code.pattern_info(pcre2.INFO_BSR) == pcre2.BSR_UNICODE
    assert code.match(b'a\x0bb', md) == 1

    code = pcre2.compile(rb'a\Rb', compile_context=pcre2.CompileContext.create(bsr=pcre2.BSR_ANYCRLF))
    assert code.pattern_info(pcre2.INFO_BSR) == pcre2.BSR_ANYCRLF
    assert code.match(b'a\x0bb', md) == pcre2.ERROR_NOMATCH
    assert code.match(b'a\r\nb', md) == 1


def test_max_pattern_length():
    context = pcre2.CompileContext.create(max_pattern_length=3)
    assert pcre2.compile(b'abc', 0, context).pattern_info(pcre2.INFO_SIZE) > 0

    with pytest.raises(pcre2.CompileError) as ei:
        pcre2.compile(b'abcd', 0, context)
    assert ei.value.code == pcre2.ERROR_PATTERN_STRING_TOO_LONG


def test_max_pattern_compiled_length():
    context = pcre2.CompileContext.create(max_pattern_compiled_length=64)
    assert pcre2.compile(b'abc', 0, context).pattern_info(pcre2.INFO_SIZE) > 0

    with pytest.raises(pcre2.CompileError) as ei:
        pcre2.compile(b'a' * 100, 0, context)
    assert ei.value.code == pcre2.ERROR_PATTERN_COMPILED_SIZE_TOO_BIG


def test_parens_nest_limit():
    context = pcre2.CompileContext.create(parens_nest_limit=2)
    assert pcre2.compile(b'((a))', 0, context).pattern_info(pcre2.INFO_CAPTURECOUNT) == 2

    with pytest.raises(pcre2.CompileError) as ei:
        pcre2.compile(b'(((a)))', 0, context)
    assert ei.value.code == pcre2.ERROR_PARENTHESES_NEST_TOO_DEEP
    assert ei.value.offset == 3


def test_max_varlookbehind():
    pattern = rb'(?<=a{1,5})b'
    assert pcre2.compile(pattern).pattern_info(pcre2.INFO_MAXLOOKBEHIND) == 5

    with pytest.raises(pcre2.CompileError) as ei:
        pcre2.compile(pattern, 0, pcre2.CompileContext.create(max_varlookbehind=2))
    assert ei.value.code == pcre2.ERROR_MAX_VAR_LOOKBEHIND_EXCEEDED


def test_extra_options():
    plain = pcre2.compile(b'cat')
    word = pcre2.compile(b'cat', 0, pcre2.CompileContext.create(extra_options=pcre2.EXTRA_MATCH_WORD))
    assert plain.pattern_info(pcre2.INFO_EXTRAOPTIONS) == 0
    assert word.pattern_info(pcre2.INFO_EXTRAOPTIONS) == pcre2.EXTRA_MATCH_WORD

    md = pcre2.MatchData.create(1)
    assert plain.match(b'concat', md) == 1
    assert word.match(b'concat', md) == pcre2.ERROR_NOMATCH
    assert word.match(b'a cat', md) == 1


@pytest.mark.parametrize(('optimize', 'matches'), [
    (None, True),
    (pcre2.OPTIMIZATION_FULL, True),
    (pcre2.START_OPTIMIZE_OFF, False),
    (pcre2.OPTIMIZATION_NONE, False),
    ([pcre2.OPTIMIZATION_NONE, pcre2.START_OPTIMIZE], True),
    ((pcre2.START_OPTIMIZE_OFF, pcre2.AUTO_POSSESS_OFF, pcre2.DOTSTAR_ANCHOR_OFF), False),
    ([], True),
])
def test_optimize(optimize, matches):
    # With its start optimizations PCRE2 only tries this where it could match, at the A, so the (*COMMIT) is never
    # reached anywhere it would rule a match out. Without them it is first tried at the D, and that is that.
    code = pcre2.compile(b'(*COMMIT)ABC', 0, pcre2.CompileContext.create(optimize=optimize))
    md = pcre2.MatchData.create(1)
    assert code.match(b'DEFABC', md) == (1 if matches else pcre2.ERROR_NOMATCH)


def test_settings_combine():
    context = pcre2.CompileContext.create(
        newline=pcre2.NEWLINE_CRLF,
        bsr=pcre2.BSR_ANYCRLF,
        max_pattern_length=100,
        parens_nest_limit=10,
        extra_options=pcre2.EXTRA_MATCH_LINE,
        optimize=pcre2.OPTIMIZATION_NONE,
    )
    code = pcre2.compile(b'b', pcre2.MULTILINE, context)
    assert code.pattern_info(pcre2.INFO_NEWLINE) == pcre2.NEWLINE_CRLF
    assert code.pattern_info(pcre2.INFO_BSR) == pcre2.BSR_ANYCRLF
    assert code.pattern_info(pcre2.INFO_EXTRAOPTIONS) == pcre2.EXTRA_MATCH_LINE

    md = pcre2.MatchData.create(1)
    assert code.match(b'ab\r\nb\r\n', md) == 1
    assert md.ovector == (4, 5)


def test_no_settings_given():
    assert pcre2.compile(b'a', 0, pcre2.CompileContext.create()).pattern_info(pcre2.INFO_EXTRAOPTIONS) == 0


def test_invalid_settings():
    for kwargs in [
        {'newline': 99},
        {'bsr': 99},
    ]:
        with pytest.raises(pcre2.Error) as ei:
            pcre2.CompileContext.create(**kwargs)
        assert ei.value.code == pcre2.ERROR_BADDATA

    for optimize in [12345, [pcre2.OPTIMIZATION_FULL, 12345]]:
        with pytest.raises(pcre2.Error) as ei:
            pcre2.CompileContext.create(optimize=optimize)  # type: ignore[arg-type]
        assert ei.value.code == pcre2.ERROR_BADOPTION


def test_arguments():
    with pytest.raises(TypeError):
        pcre2.CompileContext.create(pcre2.NEWLINE_LF)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        pcre2.CompileContext.create(newline='lf')  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        pcre2.CompileContext.create(optimize=1.5)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        pcre2.CompileContext.create(optimize=['none'])  # type: ignore[list-item]
    with pytest.raises(OverflowError):
        pcre2.CompileContext.create(parens_nest_limit=-1)
    with pytest.raises(OverflowError):
        pcre2.CompileContext.create(max_varlookbehind=1 << 32)
    with pytest.raises(OverflowError):
        pcre2.CompileContext.create(max_pattern_length=-1)
    with pytest.raises(OverflowError):
        pcre2.CompileContext.create(optimize=[-1])


def test_context_is_shared_between_threads():
    context = pcre2.CompileContext.create(max_pattern_length=8, extra_options=pcre2.EXTRA_MATCH_WORD)

    num_threads = 8
    barrier = threading.Barrier(num_threads)
    results: list = [None] * num_threads

    def run(i):
        md = pcre2.MatchData.create(1)
        out = []
        barrier.wait()
        for _ in range(200):
            code = pcre2.compile(b'cat', 0, context)
            out.append(code.match(b'concat cat', md))
            try:
                pcre2.compile(b'caterpillar', 0, context)
            except pcre2.CompileError as e:
                out.append(e.code)
        results[i] = out

    threads = [threading.Thread(target=run, args=(i,)) for i in range(num_threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    for result in results:
        assert result == [1, pcre2.ERROR_PATTERN_STRING_TOO_LONG] * 200
