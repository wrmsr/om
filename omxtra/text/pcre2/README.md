# pcre2

`_pcre2` is a direct binding of the 8-bit [PCRE2](https://github.com/PCRE2Project/pcre2) library. It is deliberately not
`re`: it exposes PCRE2's own functions, option bits, return codes, and offsets, and leaves everything `re`-shaped to
Python code layered on top.

It needs PCRE2 10.47 or newer (for `pcre2_next_match`), built for 8-bit code units with Unicode support, linked
statically with hidden visibility. The JIT is not used.

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
| `compile(pattern, options=0, *, extra_options=0)`      | `pcre2_compile`, `pcre2_set_compile_extra_options`       |
| `Code.match(subject, match_data, start_offset=0, options=0, match_context=None)` | `pcre2_match`                  |
| `Code.pattern_info(what)`                              | `pcre2_pattern_info`                                     |
| `MatchData.create(ovecsize)`                           | `pcre2_match_data_create`                                |
| `MatchData.create_from_pattern(code)`                  | `pcre2_match_data_create_from_pattern`                   |
| `MatchData.ovector`, `MatchData.ovector_count`         | `pcre2_get_ovector_pointer`, `pcre2_get_ovector_count`   |
| `MatchData.next_match()`                               | `pcre2_next_match`                                       |
| `MatchContext.create(*, match_limit=None, ...)`        | `pcre2_match_context_create`, `pcre2_set_match_limit`, ... |
| `config(what)`                                         | `pcre2_config`                                           |
| `get_error_message(code)`                              | `pcre2_get_error_message`                                |

Constants are PCRE2's with the `PCRE2_` prefix dropped: `UTF`, `CASELESS`, `INFO_CAPTURECOUNT`, `ERROR_NOMATCH`, ...

Things worth knowing:

- Patterns and subjects are bytes-like, never `str`, and every offset is a byte offset. Nothing is implied: a pattern
  holding UTF-8 is only treated as UTF-8 with `UTF`, and `\w`, `\d`, `\s`, and `\b` only see past ASCII with `UCP`.
- `Code.match` returns `pcre2_match`'s return code as is when it is non-negative, `ERROR_NOMATCH`, or `ERROR_PARTIAL`.
  Any other code raises `MatchError`. Errors carry PCRE2's `code`, and an `offset` where PCRE2 reports one: into the
  pattern for a `CompileError`, into the subject for invalid UTF-8.
- An unset offset is `UNSET`, which is -1: `PCRE2_UNSET` read as a signed size. A new `MatchData` reads as all unset.
- After a successful match a `MatchData` holds the subject's buffer, and the `Code`, until it is next matched into -
  `pcre2_next_match` reads through both. A `bytearray` cannot be resized while it is held this way.
- A UTF pattern only matches a subject which cannot change: `bytes`, or a `memoryview` of `bytes`. Anything else raises
  `BufferError` - see [Threads](#threads) for why - unless `NO_UTF_CHECK` is given, which as in C is the caller's own
  promise that the subject is, and stays, valid. Other patterns take any buffer, and see it as it is at each call. A
  writable pattern is compiled from a copy.
- Walking a subject match by match is linear in its length. PCRE2 on its own validates everything ahead of
  `start_offset` on every call, which is quadratic over a search; `Code.match` skips that for a subject the same `Code`
  has already validated through the same `MatchData`, so long as the same `bytes` object keeps being passed.
- Not bound: the JIT, DFA matching, substitution, serialization, callouts, the general context, and the compile and
  match contexts beyond the former's extra options word and the latter's limits. In particular nothing yet bounds
  compilation itself - pattern length, nesting depth, compiled size - beyond PCRE2's built-in defaults.

## Threads

Both the default and the free-threaded build are supported, and the module declares that it needs no GIL.

- A `Code` and a `MatchContext` are immutable, and can be matched with from any number of threads at once. A
  `MatchData` cannot: using one while it is already in use raises `RuntimeError` rather than corrupting it, so give each
  thread its own.
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
Besides `code_from_object` and `match_context_from_object`, which unwrap a `Code` and a `MatchContext`, every entry is
the PCRE2 function of the same name, touches no Python state, and may be called from any thread with or without a
thread state attached.

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
splits texts into regex chunks and counts them across threads, under a caller's limits.

Entries are only ever appended to `Pcre2Capi` under a given `PCRE2_CAPI_ABI_VERSION`, so a consumer built against an
earlier, shorter table keeps working, and one built against a later table than the module has is refused at import. Any
other change must bump the version.

## Building `re` on top

An `re`-compatible adapter is pure Python over what is here:

- Flags map onto options: `IGNORECASE` to `CASELESS`, `VERBOSE` to `EXTENDED`, the absence of `ASCII` to `UCP`,
  `MULTILINE` to `MULTILINE | ALT_CIRCUMFLEX` (without which `^` does not match after a trailing newline, as it does in
  `re`), and `match` / `fullmatch` to `ANCHORED` / `ANCHORED | ENDANCHORED` at match time. `pos` is `start_offset`, and
  `endpos` is a `memoryview` slice of the subject.
- `finditer`, `findall`, `split`, and `sub` are the `match` / `next_match` loop in `tests/spans.py`. On the patterns in
  `tests/test_search.py` it yields the same spans `re.finditer` does, empty matches included.
- `groups` and `groupindex` come from `pattern_info`: `INFO_CAPTURECOUNT`, and `INFO_NAMETABLE` with `INFO_NAMECOUNT`
  and `INFO_NAMEENTRYSIZE` (each entry is a two byte big-endian group number, then the zero-terminated name).
- A `str` subject is encoded to UTF-8 once per call, and that one `bytes` object passed to every `match` of the call,
  which both satisfies the rule for UTF patterns and keeps the search linear. Offsets are then translated incrementally,
  as matches arrive in order: the code points in `subject[a:b]` are `len(subject[a:b].decode())`. For an ASCII subject
  they are the same.

What does not carry over mechanically is where the two languages differ - for example `\Z`, which in PCRE2 also
matches before a trailing newline (`re`'s `\Z` is PCRE2's `\z`), `lastindex`, and the replacement template syntax.

## Known divergence from Rust's `regex`

PCRE2's `\s` still matches U+180E MONGOLIAN VOWEL SEPARATOR, which left `White_Space` in Unicode 6.3, and Rust's does
not. With the GPT-4 pre-tokenization pattern this is the only difference from rustbpe found by differential fuzzing, and
it is pinned in `tests/test_gpt4.py`.
