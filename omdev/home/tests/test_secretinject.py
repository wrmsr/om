# @om-lite
# ruff: noqa: UP006 UP045
import collections
import fcntl
import json
import os
import stat
import subprocess
import sys
import tempfile
import threading
import time
import typing as ta
import unittest

from .. import secretinject as si


##


def od(*pairs: ta.Tuple[str, ta.Any]) -> si.JsonObject:
    return collections.OrderedDict(pairs)


def items(obj: ta.Mapping[str, ta.Any]) -> ta.List[ta.Tuple[str, ta.Any]]:
    return list(obj.items())


class MergeTest(unittest.TestCase):
    def test_ordering(self) -> None:
        existing = od(('a', 1), ('b', 2), ('c', 3), ('d', 4))
        update = od(('e', 5), ('c', 30), ('a', 1), ('b', None))
        merged, changed = si.merge(existing, update)
        self.assertTrue(changed)
        self.assertIsInstance(merged, collections.OrderedDict)
        # untouched keys in read order, then every set key in stdin order (even 'a', whose value is the same), removed
        # keys gone
        self.assertEqual(items(merged), [('d', 4), ('e', 5), ('c', 30), ('a', 1)])

    def test_unchanged_value_still_reorders(self) -> None:
        merged, changed = si.merge(od(('a', 1), ('b', 2)), od(('a', 1)))
        self.assertTrue(changed)
        self.assertEqual(items(merged), [('b', 2), ('a', 1)])

    def test_no_change(self) -> None:
        # set keys are already at the tail, in stdin order, with the same values
        existing = od(('x', 0), ('b', [1, {'x': 2}]), ('a', 1))
        update = od(('b', [1, {'x': 2}]), ('a', 1), ('never_there', None))
        merged, changed = si.merge(existing, update)
        self.assertFalse(changed)
        self.assertEqual(items(merged), items(existing))

    def test_remove(self) -> None:
        merged, changed = si.merge(od(('a', 1), ('b', 2)), od(('a', None)))
        self.assertTrue(changed)
        self.assertEqual(items(merged), [('b', 2)])

    def test_remove_missing_is_noop(self) -> None:
        merged, changed = si.merge(od(('a', 1)), od(('b', None)))
        self.assertFalse(changed)
        self.assertEqual(items(merged), [('a', 1)])

    def test_shallow(self) -> None:
        existing = od(('a', od(('x', 1), ('y', 2))), ('l', [1, 2, 3]))
        update = od(('a', od(('z', 3))), ('l', [4]))
        merged, changed = si.merge(existing, update)
        self.assertTrue(changed)
        self.assertEqual(items(merged), [('a', {'z': 3}), ('l', [4])])

    def test_values_compared_by_json_not_python_equality(self) -> None:
        cases = [(1, True), (1, 1.0), (0, False), ([1], [True]), (od(('x', 1), ('y', 2)), od(('y', 2), ('x', 1)))]
        for old, new in cases:
            merged, changed = si.merge(od(('a', old)), od(('a', new)))
            self.assertTrue(changed, (old, new))
            self.assertEqual(json.dumps(merged['a']), json.dumps(new))
        for same in [1, 1.0, True, 'x', [1, {'y': None}]]:
            self.assertEqual(si.merge(od(('a', same)), od(('a', same))), (od(('a', same)), False))

    def test_empty_inputs(self) -> None:
        self.assertEqual(si.merge(od(), od()), (od(), False))
        self.assertEqual(si.merge(od(), od(('a', None))), (od(), False))
        self.assertEqual(si.merge(od(('a', 1)), od()), (od(('a', 1)), False))


