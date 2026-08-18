# Research / prior art

Four sources: two in-repo (pyrepl, minivim), two external (prompt_toolkit 3.0.53, textual 8.2.8 + rich 15.0.0, both
readable in `.venv`). This file is the distilled intelligence; go read the actual sources when implementing.

## In-repo: x/term/pyrepl (cpython pyrepl extraction, de-pythonized; PSFL)

The closest thing to minitui's rendering core that already exists. Pipeline, all immutable dataclasses:

    buffer -> SourceLine -> ContentLine (prompt + styled fragments)     [content.py]
           -> width-wrap -> WrappedRow + LayoutMap (pos<->xy)           [layout.py]
           -> RenderCell / RenderLine / RenderedScreen (+ overlays)     [render.py]
           -> diff_render_lines -> LineDiff                             [render.py]
           -> UnixRefreshPlan -> LineUpdate (insert_char / replace_char / replace_span /
              delete_then_insert / rewrite_suffix) -> terminfo writes   [unix/console.py]

Key mechanisms to carry forward:
- **Retained-frame line diff** (recent addition upstream, thanks pablo): prefix/suffix cell trim, extended to include
  trailing zero-width combining chars; stop at cells with non-SGR controls (cursor may have moved).
- `RefreshInvalidation` - a damage taxonomy (cursor_only / buffer_from_pos / prompt / layout / theme / message /
  overlay / full) with monotonic combination. `RefreshCache` - incremental relayout from the first changed buffer pos.
- Movement planning: relative moves (`cub/cuf/cuu/cud`) while content fits the viewport, switch to absolute `cup`
  ("gone tall") when it exceeds; hardware scroll via `ri`/`ind`.
- `visualize_redraws` debug mode: cycle background colors per refresh to *see* damage regions.
- `ScriptedConsole` test harness: scripted events in, rendered screens out, no tty.
- Eventqueue: terminfo-driven input trie (we are *replacing* this approach for input - see below - but the
  trie/compile_keymap shape is reused for the keymap layer).
- Sharp edges observed: paste goes through the char-by-char keymap (slow); ESC resolved eagerly (no timeout model);
  single-widget by construction (Reader owns buffer+prompt+overlays).

## In-repo: x/vibes/minivim

