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
from .results import asty


if ta.TYPE_CHECKING:
    from .compiler import HyASTCompiler


AstT = ta.TypeVar('AstT', bound=ast.AST)
ScopeT = ta.TypeVar('ScopeT', bound='ScopeBase')

type NonlocalDecl = ast.Global | ast.Nonlocal | OuterVar


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


##


class OuterVar(ast.stmt):
    """Custom AST node that can compile to either Nonlocal or Global."""

    def __init__(self, expr: Object | ast.AST, scope: ScopeBase, names: list[str]) -> None:
        super().__init__()

        self.__dict__.update(asty._get_pos(expr))

        self._scope = scope

        # As with `ast.Global` and `ast.Nonlocal`, scopes rename and remove these in place.
        self.names = names

    @property
    def scope(self) -> ScopeBase:
        return self._scope


class ResolveOuterVars(ast.NodeTransformer):
    """Find all OuterVar nodes and replace with Nonlocal or Global as necessary."""

    def visit_OuterVar(self, node: OuterVar) -> list[ast.stmt]:
        scope = node.scope
        defined: set[str] = set()
        undefined = list(node.names)  # Not a set, to keep the order.

        while undefined and scope.parent:
            scope = scope.parent

            has: ta.AbstractSet[str] = set()
            if isinstance(scope, ScopeFn):
                has = scope.defined

            elif isinstance(scope, ScopeLet):
                has = set(scope.bindings.keys())

            elif isinstance(scope, ScopeGlobal):
                if not all(name in scope.defined for name in undefined):
                    # Emit nonlocal, and let Python raise the error.
                    break

                res: list[ast.stmt] = []
                if undefined:
                    res.append(asty.Global(node, names=list(undefined)))
                if defined:
                    res.append(asty.Nonlocal(node, names=list(defined)))
                return res

            defined.update({name for name in undefined if name in has})
            undefined = [name for name in undefined if name not in has]

        return [asty.Nonlocal(node, names=node.names)] if node.names else []


