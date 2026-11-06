# Repair the incremental byte line decoder

`lines.LineDecoder` accepts arbitrary byte chunks. Its current implementation loses
partial lines and confuses byte boundaries with line boundaries.

Implement these semantics while preserving its public API:

- `feed(chunk: bytes) -> list[bytes]` emits complete lines terminated by LF (`b'\n'`).
- Remove the LF and, if immediately before that LF, one CR (`b'\r'`).
- Preserve every other byte, including lone CRs and non-ASCII bytes.
- Retain an unfinished line across calls. Empty chunks do nothing.
- Empty lines are real lines: `b'\n\n'` emits `[b'', b'']`.
- `finish() -> list[bytes]` closes the decoder. Emit an unfinished nonempty tail
  unchanged (including a trailing lone CR), but never invent an extra empty line.
- Calling `finish()` again returns `[]`. Calling `feed`, even with empty bytes,
  after `finish()` raises `ValueError`.
- Results must be independent of how the same input bytes are chunked.

Fix the implementation in `/work`. Run the existing basic checks with
`python -m unittest -v test_visible`.
