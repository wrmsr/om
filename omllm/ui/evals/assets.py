import importlib.resources


##


def eval_resources() -> importlib.resources.abc.Traversable:
    return importlib.resources.files(__package__).joinpath('eval-data')
