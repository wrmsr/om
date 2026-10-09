def reconnect_delay(attempt: int, *, base: float, cap: float, sample: float) -> float:
    """
    The delay before reconnect attempt `attempt` (from 0): doubling from `base` up to `cap`, scaled by jitter into
    [50%, 100%) by `sample`, a uniform random sample in [0, 1).
    """

    if not (0. <= sample < 1.):
        raise ValueError(sample)
    return min(cap, base * (2. ** min(attempt, 64))) * (.5 + .5 * sample)
