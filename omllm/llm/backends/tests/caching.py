"""
Shared support for real-API prompt caching integration tests.

Drives a three-step scenario against a live backend and returns the reported token usages for each step:

- 'prime': a cold request whose large system prompt carries a run-unique nonce, guaranteeing no previous run's cache
  entry (which may outlive a test session) can be hit.
- 'full': the identical request again - a full cache hit over the primed prefix.
- 'partial': the conversation extended with the prime response and a new user message - a partial hit which reuses
  the primed prefix while the extension goes uncached.

Implicit provider caches (OpenAI, Gemini, OpenRouter upstreams) are best-effort: a hit may take a retry or two to
appear, so the hit steps re-request (bounded) until a sufficient cache read is reported, and the caller asserts on
the final usages. The min_cache_read bar exists because a load-balanced upstream can report a trivial partial-block
hit (observed: 64 tokens) which would otherwise end the retries early with a read no caller assertion accepts.
"""
import asyncio
import typing as ta
import uuid

from omcore import check
from omcore import dataclasses as dc

from ...types.backends import ImmediateBackend
from ...types.context import Context
from ...types.messages import AiMessage
from ...types.messages import TokenUsage
from ...types.messages import UserMessage
from ...types.options import Options


##


# Sized so the cacheable prefix lands well above every provider's minimum (the largest documented today is 4096
# tokens) - about 45 tokens per ledger line.
DEFAULT_NUM_LEDGER_LINES: ta.Final = 200

PRIME_USER_PROMPT: ta.Final = 'Say the word "ok".'
FOLLOWUP_USER_PROMPT: ta.Final = 'Now say the word "done".'


def build_ledger_system_prompt(
        nonce: str,
        *,
        num_lines: int = DEFAULT_NUM_LEDGER_LINES,
) -> str:
    """A large, deterministic system prompt. The nonce rides its first line, so runs share no cacheable prefix."""

    lines = [
        f'You are a meticulous archivist for run {nonce}. Reply with exactly one word unless told otherwise.',
        '',
        'Reference ledger:',
    ]
    for i in range(num_lines):
        lines.append(f'- Ledger entry {i:04d} of run {nonce}: the recorded value is {(i * 7919) % 104729}.')
    return '\n'.join(lines)


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class CachingScenarioUsages:
    prime: TokenUsage
    full: TokenUsage
    partial: TokenUsage


async def run_caching_scenario(
        backend: ImmediateBackend,
        options: Options | None,
        *,
        num_ledger_lines: int = DEFAULT_NUM_LEDGER_LINES,
        hit_attempts: int = 1,
        min_cache_read: int = 1,
        retry_delay_s: float = 2.,
) -> CachingScenarioUsages:
    async def request_until_cache_read(context: Context) -> AiMessage:
        out = await backend.immediate(context, options)
        for _ in range(hit_attempts - 1):
            if (u := out.token_usage) is not None and (u.cache_read or 0) >= min_cache_read:
                break
            # A real-world propagation delay for best-effort server-side caches, not a simulated test condition.
            await asyncio.sleep(retry_delay_s)
            out = await backend.immediate(context, options)
        return out

    nonce = uuid.uuid4().hex

    prime_context = Context(
        system_prompt=build_ledger_system_prompt(nonce, num_lines=num_ledger_lines),
        messages=[UserMessage(PRIME_USER_PROMPT)],
    )

    prime_out = await backend.immediate(prime_context, options)

    full_out = await request_until_cache_read(prime_context)

    partial_context = dc.replace(prime_context, messages=[
        *check.not_none(prime_context.messages),
        prime_out,
        UserMessage(FOLLOWUP_USER_PROMPT),
    ])

    partial_out = await request_until_cache_read(partial_context)

    return CachingScenarioUsages(
        prime=check.not_none(prime_out.token_usage),
        full=check.not_none(full_out.token_usage),
        partial=check.not_none(partial_out.token_usage),
    )
