import re

from omcore import check


def parse_server_version(version):
    major = check.not_none(re.match(r'\d+', version)).group()  # leading digits in 17.0, 17rc1
    return int(major)
