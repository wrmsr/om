# Status

Snapshot of where the project stands after the initial M1-M7 plan plus the M8 review-hardening pass.

For the original goals and design, see [00_Goals.md](00_Goals.md), [02_PrePlan.md](02_PrePlan.md),
and [03_Plan.md](03_Plan.md).


## Milestones — done

| | Scope | Spec (CM default / prescan) | Tests | Source LOC |
|---|---|---|---|---|
| M0 | Skeleton, events, scanners scaffold, spec runner | n/a | 26 | ~470 |
| M1 | Block parser (CommonMark blocks, no inline) | 196 / — | 225 | ~2,700 |
| M2 | Inline core (emphasis, code, escapes, entities, autolinks, inline HTML, breaks) | 365 / — | 295 | ~3,700 |
| M3 | Links, images, refdefs, broken-link callback, fuel guard | 424 / 468 | 303 | ~4,500 |
| M4 | GFM extensions: tables, strikethrough, tasklists, admonition blockquotes | 429 / 473 | 323 | ~4,950 |
| M5 | Tight / loose list rendering | 459 / 503 | 327 | ~5,030 |
| M6 | StreamingParser + chunking-equivalence guarantee | 459 / 503 | 354 | ~5,200 |
| M7 | README, offset-consistency tests, docs polish | — | 357 | ~5,200 |
| M8 | Review hardening (see below) | 572 / 618 (of 652) | 421 | ~5,300 |
| M9 | List-machine edge semantics | 589 / 635 (of 652) | 445 | ~5,350 |
| M10 | Tabs, refdefs, raw label matching | 603 / 650 (of 652) | 463 | ~5,400 |

M10 fixed: tab-carry columns materialize into indented-code content across container boundaries; blank lines inside
code blocks keep their post-indent whitespace; HTML blocks start on a fresh line inside `<li>`; collapsed / shortcut
labels match on raw source text (escapes unprocessed - `[foo\!]` never matches `[foo!]`); the refdef parser handles
multi-line labels and titles, requires whitespace between destination and title, and peels refdefs before setext
promotion. Under prescan only 2 cases now fail (the `[foo][bar][baz]` bracket-chaining pair, 569/571); the remaining
default-mode delta is the documented forward-reference streaming tradeoff. GFM fixtures pass 14/14.

M9 fixed: tight/loose blank attribution (a blank line flips loose exactly the list that directly receives the next
block; blanks interior to fenced code, indented code, or nested blockquotes don't leak outward; empty-marker lines
aren't blanks); empty items (may contain at most one blank line; can't interrupt a paragraph directly - but CAN in
lazy position, matching cmark); different-delimiter markers split the enclosing list (`3)` after `2.` opens
`<ol start="3">`); lazy continuation appends the post-matched-marker remainder (an outer `>` no longer leaks into the
paragraph); fenced-code / HTML-block leaves swallow container markers as content; a blank line ends a GFM table.
"List items", "Lists", "Block quotes", and "Emphasis and strong emphasis" are now full sections.

M8 (a code-review-driven pass) fixed: entity prefix decoding; verbatim line joining (code spans / raw HTML keep
interior whitespace; `\\` at EOL no longer hard-breaks; exact Text-event source spans); body-vs-attribute HTML
escaping; ASCII-only href passthrough; `~` flanking (intraword strikethrough); CM 0.31 HTML comments; entity decoding
in link destinations / titles / fence info strings; mod-3 rule on original run lengths; failed-link suffix
re-tokenization (CM 528/529); iterative inline walkers + enforced `max_container_depth` / `max_nested_parens` (deep
nesting degrades instead of raising); inline-pass quadratics (binary-searched offsets, bulk text consumption) and a
cheap BlockMachine clone for streaming tentative computation.

Note: spec totals before M8 were out of 572 - the spec runner's setext-header detection swallowed the 80 examples
whose first content line was a `---`/`===` line. The corrected corpus holds all 652 upstream examples; the pre-M8
parser measured against it scores 535/652 default, 579/652 prescan.


## Cross-cutting invariants — verified

