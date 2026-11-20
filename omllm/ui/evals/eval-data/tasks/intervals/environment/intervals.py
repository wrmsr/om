import typing as ta


##


def merge_intervals(intervals: ta.Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in intervals:
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], end)
        else:
            merged.append((start, end))
    return merged
