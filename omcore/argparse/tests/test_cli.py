# ruff: noqa: PT009
# @om-lite
import argparse
import unittest

from .. import cli
from .. import parsers


##


class JunkCli(cli.ArgparseCli):
    num_runs = 0

    @parsers.argparse_cmd(
        parsers.argparse_arg('foo', metavar='foo'),
        parsers.argparse_arg('--bar', dest='bar', action='store_true'),
    )
    def run(self) -> None:
        self.num_runs += 1


class TestCli(unittest.TestCase):
    def test_cli(self):
        c = JunkCli(['run', 'xyz'])
        self.assertEqual(c.num_runs, 0)
        c()
        self.assertEqual(c.num_runs, 1)


##


class ClassVarCli(cli.ArgparseCli):
    _foo = parsers.argparse_arg('--foo')

    @parsers.argparse_cmd(
        parsers.argparse_arg('--bar'),
    )
    def baz(self) -> None:
        pass


class TestClassVar(unittest.TestCase):
    def test_cli(self):
        c = ClassVarCli(['--foo', 'foo!', 'baz', '--bar', 'bar!'])
        print(c._args)  # noqa


##


class FormatHelpCli(cli.ArgparseCli):
    _baz = parsers.argparse_arg('--baz')

    @parsers.argparse_cmd(
        parsers.argparse_arg('qux'),
    )
    def foo(self):
        pass

    @parsers.argparse_cmd()
    def bar(self):
        pass


class FooHelpFormatter(argparse.HelpFormatter):
    def add_argument(self, action):
        if not (
                isinstance(action, argparse._SubParsersAction) and  # noqa
                action.help is not argparse.SUPPRESS
        ):
            super().add_argument(action)
            return

        s1 = 's1:' + self._format_action_invocation(action)
        action_length = len(s1) + self._current_indent
        self._action_max_length = max(self._action_max_length, action_length)

        # add the item to the list
        def f():
            s2 = 's2:' + self._format_action(action)
            return s2

        self._add_item(f, [])

    def _metavar_formatter(self, action, default_metavar):
        return super()._metavar_formatter(action, default_metavar)  # noqa


class TestFormatHelp(unittest.TestCase):
    def test_cli(self):
        p = FormatHelpCli.get_parser()
        p.formatter_class = FooHelpFormatter
        print(p.format_help())


##


class TestInheritance(unittest.TestCase):
    def test_mro_precedence(self):
        class IntValueCli(cli.ArgparseCli):
            value: int = parsers.argparse_arg_('--value')

        class StrValueCli(cli.ArgparseCli):
            value: int = parsers.argparse_arg_('--value', type=str)

        class CombinedCli(IntValueCli, StrValueCli):
            pass

        c = CombinedCli(['--value', '42'])
        self.assertEqual(c.value, 42)

    def test_normal_attribute_shadows_inherited_arg(self):
        class BaseCli(cli.ArgparseCli):
            value = parsers.argparse_arg('--value')

        class ChildCli(BaseCli):
            value = 'constant'

        self.assertNotIn('--value', ChildCli.get_parser()._option_string_actions)  # noqa
        self.assertEqual(ChildCli([]).value, 'constant')


##


class AsyncCli(cli.ArgparseCli):
    @parsers.argparse_cmd()
    async def async_run(self):
        return 3

    @parsers.argparse_cmd()
    def sync_run(self):
        return 4

    @parsers.argparse_cmd()
    async def invalid_run(self):
        return 'invalid'


class TestAsyncCli(unittest.IsolatedAsyncioTestCase):
    async def test_async_run(self):
        self.assertEqual(await AsyncCli(['async-run']).async_cli_run(), 3)

    async def test_sync_run(self):
        self.assertEqual(await AsyncCli(['sync-run']).async_cli_run(), 4)

    async def test_invalid_run(self):
        with self.assertRaises(TypeError):
            await AsyncCli(['invalid-run']).async_cli_run()
