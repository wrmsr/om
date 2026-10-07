# @om-precheck-allow-any-unicode
import re
import threading

import pytest

from .. import _pcre2 as pcre2


##


def test_substitute():
    code = pcre2.compile(rb'(\w+)@(\w+)')
    assert code.substitute(b'a@b c@d', b'$2@$1') == (b'b@a c@d', 1)
    assert code.substitute(b'a@b c@d', b'$2@$1', options=pcre2.SUBSTITUTE_GLOBAL) == (b'b@a d@c', 2)
    assert code.substitute(b'nothing', b'x', options=pcre2.SUBSTITUTE_GLOBAL) == (b'nothing', 0)
    assert code.substitute(b'a@b c@d', b'X', 3, pcre2.SUBSTITUTE_GLOBAL) == (b'a@b X', 1)
    assert code.substitute(b'', b'x') == (b'', 0)


def test_replacement_syntax():
    code = pcre2.compile(rb'(?<key>\w+)=(?<value>\w+)')
    assert code.substitute(b'a=1', b'${value}=${key}') == (b'1=a', 1)
    assert code.substitute(b'a=1', b'<$0>') == (b'<a=1>', 1)
    assert code.substitute(b'a=1', b'$$') == (b'$', 1)

    # re's group references are not PCRE2's.
    assert code.substitute(b'a=1', rb'\1') == (rb'\1', 1)


def test_options():
    code = pcre2.compile(rb'(\w+)@(\w+)|(!)')
    subject = b'a@b c@d !'

    assert code.substitute(subject, b'$1', options=pcre2.SUBSTITUTE_LITERAL) == (b'$1 c@d !', 1)

    replacement_only = pcre2.SUBSTITUTE_GLOBAL | pcre2.SUBSTITUTE_REPLACEMENT_ONLY | pcre2.SUBSTITUTE_UNSET_EMPTY
    assert code.substitute(subject, b'<$1>', options=replacement_only) == (b'<a><c><>', 3)

    extended = pcre2.SUBSTITUTE_GLOBAL | pcre2.SUBSTITUTE_EXTENDED
    assert code.substitute(subject, rb'${1:+\U$1\E:bang}', options=extended) == (b'A C bang', 3)

    lenient = pcre2.SUBSTITUTE_GLOBAL | pcre2.SUBSTITUTE_UNKNOWN_UNSET | pcre2.SUBSTITUTE_UNSET_EMPTY
    assert code.substitute(subject, b'[$9]', options=lenient) == (b'[] [] []', 3)

    # Asking for what the binding always asks for anyway changes nothing.
    assert code.substitute(subject, b'x', options=pcre2.SUBSTITUTE_OVERFLOW_LENGTH) == (b'x c@d !', 1)


@pytest.mark.parametrize(('pattern', 'replacement', 'subject'), [
    (rb'a', b'x', b'banana'),
    (rb'a', b'', b'banana'),
    (rb'an', b'[an]', b'banana'),
    (rb'', b'-', b'abc'),
    (rb'x*', b'-', b'abxd'),
    (rb'\s+', b' ', b'  a \t b\n'),
    (rb'b', b'x', b''),
])
def test_agrees_with_re_for_plain_replacements(pattern, replacement, subject):
    expected = re.subn(pattern, replacement, subject)
    assert pcre2.compile(pattern).substitute(subject, replacement, options=pcre2.SUBSTITUTE_GLOBAL) == expected


@pytest.mark.parametrize('size', [0, 1, 63, 64, 65, 511, 512, 513, 5000])
def test_result_of_any_size(size):
    # The result is built in a buffer sized by a guess, and again in one of exactly the right size if that was short.
    grow = pcre2.compile(b'a')
    assert grow.substitute(b'a' * size, b'bcd' * 5, options=pcre2.SUBSTITUTE_GLOBAL) == (b'bcd' * 5 * size, size)

    shrink = pcre2.compile(b'a+')
    assert shrink.substitute(b'a' * size, b'') == (b'', 1 if size else 0)

    same = pcre2.compile(b'x')
    assert same.substitute(b'a' * size, b'y', options=pcre2.SUBSTITUTE_GLOBAL) == (b'a' * size, 0)


def test_malformed_replacement():
    code = pcre2.compile(rb'(a)|(b)')

    for replacement, options, error, offset in [
        (b'ab$', 0, pcre2.ERROR_BADREPLACEMENT, 3),
        (b'ab${1', 0, pcre2.ERROR_REPMISSINGBRACE, 5),
        (rb'ab\q', pcre2.SUBSTITUTE_EXTENDED, pcre2.ERROR_BADREPESCAPE, 4),
        (b'$9', 0, pcre2.ERROR_NOSUBSTRING, 2),
        (b'[$2]', 0, pcre2.ERROR_UNSET, 3),
    ]:
        with pytest.raises(pcre2.SubstituteError) as ei:
            code.substitute(b'a', replacement, options=options)
        assert isinstance(ei.value, pcre2.Error)
        assert not isinstance(ei.value, pcre2.MatchError)
        assert ei.value.code == error
        assert ei.value.offset == offset


