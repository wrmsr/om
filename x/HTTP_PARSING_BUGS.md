# HTTP Parsing Bugs - Priority Shortlist

Static analysis findings for `omcore/http/parsing.py` (and `omcore/http/tests/test_parsing.py`), prioritized. The
default-config posture is otherwise solid: CL/TE conflicts, duplicate Content-Length/Host, obs-fold, and
space-before-colon handling are all correctly strict and well-tested. The items below are edge conformance bugs,
default-posture questions, and missing configuration axes for the stated diagnostics use case.

## 1. `Accept: */html` is wrongly accepted (spec violation)

In `_prepare_accept`, media-range validation loops over `(type_, subtype)` and `continue`s whenever a half equals
`'*'`:

```python
for part in (type_, subtype):
    if part == '*':
        continue
    if not self._is_token(part) or '*' in part:
        raise ...
```

Per RFC 9110 §12.5.1, `media-range = "*/*" / ( type "/*" ) / ( type "/" subtype )` - `'*'` as the *type* is only
legal when the subtype is also `'*'`. The current check accepts `Accept: */html` and stores `media_range='*/html'`,
which is not a valid media-range. The test suite has no coverage of `*/html` (`test_accept_partial_wildcard_rejected`
covers `*text/*`, `te*xt/html`, `text/ht*ml`, but not a bare `*` type with a concrete subtype).

Fix: when `type_ == '*'`, require `subtype == '*'` (and vice versa for symmetry, though `text/*` is already handled
by the existing branch).

## 2. obs-text bytes are accepted and preserved in `Host` by default

RFC 9110 §7.2 / RFC 9112 §5.4: `Host = uri-host [ ":" port ]`, where `uri-host` is registered-name / IP-literal /
IPv4address - all ASCII subsets. obs-text (`0x80-0xFF`) is never legal in a Host value under any reading.

`_prepare_host` rejects only `0x00-0x20` (plus explicit SP/HTAB), so `Host: example.com\xa0` parses and is stored
verbatim - and the test `test_host_obs_text_preserved_not_stripped` explicitly *enshrines* this behavior, with a
comment arguing it agrees with "a byte-oriented peer". The opposite is true of the conformant peer set: strict
upstreams reject obs-text in Host, so accepting it is a forward differential in the default (supposedly safe)
configuration. There is also no config knob to reject it - unlike field values generally, where `reject_obs_text`
exists.

Recommendation: reject obs-text in Host by default (reuse `INVALID_HOST`), and add an `allow_obs_text_host` (or
similar) knob if the diagnostics use case wants the old behavior.

## 3. Status codes 600-999 are unreceivable, even with knobs

`parse_status_line` hard-rejects any status code outside `100 <= code <= 599`:

```python
status_code = int(status_bytes)
if not (100 <= status_code <= 599):
    raise StartLineHttpParseError(... INVALID_STATUS_CODE ...)
```

RFC 9110 §15: status codes are extensible; "a client MUST understand the class of any status code, as indicated by
the first digit, and treat an unrecognized response as being equivalent to the x00 status code of that class."
Codes 600-999 are unassigned but syntactically valid 3-digit codes. For a server-side parser, strict rejection is
defensible; but this parser is also used by the in-house HTTP *client* (via `omcore/http/pipelines/decoders.py`), so
any current or future 6xx+ response from a peer cannot be parsed even in a lenient configuration. Test
`test_status_code_600` pins the strict behavior.

Recommendation: add an `allow_extended_status_codes` config knob (accept any 3-digit code), or accept 100-999 by
default and validate only the first digit.

## 4. `_parse_comma_list` leaks quote state on unterminated quoted-strings

When a backslash is the last byte of the entire header value, the `in_quotes` branch's `i + 1 < n` guard fails and
falls through to `buf.append(ch); i += 1`, treating the trailing backslash as a literal character and leaving
`in_quotes=True`. The loop then ends with quote state still active - an unterminated quoted-string is *silently
accepted* by the splitter, and any commas after the opening quote are treated as quoted (not as separators).

