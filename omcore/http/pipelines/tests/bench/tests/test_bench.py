# ruff: noqa: UP006 UP007 UP045
# @om-lite
import unittest

from ..bench import _latency_stats_ms
from ..bench import _make_curl_command
from ..bench import _make_result
from ..bench import _parse_names
from ..bench import _parse_size
from ..bench import _partition
from ..bench import _percentile


##


class TestHttpPipelineBench(unittest.TestCase):
    def test_percentiles(self) -> None:
        values = [1., 2., 3., 4.]
        self.assertEqual(_percentile(values, 0.), 1.)
        self.assertEqual(_percentile(values, .5), 2.5)
        self.assertEqual(_percentile(values, 1.), 4.)

        stats = _latency_stats_ms([1_000_000, 2_000_000, 3_000_000])
        self.assertEqual(stats['mean'], 2.)
        self.assertEqual(stats['p50'], 2.)

    def test_parsing_and_partitioning(self) -> None:
        self.assertEqual(_parse_size('1.5MiB'), 1572864)
        self.assertEqual(_parse_size('64k'), 65536)
        self.assertEqual(_parse_names('sync,fdio', ('sync', 'asyncio', 'fdio')), ('sync', 'fdio'))

        self.assertEqual(_partition(10, 3), [4, 3, 3])
        self.assertEqual(_partition(2, 8), [1, 1])

    def test_result_rates(self) -> None:
        result = _make_result(
            suite='client',
            implementation='test',
            scenario='download',
            requests=2,
            concurrency=1,
            elapsed_s=.5,
            transferred_bytes=1024,
            latencies_ns=[1_000_000, 3_000_000],
            rss_before_bytes=100,
            peak_rss_bytes=140,
        )
        self.assertEqual(result.requests_per_s, 4.)
        self.assertEqual(result.bytes_per_s, 2048.)
        self.assertEqual(result.rss_growth_bytes, 40)
        latency_ms = result.latency_ms
        assert latency_ms is not None
        self.assertEqual(latency_ms['p50'], 2.)

    def test_curl_command_has_one_output_per_url(self) -> None:
        command = _make_curl_command(
            '/usr/bin/curl',
            'http://127.0.0.1:8080/download',
            'download',
            3,
            'payload.bin',
            5.,
        )
        self.assertEqual(command.count('--output'), 3)
        self.assertEqual(command.count('http://127.0.0.1:8080/download'), 3)
        self.assertIn('OMCORE_BENCH %{http_code}', command[command.index('--write-out') + 1])


if __name__ == '__main__':
    unittest.main()
