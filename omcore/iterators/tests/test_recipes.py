from ..recipes import sliding_window


def test_sliding_window():
    assert list(sliding_window(iter(range(5)), 3)) == [
        (0, 1, 2),
        (1, 2, 3),
        (2, 3, 4),
    ]
    assert list(sliding_window(range(3), 1)) == [(0,), (1,), (2,)]
    assert list(sliding_window(range(2), 3)) == []
