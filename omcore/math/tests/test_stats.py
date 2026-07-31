import pytest

from .. import stats


def test_statsbasic():
    st = stats.Stats(range(20))
    assert st.mean == 9.5
    assert round(st.std_dev, 2) == 5.77
    assert st.variance == 33.25
    assert st.skewness == 0
    assert round(st.kurtosis, 1) == 1.9
    assert st.median == 9.5
    print(st.get_zscore(3.))
    print(st.get_histogram_counts())
    print(st.get_histogram_counts([3, 7, 13]))


def test_empty_stats_default():
    st = stats.Stats([], default=42.)

    assert st.mean == 42.
    assert st.max == 42.
    assert st.min == 42.
    assert st.median == 42.
    assert st.variance == 42.
    assert st.std_dev == 42.
    assert st.median_abs_dev == 42.
    assert st.rel_std_dev == 42.
    assert st.skewness == 42.
    assert st.kurtosis == 42.
    assert st.iqr == 42.
    assert st.trimean == 42.

    with pytest.raises(RuntimeError):
        st.get_quantile(-.1)
    with pytest.raises(RuntimeError):
        st.get_quantile(1.1)


def test_histogram_zero_iqr():
    assert stats.Stats([1., 1., 1., 1.]).get_histogram_counts() == [(1., 4)]
    assert stats.Stats([0., 0., 0., 0., 100.]).get_histogram_counts() == [(0., 5)]


def test_trim_relative_does_not_use_data_equality_for_indexes():
    st = stats.Stats([3., 1., 2.], eq=lambda _a, _b: False)

    assert st.trim_relative(.1) is st
    assert list(st.trim_relative(.34)) == [2.]


@pytest.mark.parametrize('count', [0, -1])
def test_histogram_rejects_non_positive_bin_count(count):
    st = stats.Stats([1., 2., 3., 4.])

    with pytest.raises(RuntimeError):
        st.get_bin_bounds(count)
    with pytest.raises(RuntimeError):
        st.get_histogram_counts(count)