class NodeRef:
    """
    Wrapper for AST nodes that have symbol names, so that we can rename them if necessary. Each `NodeRef` corresponds to
    one Python identifier. `ast` nodes that accept multiple identifier names (`global`, `nonlocal`, etc) have their
    specific identifier referenced by their `index` in the list of `names` provided by the `ast` node.
    """

    ACCESSOR: ta.ClassVar[ta.Mapping[type[ast.AST], str]] = {
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

        self._node = node
        self._index = index

        self._accessor = NodeRef.ACCESSOR[type(node)]

    def __repr__(self) -> str:
        return f'NodeRef(name={self.name}, node={type(self._node).__name__}, index={self._index})'

    @property
    def node(self) -> ast.AST:
        return self._node

    @property
    def index(self) -> int | None:
        return self._index

    @property
    def name(self) -> str:
        res = getattr(self._node, self._accessor)
        if self._index is not None:
            return res[self._index]
        return res

    def rename(self, new_name: str) -> None:
        """Rename the referenced identifier in the wrapped node, in place."""

        if self._index is not None:
            getattr(self._node, self._accessor)[self._index] = new_name
        else:
            setattr(self._node, self._accessor, new_name)

    @staticmethod
    def wrap(f: ta.Callable[[ta.Any, NodeRef], AstT]) -> ta.Callable[..., AstT]:
        """Decorator for scope methods converting an AST node parameter (and optional name index) to a NodeRef."""

        def _wrapper(self: ta.Any, node: ast.AST | NodeRef, index: int | None = None) -> AstT:
            if not isinstance(node, NodeRef):
                node = NodeRef(node, index)
            return f(self, node)

        return _wrapper


##


class ScopeBase(lang.Abstract):
    def __init__(self, compiler: HyASTCompiler) -> None:
        super().__init__()

        self._compiler = compiler

        self._parent: ScopeBase | None = None
        self._children: list[ScopeBase] = []

    @property
    def parent(self) -> ScopeBase | None:
        return self._parent

    @property
    def children(self) -> ta.Sequence[ScopeBase]:
        return self._children

    def create(self, scope_type: type[ScopeT], *args: ta.Any) -> ScopeT:
        """Create new scope from this one."""

        return scope_type(self._compiler, *args)

    def __enter__(self) -> ta.Self:
        if self._compiler.scope is not self:
            parent = self._compiler.scope
            self._parent = parent
            if self not in parent._children:
                parent._children.append(self)

        self._compiler.scope = self
        return self

    def __exit__(self, *args: object) -> ta.Literal[False]:
        if self._parent is not None:
            self._compiler.scope = self._parent
        return False

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
        """Called when a symbol is defined (e.g., function names, class names, imports)."""

        raise NotImplementedError

    @abc.abstractmethod
    def define_nonlocal(self, node: NonlocalDecl, root: str) -> None:
        """Called when a symbol is declared nonlocal or global."""

        raise NotImplementedError


class ScopeGlobal(ScopeBase):
    """Global scope."""

    def __init__(self, compiler: HyASTCompiler) -> None:
        super().__init__(compiler)

        # All symbols created or assigned to in this scope.
        self._defined: set[str] = set()

        # All `nonlocal`s declared in this scope - not a set, to keep the order they were declared in.
        self._nonlocal_vars: list[str] = []

    @property
    def defined(self) -> ta.AbstractSet[str]:
        return self._defined

    def __exit__(self, *args: object) -> ta.Literal[False]:
        nonlocal_vars = self._nonlocal_vars
        self._nonlocal_vars = []
        if not self._defined.issuperset(nonlocal_vars):
            raise SyntaxError(f"no binding for nonlocal '{nonlocal_vars[0]}'")

        return super().__exit__(*args)

    @NodeRef.wrap
    def access(self, node: NodeRef) -> ast.AST:
        return node.node

    @NodeRef.wrap
    def assign(self, node: NodeRef) -> ast.AST:
        self.define(node.name)
        return node.node

    def define(self, name: str) -> None:
        self._defined.add(name)

    def define_nonlocal(self, node: NonlocalDecl, root: str) -> None:
        if root == 'nonlocal':
            self._nonlocal_vars.extend(node.names)
        else:
            self._defined.update(node.names)


class ScopeLet(ScopeBase):
    """
    Scope that supports let-binding by renaming bound symbols as they are accessed/assigned. Defined symbols are never
    renamed.
    """

    def __init__(self, compiler: HyASTCompiler) -> None:
        super().__init__(compiler)

        self._bindings: dict[str, str] = {}

    @property
    def bindings(self) -> ta.Mapping[str, str]:
        return self._bindings

    def _rename_if_bound(self, node: NodeRef) -> bool:
        if node.name in self._bindings:
            node.rename(self._bindings[node.name])
            return True

        return False

    @NodeRef.wrap
    def access(self, node: NodeRef) -> ast.AST:
        if not self._rename_if_bound(node):
            check.not_none(self._parent).access(node)
        return node.node

    @NodeRef.wrap
    def assign(self, node: NodeRef) -> ast.AST:
        if not self._rename_if_bound(node):
            check.not_none(self._parent).assign(node)
        return node.node

    def define(self, name: str) -> None:
        self._bindings.pop(name, None)
        check.not_none(self._parent).define(name)

    def define_nonlocal(self, node: NonlocalDecl, root: str) -> None:
        # Remove nonlocal defs of any let scopes in this Python scope.
        cur: ScopeBase | None = self
        while isinstance(cur, ScopeLet):
            # Iterate over a copy, as names are removed as we go.
            for name in list(node.names):
                if root == 'nonlocal':
                    if name in cur._bindings and cur is not self:
                        node.names.remove(name)
                else:
                    cur._bindings[name] = name
            cur = cur.parent

        check.not_none(cur).define_nonlocal(node, root)

    def add(self, target: str | Object, new_name: str | None = None) -> str | Object:
        """Add a new let-binding target, mapped to a new, unique name."""

        if isinstance(target, (str, Symbol)):
            if '.' in target:
                raise ValueError('binding target may not contain a dot')

            name = mangle(target)
            if new_name is None:
                new_name = self._compiler.get_anon_var('let', name)
            self._bindings[name] = new_name

            if isinstance(target, Symbol):
                return Symbol(new_name).replace(target)
            return new_name

        if new_name is not None:
            raise ValueError('cannot specify name for compound targets')

        if isinstance(target, (List, Tuple)):
            return type(target)(map(self.add, target)).replace(target)

        if (
                isinstance(target, Expression) and
                target and
                target[0] == Symbol('unpack-iterable')
        ):
            return Expression([target[0], *map(self.add, target[1:])]).replace(target)

        raise ValueError(f'invalid binding target: {type(target)}')


class ScopeFn(ScopeBase):
    """Scope that corresponds to Python's own function or class scopes."""

    def __init__(self, compiler: HyASTCompiler, args: ast.arguments | None = None, is_async: bool = False) -> None:
        super().__init__(compiler)

        self._defined: set[str] = set()
        self._seen: list[NodeRef] = []
        self._nonlocal_vars: dict[str, NonlocalDecl] = {}

        # False for class scopes.
        self._is_fn = args is not None

        # Async functions may need special handling during compilation.
        self._is_async = is_async

        # Set by the compilation of `yield`, as generator functions may also need special handling.
        self.has_yield = False

        if args is not None:
            for arg in itertools.chain(args.args, args.posonlyargs, args.kwonlyargs, [args.vararg, args.kwarg]):
                if arg:
                    self.define(arg.arg)

    @property
    def defined(self) -> ta.AbstractSet[str]:
        return self._defined

    @property
    def nonlocal_vars(self) -> ta.Mapping[str, NonlocalDecl]:
        return self._nonlocal_vars

    @property
    def is_fn(self) -> bool:
        return self._is_fn

    @property
    def is_async(self) -> bool:
        return self._is_async

    def __exit__(self, *args: object) -> ta.Literal[False]:
        self._defined.difference_update(self._nonlocal_vars.keys())

        for node in self._seen:
            if node.name not in self._defined:
                # Pass unbound and nonlocal names up to the parent scope.
                check.not_none(self._parent).access(node)

        return super().__exit__(*args)

    @NodeRef.wrap
    def access(self, node: NodeRef) -> ast.AST:
        self._seen.append(node)
        return node.node

    @NodeRef.wrap
    def assign(self, node: NodeRef) -> ast.AST:
        self.access(node)
        self.define(node.name)
        return node.node

    def define(self, name: str) -> None:
        self._defined.add(name)

    def define_nonlocal(self, node: NonlocalDecl, root: str) -> None:
        if root == 'nonlocal':
            self._nonlocal_vars.update({name: node for name in node.names})
        else:
            self._defined.update(node.names)

        for n in self._seen:
            if n.name in node.names:
                raise SyntaxError(f"name '{n.name}' is declared {root} after being used")

        if root == 'nonlocal':
            # Pass all nonlocal names up to the parent scope.
            for i in range(len(node.names)):
                check.not_none(self._parent).access(node, i)


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

        self._iterators: set[str] = set()
        self._assignments: list[NodeRef] = []
        self._exposing_assignments = False

    @property
    def exposing_assignments(self) -> bool:
        return self._exposing_assignments

    def __enter__(self) -> ta.Self:
        super().__enter__()

        # Only "leak out" assignments if we're contained in a function (or global) scope.
        enclosing = nearest_python_scope(self._parent)
        if isinstance(enclosing, ScopeGlobal) or is_function_scope(enclosing):
            self._exposing_assignments = True

        return self

    def finalize(self) -> list[str]:
        """
        Access and return all the identifiers created and potentially leaked out by this generator. This should be
        called once and only once we've processed all of the iterators in this generators so as not to leak out any
        unwanted identifiers.
        """

        res: set[str] = set()
        for node in self._assignments:
            if node.name not in self._nonlocal_vars:
                check.not_none(self._parent).access(node)
                res.add(node.name)

        return sorted(res)

    @NodeRef.wrap
    def assign(self, node: NodeRef) -> ast.AST:
        self.access(node)
        if node.name not in self._defined:
            self._assignments.append(node)
        return node.node

    @NodeRef.wrap
    def access(self, node: NodeRef) -> ast.AST:
        if node.name not in self._iterators:
            self._seen.append(node)
        return node.node

    def iterator(self, target: ast.AST) -> None:
        """
        Declare an iteration variable name for this scope; as in Python, the iteration variable(s) cannot be reassigned.
        """

        self._iterators.update(name.id for name in ast.walk(target) if isinstance(name, ast.Name))

        # Remove potentially leakable identifiers that were actually iteration variables found in `target`.
        self._assignments = [node for node in self._assignments if node.name not in self._iterators]
        self._seen = [node for node in self._seen if node.name not in self._iterators]
