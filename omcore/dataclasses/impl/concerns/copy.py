import typing as ta

from ...specs import FieldType
from ..generation.base import Generation
from ..generation.base import Generator
from ..generation.idents import CLS_IDENT
from ..generation.ops import AddMethodOp
from ..generation.registry import register_generator_type
from ..generation.utils import build_attr_kwargs_body_src_lines
from ..processing.base import ProcessingContext


##


@register_generator_type
class CopyGenerator(Generator):
    cache_version = 1

    def cache_key(self, ctx: ProcessingContext) -> ta.Any:
        return '__copy__' in ctx.cls.__dict__

    def generate(self, ctx: ProcessingContext) -> Generation | None:
        if self.cache_key(ctx):
            return None

        fields = tuple(f.name for f in ctx.cs.fields if f.field_type is not FieldType.CLASS_VAR)

        return_lines: list[str]
        if fields:
            return_lines = [
                f'    return {CLS_IDENT}(  # noqa',
                *build_attr_kwargs_body_src_lines(
                    'self',
                    *fields,
                    prefix='        ',
                ),
                f'    )',
            ]
        else:
            return_lines = [
                f'    return {CLS_IDENT}()  # noqa',
            ]

        lines = [
            f'def __copy__(self):',
            f'    if self.__class__ is not {CLS_IDENT}:',
            f'        raise TypeError(self)',
            *return_lines,
        ]

        return Generation([
            AddMethodOp(
                '__copy__',
                '\n'.join(lines),
            ),
        ])
