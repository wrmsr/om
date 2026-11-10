# ruff: noqa: SLF001
"""Scope and variable tracking for Hy/Python scopes."""
import abc
import ast
import itertools
import typing as ta

from omcore import check
from omcore import lang

from .models import Expression
from .models import List
from .models import Object
from .models import Symbol
from .models import Tuple
from .reader import mangle


if ta.TYPE_CHECKING:
    from .compiler import HyASTCompiler


AstT = ta.TypeVar('AstT', bound=ast.AST)
ScopeT = ta.TypeVar('ScopeT', bound='ScopeBase')


##


def is_function_scope(scope: ScopeBase) -> bool:
    return isinstance(scope, ScopeFn) and scope.is_fn


def is_inside_function_scope(scope: ScopeBase) -> bool:
    """True if any enclosing scope (including this one) is a function scope."""

    cur: ScopeBase | None = scope
    while cur is not None and not isinstance(cur, ScopeGlobal):
        if is_function_scope(cur):
            return True
        cur = cur.parent
    return False


def nearest_python_scope(scope: ScopeBase | None) -> ScopeBase:
    """Return the closest enclosing scope that corresponds to a Python scope."""

    cur = scope
    while isinstance(cur, (ScopeLet, ScopeGen)):
        cur = cur.parent
    return check.not_none(cur)


class OuterVar(ast.stmt):
    """Custom AST node that can compile to either Nonlocal or Global."""

    def __init__(self, expr: Object | ast.AST, scope: ScopeBase, names: list[str]) -> None:
        from .compiler import asty
        super().__init__()
        self.__dict__.update(asty._get_pos(expr))
        self._scope = scope
        self.names = names


class ResolveOuterVars(ast.NodeTransformer):
    """Find all OuterVar nodes and replace with Nonlocal or Global as necessary."""

    def visit_OuterVar(self, node: OuterVar) -> list[ast.stmt]:
        from .compiler import asty

        scope = node._scope
        defined: set[str] = set()
        undefined = list(node.names)  # keep order, so can't use set
        while undefined and scope.parent:
            scope = scope.parent
            has = set()
            if isinstance(scope, ScopeFn):
                has = scope.defined
            elif isinstance(scope, ScopeLet):
                has = set(scope.bindings.keys())
            elif isinstance(scope, ScopeGlobal):
                res = []
                if not scope.defined.issuperset(undefined):
                    # emit nonlocal, let python raise the error
                    break
                if undefined:
                    res.append(asty.Global(node, names=list(undefined)))
                if defined:
                    res.append(asty.Nonlocal(node, names=list(defined)))
                return res
            defined.update(has.intersection(undefined))
            undefined = [name for name in undefined if name not in has]
        return [asty.Nonlocal(node, names=node.names)] if node.names else []


class NodeRef:
    """
    Wrapper for AST nodes that have symbol names, so that we can rename them if necessary. Each `NodeRef` corresponds to
    one Python identifier. `ast` nodes that accept multiple identifier names (`global`, `nonlocal`, etc) have their
    specific identifier referenced by their `index` in the list of `names` provided by the `ast` node.
    """

    ACCESSOR: ta.ClassVar[dict[type[ast.AST], str]] = {
        ast.Name: 'id',
        ast.Global: 'names',
        ast.Nonlocal: 'names',
        OuterVar: 'names',
        ast.MatchAs: 'name',
        ast.MatchStar: 'name',
        ast.MatchMapping: 'rest',
    }

    def __init__(self, node: ast.AST, index: int | None = None) -> None:
        super().__init__()

        self.node = node
        self.index = index
        self._accessor = NodeRef.ACCESSOR[type(self.node)]

    @property
    def name(self) -> str:
        res = getattr(self.node, self._accessor)
        if self.index is not None:
            return res[self.index]
        return res

    @name.setter
    def name(self, new_name: str) -> None:
        """Used to rename `ast` identifiers"""

        if self.index is not None:
            getattr(self.node, self._accessor)[self.index] = new_name
        else:
            setattr(self.node, self._accessor, new_name)

    @staticmethod
    def wrap(f: ta.Callable[..., AstT]) -> ta.Callable[..., AstT]:
        """Decorator to convert AST node parameter to NodeRef."""

        def _wrapper(self, node: ast.AST | NodeRef, index: int | None = None) -> AstT:
            if not isinstance(node, NodeRef):
                node = NodeRef(node, index)
            return f(self, node)

        return _wrapper

    def __repr__(self) -> str:
        return (
            f'NodeRef(name={self.name}, node={type(self.node).__name__},'
            f' index={self.index})'
        )


