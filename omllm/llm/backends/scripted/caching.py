import math
import typing as ta

from omcore import dataclasses as dc


##


def strip_cache_controls(value: ta.Any) -> ta.Any:
    """Recursively remove cache-control markers before prompt-prefix comparison."""

    if isinstance(value, dict):
        return {
            key: strip_cache_controls(item)
            for key, item in value.items()
            if key not in ('cache_control', 'cacheControl')
        }
    if isinstance(value, list):
        return [strip_cache_controls(item) for item in value]
    return value


def common_prefix_len(a: str, b: str) -> int:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text) / 4)


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class SimulatedCacheUsage:
    uncached_input_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int


class PromptCacheSimulator:
    """Tracks the previous prompt per cache key and reports its next read/write split."""

    def __init__(self) -> None:
        super().__init__()

        self._previous_prompts: dict[str, str] = {}

    def clear(self) -> None:
        self._previous_prompts.clear()

    def check(self, cache_key: str | None, prompt_text: str) -> SimulatedCacheUsage:
        prompt_tokens = estimate_tokens(prompt_text)
        if cache_key is None:
            return SimulatedCacheUsage(
                uncached_input_tokens=prompt_tokens,
                cache_read_tokens=0,
                cache_write_tokens=0,
            )

        previous = self._previous_prompts.get(cache_key)
        if previous is None:
            cache_read = 0
            cache_write = prompt_tokens
        else:
            common = common_prefix_len(previous, prompt_text)
            cache_read = estimate_tokens(prompt_text[:common])
            cache_write = estimate_tokens(prompt_text[common:])
        self._previous_prompts[cache_key] = prompt_text

        return SimulatedCacheUsage(
            uncached_input_tokens=max(0, prompt_tokens - cache_read - cache_write),
            cache_read_tokens=cache_read,
            cache_write_tokens=cache_write,
        )
