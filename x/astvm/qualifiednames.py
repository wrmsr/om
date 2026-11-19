import ast


##


class QualifiedNames(ast.NodeVisitor):
    def __init__(self) -> None:
        super().__init__()
        self._prefix = ''

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        qualified = self._prefix + node.name
        setattr(node, '_astvm_qualname', qualified)
        for value in [*node.decorator_list, *node.bases, *(keyword.value for keyword in node.keywords)]:
            self.visit(value)

        previous = self._prefix
        self._prefix = qualified + '.'
        for statement in node.body:
            self.visit(statement)
        self._prefix = previous

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        qualified = self._prefix + node.name
        setattr(node, '_astvm_qualname', qualified)
        for value in node.decorator_list:
            self.visit(value)
        self._visit_arguments(node.args)
        if node.returns is not None:
            self.visit(node.returns)

        previous = self._prefix
        self._prefix = qualified + '.<locals>.'
        for statement in node.body:
            self.visit(statement)
        self._prefix = previous

    def visit_Lambda(self, node: ast.Lambda) -> None:
        qualified = self._prefix + '<lambda>'
        setattr(node, '_astvm_qualname', qualified)
        self._visit_arguments(node.args)

        previous = self._prefix
        self._prefix = qualified + '.<locals>.'
        self.visit(node.body)
        self._prefix = previous

    def _visit_arguments(self, args: ast.arguments) -> None:
        for value in [*args.defaults, *(default for default in args.kw_defaults if default is not None)]:
            self.visit(value)
        for arg in [*args.posonlyargs, *args.args, *args.kwonlyargs, args.vararg, args.kwarg]:
            if arg is not None and arg.annotation is not None:
                self.visit(arg.annotation)