A ~1.3k-line modal vim engine, rendering-free, protocol-driven. Architecture (mirrors real vim):

    keys -> Parser (modal state machine, operator-pending is parser state)
         -> Command dataclass ["reg][count]{op[count]}{motion|textobj}|action
         -> eval_motion -> MotionResult(target, Kind: EXCLUSIVE/INCLUSIVE/LINEWISE)
         -> resolve(start, MotionResult) -> Span   (vim's `:help exclusive` adjustment rules)
         -> operators d/c/y/>/< edit via the 5-method Buffer protocol, write typed registers

Dot-repeat is a keystroke recorder/replayer (vim's redo buffer). curswant handled. Synonyms (x=dl, D=d$, ...) compile
to op+motion. Text objects (iw/aw, pairs, quotes) yield Spans directly. Linear snapshot undo.
This is the engine to grow (see requirements.md); its `resolve()` shape is structurally closer to real vim than ptk's
cursor-relative TextObject, at half the size.

## prompt_toolkit (41.6k lines, self-contained; BSD-3)

**The gold standard for inline rendering** (`renderer.py`, 821 lines; `layout/screen.py`, 324 (!) lines).
- Screen: sparse `defaultdict[int, defaultdict[int, Char]]`, `(char, style)` interned in a 1M-entry cache. Fresh
  Screen every frame; **cell-level diff against the retained previous screen**. Trailing unstyled whitespace trimmed
  via a "does this style paint anything" cache; shrinking lines use erase-to-EOL instead of painting spaces.
- **All cursor state is layout-relative** (origin = top of the app's block). Erase = cursor_backward(x) +
  cursor_up(y) + erase_down().
- **Downward motion is `"\r\n" * n`, never CUD** - CUD can't create lines at the terminal bottom; `\r\n` forces the
  scroll. This single trick is what makes a growing inline app consistent.
- Height rule: `max(min_available_height, last_height, preferred)` - never shrink mid-session (we deliberately
  diverge: our commit model requires shrink; we erase-down + hysteresis instead).
- Bottom-space negotiation via **CPR** (`\x1b[6n`) with 2s timeout and a tri-state SUPPORTED/NOT_SUPPORTED/UNKNOWN
  enum; response arrives through the input parser as a pseudo-key. Autowrap disabled whenever not fullscreen.
- `patch_stdout` / `run_in_terminal`: erase UI -> detach input -> cooked mode -> let output happen -> re-CPR ->
  redraw. The correct solution for interleaving normal output above a live prompt.
- Style write elision: compare style identity first, then resolved attrs (different styles can render identically).
  SGR emission is always full-reset-plus-rebuild (`\x1b[0;...m`) - simple, correct.
- Input: hardcoded xterm table (~255 entries) + generator state machine with longest-match backtracking; explicit
  docstring rejecting terminfo for input. Bracketed paste bypasses the char machine entirely.
- **Two separate timeouts** (vim's model): `ttimeoutlen` flushes the escape parser (bare-ESC disambiguation),
  `timeoutlen` flushes the keymap prefix matcher. Conflating them is a classic bug.
- Update-storm defense is ten lines: `invalidate()` sets a flag and returns if already set; one
  call_soon_threadsafe'd redraw with max-postpone.
- Layout: Container/Window/UIControl split; `Dimension(min,max,weight,preferred)` with `*_specified` flags
  (distinguishing unset from default kills a class of bugs); distribution is one-cell-at-a-time weighted round-robin
  (~20 lines, exact, no rounding artifacts - terminal dims are small).
- Vim layer ~3.8k lines incl. a 1.4k digraph table; separable. Its immutable `Document` (1,183 lines of pure text
  algorithms: word boundaries, bracket matching, row/col<->index) is the *checklist* for our docs layer - built from
  scratch here, never copied.

## textual 8.2.8 + rich 15 (~121k lines effective)

- No retained framebuffer at all - correctness rests entirely on upstream region-level dirty tracking (three tiers:
  widget `_dirty_regions`, StylesCache dirty lines, compositor dirty regions -> merged spans). Fast, but no safety
  net: this is where its update storms and debugging pain live. We invert this: retained diff = ground truth.
- The "cuts + chops" compositor: per line, x-coordinates of all widget boundaries; strips divided at cuts; walked
  front-to-back, first-writer-wins (occlusion culling without a z-buffer). Clever; we don't need it (no overlapping
  widget z-stack beyond simple popup overlays).
- **Inline mode is a bolted-on afterthought** - the cautionary tale: POSIX-only, writes to stderr, disables ALL
  dirty-region optimization (full repaint per frame + CUU back up), never disables autowrap (width-exact lines can
  wrap and desync the cursor math), `\x1b[2J` on resize (nukes scrollback view), post-frame CPR with no
  timeout/fallback (exists only to translate mouse coords).
- Worth reimplementing:
  - `textual/_parser.py` (126 lines): generator-as-parser - the parser coroutine yields `Read1(timeout)` requests;
    driver feeds chars; timeouts via `gen.throw(ParseTimeout())`. Elegant; our escape parser uses this shape.
  - The `Visual` measurement protocol: `get_minimal_width` / `get_optimal_width` / `get_height(width)` -
    min-content, max-content, height-for-width. Exactly the right control-measurement contract.
  - Message coalescing via `can_replace` (resize bursts collapse); kitty keyboard protocol support
    (`\x1b[>1u`, `_keyboard_protocol.py` tables); DECRQM feature negotiation (`?2026$p` sync output, `?2048$p`
    in-band resize); SGR-mouse parse incl. the bit decode table.
  - rich's analytic truecolor->256 downgrade (greyscale branch at saturation < 0.15, non-linear 6x6x6 cube ramp) -
    better than naive division; 256->16 via nearest-match over a real palette table.
- Neither library uses terminfo for anything. Both hardcode xterm + negotiate features at runtime. (We keep our
  pure-python terminfo for *output* since it exists and costs nothing; input follows the consensus.)

## pi-mono (static knowledge)

Its internal ui layer is the "commit model" existence proof: components render to lines, a differ diffs against the
previous frame bottom-up, finalized content is printed above the live region and left to the terminal's scrollback.
Keyboard-first, no wheel capture. minitui aims for equivalent functionality, not a clone.
