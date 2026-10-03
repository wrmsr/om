# ruff: noqa: UP006 UP007 UP045
import importlib.util
import types
import typing as ta


##


def can_import(name: str, package: ta.Optional[str] = None) -> bool:
    """
    Whether the named module could be imported, without importing it. Unlike wrapping an import in `except ImportError`
    this does not also swallow import failures raised from within the module's own body.
    """

    try:
        spec = importlib.util.find_spec(name, package)
    except ImportError:
        return False
    else:
        return spec is not None


##


def import_module(dotted_path: str) -> types.ModuleType:
    if not dotted_path:
        raise ImportError(dotted_path)
    mod = __import__(dotted_path, globals(), locals(), [])
    for name in dotted_path.split('.')[1:]:
        try:
            mod = getattr(mod, name)
        except AttributeError:
            raise AttributeError(f'Module {mod!r} has no attribute {name!r}') from None
    return mod


def import_module_attr(dotted_path: str) -> ta.Any:
    module_name, _, class_name = dotted_path.rpartition('.')
    mod = import_module(module_name)
    try:
        return getattr(mod, class_name)
    except AttributeError:
        raise AttributeError(f'Module {module_name!r} has no attr {class_name!r}') from None


def import_attr(dotted_path: str) -> ta.Any:
    import importlib  # noqa
    parts = dotted_path.split('.')
    mod: ta.Any = None
    mod_pos = 0
    while mod_pos < len(parts):
        mod_name = '.'.join(parts[:mod_pos + 1])
        try:
            mod = importlib.import_module(mod_name)
        except ImportError:
            break
        mod_pos += 1
    if mod is None:
        raise ImportError(dotted_path)
    obj = mod
    for att_pos in range(mod_pos, len(parts)):
        obj = getattr(obj, parts[att_pos])
    return obj
