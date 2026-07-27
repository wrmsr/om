async def bash(
        command: str,
        *,
        timeout_s: float | None = None,
) -> str:
    """
    Executes a bash command in the current working directory. Returns stdout and stderr.

    Args:
        command: The bash command to execute.
        timeout_s: An optional timeout in seconds.
    """

    raise NotImplementedError
