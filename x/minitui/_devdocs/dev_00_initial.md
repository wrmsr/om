# dev 00 - initial

Running journal, standup-notes style. Newest entries appended at the bottom. When an era ends, start
`dev_01_<name>.md`.

## 2026-08-14: project start

Design conversation with the repo owner concluded; all decisions captured in `requirements.md` / `design.md` /
`research.md`. Created the package skeleton and these devdocs.

Plan of attack is phase 1 from design.md: prove the commit model end-to-end before anything else exists -
`text/` -> `screens/` -> `tty/` -> `surfaces/InlineSurface` -> vt100 emulator extension -> a fake-stream demo
runnable in a real terminal, with emulator-backed tests.

## 2026-08-14: phase 1 built and proven

The whole phase-1 chain exists and passes end-to-end:

- `text/`: `colors.py` (structured Color family + rgb->256 analytic downgrade with the greyscale branch, 256->16
  nearest-match with the saturation-excludes-greys heuristic), `styles.py` (Style + overlay merge, Theme tag
  resolution), `widths.py` (PSFL, cpython-derived char widths), `segments.py` (plain-text styled runs),
  `sgr.py` (full-reset-plus-rebuild emission, transition elision helper, ANSI->segments parse incl. 38;5/38;2).
- `screens/`: `cells.py` + `diffs.py` (both PSFL, pyrepl-derived). Dropped from pyrepl: 'controls' cells (frames are
  structured content only - deleted the whole cursor-resync complication) and the ich1/dch1 update kinds (baud-rate
  era; diff already reduces typing to a small span rewrite). Updates are uniformly move+write+maybe-EL.
- `tty/terminals.py`: raw mode (ISIG kept on for now), TIOCGWINSZ, SIGWINCH flag.
- `surfaces/`: `writers.py` (PSFL; terminfo caps with hardcoded-xterm fallbacks, bytes-buffered, no tputs delays),
  `bases.py`, `inlines.py` (greenfield - the commit model). Key mechanics that made it work:
  - All tracking relative to live origin; down-moves are literal '\r\n' (scrolls exactly when at terminal bottom).
  - `commit()` diffs committed lines against the displayed top rows (identical finalize = zero bytes), then
    re-anchors: origin += n, retained frame = old[n:].
  - Margin resync: with autowrap off the cursor pins at the last column, so any write reaching the right margin is
    followed by CR to keep tracking exact.
  - Live region must fit the terminal (`check.arg(frame.height <= term_height)`) - rows scrolled off the top would
    break relative tracking. The layout layer owns making frames fit.
  - Resize: erase live region + forget frame; next present redraws. Committed content is the terminal's problem.
- vt100 emulator (omcore, in place): rewritten - scroll-at-bottom into captured scrollback, DECAWM with proper
  *deferred* wrap + pin-when-off, DECTCEM, structured SGR colors on cells, proper CSI final-byte detection, OSC
  swallowing, feed(). Old naive parser/clamp behavior is gone; existing (trivial) tests still pass.
- Tests: `tests/harness.py` (RecordingTty + SurfaceHarness wiring surface bytes into the emulator) + 13 surface tests
  (minimal-diff assertions, zero-byte identical commit, grow-scroll, partial-commit re-anchor, style roundtrip,
  autowrap desync guard, resize, cursor visibility) + demo transcript test. Also ran the demo under a real pty
  (pty.fork + TIOCSWINSZ) and replayed its actual bytes into the emulator: full transcript lands in scrollback
  correctly; whole animated demo is ~7.8kb of output.
- `apps/streamdemo.py`: word-by-word fake stream, bounded live tail + spinner, commits paragraphs. Run it:
  `./python -m x.minitui.apps.streamdemo` (add `--visualize-redraws` to see damage regions cycle colors).

Gotchas encountered (so you don't re-learn them):
- Commit re-anchors at the *current* rows - after committing the whole live region, the next present's first line
  lands on the old bottom row; history above stays in the viewport until it scrolls naturally. Tests initially
  expected phantom blank rows.
- Demo bug found by the pty run: a final line wider than the terminal pins at the margin (autowrap off) and displays
  garbled - wrapping is strictly the content producer's job, the surface only truncates. The controls layer must
  make this impossible to get wrong.
- mypy rejects `dc.replace(x, **{dynamic: ...})` per-call; accumulate a `dict[str, ta.Any]` and replace once.

What's next (phase 2): events/ (generator escape parser, key/mouse/paste events, keymap trie -> command objects,
two-timeout model, DECRQM/kitty negotiation), runtime/ frame scheduler (coalescing invalidate), first controls
(status bar, text) + the Dimension/dock layout. Then docs/+vim/ (phase 3).

## 2026-08-14 (later): phase 2 built and proven

events/ + runtime/ + first controls/ + an interactive demo, all sync, all tested:

