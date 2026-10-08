"""
A slow and obvious byte pair encoder to check the extension against. It recounts every pair for every merge, and
re-scans every chunk for every merge it applies, and has nothing in common with the extension but the regex engine it
splits with.
"""
import collections
import itertools

from omcore.text.pcre2 import _pcre2


##


def split(pattern, text):
    code = _pcre2.compile(pattern.encode(), _pcre2.UTF | _pcre2.UCP)
    match_data = _pcre2.MatchData.create_from_pattern(code)
    subject = text.encode()

    chunks = []
    offset = 0
    while offset <= len(subject) and code.match(subject, match_data, offset) >= 0:
        start, end = match_data.ovector[:2]
        if end > start:
            chunks.append(subject[start:end])
            offset = end
        else:
            # An empty match is no chunk, and the next is looked for from one character on: how Rust's regexes go
            # about it, which is not how PCRE2's own next_match does.
            offset = end + 1
            while offset < len(subject) and subject[offset] & 0xC0 == 0x80:
                offset += 1
    return chunks


def merge(ids, pair, token):
    out = []
    i = 0
    while i < len(ids):
        if i + 1 < len(ids) and (ids[i], ids[i + 1]) == pair:
            out.append(token)
            i += 2
        else:
            out.append(ids[i])
            i += 1
    return out


def train(pattern, texts, vocab_size):
    chunk_counts = collections.Counter(chunk for text in texts for chunk in split(pattern, text))
    words = [(list(chunk), count) for chunk, count in chunk_counts.items()]

    merges = []
    for token in range(256, vocab_size):
        pair_counts: collections.Counter = collections.Counter()
        for ids, count in words:
            for pair in itertools.pairwise(ids):
                pair_counts[pair] += count
        if not pair_counts:
            break

        # The most frequent pair, and of those equally frequent the least.
        pair = min(pair_counts, key=lambda pair: (-pair_counts[pair], pair))
        merges.append(pair)
        words = [(merge(ids, pair, token), count) for ids, count in words]

    return merges


def encode(pattern, merges, text):
    ranks = {pair: 256 + i for i, pair in enumerate(merges)}

    out = []
    for chunk in split(pattern, text):
        ids = list(chunk)
        while True:
            # The pair merged earliest in training, and of those the first, one occurrence at a time.
            candidates = [(ranks[pair], i) for i, pair in enumerate(itertools.pairwise(ids)) if pair in ranks]
            if not candidates:
                break
            rank, i = min(candidates)
            ids[i:i + 2] = [rank]
        out.extend(ids)
    return out


def mergeable_ranks(merges):
    vocab = [bytes([byte]) for byte in range(256)]
    for left, right in merges:
        vocab.append(vocab[left] + vocab[right])
    return [(token_bytes, token) for token, token_bytes in enumerate(vocab)]
