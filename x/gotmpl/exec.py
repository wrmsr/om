"""Translation of Go's text/template/exec.go."""

# Copyright 2011 The Go Authors.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#      disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#      following disclaimer in the documentation and/or other materials provided with the distribution.
#    * Neither the name of Google LLC nor the names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import collections.abc
import inspect
import io
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from .funcs import call
from .funcs import find_function
from .funcs import go_format_value
from .funcs import map_zero_value
from .funcs import safe_call
from .funcs import truth
from .nodes import ActionNode
from .nodes import BoolNode
from .nodes import BreakNode
from .nodes import ChainNode
from .nodes import CommandNode
from .nodes import CommentNode
from .nodes import ContinueNode
from .nodes import DotNode
from .nodes import FieldNode
from .nodes import IdentifierNode
from .nodes import IfNode
from .nodes import ListNode
from .nodes import NilNode
from .nodes import Node
from .nodes import NodeType
from .nodes import NumberNode
from .nodes import PipeNode
from .nodes import RangeNode
from .nodes import StringNode
from .nodes import TemplateNode
from .nodes import TextNode
from .nodes import VariableNode
from .nodes import WithNode
from .quoting import quote_go_string
from .values import MISSING
from .values import is_missing


if ta.TYPE_CHECKING:
    from .tmpl import Template


MAX_EXEC_DEPTH = 100_000


##


_MISSING_VAL = MISSING


def double_percent(value: str) -> str:
    return value.replace('%', '%%')


# ExecError is the custom error type returned when execute has an error evaluating its template. Writer errors escape
# unchanged, matching Go's distinction between execution and output failures.
@dc.dataclass()
class ExecError(Exception):
    name: str
    msg: str

    def __post_init__(self) -> None:
        super().__init__(self.msg)

    def __str__(self) -> str:
        return self.msg


@dc.dataclass()
class Variable:
    name: str
    value: ta.Any


class _WalkBreakError(Exception):
    __slots__ = ()


class _WalkContinueError(Exception):
    __slots__ = ()


