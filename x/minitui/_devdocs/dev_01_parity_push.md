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
- `pdcmark` (`text/pdcmarks.py`): omxtra's pulldown-cmark translation. Its `StreamingParser` contract (committed
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
