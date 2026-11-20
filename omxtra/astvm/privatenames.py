import ast


##


class PrivateNames(ast.NodeTransformer):
    def __init__(self) -> None:
        super().__init__()
        self._class_name: str | None = None

    def _mangle(self, name: str) -> str:
        class_name = self._class_name
        if (
            class_name is None or not name.startswith('__') or name.endswith('__') or
            '.' in name or not class_name.strip('_')
        ):
            return name
        return '_' + class_name.lstrip('_') + name

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        setattr(node, '_astvm_binding_name', self._mangle(node.name))
        node.bases = [self.visit(base) for base in node.bases]
        node.decorator_list = [self.visit(decorator) for decorator in node.decorator_list]
        node.keywords = [self.visit(keyword) for keyword in node.keywords]

        previous = self._class_name
        self._class_name = node.name
        node.body = [self.visit(statement) for statement in node.body]
        self._class_name = previous
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        setattr(node, '_astvm_binding_name', self._mangle(node.name))
        self.generic_visit(node)
        return node

    def visit_Name(self, node: ast.Name) -> ast.Name:
        node.id = self._mangle(node.id)
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.Attribute:
        node.value = self.visit(node.value)
        node.attr = self._mangle(node.attr)
        return node

    def visit_arg(self, node: ast.arg) -> ast.arg:
        node.arg = self._mangle(node.arg)
        self.generic_visit(node)
        return node

    def visit_Global(self, node: ast.Global) -> ast.Global:
        node.names = [self._mangle(name) for name in node.names]
        return node

    def visit_Nonlocal(self, node: ast.Nonlocal) -> ast.Nonlocal:
        node.names = [self._mangle(name) for name in node.names]
        return node

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> ast.ExceptHandler:
        if node.name is not None:
            node.name = self._mangle(node.name)
        self.generic_visit(node)
        return node

    def visit_Import(self, node: ast.Import) -> ast.Import:
        for alias in node.names:
            binding = alias.asname or alias.name.split('.')[0]
            mangled = self._mangle(binding)
            if mangled != binding:
                alias.asname = mangled
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom:
        for alias in node.names:
            binding = alias.asname or alias.name
            mangled = self._mangle(binding)
            if mangled != binding:
                alias.asname = mangled
        return node