def test_errors():
    code = pcre2.compile(b'a')

    with pytest.raises(pcre2.SubstituteError) as ei:
        code.substitute(b'abc', b'x', 4)
    assert ei.value.code == pcre2.ERROR_BADOFFSET
    assert ei.value.offset is None

    with pytest.raises(pcre2.SubstituteError) as ei:
        code.substitute(b'abc', b'x', options=pcre2.UTF)
    assert ei.value.code == pcre2.ERROR_BADOPTION

    # Partial matching is only allowed where just the replacements are asked for.
    with pytest.raises(pcre2.SubstituteError) as ei:
        code.substitute(b'abc', b'x', options=pcre2.PARTIAL_SOFT)
    assert ei.value.code == pcre2.ERROR_BADOPTION


def test_arguments():
    code = pcre2.compile(b'a')

    with pytest.raises(TypeError):
        code.substitute('a', b'x')  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        code.substitute(b'a', 'x')  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        code.substitute(b'a')  # type: ignore[call-arg]
    with pytest.raises(ValueError):  # noqa
        code.substitute(b'a', b'x', -1)
    with pytest.raises(OverflowError):
        code.substitute(b'a', b'x', 0, -1)
    with pytest.raises(TypeError, match='expected MatchData or None'):
        code.substitute(b'a', b'x', match_data=code)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match='expected MatchContext or None'):
        code.substitute(b'a', b'x', match_context=code)  # type: ignore[arg-type]

    assert code.substitute(b'a', b'x', 0, 0, None, None) == (b'x', 1)


def test_utf():
    code = pcre2.compile(rb'\w+', pcre2.UTF | pcre2.UCP)
    subject = 'héllo wörld'.encode()
    result, count = code.substitute(subject, '«$0»'.encode(), options=pcre2.SUBSTITUTE_GLOBAL)
    assert (result.decode(), count) == ('«héllo» «wörld»', 2)

    for bad_subject, bad_replacement in [(b'ab\xff', b'x'), (b'ab', b'\xff')]:
        with pytest.raises(pcre2.SubstituteError) as ei:
            code.substitute(bad_subject, bad_replacement)
        assert pcre2.ERROR_UTF8_ERR21 <= ei.value.code <= pcre2.ERROR_UTF8_ERR1


def test_utf_pattern_needs_an_immutable_subject():
    code = pcre2.compile(b'a', pcre2.UTF)
    for subject in [bytearray(b'a'), memoryview(bytearray(b'a')).toreadonly()]:
        with pytest.raises(BufferError, match='could change during the match'):
            code.substitute(subject, b'x')  # type: ignore[arg-type]
        assert code.substitute(subject, b'x', options=pcre2.NO_UTF_CHECK) == (b'x', 1)  # type: ignore[arg-type]

    assert code.substitute(memoryview(b'ba')[1:], b'x') == (b'x', 1)
    assert pcre2.compile(b'a').substitute(bytearray(b'a'), b'x') == (b'x', 1)


def test_replacement_which_could_change_is_copied():
    code = pcre2.compile(b'a', pcre2.UTF)
    for replacement in [bytearray(b'[$0]'), memoryview(bytearray(b'[$0]')), memoryview(b'[$0]')]:
        assert code.substitute(b'a', replacement) == (b'[a]', 1)  # type: ignore[arg-type]


def test_limits():
    code = pcre2.compile(rb'(a+)+$')
    subject = b'a' * 40 + b'b'
    context = pcre2.MatchContext.create(match_limit=1000)

    with pytest.raises(pcre2.SubstituteError) as ei:
        code.substitute(subject, b'x', match_context=context)
    assert ei.value.code == pcre2.ERROR_MATCHLIMIT

    assert code.substitute(b'aaa', b'x', match_context=context) == (b'x', 1)


def test_substitution_which_outlasts_the_probe():
    # Short enough to be tried attached, and more backtracking than that is allowed - see test_detach.
    code = pcre2.compile(rb'(a|b)*$')
    subject = b'ab' * 200
    assert code.substitute(subject, b'[$1]') == (b'[b]', 1)
    everywhere = pcre2.SUBSTITUTE_GLOBAL | pcre2.SUBSTITUTE_UNSET_EMPTY
    assert code.substitute(subject, b'[$1]', options=everywhere) == (b'[b][]', 2)

    with pytest.raises(pcre2.SubstituteError) as ei:
        code.substitute(subject, b'x', match_context=pcre2.MatchContext.create(match_limit=300))
    assert ei.value.code == pcre2.ERROR_MATCHLIMIT


def test_long_subject():
    code = pcre2.compile(b'needle')
    subject = b'hay ' * 100_000 + b'needle'
    result, count = code.substitute(subject, b'pin', options=pcre2.SUBSTITUTE_GLOBAL)
    assert count == 1
    assert result == b'hay ' * 100_000 + b'pin'


##


