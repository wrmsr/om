import typing as ta

from ..generation.base import Generation
from ..generation.base import Generator
from ..generation.ops import AddMethodOp
from ..generation.registry import register_generator_type
from ..generation.utils import build_attr_tuple_body_src_lines
from ..processing.base import ProcessingContext
from .fields import InstanceFields


##


ORDER_NAME_OP_PAIRS = [
    ('__lt__', '<'),
    ('__le__', '<='),
    ('__gt__', '>'),
    ('__ge__', '>='),
]


##


@register_generator_type
class OrderGenerator(Generator):
    cache_version = 1

    def cache_key(self, ctx: ProcessingContext) -> ta.Any:
        return tuple(name for name, _ in ORDER_NAME_OP_PAIRS if name in ctx.cls.__dict__)

    def generate(self, ctx: ProcessingContext) -> Generation | None:
        if not ctx.cs.order:
            return None

        for name in self.cache_key(ctx):
            raise TypeError(
                f'Cannot overwrite attribute {name} in class {ctx.cls.__name__}. '
                f'Consider using functools.total_ordering',
            )

        fields = tuple(f.name for f in ctx[InstanceFields] if f.compare)

        ops: list[AddMethodOp] = []

        for name, op in ORDER_NAME_OP_PAIRS:
            ret_lines: list[str] = []
            if fields:
                ret_lines.extend([
                    f'    return (',
                    *build_attr_tuple_body_src_lines(
                        'self',
                        *fields,
                        prefix='        ',
                    ),
                    f'    ) {op} (',
                    *build_attr_tuple_body_src_lines(
                        'other',
                        *fields,
                        prefix='        ',
                    ),
                    f'    )',
                ])
            else:
                ret_lines.append(
                    f'    return {"True" if "=" in op else "False"}',
                )

            ops.append(AddMethodOp(
                name,
                '\n'.join([
                    f'def {name}(self, other):',
                    f'    if other.__class__ is not self.__class__:',
                    f'        return NotImplemented',
                    *ret_lines,
                ]),
            ))

        return Generation(ops)
