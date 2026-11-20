import textwrap

import pytest

from .. import astvm


##


def _expected(source):
    namespace: dict[str, object] = {}
    exec(source, namespace)
    return namespace['result']


def _check_replay(setup, body):
    setup = textwrap.dedent(setup)
    body = textwrap.dedent(body)
    expected = _expected(setup + '\n' + body)

    vm = astvm.Interpreter()
    vm.execute(setup)
    checkpoint = vm.checkpoint()
    vm.execute(body)
    assert vm.get('result') == expected

    for _ in range(2):
        vm.restore(checkpoint)
        vm.execute(body)
        assert vm.get('result') == expected


def _check_pending_replay(source, task_kind, *, predicate=None, occurrence=1):
    expected = _expected(source)
    runtime = astvm.DictRuntime()
    vm = astvm.Interpreter(runtime=runtime)
    vm.start(source)
    while not vm.done:
        execution = runtime.read_thread().executions[-1]
        if execution.tasks:
            task = execution.tasks[-1]
            if task.kind == task_kind and (predicate is None or predicate(task)):
                occurrence -= 1
                if not occurrence:
                    break
        vm.step()
    else:
        pytest.fail(f'{task_kind!r} continuation was not reached')

    checkpoint = vm.checkpoint()
    vm.run()
    assert vm.get('result') == expected

    for _ in range(2):
        vm.restore(checkpoint)
        vm.run()
        assert vm.get('result') == expected


@pytest.mark.parametrize('source', ['mapping', 'mapping.keys()', 'mapping.values()', 'mapping.items()'])
@pytest.mark.parametrize('removed', ['a', 'b'])
@pytest.mark.parametrize('replacement', ['same', 'new'])
def test_mapping_iteration_observes_same_size_edits(source, removed, replacement):
    _check_replay(
        f"""
        mapping = {{'a': 1, 'b': 2, 'c': 3}}
        iterator = iter({source})
        first = next(iterator)
        """,
        f"""
        del mapping[{removed!r}]
        mapping[{(removed if replacement == 'same' else 'd')!r}] = 4
        mapping['c'] = 5
        result = [first]
        for _ in range(4):
            try:
                result.append(next(iterator))
            except RuntimeError:
                result.append('changed')
            except StopIteration:
                result.append('stopped')
        """,
    )


def test_class_mapping_proxy_view_reads_live_entries_after_restore():
    _check_replay(
        """
        class Target:
            a = 1
            b = 2
            c = 3

        view = vars(Target).items()
        iterator = iter(view)
        for key, value in iterator:
            if key == 'a':
                break
        """,
        """
        Target.c = 5
        result = [(key, value) for key, value in iterator if key in ('a', 'b', 'c')]
        """,
    )


def test_runtime_without_key_positions_can_iterate_mapping():
    class PlainRuntime(astvm.DictRuntime):
        def read(self, ref):
            obj = super().read(ref)
            return astvm.HeapObject(obj.kind, obj.data)

    vm = astvm.Interpreter(runtime=PlainRuntime())
    vm.execute(textwrap.dedent("""
    target = {'a': 1, 'b': 2}
    iterator = iter(target.items())
    first = next(iterator)
    target['b'] = 3
    result = first, list(iterator)
    """))
    assert vm.get('result') == (('a', 1), [('b', 3)])


@pytest.mark.parametrize(('target', 'source', 'grow', 'shrink'), [
    ("{'a': 1}", 'target', "target['b'] = 2", "del target['b']"),
    ("{'a': 1}", 'target.items()', "target['b'] = 2", "del target['b']"),
    ("{'a'}", 'target', "target.add('b')", "target.remove('b')"),
])
def test_mapping_and_set_size_errors_are_sticky(target, source, grow, shrink):
    _check_replay(
        f'target = {target}\niterator = iter({source})',
        f"""
        result = []
        {grow}
        try:
            next(iterator)
        except RuntimeError:
            result.append('changed')
        {shrink}
        try:
            next(iterator)
        except RuntimeError:
            result.append('still invalid')
        result.append(list(target))
        """,
    )