class LoadDumpTest(unittest.TestCase):
    def test_dump_empty_is_bare_braces(self) -> None:
        self.assertEqual(si.dump(od()), b'{}')

    def test_dump_pretty_printed(self) -> None:
        data = od(('a', 1), ('b', od(('c', [1, 2]), ('d', 'é'))), ('e', od()), ('f', None))
        expected = (
            '{\n'
            '  "a": 1,\n'
            '  "b": {\n'
            '    "c": [\n'
            '      1,\n'
            '      2\n'
            '    ],\n'
            '    "d": "é"\n'
            '  },\n'
            '  "e": {},\n'
            '  "f": null\n'
            '}\n'
        )
        self.assertEqual(si.dump(data), expected.encode('utf-8'))

    def test_load_empty_is_empty_object(self) -> None:
        for raw in [b'', b' \n\t']:
            self.assertEqual(si.load(raw), od())
            self.assertIsInstance(si.load(raw), collections.OrderedDict)

    def test_load_preserves_order(self) -> None:
        loaded = si.load(b'{"z": 1, "a": {"y": 2, "b": 3}}')
        self.assertIsInstance(loaded, collections.OrderedDict)
        self.assertEqual(list(loaded), ['z', 'a'])
        self.assertEqual(list(loaded['a']), ['y', 'b'])

    def test_load_rejects_non_objects(self) -> None:
        for raw in [b'nope', b'[1]', b'"s"', b'null', b'1']:
            with self.assertRaises(ValueError):
                si.load(raw)

    def test_parse_object_rejects_empty(self) -> None:
        with self.assertRaises(ValueError):
            si.parse_object('')

    def test_roundtrip(self) -> None:
        data = od(('z', 1), ('a', od(('y', [1, 'two', None]), ('b', True))))
        self.assertEqual(json.dumps(si.load(si.dump(data))), json.dumps(data))


