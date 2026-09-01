import sys


##


def is_cancelled_error(e: BaseException) -> bool:
    if (asyncio := sys.modules.get('asyncio')) is not None:
        if (
                (ace := getattr(asyncio, 'CancelledError', None)) is not None and
                isinstance(ace, type) and
                isinstance(e, ace)
        ):
            return True  # noqa

    return False