def test_match_data_is_left_holding_nothing():
    code = pcre2.compile(rb'(*MARK:m)(\w)')
    md = pcre2.MatchData.create_from_pattern(code)
    subject = b'ab cd'

    assert code.match(subject, md) == 2
    assert md.mark == b'm'
    assert md.next_match() == (1, 0)

    for _ in range(3):
        assert code.substitute(subject, b'<$1>', options=pcre2.SUBSTITUTE_GLOBAL, match_data=md) == (
            b'<a><b> <c><d>',
            4,
        )
        assert md.next_match() is None
        assert md.mark is None

    assert code.match(subject, md) == 2
    assert md.ovector == (0, 1, 0, 1)


def test_substitute_matched():
    code = pcre2.compile(rb'(\w)@(\w)')
    md = pcre2.MatchData.create_from_pattern(code)
    subject = b'a@b c@d'
    matched = pcre2.SUBSTITUTE_MATCHED

    assert code.match(subject, md) == 3
    assert code.substitute(subject, b'<$1>', options=matched | pcre2.SUBSTITUTE_GLOBAL, match_data=md) == (
        b'<a> <c>',
        2,
    )

    # The block still holds the match it was given.
    assert md.ovector == (0, 3, 0, 1, 2, 3)
    assert md.next_match() == (3, 0)
    assert code.substitute(subject, b'<$2>', options=matched, match_data=md) == (b'<b> c@d', 1)

    # A match which found nothing is as good a place to start from.
    assert code.match(b'zzz', md) == pcre2.ERROR_NOMATCH
    assert code.substitute(b'zzz', b'x', options=matched, match_data=md) == (b'zzz', 0)


def test_substitute_matched_needs_the_match_it_is_given():
    code = pcre2.compile(rb'(\w)@(\w)')
    md = pcre2.MatchData.create_from_pattern(code)
    subject = b'a@b c@d'
    matched = pcre2.SUBSTITUTE_MATCHED

    for match_data in [None, pcre2.MatchData.create(3)]:
        with pytest.raises(ValueError, match='needs a MatchData holding the match'):
            code.substitute(subject, b'x', options=matched, match_data=match_data)

    assert code.match(subject, md, 1) == 3
    for other_code, other_subject, start_offset, options, error in [
        (pcre2.compile(b'a'), subject, 1, 0, pcre2.ERROR_DIFFSUBSPATTERN),
        (code, b'a@b c@d!', 1, 0, pcre2.ERROR_DIFFSUBSSUBJECT),
        (code, bytes(bytearray(subject)), 1, 0, pcre2.ERROR_DIFFSUBSSUBJECT),
        (code, subject, 0, 0, pcre2.ERROR_DIFFSUBSOFFSET),
        (code, subject, 1, pcre2.NOTBOL, pcre2.ERROR_DIFFSUBSOPTIONS),
    ]:
        with pytest.raises(pcre2.SubstituteError) as ei:
            other_code.substitute(other_subject, b'x', start_offset, matched | options, md)
        assert ei.value.code == error

    # None of which disturbed the block.
    assert md.ovector == (4, 7, 4, 5, 6, 7)
    assert code.substitute(subject, b'x', 1, matched, md) == (b'a@b x', 1)

    # A match which raised leaves nothing to start from.
    with pytest.raises(pcre2.MatchError):
        code.match(subject, md, 99)
    with pytest.raises(ValueError, match='needs a MatchData holding the match'):
        code.substitute(subject, b'x', options=matched, match_data=md)


def test_match_data_is_not_reentrant():
    code = pcre2.compile(b'a')
    md = pcre2.MatchData.create_from_pattern(code)

    class Reentrant:
        def __buffer__(self, flags):
            code.substitute(b'a', b'x', match_data=md)
            raise NotImplementedError

    with pytest.raises(RuntimeError, match='already in use'):
        code.substitute(Reentrant(), b'x', match_data=md)
    with pytest.raises(RuntimeError, match='already in use'):
        code.substitute(b'a', Reentrant(), match_data=md)

    assert code.substitute(b'a', b'x', match_data=md) == (b'x', 1)


def test_code_is_shared_between_threads():
    code = pcre2.compile(rb'\p{L}+', pcre2.UTF | pcre2.UCP)
    context = pcre2.MatchContext.create(match_limit=100_000)
    subjects = [
        'short héllo 123'.encode(),
        'long enough to be substituted off the interpreter, wörld 456 '.encode() * 200,
    ]
    replacement = '‹$0›'.encode()
    expected = [code.substitute(subject, replacement, options=pcre2.SUBSTITUTE_GLOBAL) for subject in subjects]

    num_threads = 8
    barrier = threading.Barrier(num_threads)
    results: list = [None] * num_threads

    def run(i):
        md = pcre2.MatchData.create_from_pattern(code)
        out = []
        barrier.wait()
        for _ in range(5):
            out.append([
                code.substitute(subject, replacement, 0, pcre2.SUBSTITUTE_GLOBAL, md if i % 2 else None, context)
                for subject in subjects
            ])
        results[i] = out

    threads = [threading.Thread(target=run, args=(i,)) for i in range(num_threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    for result in results:
        assert result == [expected] * 5
