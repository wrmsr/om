import random

from omcore import lang
from omcore.asyncs.asynclite import all as asl

from ..errors import S3FailureKind
from ..retries import S3Failure
from ..retries import SimpleS3RetryPolicy


class RecordingSleeps(asl.Sleeps):
    def __init__(self):
        super().__init__()
        self.delays = []

    async def sleep(self, delay):
        self.delays.append(delay)


def _f(attempt, kind=S3FailureKind.READ_FAILED):
    return S3Failure(op='get', attempt=attempt, kind=kind, conditional=False)


def test_backoff():
    sl = RecordingSleeps()
    p = SimpleS3RetryPolicy(sl, max_attempts=4, base_delay_s=1., max_delay_s=3., rng=random.Random(0))
    assert [lang.sync_await(p.should_retry(_f(i))) for i in range(1, 6)] == [True, True, True, False, False]
    assert len(sl.delays) == 3
    for i, d in enumerate(sl.delays, 1):
        assert 0 <= d <= min(3., 2 ** (i - 1))


def test_no_throttled():
    sl = RecordingSleeps()
    p = SimpleS3RetryPolicy(sl, no_throttled=True, rng=random.Random(0))
    assert not lang.sync_await(p.should_retry(_f(1, S3FailureKind.THROTTLED)))
    assert lang.sync_await(p.should_retry(_f(1, S3FailureKind.NOT_APPLIED)))
    assert len(sl.delays) == 1
