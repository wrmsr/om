import typing as ta

from ... import dataclasses as dc


##


@dc.dataclass(frozen=True)
class SourceSpan:
    start: int
    end: int


@dc.dataclass(frozen=True, kw_only=True)
class Node:
    span: SourceSpan


@dc.dataclass(frozen=True)
class Identity(Node):
    pass


@dc.dataclass(frozen=True)
class Empty(Node):
    pass


@dc.dataclass(frozen=True)
class Literal(Node):
    value: ta.Any


@dc.dataclass(frozen=True)
class Variable(Node):
    name: str


@dc.dataclass(frozen=True)
class Call(Node):
    name: str
    arguments: tuple[Node, ...]


@dc.dataclass(frozen=True)
class Comma(Node):
    left: Node
    right: Node


@dc.dataclass(frozen=True)
class Pipe(Node):
    left: Node
    right: Node


@dc.dataclass(frozen=True)
class Array(Node):
    value: Node | None


@dc.dataclass(frozen=True)
class ObjectMember:
    key: Node
    value: Node


@dc.dataclass(frozen=True)
class Object(Node):
    members: tuple[ObjectMember, ...]


@dc.dataclass(frozen=True)
class Index(Node):
    value: Node
    key: Node


@dc.dataclass(frozen=True)
class Iterate(Node):
    value: Node


@dc.dataclass(frozen=True)
class Slice(Node):
    value: Node
    start: Node | None
    end: Node | None


@dc.dataclass(frozen=True)
class Optional(Node):
    value: Node


@dc.dataclass(frozen=True)
class RecursiveDescent(Node):
    pass


@dc.dataclass(frozen=True)
class Unary(Node):
    operator: str
    operand: Node


@dc.dataclass(frozen=True)
class Binary(Node):
    operator: str
    left: Node
    right: Node


@dc.dataclass(frozen=True)
class Alternative(Node):
    left: Node
    right: Node


@dc.dataclass(frozen=True)
class Assignment(Node):
    operator: str
    left: Node
    right: Node


@dc.dataclass(frozen=True)
class Binding(Node):
    source: Node
    name: str
    body: Node


@dc.dataclass(frozen=True)
class IfBranch:
    condition: Node
    body: Node


@dc.dataclass(frozen=True)
class Conditional(Node):
    branches: tuple[IfBranch, ...]
    otherwise: Node


@dc.dataclass(frozen=True)
class FunctionParameter:
    name: str
    binding: bool


@dc.dataclass(frozen=True)
class FunctionDefinition(Node):
    name: str
    parameters: tuple[FunctionParameter, ...]
    body: Node
    next: Node


@dc.dataclass(frozen=True)
class Reduce(Node):
    source: Node
    variable: str
    initial: Node
    update: Node


@dc.dataclass(frozen=True)
class Foreach(Node):
    source: Node
    variable: str
    initial: Node
    update: Node
    extract: Node


@dc.dataclass(frozen=True)
class Try(Node):
    value: Node
    handler: Node | None


@dc.dataclass(frozen=True)
class Label(Node):
    name: str
    body: Node


@dc.dataclass(frozen=True)
class Break(Node):
    name: str


StringPart: ta.TypeAlias = str | Node


@dc.dataclass(frozen=True)
class String(Node):
    parts: tuple[StringPart, ...]
