# ruff: noqa: UP006 UP007 UP045
# @om-lite
import argparse
import contextlib
import typing as ta
import unittest

from ..suite import BenchmarkResult
from ..suite import _latency_stats_ms
from ..suite import _make_curl_command
from ..suite import _make_result
from ..suite import _parse_names
from ..suite import _parse_size
from ..suite import _partition
from ..suite import _percentile
from ..suite import _run_client_suite


##


class TestHttpPipelineBench(unittest.TestCase):
    @staticmethod
    def _client_suite_args(*, client_base_url: ta.Optional[str] = None) -> argparse.Namespace:
        return argparse.Namespace(
            clients='sync,urllib',
            client_base_url=client_base_url,
            nginx='nginx',
            requests=3,
            transfer_requests=2,
            warmup=1,
            concurrency=1,
            payload_size=1024,
            timeout=5.,
        )

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

    def test_managed_client_target_is_fresh_per_case(self) -> None:
        events: ta.List[ta.Tuple[str, str]] = []
        active: ta.Set[str] = set()
        next_target = 0

        @contextlib.contextmanager
        def target() -> ta.Iterator[str]:
            nonlocal next_target
            next_target += 1
            base_url = f'http://target-{next_target}'
            events.append(('enter', base_url))
            active.add(base_url)
            try:
                yield base_url
            finally:
                active.remove(base_url)
                events.append(('exit', base_url))

        def run_case(**kwargs: ta.Any) -> BenchmarkResult:
            base_url = kwargs['base_url']
            self.assertIn(base_url, active)
            events.append(('run', base_url))
            return BenchmarkResult(
                suite='client',
                implementation=kwargs['implementation'],
                scenario=kwargs['scenario'],
            )

        results = _run_client_suite(
            self._client_suite_args(),
            ('requests', 'download'),
            target_factory=target,
            case_runner=run_case,
        )

        self.assertEqual(len(results), 4)
        self.assertEqual(events, [
            ('enter', 'http://target-1'),
            ('run', 'http://target-1'),
            ('exit', 'http://target-1'),
            ('enter', 'http://target-2'),
            ('run', 'http://target-2'),
            ('exit', 'http://target-2'),
            ('enter', 'http://target-3'),
            ('run', 'http://target-3'),
            ('exit', 'http://target-3'),
            ('enter', 'http://target-4'),
            ('run', 'http://target-4'),
            ('exit', 'http://target-4'),
        ])

    def test_external_client_target_is_reused(self) -> None:
        base_urls: ta.List[str] = []

        def run_case(**kwargs: ta.Any) -> BenchmarkResult:
            base_urls.append(kwargs['base_url'])
            return BenchmarkResult(
                suite='client',
                implementation=kwargs['implementation'],
                scenario=kwargs['scenario'],
            )

        args = self._client_suite_args(client_base_url='http://example.test:8080/')
        args.clients = 'sync'
        results = _run_client_suite(
            args,
            ('requests', 'download'),
            case_runner=run_case,
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(base_urls, [
            'http://example.test:8080',
            'http://example.test:8080',
        ])


if __name__ == '__main__':
    unittest.main()
