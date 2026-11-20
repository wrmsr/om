import ast

import pytest

from .replay import check_pending_replay


##


_EXCEPTIONS = """
def summary(exc):
    if exc is None:
        return None
    return type(exc).__name__, exc.args

def chain(exc):
    return summary(exc), summary(exc.__context__), summary(exc.__cause__), exc.__suppress_context__

def active_exception():
    try:
        raise
    except BaseException as exc:
        return exc
"""


_NESTED_CLEANUP = """
events = []
injected = ValueError('injected')

class Manager:
    def __init__(self, name, action='propagate'):
        self.name = name
        self.action = action
    def __enter__(self):
        events.append(('enter', self.name))
    def __exit__(self, cls, exc, tb):
        events.append(('exit', self.name, summary(exc), exc is injected, exc is active_exception()))
        if self.action == 'replace':
            raise LookupError('cleanup')
        if self.action == 'chain':
            raise LookupError('cleanup') from exc
        return self.action == 'suppress'

def inner(action):
    try:
        with Manager('middle'), Manager('inner', action):
            yield 'ready'
        events.append('after inner')
        return 'inner result'
    finally:
        events.append(('inner finally', summary(active_exception())))

def outer():
    try:
        with Manager('outer'):
            value = yield from child
            events.append(('delegated return', value))
        return 'outer result'
    finally:
        events.append(('outer finally', summary(active_exception())))
"""


def _exit_decision(task):
    node = task.node
    if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
        return False
    return any(isinstance(operand, ast.Constant) and operand.value == 'replace' for operand in node.test.comparators)


@pytest.mark.parametrize('exit_number', [1, 2], ids=['inner-exit', 'middle-exit'])
@pytest.mark.parametrize('action', ['propagate', 'suppress', 'replace', 'chain'])
@pytest.mark.parametrize('resume', ['parent.throw(injected)', 'parent.close()'], ids=['throw', 'close'])
def test_nested_generator_cleanup_replays_in_exit(resume, action, exit_number):
    source = _EXCEPTIONS + _NESTED_CLEANUP + f"""
child = inner({action!r})
parent = outer()
result = [next(parent)]
try:
    result.append({resume})
except BaseException as exc:
    result.append((chain(exc), exc is injected))
result.append((next(parent, 'parent closed'), next(child, 'child closed')))
result.append((parent.close(), child.close()))
result.append(events)
result.append(summary(active_exception()))
"""
    check_pending_replay(source, 'exec', predicate=_exit_decision, occurrence=exit_number)


@pytest.mark.parametrize('mode', ['throw', 'close'])
@pytest.mark.parametrize('checkpoint_task', ['yield_value', 'restore_outcome'])
def test_delegated_generator_replays_exception_across_yield_in_finally(mode, checkpoint_task):
    resume = 'parent.throw(injected)' if mode == 'throw' else 'parent.close()'
    resumed = 'parent' if mode == 'throw' else 'child'
    source = _EXCEPTIONS + f"""
events = []
injected = ValueError('injected')

def inner():
    try:
        yield 'ready'
    finally:
        events.append(('before cleanup yield', summary(active_exception())))
        yield 'cleanup'
        events.append(('after cleanup yield', summary(active_exception())))

def outer():
    try:
        yield from child
    finally:
        events.append(('outer finally', summary(active_exception())))

child = inner()
parent = outer()
result = [next(parent)]
try:
    result.append({resume})
except BaseException as exc:
    result.append((chain(exc), exc is injected))
try:
    next({resumed})
except BaseException as exc:
    result.append((chain(exc), exc is injected))
result.append((next(parent, 'parent closed'), next(child, 'child closed')))
result.append(events)
"""
    occurrence = 2 if checkpoint_task == 'yield_value' else 1
    check_pending_replay(source, checkpoint_task, occurrence=occurrence)