All current consumers happen to be safe because the malformed element (`'"a'` etc.) subsequently fails token/quoted
-string validation in `_prepare_connection`, `_prepare_trailer`, `_prepare_transfer_encoding`, etc. (covered by
`test_trailing_backslash_does_not_crash`), so this is a latent utility bug rather than a live hole - but any future
caller of `_parse_comma_list` that does not re-validate quoted-strings will inherit the differential.

Recommendation: raise `ValueError` from `_parse_comma_list` when the input ends inside a quoted-string (or with a
dangling escape), so quote-state errors surface at the split site.

## 5. IMF-fixdate and RFC 850 dates accept wrong-width weekday names

`_parse_http_date` cross-checks the weekday using only its first three characters in both comma-bearing formats:

```python
cls._check_http_date_weekday(dt, weekday_str[:3])
```

Consequences:

- IMF-fixdate (`day-name "," ...` where day-name is exactly the 3-letter abbreviation per RFC 9110 §10.1.1) accepts
  `Sunday, 06 Nov 1994 08:49:37 GMT` - the full RFC 850 weekday name in the IMF format. (The RFC 850 branch
  *deliberately* accepts both full names and abbreviations, which is documented leniency; the IMF branch doing the
  same is not.)
- Any weekday *prefix* passes: `'Sundays, 06-Nov-94 ...'` or `'Sundark, 06-Nov-94 ...'` both reduce to `'sun'` and
  validate.

Pedantically nonconformant; practically low-risk since the date itself must still be internally consistent with the
weekday. Recommendation: require exactly 3 chars for the IMF day-name; keep (or tighten) the documented leniency in
the RFC 850 branch.

## 6. Duplicate `Date` / `Expect` headers are handled inconsistently with other singletons

Singleton-header duplicate policy varies across prepared headers:

- `Content-Type`: dedicated `MULTIPLE_CONTENT_TYPES` + `allow_multiple_content_types` knob; conflicting values get
  `CONFLICTING_CONTENT_TYPES`.
- `Authorization`: dedicated `MULTIPLE_AUTHORIZATION_HEADERS` (no knob).
- `Content-Length`: `DUPLICATE_CONTENT_LENGTH` + `allow_multiple_content_lengths` + identical-value tolerance.
- `Host`: `MULTIPLE_HOST_HEADERS` + `allow_multiple_hosts`.
- **`Date` / `Expect`: no duplicate detection at all.** They use `headers['date']` / `headers['expect']`, which
  comma-joins duplicates into a value that then fails generic validation (`INVALID_DATE` / `INVALID_EXPECT`) with a
  confusing message, rather than surfacing the actual problem (a duplicate singleton header).

Recommendation: detect duplicates explicitly in `_prepare_date` and `_prepare_expect` and raise dedicated error codes
(e.g. `MULTIPLE_DATE_HEADERS` / `MULTIPLE_EXPECT_HEADERS`), optionally with `allow_multiple_*` knobs for consistency
with Content-Type/Host/Content-Length.

## 7. No `max_start_line_length` - the start-line has no length cap

`max_header_length` applies only to header lines; the request/status line is unbounded. `find_line_end` scans it at
C speed, so the cost is linear, but the parsed start line is stored, decoded, and regex-matched without any size
limit. In practice the pipeline decoder's head buffer (4 KiB default in `IoPipelineHttpDecodingConfig`) caps this,
but the parser itself is also a public API used directly, per its module docstring, and a Config knob is cheap.

Recommendation: add `max_start_line_length: ta.Optional[int]` (suggest default 8192 to match `max_header_length`)
and check the start-line slice in `parse_message`.

## 8. Missing leniency knobs for the diagnostics / adversarial-analysis use case

