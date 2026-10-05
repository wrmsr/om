"""
Retry policies. The store itself never retries or sleeps: with no policy, every failure is raised immediately with its
blob error type. A policy is offered every retryable failure - except ambiguous failures of conditional writes, which
are never offered, and always raise BlobIndeterminateError: a retry of a conditional write that did land would fail its
precondition against itself.
"""
import abc
import random
import typing as ta

from omcore import dataclasses as dc
from omcore import lang
from omcore.asyncs.asynclite import all as asl

from .errors import S3FailureKind


##


@dc.dataclass(frozen=True, kw_only=True)
class S3Failure:
    op: str
    attempt: int  # 1-based
    kind: S3FailureKind
    conditional: bool
    status: int | None = None
    code: str | None = None
    cause: BaseException | None = None


class S3RetryPolicy(lang.Abstract):
    @abc.abstractmethod
    def should_retry(self, failure: S3Failure) -> ta.Awaitable[bool]:
        """May sleep before returning True."""

        raise NotImplementedError


class SimpleS3RetryPolicy(S3RetryPolicy):
    """Retries whatever it is offered, with full-jitter exponential backoff, up to max_attempts total attempts."""

    def __init__(
            self,
            sleeps: asl.Sleeps,
            *,
            max_attempts: int = 5,
            base_delay_s: float = .05,
            max_delay_s: float = 2.,
            rng: random.Random | None = None,
            no_throttled: bool = False,
    ) -> None:
        super().__init__()

        self._sleeps = sleeps
        self._max_attempts = max_attempts
        self._base_delay_s = base_delay_s
        self._max_delay_s = max_delay_s
        self._rng = rng if rng is not None else random.Random()
        self._no_throttled = no_throttled

    def delay_for(self, attempt: int) -> float:
        return self._rng.uniform(0., min(self._max_delay_s, self._base_delay_s * (2 ** (attempt - 1))))

    async def should_retry(self, failure: S3Failure) -> bool:
        if failure.attempt >= self._max_attempts:
            return False
        if failure.kind == S3FailureKind.THROTTLED and self._no_throttled:
            return False
        await self._sleeps.sleep(self.delay_for(failure.attempt))
        return True
