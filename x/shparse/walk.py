# Copyright (c) 2016, Daniel Martí. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#   disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
#   disclaimer in the documentation and/or other materials provided with the distribution.
# * Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote
#   products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import enum
import functools
import typing as ta

from omcore import dataclasses as dc

from .nodes import ArithmCmd
from .nodes import ArithmExp
from .nodes import ArrayElem
from .nodes import ArrayExpr
from .nodes import Assign
from .nodes import BinaryArithm
from .nodes import BinaryCmd
from .nodes import BinaryTest
from .nodes import Block
from .nodes import CallExpr
from .nodes import CaseClause
from .nodes import CaseItem
from .nodes import CmdSubst
from .nodes import Comment
from .nodes import CoprocClause
from .nodes import CStyleLoop
from .nodes import DblQuoted
from .nodes import DeclClause
from .nodes import ExtGlob
from .nodes import File
from .nodes import FlagsArithm
from .nodes import ForClause
from .nodes import FuncDecl
from .nodes import IfClause
from .nodes import LetClause
from .nodes import Lit
from .nodes import Node
from .nodes import ParamExp
from .nodes import ParenArithm
from .nodes import ParenTest
from .nodes import Pos
from .nodes import ProcSubst
from .nodes import Redirect
from .nodes import SglQuoted
from .nodes import Stmt
from .nodes import Subshell
from .nodes import TestClause
from .nodes import TestDecl
from .nodes import TimeClause
from .nodes import UnaryArithm
from .nodes import UnaryTest
from .nodes import WhileClause
from .nodes import Word
from .nodes import WordIter


##


# walk traverses a syntax tree in depth-first order: It starts by calling
# f(node); node must not be nil. If f returns true, Walk invokes f
# recursively for each of the non-nil children of node, followed by
# f(nil).
def walk(node: Node, f: ta.Callable[[Node | None], bool]) -> None:
    if not f(node):
        return

    defers: list[ta.Callable[[], None]] = []

    if isinstance(node, File):
        walk_list(node.stmts, f)
        walk_comments(node.last, f)
    elif isinstance(node, Comment):
        pass
    elif isinstance(node, Stmt):
        for c in node.comments:
            if not node.end().after(c.pos()):
                defers.append(functools.partial(walk, c, f))
                break
            walk(c, f)
        if node.cmd is not None:
            walk(node.cmd, f)
        walk_list(node.redirs, f)
    elif isinstance(node, Assign):
        walk_nilable(node.name, f)
        walk_nilable(node.value, f)
        walk_nilable(node.index, f)
        walk_nilable(node.array, f)
    elif isinstance(node, Redirect):
        walk_nilable(node.n, f)
        walk(node.word, f)
        walk_nilable(node.hdoc, f)
    elif isinstance(node, CallExpr):
        walk_list(node.assigns, f)
        walk_list(node.args, f)
    elif isinstance(node, Subshell):
        walk_list(node.stmts, f)
        walk_comments(node.last, f)
    elif isinstance(node, Block):
        walk_list(node.stmts, f)
        walk_comments(node.last, f)
    elif isinstance(node, IfClause):
        walk_list(node.cond, f)
        walk_comments(node.cond_last, f)
        walk_list(node.then, f)
        walk_comments(node.then_last, f)
        walk_nilable(node.else_, f)
    elif isinstance(node, WhileClause):
        walk_list(node.cond, f)
        walk_comments(node.cond_last, f)
        walk_list(node.do, f)
        walk_comments(node.do_last, f)
    elif isinstance(node, ForClause):
        walk_nilable(node.loop, f)
        walk_list(node.do, f)
        walk_comments(node.do_last, f)
    elif isinstance(node, WordIter):
        walk(node.name, f)
        walk_list(node.items, f)
    elif isinstance(node, CStyleLoop):
        walk_nilable(node.init, f)
        walk_nilable(node.cond, f)
        walk_nilable(node.post, f)
    elif isinstance(node, BinaryCmd):
        walk(node.x, f)
        walk(node.y, f)
    elif isinstance(node, FuncDecl):
        walk_nilable(node.name, f)
        walk_list(node.names, f)
        walk_nilable(node.body, f)
    elif isinstance(node, Word):
        walk_list(node.parts, f)
    elif isinstance(node, (Lit, SglQuoted)):
        pass
    elif isinstance(node, DblQuoted):
        walk_list(node.parts, f)
    elif isinstance(node, CmdSubst):
        walk_list(node.stmts, f)
        walk_comments(node.last, f)
    elif isinstance(node, ParamExp):
        walk_nilable(node.flags, f)
        walk_nilable(node.param, f)
        walk_nilable(node.nested_param, f)
        walk_nilable(node.index, f)
        if node.slice is not None:
            walk_nilable(node.slice.offset, f)
            walk_nilable(node.slice.length, f)
        if node.repl is not None:
            walk_nilable(node.repl.orig, f)
            walk_nilable(node.repl.with_, f)
        if node.exp is not None:
            walk_nilable(node.exp.word, f)
    elif isinstance(node, ArithmExp):
        walk_nilable(node.x, f)
    elif isinstance(node, ArithmCmd):
        walk_nilable(node.x, f)
    elif isinstance(node, BinaryArithm):
        walk_nilable(node.x, f)
        walk_nilable(node.y, f)
    elif isinstance(node, BinaryTest):
        walk_nilable(node.x, f)
        walk_nilable(node.y, f)
    elif isinstance(node, UnaryArithm):
        walk_nilable(node.x, f)
    elif isinstance(node, UnaryTest):
        walk_nilable(node.x, f)
    elif isinstance(node, ParenArithm):
        walk_nilable(node.x, f)
    elif isinstance(node, FlagsArithm):
        walk_nilable(node.flags, f)
        walk_nilable(node.x, f)
    elif isinstance(node, ParenTest):
        walk_nilable(node.x, f)
    elif isinstance(node, CaseClause):
        walk_nilable(node.word, f)
        walk_list(node.items, f)
        walk_comments(node.last, f)
    elif isinstance(node, CaseItem):
        for c in node.comments:
            if c.pos().after(node.pos()):
                defers.append(functools.partial(walk, c, f))
                break
            walk(c, f)
        walk_list(node.patterns, f)
        walk_list(node.stmts, f)
        walk_comments(node.last, f)
    elif isinstance(node, TestClause):
        walk_nilable(node.x, f)
    elif isinstance(node, DeclClause):
        walk_list(node.args, f)
    elif isinstance(node, ArrayExpr):
        walk_list(node.elems, f)
        walk_comments(node.last, f)
    elif isinstance(node, ArrayElem):
        for c in node.comments:
            if c.pos().after(node.pos()):
                defers.append(functools.partial(walk, c, f))
                break
            walk(c, f)
        walk_nilable(node.index, f)
        walk_nilable(node.value, f)
    elif isinstance(node, ExtGlob):
        walk_nilable(node.pattern, f)
    elif isinstance(node, ProcSubst):
        walk_list(node.stmts, f)
        walk_comments(node.last, f)
    elif isinstance(node, TimeClause):
        walk_nilable(node.stmt, f)
    elif isinstance(node, CoprocClause):
        walk_nilable(node.name, f)
        walk_nilable(node.stmt, f)
    elif isinstance(node, LetClause):
        walk_list(node.exprs, f)
    elif isinstance(node, TestDecl):
        walk_nilable(node.description, f)
        walk_nilable(node.body, f)
    else:
        raise TypeError(node)

    f(None)

    for defer in defers:
        defer()