Three behaviors are unconditionally strict with no opt-out, which limits the parser's usefulness off the serving
path:

- **`allow_missing_reason_phrase_sp`**: `parse_status_line` requires the SP before the reason-phrase even when the
  phrase is empty (`HTTP/1.1 200\r\n` is rejected with `MALFORMED_STATUS_LINE`). The grammar does mandate the SP, but
  the form without it is widely seen in the wild. Test `test_status_line_missing_second_sp` pins the strict behavior;
  a knob would treat it as `reason_phrase=''`.
- **`allow_te_without_chunked_in_request`**: `_prepare_transfer_encoding` unconditionally rejects a Transfer-Encoding
  without a final `chunked` in a request (`TE_WITHOUT_CHUNKED_LAST`). Rejection is correct server-side (RFC 9112 §6.1
  mandates 400), and a knob exists for responses (`allow_te_without_chunked_in_response`) - but not for requests, an
  asymmetry that blocks diagnostics parsing of such requests.
- **`accept-ext` parameters after `q` in `Accept`**: RFC 9110 §12.5.1 defines
  `accept-params = weight *( ";" accept-ext )` - extension parameters *after* the qvalue are legal in `Accept`
  specifically. `_split_header_element` rejects them outright ("q must be the last parameter", citing §12.4.2), which
  is correct for TE and Accept-Encoding (no such ext grammar) but over-strict for `Accept`. Either allow accept-ext
  in `_prepare_accept` or add a knob.

## 9. `reject_obs_text` does not apply to the request-target

With `reject_obs_text=True`, obs-text is rejected in field values and the reason-phrase, but the request-target still
accepts `0x80-0xFF` unless `reject_non_visible_ascii_request_target` is *also* set. Two knobs where a user would
reasonably expect `reject_obs_text` to mean "no obs-text anywhere in the head."

Related default-posture question: by default the request-target accepts raw `0x80-0xFF` bytes
(`_REQUEST_TARGET_BYTES = VCHAR | obs-text`), which is more lenient than the RFCs (request-target is a URI - ASCII).
Raw UTF-8 targets are ubiquitous in practice so default rejection would break real clients, but note the
strict-safe direction is currently opt-in (`reject_non_visible_ascii_request_target`) rather than the default.
Worth an explicit decision either way; at minimum, document the coupling (or make `reject_obs_text` imply it).

---

# Remaining Actionable Suggestions

Lower-priority items that are still worth acting on, roughly ordered.

## Correctness / consistency

1. **`WWW-Authenticate` / `Proxy-Authenticate` are comma-combined on access, but are not safely combinable.**
   `_NO_COMBINE_HEADERS` contains only `set-cookie`. Per RFC 9110 §11.6.1/§11.7.1, an auth challenge may itself
   contain commas, and combining multiple challenges with `", "` (as `__getitem__` / `get` / `items()` do for
   non-exempt headers) produces an ambiguous value that is commonly mishandled downstream. Consider adding
   `www-authenticate` and `proxy-authenticate` to the no-combine set, or making the set configurable.

2. **`TE` qvalues are validated and then silently discarded.** `_prepare_te` fully parses and validates qvalues (and
   correctly rejects `trailers;q=0`), but `prepared.te` is a plain `List[str]` - `TE: trailers;q=0.5, gzip;q=0.9`
   becomes `['trailers', 'gzip']`. TE qvalues are near-meaningless in practice, so this may be intended, but the
   parser went to the trouble of validating data it then drops. Consider an `AcceptEncodingItem`-style
   `(coding, q)` pair list, or document the discard.

3. **`Authorization` in a response is not flagged.** The parser rejects request-only headers in responses (`Host` →
   `HOST_IN_RESPONSE`, `TE` → `TE_IN_RESPONSE`, `Expect` → `EXPECT_IN_RESPONSE`) but Authorization - also a
   request-scoped field (RFC 9110 §11.6.2) - is parsed and stored without complaint in responses. Harmless in
   practice; add for symmetry if desired (low value).

