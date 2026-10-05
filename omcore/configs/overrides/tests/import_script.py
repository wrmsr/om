import sys

from omcore.configs import overrides as ovr  # noqa


def _is_jq_loaded() -> bool:
    return any(n == 'omcore.specs.jq' or n.startswith('omcore.specs.jq.') for n in sys.modules)


def _main() -> None:
    assert not _is_jq_loaded()

    assert ovr.apply_overrides({'a': {'b': 1}}, ['a.b=2', 'a.c+=[x]', '/a.b']) == {'a': {'c': ['x']}}
    assert list(ovr.dump_overrides({'a': 1})) == ['a=1']
    assert ovr.override_config(5, ['=6']) == 6
    assert ovr.JqOp('.a') is not None
    assert not _is_jq_loaded()

    assert ovr.apply_overrides({'a': 1}, [ovr.JqOp('.a += 1')]) == {'a': 2}
    assert _is_jq_loaded()


if __name__ == '__main__':
    _main()
