from .. import _pcre2 as pcre2


##


def find_spans(code, subject, options=0):
    """Every match of a global search, found by the loop PCRE2 documents for pcre2_next_match."""

    md = pcre2.MatchData.create_from_pattern(code)
    spans = []
    start_offset = 0
    next_options = 0
    while code.match(subject, md, start_offset, options | next_options) >= 0:
        ovector = md.ovector
        spans.append((ovector[0], ovector[1]))
        if (nxt := md.next_match()) is None:
            break
        start_offset, next_options = nxt
    return spans
