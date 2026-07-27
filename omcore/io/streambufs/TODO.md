- !! clean up util.ByteStreamBuffers !!
  - orthogonality - m_to_n
    - bytes
    - bytearray
    - memoryview
    - ByteStreamBufferLike
    - ByteStreamBufferView
    - ByteStreamBuffer
  - 'any'?
  - 'can_bytes'?
- hand optimize lol
  - segmented find/rfind multi-segment walks are still heavy - single-segment fast paths and `find_all_in_prefix`
    batch scanning cover the hot cases, but the cross-boundary comb logic remains expensive per segment
  - segmented split_to should mutate list in place
  - per-frame `DirectByteStreamBufferView` construction is the main remaining cost of batch delimiter decoding
    (positions-only scanning is ~2x faster - see `tests/bench/framers.py`)
- `import bisect` find/rfind initial segment index, `key=len`
- cext lol
  - deferred for now - `find_all_in_prefix` is the intended seam: swap the scan loop per backend, keep the pure-py
    fallback for lite/no-cext runtimes
