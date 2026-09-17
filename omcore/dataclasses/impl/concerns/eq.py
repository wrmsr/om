import dataclasses as dc

from ..generation.base import Generation
from ..generation.base import Generator
from ..generation.ops import AddMethodOp
from ..generation.registry import register_generator_type
from ..processing.base import ProcessingContext
from .fields import InstanceFields


##


@dc.dataclass(frozen=True)
class _EqCacheKey:
    has_own_eq: bool


@register_generator_type
class EqGenerator(Generator):
    cache_version = 2
    cache_schema = (_EqCacheKey,)

    def cache_key(self, ctx: ProcessingContext) -> _EqCacheKey:
        return _EqCacheKey(
            has_own_eq='__eq__' in ctx.cls.__dict__,
        )

    def generate(self, ctx: ProcessingContext) -> Generation | None:
        if not ctx.cs.eq or self.cache_key(ctx).has_own_eq:
            return None

        fields = tuple(f.name for f in ctx[InstanceFields] if f.compare)

        ret_lines: list[str]
        if fields:
            ret_lines = [
                f'    return (',
                *[
                    f'        self.{a} == other.{a}{" and" if i < len(fields) - 1 else ""}'
                    for i, a in enumerate(fields)
                ],
                f'    )',
            ]
        else:
            ret_lines = [
                f'    return True',
            ]

        return Generation([
            AddMethodOp(
                '__eq__',
                '\n'.join([
                    f'def __eq__(self, other):',
                    f'    if self is other:',
                    f'        return True',
                    f'    if self.__class__ is not other.__class__:',
                    f'        return NotImplemented',
                    *ret_lines,
                ]),
            ),
        ])