class TempDirTest(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.dir = self._td.name
        self.path = os.path.join(self.dir, 'config.json')

    def tearDown(self) -> None:
        self._td.cleanup()

    def write(self, text: str, path: ta.Optional[str] = None) -> None:
        with open(path or self.path, 'w', encoding='utf-8') as f:
            f.write(text)

    def read_raw(self, path: ta.Optional[str] = None) -> bytes:
        with open(path or self.path, 'rb') as f:
            return f.read()

    def read(self, path: ta.Optional[str] = None) -> si.JsonObject:
        return si.load(self.read_raw(path))

    def temps(self) -> ta.List[str]:
        return [n for n in os.listdir(self.dir) if n.startswith('.config.json.')]

    def hold_lock(self, path: ta.Optional[str] = None) -> int:
        fd = os.open(path or self.path, os.O_RDONLY)
        fcntl.flock(fd, fcntl.LOCK_EX)
        return fd


class InjectTest(TempDirTest):
    def test_creates_file(self) -> None:
        si.inject_secrets(self.path, od(('a', 'x'), ('gone', None), ('b', [1])), timeout=1.0)
        self.assertEqual(items(self.read()), [('a', 'x'), ('b', [1])])
        self.assertEqual(stat.S_IMODE(os.stat(self.path).st_mode), 0o600)
        self.assertEqual(self.temps(), [])

    def test_creates_empty_object_file(self) -> None:
        si.inject_secrets(self.path, od(('a', None)), timeout=1.0)
        self.assertEqual(self.read_raw(), b'{}')

    def test_updates_existing_preserving_mode_and_order(self) -> None:
        self.write('{"a": 1, "b": 2, "c": 3}')
        os.chmod(self.path, 0o640)
        si.inject_secrets(self.path, od(('b', 20), ('d', 4), ('a', None)), timeout=1.0)
        self.assertEqual(items(self.read()), [('c', 3), ('b', 20), ('d', 4)])
        self.assertEqual(stat.S_IMODE(os.stat(self.path).st_mode), 0o640)
        self.assertEqual(self.temps(), [])

    def test_becomes_empty_object(self) -> None:
        self.write('{"a": 1}')
        si.inject_secrets(self.path, od(('a', None)), timeout=1.0)
        self.assertEqual(self.read_raw(), b'{}')

    def test_rewrite_is_a_new_inode(self) -> None:
        # i.e. done via rename of a temp file, never by writing in place
        self.write('{"a": 1}')
        before = os.stat(self.path).st_ino
        si.inject_secrets(self.path, od(('a', 2)), timeout=1.0)
        self.assertNotEqual(before, os.stat(self.path).st_ino)
        self.assertEqual(self.read_raw(), b'{\n  "a": 2\n}\n')

    def test_no_change_no_rewrite(self) -> None:
        text = '{"a": 1,   "b": 2}'  # odd formatting on purpose: an untouched file stays byte-identical
        self.write(text)
        before = os.stat(self.path).st_ino
        # 'b' is already last, so nothing to do
        si.inject_secrets(self.path, od(('b', 2), ('nope', None)), timeout=1.0)
        self.assertEqual(before, os.stat(self.path).st_ino)
        self.assertEqual(self.read_raw(), text.encode('utf-8'))

    def test_empty_file_treated_as_empty_object(self) -> None:
        self.write('')
        si.inject_secrets(self.path, od(('a', 1)), timeout=1.0)
        self.assertEqual(items(self.read()), [('a', 1)])

    def test_repeated_runs_are_stable(self) -> None:
        update = od(('b', 2), ('a', 1))
        si.inject_secrets(self.path, update, timeout=1.0)
        first = os.stat(self.path).st_ino, self.read_raw()
        si.inject_secrets(self.path, update, timeout=1.0)
        self.assertEqual((os.stat(self.path).st_ino, self.read_raw()), first)  # second run didn't even rewrite

    def test_resending_unchanged_value_reorders(self) -> None:
        self.write('{"a": 1, "b": 2}')
        si.inject_secrets(self.path, od(('a', 1)), timeout=1.0)
        self.assertEqual(self.read_raw(), b'{\n  "b": 2,\n  "a": 1\n}\n')

    def test_symlink_updates_target(self) -> None:
        real = os.path.join(self.dir, 'real.json')
        self.write('{}', real)
        os.symlink('real.json', self.path)
        si.inject_secrets(self.path, od(('a', 1)), timeout=1.0)
        self.assertTrue(os.path.islink(self.path))
        self.assertEqual(items(self.read(real)), [('a', 1)])

    def test_rejects_invalid_file_and_leaves_it_alone(self) -> None:
        for text in ['nope', '[1]', '"s"', 'null']:
            self.write(text)
            with self.assertRaises(ValueError):
                si.inject_secrets(self.path, od(('a', 1)), timeout=1.0)
            self.assertEqual(self.read_raw(), text.encode('utf-8'))
            self.assertEqual(self.temps(), [])

    def test_rejects_directory(self) -> None:
        os.mkdir(self.path)
        with self.assertRaises(OSError):
            si.inject_secrets(self.path, od(('a', 1)), timeout=1.0)

    def test_timeout_while_locked(self) -> None:
        self.write('{}')
        fd = self.hold_lock()
        try:
            t0 = time.monotonic()
            with self.assertRaises(TimeoutError):
                si.inject_secrets(self.path, od(('a', 1)), timeout=0.2)
            self.assertGreaterEqual(time.monotonic() - t0, 0.2)
        finally:
            os.close(fd)
        self.assertEqual(self.read_raw(), b'{}')
        self.assertEqual(self.temps(), [])

    def test_waits_for_lock_and_merges_into_replacement(self) -> None:
        # Play the part of a concurrent writer: hold the lock on the current inode, rename a new file over the path
        # (exactly what inject() does), then release. The waiting injector must merge into the replacement, not into the
        # file it originally found.
        self.write('{"a": 1}')
        fd = self.hold_lock()

        errors: ta.List[BaseException] = []

        def run() -> None:
            try:
                si.inject_secrets(self.path, od(('b', 2)), timeout=5.0)
            except BaseException as e:  # noqa
                errors.append(e)

        t = threading.Thread(target=run)
        t.start()
        try:
            time.sleep(0.2)  # injector is now polling for the lock
            self.assertTrue(t.is_alive())
            self.assertEqual(self.read_raw(), b'{"a": 1}')

            replacement = os.path.join(self.dir, 'replacement')
            self.write('{"a": 1, "c": 3}', replacement)
            os.rename(replacement, self.path)
        finally:
            os.close(fd)  # release the lock
            t.join(5.0)

        self.assertFalse(t.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(items(self.read()), [('a', 1), ('c', 3), ('b', 2)])
        self.assertEqual(self.temps(), [])


class CliTest(TempDirTest):
    def run_cli(self, *args: str, stdin: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, si.__file__, *args],
            input=stdin.encode('utf-8'),
            capture_output=True,
            check=False,
        )

    def test_success(self) -> None:
        self.write('{"keep": true, "old": 1}')
        r = self.run_cli(self.path, stdin='{"new": "x", "old": null}\n')
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, b'', b''))
        self.assertEqual(items(self.read()), [('keep', True), ('new', 'x')])

    def test_description_is_accepted_and_ignored(self) -> None:
        r = self.run_cli('--description', 'inject db creds', self.path, stdin='{"a": 1}')
        self.assertEqual((r.returncode, r.stderr), (0, b''))
        self.assertEqual(items(self.read()), [('a', 1)])

    def test_bad_stdin(self) -> None:
        for stdin in ['', 'nope', '[1]', '"s"', 'null']:
            r = self.run_cli(self.path, stdin=stdin)
            self.assertEqual(r.returncode, 1, stdin)
            self.assertIn(b'stdin', r.stderr)
            self.assertFalse(os.path.exists(self.path))

    def test_bad_file(self) -> None:
        self.write('[1]')
        r = self.run_cli(self.path, stdin='{"a": 1}')
        self.assertEqual(r.returncode, 1)
        self.assertIn(self.path.encode('utf-8'), r.stderr)
        self.assertEqual(self.read_raw(), b'[1]')

    def test_usage(self) -> None:
        r = self.run_cli(stdin='{}')
        self.assertEqual(r.returncode, 2)

    def test_timeout_exit_code(self) -> None:
        self.write('{}')
        fd = self.hold_lock()
        try:
            r = self.run_cli('--timeout', '0.2', self.path, stdin='{"a": 1}')
        finally:
            os.close(fd)
        self.assertEqual(r.returncode, 3)
        self.assertIn(b'timed out', r.stderr)
        self.assertEqual(self.read_raw(), b'{}')


