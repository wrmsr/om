import importlib.abc
import operator
import pickle
import sys


if __name__ == '__main__':
    class CextBlocker(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname in {'omcore.lang._comparison', 'omcore.lang._functions'}:
                raise ModuleNotFoundError(fullname)
            return None  # noqa

    sys.meta_path.insert(0, CextBlocker())

    # NOTE: This function can't use `assert` because pytest rewrites it making `getsource` not work.
    from omcore import check  # noqa
    from omcore.lang import comparison  # noqa
    from omcore.lang import functions  # noqa

    def make_objects():
        return {
            'key_default': comparison.key_cmp(),
            'key_cmp': comparison.key_cmp(comparison.cmp),
            'key_hash_eq_id_cmp': comparison.key_cmp(comparison.hash_eq_id_cmp),
            'key_custom': comparison.key_cmp(operator.sub),
            'attr_unbound': functions.attrsetter('value'),
            'attr_none': functions.attrsetter('value', None),
            'item_unbound': functions.itemsetter('value'),
            'item_none': functions.itemsetter('value', None),
        }

    def check_objects(objects):
        check.equal(objects['key_default']((1, 'a'), (2, 'b')), -1)
        check.equal(objects['key_cmp']((1, 'a'), (2, 'b')), -1)
        check.equal(objects['key_hash_eq_id_cmp']((1, 'a'), (2, 'b')), -1)
        check.equal(objects['key_custom']((1, 'a'), (2, 'b')), -1)

        class Target:
            value: object

        target = Target()
        objects['attr_unbound'](target, 420)
        check.equal(target.value, 420)
        objects['attr_none'](target)
        check.none(target.value)

        target_dict: dict[str, object] = {}
        objects['item_unbound'](target_dict, 420)
        check.equal(target_dict['value'], 420)
        objects['item_none'](target_dict)
        check.none(target_dict['value'])

    check.none(comparison._comparison)  # noqa
    check.none(functions._functions)  # noqa

    if sys.argv[1] == 'load':
        objects = pickle.loads(sys.stdin.buffer.read())  # noqa
        check_objects(objects)
        check.equal(type(objects['key_default']).__module__, 'omcore.lang.comparison')
        check.equal(type(objects['attr_unbound']).__module__, 'omcore.lang.functions')
    elif sys.argv[1] == 'dump':
        objects = make_objects()
        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            round_tripped = pickle.loads(pickle.dumps(objects, protocol))  # noqa
            check_objects(round_tripped)
        sys.stdout.buffer.write(pickle.dumps(objects))
    else:
        raise RuntimeError(sys.argv[1])