4. **Leftover thinking-aloud comment in `parse_request_line`.** The block above the `line.count(b' ') != 2` check
   ("Actually the HTTP spec says request-target can contain spaces? No - it's defined as *visible ASCII*. But to find
   the correct split... Let's be strict") is leftover reasoning, not a durable comment. Replace with a one-liner
   stating the invariant (exactly 2 SPs: method/target/version are all SP-free by grammar).

5. **asctime parsing does not validate its fixed separator positions.** `_parse_http_date`'s asctime branch slices
   fixed columns (`value[4:7]`, `value[8:10]`, `value[11:19]`, `value[20:24]`) but never checks that positions 3, 7,
   10, 19 are the expected SP characters. The shape is over-constrained enough that garbage can't produce a
   *different valid* parse (any misplaced char shifts a digit slice into non-digits and fails), so this is
   fragility rather than a live bug - but an explicit separator check (or a comment noting why it's safe) would
   remove the need to re-derive that argument. Also, `day_str = value[8:10].replace(' ', '0')` would turn a
   hypothetical trailing-space day (`'6 '`) into `'60'`; only the leading-space form (`' 6'`) is legitimate -
   consider handling the two cases explicitly.

## Performance (peephole, clarity-preserving)

6. **Allocation-free field-value validation.** `_parse_one_header` validates every value with
   `value_stripped.translate(None, allowed_bytes)`, which allocates a result bytes object even when the value is
   valid. Precompiling one bytes-regex per `(allow_bare_cr_in_value, reject_obs_text)` variant (the same 4-way table,
   mirroring `_RE_REASON_PHRASE`) and using `.match()` scans at C speed with no allocation on the happy path.

7. **Fast path in `_parse_comma_list`.** The overwhelmingly common case contains no quotes. Guard with
   `if '"' not in value:` and use a simple `str.split(',')` + strip + drop-empty comprehension, keeping the
   quote-aware loop as the fallback. Benefits `Connection`, `TE`, `Trailer`, `Transfer-Encoding`, `Cache-Control`,
   `Accept*` - every list-valued header.

8. **Skip the split in `_prepare_content_length` for the common single value.** `v.split(',')` allocates for every
   value; guard with `if ',' in v:`.

9. **Simplify redundant conditions in `find_line_end`.** `if first == nul_at and nul_at <= cr_at and nul_at <= lf_at:`
   - the trailing comparisons are implied by the bounded NUL find (`nul_at` is searched within
   `[pos, min(cr_at, lf_at))`); `if first == nul_at:` suffices. Same for the CR branch's `cr_at <= lf_at`. Pure
   clarity change.

10. **Reason-phrase bad-byte offset via regex.** `parse_status_line`'s error path re-scans `reason_bytes` byte-by-byte
    using the `_REASON_PHRASE_CHARS` frozenset to locate the offending byte. A precompiled complement regex
    (`re.compile(rb'[^\x09\x20\x21-\x7e\x80-\xff]').search(...)`) yields the offset directly and replaces the set +
    loop. (Error path only - zero happy-path impact either way.)

11. **`^` → `\A` pedantry in `_RE_REASON_PHRASE` / `_RE_TOKEN`.** Both use `^...\Z`; without `re.MULTILINE` they are
    equivalent, but `\A` states the intent precisely and is immune to a future flag change.

## API / docs

12. **Document the empty-trailers special case in `parse_trailers`.** `data == b'\r\n'` (or `b'\n'` under
    `allow_bare_lf`) short-circuits before `verify_terminator`; the general path would handle it identically
    (`parse_header_fields` hits the empty line at pos 0 and breaks). It's a correct fast path, but a one-line comment
    saying "pure fast path - the general path below handles this identically" would stop readers from auditing
    whether the two paths can diverge.