@dc.dataclass()
class State:
    tmpl: Template
    wr: ta.TextIO
    vars: list[Variable]
    node: Node | None = None
    depth: int = 0

    def push(self, name: str, value: ta.Any) -> None:
        self.vars.append(Variable(name, value))

    def mark(self) -> int:
        return len(self.vars)

    def pop(self, mark: int) -> None:
        del self.vars[mark:]

    def set_var(self, name: str, value: ta.Any) -> None:
        for variable in reversed(self.vars):
            if variable.name == name:
                variable.value = value
                return
        self.errorf('undefined variable: %s', name)

    def set_top_var(self, n: int, value: ta.Any) -> None:
        self.vars[len(self.vars) - n].value = value

    def var_value(self, name: str) -> ta.Any:
        for variable in reversed(self.vars):
            if variable.name == name:
                return variable.value
        self.errorf('undefined variable: %s', name)
        raise AssertionError('unreachable')

    def at(self, node: Node) -> None:
        self.node = node

    def errorf(self, format_string: str, *args: ta.Any) -> ta.NoReturn:
        name = double_percent(self.tmpl.name)
        if self.node is None or self.tmpl.tree is None:
            message_format = f'template: {name}: {format_string}'
        else:
            location, context = self.tmpl.tree.error_context(self.node)
            message_format = (
                f'template: {double_percent(location)}: executing {name} '
                f'at <{double_percent(context)}>: {format_string}'
            )
        raise ExecError(name=self.tmpl.name, msg=message_format % args)

    # Walk functions step through the major pieces of the template structure, generating output as they go.
    def walk(self, dot: ta.Any, node: Node) -> None:
        self.at(node)
        if isinstance(node, ActionNode):
            # Do not pop variables so they persist until the next end. If the action declares variables, do not print
            # its result.
            value = self.eval_pipeline(dot, node.pipe)
            if not node.pipe.decl:
                self.print_value(node, value)
        elif isinstance(node, BreakNode):
            raise _WalkBreakError
        elif isinstance(node, CommentNode):
            return
        elif isinstance(node, ContinueNode):
            raise _WalkContinueError
        elif isinstance(node, IfNode):
            self.walk_if_or_with(NodeType.IF, dot, node.pipe, node.lst, node.else_lst)
        elif isinstance(node, ListNode):
            for child in node.nodes:
                self.walk(dot, child)
        elif isinstance(node, RangeNode):
            self.walk_range(dot, node)
        elif isinstance(node, TemplateNode):
            self.walk_template(dot, node)
        elif isinstance(node, TextNode):
            self.wr.write(node.text)
        elif isinstance(node, WithNode):
            self.walk_if_or_with(NodeType.WITH, dot, node.pipe, node.lst, node.else_lst)
        else:
            self.errorf('unknown node: %s', node)

    def walk_if_or_with(
        self,
        typ: NodeType,
        dot: ta.Any,
        pipe: PipeNode,
        lst: ListNode,
        else_lst: ListNode | None,
    ) -> None:
        mark = self.mark()
        try:
            value = self.eval_pipeline(dot, pipe)
            condition, ok = is_true(value)
            if not ok:
                self.errorf("if/with can't use %s", go_format_value(value))
            if condition:
                self.walk(value if typ == NodeType.WITH else dot, lst)
            elif else_lst is not None:
                self.walk(dot, else_lst)
        finally:
            self.pop(mark)

    def walk_range(self, dot: ta.Any, node: RangeNode) -> None:
        self.at(node)
        outer_mark = self.mark()
        try:
            value = self.eval_pipeline(dot, node.pipe)
            mark = self.mark()

            def one_iteration(index: ta.Any, element: ta.Any) -> None:
                if node.pipe.decl:
                    if node.pipe.is_assign:
                        if len(node.pipe.decl) > 1:
                            self.set_var(node.pipe.decl[0].ident[0], index)
                        else:
                            self.set_var(node.pipe.decl[0].ident[0], element)
                    else:
                        self.set_top_var(1, element)
                if len(node.pipe.decl) > 1:
                    if node.pipe.is_assign:
                        self.set_var(node.pipe.decl[1].ident[0], element)
                    else:
                        self.set_top_var(2, index)
                try:
                    self.walk(element, node.lst)
                except _WalkContinueError:
                    pass
                finally:
                    self.pop(mark)

            iterations: ta.Iterable[tuple[ta.Any, ta.Any]]
            if is_missing(value) or value is None:
                iterations = ()
            elif isinstance(value, bool):
                self.errorf("range can't iterate over %s", go_format_value(value))
            elif isinstance(value, int):
                if len(node.pipe.decl) > 1:
                    self.errorf("can't use %s to iterate over more than one variable", go_format_value(value))
                iterations = ((None, i) for i in range(max(value, 0)))
            elif isinstance(value, collections.abc.Mapping):
                try:
                    keys = sorted(value)
                except TypeError:
                    keys = sorted(value, key=lambda key: (type(key).__name__, repr(key)))
                iterations = ((key, value[key]) for key in keys)
            elif isinstance(value, (list, tuple, bytes, bytearray)):
                iterations = enumerate(value)
            elif isinstance(value, str):
                self.errorf("range can't iterate over %s", go_format_value(value))
            elif isinstance(value, collections.abc.Iterable):
                iterations = enumerate(value)
            else:
                self.errorf("range can't iterate over %s", go_format_value(value))

            ran = False
            try:
                for index, element in iterations:
                    ran = True
                    one_iteration(index, element)
            except _WalkBreakError:
                return
            if not ran and node.else_lst is not None:
                self.walk(dot, node.else_lst)
        finally:
            self.pop(outer_mark)

    def walk_template(self, dot: ta.Any, node: TemplateNode) -> None:
        self.at(node)
        tmpl = self.tmpl.lookup(node.name)
        if tmpl is None:
            self.errorf('template %s not defined', quote_go_string(node.name))
        if self.depth == MAX_EXEC_DEPTH:
            self.errorf('exceeded maximum template depth (%d)', MAX_EXEC_DEPTH)
        dot = self.eval_pipeline(dot, node.pipe)
        new_state = State(
            tmpl=tmpl,
            wr=self.wr,
            vars=[Variable('$', dot)],
            depth=self.depth + 1,
        )
        new_state.walk(dot, check.not_none(check.not_none(tmpl.tree).root))

    # Eval functions evaluate pipelines, commands, and their elements. Printing happens only through walk functions.
    def eval_pipeline(self, dot: ta.Any, pipe: PipeNode | None) -> ta.Any:
        if pipe is None:
            return _MISSING_VAL
        self.at(pipe)
        value: ta.Any = _MISSING_VAL
        for command in pipe.cmds:
            value = self.eval_command(dot, command, value)
        for variable in pipe.decl:
            if pipe.is_assign:
                self.set_var(variable.ident[0], value)
            else:
                self.push(variable.ident[0], value)
        return value

    def not_a_function(self, args: ta.Sequence[Node], final: ta.Any) -> None:
        if len(args) > 1 or not is_missing(final):
            self.errorf("can't give argument to non-function %s", args[0])

    def eval_command(self, dot: ta.Any, command: CommandNode, final: ta.Any) -> ta.Any:
        first_word = command.args[0]
        if isinstance(first_word, FieldNode):
            return self.eval_field_node(dot, first_word, command.args, final)
        if isinstance(first_word, ChainNode):
            return self.eval_chain_node(dot, first_word, command.args, final)
        if isinstance(first_word, IdentifierNode):
            return self.eval_function(dot, first_word, command, command.args, final)
        if isinstance(first_word, PipeNode):
            self.not_a_function(command.args, final)
            return self.eval_pipeline(dot, first_word)
        if isinstance(first_word, VariableNode):
            return self.eval_variable_node(dot, first_word, command.args, final)
        self.at(first_word)
        self.not_a_function(command.args, final)
        if isinstance(first_word, BoolNode):
            return first_word.is_true
        if isinstance(first_word, DotNode):
            return dot
        if isinstance(first_word, NilNode):
            self.errorf('nil is not a command')
        if isinstance(first_word, NumberNode):
            return self.ideal_constant(first_word)
        if isinstance(first_word, StringNode):
            return first_word.text
        self.errorf("can't evaluate command %s", quote_go_string(str(first_word)))
        raise AssertionError('unreachable')

    def ideal_constant(self, constant: NumberNode) -> int | float | complex:
        self.at(constant)
        if constant.is_complex:
            return constant.complex128
        if (
            constant.is_float
            and not is_hex_int(constant.text)
            and not is_rune_int(constant.text)
            and any(char in constant.text for char in '.eEpP')
        ):
            return constant.float64
        if constant.is_int:
            return constant.int64
        if constant.is_uint:
            self.errorf('%s overflows int', constant.text)
        self.errorf('invalid ideal constant %s', constant.text)
        raise AssertionError('unreachable')

    def eval_field_node(
        self,
        dot: ta.Any,
        field: FieldNode,
        args: ta.Sequence[Node] | None,
        final: ta.Any,
    ) -> ta.Any:
        self.at(field)
        return self.eval_field_chain(dot, dot, field, field.ident, args, final)

    def eval_chain_node(
        self,
        dot: ta.Any,
        chain: ChainNode,
        args: ta.Sequence[Node] | None,
        final: ta.Any,
    ) -> ta.Any:
        self.at(chain)
        if not chain.field:
            self.errorf('internal error: no fields in eval_chain_node')
        if isinstance(chain.node, NilNode):
            self.errorf('indirection through explicit nil in %s', chain)
        receiver = self.eval_arg(dot, chain.node)
        return self.eval_field_chain(dot, receiver, chain, chain.field, args, final)

    def eval_variable_node(
        self,
        dot: ta.Any,
        variable: VariableNode,
        args: ta.Sequence[Node] | None,
        final: ta.Any,
    ) -> ta.Any:
        self.at(variable)
        value = self.var_value(variable.ident[0])
        if len(variable.ident) == 1:
            self.not_a_function(args or (variable,), final)
            return value
        return self.eval_field_chain(dot, value, variable, variable.ident[1:], args, final)

    def eval_field_chain(
        self,
        dot: ta.Any,
        receiver: ta.Any,
        node: Node,
        ident: ta.Sequence[str],
        args: ta.Sequence[Node] | None,
        final: ta.Any,
    ) -> ta.Any:
        for field_name in ident[:-1]:
            receiver = self.eval_field(dot, field_name, node, None, _MISSING_VAL, receiver)
        return self.eval_field(dot, ident[-1], node, args, final, receiver)

    def eval_function(
        self,
        dot: ta.Any,
        node: IdentifierNode,
        command: Node,
        args: ta.Sequence[Node] | None,
        final: ta.Any,
    ) -> ta.Any:
        self.at(node)
        function, is_builtin = find_function(node.ident, self.tmpl)
        if function is None:
            self.errorf('%s is not a defined function', quote_go_string(node.ident))
        return self.eval_call(dot, function, is_builtin, command, node.ident, args, final)

    def eval_field(
        self,
        dot: ta.Any,
        field_name: str,
        node: Node,
        args: ta.Sequence[Node] | None,
        final: ta.Any,
        receiver: ta.Any,
    ) -> ta.Any:
        if is_missing(receiver) or receiver is None:
            if self.tmpl.missing_key_action.name == 'ERROR':
                self.errorf('nil data; no entry for key %s', quote_go_string(field_name))
            return _MISSING_VAL

        has_args = bool(args and len(args) > 1) or not is_missing(final)
        if isinstance(receiver, collections.abc.Mapping):
            if has_args:
                self.errorf('%s is not a method but has arguments', field_name)
            if field_name in receiver:
                return receiver[field_name]
            action = self.tmpl.missing_key_action.name
            if action == 'ZERO_VALUE':
                return map_zero_value(receiver)
            if action == 'ERROR':
                self.errorf('map has no entry for key %s', quote_go_string(field_name))
            return _MISSING_VAL

        if not field_name[:1].isupper():
            self.errorf('%s is an unexported field of struct type %s', field_name, type(receiver).__name__)
        try:
            value = getattr(receiver, field_name)
        except AttributeError:
            self.errorf("can't evaluate field %s in type %s", field_name, type(receiver).__name__)
        except Exception as exc:  # noqa: BLE001 - descriptor access may run arbitrary user code.
            self.errorf('error evaluating field %s: %s', field_name, exc)
        if inspect.ismethod(value) or inspect.isbuiltin(value):
            return self.eval_call(dot, value, False, node, field_name, args, final)
        if has_args:
            self.errorf('%s has arguments but cannot be invoked as function', field_name)
        return value

    def eval_call(
        self,
        dot: ta.Any,
        function: ta.Callable[..., ta.Any],
        is_builtin: bool,
        node: Node,
        name: str,
        args: ta.Sequence[Node] | None,
        final: ta.Any,
    ) -> ta.Any:
        arg_nodes = list(args[1:] if args is not None else ())

        if is_builtin and name in ('and', 'or'):
            if not arg_nodes and is_missing(final):
                self.errorf('wrong number of args for %s: want at least 1 got 0', name)
            value: ta.Any = _MISSING_VAL
            for arg_node in arg_nodes:
                value = self.eval_arg(dot, arg_node)
                if truth(value) == (name == 'or'):
                    return value
            if not is_missing(final):
                return final
            return value

        argv = [self.eval_arg(dot, arg_node) for arg_node in arg_nodes]
        if not is_missing(final):
            argv.append(final)

        if is_builtin and name == 'call':
            if not argv:
                self.errorf('wrong number of args for call: want at least 1 got 0')
            callee = argv.pop(0)
            callee_name = arg_nodes[0].string() if arg_nodes else 'call'

            def call_function(*call_args: ta.Any) -> ta.Any:
                return call(callee_name, callee, *call_args)

            function = call_function

        elif not is_builtin:
            argv = [None if is_missing(value) else value for value in argv]

        try:
            # Binding first produces a stable template error instead of exposing Python's call-site traceback.
            try:
                inspect.signature(function).bind(*argv)
            except ValueError:
                pass
            return safe_call(function, argv)
        except ExecError:
            raise
        except Exception as exc:  # noqa: BLE001 - template calls must translate arbitrary user errors.
            self.at(node)
            self.errorf('error calling %s: %s', name, exc)

    def eval_arg(self, dot: ta.Any, node: Node) -> ta.Any:
        self.at(node)
        if isinstance(node, DotNode):
            return dot
        if isinstance(node, NilNode):
            return None
        if isinstance(node, FieldNode):
            return self.eval_field_node(dot, node, (node,), _MISSING_VAL)
        if isinstance(node, VariableNode):
            return self.eval_variable_node(dot, node, None, _MISSING_VAL)
        if isinstance(node, PipeNode):
            return self.eval_pipeline(dot, node)
        if isinstance(node, IdentifierNode):
            return self.eval_function(dot, node, node, None, _MISSING_VAL)
        if isinstance(node, ChainNode):
            return self.eval_chain_node(dot, node, None, _MISSING_VAL)
        if isinstance(node, BoolNode):
            return node.is_true
        if isinstance(node, NumberNode):
            return self.ideal_constant(node)
        if isinstance(node, StringNode):
            return node.text
        self.errorf("can't handle assignment of %s to empty interface argument", node)
        raise AssertionError('unreachable')

    def print_value(self, node: Node, value: ta.Any) -> None:
        self.at(node)
        if is_missing(value) or value is None:
            self.wr.write('<no value>')
            return
        if callable(value):
            self.errorf("can't print %s of type %s", node, type(value).__name__)
        self.wr.write(go_format_value(value))


