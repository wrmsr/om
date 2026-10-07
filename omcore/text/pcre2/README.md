# pcre2

`_pcre2` is a direct binding of the 8-bit [PCRE2](https://github.com/PCRE2Project/pcre2) library. It is deliberately not
`re`: it exposes PCRE2's own functions, option bits, return codes, and offsets, and leaves everything `re`-shaped to
Python code layered on top.

It needs PCRE2 10.49 or newer - its table of constants is that release's - built for 8-bit code units with Unicode
support, linked statically with hidden visibility. The JIT is not used. The sources it is built from are vendored under
`_pcre2_`, and are only those it needs: binding more of PCRE2 can mean adding to the list in `_pcre2_/.om-vendor.json`.

## The binding

```python
code = _pcre2.compile(rb'(\w+)@(\w+)', _pcre2.UTF | _pcre2.UCP)
md = _pcre2.MatchData.create_from_pattern(code)

rc = code.match(b'  bob@example ', md)  # 3: the highest numbered group that matched, plus one
md.ovector                              # (2, 13, 2, 5, 6, 13)
md.next_match()                         # (13, 0): where, and with what options, to search next
```

| Python                                                 | PCRE2                                                    |
|--------------------------------------------------------|----------------------------------------------------------|
| `compile(pattern, options=0, compile_context=None)`    | `pcre2_compile`                                          |
| `Code.match(subject, match_data, start_offset=0, options=0, match_context=None)` | `pcre2_match`                  |
| `Code.dfa_match(subject, match_data, ..., wscount=1000)` | `pcre2_dfa_match`                                      |
| `Code.substitute(subject, replacement, ...)`           | `pcre2_substitute`                                       |
| `Code.pattern_info(what)`                              | `pcre2_pattern_info`                                     |
| `Code.substring_number_from_name(name)`                | `pcre2_substring_number_from_name`                       |
| `Code.substring_nametable_scan(name)`                  | `pcre2_substring_nametable_scan`                         |
| `MatchData.create(ovecsize)`                           | `pcre2_match_data_create`                                |
| `MatchData.create_from_pattern(code)`                  | `pcre2_match_data_create_from_pattern`                   |
| `MatchData.ovector`, `MatchData.ovector_count`         | `pcre2_get_ovector_pointer`, `pcre2_get_ovector_count`   |
| `MatchData.mark`, `MatchData.startchar`                | `pcre2_get_mark`, `pcre2_get_startchar`                  |
| `MatchData.size`, `MatchData.heapframes_size`          | `pcre2_get_match_data_size`, `..._heapframes_size`       |
| `MatchData.next_match()`                               | `pcre2_next_match`                                       |
| `CompileContext.create(*, newline=None, ...)`          | `pcre2_compile_context_create`, `pcre2_set_newline`, ... |
| `MatchContext.create(*, match_limit=None, ...)`        | `pcre2_match_context_create`, `pcre2_set_match_limit`, ... |
| `config(what)`                                         | `pcre2_config`                                           |
| `get_error_message(code)`                              | `pcre2_get_error_message`                                |

Constants are PCRE2's with the `PCRE2_` prefix dropped: `UTF`, `CASELESS`, `INFO_CAPTURECOUNT`, `ERROR_NOMATCH`, ...

Things worth knowing:

- Patterns and subjects are bytes-like, never `str`, and every offset is a byte offset. Nothing is implied: a pattern
  holding UTF-8 is only treated as UTF-8 with `UTF`, and `\w`, `\d`, `\s`, and `\b` only see past ASCII with `UCP`.
- `Code.match` returns `pcre2_match`'s return code as is when it is non-negative, `ERROR_NOMATCH`, or `ERROR_PARTIAL`.
  Any other code raises `MatchError`. Errors carry PCRE2's `code`, and an `offset` where PCRE2 reports one: into the
  pattern for a `CompileError`, into the subject for a `MatchError` over invalid UTF-8, and into the replacement for a
  `SubstituteError` over a malformed one. Every `ERROR_*` PCRE2 defines is exported, the compile errors included.
- An unset offset is `UNSET`, which is -1: `PCRE2_UNSET` read as a signed size. A new `MatchData` reads as all unset.
- After a successful match a `MatchData` holds the subject's buffer, and the `Code`, until it is next matched into -
  `pcre2_next_match` reads through both. A `bytearray` cannot be resized while it is held this way. After a failed or
  partial match it holds just the `Code`, which a mark points into.
- `MatchData.mark` is the name PCRE2 reports for the last match attempt: of the last `(*MARK)` on the way to a match,
  which is how a pattern can say which of its alternatives matched, or of the last one a failed attempt passed. It is
  `None` if there is none, and if the last attempt raised. `MatchData.startchar` is where the last match began, which
  `\K` can leave before the start of what it reports having matched.
- Groups are found by name with `Code.substring_number_from_name`, or with `Code.substring_nametable_scan`, which
  returns the numbers of every group of that name, where a pattern compiled with `DUPNAMES` has several. Names are
  `bytes`. Which of several took part in a match is for the ovector to say.
- `sys.getsizeof` of a `Code` or a `MatchData` includes what PCRE2 holds for it: for a `MatchData` the memory a match
  needed for backtracking and the DFA matcher's workspace, both of which it keeps to use again.
- A UTF pattern only matches a subject which cannot change: `bytes`, or a `memoryview` of `bytes`. Anything else raises
  `BufferError` - see [Threads](#threads) for why - unless `NO_UTF_CHECK` is given, which as in C is the caller's own
  promise that the subject is, and stays, valid. Other patterns take any buffer, and see it as it is at each call. A
  pattern which could change is compiled from a copy, as a replacement which could is used through one. What PCRE2
  then validates and reads is the copy, so it cannot be led out of bounds, but a copy is not a snapshot: taken while
  another thread is writing to the buffer it can come out part old and part new. Holding a buffer keeps it in place,
  not still, and keeping it still while it is in use is the caller's to do.
- Walking a subject match by match is linear in its length. PCRE2 on its own validates everything ahead of
  `start_offset` on every call, which is quadratic over a search; `Code.match` skips that for a subject the same `Code`
  has already validated through the same `MatchData`, so long as the same `bytes` object keeps being passed.
- Not bound: the JIT, serialization, pattern conversion, custom character tables, callouts of every kind, and the
  general context.

## The DFA matcher

`Code.dfa_match` is PCRE2's other matching algorithm. Where `match` follows one way through a pattern at a time, and
backs up to try another when it fails, this reads the subject once and keeps track of every way through that is still
open. It does not backtrack, and what it finds is not the one match Perl would but all of them:

```python
code = _pcre2.compile(rb'cat(er(pillar)?)?')
md = _pcre2.MatchData.create(8)

code.dfa_match(b'the caterpillar', md)  # 3
md.ovector[:6]                           # (4, 15, 4, 9, 4, 7): caterpillar, cater, and cat
```

- It returns how many matches it found from the first place any starts, and leaves them in the ovector longest first,
  each a start and an end. There are no captured groups, so the size of a block is how many matches it can hold, and
  zero is returned if there were more. `DFA_SHORTEST` has it stop at the first, shortest one.
- Which matches there are can turn on how PCRE2 compiled the pattern: a repeat which nothing after it could give
  ground to is made possessive, which leaves it one match. `NO_AUTO_POSSESS` at compile time brings back the rest.
- It does not do everything `match` does. A pattern with a backreference, `\K`, or a backtracking verb raises
  `MatchError` with `ERROR_DFA_UITEM`, and one compiled with `MATCH_INVALID_UTF` with `ERROR_DFA_UINVALID_UTF`.
- It works in a workspace of `wscount` ints, which the `MatchData` keeps for the next time. One too small for the ways
  through it has to keep track of ends the match with `ERROR_DFA_WSSIZE`. That is what bounds this matcher, and the
  bound is worth having: it does more the more it is tracking, and given room enough it can be as slow on a hostile
  pattern as backtracking is - the pattern in `tests/test_limits.py` fails at once in the default workspace, and with
  eight times that takes over a second on a subject of 400 characters. A match limit means something else to it, the
  number of places it starts a match from, and the depth and heap limits apply as usual.
- A match which ran out of subject - `ERROR_PARTIAL`, under `PARTIAL_HARD` or `PARTIAL_SOFT` - can be carried on into
  the next piece of it with `DFA_RESTART`, which is how a subject is matched in pieces. That has to be the next thing
  done with the block, by the same `Code`: what is carried on from is in the workspace, and anything else raises
  `MatchError` with `ERROR_DFA_BADRESTART`.
- Otherwise it is used as `match` is: the same rule for the subject of a UTF pattern, the same return codes and errors,
  and `MatchData.next_match` for a global search. It always runs detached from the interpreter.

## Substitution

```python
code = _pcre2.compile(rb'(?<user>\w+)@(?<host>\w+)')
code.substitute(b'bob@example, eve@other', b'${host}!$1', options=_pcre2.SUBSTITUTE_GLOBAL)
# (b'example!bob, other!eve', 2): the result, and how many substitutions made it
```

- The replacement is in PCRE2's syntax, not `re`'s: `$1` and `${name}`, `$$` for a dollar, and with
  `SUBSTITUTE_EXTENDED` case forcing and `${1:+set:unset}`. `re`'s `\1` is two ordinary characters.
- Just the first match is replaced without `SUBSTITUTE_GLOBAL`. The other `SUBSTITUTE_*` options are PCRE2's as they
  come, except that the binding always sizes the result itself, which is what `SUBSTITUTE_OVERFLOW_LENGTH` is for in C.
- A negative return code raises `SubstituteError`, whichever part of the work it came from - a match limit being
  exceeded is `ERROR_MATCHLIMIT` here just as it is from `match`.
- The subject is held to the same rule as in `match`. A replacement which could change is used through a copy.
- A `MatchData` is optional. Passing one reuses its memory, and it holds nothing afterwards. With `SUBSTITUTE_MATCHED`
  it is instead the match to start from, so has to be holding one - PCRE2 checks that it was made by this `Code`, in
  this subject, at this offset and with these options - and is left exactly as it was.
- Like a match, a substitution with little subject ahead of it is first tried attached to the interpreter, and one that
  outlasts that, or has more, runs detached.

## Compiling

A `CompileContext` carries what a compilation is done under, and is passed to `compile`:

```python
context = _pcre2.CompileContext.create(max_pattern_length=1000, parens_nest_limit=50, newline=_pcre2.NEWLINE_ANYCRLF)
code = _pcre2.compile(pattern, _pcre2.UTF, context)
```

- `max_pattern_length`, `max_pattern_compiled_length`, `parens_nest_limit`, and `max_varlookbehind` bound a pattern
  and what it compiles to. Exceeding one is a `CompileError`: `ERROR_PATTERN_STRING_TOO_LONG`,
  `ERROR_PATTERN_COMPILED_SIZE_TOO_BIG`, `ERROR_PARENTHESES_NEST_TOO_DEEP`, `ERROR_MAX_VAR_LOOKBEHIND_EXCEEDED`.
  Anything compiling patterns it does not control should set them, as it should match under a `MatchContext`.
- `newline` and `bsr` are what a newline is, and what `\R` matches: a `NEWLINE_*` and a `BSR_*`.
- `extra_options` is the second word of compile options, the `EXTRA_*` ones.
- `optimize` is one `pcre2_set_optimize` directive, or a sequence of them to apply in order: `OPTIMIZATION_NONE`,
  `OPTIMIZATION_FULL`, and `AUTO_POSSESS`, `DOTSTAR_ANCHOR`, and `START_OPTIMIZE` with their `_OFF`s.
- Like a `MatchContext`, it is given its settings when created rather than through setters, so that it is immutable and
  can be shared between threads. A setting left as `None` keeps PCRE2's default.

## Threads

Both the default and the free-threaded build are supported, and the module declares that it needs no GIL.

- A `Code`, a `CompileContext`, and a `MatchContext` are immutable, and can be used from any number of threads at
  once. A `MatchData` cannot: using one while it is already in use raises `RuntimeError` rather than corrupting it, so
  give each thread its own. That holds for use from within, too: a subject's buffer is released by calling its exporter
  back, and an exporter written in Python which uses the block from there is refused the same way - whether the block
  is letting go of the buffer to match something else, or being emptied by the collector.
- No match holds the interpreter for long. One with 512 bytes or more of subject ahead of it runs detached from the
  start. A shorter one is first tried attached, under a match limit of 256, which ordinary matches finish well within,
  and only if that runs out is it run again, detached, under its real limit. Compiling a pattern of 512 bytes or more
  is detached as well. Detached means that under the GIL other threads run, and that free-threaded a collection in
  another thread is not held up waiting for the match. An attached match ordinarily takes microseconds, and the worst
  pattern found for one - built for the purpose - took under 20 milliseconds.
- PCRE2 validates a UTF subject and from then on trusts it, reading whole characters without checking them against the
  end of the subject. A subject which another thread changes during a match is therefore an out of bounds read, not
  just a wrong answer, and neither the GIL - a match may be detached - nor a read-only buffer - it may be a view of
  memory something else writes to - rules that out. Hence the rule above that a UTF pattern only matches `bytes`.

## Limits

A `MatchContext` carries the limits a match runs under, and is passed to `Code.match`:

```python
context = _pcre2.MatchContext.create(match_limit=100_000, heap_limit=64 * 1024)
code.match(subject, md, match_context=context)
```

- `match_limit` bounds the backtracking a match may do from any one position, `depth_limit` how deeply it may nest, and
  `heap_limit` the memory it may hold while doing so - in kibibytes. Exceeding one raises `MatchError` with
  `ERROR_MATCHLIMIT`, `ERROR_DEPTHLIMIT`, or `ERROR_HEAPLIMIT`.
- `offset_limit` is the furthest offset a match may start at, and is only honored for patterns compiled with
  `USE_OFFSET_LIMIT` - without it the match fails with `ERROR_BADOFFSETLIMIT`.
- A limit left as `None` keeps PCRE2's default, which `config` reports: `CONFIG_MATCHLIMIT`, `CONFIG_DEPTHLIMIT`,
  `CONFIG_HEAPLIMIT`. A pattern can lower a limit for itself, with `(*LIMIT_MATCH=n)` and the like, but not raise it.
- The limits are given when the context is created, rather than through setters as in C, so that it is immutable and
  one context can be shared by every thread matching under the same policy.

The defaults bound a match, but loosely: the match limit is ten million unless PCRE2 was built otherwise, which the
pattern in `tests/test_limits.py` takes a noticeable fraction of a second to exhaust on every call. Anything matching
patterns or subjects it does not control should pass a context.

PCRE2 counts the match limit afresh at each position it tries a pattern from, so what it bounds is the work done at
any one position, and the time an unanchored search can take still grows with the length of the subject. Bounding that
too takes a bound on the subject passed, or an `offset_limit`.

## Using it from another extension

`_pcre2.capi` is a capsule holding a table of function pointers into this module's copy of PCRE2, so that another
extension can drive it without linking a second copy. The table is `Pcre2Capi`, declared near the bottom of `_pcre2.c`.
Besides `code_from_object`, `match_context_from_object`, and `compile_context_from_object`, which unwrap the objects
they are named for, every entry is the PCRE2 function of the same name, touches no Python state, and may be called from
any thread with or without a thread state attached. Everything the module binds is in it.

A consumer includes `pcre2.h` for the types alone, declares the struct verbatim, and at import does:

```c++
// PyCapsule_Import alone only finds a submodule which something has already imported.
PyObject *pcre2_module = PyImport_ImportModule(PCRE2_CAPI_MODULE_NAME);
if (pcre2_module == nullptr) {
    return -1;
}
const Pcre2Capi *capi = (const Pcre2Capi *)PyCapsule_Import(PCRE2_CAPI_CAPSULE_NAME, 0);
Py_DECREF(pcre2_module);
if (capi == nullptr) {
    return -1;
}
if (capi->abi_version != PCRE2_CAPI_ABI_VERSION || capi->struct_size < sizeof(Pcre2Capi)) {
    // raise ImportError
}
```

It then holds a reference to the `Code`, and to any `MatchContext`, for as long as it uses what it unwrapped from them,
and gives each of its threads a match data block of its own. A context it creates itself, through the table, is its own
to set limits on and free.

The table is PCRE2 as it comes, so what `Code.match` adds around it is the consumer's to do for itself:

- Only match UTF patterns against memory which cannot change while it does - `bytes`, or the UTF-8 of a `str`.
- In a global search pass `PCRE2_NO_UTF_CHECK` on every call after the first successful one, as PCRE2 documents, or the
  search is quadratic in the length of the subject. That is sound for a pattern compiled with `UTF` and without
  `MATCH_INVALID_UTF`, over a subject which cannot change.

`tests/_capiclient.cc` is a complete example which does both, and is shaped like the ingest stage of a BPE trainer: it
splits texts into regex chunks and counts them across threads, under a caller's limits. It is test code, and so is not
built with the package: the `capiclient` fixture in `tests/conftest.py` compiles it into a temporary directory the
first time a test asks for it, and loads it from there.

Entries are only ever appended to `Pcre2Capi` under a given `PCRE2_CAPI_ABI_VERSION`, so a consumer built against an
earlier, shorter table keeps working, and one built against a later table than the module has is refused at import. Any
other change must bump the version.

## The `re` adapter

The `re` subpackage is a best effort at the standard library's `re` on top of the binding, in pure Python: the same
functions, the same flags, and `Pattern` and `Match` objects with the attributes and methods of the originals.

```python
from omcore.text.pcre2 import re as pre

pre.sub(r'(\w+)@(\w+)', r'\2 at \1', 'bob@example')  # 'example at bob'
```

The flags are the standard library's own objects, and so is the exception raised for a bad pattern, `re.PatternError`,
so code written against `re` can be pointed at this without changing either. What it does to get there:

- Patterns are rewritten where the two dialects part, in `re/translating.py`: `\Z` becomes `\z`, `\v` a vertical tab,
  `\uXXXX`, `\UXXXXXXXX`, and `\N{NAME}` plain code points, a `[` inside a class is escaped so that it does not open a
  POSIX class, and the `u` flag letter is dropped. For a str pattern not under `ASCII`, `\w`, `\s`, and `\b` are
  written out as what `re` means by them, which is not quite what PCRE2 does - checked against `re` over every code
  point, they then differ only where PCRE2's Unicode data, version 17, is newer than Python's.
- It compiles with `EXTRA_PYTHON_OCTAL`, with a linefeed as the only newline, and with `ALT_CIRCUMFLEX`, and maps
  `IGNORECASE`, `MULTILINE`, `DOTALL`, and `VERBOSE` to PCRE2's options. A str pattern is compiled with `UTF`, and with
  `UCP` unless `ASCII` is given. A bytes pattern is compiled with neither.
- A str subject is matched as its UTF-8, encoded once per call. Groups are sliced out of that and decoded, and offsets
  are only translated into characters when a `Match` is asked for one, each counted from the nearest already known.
- `finditer`, `findall`, `split`, and `sub` are all the `match` / `next_match` loop, which finds the same matches as
  `re`'s, empty ones included. Replacement templates are parsed in `re/templates.py`, to `re`'s rules and with its
  error messages - PCRE2's own substitution is not used, as its templates are another language.
- `Match.lastindex` is not something PCRE2 reports. It is worked out from what it does report and from where each
  group closes in the pattern.
- `Pattern` takes one keyword `re.compile` does not, `match_context`, so that a pattern can carry limits.

It is tested against `re` itself: `re/tests/test_stdlib.py` runs both over a grid of patterns and subjects, through
every operation, and requires the same answers. Where they are known to differ is pinned in
`re/tests/test_divergences.py`:

- Under `ASCII` with `IGNORECASE`, `re` folds the case of ASCII letters only, and PCRE2 folds all of them.
- `\W` and `\S` inside a character class keep PCRE2's meaning, as a negated class cannot be written out as members of
  another. That differs for combining marks and connector punctuation, which are word characters to PCRE2, and for a
  handful of control characters.
- A repeat of something which can match nothing - `(a?)*`, say - is handled by each engine's own rules, which can leave
  different text in its groups and, more rarely, find different matches. Of 12,000 randomly generated patterns this
  was the only disagreement found, in 51 of them.
- A match which backtracks past PCRE2's match limit raises the binding's `MatchError`, where `re` would have carried
  on. `LOCALE` is not supported, `DEBUG` is ignored, and a str holding a lone surrogate cannot be encoded to be matched.
- Error messages are PCRE2's, and where a pattern was rewritten the position of an error in it is not reported.
- PCRE2's syntax is a superset of `re`'s, and none of the rest of it is refused: `\p{L}`, `\h`, `\K`, recursion, and
  lookbehinds of varying length all work, where `re` would raise.

It is also slower per match than `re`, whose loops are in C where these are in Python. A `findall` of every word in a
text took around five times as long, and of a literal over ten, while one with more to do per match took under three
times as long, and one of a case-insensitive alternation the same. PCRE2 only earns its overhead back where the
matching itself dominates.

## Known divergence from Rust's `regex`

PCRE2's `\s` still matches U+180E MONGOLIAN VOWEL SEPARATOR, which left `White_Space` in Unicode 6.3, and Rust's does
not. With the GPT-4 pre-tokenization pattern this is the only difference from rustbpe found by differential fuzzing, and
it is pinned in `tests/test_gpt4.py`.
