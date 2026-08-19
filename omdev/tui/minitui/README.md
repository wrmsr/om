# minitui

A zero-dependency TUI library built around being a good terminal citizen: app output is a **log plus a live tail**.
Finalized content commits into the terminal's own scrollback (native scrolling, tmux-friendly, survives exit); only the
bottom few rows - the streaming tail, a vim-powered input, a status bar - are retained-frame diffed and redrawn in place
on the main screen. No alternate screen required (one exists for genuinely-fullscreen apps), no CSS, no reactive layer,
no DOM, no string-eval dispatch: dataclasses, direct calls, and typed events throughout.

Built primarily for llm coding-agent chat TUIs, deliberately generalized for any interactive-repl-ish thing.

## Try it

```bash
./python -m omdev.tui.minitui.apps.chatdemo               # streaming markdown chat: tool cards (f10/f2), /help, history, search
./python -m omdev.tui.minitui.apps.chatdemo --md=pdcmark  # swap the streaming markdown backend (internal|pdcmark|markdown-it)
./python -m omdev.tui.minitui.apps.chatdemo --mouse       # + click-to-expand cards / click suggestions (trades wheel scrollback)
./python -m omdev.tui.minitui.apps.inputdemo              # minimal typing-while-streaming proof
./python -m omdev.tui.minitui.apps.streamdemo             # the bare commit model, no input
./python -m omdev.tui.minitui.apps.vimdemo f.py           # fullscreen vim clone (:w/:q, ctrl+v blocks, %/~/zz), tree-sitter highlighted
```

Run them in tmux and scroll back; add `--visualize-redraws` to streamdemo to watch damage regions.

## Architecture (dependencies point strictly inward)

    apps -> runtime -> controls -> { surfaces, events, docs+vim } -> screens -> text

- **text/** - structured `Style`/`Color` (+ depth downgrade), styled segments, word wrap, width measurement, SGR
  emit/parse, streaming markdown with swappable backends (zero-dep internal / omcore pdcmark / markdown-it) over a
  shared block model, the `Highlighter` protocol with python (stdlib tokenize) and diff highlighters.
- **screens/** - `Cell`/`Line`/`Frame` and retained-frame diffing: the correctness ground truth. Spurious redraws cost a
  re-render and an empty diff, never visible output.
- **surfaces/** - `InlineSurface` (the commit model: relative cursor tracking, `\r\n`-forced scrolling, commit-above
  re-anchoring, CPR origin negotiation) and `AltSurface` (fullscreen, absolute addressing). Terminfo for output
  capabilities; hardcoded-xterm fallbacks; runtime-negotiated extras (kitty keys, bracketed paste, sync output).
- **events/** - typed `Key`/events, a generator escape-sequence parser with clock-free cooperative timeouts, keymap trie
  with vim's two-timeout semantics, SGR mouse / CPR / DECRQM / kitty decoding.
- **docs/** - `Document` mutated only through range edits (`TextEdit`, tree-sitter/LSP-shaped) carrying exact inverses;
  position remapping; cursor-tuple groundwork for multi-cursor; smartcase search; the incremental highlighter protocol
  with the (optional, quarantined) tree-sitter implementation riding those same edits.
- **vim/** - the modal engine (grown from `x/vibes/minivim`): motions/operators/text objects/registers, edit-group
  undo/redo, CMDLINE mode with incremental search, blockwise visual (ctrl+v) with live multi-cursor I/A/c replication,
  `%`/`~`, `status()`/`decorations()` as its only outputs. Never renders, never reads a keyboard.
- **controls/** - small and passive: `TextArea` (a scrolled vim window - grows to a max height, then the viewport
  follows the cursor; optional syntax highlighting under engine decorations; ctrl+d/u, zz/zt/zb, H/M/L viewport ops),
  status bar, statics, spinner, suggestions popup, markdown tail, lifecycle cards, input history, stack layout with
  mouse hit regions.
- **runtime/** - `SyncDriver` (poll + self-pipe) and `AsyncDriver` (asyncio; `post()` is the sole thread-safe entry).
  Both share the `App` contract: `render(width, max_height) -> Frame` + `handle_event(event)`, with coalescing
  invalidation.

## Notes

- `_devdocs/` holds the design docs and the running dev journal - read `intro.md` first.
- Files with PSF license headers derive from cpython via `x/term/pyrepl`; they stay coherent units.
- Tests run against the `omcore.term.vt100` emulator (screen + scrollback assertions on real emitted bytes) plus
  pty-level end-to-end runs of the demo apps.
