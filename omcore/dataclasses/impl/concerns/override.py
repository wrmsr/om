from ..generation.base import Generation
from ..generation.base import Generator
from ..generation.globals import NONE_GLOBAL
from ..generation.idents import SELF_IDENT
from ..generation.idents import VALUE_IDENT
from ..generation.ops import AddPropertyOp
from ..generation.ops import Op
from ..generation.ops import OpRef
from ..generation.ops import Ref
from ..generation.ops import add_ref
from ..generation.registry import register_generator_type
from ..generation.utils import SetattrSrcBuilder
from ..generation.values import SpecVal
from ..processing.base import ProcessingContext
from .fields import InstanceFields


##


@register_generator_type
class OverrideGenerator(Generator):
    cache_version = 1

    def generate(self, ctx: ProcessingContext) -> Generation | None:
        orm = {}
        ops: list[Op] = []

        ifs = ctx[InstanceFields]
        r_g = OpRef.numbered(len(ifs))
        for i, f in enumerate(ifs):
            if not (f.override or ctx.cs.override):
                continue
            r: OpRef = r_g('override.fields.{i}.annotation', i)
            orm[r] = SpecVal(('fields', ctx.cs.field_indexes_by_name[f.name], 'annotation'))
            op_refs: set[Ref] = {r}

            get_src = '\n'.join([
                f'def {f.name}({SELF_IDENT}) -> {r.ident()}:',
                f'    return {SELF_IDENT}.__dict__[{f.name!r}]',
            ])

            set_src: str | None = None
            if not ctx.cs.frozen:
                sab = SetattrSrcBuilder()
                set_src = '\n'.join([
                    f'def {f.name}({SELF_IDENT}, {VALUE_IDENT}) -> {add_ref(NONE_GLOBAL, op_refs).ident}:',
                    *[
                        f'    {l}'
                        for l in sab(
                            f.name,
                            VALUE_IDENT,
                            frozen=ctx.cs.frozen,
                            override=True,
                        )
                    ],
                ])
                op_refs.update(sab.refs)

            ops.append(AddPropertyOp(
                f.name,
                get_src=get_src,
                set_src=set_src,
                refs=frozenset(op_refs),
            ))

        return Generation(ops, bindings=orm) if ops else None
