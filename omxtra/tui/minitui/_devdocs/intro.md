# minitui

A zero-dependency TUI library, replacing textual for this codebase's interactive terminal apps - primarily the llm
coding agent chat TUI, but built as a generalized platform for interactive-repl-y things: streaming output, text
editing, status bars, animations, dynamically updating controls.

## The one-paragraph pitch

The app's visual output is a **log plus a live tail**: committed lines are printed into the terminal's own scrollback
(immutable once emitted, tmux-native, visible after exit), while a **live region** - the bottom N lines (streaming
message tail, input textarea, status bar, popups) - is damage-diffed and redrawn in place on the main screen. No alt
screen (an alt-screen surface exists for eventual fullscreen apps, but the inline surface is the primary target). The
core is fully synchronous and deterministic; async lives only in one outer driver. No CSS, no reactive layer, no DOM,
no string-eval action dispatch - dataclasses, direct method calls, and typed command objects all the way down. Editing
is powered by a real modal vim engine operating over a headless document layer.

## Why not textual

textual is excellent but wrong for this codebase: operationally huge (~82k lines + rich's ~38k), deeply stacked
abstractions, a reactive layer that infects debugging, CSS/DOM/action-DSL dynamism that defeats IDE navigation,
blurred sync/async, per-widget message pumps prone to unbatched update storms, and - fatally - a fullscreen-first
compositor whose inline mode is a bolted-on afterthought. Its alt-screen commitment forced the previous chat TUI to
dual-write finalized messages to the main screen through a driver hack (`BackgroundTerminalRenderer` +
`render_write_from_alt`). minitui's commit model makes that behavior the foundation instead of a workaround.

## Reading order for a new worker

1. `requirements.md` - what this must do (the functionality bar extracted from the old textual chat head, plus the
   requirements added during design discussion).
2. `research.md` - prior-art intelligence: pyrepl, minivim, prompt_toolkit, textual - what we take from each.
3. `design.md` - the architecture: layers, key types, the commit model, the vim/document plan.
4. `dev_00_initial.md` onward - the running dev journal (standup-notes style; the most recent entry is the current
   state of the world).

## Ground rules (from the repo owner)

- Greenfield code, but copying wholesale from other `x/` dirs is encouraged (leave the originals unmodified).
- **Provenance is file-granular**: files that began life as pyrepl-derived code keep the PSFL license header (see
  `omcore/c3.py` for the pattern) and remain coherent units - never blend licensed code line-by-line into greenfield
  files. prompt_toolkit/textual mechanisms are *reimplemented from their described behavior*, not copied; if extraction
  is ever truly warranted, one quarantined file with the BSD-3 header.
- `omcore/term/vt100` is the one pre-approved omcore modification zone - extend it in place as the test emulator (do
  not copy it here). Any other omcore change needs explicit approval first.
- Our pure-python terminfo (`omcore.term.terminfo`) for *output* capabilities; hardcoded-xterm + runtime feature
  negotiation (DECRQM 2026/2048, kitty keyboard protocol) for *input* - the modern consensus.
- curses is never referenced at runtime; at most an optional test-only cross-validation oracle for terminfo.
- `x/` is not covered by the `make fix check` entrypoints - run manually:
  `./python -mruff check x/minitui && ./python -m mypy x/minitui`
- Follow `CODESTYLE.md` strictly (module layout, one-import-per-line, relative imports, `lang.Abstract`, `check` not
  `assert`, frozen dataclasses, blank line after docstrings, ...).
