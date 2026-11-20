import typing as ta


##


def merge_intervals(intervals: ta.Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    nonempty: list[tuple[int, int]] = []
    for start, end in intervals:
        if start > end:
            raise ValueError((start, end))
        if start != end:
            nonempty.append((start, end))

    merged: list[tuple[int, int]] = []
    for start, end in sorted(nonempty):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged
