import sys

from .. import _pcre2 as pcre2


##


def test_code_size():
    small = pcre2.compile(b'a')
    large = pcre2.compile(b'|'.join(f'word{i}'.encode() for i in range(1000)))

    assert sys.getsizeof(small) > small.pattern_info(pcre2.INFO_SIZE) > 0
    assert sys.getsizeof(large) - sys.getsizeof(small) == (
        large.pattern_info(pcre2.INFO_SIZE) - small.pattern_info(pcre2.INFO_SIZE)
    )


def test_match_data_size():
    small = pcre2.MatchData.create(1)
    large = pcre2.MatchData.create(100)
    assert small.size > 0
    assert large.size - small.size == 99 * 2 * 8
    assert small.heapframes_size == 0
    assert sys.getsizeof(large) - sys.getsizeof(small) == large.size - small.size


def test_heapframes_size():
    # A block keeps the memory a match needed for backtracking, to use again.
    code = pcre2.compile(rb'(a|b)*$')
    md = pcre2.MatchData.create_from_pattern(code)
    before = sys.getsizeof(md)

    assert code.match(b'ab', md) == 2
    shallow = md.heapframes_size
    assert shallow > 0

    assert code.match(b'ab' * 5000, md) == 2
    deep = md.heapframes_size
    assert deep > shallow
    assert sys.getsizeof(md) - before == deep
