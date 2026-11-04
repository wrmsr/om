"""Exercises the standard-code demo in `examples/` - not lite, as it is not."""
import unittest

from ..dispatch import RpcMethodTableHandler
from ..dispatch import rpc_merge_method_tables
from ..examples.services import AddCommand
from ..examples.services import Command
from ..examples.services import CommandClient
from ..examples.services import CommandService
from ..examples.services import ConcatCommand
from ..examples.services import EchoCommand
from ..examples.services import GreeterService
from ..examples.services import GreetRequest
from ..examples.services import GreetResult
from ..examples.services import LoudGreeterService
from ..examples.services import rpc_service_method_table
from ..marshal import MarshalRpcSerde
from ..pure import pure_rpc_connection_pair
from ..serde import RpcTypedCaller


class TestExamples(unittest.TestCase):
    def test_service_methods(self):
        serde = MarshalRpcSerde()

        table = rpc_service_method_table(GreeterService(), serde)
        self.assertEqual(sorted(table), ['greeter.count', 'greeter.greet'])

        loud = rpc_service_method_table(LoudGreeterService(), serde)
        self.assertEqual(sorted(loud), ['greeter.greet'])

        pair = pure_rpc_connection_pair(b_kwargs=dict(handler=RpcMethodTableHandler(table)))
        caller = RpcTypedCaller(pair.a.connection, serde)
        self.assertEqual(
            pair.a.run(caller.call('greeter.greet', GreetRequest('bob', excited=True), GreetResult)),
            GreetResult('hello, bob!'),
        )
        self.assertEqual(pair.a.run(caller.call('greeter.count')), 1)

        pair = pure_rpc_connection_pair(b_kwargs=dict(handler=RpcMethodTableHandler(loud)))
        caller = RpcTypedCaller(pair.a.connection, serde)
        self.assertEqual(
            pair.a.run(caller.call('greeter.greet', GreetRequest('bob'), GreetResult)),
            GreetResult('HELLO, BOB!'),
        )

    def test_polymorphic_commands(self):
        serde = MarshalRpcSerde()

        self.assertEqual(serde.marshal(AddCommand(1, 2), Command), {'add': {'x': 1, 'y': 2}})

        table = rpc_merge_method_tables(
            CommandService().method_table(serde),
            rpc_service_method_table(GreeterService(), serde),
        )
        pair = pure_rpc_connection_pair(b_kwargs=dict(handler=RpcMethodTableHandler(table)))
        client = CommandClient(pair.a.connection, serde)

        self.assertEqual(pair.a.run(client.execute(EchoCommand('hi'))), 'hi')
        self.assertEqual(pair.a.run(client.execute(AddCommand(2, 3))), 5)
        self.assertEqual(pair.a.run(client.execute(ConcatCommand(['a', 'b', 'c']))), 'abc')
