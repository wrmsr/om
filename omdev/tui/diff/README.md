# Styled diff renderer

This package renders `omdev.diffs` patch trees into fixed-width, target-neutral `omcore.text.styled.StyledDocument`
values. The document preserves the former Rich renderer's split layout, line alignment, syntax coloring, intraline
highlights, file summaries, and special-file bodies without importing Rich or requiring a terminal.

`render_diff_document()` is the reusable presentation boundary. Its result can go through the shared plain or HTML
renderers. `render_diff_ansi()` is the terminal adapter; it resolves the diff theme through `omcore.term.styled` and
emits a complete ANSI string synchronously, without a screen, surface, driver, or event loop.
