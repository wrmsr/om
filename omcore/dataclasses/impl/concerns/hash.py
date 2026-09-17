import dataclasses as dc
import typing as ta

from ..generation.base import Generation
from ..generation.base import Generator
from ..generation.ops import AddMethodOp
from ..generation.ops import SetAttrOp
from ..generation.registry import register_generator_type
from ..generation.utils import build_attr_tuple_body_src_lines
from ..processing.base import ProcessingContext
from .fields import InstanceFields


##


HashAction: ta.TypeAlias = ta.Literal['set_none', 'add', 'exception']


# See https://bugs.python.org/issue32929#msg312829 for an if-statement version of this table.
HASH_ACTIONS: ta.Mapping[tuple[bool, bool, bool, bool], HashAction | None] = {
    #
    # +-------------------------------------- unsafe_hash?
    # |      +------------------------------- eq?
    # |      |      +------------------------ frozen?
    # |      |      |      +----------------  has-explicit-hash?
    # v      v      v      v
    (False, False, False, False): None,
    (False, False, False, True): None,
    (False, False, True, False): None,
    (False, False, True, True): None,
    (False, True, False, False): 'set_none',
    (False, True, False, True): None,
    (False, True, True, False): 'add',
    (False, True, True, True): None,
    (True, False, False, False): 'add',
    (True, False, False, True): 'exception',
    (True, False, True, False): 'add',
    (True, False, True, True): 'exception',
    (True, True, False, False): 'add',
    (True, True, False, True): 'exception',
    (True, True, True, False): 'add',
    (True, True, True, True): 'exception',
}


def _raise_hash_action_exception(cls: type) -> ta.NoReturn:
    raise TypeError(f'Cannot overwrite attribute __hash__ in class {cls.__name__}')


CACHED_HASH_ATTR = '__dataclass_hash__'


#


@register_generator_type
class HashGenerator(Generator):
    cache_version = 1

    def cache_key(self, ctx: ProcessingContext) -> ta.Any:
        class_hash = ctx.cls.__dict__.get('__hash__', dc.MISSING)
        return not (class_hash is dc.MISSING or (class_hash is None and '__eq__' in ctx.cls.__dict__))

    def generate(self, ctx: ProcessingContext) -> Generation | None:
        action = HASH_ACTIONS[(
            bool(ctx.cs.unsafe_hash),
            bool(ctx.cs.eq),
            bool(ctx.cs.frozen),
            self.cache_key(ctx),
        )]

        if action == 'set_none':
            return Generation([SetAttrOp('__hash__', None, if_present='replace')])

        elif action == 'exception':
            _raise_hash_action_exception(ctx.cls)

        elif action is None:
            return None

        elif action != 'add':
            raise ValueError(action)

        fields = tuple(
            f.name
            for f in ctx[InstanceFields]
            if (f.compare if f.hash is None else f.hash)
        )

        lines = [
            'def __hash__(self):',
        ]

        hash_lines: list[str]
        if fields:
            hash_lines = [
                'hash((',
                *build_attr_tuple_body_src_lines(
                    'self',
                    *fields,
                    prefix='    ',
                ),
                '))',
            ]
        else:
            hash_lines = ['hash(())']

        if ctx.cs.cache_hash:
            lines.extend([
                f'    try:',
                f'        return self.{CACHED_HASH_ATTR}',
                f'    except AttributeError:',
                f'        pass',
                f'    object.__setattr__(',
                f'        self,',
                f'        {CACHED_HASH_ATTR!r},',
                f'        h := {hash_lines[0]}',
                *[
                    f'        {l}'
                    for l in hash_lines[1:]
                ],
                f'    )',
                f'    return h',
            ])
        else:
            lines.extend([
                f'    return {hash_lines[0]}',
                *[
                    f'    {l}'
                    for l in hash_lines[1:]
                ],
            ])

        return Generation([
            AddMethodOp(
                '__hash__',
                '\n'.join(lines),
                if_present='replace',
            ),
        ])
