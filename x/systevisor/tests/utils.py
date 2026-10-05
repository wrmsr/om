import shutil

from omcore.lite.check import check


def true_bin() -> str:
    return check.not_none(shutil.which('true'))
