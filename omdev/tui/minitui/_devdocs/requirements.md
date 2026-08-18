# Requirements

## Primary use case

The llm coding agent chat TUI (the `ommlds` chat head, being rebuilt on the new minichain). minitui must not couple to
it, but its needs define the bar. Secondary: a generalized platform for other interactive-repl-y apps, and eventually a
tiny fullscreen vim clone demo app.

## Functionality bar (extracted from the old textual chat head, `x/ommlds/cli/chat/interfaces/textual`)

- **Streaming markdown messages**: append-only content stream into a message, then finalize (re-render final form).
  States: new / streaming / finalized.
- **Tool cards**: a single updatable widget following one tool use through its lifecycle
  (streaming/pending/running/complete/confirming/denied/failed), expandable inner content while warm.
- **Tool confirmations**: block on a future resolved by keyboard (allow-all / deny-all bindings) or click while warm.
- **Input**: multi-line text entry, history (prev/next), slash-command suggestions popup with tab cycling, mode glyph.
- **Status bar**: spinner while active, driver state display; now also vim mode/pending-keys display.
- **Global bindings**: cancel (esc), suspend (ctrl-z), quit; app-defined commands.
- **Finalized content must reach the terminal's main-screen scrollback** - in textual this was a driver hack; here it
  is the core commit model.
- Batched display updates (the old head funneled all mutation through one ordered async relay to fight update storms -
  minitui's frame scheduler makes this native).
- Clipboard actions on messages (deferred to app-level slash commands over a message registry, since committed content
  is dead - e.g. `/pbcopy -plain <message-number>`, with visible message numbers).
- Exception display as messages.

## Decisions from the design discussion (2026-08)

- **99% all-in on dead scrollback** (commit model). Browse mode (an alt-screen viewer over app-retained message
  records) is a possible future avenue; never design so as to "seal the tomb" on it, but no placeholders needed.
  Commits carry app-assigned identity via a hook; a future browse mode replays app records, never scrapes emitted ANSI.
- **Mouse**: click-only, live-region only, designed to be cleanly absent. No wheel capture (preserves native terminal
  scrollback). SGR mouse mode.
- **Retained-frame diff is the correctness ground truth**; widget-level damage is only a render-skipping optimization.
  Spurious invalidations must be cheap (re-render + empty diff), not visible.
- **Sync core, async rind**: everything inside (text, layout, controls, diff, vim engine) is synchronous and
  single-threaded, driven by an explicit frame loop. One asyncio outer driver: fd reader, thread-safe op queue (the
  sole thread-safe entry point), coalescing invalidate, timers. Freethreaded (3.14t) kept in mind for the queue.
- **Input textarea = a scrolled vim window**: full width, min height 1, grows with content to a max-height knob
  (default ~1/3 of terminal height), then scrolls like a vim viewport - all pasted content motion/search-accessible,
  never `[123 additional lines]` truncation. Keyboard-only scrolling (no wheel).
- **Vim always-on for input, starting in INSERT mode.** Enter semantics: insert mode Enter = newline (vim-pure);
  normal mode Enter = submit; ctrl+enter or alt+enter = submit from insert mode (ctrl+enter needs kitty protocol;
  alt+enter is the universal fallback). The emacs-ish command set (pyrepl's) remains a configurable alternative.
- **Vim scope is per-document**: search/motions operate only within the focused textarea's document.
- **Elastic status bar**: readonly, not focusable, grows to multiple lines via height-for-width.
- **Warm-window expand/collapse**: live-region messages can re-render freely; shrink policy = explicit erase-down +
  hysteresis against grow/shrink jitter. Once committed (possibly truncated), rendering is dead; full content via
  app-level commands only.

## Styled output & highlighting (mid-term, groundwork from day one)

- Render pipeline is style-span-first everywhere: rendered line = text + merged style spans from N producers
  (syntax highlighter, search matches, selection, semantic decorations) with a priority order. Static code blocks and
  editable textareas share this pipeline.
- `Highlighter` protocol: full highlight (document -> spans) + incremental update (change event -> damage-limited
  spans). Document's transaction/change-event model is deliberately shaped to translate directly to tree-sitter's
  `edit()` API.
- Internal zero-dep highlighters: python (stdlib tokenize), diffs. Optional quarantined deps: pygments (the catalog),
  tree-sitter (the incremental big boy - "spiritual carveout" from day one, integration later). Streaming highlight of
  a code block's unstable tail is desirable (re-lex per frame is acceptable).
- Colorized *editable* textareas are not an immediate goal but must not require rearchitecting.

## Vim engine growth path (greenfielded from x/vibes/minivim, copied in)

- Rendering-agnostic forever; grows pure-data feedback surfaces instead:
  - `status()` -> mode, pending keys, count, register, command-line contents.
  - `decorations()` -> semantically-tagged spans (visual selection, search matches, current vs other match).
  - Optional injected `View` protocol (viewport dims, scroll offset) for ctrl-d/zz-class motions.
- `/` `?` `:` become a real CMDLINE mode with realtime incremental search + match highlighting.
- Command subsystem: ex-style `:` grammar in the engine (vim-clone use case); chat slash commands stay app-level.
- **Multi-cursor + blockwise (box) selection: baked-in data-model support from day one** even if features land much
  later: `cursors: tuple[Cursor, ...]` (primary first), edits as transactions with position remapping, `Kind.BLOCK`
  reserved.
- Operator garden must grow toward prompt_toolkit's coverage (its `Document` is the checklist; built from scratch, not
  copied - frankenstein-ing ptk/textual ecosystems has repeatedly proven disgusting).
- minivim must eventually power a "full-ish" tiny fullscreen vim clone (`apps/`), sharing the headless document layer.

## Non-goals

- Windows support (per CODESTYLE; POSIX only).
- CSS, themes-as-stylesheets, reactive attributes, per-widget message pumps, DOM queries.
- Wheel/hover/drag mouse interactions.
- Being a widget zoo. Small control set, apps compose.
