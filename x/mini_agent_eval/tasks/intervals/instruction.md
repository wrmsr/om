# Merge half-open intervals

`intervals.merge_intervals` should return the sorted union of integer half-open intervals.
It currently mishandles unsorted input, nesting, adjacent intervals, and empty intervals.

Requirements:

- Accept any iterable of `(start, end)` integer pairs.
- Discard empty intervals (`start == end`).
- Reject any reversed interval (`start > end`) with `ValueError`.
- Merge overlaps and touching boundaries, including transitively.
- Return a new `list[tuple[int, int]]`, sorted by start, with no empty intervals.
- Do not mutate the caller's data.

For example, `[(5, 8), (1, 3), (3, 6), (9, 9)]` should become `[(1, 8)]`.
Fix the implementation in `/work`. You can run `python -m unittest -v test_visible`.