- `events/keys.py`: structured `Key` (base + ctrl/alt/shift/super_ flags), `parse_key('ctrl+alt+x')` specs,
  `key_from_char` (control-char normalization: 0x01-0x1a -> ctrl+letter; tab/enter/escape/backspace named),
  `key_text` (insertable text). Printables never carry shift; space is the named base 'space'.
- `events/types.py`: Event family - KeyEvent, PasteEvent, MouseEvent(+Kind), FocusEvent, ResizeEvent (runtime-
  synthesized), CursorPositionEvent, ModeReportEvent, KittyFlagsEvent, UnknownSequenceEvent (debuggability: unknown
  sequences surface as events, never silently drop).
- `events/parsing.py`: the generator-as-parser engine (textual `_parser.py` idea, reimplemented smaller). Clock-free
  cooperative timeouts: generator yields `Read1(timeout_s)`; owner calls `flush_timeout()` when time passes; tests
  call it directly = every timeout path deterministic. `pending_read` identity tells loops when a new wait began.
- `events/xterm.py`: structural decoding over big tables - CSI modifier params decoded arithmetically; letter/tilde/
  SS3 base-name tables only. Bare-ESC via 50ms `Read1` timeout; ESC ESC handled; bracketed paste bypasses the char
  machine (O(1) tail check on '~'); SGR mouse bit decode; CPR-vs-F3 ambiguity resolved by an `expect_cpr` flag armed
  when a DSR-6 is sent; DECRQM `$y` reports; kitty extended keys (u-final) incl. release swallowing.
- `events/keymaps.py`: trie matcher with explicit prefix state, `timeoutlen` semantics (bound-and-prefix waits, then
  resolves shorter binding via `flush()`), unmatched keys replay verbatim. Commands are arbitrary typed objects.
- `runtime/timers.py`: heap timers on an injectable clock; repeating timers reschedule from fire time (no catch-up
  bursts - a test initially assumed nominal-time rescheduling and was wrong).
- `runtime/drivers.py`: `SyncDriver` - poll on input fd + a self-pipe via `signal.set_wakeup_fd` (**PEP 475 makes
  poll retry EINTR, so SIGWINCH would never wake the loop without it**), utf-8 incremental decoder, parser-timeout
  deadline tracking via `pending_read` identity, coalescing `invalidate()`, `App` abstract (render(width,
  max_height) -> Frame + handle_event). On input EOF the parser timeout is flushed before stopping (else a trailing
  lone ESC is lost - a test caught this).
- `text/wraps.py`: word wrap over styled segments (space-break, hard-break for over-wide words, wrap-point
  whitespace dropped, styles preserved per char, wide-char aware).
- `controls/`: `Control` (render(width) -> rows of *segments* - semantic, theme applied at composition), Static,
  StatusBar (right-aligned when it fits, stacks when not), Spinner, `stack_frame` (vertical stack, drop-from-top
  truncation - bottom of the live region is what must stay visible).
- Surface additions: bracketed paste always on in prepare (forgetting this = no paste events); `kitty_keys` and
  `mouse` ctor opt-ins (mouse off by default per the wheel-vs-native-scrollback tension).
- `apps/inputdemo.py`: typing-while-streaming - fake ai stream commits paragraphs via timers while an EchoInput
  echoes typing, paste, and chords; enter commits your line as 'you'; status spinner + last-key display; ctrl+d
  quits. Driven under a real pty end-to-end.

**The bug of the day** (found by the pty run, invisible to unit tests): `Tty.enter_raw` didn't clear ICRNL, so the
Enter key's '\r' arrived as '\n' = ctrl+j and never submitted. pyrepl inherits this from cpython and papers over it
by binding both ctrl+j and ctrl+m to accept; we clear ICRNL/INLCR/IGNCR properly and keep the keys distinct (vim
wants ctrl+j distinct). Lesson: keep pty-level end-to-end runs in the loop - termios bugs don't exist below them.

mypy notes: it narrows attribute/property reads across mutating calls (unsoundly for our loop flags) - defeated with
tiny accessor methods (`_stopped()`) or fresh locals in tests.

What's next (phase 3): docs/ (Document, transactions, position remapping, cursors tuple) + vim/ (minivim copy-in,
reshaped: CMDLINE mode, incremental search, status()/decorations()) + a real TextArea control with the scrolled-vim-
window behavior + enter semantics (insert=newline, normal=submit, ctrl/alt+enter submit-from-insert).

## 2026-08-14 (later still): phase 3 built and proven - docs/ + vim/ + TextArea

The document layer, the reshaped vim engine, and the scrolled-vim-window TextArea, end-to-end under a pty.

- `docs/`: `positions.py` (Pos/Kind incl. reserved BLOCK/Span), `edits.py` (**TextEdit range primitive** - insert is
  start==end, delete is text=''; same shape as tree-sitter `edit()` and LSP; `AppliedEdit` carries the exact inverse;
  `remap_pos` with insert bias for cursors-vs-anchors), `documents.py` (never-empty lines; `replace()` is the single
  mutation primitive - validates, applies, bumps version, computes inverse, notifies listeners), `cursors.py`
  (Cursor tuple groundwork), `searches.py` (literal smartcase matching -> Spans; `next_match` with wrap).
