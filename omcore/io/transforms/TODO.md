# TODO

- **Bounded-output / pull mode**: `feed` currently returns all resultant output eagerly, which cannot bound output size
  (think decompression bombs - a tiny fed chunk may explode into arbitrarily large output). An h11-style ingest/pull
  split (`feed` ingests, a separate bounded `pull(max_size)` extracts) should be added as a *sibling* interface, not a
  parameter on this one. Notably pump-backed transforms can support this nearly for free (emits already suspend), and
  `zlib`-style backends can via `max_length` / `unconsumed_tail`.
- Extract a `ByteStreamTransformContext` interface (from the pump's concrete class) if/when transform bodies should
  also run against real IO endpoints (asynclite-style).
- `reset()` / instance reuse, if pooling ever matters.
- Str / event-typed specializations (`StreamTransform[str, Token, R]` etc.) - candidate convergence point for
  `GenMachine`-based machines (a small adapter suffices).
