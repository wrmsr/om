# dev 01 - the parity push (phases 4 & 5)

Continues from `dev_00_initial.md` (phases 1-3 + async driver). This era: chat-head parity pieces and the fullscreen
side of the world.

## 2026-08-15: markdown stack + highlighters

- `text/markdowns.py`: the zero-dep, line-oriented markdown subset, built around the commit model from the start:
  `parse_lines(lines, at_eof)` returns `(blocks, settled_line_count)` - a block settles when its terminator is seen
  (blank line, next block's opener, closing fence). `MarkdownStream` uses that for the settled/tail split; the
  trailing partial line can never settle. Blocks: atx headings, paragraphs, fenced code (info string -> highlighter),
  quotes, flat lists (indented continuations join), rules. Inline: bold/italic/strike/inline-code/links, one pass,
  outermost-marker-wins (terminal styling doesn't meaningfully nest). Renderer emits segment rows with `md.*` theme
  tags; code blocks right-fill to width so bg themes paint solid; hanging indents for lists/quotes/headings.
  NOT commonmark: no setext, nesting, tables, ref links, html - documented in the module docstring.
  markdown-it/incparse can slot behind the same block types later.
- `text/highlights.py`: `Highlighter` abstract (lines -> segment rows, plain=None style so containers can re-base),
  `PythonHighlighter` (stdlib tokenize; **any** tokenize error = fall back to plain, since streams and snippets are
  the norm; multi-line strings span rows via a span sink; def/class names, builtins, soft keywords, decorators),
  `DiffHighlighter`, plus the `highlight_code` adapter markdown consumes. Incremental (tree-sitter) extends this
  protocol later; full-retokenize stays the fallback.

## 2026-08-15: history, suggestions, chatdemo

- `controls/histories.py` (draft-stashing prev/next), `controls/suggestions.py` (selectable popup, tab cycling),
  `controls/markdowns.py` (`MarkdownTail`: feed/pop_settled/finalize + live tail render - the app commits what
  settles), `TextArea.set_text` for history fills.
- `apps/chatdemo.py`: the chat-head-shaped flagship. Canned markdown responses stream char-chunk-wise; settled
  blocks commit with python/diff highlighting; messages numbered via a registry (`/show n` re-commits raw source -
  the unsealed-tomb pattern standing in for /pbcopy); `/` popup with tab-complete; up/ctrl+p history at first line;
  user messages render as markdown too. Verified under pty end-to-end (including keyword-colored cells in the
  emulator's captured scrollback).
- Bug caught by pty: the app constructor committed (response header) before driver.run() prepared the surface -
  first-response start now rides a 0-delay timer. Pattern to remember: **anything touching the terminal must happen
  inside the loop.**
- /show initially committed unwrapped raw lines wider than the terminal - they pin at the margin (autowrap off) and
  garble. Rule restated: wrapping is strictly the content producer's job; commits must fit the width.

## 2026-08-15: AltSurface + vimdemo

- `surfaces/alts.py`: fullscreen over the same diff machinery; absolute `cup` movement with tracked-cursor elision
  (an identical frame costs exactly the sync-output bracket, same as inline); no commit - that's the tradeoff
  fullscreen opts into. `Surface` base grew `tty` + `take_resized`; drivers accept any `Surface` (commit()
  isinstance-checks Inline).
- `apps/vimdemo.py`: the demotty successor - same TextArea/engine fullscreen, '~' filler rows, vim status line
  (mode/pending/cmdline + file [+] ruler), `:w/:q/:q!/:wq` with real file IO. pty-verified: `/two<CR>ciwTWO<Esc>
  ggddp:w:q` produced exactly the right file on disk. Cosmetic lesson: the elastic status bar can be >1 row (long
  filenames), so the editor height budget must *measure* it, not assume 1.
- Modified-flag caveat: tracked via doc.version, so undo-back-to-saved still reads as modified. Fine for a demo;
  a real editor wants content hashing or version-pinning.

## 2026-08-15: CPR origin negotiation

The last known citizenship gap: prepare()'s bare CR overwrote a shell's partial prompt line. Now both drivers do the
ptk-style dance: `prepare(defer_origin=True)` writes nothing positional; a DSR-6 goes out with the parser armed
(`expect_cursor_position_report`); rendering AND commits hold (commits queue in order) until the response - mid-line
cursor gets a fresh `\r\n`, col-0 stays put - with a 250ms fallback to the old overwrite behavior for terminals that
never answer. The origin CPR is consumed as plumbing, never forwarded to the app. Standalone surface use (no driver)
keeps the old immediate-CR default. Tests answer the CPR like a real terminal; one test proves the mid-line prompt
survives with output starting below it.

## State

125 tests, ruff+mypy clean. Since dev_00: markdown/highlights, history/suggestions/chatdemo, AltSurface/vimdemo,
CPR origin. Remaining ideas, roughly by value:
- DECRQM-negotiated sync-output + kitty flags query (currently emitted unconditionally/blind - harmless but blind).
- Warm-window message controls (tool-card lifecycle, confirmations) - likely best designed against the real chat
  head rather than speculatively here.
- Keymap layer is built+tested but apps still hardcode key checks; adopt it when bindings become configurable.
- pygments/tree-sitter optional highlighters; markdown-it/incparse optional block parser.
- vt100 emulator: model the alt screen (tests currently grep bytes for 1049).
- Mouse hit-region map for click-only interactions.
- 3.14t (freethreaded) run of the test suite.

## 2026-08-15 (later): pygments, sync-output negotiation, freethreaded check

- `text/pygmenting.py`: the optional long-tail highlighter, quarantined per the dependency policy (proxy-imported,
  `find_spec` availability probe, None on unknown language). Token subsumption maps pygments types onto the same
  `code.*` tags; internal zero-dep highlighters keep precedence in `get_highlighter` (the fallback is wired through a
  `lang.proxy_import` to avoid the import cycle). Fun fact caught by CI: pygments has a brainfuck lexer, breaking the
  'unknown language' test's choice of strawman.
- DECRQM negotiation for synchronized output: drivers send `CSI ? 2026 $p` at startup; a `ModeReportEvent(2026, 0)`
  (unrecognized) turns the per-frame sync bracket off. Consumed as plumbing like the origin CPR; still
  blind-optimistic until/unless the terminal answers, since unknown DECSETs are ignored anyway. `Surface` base grew
  `set_sync_output`/`request_sync_output_report`.
- Re-verified chatdemo under a pty *answering* the CPR mid-line: the shell's partial prompt survives with output on
  a fresh line below.
- The whole suite (127 tests) passes under freethreaded 3.14t (`.venvs/14t`, GIL off) as well as the default 3.14.

## 2026-08-15 (session 3): editor depth + warm window

**Highlighting in the editor.** TextArea grew a display transform (tabs -> four spaces, control chars -> caret
notation - fixing a real cursor-desync bug: typed tabs rendered as literal \t, terminal advanced to a tab stop while
tracking assumed width 1) and a highlighter-as-base-span layer under engine decorations (search/selection override
syntax where they overlap), cached by doc version. Consequence: highlighter output columns must be SOURCE-true - the
python highlighter no longer expands tabs (markdown's code renderer expands display-side instead).

**tree-sitter landed** (docs/treesitting.py + docs/highlighting.py). The IncrementalHighlighter protocol lives in
docs/ because it speaks TextEdit (text/ stays below docs/ in the layering). TextArea auto-subscribes doc edits to an
incremental highlighter; TreeSitterHighlighter maps edits onto Tree.edit() (byte offsets/points computed against its
own tracked source copy, so a missed edit degrades to a full parse, never wrong output - `parse_counts` exposes
full/incremental for tests). Grammar packs probed as tree_sitter_<name>; capture names map onto the shared code.*
tags. Tests prove: incremental engages on keystrokes, results byte-identical to a fresh full parse, unicode/multiline
edits correct. vimdemo now prefers tree-sitter by extension (verified live under pty while editing - 882 bytes total
for open/edit/quit, incremental reparse + retained diff both earning their keep).

**Vim depth.** `%` (bracket match via scans.match_bracket - vim's seek-first-bracket-on-line then nesting-aware
multi-line match), `~` (case toggle + advance). **Blockwise visual shipped**: ctrl+v (engine token '<c-v>'),
Kind.BLOCK spans from _visual_span, per-row rectangle decorations in TextArea, d/y/c/p over rectangles (block paste
pads short lines and creates rows; block change types on the first row only - replication and I/A block-insert are
the multi-cursor era's). Registers append blocks vertically. Viewport ops in TextArea (view concern, engine stays
headless): ctrl+d/u half-page, ctrl+e/y line scroll, zz/zt/zb (z chord held by the view layer), H/M/L - all yielding
to pending operator commands.

**Emulator alt screen** (omcore, in place): DECSET 47/1047/1049 with saved main screen+cursor, alt scrolling
discards instead of feeding scrollback. Alt-surface tests now assert emulator state instead of grepping bytes.

**Warm window.** `controls/cards.py`: the updatable/expandable lifecycle card (PENDING/CONFIRMING/RUNNING/COMPLETE/
DENIED/FAILED, state glyphs+tags, click-to-expand). `stack_layout` returns hit regions (clip_top keeps local row
indices control-true under drop-from-top truncation - a test caught the naive mapping). chatdemo demonstrates the
full flow: stream pauses mid-response, card appears CONFIRMING (f10/f2 to decide, ctrl+o toggles detail, click works
under --mouse), runs, completes with results, then **commits exactly as displayed** and streaming resumes - verified
under pty end-to-end. Mouse stays opt-in (--mouse) per the wheel-vs-native-scrollback tradeoff.

Session totals: 150 tests (plus tree-sitter suite), ruff+mypy clean, 14t green. Still open, honestly: block-change
replication + block I/A (needs the multi-cursor machinery), marks/macros/regex-search, mouse hit-testing within
committed content (impossible by design - dead scrollback), DECRQM-gating kitty pushes, markdown-it optional parser.

## 2026-08-15 (session 4): multi-cursor + swappable markdown backends

**Multi-cursor is live.** The day-one groundwork (cursors tuple, range edits with position remapping) paid off
exactly as designed - the core is one function: `_edit_at_cursors` applies a logical edit at every cursor in
ascending document order, each position remapped through the edits already applied that keystroke. Everything in
insert mode multiplexes: typing, backspace (incl. line joins), enter, paste. Entry points: blockwise `I` (skips rows
short of the block edge, per vim), `A` (pads short rows), and `c` - **block change now live-replicates onto every
row** (real vim replays at Esc; we show it as you type). Plus a public `add_cursor(pos)` API for frontends. Esc
collapses to the primary; colliding cursors merge; undo/redo collapse too (grouped edits made that free). Secondary
cursors render via a `vim.cursor` decoration tag - including a styled-space cell when parked on the newline slot
(TextArea grew EOL-tag rendering). `VimStatus.cursor_count` feeds status bars. Still future: normal-mode multi
(the vim-multiple-cursors replay model), block I/A via dot-repeat.

**Streaming markdown backends are swappable.** `MarkdownStreamBackend` abstract (feed / pop_settled / tail_blocks /
finalize), three implementations behind `get_markdown_stream(name)`:
- `internal` (default): the zero-dep line-based parser, unchanged behavior.
- `pdcmark` (`text/pdcmarks.py`): omcore's pulldown-cmark translation. Its `StreamingParser` contract (committed
  events append-only + tentative tail, chunking-invariant) IS this layer's contract - **zero pdcmark modifications
  needed**; the adapter is pure event->MdBlock conversion, buffering committed events until top-level groups
  complete. In-repo dependency, no quarantine.
- `markdown-it` (`text/markdownits.py`): tokens via omdev's `IncrementalMarkdownParser` (quarantined external dep).
  Note its stability rule is more conservative (holds the last TWO top-level blocks) - a settle-timing difference,
  not a correctness one; tests encode the loosened contract.
Enabler: **MdBlock inline content is now styled spans** (`.of(text)` constructors keep the internal parser and tests
ergonomic) - backends with real inline engines produce spans directly instead of reconstructing markdown for the
regex inliner. Flattenings for the simple render model: nested quote/item content joins into parent spans (non-
paragraph children become siblings), nested lists merge, tables render as pipe-joined rows, hard breaks soften.
Cross-backend tests: identical rendered output for the shared sample at chunk sizes 1/7/4096; per-backend
incremental-settle behavior; inline style survival. chatdemo takes `--md=internal|pdcmark|markdown-it` - both new
backends pty-verified streaming the full demo with highlighted code fences.

Next up (per the repo owner): wiring minitui to what minichain has become.

## 2026-08-15 (later): the enter-chord ergonomics fix

Why ctrl/shift+enter didn't work on the owner's mac: Enter is the single byte 0x0d on the legacy wire and shift/ctrl
don't change it - only extended-key protocols can report them. We spoke kitty's protocol but not xterm's older
`modifyOtherKeys`, which is what iTerm2 (pre-3.5), xterm, mintty, and notably tmux's `extended-keys` forwarding emit.
Fixes:
- Surfaces now request modifyOtherKeys (`CSI >4;2m`) alongside the kitty push (same `kitty_keys` opt-in - it's
  'extended key reporting' generally now), reset on restore; the parser decodes `CSI 27;mod;code~` through the same
  codepoint+modifiers path as kitty's `CSI code;mod u`.
- **ctrl+j submits from insert** (when the TextArea has a submit handler): 0x0a is byte-distinguishable from Enter's
  0x0d on every terminal ever made because we clear ICRNL - the universally-portable chord, per the owner's pick.
- shift+enter now also submits (all modified Enters mean 'send'; plain Enter in insert is the newline).
pty-verified all three: modifyOtherKeys ctrl+enter, raw ctrl+j, kitty shift+enter. Remaining true limitation:
Terminal.app supports neither protocol - there, ctrl+j / alt+enter (with option-as-meta) are the options.

## 2026-08-15 (later): :s[ubstitute], ex ranges, line jumps

`vim/substitutes.py` + engine wiring: engine-owned ex built-ins run before app-handler delegation.
- `[range]s<sep>pat<sep>repl<sep>flags`: ranges `%` / `N,M` / `.` / `$` / `'<,'>` (visual-mode `:` leaves visual,
  records the marks, and prefills `:'<,'>` like vim); any punctuation separator with backslash escaping; flags `g`
  (per-line-all; first-only default, like vim) and `i`.
- **Documented divergence: patterns are python `re` syntax**, not vim's dialect (no magicness levels; `(...)` not
  `\(...\)`). Replacement keeps the vim conveniences: `&` = whole match (`\&` literal), `\1` groups, `\r` inserts a
  real line break (the row-offset bookkeeping handles document growth mid-range). Empty pattern reuses the last `/`
  search, escaped literally.
- One undo unit per substitute; cursor to the last substituted line (vim semantics - which promptly confused my own
  pty script: after `:%s` the cursor is on the last line, so select ranges from a known spot). vim-style message
  ('N substitutions on M lines'), 'Pattern not found', 'Invalid pattern: ...'.
- Bare ranges jump: `:42`, `:$`, `:%`. Everything unrecognized (`:w`, `:set ...` - note `set` starts with 's' but
  has no separator, tested) still reaches the app's ex handler untouched.
- Not yet: `c` confirm flag, `:g//`, counts, `~` sugar. 193 tests; live-verified in vimdemo (:%s, visual-range :s,
  group refs, :w roundtrip to disk).

## 2026-08-15 (later): pdcmark code review (owner asked "how does that code look?")

Full read + differential + benchmarks of omcore/text/pdcmark while we're depending on it as an md backend.
- **Verdict: high quality.** Faithful firstpass.rs analogue in blocks/machine.py (immutable open-block records via
  dc.replace, offsets on everything), honest docs (04_Status.md lists real limitations), zero TODO/FIXME markers,
  359-test suite incl. chunking-equivalence invariants over 8 feed strategies.
- **Found+fixed one real bug** (ee77bfccb): named-entity scanning trusted `html.unescape(raw) != raw`, but unescape
  resolves legacy semicolon-less entities embedded as *prefixes* - `&notanentity;` decoded to `¬anentity;` via the
  HTML4 `&not`. Now an exact `html.entities.html5` lookup of `name + ';'`. Regression test added.
- Differential HTML vs markdown-it, 62 tricky cases normalized: **59/62 identical**; all 3 divergences are
  option-gated, not bugs (forward refdefs -> `prescan_refdefs=True`; strikethrough/tables are off-by-default GFM
  extensions; pdcmark emits `<del>` like pulldown, markdown-it emits `<s>`). Unclosed-fence handling is
  spec-correct where markdown-it deviates.
- Perf: oneshot ~0.43 MB/s vs markdown-it 0.70 (same order, fine); streaming 8-char chunks ~64 KB/s - the
  deepcopy-per-feed tentative computation is the tax. Still ~1000x faster than LLM tokens arrive; noted as the
  obvious optimization target if it ever matters (lazy tentative, or snapshot only the open-block spine).
- Minor: `BlockMachine.tentative_events` (machine.py:180) is dead code with a false "does not mutate" docstring
  (routes through refdef consumption + shared Fuel). Left for the owner's call.

Deep-dive addendum (inlines/scanning layers, agent-assisted, top claims re-verified by hand):
- Confirmed real bugs beyond the entity fix: (a) per-line trim at join time destroys trailing spaces/`\` inside
  code spans and raw HTML (~7 spec cases); (b) `\\` at EOL wrongly becomes a hard break (even-run rule ignored);
  (c) `~` delimiters use the *underscore* flanking rules so intraword `a~~b~~c` never strikes; (d) Text-event end
  offsets shrink after entities/escapes (decoded length added to source position); (e) unbounded recursion -
  `'*'*3000+'a'+'*'*3000` raises bare RecursionError; `options.max_container_depth`/`max_nested_parens` and
  `ResourceLimitExceededError` are never read/raised; (f) `_escape_html` escapes `"` in body text (attribute-style
  everywhere) - swapping just that function measured 459->477 default / 503->521 prescan; (g) `_escape_href` uses
  unicode-aware `isalnum` so non-ASCII never percent-encodes.
- Perf root cause found: `_source_offset` + `_line_index_at_newline` are linear scans -> inline pass ~O(n^1.9);
  75% of a 2000-line-paragraph parse. Trivial fixes (bisect over joined_start; newline-pos dict).
- Architectural limit: link suffix consumed at tokenize time, so failed links can't rescan (CM 528/529).
- Sizeable dead-code inventory (whitespace.py scanners, LineStart.min_hrule plumbing, refdefs
  parse_single_line_refdef with a false "still used" comment, etc.); inlines/links.py and parser.py have no unit
  tests of their own; offset tests only assert bounds so (d) sails through.
- None of it blocks the minitui backend usage: streaming chat markdown doesn't hit the pathological shapes, and
  the differential is fully explained. Fix-ups are the owner's call.

## 2026-08-15 (later still): pdcmark M8 - fixed everything the review found

Owner said "fix all of it, especially the performance issue". Eight commits (617101791..cff233a23):
- **Perf**: binary-searched offset mapping + bulk plain-text consumption in the tokenizer (75%-of-parse quadratic
  gone; 400-line paragraph 39->14ms) and a cheap shallow BlockMachine.clone() replacing deepcopy for streaming
  tentative computation (100-line/40-char-chunk stream 329->81ms, 4x).
- **The invasive one**: verbatim line joining - trailing-space/backslash hard breaks, next-line leading-skip, and
  paragraph edge-trimming all decided in the walk where text context is known. Fixes code spans/raw HTML eating
  interior whitespace, `\\` EOL false hard break, and exact Text-event source spans (offsets from joined positions,
  not decoded lengths).
- Renderer escaping split (body &<> vs attribute +"), ASCII-only href passthrough; ~ uses * flanking; CM 0.31
  comments; entities decoded in dests/titles/fence infos; Zs-only whitespace; mod-3 on original run lengths
  (DelimNode.original_count).
- **Link-suffix rescan** (the one the reviewer called architectural): LinkCloseNode records its suffix's joined
  span; on failure resolve_links re-tokenizes it (prefix-slice bounded) and splices fresh nodes in. CM 528/529 pass.
- Iterative inline walkers (no more RecursionError at any depth); max_container_depth and max_nested_parens actually
  enforced (degrade to content, never raise); never-raised ResourceLimitExceededError removed.
- Dead-code sweep (whitespace/lines scanners, min_hrule plumbing, parse_single_line_refdef, no-op branches, false
  comments); abstractmethod on BrokenLinkResolver.resolve; annotations; README links.
- **Test-runner bombshell**: the spec runner's setext-header detection was swallowing 80 upstream examples whose
  first content line was ---/=== (and misattributing sections - 'Thematic breaks' really has 19 cases, not 2).
  True corpus is 652 examples. Honest before/after on the FULL corpus: **535/579 -> 572/618** (default/prescan,
  88%/95%). Ratchets raised; curated indices remapped to true upstream numbering; 5 new strict sections.
- 421 pdcmark tests (was 355 + removed-dead-fn tests) incl. new test_links.py/test_parser.py/test_rendering.py,
  exact-span offsets, multi-line inline semantics, strikethrough/unicode flanking, deep-nesting DoS. Green on 3.14
  and 3.14t. minitui's 193 still green; differential vs markdown-it still 59/62 with all 3 option-gated.

## 2026-08-15 (M9): list-machine edge semantics - List items/Lists/Block quotes/Emphasis now full

Owner asked what the list gaps were, then "take a run at all of them". One commit (5c7c78ee4):
- **Tight/loose rework**: pending-blank model - _handle_blank records a pending blank on open lists (skipping
  verbatim-leaf content, still-matched blockquote interiors, and empty-marker lines); _consume_pending_blank flips
  loose exactly the list that directly receives the next block (innermost open item's list) and clears the rest;
  indented-code continuation drops the pending blank (interior to the block). Every shape cross-checked against
  markdown-it (18/18 battery).
- **Empty items**: began_empty on OpenItem; item + immediately-following blank stays empty (list stays open); empty
  markers can't interrupt a paragraph *directly* but CAN in lazy position (cmark's interrupts_paragraph is true only
  when the matched container is the paragraph itself - so `> foo` + `2. bar` splits into quote + ol start=2, which
  we previously got wrong too).
- **Different-delimiter split**: `3)` after `2.` closes the list and opens ol start=3 (lazy gate no longer applies
  interrupt restrictions; the start!=1 and non-empty rules live only in the direct-interrupt paths).
- **Lazy remainder**: lazy continuation appends the post-matched-marker slice, not the raw line - `> 1. > quote` +
  `> lazy` no longer leaks a literal `>` into the paragraph.
- **Two extra machine bugs found while in there**: fenced-code/HTML-block leaves were being displaced by container
  markers in their content (`>` or `-` lines inside a fence shredded it!) - now skipped per cmark's loop guard; and
  blank lines didn't close GFM tables (following paragraph became a table row).
- CM spec 589/652 default, 635/652 prescan (ratchets raised); 17 of 26 sections now 100% incl. List items(48),
  Lists(26), Block quotes(25), Emphasis(132). 445 pdcmark tests (20 new in blocks/tests/test_list_edges.py), green
  on 3.14 + 3.14t; minitui 193 green; remaining default-mode failures are the documented forward-refdef streaming
  cluster (Links/Images/refdefs) plus Tabs 8/11 and singleton stragglers.

## 2026-08-15 (M10): tabs, refdefs, raw label matching - 650/652 prescan

Owner: "do all the easy and medium ones, and the GFM table edge". One commit (4f36da6c0):
- GFM table edge turned out already fixed by M9's blank-closes-table; floor raised to 9/9 (14/14 GFM fixtures).
- Easy: blank lines inside indented/fenced code keep post-indent whitespace (_handle_blank now takes the LineStart);
  HTML blocks start on a fresh line inside <li>; collapsed/shortcut labels match RAW source text via a joined-text
  slice on TokenizedBlock (LinkOpen/LinkClose carry joined positions) - `[foo\!]` never matches `[foo!]`, `[bar\\]`
  matches itself.
- Medium: _strip_indent_columns(carry, text, cols) materializes leftover tab-carry columns into indented-code
  content (`- foo` + tab-tab-bar keeps its two spaces; same via `>`); try_consume_refdef reworked over joined
  candidate text - multi-line labels (scan_link_label now treats \n as whitespace for the only-ws check) and
  multi-line titles, whitespace REQUIRED between dest and title (`<bar>(baz)` is garbage), invalid-title-line
  fallback keeps the refdef title-less; refdefs peel BEFORE setext promotion (empty remainder -> the === underline
  is paragraph text; one old test encoded the wrong behavior and was rewritten to CM 215/216).
- CM spec 603/652 default, 650/652 prescan - the ONLY prescan failures left are the bracket-chaining pair 569/571
  (bounded-rescan limitation, documented). Strict sections now include Tabs, Indented/Fenced code, HTML blocks
  (21 of 26 sections at 100% in default mode).
- 463 pdcmark tests (18 new), green 3.14 + 3.14t; minitui 193 green; differential 59/62 steady; perf unchanged
  (13.4ms / 84ms benchmarks).

## 2026-08-15 (perf research): profile + micro-batch, extension assessment

Owner asked for a profile, low-hanging wins, and whether a c++/mypyc extension is warranted.
- Bench harness (scratchpad pdc_bench.py) vs markdown-it over 9 shaped corpora. Before: 1.1-3.2x slower by shape.
- Low-hanging batch landed (8b4ddf97b): is_blank_line via str.strip (6x on itself); _iter_lines str.find scan with
  LF fast path (was per-char over the whole doc); hot dc.replace sites -> direct construction (~8us -> ~1us each;
  paragraph/fence/html/indented line appends + BufferedLine rebuilds; _fence_with_content helper for the 7-field
  record). Net -23% on spec.txt (190->147ms), long-para at PARITY (0.99x), code-heavy 3.2->2.4x. No behavior change.
- Post-batch profile is FLAT: top entries are _process_line itself, isinstance, dataclass init - interpreter fixed
  cost per line/node/event. No function >10%. Remaining candidates are ~2-3% each (renderer type-dict dispatch,
  BufferedLine as plain class) - diminishing returns.
- Extension verdict: NO well-isolated kernel to compile. Cost is smeared across machine+tokenizer+events; mypyc
  wouldn't help the omcore-dataclass records in hot paths without first rewriting them as plain classes (a real
  refactor, not a bolt-on); a C++ extension would be a rewrite. Documented in 04_Status's new Performance section
  with the measured table. Current 0.5-4 MB/s beats LLM streaming rates by 3-4 orders of magnitude.

## 2026-08-16 (later): the moves - pdcmark -> omcore/text/, minitui -> omxtra/tui/

Owner asked me to perform the relocations (previous session's renames had been done in place).
- omcore/text/pdcmark: all `from omcore import X` relativized per omcore convention (`from ... import` at package
  level, one more dot per subpackage); dataclass codegen regenerated; 463 tests green in place. tui's backend
  wrapper now imports omcore.text.pdcmark.
- omxtra/tui/minitui: merged alongside the pre-existing apps/txpython. Module-path strings in app docstrings/README
  updated (x.minitui -> omxtra.tui.minitui); design.md layout header and intro.md gate commands updated - the package is
  now inside the repo-wide make targets.
- Combined suites green on 3.14 + 3.14t (656 tests), ruff + mypy clean across both new locations, spec scores
  and differential unchanged (603/650, 59/62).

## 2026-08-16 (later): ctrl+[ dead on iTerm2 - extended-protocol legacy aliases

Owner report: ctrl+[ broken on mac iTerm2 (with or without tmux) but fine through iterm->tmux->mosh->linux-tmux.
Perfect protocol fingerprint: iTerm2 3.5+ speaks the kitty keyboard protocol we negotiate, so ctrl+[ arrives as
`CSI 91;5u` -> Key('[', ctrl) instead of raw 0x1b -> Key('escape'); mosh strips the negotiation so the remote chain
stays legacy and "works". Fix (2b3645e99): `_CTRL_ALIAS_BASES` in the shared codepoint path folds the three
diverging legacy aliases back - ctrl+[ -> escape, ctrl+m -> enter, ctrl+i -> tab (alt survives, matching legacy
ESC-prefix; ctrl+h/ctrl+j already agreed across wires since 0x08/0x0a decode to ctrl+h/ctrl+j). Distinctions the
protocols exist to provide are kept: ctrl+enter (13;5u, the submit chord), ctrl+shift+i, ctrl+h stay themselves.
Parser regression tests for both wire forms + kept-distinctions; verified end-to-end that kitty-wire ctrl+[ leaves
INSERT in a TextArea. (Also removed the pycache-husk dirs left at omxtra/tui/<pkg> by the minitui re-nesting;
package now lives at omxtra/tui/minitui alongside apps/txpython.)

## 2026-08-18: colors - default dark theme from textual-dark

Owner wanted minitui prettier before the omllm wiring: soft default scheme (the tool-confirmation ANSI bg=GREEN/RED
was the poster child), textual-dark as reference (dumped hexes at omdev/tui/rich/textual/dark.py). Settled: truecolor
authoring w/ auto-downgrade, subtle bg accents, full scope incl. syntax. One commit (cd6a23aab):
- text/themes.py: DARK_THEME/DEFAULT_THEME - palette constants parsed from the dump (values copied, no omdev import),
  covering every library tag (md.h1-6/code.*/card.*/popup.*/vim.*/status.*). Deliberate divergences documented in
  the module docstring: code-block bg uses surface #1E1E1E (fence #101010 is invisible on near-black terminals),
  code.def bold not underline, syntax styles carry the block bg themselves (no bg-inheritance rule - fullscreen
  apps strip it via extend, as vimdemo does).
- colors.py: parse_rgb (#RGB/#RRGGBB, alpha rejected - dump pre-blends) + detect_color_depth (COLORTERM truecolor/
  24bit -> TRUE; TERM 256color -> 256; direct/truecolor -> TRUE; dumb -> MONO; else 16). Surfaces' depth param is
  now `ColorDepth | None = None` -> detect; tests/harness pins TRUE for deterministic captures.
- styles.py: Theme.extend (dict overlay, whole-entry replacement per tag).
- Mechanical: md heading clamp 3->6 (all backends route through MdHeading.of, one site + render retag); status-bar
  filler tagged 'status.bar'.
- Demos: DEFAULT_THEME.extend({app-locals}) - chatdemo's 45-entry dict + CODE_BG gone; confirmation buttons now
  #121212-on-#71AC84 / #E0E0E0-on-#B93C5B.
- Tests 195 -> 204: parse_rgb/detect matrix, theme-coverage (every library tag resolves non-empty AND uses no
  NamedColor - the no-jarring-ANSI invariant), md.h4-6 retag, confirmation-card cells resolve to RgbColor.
  Green 3.14 + 3.14t; ruff/mypy clean. SGR ladder verified: #0178D4 -> 38;2;1;120;212 / 38;5;32 / cyan.
- Owner should eyeball chatdemo (+ --md=pdcmark) and vimdemo for taste tweaks - hexes are all named constants in
  themes.py, trivially adjustable.

## 2026-08-18 (later): THE WIRING - flat API + omllm/ui/tui/minitui

The moment the whole project pointed at. Two commits (04b744757, 80da20d34):
- **Flat lazy API**: minitui/__init__.py grew the minichain-style auto_proxy_init block - ~200 names, `from
  omxtra.tui import minitui as mt`, everything a dot away, ~40ms import (lazy). Only ONE flattening clash existed
  (SegmentRows, identical aliases in text.highlights + text.markdown -> canonicalized in text.segments). Curated
  exclusions: vim engine internals (scans/motions/textobjs/parsing tables), events Read1/ParseGenerator. Also
  restored the surfaces/bases.py -> base.py rename that the re-nest had eaten.
- **omllm/ui/tui/minitui** (alongside bare, same bind_input/bind_output convention + own main):
  - app.py: MinituiChatApp - chatdemo's skeleton made pure-UI (no agent knowledge): stream_feed/stream_break
    (MarkdownTail commit model), begin_ai_turn/end_ai_turn headers+status, single-slot warm tool card,
    begin_permission_card, popup fed from CommandsManager command list, ctrl+d/:q quit.
  - output.py: MinituiTextDisplayer walks the shared ui.Text family (MarkdownText -> md render; DiffText ->
    MdCode('diff') through the diff highlighter; JsonText -> code-inline; Str/Concat/Style -> soft-palette
    inline segments via split_segment_lines). AgentEventRenderer: TextDelta->stream_feed, TextEnd->stream_break,
    Thinking->status, ToolExecutionStart/End->card lifecycle, TurnEnd for non-stream mode, AgentStart/End.
  - input.py: CardPermissionAsker - agn.PermissionAsker awaiting an asyncio Future resolved by the card's
    f10/f2; the turn parks on the decision while the driver keeps rendering.
  - main.py: unlike bare's blocking read loop, AsyncDriver.run(app) owns the terminal for the process lifetime;
    PromptPump runs session.prompt as queued concurrent tasks (typing-while-streaming); DriverQuitSignal stops
    the driver (terminal restore) instead of raising SystemExit through a turn; Config instance bound (the
    renderer injects it); stream defaults True.
  - backends.py: 'scripted' model option (llm.ScriptedStreamBackend, offline, no keys) - used for the pty e2e.
- **Verified**: pty end-to-end (`-m scripted`): submit -> you-header -> ai-header -> streamed markdown ->
  ctrl+d clean exit w/ protocol resets; /echo + /quit through CommandsManager/QuitSignal; permission card
  ALLOW + DENY paths headlessly (frame text + future resolution). ruff/mypy clean omllm+omxtra; omllm suite
  417 passed; minitui 204.
- Untested against a REAL streaming backend (needs keys) - owner should run `python -m omllm.ui.tui.minitui`.

## 2026-08-18 (later): -v startup crash - two AsyncDriver commit-buffering holes

Owner hit `RuntimeError: State condition not met` running the omllm minitui ui with `-v -X ...`. Static diagnosis
confirmed by pty repro with the scripted backend: (1) verbose subscriber commits on the StateUpdateEvent published
by agent.update_state during setup, BEFORE driver.run prepared the surface - InlineSurface.commit rightly refuses;
(2) fixing that exposed a second hole the fast autoexec path revealed: everything completed inside the 250ms
CPR-origin window, and stop()'s teardown dropped the still-buffered commits (all scrollback lost, silent).
Fixes (both in the library, plus ordering hygiene in the app): AsyncDriver.commit buffers when not running
(pre-run parity with AsyncTimers); run() teardown resolves origin via the fallback and flushes pending commits
before restore; omllm main starts the driver before subscribing/update_state, with the whole setup inside the
try/finally that stops the driver. Regression tests: commit-before-run buffers+flushes; stop-before-origin
flushes. e2e repro green (-v -X hello -X /quit: verbose events + response rendered, exit 0).

## 2026-08-18 (later): multiline tool output - Segment's no-newlines contract vs grep

Owner hit Segment.__post_init__ rejecting a ToolExecutionEndEvent result containing newlines (grep output). Segments
are single-line by design; the omllm backend was stuffing raw result text into one. Fixes (aa8117ad0, all
backend-side - the library contract is correct): _detail_rows() splits tool results via split_segment_lines with an
8-line cap and '(+N more lines)' tail (cards wrap rows to width already, so only newlines were the hazard);
MinituiChatApp.display_text() is the newline-safe plain-text path (split -> wrap -> single commit block) used by the
verbose renderer, command echo, and prompt-error paths; the TextDisplayer inline branch now commits multi-line
inline text as ONE block (it was emitting a blank-separated commit per line). Verified headlessly with a 14-line
grep-style result: card renders, expands with capped detail; display_text commits 3 rows + 1 blank as one block.
Both pty e2es still green.

## 2026-08-18 (later): stuck confirmation card on back-to-back tool uses - stale finalize timer

Owner report: the f10/f2 card stops responding, but only when a second tool use immediately follows the first.
Timeline diagnosis: tool_finished schedules `call_later(.8, self.finalize_card)` - capturing the SLOT, not the
card. Tool 2's ask displaces card 1 (immediate finalize) and installs card 2 CONFIRMING; 0.8s later tool 1's stale
timer fires finalize_card and commits card 2 to scrollback mid-confirmation: frozen allow/deny row in history,
self._card None so f10/f2 fall through to the textarea, the asker future never resolves, turn parked forever.
Fix (643a848ce): _finalize_card_later(card, delay) with an identity guard (`if self._card is card`) replaces the
raw call_later at both scheduling sites (tool-complete .8s, deny .6s), and begin_permission_card's respond closure
now acts only on its own captured card rather than whatever occupies the slot. Regression test drives ask->allow->
finish->ask with the stale timer fired in between (and the deny-path variant); both successor cards stay live and
confirmable. pty e2es green.

## 2026-08-18 (later): timing-hazard audit - "how many of these are we sitting on?"

Owner asked, after the second timer bug. Full sweep of every deferred/timed construct (ce660a18f):
- FOUND + FIXED: SyncDriver had BOTH AsyncDriver holes unfixed (pre-run commit -> check.state crash; stop-before-
  origin -> dropped commits). commit() buffers while `not self._running`; run() finally resolves origin fallback
  before restore. Regression tests mirror the async pair.
- FOUND + HARDENED: chatdemo's warm-window timers (`call_later(1.2, self._tool_complete)` etc.) captured the card
  SLOT - the exact pattern the omllm stuck-card bug was copied from. Now identity-guarded (`_tool_complete(card)`,
  `_finalize_card(card)` with `self._card is not card` early-outs). Reachability analysis said chatdemo was
  accidentally safe (the stream holds while a card is live), but the demo is the reference people copy.
- ASSESSED SAFE (with reasons, for the record):
  * call_every ticks (spinners, chat pump, omllm _tick): idempotent state-refresh; guarded by flags.
  * Parser escape-timeout: single-threaded dispatch; deadline re-arms only on Read1 identity change; flush
    handles cancelled in run() teardown (async) / never fire post-loop (sync). The classic ESC-then-[ 50ms
    ambiguity is inherent to the wire and bracketed paste covers the paste case.
  * Timers.fire_due: snapshot-now, cancel-safe, reschedule-from-now (no catch-up bursts); a 0-delay self-
    rescheduling callback only terminates because monotonic advances - noted as a footgun, not fixed.
  * Post-stop timer callbacks (async loop outlives driver): commit buffers harmlessly, invalidate no-ops.
  * omllm PromptPump: create_task+sleep(0) deterministically covers run()'s synchronous prologue; aclose
    cancellation propagates through a parked permission future (quit-mid-confirmation unwinds cleanly).
  * AsyncTimers re-bind on driver reuse would replay stale pending timers - driver reuse is out of contract.
Scoreboard: 4 real bugs total in this class (2 async driver, 2 sync driver) + 2 stale-slot card patterns
(omllm + chatdemo), all fixed with regression tests; everything else audited clean.
