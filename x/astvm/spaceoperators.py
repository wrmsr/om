# mypy: disable-error-code=attr-defined

from .values import _ELLIPSIS
from .values import _NOT_IMPLEMENTED
from .values import _NUMBERS
from .values import _SCALARS
from .values import ObjectRef
from .values import Value


##


class SpaceOperators:
    def identity_number(self, value: Value) -> int:
        if type(value) is ObjectRef:
            self.runtime.read(value)
            return value.serial

        key = id(value)
        if key not in self._scalar_identities:
            self.budget.allocate(1, object_count=1)
            self._scalar_identities[key] = (value, -(len(self._scalar_identities) + 1))

        return self._scalar_identities[key][1]

    def identical(self, left: Value, right: Value) -> bool:
        if type(left) is ObjectRef or type(right) is ObjectRef:
            return type(left) is ObjectRef and type(right) is ObjectRef and left == right
        return left is right

    def equal(
            self,
            left: Value,
            right: Value,
            depth: int = 0,
    ) -> bool:
        self.budget.tick()

        if self.identical(left, right):
            return True

        if depth > self.budget.limits.conversion_depth:
            self.error('RecursionError', 'comparison nesting limit')

        if type(left) in _SCALARS and type(right) in _SCALARS:
            return left == right

        lk, rk = self.kind(left), self.kind(right)

        if lk == rk and lk in ('list', 'tuple'):
            a, b = self.data(left), self.data(right)
            return len(a) == len(b) and all(self.equal(x, y, depth + 1) for x, y in zip(a, b))

        if lk in ('dict', 'namespace') and rk in ('dict', 'namespace'):
            a, b = self.mapping_pairs(left), self.mapping_pairs(right)
            if len(a) != len(b):
                return False
            tokens = {self.key(k): v for k, v in b}
            return all(self.key(k) in tokens and self.equal(v, tokens[self.key(k)], depth + 1) for k, v in a)

        if lk in ('set', 'frozenset') and rk in ('set', 'frozenset'):
            return self.data(left).keys() == self.data(right).keys()

        if lk == rk == 'range':
            a, b = self.data(left), self.data(right)
            return range(a.start, a.stop, a.step) == range(b.start, b.stop, b.step)

        return False

    def compare(
            self,
            name: str,
            left: Value,
            right: Value,
            depth: int = 0,
    ) -> bool:
        self.budget.tick()
        if depth > self.budget.limits.conversion_depth:
            self.error('RecursionError', 'comparison nesting limit')

        if name in ('Is', 'IsNot'):
            result = self.identical(left, right)
            return result if name == 'Is' else not result

        if name in ('Eq', 'NotEq'):
            result = self.equal(left, right)
            return result if name == 'Eq' else not result

        if type(left) in _SCALARS and type(right) in _SCALARS:
            return self.native(self._ORDER[name], left, right)

        if self.kind(left) == self.kind(right) and self.kind(left) in ('list', 'tuple'):
            a, b = self.data(left), self.data(right)
            for x, y in zip(a, b):
                if not self.equal(x, y):
                    return self.compare(name, x, y, depth + 1)

            return self._ORDER[name](len(a), len(b))

        return self.error('TypeError', 'ordering is not supported between these values')

    def binary(
            self,
            name: str,
            left: Value,
            right: Value,
    ) -> Value:
        lk, rk = self.kind(left), self.kind(right)

        if (
                name == 'Add' and
                lk == rk and
                lk in ('list', 'tuple', 'str', 'bytes')
        ):
            self.budget.size(self.length(left) + self.length(right), string=lk in ('str', 'bytes'))
            if lk in ('list', 'tuple'):
                return self.new(lk, self.data(left) + self.data(right))
            self.budget.allocate(len(left) + len(right))
            return left + right

        if (
                name == 'Mult' and
                (
                        lk in ('list', 'tuple', 'str', 'bytes') or
                        rk in ('list', 'tuple', 'str', 'bytes')
                )
        ):
            seq, count = (left, right) if lk in ('list', 'tuple', 'str', 'bytes') else (right, left)
            count = max(0, self.index(count))
            kind = self.kind(seq)
            size = self.length(seq) * count
            self.budget.size(size, string=kind in ('str', 'bytes'))
            if kind in ('list', 'tuple'):
                return self.new(kind, self.data(seq) * count)
            self.budget.allocate(size)
            return seq * count

        if (
                lk in ('set', 'frozenset') and
                rk in ('set', 'frozenset') and
                name in ('BitOr', 'BitAnd', 'BitXor', 'Sub')
        ):
            a, b = self.data(left), self.data(right)
            keys = self._BINARY[name](a.keys(), b.keys())
            self.budget.size(len(keys))
            return self.new(lk, {k: a[k] if k in a else b[k] for k in keys})

        if (
                lk in ('dict', 'namespace') and
                rk in ('dict', 'namespace') and
                name == 'BitOr'
        ):
            return self.make_dict([*self.mapping_pairs(left), *self.mapping_pairs(right)])

        if (
                type(left) not in _NUMBERS or
                type(right) not in _NUMBERS
        ):
            self.error('TypeError', f'unsupported operands for {name}: {lk}, {rk}')

        if (
                name == 'Pow' and
                type(left) in (int, bool) and
                type(right) in (int, bool) and
                right >= 0
        ):
            estimate = max(1, abs(left).bit_length()) * right
            if abs(left) > 1 and estimate > self.budget.limits.integer_bits:
                self.budget.fail('power result size limit')

        if (
                name == 'LShift' and
                type(left) in (int, bool) and
                type(right) in (int, bool)
        ):
            if right >= 0 and left and left.bit_length() + right > self.budget.limits.integer_bits:
                self.budget.fail('shift result size limit')

        return self.native(self._BINARY[name], left, right)

    def mapping_pairs(self, value: Value) -> list[tuple[Value, Value]]:
        kind = self.kind(value)

        if kind == 'namespace':
            return list(self.data(value).items())

        if kind == 'dict':
            return list(self.data(value).values())

        return self.error('TypeError', 'expected an intrinsic mapping')

    def representation(
            self,
            value: Value,
            *,
            string: bool = False,
            seen: set[int] | None = None,
    ) -> str:
        self.budget.tick()

        if type(value) in _SCALARS:
            return self.native(str if string else repr, value)

        if value in (_ELLIPSIS, _NOT_IMPLEMENTED):
            return value.name

        kind = self.kind(value)

        if seen is None:
            seen = set()
        if len(seen) > self.budget.limits.conversion_depth:
            self.budget.fail('representation nesting limit')

        if value.serial in seen:
            return {
                'list': '[...]',
                'dict': '{...}',
                'namespace': '{...}',
                'tuple': '(...)',
            }.get(kind, '...')

        seen.add(value.serial)

        try:
            if kind in ('list', 'tuple', 'set', 'frozenset'):
                values = self.data(value)

                if kind in ('set', 'frozenset'):
                    values = values.values()

                parts = []
                size = 0
                for part in values:
                    text = self.representation(part, seen=seen)
                    size += len(text) + 2
                    self.budget.size(size, string=True)
                    parts.append(text)

                text = ', '.join(parts)

                if kind == 'list':
                    return '[' + text + ']'

                if kind == 'tuple':
                    return '(' + text + (',' if len(parts) == 1 else '') + ')'

                if kind == 'set':
                    return '{' + text + '}' if parts else 'set()'

                return 'frozenset({' + text + '})' if parts else 'frozenset()'

            if kind in ('dict', 'namespace'):
                parts = []
                size = 0
                for key, item in self.mapping_pairs(value):
                    text = self.representation(key, seen=seen) + ': ' + self.representation(item, seen=seen)
                    size += len(text) + 2
                    self.budget.size(size, string=True)
                    parts.append(text)

                return '{' + ', '.join(parts) + '}'

            if kind in ('class', 'type'):
                return "<class '" + self.data(value).name + "'>"

            if kind == 'exception':
                info = self.data(value)

                if string:
                    if not info.args:
                        return ''

                    if len(info.args) == 1:
                        return self.representation(
                            info.args[0],
                            string=self.exception_name(value) != 'KeyError',
                            seen=seen,
                        )

                    return self.representation(self.new('tuple', info.args), seen=seen)

                parts = ', '.join(self.representation(v, seen=seen) for v in info.args)
                return self.exception_name(value) + '(' + parts + ')'

            if kind == 'range':
                info = self.data(value)
                args = f'{info.start}, {info.stop}' + (f', {info.step}' if info.step != 1 else '')
                return 'range(' + args + ')'

            if kind == 'instance':
                return '<' + self.data(self.data(value).cls).name + ' object>'

            return '<guest ' + kind + '>'

        finally:
            seen.remove(value.serial)