def walk_nilable(node: Node | None, f: ta.Callable[[Node | None], bool]) -> None:
    if node is not None:
        walk(node, f)


NodeT = ta.TypeVar('NodeT', bound=Node)


def walk_list(lst: ta.Sequence[NodeT], f: ta.Callable[[Node | None], bool]) -> None:
    for node in lst:
        walk(node, f)


def walk_comments(lst: ta.Sequence[Comment], f: ta.Callable[[Node | None], bool]) -> None:
    # Note that []Comment does not satisfy the generic constraint []Node.
    for n in lst:
        walk(n, f)


# DebugPrint prints the provided syntax tree, spanning multiple lines and with
# indentation. Can be useful to investigate the content of a syntax tree.
def debug_print(out: ta.TextIO, node: Node) -> None:
    """Write a multiline representation of a syntax tree."""

    printer = _DebugPrinter(out)
    printer.print(node)
    out.write('\n')


class _DebugPrinter:
    def __init__(self, out: ta.TextIO) -> None:
        super().__init__()

        self._out = out
        self._level = 0

    def _newline(self) -> None:
        self._out.write('\n')
        self._out.write('.  ' * self._level)

    def print(self, value: ta.Any) -> None:
        if value is None:
            self._out.write('None')
        elif isinstance(value, Pos):
            if value.is_recovered():
                self._out.write('<recovered>')
            else:
                self._out.write(value.string())
        elif isinstance(value, list):
            self._out.write(f'list (len = {len(value)}) {{')
            if value:
                self._level += 1
                self._newline()
                for index, item in enumerate(value):
                    self._out.write(f'{index}: ')
                    self.print(item)
                    if index == len(value) - 1:
                        self._level -= 1
                    self._newline()
            self._out.write('}')
        elif dc.is_dataclass(value):
            self._out.write(f'{type(value).__name__} {{')
            fields = dc.fields(value)
            if fields:
                self._level += 1
                self._newline()
                for index, field in enumerate(fields):
                    self._out.write(f'{field.name}: ')
                    self.print(getattr(value, field.name))
                    if index == len(fields) - 1:
                        self._level -= 1
                    self._newline()
            self._out.write('}')
        elif isinstance(value, enum.Enum):
            self._out.write(repr(value.value))
        else:
            self._out.write(repr(value))
