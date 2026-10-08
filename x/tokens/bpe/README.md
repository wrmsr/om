# bpe

`_bpe` is a byte pair encoding trainer and encoder in the style of GPT-4's tokenizer: a regex splits text into chunks,
each chunk starts out as its UTF-8 bytes, and training repeatedly replaces the most frequent adjacent pair of tokens
with a new one. It is a C++ port of [rustbpe](https://github.com/karpathy/rustbpe): it keeps that library's interface,
and from the same text learns the same merges.

It links nothing. Its regex engine is PCRE2, which it uses through the table of functions `omcore.text.pcre2._pcre2`
exports - so that extension has to be built, or `omcore-cext` installed, for this one to import.

## Use

```python
from omllm.tokens.bpe import _bpe

tok = _bpe.Tokenizer()
tok.train_from_iterator(texts, vocab_size=4096)  # any iterable of str

ids = tok.encode('Hello world!')
tok.decode(ids)                    # 'Hello world!'
tok.batch_encode(['one', 'two'])   # a list of each one's tokens

tok.vocab_size                     # 4096, or fewer if the text ran out of pairs to merge
tok.get_pattern()                  # the regex the text is split by
tok.get_mergeable_ranks()          # [(b'\x00', 0), ..., (b'th', 256), ...]: what tiktoken takes a vocabulary as
```

The whole of it:

```python
Tokenizer()
Tokenizer.train_from_iterator(iterator, vocab_size, buffer_size=8192, pattern=None, *, num_threads=None)
Tokenizer.encode(text)
Tokenizer.batch_encode(texts, *, num_threads=None)
Tokenizer.decode(ids)
Tokenizer.get_pattern()
Tokenizer.get_mergeable_ranks()
Tokenizer.vocab_size
GPT4_PATTERN
```

Things worth knowing:

- A token is an `int`: 0 to 255 are the bytes, and 256 on are the merges, in the order they were learned. `encode`
  applies them in that order within each chunk, and never across two.
- Text the pattern does not match is in no chunk. It is not trained on, and `encode` leaves it out - so `decode` only
  gives a text back whole if the pattern, like the default one, matches all of it.
- Training takes texts from the iterator `buffer_size` at a time and splits each batch on up to `num_threads` threads,
  by default one per core. Neither changes what is learned.
- Training replaces a tokenizer's pattern and merges, but only once it is done. Until then, and if it raises - for a
  bad pattern, something other than a `str` in the texts, or `KeyboardInterrupt` - the tokenizer is as it was.
- A `Tokenizer` may be used from any number of threads at once, training included: every call works from whichever
  whole pattern and set of merges were current when it was made. Of two trainings at once the last to finish wins.
- All the heavy work - splitting, counting, merging, encoding anything of size - is done detached from the
  interpreter, and both training and `batch_encode` use threads of their own for it. A long training looks for signals
  as it goes, so can be interrupted.

## Differences from rustbpe

What is the same is the interface and, for the same pattern and text, the merges and the encodings. What is not:

- **The regex engine.** Patterns are PCRE2's, compiled with `UTF` and `UCP`, where rustbpe's are fancy-regex's. Both
  take what tokenizer patterns are written in - `\p{L}`, possessive quantifiers, lookaround - but they are not the same
  language, and where they share syntax they do not always share meaning:
  - `\s` matches U+180E, the Mongolian vowel separator, in PCRE2 and not in Rust.
  - `\w`, and so `\b`, differ past ASCII: Rust's has the zero width joiner and non-joiner, the spacing and enclosing
    marks, and the lettered symbols like Ⓐ, and PCRE2's has the numbers which are neither digits nor letters, like ½.
  - Each knows the Unicode of its day. PCRE2 10.49 has the letters and numbers of Unicode 17, which an engine built
    against an earlier version does not see as such.
  - `\C` is refused.

  The default pattern only uses `\s`, `\p{L}`, and `\p{N}` of these, so with it only U+180E and characters newer than
  the older engine's Unicode can split differently. This holds for tiktoken too, which is what a vocabulary trained
  here is likely to be encoded with: on such text it and `encode` here can disagree.
- **Errors.** A `vocab_size` under 256 or a `buffer_size` under 1 raises `ValueError`, where rustbpe panics at the one
  and hangs at the other. A match which runs into the regex engine's limits raises `RuntimeError`, from training and
  encoding alike, where rustbpe carries on without the text it could not match. `decode` raises `ValueError` for any
  `int` which is not a token, and `UnicodeDecodeError` for tokens whose bytes are not UTF-8, where rustbpe has an
  `OverflowError` for the negative ones and a `TypeError` for the bytes.
- **Counts** are 64 bit, where rustbpe's are 32.
- **Long chunks.** rustbpe encodes a chunk in time quadratic in its length, and this does not: a megabyte with nothing
  to split it at is encoded in a fraction of a second, where at the rate rustbpe goes it would take over an hour.
- **Threads and failure**, as above: rustbpe refuses to be used while it is training, and a training which fails
  leaves it with the new pattern and the old merges.

## Tests

`tests/golden.py` is what the rustbpe wheel itself makes of the texts in `tests/texts.py` - the merges it learns, the
encodings it gives, and where it splits - and is written by `tests/goldengen.py`, which needs that wheel installed.
The rest of the tests hold the extension to `tests/reference.py`, a few dozen lines of Python which do the same thing
slowly.
