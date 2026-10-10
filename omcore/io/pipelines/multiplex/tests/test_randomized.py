# @om-lite
import unittest

from .randomized import run_churn
from .randomized import run_session


##


class TestRandomizedMultiplexSessions(unittest.TestCase):
    def test_long_lived_connection_with_stream_resets(self):
        for tls in (False, True):
            with self.subTest(tls=tls):
                run_churn(self, 1, tls=tls)

    def test_fragmented_sessions(self):
        for protocol in ('h2', 'ssh'):
            for seed in range(6):
                with self.subTest(protocol=protocol, seed=seed):
                    run_session(self, seed, protocol=protocol)

    def test_fragmented_sessions_over_tls(self):
        for protocol in ('h2', 'ssh'):
            for seed in (2, 4):
                with self.subTest(protocol=protocol, seed=seed):
                    run_session(self, seed, protocol=protocol, tls=True)
