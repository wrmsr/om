"""
The first stage of the loader pipeline: from canonical parameter names to the parameters the model will hold.

A `ParamSpec` is one parameter as the model holds it -- a single source tensor, or several stacked along the output dim
(a fused projection) -- with its placement decided: the width it is held at (None: dense in the compute dtype) and
whether it stays float32 whatever the compute dtype. `plan_params` derives the specs from the names, the architecture's
`LayoutRules` and a per-name width (the precision policy's decision). It reads no tensor data; the materializer does
that, stage two.
"""
import typing as ta

from omcore import dataclasses as dc


Fusion: ta.TypeAlias = tuple[str, tuple[str, ...], int | None]  # (fused suffix, part suffixes, bits override)


##


@dc.dataclass(frozen=True)
class LayoutRules:
    """
    What an architecture tells the loader about its parameters beyond their names: which projections sharing an input
    are loaded fused (one weight stacked along the output dim, with an optional bits override for the group), which
    tensors stay float32 whatever the compute dtype, and which 2-D weights are never quantized. Patterns are name
    substrings (keep_f32, no_quant) and name suffixes (fusions).
    """

    fusions: tuple[Fusion, ...] = ()
    keep_f32: tuple[str, ...] = ()
    no_quant: tuple[str, ...] = ()


@dc.dataclass(frozen=True)
class ParamSpec:
    name: str  # the canonical name the model holds it under (the fused name for a fused projection)
    parts: tuple[str, ...]  # its source tensors, stacked along the output dim in this order
    bits: int | None = None  # held quantized at this width when its shape allows; None: dense
    keep_f32: bool = False  # dense float32 whatever the compute dtype


def find_fusion(name: str, fusions: ta.Sequence[Fusion]) -> tuple[str, list[str], int | None] | None:
    """For a canonical part name, the (fused name, all part names, bits override) it belongs to."""

    for fused, parts, fbits in fusions:
        for part in parts:
            if name.endswith(part):
                prefix = name[: -len(part)]
                return prefix + fused, [prefix + p for p in parts], fbits
    return None


def plan_params(
        names: ta.Sequence[str],
        *,
        layout: LayoutRules,
        width: ta.Callable[[str], int | None],
        available: ta.AbstractSet[str],
) -> list[ParamSpec]:
    """
    The specs for `names`, in order (a fused spec takes the place of its first part). `width(name)` is the precision
    policy's width for a source tensor, None throughout for a dense model. A fusion group is loaded fused when all its
    parts are available and the policy gives them one width, at the group's override if it has one; otherwise its parts
    are loaded on their own. A tensor matching `keep_f32` or `no_quant` is never quantized on its own.
    """

    specs: list[ParamSpec] = []
    fused_done: set[str] = set()

    for name in names:
        fusion = find_fusion(name, layout.fusions)

        if fusion is not None:
            fused, parts, fbits = fusion
            if fused in fused_done:
                continue

            if all(p in available for p in parts) and len({width(p) for p in parts}) == 1:
                w = width(name)
                specs.append(ParamSpec(
                    fused,
                    tuple(parts),
                    bits=None if w is None else (fbits or w),
                ))
                fused_done.add(fused)
                continue

        # a tensor of its own: a part without its siblings, or of a group the policy splits across widths
        keep_f32 = any(s in name for s in layout.keep_f32)
        quantizable = not keep_f32 and not any(s in name for s in layout.no_quant)
        specs.append(ParamSpec(
            name,
            (name,),
            bits=width(name) if quantizable else None,
            keep_f32=keep_f32,
        ))

    return specs