class ConcurrencyTest(TempDirTest):
    N = 32

    def stress(self) -> None:
        stop = threading.Event()
        bad: ta.List[bytes] = []
        reads = [0]

        def reader() -> None:
            # Hammer the file the whole time; every read must be a complete JSON object (or ENOENT before creation).
            while not stop.is_set():
                try:
                    raw = self.read_raw()
                except FileNotFoundError:
                    continue
                reads[0] += 1
                try:
                    if not isinstance(json.loads(raw), dict):
                        bad.append(raw)
                except ValueError:
                    bad.append(raw)

        rt = threading.Thread(target=reader)
        rt.start()
        try:
            procs: ta.List[subprocess.Popen] = []
            for i in range(self.N):
                p = subprocess.Popen(
                    [sys.executable, si.__file__, self.path],
                    stdin=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                p.stdin.write(json.dumps({f'k{i}': f'v{i}', 'shared': i}).encode('utf-8'))  # type: ignore
                p.stdin.close()  # type: ignore
                procs.append(p)
            for p in procs:
                err = p.stderr.read()  # type: ignore
                p.stderr.close()  # type: ignore
                self.assertEqual(p.wait(), 0, err)
        finally:
            stop.set()
            rt.join()

        self.assertEqual(bad, [])
        self.assertGreater(reads[0], 0)
        self.assertEqual(self.temps(), [])

        data = self.read()
        for i in range(self.N):
            self.assertEqual(data[f'k{i}'], f'v{i}')
        self.assertIn(data['shared'], range(self.N))

    def test_concurrent_creation(self) -> None:
        self.stress()

    def test_concurrent_update(self) -> None:
        self.write('{"existing": true}')
        self.stress()
        self.assertEqual(next(iter(self.read())), 'existing')  # untouched, so still first
