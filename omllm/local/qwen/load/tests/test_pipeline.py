"""
The loader pipeline's stages on their own: the plan (fusion, placement, precision) from names alone, the recipe's
contribution to the parameter cache's key, and the report of a load against a cold and a warm cache.
"""
import tempfile

import pytest

from ...core.params import mtp_param_names
from ...core.params import required_param_names
from ...ops.reference import NumpyOps
from ...tests.test_parity import synthetic_source
from ..pipeline import ParamLoader
from ..pipeline import open_param_cache
from ..plan import LayoutRules
from ..plan import plan_params
from ..policies import QWEN35_LAYOUT
from ..recipe import LoadRecipe


##


def _by_name(specs):
    return {s.name: s for s in specs}


def test_plan_fuses_places_and_widths():
    cfg, _, src = synthetic_source()
    names = required_param_names(cfg) + mtp_param_names()
    available = set(src.names())

    def int4(_):
        return 4

    specs = _by_name(plan_params(names, layout=QWEN35_LAYOUT, width=int4, available=available))

    # fused groups replace their parts; the a/b pair carries its int8 override
    assert specs['layers.0.mlp.gate_up_proj.weight'].parts == ('layers.0.mlp.gate_proj.weight', 'layers.0.mlp.up_proj.weight')  # noqa
    assert 'layers.0.mlp.gate_proj.weight' not in specs
    assert specs['layers.0.linear_attn.in_proj_qkvz.weight'].bits == 4
    assert specs['layers.0.linear_attn.in_proj_ab.weight'].bits == 8
    assert specs['layers.3.self_attn.qkv_proj.weight'].parts[2] == 'layers.3.self_attn.v_proj.weight'
    assert specs['mtp.layers.0.mlp.gate_up_proj.weight'].bits == 4  # the draft head's names fuse the same way

    # placement: norms and the DeltaNet scalars stay float32 and dense
    assert specs['layers.0.input_layernorm.weight'].keep_f32 and specs['layers.0.input_layernorm.weight'].bits is None
    assert specs['layers.0.linear_attn.A'].keep_f32
    assert specs['layers.0.mlp.down_proj.weight'].bits == 4 and not specs['layers.0.mlp.down_proj.weight'].keep_f32

    # a dense model: nothing has a width, fused or not
    dense = plan_params(names, layout=QWEN35_LAYOUT, width=lambda _: None, available=available)
    assert all(s.bits is None for s in dense)

    # a policy that splits a group across widths loads its parts on their own; a part that is never quantized stays
    # dense on its own even then
    def split(n):
        return 8 if n.endswith(('mlp.gate_proj.weight', 'in_proj_a.weight')) else 4

    s2 = _by_name(plan_params(names, layout=QWEN35_LAYOUT, width=split, available=available))
    assert 'layers.0.mlp.gate_up_proj.weight' not in s2
    assert s2['layers.0.mlp.gate_proj.weight'].bits == 8 and s2['layers.0.mlp.up_proj.weight'].bits == 4
    assert s2['layers.0.linear_attn.in_proj_a.weight'].bits is None

    # no layout rules: one spec per name, in order
    plain = plan_params(names, layout=LayoutRules(), width=int4, available=available)
    assert [s.name for s in plain] == names


def test_recipe_cache_variant():
    def int8_heads(name, cfg):
        return None

    assert LoadRecipe(quant='int4').cache_variant() == 's'
    assert LoadRecipe(quant='int4', policy='km').cache_variant() == 'km-s'
    assert LoadRecipe(quant='int8', search=False).cache_variant() == ''
    assert LoadRecipe(quant='int4', policy='km', search=False).cache_variant() == 'km'
    assert LoadRecipe(quant='int4', policy=int8_heads).cache_variant() == 'int8_heads-s'
    with pytest.raises(ValueError, match='quant must be one of'):
        LoadRecipe(quant='int3')


def test_load_report_cold_and_warm():
    cfg, _, src = synthetic_source()
    ops = NumpyOps('float32')
    recipe = LoadRecipe(quant='int8')

    with tempfile.TemporaryDirectory() as cache_dir:
        reports = []
        for _ in range(2):
            loader = ParamLoader(
                src,
                ops,
                recipe=recipe,
                layout=QWEN35_LAYOUT,
                dtype='f32',
                cache=open_param_cache(cache_dir, src, recipe),
            )
            specs = loader.plan(required_param_names(cfg), optional=('lm_head.weight',))
            specs += loader.plan(mtp_param_names())
            params = loader.materialize(specs)
            assert list(params) == [s.name for s in specs]
            reports.append(loader.report())

    cold, warm = reports
    assert cold.params == warm.params == len(specs)
    assert cold.cache_hits == 0 and cold.cache_misses == cold.params
    assert set(cold.acquired) == {'quantize', 'dense'}
    assert warm.acquired == {'cache': warm.params} and warm.cache_hits == warm.params and warm.cache_misses == 0
    assert cold.quantized == warm.quantized > 0  # held quantized either way: computed now, or from the cache
    assert cold.nbytes == warm.nbytes
    assert 'int8' in cold.summary() and '0 hit' in cold.summary()


def test_missing_tensors():
    cfg, _, src = synthetic_source()
    loader = ParamLoader(src, NumpyOps(), recipe=LoadRecipe(), layout=QWEN35_LAYOUT)
    with pytest.raises(KeyError):
        loader.plan(['layers.0.no_such.weight'])