class ScopeBase(lang.Abstract):
    def __init__(self, compiler: HyASTCompiler) -> None:
        super().__init__()

        self.parent: ScopeBase | None = None
        self.compiler = compiler
        self.children: list[ScopeBase] = []

    def create(self, scope_type: type[ScopeT], *args: ta.Any) -> ScopeT:
        """Create new scope from this one."""

        return scope_type(self.compiler, *args)

    def __enter__(self) -> ta.Self:
        if self.compiler.scope is not self:
            self.parent = self.compiler.scope
            if self not in self.parent.children:
                self.parent.children.append(self)
        self.compiler.scope = self
        return self

    def __exit__(self, *args: object) -> ta.Literal[False]:
        if self.parent:
            self.compiler.scope = self.parent
        return False

    # Scope interface
    @abc.abstractmethod
    def access(self, node: ast.AST | NodeRef, index: int | None = None) -> ast.AST:
        """Called when a symbol is accessed."""

        raise NotImplementedError

    @abc.abstractmethod
    def assign(self, node: ast.AST | NodeRef, index: int | None = None) -> ast.AST:
        """Called when a symbol is assigned to."""

        raise NotImplementedError

    @abc.abstractmethod
    def define(self, name: str) -> None:
        """Called when a symbol is defined. (e.g., function names, class names, imports)"""

        raise NotImplementedError

    @abc.abstractmethod
    def define_nonlocal(self, node: ast.Global | ast.Nonlocal | OuterVar, root: str) -> None:
        """Called when a symbol is declared nonlocal or global."""

        raise NotImplementedError


class ScopeGlobal(ScopeBase):
    """Global scope."""

    def __init__(self, compiler: HyASTCompiler) -> None:
        super().__init__(compiler)

        self.defined: set[str] = set()
        #set: of all symbols created or assigned to in this scope

        self.nonlocal_vars: list[str] = []
        # list: of all `nonlocal`'s defined in this scope.
        # Explicitly not a `set` so that we maintain the order they were defined in

    def __exit__(self, *args: object) -> ta.Literal[False]:
        nonlocal_vars = self.nonlocal_vars
        self.nonlocal_vars = []
        if not self.defined.issuperset(nonlocal_vars):
            raise SyntaxError(f"no binding for nonlocal '{nonlocal_vars[0]}'")
        return super().__exit__(*args)

    @NodeRef.wrap
    def access(self, node: NodeRef, index: int | None = 0) -> ast.AST:
        return node.node

    @NodeRef.wrap
    def assign(self, node: NodeRef) -> ast.AST:
        self.define(node.name)
        return node.node

    def define(self, name: str) -> None:
        self.defined.add(name)

    def define_nonlocal(self, node: ast.Global | ast.Nonlocal | OuterVar, root: str) -> None:
        if root == 'nonlocal':
            self.nonlocal_vars.extend(node.names)
        else:
            self.defined.update(node.names)


class ScopeLet(ScopeBase):
    """
    Scope that supports let-binding by renaming bound symbols as they are accessed/assigned. Defined symbols are never
    renamed.
    """

    def __init__(self, compiler: HyASTCompiler) -> None:
        super().__init__(compiler)

        self.bindings: dict[str, str] = {}

    def _rename_if_bound(self, node: NodeRef) -> bool:
        if node.name in self.bindings:
            node.name = self.bindings[node.name]
            return True
        return False

    @NodeRef.wrap
    def access(self, node: NodeRef) -> ast.AST:
        self._rename_if_bound(node) or check.not_none(self.parent).access(node)
        return node.node

    @NodeRef.wrap
    def assign(self, node: NodeRef) -> ast.AST:
        self._rename_if_bound(node) or check.not_none(self.parent).assign(node)
        return node.node

    def define(self, name: str) -> None:
        self.bindings.pop(name, None)
        check.not_none(self.parent).define(name)

    def define_nonlocal(self, node: ast.Global | ast.Nonlocal | OuterVar, root: str) -> None:
        # remove nonlocal defs of any let scopes in this Python scope
        cur: ScopeBase | None = self
        while isinstance(cur, ScopeLet):
            for name in node.names:
                if root == 'nonlocal':
                    if name in cur.bindings and cur is not self:
                        node.names.remove(name)
                else:
                    cur.bindings[name] = name
            cur = cur.parent
        check.not_none(cur).define_nonlocal(node, root)

    def add(self, target: str | Object, new_name: str | None = None) -> str | Object:
        """Add a new let-binding target, mapped to a new, unique name."""

        if isinstance(target, (str, Symbol)):
            if '.' in target:
                raise ValueError('binding target may not contain a dot')
            name = mangle(target)
            if new_name is None:
                new_name = self.compiler.get_anon_var('let', name)
            self.bindings[name] = new_name
            if isinstance(target, Symbol):
                return Symbol(new_name).replace(target)
            return new_name
        if new_name is not None:
            raise ValueError('cannot specify name for compound targets')
        if isinstance(target, (List, Tuple)):
            return target.__class__(map(self.add, target)).replace(target)
        if (
            isinstance(target, Expression)
            and target
            and target[0] == Symbol('unpack-iterable')
        ):
            return Expression([target[0], *map(self.add, target[1:])]).replace(target)
        raise ValueError(f'invalid binding target: {type(target)}')


