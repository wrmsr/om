import pytest

from .. import astvm


##


def expected_result(source):
    namespace: dict[str, object] = {}
    exec(source, namespace)
    return namespace['result']


def check_pending_replay(source, task_kind, *, predicate=None, occurrence=1):
    expected = expected_result(source)
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
