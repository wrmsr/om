# ruff: noqa: N803 N806 N812


##


class Cancelled(Exception):  # noqa
    """Raised out of `generate` (by its callbacks) to abandon a generation between rounds or prefill chunks."""