##


def is_true(value: ta.Any) -> tuple[bool, bool]:
    if is_missing(value):
        return False, True
    return truth(value), True


def is_rune_int(value: str) -> bool:
    return value.startswith("'")


def is_hex_int(value: str) -> bool:
    return len(value) > 2 and value[:2].lower() == '0x' and 'p' not in value.lower()


def execute_template(tmpl: Template, wr: ta.TextIO, name: str, data: ta.Any = None) -> None:
    found = tmpl.lookup(name)
    if found is None:
        raise ExecError(
            name=tmpl.name,
            msg=(
                f'template: no template {quote_go_string(name)} associated with template {quote_go_string(tmpl.name)}'
            ),
        )
    execute(found, wr, data)


def execute(tmpl: Template, wr: ta.TextIO, data: ta.Any = None) -> None:
    state = State(tmpl=tmpl, wr=wr, vars=[Variable('$', data)])
    if tmpl.tree is None or tmpl.tree.root is None:
        state.errorf('%s is an incomplete or empty template', quote_go_string(tmpl.name))
    state.walk(data, tmpl.tree.root)


def render(tmpl: Template, data: ta.Any = None) -> str:
    wr = io.StringIO()
    execute(tmpl, wr, data)
    return wr.getvalue()


def defined_templates(tmpl: Template) -> str:
    common = tmpl._common  # noqa: SLF001
    if common is None:
        return ''
    names: list[str] = []
    with common.tmpl_lock:
        for name, associated in common.tmpl.items():
            if associated.tree is not None and associated.tree.root is not None:
                names.append(quote_go_string(name))
    if not names:
        return ''
    return '; defined templates are: ' + ', '.join(names)
