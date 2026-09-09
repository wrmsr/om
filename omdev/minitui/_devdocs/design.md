# Design

## Package layout

    omdev/tui/minitui/
      text/        adapter from omcore.text.styled into terminal segments/lines; terminal-only
                   named/indexed colors, width measurement, SGR emit/parse, color downgrade
      screens/     Cell/Line/Frame, retained-frame line diff, update planning        [pyrepl-derived, PSFL]
      surfaces/    Surface abstract; InlineSurface (live region + commit-above);
                   AltSurface; terminfo write layer                                  [writer PSFL-derived]
      events/      typed events; generator-parser engine; xterm tables; keymap trie ->
                   bound command objects; two-timeout model; feature negotiation
      tty/         termios/raw-mode state, fd plumbing, SIGWINCH
      docs/        Document: transactions, position remapping, change events, cursor
                   sets, search/match machinery (the shared headless layer)
      vim/         the modal engine: parser/motions/operators/registers/modes,
                   status()/decorations(), View protocol                             [seeded from minivim copy-in]
      controls/    Control base (min/optimal width + height-for-width), dock/flex
                   layout, text, TextArea, status bar, spinner, popups, markdown stream
      runtime/     frame scheduler (coalescing invalidate), sync loop, asyncio driver
      apps/        demos: streaming chat skeleton; later the tiny vim clone
      tests/       vt100-emulator harness, scripted surfaces, terminfo cross-validation

Dependency direction (strictly inward): apps -> runtime -> controls -> {surfaces, events, docs+vim} -> screens ->
text -> `omcore.text.styled`. `docs/` and `vim/` import nothing from surfaces/controls - rendering-agnosticism enforced
by import direction.

## The commit model (the core idea)

Terminal viewport = [...native scrollback... | committed tail | LIVE REGION]. The live region is the bottom K rows of
our output; we retain its Frame and our cursor position *relative to its origin* (ptk-style - no absolute coordinates
anywhere).

- **present(frame)**: diff against retained frame, emit minimal updates. Growth: move to last row, `"\r\n" * n`
  (forces terminal scroll at the bottom); shrink: redraw + erase-down (divergence from ptk's never-shrink: commits
  make shrink routine; hysteresis avoids grow/shrink jitter).
- **commit(lines)**: draw the committed lines over the top rows of the live region (diffed against what's displayed
  there - a message that finalizes exactly as displayed costs zero bytes), then re-anchor: origin moves down
  len(lines), retained frame becomes old_frame[len(lines):]. Committed lines are never touched again; the terminal
  owns them (scrollback, resize-rewrap, copy/paste, exit visibility).
- Resize: full redraw of the live region only. Committed content is the terminal's problem (native behavior).
- Frames are wrapped in synchronized-output (DECSET 2026) - unconditionally for now, negotiated once events/ lands.
- Autowrap disabled while active (prevents width-exact lines desyncing relative cursor tracking).
- App-level message identity flows through a commit hook (commit records carry opaque app tags) - this is the
  unsealed door to a future browse mode; minitui itself never retains committed content.

## Rendering data model

- `omcore.text.styled`: owns target-neutral `RgbColor`, tri-state `StylePatch`, concrete `ResolvedStyle`, semantic
  `StyleName`/`StyleTheme`, immutable overlapping-span `StyledText`, and row-structured `StyledDocument`.
- `text.styles`: a compatibility facade (`Style` is `ResolvedStyle`) and minitui `Theme` adapter. Theme definitions are
  patches, so layered spans can explicitly disable attributes or clear colors; legacy concrete `Style` entries remain
  accepted. Controls emit semantic tags rather than colors wherever reasonable.
- `omcore.term.styled`: owns the terminal-specific named-16/indexed-256 colors, color-depth downgrade, SGR emit/parse,
  and headless ANSI rendering of styled text and documents; RGB is the shared `omcore.text.styled` type.
  `styled_text_to_segment_lines` resolves and splits a `StyledText` synchronously; `render_ansi_segments` renders
  segment rows. Segments -> cells -> SGR is entirely driver-free; drivers add lifecycle, input, scheduling, and
  terminal commits.
