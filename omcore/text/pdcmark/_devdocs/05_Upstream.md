# Upstream review, 2026-11-12

## Revision range and method

The Python translation entered this repository in `3ec91e57c` on 2026-05-26. Its original upstream checkout/pin was
not imported. All 14 vendored `specs/*.txt` files are byte-identical to upstream
[`b93cbc0`](https://github.com/pulldown-cmark/pulldown-cmark/commit/b93cbc043fe8a24b5ee3868b21299e320e0f7d41)
(2026-05-22). This establishes a reproducible **inferred fixture baseline**, rather than proving the exact source
revision used by the translator. The May 25 upstream reference-link/title fixes are absent from those fixtures.

Reviewed the reachable git history and source/test differences from that baseline through
[`1c1a312`](https://github.com/pulldown-cmark/pulldown-cmark/commit/1c1a3123207d9e07fdfcf3d3418a047907185afb)
(2026-11-08): 190 commits, including 49 first-parent commits and 133 non-merge commits. This includes changes authored
earlier but merged after the baseline. Read parser/scanner/renderer patches and their regression examples, then
checked the supported examples against the current Python implementation, including its later hardening work.

No Rust orchestration, byte-offset arithmetic, or representation-specific optimization was transplanted. Python
continues to use character offsets, frozen event records, the line-driven block machine, direct construction of hot
path records, and an LF-only scanning fast path. The original vendored fixtures remain unchanged.

## Implemented

| Upstream change | Python adaptation |
|---|---|
| [NUL replacement, #1087](https://github.com/pulldown-cmark/pulldown-cmark/pull/1087) (`21ea5ac`, `627755d`, `622420a`) | Replace U+0000 with U+FFFD before block scanning. This covers text, code, HTML, fence info, destinations, titles, and reference-definition/lookup labels. Replacement is one character for one character, preserving Python offsets. |
| [Leading BOM, #1157](https://github.com/pulldown-cmark/pulldown-cmark/pull/1157) (`a9ad8c7`, `c966c9c`) | Skip U+FEFF only at absolute input position zero, advancing the source start by one character. Later BOMs remain content; streaming and prescan use the same normalization. |
| [Title separation, #1100](https://github.com/pulldown-cmark/pulldown-cmark/pull/1100) (`6aa902d`) | Require whitespace between an inline link destination and its title. Reference-definition parsing already enforced this, but inline parsing did not. |
| [Task-list block interpretation, #1135](https://github.com/pulldown-cmark/pulldown-cmark/pull/1135) (`bbc52a0`, `52e0e30`) | Keep the raw marker in an open paragraph and delay the checkbox event until paragraph close. Setext promotion restores ordinary inline parsing of `[x]`; loose-list checkboxes belong inside their paragraph. The raw marker also prevents incorrect table promotion. No committed checkbox needs retraction. |
| [Code-span indentation, #1159](https://github.com/pulldown-cmark/pulldown-cmark/pull/1159) (`87a6fce`) | Strip spaces/tabs following a continuation newline inside code spans, preserving spaces before the newline and the complete original source span. Raw HTML retains its whitespace. Updated the old Python test that encoded the previous behavior. |
| [Underscore search bounds, #1155](https://github.com/pulldown-cmark/pulldown-cmark/pull/1155) (`2391215`) | Add failed-opener bounds keyed by delimiter, flanking state, and original run length modulo three. Bounds use source positions so list splicing cannot invalidate them. The `*a_` flood no longer repeatedly searches every prior opener. |
| [Quote continuation, #1172](https://github.com/pulldown-cmark/pulldown-cmark/pull/1172) (`365429b`) | Reject four columns of indentation before a quote continuation/new container, including tabs and tab carry. An indented `>` remains paragraph/code content where required. |
| [HTML indentation, #1180](https://github.com/pulldown-cmark/pulldown-cmark/pull/1180) (`d5c99bf`) | Reuse the original `LineStart` cursor for indentation decisions and stripping, rather than restarting tab stops after container prefixes. Preserve whole tabs before HTML; materialize only the leftover portion of a split tab. |
| [HTML block endings, #1163](https://github.com/pulldown-cmark/pulldown-cmark/pull/1163) | Case-insensitive matching against any of the four type-1 tags already worked. Tightened the Python matcher to require the complete literal end tag and ASCII case folding, and combined its four searches into one regex. Incomplete `</pre`/`</pre x>` and Unicode lookalikes no longer close the block. |
| [CR recognition, #1091](https://github.com/pulldown-cmark/pulldown-cmark/pull/1091), [EOL normalization, #1116](https://github.com/pulldown-cmark/pulldown-cmark/pull/1116) | Oneshot already normalized CR/CRLF and synthesized final newlines. Streaming incorrectly preferred a later LF over an earlier bare CR and treated a terminal CR as content. Fixed first-ending selection, terminal-CR finalization, and tentative output, retaining the LF fast path. |

The code-span change intentionally changes the old Python result for `` `a\n   b` `` from `a    b` to `a b`.
Upstream made the same correction, checked it against cmark/commonmark.js, and updated its previous expectations.
Trailing spaces before the newline remain significant.

## Already satisfied; regression coverage added

These changes did not need their Rust implementation ported:

- [Escaped reference suffixes, #1094](https://github.com/pulldown-cmark/pulldown-cmark/pull/1094): Python scans raw source
  after `]`, rather than looking at the next transformed tree node. The new examples pass with oneshot prescan.
- [Collapsed-reference spans, #1138](https://github.com/pulldown-cmark/pulldown-cmark/pull/1138): `consumed_end` already
  includes the final `[]`; added an exact-offset regression.
- [Closing-fence tabs, #1150](https://github.com/pulldown-cmark/pulldown-cmark/pull/1150): already accepted spaces/tabs.
- [EOF container ranges, #1168](https://github.com/pulldown-cmark/pulldown-cmark/pull/1168): Python closes at the supplied
  final offset, without the Rust fence parser's overrun arithmetic.
- [Whitespace-only final fenced/HTML lines, #1164](https://github.com/pulldown-cmark/pulldown-cmark/pull/1164): already
  buffered as real lines, including lines emptied by container-prefix removal. Added unterminated-input tests.
- [Multiline inline HTML prefixes, #1165](https://github.com/pulldown-cmark/pulldown-cmark/pull/1165): container prefixes
  are removed before inline parsing, so declarations cannot accidentally close at a quote marker.
- [Info-string tabs, #1173](https://github.com/pulldown-cmark/pulldown-cmark/pull/1173): the renderer already splits the
  language at whitespace.
- [Inline HTML scanning, #1169](https://github.com/pulldown-cmark/pulldown-cmark/pull/1169): Python already finds the first
  complete CDATA terminator, excludes tabs from unquoted attribute values, and accepts continuation whitespace before
  a closing tag's `>`.
- [Escaped multiline title delimiters, #1167](https://github.com/pulldown-cmark/pulldown-cmark/pull/1167): the title scanner
  sees raw backslashes, so it does not need Rust's transformed-node escape flag repair.
- [Hard breaks, #1170](https://github.com/pulldown-cmark/pulldown-cmark/pull/1170): two actual trailing spaces were already
  required, and a backslash break inside link text already survived the emphasis pass.
- [Container-fence interruption gating, #1144](https://github.com/pulldown-cmark/pulldown-cmark/pull/1144): with that
  extension absent, Python already keeps `::: note` as paragraph text.
- [Tab-indented list spans, #1151](https://github.com/pulldown-cmark/pulldown-cmark/pull/1151): Python already uses cursor
  character positions instead of subtracting column counts from source indices. Added all four ordinary-list examples.

## Changes requiring a scope/design decision

- **CJK-friendly emphasis** ([#1059](https://github.com/pulldown-cmark/pulldown-cmark/pull/1059)): a new opt-in grammar,
  including Unicode ranges, ideographic variation selectors, and different punctuation/flanking rules. Streaming is
  compatible, but adding it requires a public option and agreeing on Unicode data maintenance. Left default semantics
  unchanged.
- **`==highlight==`** ([`c8960aa`](https://github.com/pulldown-cmark/pulldown-cmark/commit/c8960aa)): new syntax, option,
  event/tag, and HTML `<mark>` rendering. It fits this architecture, but extends the supported feature surface rather
  than correcting an existing feature. Left for explicit adoption.
- **HTML failed-scan caching** (`7217dca`): Rust adjusts its existing `HtmlScanGuard` to avoid repeat failed comment/CDATA
  searches. Python's stateless scanner has no corresponding guard. The correctness examples already pass; a per-block
  caching design would be a separate optimization. This review does not establish linear time for all malformed HTML.
- **Forward references**: retained the existing tradeoff. Full HTML comparisons use `prescan_refdefs=True`; streaming
  tests use normal backward-only lookup. No future definition retroactively alters committed events.
- **Table dialect choices**: retained Python's documented cmark-gfm choices for multiline headers without a leading
  pipe and the list-marker priority of `- | -`. Upstream fixture-option corrections do not override these choices.
- **Remaining adversarial work**: the delimiter bounds fix addresses failed searches, not every cost of Python list
  splicing. Deep bracket floods and successful nested delimiter wrapping are still candidates for a separate IR redesign.

## Other changes that do not apply directly

- Wikilink termination/empty-label/sibling-chain/underflow repairs (#1102, #1111), and nested image-wikilink quadratic
  parsing (#1186): this parser does not implement wikilinks or Rust's sibling-linked tree.
- Footnote interrupt-probe quadratic parsing (#1136) and footnotes inside link labels (#1153): footnotes are still an
  explicit non-goal; the corresponding syntax and tree/link-stack interactions are absent.
- Definition-list UTF-8 boundaries (#1143), container-fence trailing backslashes (#1146), and heading-attribute/setext
  repairs (#1183): those extensions are absent. Ordinary lists/setext headings were checked separately above.
- Subscript/strikethrough interaction (#1121): repairs branches conditional on subscript/superscript options that Python
  does not have. Existing strikethrough remains covered by its own tests and the GFM fixtures.
- Consecutive blank-line container-scan optimization (#1148): Rust can traverse arbitrarily deep list trees; Python
  bounds the container stack at 32 entries by default. Its scan is already bounded per line. Porting Rust's mutable
  list flags would add state without addressing the same unbounded-depth problem here.
- Borrowed/owned strings, lifetime repairs (#1092), redundant clone removal, deprecated Rust APIs, memchr/SIMD search
  mechanics: different representation/language. Kept Python's string/regex operations and existing hot-path choices.
- Spec option metadata/line-number generation (#1122): applies to Rust's generated test infrastructure. Selected new
  fixtures preserve explicit supported flags; unsupported extensions are not silently enabled. Full corpus migration
  was unnecessary for this review. The one compact closing-tag formatting difference is noted in the copied fixture.
- Cargo/dependency updates, demo/WASM/book work, fuzz harness wiring, generated Rust tests, wording changes, security
  policy, contribution policy, and issue/PR templates do not change this library's runtime behavior.

## Validation

- Existing baseline before edits: 477 passing pytests.
- Added 74 supported upstream regression fixtures; assertions cover expected HTML, default-mode streaming at chunk
  sizes 1/3/17, every intermediate committed-plus-tentative prefix, and final source-offset bounds.
- Added standalone EOF, mixed CR/CRLF, BOM, NUL, task commitment, exact offset, and HTML-terminator tests. Each short
  EOF fixture is streamed at every possible two-chunk split.
- The underscore regression counts node reads with a real instrumented list, avoiding timing thresholds or sleeps.
- A deterministic 10,000-input comparison checked the new delimiter resolver against the previous implementation.
- `make fix gen check` passed, including mypy over 5,225 source files. Code generation updated the cached dataclass
  implementation after adding the pending task marker to `OpenParagraph`.
- Final pytest run: **587 passed** (523 pdcmark tests plus 64 minitui markdown consumer tests), using
  `./python -m pytest -q omcore/text/pdcmark omdev/minitui/text/markdown/tests` after generation.
