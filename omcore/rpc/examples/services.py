"""
A demo of the standard-code niceties which layer over the lite rpc core without it knowing of them: polymorphic serde
from `omcore.marshal`, MRO-honoring single dispatch from `omcore.dispatch`, and MRO-honoring attribute registration from
`omcore.collections`. Two independent recipes:

 - Service methods. `@rpc_service_method(name, params_type, result_type)` marks methods of a service class as rpc
   methods, recorded in an `AttrRegistry`. `rpc_service_method_table` collects them along the instance's MRO - so a
   subclass inherits its bases' methods, overrides one by re-marking it, or withdraws one by shadowing it unmarked - and
   builds a typed method table over a serde. No signatures are inspected: the types are stated where the method is
   marked.

 - Polymorphic commands. A command hierarchy marshaled as tagged objects by `omcore.marshal`, served by a single rpc
   method whose implementation is chosen by a dispatch `Method` on the command's type. This is `ominfra.manage`'s
   command style, expressed as a recipe over the core rather than as a protocol of its own.

Not lite: this is what standard code gets on top of the lite core.
"""
import typing as ta

from ... import collections as col
from ... import dataclasses as dc
from ... import dispatch
from ... import lang
from ... import marshal as msh
from ..connection import RpcConnection
from ..dispatch import RpcMethodFn
from ..serde import RpcSerde
from ..serde import RpcTypedCaller
from ..serde import rpc_typed_method


##
# service methods


@dc.dataclass(frozen=True)
class RpcServiceMethodInfo:
    name: str
    params_type: ta.Any = None
    result_type: ta.Any = None


_RPC_SERVICE_METHODS: col.AttrRegistry[ta.Callable, RpcServiceMethodInfo] = col.AttrRegistry()


def rpc_service_method(
        name: str,
        params_type: ta.Any = None,
        result_type: ta.Any = None,
) -> ta.Callable[[ta.Callable], ta.Callable]:
    def inner(fn):
        _RPC_SERVICE_METHODS.register(fn, RpcServiceMethodInfo(name, params_type, result_type))
        return fn

    return inner


def rpc_service_method_table(service: ta.Any, serde: RpcSerde) -> dict[str, RpcMethodFn]:
    out: dict[str, RpcMethodFn] = {}
    for att, (_, info) in _RPC_SERVICE_METHODS.collect(type(service)).items():
        if info.name in out:
            raise KeyError(f'duplicate rpc service method: {info.name!r}')
        out[info.name] = rpc_typed_method(
            getattr(service, att),
            info.params_type,
            info.result_type,
            serde=serde,
        )
    return out


#


@dc.dataclass(frozen=True)
class GreetRequest:
    name: str
    excited: bool = False


@dc.dataclass(frozen=True)
class GreetResult:
    greeting: str


class GreeterService:
    @rpc_service_method('greeter.greet', GreetRequest, GreetResult)
    async def greet(self, req: GreetRequest) -> GreetResult:
        return GreetResult(f'hello, {req.name}' + ('!' if req.excited else ''))

    @rpc_service_method('greeter.count')
    async def count(self) -> int:
        return 1


class LoudGreeterService(GreeterService):
    @rpc_service_method('greeter.greet', GreetRequest, GreetResult)
    async def greet(self, req: GreetRequest) -> GreetResult:
        return GreetResult(f'HELLO, {req.name.upper()}!')

    # Shadowed without the mark: withdrawn from the subclass's table.
    async def count(self) -> int:
        raise NotImplementedError


##
# polymorphic commands


@msh.set_polymorphic(
    naming='snake',
    suffix_stripping='required',
)
class Command(lang.Abstract):
    pass


@dc.dataclass(frozen=True)
class EchoCommand(Command):
    message: str


@dc.dataclass(frozen=True)
class AddCommand(Command):
    x: int
    y: int


@dc.dataclass(frozen=True)
class ConcatCommand(Command):
    parts: ta.Sequence[str]


COMMAND_EXECUTE_METHOD = 'command.execute'


class CommandService:
    @dispatch.method(instance_cache=True)
    async def execute(self, cmd: Command) -> ta.Any:
        raise TypeError(cmd)

    @execute.register
    async def execute_echo(self, cmd: EchoCommand) -> ta.Any:
        return cmd.message

    @execute.register
    async def execute_add(self, cmd: AddCommand) -> ta.Any:
        return cmd.x + cmd.y

    @execute.register
    async def execute_concat(self, cmd: ConcatCommand) -> ta.Any:
        return ''.join(cmd.parts)

    def method_table(self, serde: RpcSerde) -> dict[str, RpcMethodFn]:
        return {COMMAND_EXECUTE_METHOD: rpc_typed_method(self.execute, Command, serde=serde)}


class CommandClient:
    def __init__(self, connection: RpcConnection, serde: RpcSerde) -> None:
        super().__init__()

        self._caller = RpcTypedCaller(connection, serde)

    async def execute(self, cmd: Command, result_type: ta.Any = None) -> ta.Any:
        return await self._caller.call(COMMAND_EXECUTE_METHOD, cmd, result_type, params_type=Command)