def test_list_iterator_sees_growth_until_exhausted():
    _check_replay(
        """
        target = [1]
        iterator = iter(target)
        first = next(iterator)
        """,
        """
        target.extend(target)
        result = [first, next(iterator), next(iterator, None)]
        target.append(3)
        result.append(next(iterator, None))
        result.append(target)
        """,
    )


@pytest.mark.parametrize('make', [
    'zip(source, source)',
    'zip(source, source, strict=True)',
    'map(str, source)',
    'filter(None, source)',
    'enumerate(source)',
])
def test_adapters_can_resume_after_input_stop_iteration(make):
    _check_replay(
        f"""
        class Source:
            def __init__(self):
                self.index = 0
            def __iter__(self):
                return self
            def __next__(self):
                self.index += 1
                if self.index in (2, 5):
                    raise StopIteration('transient')
                return self.index

        source = Source()
        adapter = {make}
        """,
        """
        result = []
        for _ in range(5):
            try:
                result.append(next(adapter))
            except StopIteration as exc:
                result.append(exc.args)
            except ValueError:
                result.append('uneven')
        result.append(source.index)
        """,
    )


@pytest.mark.parametrize('strict', [False, True])
def test_zip_replay_keeps_aliases_and_partially_consumed_row(strict):
    source = textwrap.dedent(f"""
    source = iter([1, 2, 3])
    adapter = zip(source, source, strict={strict})
    result = [next(adapter)]
    try:
        result.append(next(adapter))
    except StopIteration:
        result.append('stopped')
    except ValueError:
        result.append('uneven')
    result.append(next(source, None))
    """)
    _check_pending_replay(source, 'adapter_pull', predicate=lambda task: task.data[1] == (3,))


def test_strict_zip_consumes_one_item_from_longer_input_when_probing():
    source = textwrap.dedent("""
    source = iter([1, 2, 3])
    adapter = zip([0], source, strict=True)
    result = [next(adapter)]
    try:
        next(adapter)
    except ValueError:
        result.append(next(source))
    """)
    _check_pending_replay(source, 'zip_probe')


@pytest.mark.parametrize('make', ['zip(left, right)', 'map(lambda a, b: (a, b), left, right)'])
def test_adapter_keeps_partial_consumption_after_input_error(make):
    source = textwrap.dedent(f"""
    class Pulsed:
        def __init__(self):
            self.first = True
        def __iter__(self):
            return self
        def __next__(self):
            if self.first:
                self.first = False
                raise ValueError('retry')
            return 10

    left = iter([1, 2, 3])
    right = Pulsed()
    adapter = {make}
    try:
        next(adapter)
    except ValueError as exc:
        result = (exc.args, next(adapter), next(left))
    """)
    _check_pending_replay(source, 'adapter_pull', predicate=lambda task: task.data[1] == (1,))


@pytest.mark.parametrize('make', ['iter(source, None)', 'reversed(source)'])
def test_callable_iterator_and_reverse_sequence_stay_exhausted(make):
    _check_replay(
        f"""
        class Source:
            def __init__(self):
                self.calls = []
            def __call__(self):
                self.calls.append('call')
                if len(self.calls) == 2:
                    raise StopIteration('done')
                return 1
            def __len__(self):
                return 3
            def __getitem__(self, index):
                self.calls.append(index)
                if index == 1:
                    raise ValueError('failed')
                return index

        source = Source()
        iterator = {make}
        first = next(iterator)
        """,
        """
        result = [first]
        for _ in range(3):
            try:
                result.append(next(iterator))
            except StopIteration as exc:
                result.append(exc.args)
            except ValueError:
                result.append('failed')
        result.append(source.calls)
        """,
    )


@pytest.mark.parametrize(('target', 'operation', 'value', 'task_kind'), [
    ('[]', 'extend', '1', 'extend_next'),
    ('{}', 'update', "('a', 1)", 'mapping_update_next'),
])
def test_mutating_consumer_keeps_partial_changes_when_input_raises(target, operation, value, task_kind):
    source = textwrap.dedent(f"""
    events = []
    def values():
        events.append('before')
        yield {value}
        events.append('after')
        raise ValueError('done')

    target = {target}
    iterator = values()
    try:
        target.{operation}(iterator)
    except ValueError as exc:
        result = (target, events, exc.args, next(iterator, None))
    """)
    _check_pending_replay(source, task_kind, occurrence=2)