All four invariants from [00_Goals.md](00_Goals.md#cross-cutting-invariants) hold under test:

1. **Committed events are immutable, append-only.** No M6 test detects a committed event
   changing across feeds.
2. **`tentative` is a contiguous suffix of the oracle event stream.** Verified implicitly by the
   M6 equivalence tests (the prefix `committed_so_far + current_tentative` always matches the
   oneshot parse of the prefix-of-input-seen-so-far on small fixtures).
3. **Full-reparse equivalence.** `StreamingParser().feed(text_in_N_chunks).committed +
   finish().committed == parse(text)` for any chunking. Verified over 652 CommonMark spec cases
   + 14 GFM cases × 8 chunking strategies (whole / each-char / fixed-1 / fixed-3 / fixed-32 /
   by-lines / random-7 / random-42). Plus a smoke test that splits a representative fixture at
   every possible byte position.
4. **Absolute char-position source offsets on every event.** `pdcmark/tests/test_offsets.py`
   asserts `0 ≤ start ≤ end ≤ len(input)` for every event in every CM spec case, that Start/End
   spans enclose their inner events for the first 200 cases, and exact spans on hand-written
   inputs (entities / escapes must not shrink a Text event's source span).


## Spec section breakdown (current)

| Section | Default | Prescan | Total |
|---|---|---|---|
| ATX headings | 18 | 18 | 18 |
| Autolinks | 19 | 19 | 19 |
| Backslash escapes | 12 | 13 | 13 |
| Blank lines | 1 | 1 | 1 |
| Block quotes | 25 | 25 | 25 |
| Code spans | 22 | 22 | 22 |
| Emphasis and strong emphasis | 132 | 132 | 132 |
| Entity and numeric character references | 16 | 17 | 17 |
| Fenced code blocks | 29 | 29 | 29 |
| HTML blocks | 44 | 44 | 44 |
| Hard line breaks | 15 | 15 | 15 |
| Images | 9 | 22 | 22 |
| Indented code blocks | 12 | 12 | 12 |
| Inlines | 1 | 1 | 1 |
| Link reference definitions | 23 | 27 | 27 |
| Links | 60 | 88 | 90 |
| List items | 48 | 48 | 48 |
| Lists | 26 | 26 | 26 |
| Paragraphs | 8 | 8 | 8 |
| Precedence | 1 | 1 | 1 |
| Raw HTML | 20 | 20 | 20 |
| Setext headings | 27 | 27 | 27 |
| Soft line breaks | 2 | 2 | 2 |
| Tabs | 11 | 11 | 11 |
| Textual content | 3 | 3 | 3 |
| Thematic breaks | 19 | 19 | 19 |

GFM extensions (under `pdcmark.GFM`):

| File | Pass |
|---|---|
| `gfm_strikethrough.txt` | 3/3 |
| `gfm_table.txt` | 9/9 |
| `gfm_tasklist.txt` | 2/2 |


## Performance

Measured against markdown-it-py (`commonmark` preset) on shaped corpora, best-of-3, CPython 3.14 (see the review
session's bench script; ratios are pdcmark time / markdown-it time):

| shape | size | pdcmark | markdown-it | ratio |
|---|---|---|---|---|
| plain paragraphs | 41 KB | 12.4 ms | 9.1 ms | 1.36x |
| one long paragraph | 32 KB | 8.2 ms | 8.3 ms | 0.99x |
| emphasis-heavy | 40 KB | 84 ms | 66 ms | 1.26x |
| code-heavy | 16 KB | 16 ms | 6.5 ms | 2.4x |
| list-heavy | 17 KB | 72 ms | 44 ms | 1.6x |
| link-heavy | 21 KB | 35 ms | 34 ms | 1.02x |
| quote-heavy | 14 KB | 39 ms | 23 ms | 1.7x |
| LLM-chat-like | 35 KB | 51 ms | 34 ms | 1.5x |
| CommonMark spec.txt | 204 KB | 147 ms | 85 ms | 1.7x |

Streaming a 100-line paragraph in 40-char chunks: ~82 ms (the tentative tail re-inline-parses the open block each
feed - O(block²) while a single block streams; irrelevant at chat scale).

The profile is flat: no function exceeds ~10% of runtime. Time is interpreter fixed cost per line / node / event
(the top entries are the per-line orchestrator itself, `isinstance` dispatch, and dataclass construction). The
remaining gap to markdown-it is that its inline lexer leans on C-level regex sweeps where we make many small Python
calls. Closing it would take compilation (mypyc / C++), and there is no well-isolated kernel to compile: the cost is
smeared across the block machine, tokenizer, and event layer, and the omcore dataclass records in those hot paths
would not benefit from mypyc without first being rewritten as plain classes. Deliberately not pursued - current
throughput (~0.5-4 MB/s by shape) exceeds LLM streaming rates by 3-4 orders of magnitude.

## Out of scope (explicit non-goals)

These are pulldown-cmark extensions we explicitly don't port — see
[00_Goals.md](00_Goals.md#non-goals). Hooks exist at the option layer where they'd live; the
parser doesn't emit corresponding events:

- Definition lists
- Math (`$...$`, `$$...$$`)
- Wikilinks
- Metadata blocks (YAML / `+++`)
- Heading attributes (`# h { #id .class }`)
- Smart punctuation
- Superscript / subscript
- Old-footnote syntax
- Container extensions (`:::name`)
- Footnotes — design hooks present, but the parser doesn't currently emit `FootnoteReference` or
  `Tag::FootnoteDefinition` events. Adding them is a small, additive change (recognize `[^id]`
  in inline tokenization; recognize `[^id]:` at refdef-collection time).


## Known limitations beyond non-goals

- The `[foo][bar][baz]` bracket-chaining pair (CM 569/571): a failed `[foo][bar]`'s re-tokenized
  `[bar]` cannot pair with the following `[baz]` - the suffix rescan is bounded at its own span.
  The last two prescan-mode failures.
- Pulldown's own `specs/table.txt` is a stricter suite than the GFM spec. Compared structurally
  (ignoring whitespace between tags - its fixtures compact table markup onto one line) 25/28 pass
  by default, 26/28 under prescan. Two misses are deliberate cmark-gfm / GitHub-compatible choices:
  a header row may be the last line of a multi-line paragraph without a leading pipe (pulldown
  requires the pipe), and a `- | -` delimiter row is a list item (pulldown reads it as a table).
  The third is the forward-reference streaming tradeoff (refdefs below the tables that use them).
- Forward-reference resolution in streaming mode degrades to `LinkType.*_UNKNOWN` /
  `BrokenLinkResolver`. Documented; oneshot's `prescan_refdefs=True` recovers full spec behavior.
- Pathological bracket floods (`[` × N + `]` × N) are polynomial (list splicing), not linear —
  bounded and crash-free, but slower than pulldown on that shape.
- Emphasis resolution has no `openers_bottom` optimization; a failed closer rescans the whole
  delimiter stack (fine in practice, quadratic in adversarial delimiter soup).
