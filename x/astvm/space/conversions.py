# mypy: disable-error-code=attr-defined

from ..capabilities import HostObject
from ..values import _ELLIPSIS
from ..values import _MISSING
from ..values import _NOT_IMPLEMENTED
from ..values import _SCALARS
from ..values import BoundaryError
from ..values import Value


##


class SpaceConversions:
    def import_value(
            self,
            value: object,
            *,
            capabilities: bool = False,
            memo: dict[int, Value] | None = None,
            depth: int = 0,
    ) -> Value:
        self.budget.tick()
        if depth > self.budget.limits.conversion_depth:
            self.budget.fail('boundary nesting limit')

        if type(value) in _SCALARS:
            self.budget.scalar(value)
            self.budget.allocate(len(value) if type(value) in (str, bytes) else 1)
            return value

        if value is Ellipsis:
            return _ELLIPSIS

        if value is NotImplemented:
            return _NOT_IMPLEMENTED

        if memo is None:
            memo = {}
        if id(value) in memo:
            return memo[id(value)]

        if capabilities and type(value) is HostObject:
            # Keep guest identity in the rollbackable heap, not the external capability registry.
            result = self.data(self._host_objects).get(id(value))

            if result is None:
                result = self.new('host_object', self.capabilities.register_object(value))
                self.runtime.write(self._host_objects, id(value), result)

            memo[id(value)] = result
            return result

        if type(value) not in (list, tuple, dict, set, frozenset):
            raise BoundaryError('only exact data types may cross the boundary; use an explicit capability')

        self.budget.size(len(value))

        kind = type(value).__name__
        result = self.new(kind, [] if kind in ('list', 'tuple') else {})

        memo[id(value)] = result

        if kind in ('list', 'tuple'):
            for item in value:
                imported = self.import_value(
                    item,
                    capabilities=capabilities,
                    memo=memo,
                    depth=depth + 1,
                )
                self.runtime.append(result, imported)

            if kind == 'tuple':
                self.runtime.replace(result, tuple(self.data(result)))

        elif kind == 'dict':
            for key, item in value.items():
                imported_key = self.import_value(
                    key,
                    capabilities=capabilities,
                    memo=memo,
                    depth=depth + 1,
                )
                imported = self.import_value(
                    item,
                    capabilities=capabilities,
                    memo=memo,
                    depth=depth + 1,
                )
                self.set_item(result, imported_key, imported)

        else:
            for item in value:
                imported = self.import_value(
                    item,
                    capabilities=capabilities,
                    memo=memo,
                    depth=depth + 1,
                )
                self.runtime.write(result, self.key(imported), imported)

        return result

    def export_value(
            self,
            value: Value,
            *,
            memo: dict[int, object] | None = None,
            depth: int = 0,
    ) -> object:
        self.budget.tick()
        if depth > self.budget.limits.conversion_depth:
            self.budget.fail('boundary nesting limit')

        if type(value) in _SCALARS:
            return value

        if value is _ELLIPSIS:
            return Ellipsis

        if value is _NOT_IMPLEMENTED:
            return NotImplemented

        if memo is None:
            memo = {}
        if value.serial in memo:
            result = memo[value.serial]
            if result is _MISSING:
                raise BoundaryError('cyclic immutable export is not supported')
            return result

        kind = self.kind(value)

        if kind == 'list':
            result = []
            memo[value.serial] = result
            for item in self.data(value):
                result.append(self.export_value(item, memo=memo, depth=depth + 1))
            return result

        if kind in ('dict', 'namespace', 'mappingproxy'):
            result = {}
            memo[value.serial] = result
            for key, item in self.mapping_pairs(value):
                result[self.export_value(key, memo=memo, depth=depth + 1)] = self.export_value(
                    item, memo=memo, depth=depth + 1,
                )
            return result

        if kind in ('tuple', 'set', 'frozenset'):
            memo[value.serial] = _MISSING
            items = self.data(value)
            if kind != 'tuple':
                items = items.values()
            parts = [self.export_value(item, memo=memo, depth=depth + 1) for item in items]
            result = {'tuple': tuple, 'set': set, 'frozenset': frozenset}[kind](parts)
            memo[value.serial] = result
            return result

        if kind == 'range':
            info = self.data(value)
            return range(info.start, info.stop, info.step)

        raise BoundaryError(f'{kind} is not exportable data; use the guest-value host API explicitly')
