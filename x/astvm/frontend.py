import ast
import dataclasses as dc
import symtable
import typing as ta

from .budget import Budget
from .values import _SCALARS
from .values import UnsupportedSyntaxError


##


@dc.dataclass(frozen=True, slots=True)
class Scope:
    kind: str
    local_names: frozenset[str]
    global_names: frozenset[str]
    nonlocal_names: frozenset[str]
    generator: bool = False


@dc.dataclass(frozen=True)
class Program:
    tree: ast.Module | ast.Expression
    scopes: ta.Mapping[ast.AST, Scope]
    filename: str

    def __deepcopy__(self, memo: dict[int, object]) -> Program:
        return self


class _Bindings(ast.NodeVisitor):
    def __init__(self) -> None:
        super().__init__()

        self.names: set[str] = set()
        self.globals: set[str] = set()
        self.nonlocals: set[str] = set()
        self.generator = False

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.names.add(node.id)

    def visit_Global(self, node: ast.Global) -> None:
        self.globals.update(node.names)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self.nonlocals.update(node.names)

    def visit_Yield(self, node: ast.Yield) -> None:
        self.generator = True
        self.generic_visit(node)

    def visit_YieldFrom(self, node: ast.YieldFrom) -> None:
        self.generator = True
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name is not None:
            self.names.add(node.name)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.names.add(alias.asname or alias.name.split('.')[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            self.names.add(alias.asname or alias.name)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.names.add(node.name)
        for item in [*node.decorator_list, *node.args.defaults, *node.args.kw_defaults]:
            if item is not None:
                self.visit(item)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        for item in [*node.args.defaults, *node.args.kw_defaults]:
            if item is not None:
                self.visit(item)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.names.add(node.name)
        for item in [*node.decorator_list, *node.bases, *(k.value for k in node.keywords)]:
            self.visit(item)

    def _comprehension(self, node: ast.AST) -> None:
        # Assignment expressions bind outside comprehensions, but not across nested lambdas.
        if isinstance(node, ast.DictComp):
            self.visit(node.key)
            self.visit(node.value)
        else:
            self.visit(node.elt)

        for gen in node.generators:
            self.visit(gen.iter)
            for condition in gen.ifs:
                self.visit(condition)

    visit_ListComp = _comprehension  # noqa: N815
    visit_SetComp = _comprehension  # noqa: N815
    visit_DictComp = _comprehension  # noqa: N815
    visit_GeneratorExp = _comprehension  # noqa: N815


class Frontend:
    _SUPPORTED = frozenset({
        'Module',
        'Expression',
        'Expr',
        'Constant',
        'Name',
        'Load',
        'Store',
        'Del',
        'List',
        'Tuple',
        'Set',
        'Dict',
        'Starred',
        'Slice',
        'Subscript',
        'Attribute',
        'BinOp',
        'UnaryOp',
        'BoolOp',
        'Compare',
        'IfExp',
        'NamedExpr',
        'Call',
        'keyword',
        'JoinedStr',
        'FormattedValue',
        'ListComp',
        'SetComp',
        'DictComp',
        'GeneratorExp',
        'comprehension',
        'Add',
        'Sub',
        'Mult',
        'Div',
        'FloorDiv',
        'Mod',
        'Pow',
        'LShift',
        'RShift',
        'BitOr',
        'BitXor',
        'BitAnd',
        'Invert',
        'Not',
        'UAdd',
        'USub',
        'And',
        'Or',
        'Eq',
        'NotEq',
        'Lt',
        'LtE',
        'Gt',
        'GtE',
        'Is',
        'IsNot',
        'In',
        'NotIn',
        'Assign',
        'AnnAssign',
        'AugAssign',
        'Delete',
        'Pass',
        'If',
        'For',
        'While',
        'Break',
        'Continue',
        'FunctionDef',
        'Lambda',
        'arguments',
        'arg',
        'Return',
        'Yield',
        'YieldFrom',
        'Global',
        'Nonlocal',
        'Raise',
        'Assert',
        'Try',
        'ExceptHandler',
        'With',
        'withitem',
        'ClassDef',
        'Import',
        'ImportFrom',
        'alias',
    })

    def __init__(self, budget: Budget) -> None:
        super().__init__()

        self._budget = budget

    def _scope(self, node: ast.AST, kind: str) -> Scope:
        scan = _Bindings()

        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            for gen in node.generators:
                scan.visit(gen.target)

        elif isinstance(node, ast.Lambda):
            scan.visit(node.body)

        else:
            for child in node.body:
                scan.visit(child)

        if isinstance(node, (ast.FunctionDef, ast.Lambda)):
            args = node.args
            scan.names.update(a.arg for a in [*args.posonlyargs, *args.args, *args.kwonlyargs])
            if args.vararg is not None:
                scan.names.add(args.vararg.arg)
            if args.kwarg is not None:
                scan.names.add(args.kwarg.arg)

        return Scope(
            kind,
            frozenset(scan.names - scan.globals - scan.nonlocals),
            frozenset(scan.globals),
            frozenset(scan.nonlocals),
            scan.generator or isinstance(node, ast.GeneratorExp),
        )

    def _validate_context(self, tree: ast.AST) -> None:
        todo = [(tree, 'module', 0)]

        while todo:
            node, scope, loops = todo.pop()

            if isinstance(node, (ast.Return, ast.Yield, ast.YieldFrom)) and scope != 'function':
                raise SyntaxError(f'{type(node).__name__} outside function')

            if isinstance(node, (ast.Break, ast.Continue)) and not loops:
                raise SyntaxError(f'{type(node).__name__} outside loop')

            if isinstance(node, (ast.FunctionDef, ast.Lambda)):
                body = node.body if isinstance(node.body, list) else [node.body]
                todo.extend((n, 'function', 0) for n in body)
                for expr in [*node.args.defaults, *node.args.kw_defaults]:
                    if expr is not None:
                        todo.append((expr, scope, loops))
                if isinstance(node, ast.FunctionDef):
                    todo.extend((n, scope, loops) for n in node.decorator_list)
                continue

            if isinstance(node, ast.ClassDef):
                todo.extend((n, 'class', 0) for n in node.body)
                todo.extend((n, scope, loops) for n in [*node.bases, *node.decorator_list])
                continue

            if isinstance(node, (ast.While, ast.For)):
                todo.extend((n, scope, loops + 1) for n in node.body)
                todo.extend((n, scope, loops) for n in node.orelse)
                if isinstance(node, ast.While):
                    todo.append((node.test, scope, loops))
                else:
                    todo.append((node.iter, scope, loops))
                continue

            todo.extend((n, scope, loops) for n in ast.iter_child_nodes(node))

    def prepare(
            self,
            source: str,
            *,
            filename: str = '<guest>',
            expression: bool = False,
    ) -> Program:
        if type(source) is not str:
            raise TypeError('source must be an exact str')
        if len(source) > self._budget.limits.source_chars:
            self._budget.fail('source size limit')

        mode = 'eval' if expression else 'exec'
        tree = ast.parse(source, filename, mode)
        nodes: list[ast.AST] = []
        todo = [(tree, 0)]

        while todo:
            node, depth = todo.pop()
            nodes.append(node)

            if len(nodes) > self._budget.limits.ast_nodes or depth > self._budget.limits.ast_depth:
                self._budget.fail('AST size/depth limit')

            if type(node).__name__ not in self._SUPPORTED:
                raise UnsupportedSyntaxError(f'{type(node).__name__} at line {getattr(node, "lineno", 0)}')

            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.type_params:
                raise UnsupportedSyntaxError('type parameters')

            if isinstance(node, ast.ClassDef):
                if len(node.bases) > 1 or node.keywords:
                    raise UnsupportedSyntaxError('multiple inheritance and class keywords')

            if isinstance(node, ast.comprehension) and node.is_async:
                raise UnsupportedSyntaxError('asynchronous comprehension')

            if isinstance(node, ast.Import) and any('.' in a.name for a in node.names):
                raise UnsupportedSyntaxError('package imports')

            if isinstance(node, ast.ImportFrom) and (node.level or any(a.name == '*' for a in node.names)):
                raise UnsupportedSyntaxError('relative and star imports')

            if isinstance(node, ast.Constant):
                if node.value is not Ellipsis and type(node.value) not in _SCALARS:
                    raise UnsupportedSyntaxError('non-data constant')

                if node.value is not Ellipsis:
                    self._budget.scalar(node.value)

            todo.extend((n, depth + 1) for n in ast.iter_child_nodes(node))

        # The symbol-table frontend validates global/nonlocal declarations and comprehension restrictions. It does not
        # create executable code objects. Context checks above are still necessary.
        symtable.symtable(source, filename, mode)

        self._validate_context(tree)
        self._budget.allocate(len(nodes))

        scopes: dict[ast.AST, Scope] = {}

        if isinstance(tree, ast.Module):
            scopes[tree] = self._scope(tree, 'module')

        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.Lambda)):
                scopes[node] = self._scope(node, 'function')

            elif isinstance(node, ast.ClassDef):
                scopes[node] = self._scope(node, 'class')

            elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                scopes[node] = self._scope(node, 'comprehension')

        return Program(tree, scopes, filename)
