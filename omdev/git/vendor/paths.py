##


def is_path_under(path: str, dir: str) -> bool:  # noqa
    return path == dir or path.startswith(dir + '/')