- `vim/`: minivim copied in and reshaped into modules (modes/registers/scans/motions/textobjs/parsing/status/engine).
  Everything minivim had survives (**all 22 of its tests pass ported verbatim**), plus:
  - Edit-based undo *groups* replacing whole-buffer snapshots: a group opens at a change command, stays open through
    insert mode, closes on Esc - `cwfoo<Esc>` is one undo unit. Redo added (engine.redo(); ctrl+r via TextArea).
    External (non-engine) document edits invalidate history rather than corrupting it (listener sees an edit with no
    open group -> clear both stacks).
  - CMDLINE mode: `/` `?` incremental search (live decorations while typing, smartcase, wrap, n/N motions, dn works)
    and `:` with an injectable ex handler (the demo binds :q/:wq to quit). Esc in normal mode = :noh + clear message.
  - `status()` (mode/pending-keys/cmdline/message) and `decorations()` (selection + search match/current spans with
    theme tags) - the engine's only outputs besides the document.
  - '<left>'-style tokens for special keys; insert-mode arrows/home/end.
  - Cursors held as a tuple (primary first) per the multi-cursor groundwork.
- `controls/textareas.py`: the scrolled vim window. Hard-wrap at width (cell-exact, mid-word - deliberately not the
  word-wrap used for static text, so doc<->screen math stays trivial), viewport follows cursor, min 1 row growing to
  max_height then scrolling; prompt glyph with continuation indent; decoration spans -> per-char style tags -> theme.
  Enter semantics implemented as decided: insert=newline, normal=submit, ctrl/alt+enter=submit-from-insert; submit
  clears and returns to insert. Paste goes through engine.insert_text (never the key path).
- `apps/inputdemo.py` now runs the real TextArea; status bar shows spinner + vim mode/pending/cmdline + last event.
- Bug of note: `_leave_cmdline()` cleared the query before `_accept_search` read it - caught by 6 failing tests at
  once; capture-then-leave. Also mypy's property narrowing bit again in tests (fresh locals per read).
- pty end-to-end verified: type two lines (enter=newline), Esc, gg, daw edits the doc, /line searches, Enter submits
  the edited text, alt+enter submits a second message from insert - all while paragraphs stream and commit above.

State of the phase plan: 1, 2, 3 done. Next is phase 4: streaming markdown (incparse), the asyncio driver, popups/
history/suggestions -> chat-head parity. Then phase 5 (vim clone app on an AltSurface, which doesn't exist yet).

## 2026-08-14 (session cap): asyncio driver

`runtime/asyncs.py`: `AsyncDriver` - the same `App` contract as SyncDriver, hosted in an asyncio loop. This is the
deliberate asyncio isolation point (the anyio-vs-asyncio flux stops here; apps layer their own tasks above it).
- `add_reader` on the tty fd; `add_signal_handler(SIGWINCH)` (with a fallback to the tty's own signal handler when
  not on the main thread - `Tty.mark_resized()` added as the public hook since asyncio's handler *replaces* ours).
- Coalescing `invalidate()`: flag + at most one `call_soon(_render)` per loop turn (the ptk trick).
- Escape-parser timeouts via `call_later`, keyed on `pending_read` identity like the sync driver.
- `post(fn)` is the SOLE thread-safe entry point (call_soon_threadsafe); everything else is loop-affine.
- `AsyncTimers`: call_later/call_every duck-compatible with runtime.timers.Timers, and creatable *before* run - apps
  register spinners in __init__, so timers created pre-bind are held and scheduled at loop bind (a test caught this).
- Tests: dispatch+render parity with the sync driver, escape timeout, pre-run timers + cross-thread post.

Session total: phases 1-3 complete + the phase-4 async driver. 102 tests, ruff+mypy clean throughout.
Remaining for phase 4: streaming markdown control (incparse + a zero-dep fallback renderer - design conversation
worth having about scope/look), history + suggestions popup, and the app-side message registry/commit-tag hooks.
Then phase 5: AltSurface + the vim clone app.

Notes to self / near-term decisions already made:
- Style model is structured dataclasses resolved to SGR at the surface boundary; semantic tags resolved via Theme at
  render time. pyrepl's StyleRef (tag + raw-sgr string) is the seed but we go fully structured.
- screens/ files derived from pyrepl's render.py carry the PSFL header; greenfield files do not. Keep them coherent
  units (the soft barrier).
- InlineSurface cursor tracking is fully relative (ptk-style); no CPR needed in phase 1 (CPR + negotiation arrive
  with events/ in phase 2 - until then, first present() starts from wherever the cursor is, which is fine for the
  demo).
- Sync-output 2026 wrapped around every present unconditionally for now.
- vt100 emulator needs: scroll-at-bottom (it currently clamps!), scrollback capture, autowrap flag, and enough SGR to
  round-trip our styles. Extend in place in omcore, tests live here.
