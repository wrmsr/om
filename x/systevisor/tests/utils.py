import shutil

from omcore import check


def true_bin() -> str:
    return check.not_none(shutil.which('true'))