- `screens.Cell`: grapheme cluster + display width + resolved Style. `screens.Line`: tuple of cells (+ cached
  rendered string). `screens.Frame`: tuple of lines + cursor xy + cursor visibility.
- Diff: per-line prefix/suffix trim with combining-char extension (pyrepl-derived), producing typed updates consumed
  by the surface's write planner. Retained-frame diff is the *ground truth*; control-level damage only skips
  re-rendering, never skips diffing.

## Controls & layout (phase 2+)

- `Control`: `measure()` -> min/optimal width; `height(width)` -> height-for-width; `render(width, height)` ->
  lines; `handle(event)`; `invalidate()`. (The textual Visual trio, without the rest of textual.)
- Layout: vertical dock stack for the live region (messages tail / input / status), `Dimension(min, max, weight,
  preferred)` with specified-flags, one-cell-at-a-time weighted distribution (ptk's algorithm, ~20 lines).
- Overlays (suggestion popups) composite over the frame post-layout (generalized pyrepl ScreenOverlay).
- Mouse: a per-frame hit-region map (control + region + handler); click-only.

## Documents & vim (phase 3)

- `docs.Document`: lines storage behind minivim's 5-method Buffer protocol; **all mutation via transactions**
  (ordered atomic edits) producing change events; **position remapping through edits** - the load-bearing wall for
  multi-cursor (N edits, N-1 cursors adjusted), durable match/highlight spans, precise renderer damage, undo units,
  and tree-sitter's `edit()` API shape.
- Cursor state: `cursors: tuple[Cursor, ...]` primary-first from day one (single-cursor code uses cursors[0]).
  `SpanKind` reserves BLOCK for blockwise visual.
- Engine feedback: `status()` (mode, pending keys, count, register, cmdline) + `decorations()` (tagged spans:
  selection, search matches) + optional injected `View` (viewport dims/offset) for ctrl-d/zz.
- CMDLINE mode for `/` `?` `:` with incremental search recompute per keystroke -> decorations -> frame damage.
- The input textarea is a scrolled vim window: viewport follows cursor, grows to max-height then scrolls.
- Enter semantics: insert=newline, normal=submit, ctrl/alt+enter=submit-from-insert.

## Highlighting (groundwork now, features later)

- Rendered line = document text + merged `StyleSpan`s from N producers with priorities: syntax < selection < search
  < current-match (tunable). Same pipeline for static code blocks and editable textareas.
- `Highlighter` protocol: `highlight(document) -> spans` + `update(change) -> spans` (incremental). Zero-dep impls:
  python (stdlib tokenize), diff. Optional quarantined: pygments, tree-sitter (the incremental path; Document change
  events translate directly).
- Streaming markdown: `omdev/markdown/incparse.py` stable/unstable split maps onto commit/live - new_stable renders
  and commits; unstable re-renders per frame (code-block tails re-lexed per frame is acceptable).

## Runtime (phases 2/4)

- Frame scheduler: coalescing `invalidate()` (flag + single scheduled render, max-postpone), one render per tick max.
- Sync loop for simple apps; asyncio driver for the chat case: `add_reader` on the tty fd, a thread-safe op queue as
  the *sole* cross-thread/task entry, timer wheel for spinners/animation.
- Two-timeout input model: escape-parser flush (`ttimeoutlen`-alike) vs keymap-prefix flush (`timeoutlen`-alike).

## Testing

- `omcore/term/vt100` (extended in place, pre-approved) is the oracle: feed the surface's actual byte output into the
  emulator; assert viewport contents, cursor, and **scrollback** (commit correctness is a scrollback assertion).
- Scripted surfaces/consoles for control/runtime tests without a tty; deterministic, no sleeps, parallel-safe.
- Optional curses cross-validation of terminfo (skipped when curses unavailable), boto-pattern.

## Phase plan

1. text + screens + tty + InlineSurface + vt100 extension + streaming demo  <- the differentiator, proven first
2. events (parser/keymaps/negotiation) + runtime scheduler + first controls (status, text)
3. docs + vim (copy-in, reshape onto Document/cursors/decorations) + TextArea + emacs command set
4. markdown streaming + asyncio driver + popups/history -> chat-head parity
5. apps/ vim clone on AltSurface