class ScopeFn(ScopeBase):
    """Scope that corresponds to Python's own function or class scopes."""

    def __init__(self, compiler: HyASTCompiler, args: ast.arguments | None = None, is_async: bool = False) -> None:
        super().__init__(compiler)

        self.defined: set[str] = set()
        # set: of all vars defined in this scope
        self.seen: list[NodeRef] = []
        # list: of all vars accessedto in this scope
        self.nonlocal_vars: dict[str, ast.Global | ast.Nonlocal | OuterVar] = {}
        # set: of all `nonlocal`'s defined in this scope
        self.is_fn = args is not None
        # bool: `True` if this scope is being used to track a python function `False` for classes
        self.is_async = is_async
        # bool: `True` if this scope is for an async function, which may need special handling during compilation
        self.has_yield = False
        # bool: `True` if this scope is tracking a function that has `yield` statements, as generator functions may need
        # special handling

        if args:
            for arg in itertools.chain(
                args.args, args.posonlyargs, args.kwonlyargs, [args.vararg, args.kwarg],
            ):
                if arg:
                    self.define(arg.arg)

    def __exit__(self, *args: object) -> ta.Literal[False]:
        self.defined.difference_update(self.nonlocal_vars.keys())
        for node in self.seen:
            if node.name not in self.defined:
                # pass unbound/nonlocal names up to parent scope
                check.not_none(self.parent).access(node)
        return super().__exit__(*args)

    @NodeRef.wrap
    def access(self, node: NodeRef) -> ast.AST:
        self.seen.append(node)
        return node.node

    @NodeRef.wrap
    def assign(self, node: NodeRef) -> ast.AST:
        self.access(node)
        self.define(node.name)
        return node.node

    def define(self, name: str) -> None:
        self.defined.add(name)

    def define_nonlocal(self, node: ast.Global | ast.Nonlocal | OuterVar, root: str) -> None:
        if root == 'nonlocal':
            self.nonlocal_vars.update({name: node for name in node.names})
        else:
            self.defined.update(node.names)

        for n in self.seen:
            if n.name in node.names:
                raise SyntaxError(f"name '{n.name}' is declared {root} after being used")
        if root == 'nonlocal':
            # toss all nonlocal names up to parent scope
            for i in range(len(node.names)):
                check.not_none(self.parent).access(node, i)


class ScopeGen(ScopeFn):
    """
    Scope that supports generator forms (`lfor`, `gfor`, ...). If this scope is contained within a function scope or the
    global scope, then any variable assignments are "leaked out" to the parent scope, mimicking Python's inline
    generator semantics.

    .. note::
       see :pep:`572#why-not-use-a-sublocal-scope-and-prevent-namespace-pollution` for more details on how and when
       variables are leaked into enclosing scopes.
    """

    def __init__(self, compiler: HyASTCompiler) -> None:
        super().__init__(compiler)

        self.iterators: set[str] = set()
        self.assignments: list[NodeRef] = []
        self.exposing_assignments = False

    def __enter__(self) -> ta.Self:
        super().__enter__()
        enclosing = nearest_python_scope(self.parent)
        if isinstance(enclosing, ScopeGlobal) or is_function_scope(enclosing):
            # only "leak out" assignments if we're contained in a function (or global) scope
            self.exposing_assignments = True
        return self

    def finalize(self) -> list[str]:
        """
        Access and return all the identifiers created and potentially leaked out by this generator. This should be
        called once and only once we've processed all of the iterators in this generators so as not to leak out any
        unwanted identifiers
        """

        res = set()
        for node in self.assignments:
            if node.name not in self.nonlocal_vars:
                check.not_none(self.parent).access(node)
                res.add(node.name)
        return sorted(res)

    @NodeRef.wrap
    def assign(self, node: NodeRef) -> ast.AST:
        self.access(node)
        if node.name not in self.defined:
            self.assignments.append(node)
        return node.node

    @NodeRef.wrap
    def access(self, node: NodeRef) -> ast.AST:
        if node.name not in self.iterators:
            self.seen.append(node)
        return node.node

    def iterator(self, target: ast.AST) -> None:
        """
        Declare an iteration variable name for this scope; as in Python, the iteration variable(s) cannot be reassigned.
        """

        self.iterators.update(
            name.id for name in ast.walk(target) if isinstance(name, ast.Name)
        )
        # remove potentially leakable identifiers that were actually iteration variables found in `target`
        self.assignments = [
            node for node in self.assignments if node.name not in self.iterators
        ]
        self.seen = [node for node in self.seen if node.name not in self.iterators]
