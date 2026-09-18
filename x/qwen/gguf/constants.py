# ruff: noqa: N801 N806 N812 S105
# MIT License
#
# Copyright (c) 2023 Georgi Gerganov
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import enum
import typing as ta


##
# constants


GGUF_MAGIC             = 0x46554747  # "GGUF"
GGUF_VERSION           = 3
GGUF_DEFAULT_ALIGNMENT = 32
GGML_QUANT_VERSION     = 2  # GGML_QNT_VERSION from ggml.h


##
# metadata keys


class Keys:
    class General:
        TYPE                       = 'general.type'
        ARCHITECTURE               = 'general.architecture'
        QUANTIZATION_VERSION       = 'general.quantization_version'
        ALIGNMENT                  = 'general.alignment'
        FILE_TYPE                  = 'general.file_type'

        # Recommended Sampler Parameters
        SAMPLING_SEQUENCE           = 'general.sampling.sequence'
        SAMPLING_TOP_K              = 'general.sampling.top_k'
        SAMPLING_TOP_P              = 'general.sampling.top_p'
        SAMPLING_MIN_P              = 'general.sampling.min_p'
        SAMPLING_XTC_PROBABILITY    = 'general.sampling.xtc_probability'
        SAMPLING_XTC_THRESHOLD      = 'general.sampling.xtc_threshold'
        SAMPLING_TEMP               = 'general.sampling.temp'
        SAMPLING_PENALTY_LAST_N     = 'general.sampling.penalty_last_n'
        SAMPLING_PENALTY_REPEAT     = 'general.sampling.penalty_repeat'
        SAMPLING_MIROSTAT           = 'general.sampling.mirostat'
        SAMPLING_MIROSTAT_TAU       = 'general.sampling.mirostat_tau'
        SAMPLING_MIROSTAT_ETA       = 'general.sampling.mirostat_eta'

        # Authorship Metadata
        NAME                       = 'general.name'
        AUTHOR                     = 'general.author'
        VERSION                    = 'general.version'
        ORGANIZATION               = 'general.organization'

        FINETUNE                   = 'general.finetune'
        BASENAME                   = 'general.basename'

        DESCRIPTION                = 'general.description'
        QUANTIZED_BY               = 'general.quantized_by'

        SIZE_LABEL                 = 'general.size_label'

        # Licensing details
        LICENSE                    = 'general.license'
        LICENSE_NAME               = 'general.license.name'
        LICENSE_LINK               = 'general.license.link'

        # Typically represents the converted GGUF repo (Unless native)
        URL                        = 'general.url'  # Model Website/Paper
        DOI                        = 'general.doi'
        UUID                       = 'general.uuid'
        REPO_URL                   = 'general.repo_url'  # Model Source Repository (git/svn/etc...)

        # Model Source during conversion
        SOURCE_URL                 = 'general.source.url'  # Model Website/Paper
        SOURCE_DOI                 = 'general.source.doi'
        SOURCE_UUID                = 'general.source.uuid'
        SOURCE_REPO_URL            = 'general.source.repo_url'  # Model Source Repository (git/svn/etc...)

        # Base Model Source. There can be more than one source if it's a merged
        # model like with 'Mistral-7B-Merge-14-v0.1'. This will assist in
        # tracing linage of models as it is finetuned or merged over time.
        BASE_MODEL_COUNT           = 'general.base_model.count'
        BASE_MODEL_NAME            = 'general.base_model.{id}.name'
        BASE_MODEL_AUTHOR          = 'general.base_model.{id}.author'
        BASE_MODEL_VERSION         = 'general.base_model.{id}.version'
        BASE_MODEL_ORGANIZATION    = 'general.base_model.{id}.organization'
        BASE_MODEL_DESCRIPTION     = 'general.base_model.{id}.description'
        BASE_MODEL_URL             = 'general.base_model.{id}.url'  # Model Website/Paper
        BASE_MODEL_DOI             = 'general.base_model.{id}.doi'
        BASE_MODEL_UUID            = 'general.base_model.{id}.uuid'
        BASE_MODEL_REPO_URL        = 'general.base_model.{id}.repo_url'  # Model Source Repository (git/svn/etc...)

        # Dataset Source
        DATASET_COUNT           = 'general.dataset.count'
        DATASET_NAME            = 'general.dataset.{id}.name'
        DATASET_AUTHOR          = 'general.dataset.{id}.author'
        DATASET_VERSION         = 'general.dataset.{id}.version'
        DATASET_ORGANIZATION    = 'general.dataset.{id}.organization'
        DATASET_DESCRIPTION     = 'general.dataset.{id}.description'
        DATASET_URL             = 'general.dataset.{id}.url'  # Model Website/Paper
        DATASET_DOI             = 'general.dataset.{id}.doi'
        DATASET_UUID            = 'general.dataset.{id}.uuid'
        DATASET_REPO_URL        = 'general.dataset.{id}.repo_url'  # Model Source Repository (git/svn/etc...)

        # Array based KV stores
        TAGS                       = 'general.tags'
        LANGUAGES                  = 'general.languages'

    class LLM:
        VOCAB_SIZE                        = '{arch}.vocab_size'
        CONTEXT_LENGTH                    = '{arch}.context_length'
        EMBEDDING_LENGTH                  = '{arch}.embedding_length'
        EMBEDDING_LENGTH_OUT              = '{arch}.embedding_length_out'
        FEATURES_LENGTH                   = '{arch}.features_length'
        BLOCK_COUNT                       = '{arch}.block_count'
        LEADING_DENSE_BLOCK_COUNT         = '{arch}.leading_dense_block_count'
        FEED_FORWARD_LENGTH               = '{arch}.feed_forward_length'
        EXPERT_FEED_FORWARD_LENGTH        = '{arch}.expert_feed_forward_length'
        EXPERT_SHARED_FEED_FORWARD_LENGTH = '{arch}.expert_shared_feed_forward_length'
        EXPERT_CHUNK_FEED_FORWARD_LENGTH  = '{arch}.expert_chunk_feed_forward_length'
        USE_PARALLEL_RESIDUAL             = '{arch}.use_parallel_residual'
        TENSOR_DATA_LAYOUT                = '{arch}.tensor_data_layout'
        EXPERT_COUNT                      = '{arch}.expert_count'
        EXPERT_USED_COUNT                 = '{arch}.expert_used_count'
        EXPERT_SHARED_COUNT               = '{arch}.expert_shared_count'
        EXPERT_GROUP_COUNT                = '{arch}.expert_group_count'
        EXPERT_GROUP_USED_COUNT           = '{arch}.expert_group_used_count'
        EXPERT_WEIGHTS_SCALE              = '{arch}.expert_weights_scale'
        EXPERT_WEIGHTS_NORM               = '{arch}.expert_weights_norm'
        EXPERT_GATING_FUNC                = '{arch}.expert_gating_func'
        EXPERT_GROUP_SCALE                = '{arch}.expert_group_scale'
        EXPERTS_PER_GROUP                 = '{arch}.experts_per_group'
        MOE_EVERY_N_LAYERS                = '{arch}.moe_every_n_layers'
        MOE_LATENT_SIZE                   = '{arch}.moe_latent_size'
        NEXTN_PREDICT_LAYERS              = '{arch}.nextn_predict_layers'
        NUM_DEEPSTACK_LAYERS              = '{arch}.n_deepstack_layers'
        POOLING_TYPE                      = '{arch}.pooling_type'
        LOGIT_SCALE                       = '{arch}.logit_scale'
        DECODER_START_TOKEN_ID            = '{arch}.decoder_start_token_id'
        DECODER_BLOCK_COUNT               = '{arch}.decoder_block_count'
        ATTN_LOGIT_SOFTCAPPING            = '{arch}.attn_logit_softcapping'
        ROUTER_LOGIT_SOFTCAPPING          = '{arch}.router_logit_softcapping'
        FINAL_LOGIT_SOFTCAPPING           = '{arch}.final_logit_softcapping'
        SWIN_NORM                         = '{arch}.swin_norm'
        RESCALE_EVERY_N_LAYERS            = '{arch}.rescale_every_n_layers'
        TIME_MIX_EXTRA_DIM                = '{arch}.time_mix_extra_dim'
        TIME_DECAY_EXTRA_DIM              = '{arch}.time_decay_extra_dim'
        RESIDUAL_SCALE                    = '{arch}.residual_scale'
        EMBEDDING_SCALE                   = '{arch}.embedding_scale'
        TOKEN_SHIFT_COUNT                 = '{arch}.token_shift_count'
        INTERLEAVE_MOE_LAYER_STEP         = '{arch}.interleave_moe_layer_step'
        FULL_ATTENTION_INTERVAL           = '{arch}.full_attention_interval'
        ACTIVATION_SPARSITY_SCALE         = '{arch}.activation_sparsity_scale'
        ALTUP_ACTIVE_IDX                  = '{arch}.altup.active_idx'
        ALTUP_NUM_INPUTS                  = '{arch}.altup.num_inputs'
        EMBD_LENGTH_PER_LAYER_INP         = '{arch}.embedding_length_per_layer_input'
        SWIGLU_CLAMP_EXP                  = '{arch}.swiglu_clamp_exp'
        SWIGLU_CLAMP_SHEXP                = '{arch}.swiglu_clamp_shexp'
        DENSE_FEAT_IN_SIZE                = '{arch}.{dense}_feat_in'
        DENSE_FEAT_OUT_SIZE               = '{arch}.{dense}_feat_out'

    class Attention:
        HEAD_COUNT                   = '{arch}.attention.head_count'
        HEAD_COUNT_KV                = '{arch}.attention.head_count_kv'
        MAX_ALIBI_BIAS               = '{arch}.attention.max_alibi_bias'
        CLAMP_KQV                    = '{arch}.attention.clamp_kqv'
        KEY_LENGTH                   = '{arch}.attention.key_length'
        VALUE_LENGTH                 = '{arch}.attention.value_length'
        LAYERNORM_EPS                = '{arch}.attention.layer_norm_epsilon'
        LAYERNORM_RMS_EPS            = '{arch}.attention.layer_norm_rms_epsilon'
        GROUPNORM_EPS                = '{arch}.attention.group_norm_epsilon'
        GROUPNORM_GROUPS             = '{arch}.attention.group_norm_groups'
        CAUSAL                       = '{arch}.attention.causal'
        Q_LORA_RANK                  = '{arch}.attention.q_lora_rank'
        KV_LORA_RANK                 = '{arch}.attention.kv_lora_rank'
        DECAY_LORA_RANK              = '{arch}.attention.decay_lora_rank'
        ICLR_LORA_RANK               = '{arch}.attention.iclr_lora_rank'
        VALUE_RESIDUAL_MIX_LORA_RANK = '{arch}.attention.value_residual_mix_lora_rank'
        GATE_LORA_RANK               = '{arch}.attention.gate_lora_rank'
        REL_BUCKETS_COUNT            = '{arch}.attention.relative_buckets_count'
        SLIDING_WINDOW               = '{arch}.attention.sliding_window'
        SCALE                        = '{arch}.attention.scale'
        OUTPUT_SCALE                 = '{arch}.attention.output_scale'
        TEMPERATURE_LENGTH           = '{arch}.attention.temperature_length'
        KEY_LENGTH_MLA               = '{arch}.attention.key_length_mla'
        VALUE_LENGTH_MLA             = '{arch}.attention.value_length_mla'
        KEY_LENGTH_SWA               = '{arch}.attention.key_length_swa'
        VALUE_LENGTH_SWA             = '{arch}.attention.value_length_swa'
        SHARED_KV_LAYERS             = '{arch}.attention.shared_kv_layers'
        SLIDING_WINDOW_PATTERN       = '{arch}.attention.sliding_window_pattern'
        TEMPERATURE_SCALE            = '{arch}.attention.temperature_scale'

        class Indexer:
            HEAD_COUNT = '{arch}.attention.indexer.head_count'
            KEY_LENGTH = '{arch}.attention.indexer.key_length'
            TOP_K      = '{arch}.attention.indexer.top_k'

    class Rope:
        DIMENSION_COUNT           = '{arch}.rope.dimension_count'
        DIMENSION_COUNT_SWA       = '{arch}.rope.dimension_count_swa'
        DIMENSION_SECTIONS        = '{arch}.rope.dimension_sections'
        FREQ_BASE                 = '{arch}.rope.freq_base'
        FREQ_BASE_SWA             = '{arch}.rope.freq_base_swa'
        SCALING_TYPE              = '{arch}.rope.scaling.type'
        SCALING_FACTOR            = '{arch}.rope.scaling.factor'
        SCALING_ALPHA             = '{arch}.rope.scaling.alpha'
        SCALING_ATTN_FACTOR       = '{arch}.rope.scaling.attn_factor'
        SCALING_ORIG_CTX_LEN      = '{arch}.rope.scaling.original_context_length'
        SCALING_FINETUNED         = '{arch}.rope.scaling.finetuned'
        SCALING_YARN_LOG_MUL      = '{arch}.rope.scaling.yarn_log_multiplier'
        SCALING_YARN_EXT_FACTOR   = '{arch}.rope.scaling.yarn_ext_factor'
        SCALING_YARN_ATTN_FACTOR  = '{arch}.rope.scaling.yarn_attn_factor'
        SCALING_YARN_BETA_FAST    = '{arch}.rope.scaling.yarn_beta_fast'
        SCALING_YARN_BETA_SLOW    = '{arch}.rope.scaling.yarn_beta_slow'

    class Split:
        LLM_KV_SPLIT_NO            = 'split.no'
        LLM_KV_SPLIT_COUNT         = 'split.count'
        LLM_KV_SPLIT_TENSORS_COUNT = 'split.tensors.count'

    class SSM:
        CONV_KERNEL    = '{arch}.ssm.conv_kernel'
        INNER_SIZE     = '{arch}.ssm.inner_size'
        STATE_SIZE     = '{arch}.ssm.state_size'
        TIME_STEP_RANK = '{arch}.ssm.time_step_rank'
        GROUP_COUNT    = '{arch}.ssm.group_count'
        DT_B_C_RMS     = '{arch}.ssm.dt_b_c_rms'

    class KDA:
        HEAD_DIM = '{arch}.kda.head_dim'

    class WKV:
        HEAD_SIZE = '{arch}.wkv.head_size'

    class PosNet:
        EMBEDDING_LENGTH = '{arch}.posnet.embedding_length'
        BLOCK_COUNT      = '{arch}.posnet.block_count'

    class ConvNext:
        EMBEDDING_LENGTH = '{arch}.convnext.embedding_length'
        BLOCK_COUNT      = '{arch}.convnext.block_count'

    class Classifier:
        OUTPUT_LABELS = '{arch}.classifier.output_labels'

    class ShortConv:
        L_CACHE = '{arch}.shortconv.l_cache'

    class Tokenizer:
        MODEL                = 'tokenizer.ggml.model'
        PRE                  = 'tokenizer.ggml.pre'
        LIST                 = 'tokenizer.ggml.tokens'
        TOKEN_TYPE           = 'tokenizer.ggml.token_type'
        TOKEN_TYPE_COUNT     = 'tokenizer.ggml.token_type_count'  # for BERT-style token types
        SCORES               = 'tokenizer.ggml.scores'
        MERGES               = 'tokenizer.ggml.merges'
        BOS_ID               = 'tokenizer.ggml.bos_token_id'
        EOS_ID               = 'tokenizer.ggml.eos_token_id'
        EOT_ID               = 'tokenizer.ggml.eot_token_id'
        EOM_ID               = 'tokenizer.ggml.eom_token_id'
        UNK_ID               = 'tokenizer.ggml.unknown_token_id'
        SEP_ID               = 'tokenizer.ggml.seperator_token_id'
        PAD_ID               = 'tokenizer.ggml.padding_token_id'
        MASK_ID              = 'tokenizer.ggml.mask_token_id'
        ADD_BOS              = 'tokenizer.ggml.add_bos_token'
        ADD_EOS              = 'tokenizer.ggml.add_eos_token'
        ADD_SEP              = 'tokenizer.ggml.add_sep_token'
        ADD_PREFIX           = 'tokenizer.ggml.add_space_prefix'
        REMOVE_EXTRA_WS      = 'tokenizer.ggml.remove_extra_whitespaces'
        PRECOMPILED_CHARSMAP = 'tokenizer.ggml.precompiled_charsmap'
        HF_JSON              = 'tokenizer.huggingface.json'
        RWKV                 = 'tokenizer.rwkv.world'
        CHAT_TEMPLATE        = 'tokenizer.chat_template'
        CHAT_TEMPLATE_N      = 'tokenizer.chat_template.{name}'
        CHAT_TEMPLATES       = 'tokenizer.chat_templates'
        # FIM/Infill special tokens constants
        FIM_PRE_ID           = 'tokenizer.ggml.fim_pre_token_id'
        FIM_SUF_ID           = 'tokenizer.ggml.fim_suf_token_id'
        FIM_MID_ID           = 'tokenizer.ggml.fim_mid_token_id'
        FIM_PAD_ID           = 'tokenizer.ggml.fim_pad_token_id'
        FIM_REP_ID           = 'tokenizer.ggml.fim_rep_token_id'
        FIM_SEP_ID           = 'tokenizer.ggml.fim_sep_token_id'
        # deprecated:
        PREFIX_ID            = 'tokenizer.ggml.prefix_token_id'
        SUFFIX_ID            = 'tokenizer.ggml.suffix_token_id'
        MIDDLE_ID            = 'tokenizer.ggml.middle_token_id'

    class Adapter:
        TYPE                    = 'adapter.type'
        LORA_ALPHA              = 'adapter.lora.alpha'
        LORA_TASK_NAME          = 'adapter.lora.task_name'
        LORA_PROMPT_PREFIX      = 'adapter.lora.prompt_prefix'
        ALORA_INVOCATION_TOKENS = 'adapter.alora.invocation_tokens'

    class IMatrix:
        CHUNK_COUNT = 'imatrix.chunk_count'
        CHUNK_SIZE  = 'imatrix.chunk_size'
        DATASETS    = 'imatrix.datasets'

    class Clip:
        PROJECTOR_TYPE        = 'clip.projector_type'
        HAS_VISION_ENCODER    = 'clip.has_vision_encoder'
        HAS_AUDIO_ENCODER     = 'clip.has_audio_encoder'
        HAS_LLAVA_PROJECTOR   = 'clip.has_llava_projector'

    class ClipVision:
        PROJECTOR_TYPE      = 'clip.vision.projector_type'  # for mixed modality models
        IMAGE_SIZE          = 'clip.vision.image_size'
        IMAGE_MIN_PIXELS    = 'clip.vision.image_min_pixels'
        IMAGE_MAX_PIXELS    = 'clip.vision.image_max_pixels'
        PREPROC_MIN_TILES   = 'clip.vision.preproc_min_tiles'
        PREPROC_MAX_TILES   = 'clip.vision.preproc_max_tiles'
        PREPROC_IMAGE_SIZE  = 'clip.vision.preproc_image_size'
        PATCH_SIZE          = 'clip.vision.patch_size'
        EMBEDDING_LENGTH    = 'clip.vision.embedding_length'
        FEED_FORWARD_LENGTH = 'clip.vision.feed_forward_length'
        PROJECTION_DIM      = 'clip.vision.projection_dim'
        BLOCK_COUNT         = 'clip.vision.block_count'
        IMAGE_MEAN          = 'clip.vision.image_mean'
        IMAGE_STD           = 'clip.vision.image_std'
        SPATIAL_MERGE_SIZE  = 'clip.vision.spatial_merge_size'
        USE_GELU            = 'clip.use_gelu'
        USE_SILU            = 'clip.use_silu'
        N_WA_PATTERN        = 'clip.vision.n_wa_pattern'  # used by qwen2.5vl
        WA_LAYER_INDEXES    = 'clip.vision.wa_layer_indexes'  # used by youtuvl
        IS_DEEPSTACK_LAYERS = 'clip.vision.is_deepstack_layers'
        WINDOW_SIZE         = 'clip.vision.window_size'

        class Attention:
            HEAD_COUNT      = 'clip.vision.attention.head_count'
            LAYERNORM_EPS   = 'clip.vision.attention.layer_norm_epsilon'

        class Projector:
            SCALE_FACTOR    = 'clip.vision.projector.scale_factor'

        class SAM:
            BLOCK_COUNT         = 'clip.vision.sam.block_count'
            EMBEDDING_LENGTH    = 'clip.vision.sam.embedding_length'
            HEAD_COUNT          = 'clip.vision.sam.head_count'

    class ClipAudio:
        PROJECTOR_TYPE      = 'clip.audio.projector_type'  # for mixed modality models
        NUM_MEL_BINS        = 'clip.audio.num_mel_bins'
        EMBEDDING_LENGTH    = 'clip.audio.embedding_length'
        FEED_FORWARD_LENGTH = 'clip.audio.feed_forward_length'
        PROJECTION_DIM      = 'clip.audio.projection_dim'
        BLOCK_COUNT         = 'clip.audio.block_count'
        CHUNK_SIZE          = 'clip.audio.chunk_size'
        CONV_KERNEL_SIZE    = 'clip.audio.conv_kernel_size'
        MAX_POS_EMB         = 'clip.audio.max_pos_emb'

        class Attention:
            HEAD_COUNT      = 'clip.audio.attention.head_count'
            LAYERNORM_EPS   = 'clip.audio.attention.layer_norm_epsilon'

        class Projector:
            STACK_FACTOR    = 'clip.audio.projector.stack_factor'
            WINDOW_SIZE     = 'clip.audio.projector.window_size'
            DOWNSAMPLE_RATE = 'clip.audio.projector.downsample_rate'
            HEAD_COUNT      = 'clip.audio.projector.head_count'

    class Diffusion:
        SHIFT_LOGITS        = 'diffusion.shift_logits'

    class xIELU:
        ALPHA_P             = 'xielu.alpha_p'
        ALPHA_N             = 'xielu.alpha_n'
        BETA                = 'xielu.beta'
        EPS                 = 'xielu.eps'


##
# recommended mapping of model tensor names for storage in gguf


class GGUFType:
    MODEL   = 'model'
    ADAPTER = 'adapter'
    IMATRIX = 'imatrix'
    MMPROJ  = 'mmproj'  # dummy, unused for now


class MODEL_ARCH(enum.IntEnum):
    MMPROJ           = enum.auto() # dummy arch for clip.cpp
    LLAMA            = enum.auto()
    LLAMA4           = enum.auto()
    DECI             = enum.auto()
    FALCON           = enum.auto()
    FALCON_H1        = enum.auto()
    BAICHUAN         = enum.auto()
    GROK             = enum.auto()
    GPT2             = enum.auto()
    GPTJ             = enum.auto()
    GPTNEOX          = enum.auto()
    MPT              = enum.auto()
    STARCODER        = enum.auto()
    REFACT           = enum.auto()
    BERT             = enum.auto()
    MODERN_BERT      = enum.auto()
    NOMIC_BERT       = enum.auto()
    NOMIC_BERT_MOE   = enum.auto()
    NEO_BERT         = enum.auto()
    JINA_BERT_V2     = enum.auto()
    JINA_BERT_V3     = enum.auto()
    EUROBERT         = enum.auto()
    BLOOM            = enum.auto()
    STABLELM         = enum.auto()
    QWEN             = enum.auto()
    QWEN2            = enum.auto()
    QWEN2MOE         = enum.auto()
    QWEN2VL          = enum.auto()
    QWEN3            = enum.auto()
    QWEN3MOE         = enum.auto()
    QWEN3NEXT        = enum.auto()
    QWEN3VL          = enum.auto()
    QWEN3VLMOE       = enum.auto()
    QWEN35           = enum.auto()
    QWEN35MOE        = enum.auto()
    PHI2             = enum.auto()
    PHI3             = enum.auto()
    PHIMOE           = enum.auto()
    PLAMO            = enum.auto()
    PLAMO2           = enum.auto()
    PLAMO3           = enum.auto()
    CODESHELL        = enum.auto()
    ORION            = enum.auto()
    INTERNLM2        = enum.auto()
    MINICPM          = enum.auto()
    MINICPM3         = enum.auto()
    GEMMA            = enum.auto()
    GEMMA2           = enum.auto()
    GEMMA3           = enum.auto()
    GEMMA3N          = enum.auto()
    GEMMA4           = enum.auto()
    GEMMA_EMBEDDING  = enum.auto()
    STARCODER2       = enum.auto()
    RWKV6            = enum.auto()
    RWKV6QWEN2       = enum.auto()
    RWKV7            = enum.auto()
    ARWKV7           = enum.auto()
    MAMBA            = enum.auto()
    MAMBA2           = enum.auto()
    JAMBA            = enum.auto()
    XVERSE           = enum.auto()
    COMMAND_R        = enum.auto()
    COHERE2          = enum.auto()
    DBRX             = enum.auto()
    OLMO             = enum.auto()
    OLMO2            = enum.auto()
    OLMOE            = enum.auto()
    OPENELM          = enum.auto()
    ARCTIC           = enum.auto()
    DEEPSEEK         = enum.auto()
    DEEPSEEK2        = enum.auto()
    DEEPSEEK2OCR     = enum.auto()
    CHATGLM          = enum.auto()
    GLM4             = enum.auto()
    GLM4_MOE         = enum.auto()
    GLM_DSA          = enum.auto()
    BITNET           = enum.auto()
    T5               = enum.auto()
    T5ENCODER        = enum.auto()
    JAIS             = enum.auto()
    JAIS2            = enum.auto()
    NEMOTRON         = enum.auto()
    NEMOTRON_H       = enum.auto()
    NEMOTRON_H_MOE   = enum.auto()
    EXAONE           = enum.auto()
    EXAONE4          = enum.auto()
    EXAONE_MOE       = enum.auto()
    GRANITE          = enum.auto()
    GRANITE_MOE      = enum.auto()
    GRANITE_HYBRID   = enum.auto()
    CHAMELEON        = enum.auto()
    WAVTOKENIZER_DEC = enum.auto()
    PLM              = enum.auto()
    BAILINGMOE       = enum.auto()
    BAILINGMOE2      = enum.auto()
    DOTS1            = enum.auto()
    ARCEE            = enum.auto()
    AFMOE            = enum.auto()
    ERNIE4_5         = enum.auto()
    ERNIE4_5_MOE     = enum.auto()
    HUNYUAN_MOE      = enum.auto()
    HUNYUAN_DENSE    = enum.auto()
    HUNYUAN_VL       = enum.auto()
    SMOLLM3          = enum.auto()
    GPT_OSS          = enum.auto()
    LFM2             = enum.auto()
    LFM2MOE          = enum.auto()
    DREAM            = enum.auto()
    SMALLTHINKER     = enum.auto()
    LLADA            = enum.auto()
    LLADA_MOE        = enum.auto()
    SEED_OSS         = enum.auto()
    GROVEMOE         = enum.auto()
    APERTUS          = enum.auto()
    COGVLM           = enum.auto()
    MINIMAXM2        = enum.auto()
    RND1             = enum.auto()
    PANGU_EMBED      = enum.auto()
    MISTRAL3         = enum.auto()
    MISTRAL4         = enum.auto()
    PADDLEOCR        = enum.auto()
    MIMO2            = enum.auto()
    STEP35           = enum.auto()
    LLAMA_EMBED      = enum.auto()
    MAINCODER        = enum.auto()
    KIMI_LINEAR      = enum.auto()


class VISION_PROJECTOR_TYPE(enum.IntEnum):
    MLP       = enum.auto()
    LDP       = enum.auto()
    LDPV2     = enum.auto()
    RESAMPLER = enum.auto()
    GLM_EDGE  = enum.auto()
    MERGER    = enum.auto()
    GEMMA3N   = enum.auto()
    GEMMA3    = enum.auto()
    QWEN3VL   = enum.auto()
    STEP3VL   = enum.auto()
    COGVLM    = enum.auto()


class MODEL_TENSOR(enum.IntEnum):
    TOKEN_EMBD             = enum.auto()
    TOKEN_EMBD_NORM        = enum.auto()
    TOKEN_TYPES            = enum.auto()
    POS_EMBD               = enum.auto()
    OUTPUT                 = enum.auto()
    DENSE_2_OUT            = enum.auto() # embeddinggemma 2_Dense
    DENSE_3_OUT            = enum.auto() # embeddinggemma 3_Dense
    OUTPUT_NORM            = enum.auto()
    ROPE_FREQS             = enum.auto()
    ROPE_FACTORS_LONG      = enum.auto()
    ROPE_FACTORS_SHORT     = enum.auto()
    ATTN_Q                 = enum.auto()
    ATTN_K                 = enum.auto()
    ATTN_V                 = enum.auto()
    ATTN_QKV               = enum.auto()
    ATTN_OUT               = enum.auto()
    ATTN_NORM              = enum.auto()
    ATTN_NORM_2            = enum.auto()
    ATTN_OUT_NORM          = enum.auto()
    ATTN_POST_NORM         = enum.auto()
    ATTN_ROT_EMBD          = enum.auto()
    ATTN_SINKS             = enum.auto()
    ATTN_GATE              = enum.auto()
    FFN_GATE_INP           = enum.auto()
    FFN_GATE_INP_SHEXP     = enum.auto()
    FFN_NORM               = enum.auto()
    FFN_PRE_NORM           = enum.auto() # alias of FFN_NORM
    FFN_PRE_NORM_2         = enum.auto() # gemma4
    FFN_POST_NORM          = enum.auto()
    FFN_POST_NORM_1        = enum.auto() # gemma4
    FFN_POST_NORM_2        = enum.auto() # gemma4
    FFN_GATE               = enum.auto()
    FFN_DOWN               = enum.auto()
    FFN_UP                 = enum.auto()
    FFN_ACT                = enum.auto()
    FFN_NORM_EXP           = enum.auto()
    FFN_GATE_EXP           = enum.auto()
    FFN_DOWN_EXP           = enum.auto()
    FFN_UP_EXP             = enum.auto()
    FFN_GATE_UP_EXP        = enum.auto()
    FFN_GATE_SHEXP         = enum.auto()
    FFN_DOWN_SHEXP         = enum.auto()
    FFN_UP_SHEXP           = enum.auto()
    FFN_GATE_CHEXP         = enum.auto()
    FFN_DOWN_CHEXP         = enum.auto()
    FFN_UP_CHEXP           = enum.auto()
    FFN_EXP_PROBS_B        = enum.auto()
    MOE_LATENT_DOWN        = enum.auto() # nemotron 3 super
    MOE_LATENT_UP          = enum.auto() # nemotron 3 super
    ATTN_Q_NORM            = enum.auto()
    ATTN_K_NORM            = enum.auto()
    LAYER_OUT_NORM         = enum.auto()
    LAYER_OUT_SCALE        = enum.auto()
    PER_LAYER_TOKEN_EMBD   = enum.auto() # gemma3n
    PER_LAYER_MODEL_PROJ   = enum.auto() # gemma3n
    PER_LAYER_INP_GATE     = enum.auto() # gemma3n
    PER_LAYER_PROJ         = enum.auto() # gemma3n
    PER_LAYER_PROJ_NORM    = enum.auto() # gemma3n
    PER_LAYER_POST_NORM    = enum.auto() # gemma3n
    ALTUP_PROJ             = enum.auto() # gemma3n
    ALTUP_UNEMBD_PROJ      = enum.auto() # gemma3n
    ALTUP_CORRECT_COEF     = enum.auto() # gemma3n
    ALTUP_CORRECT_SCALE    = enum.auto() # gemma3n
    ALTUP_PREDICT_COEF     = enum.auto() # gemma3n
    ALTUP_ROUTER           = enum.auto() # gemma3n
    ALTUP_ROUTER_NORM      = enum.auto() # gemma3n
    LAUREL_L               = enum.auto() # gemma3n
    LAUREL_R               = enum.auto() # gemma3n
    LAUREL_POST_NORM       = enum.auto() # gemma3n
    SSM_IN                 = enum.auto()
    SSM_CONV1D             = enum.auto()
    SSM_X                  = enum.auto()
    SSM_DT                 = enum.auto()
    SSM_DT_NORM            = enum.auto()
    SSM_A                  = enum.auto()
    SSM_B_NORM             = enum.auto()
    SSM_C_NORM             = enum.auto()
    SSM_D                  = enum.auto()
    SSM_NORM               = enum.auto()
    SSM_OUT                = enum.auto()
    SSM_ALPHA              = enum.auto() # qwen3.5
    SSM_BETA_ALPHA         = enum.auto() # qwen3next
    SSM_CONV1D_Q           = enum.auto() # Kimi Linear
    SSM_CONV1D_K           = enum.auto() # Kimi Linear
    SSM_CONV1D_V           = enum.auto() # Kimi Linear
    SSM_F_A                = enum.auto() # Kimi Linear
    SSM_F_B                = enum.auto() # Kimi Linear
    SSM_BETA               = enum.auto() # Kimi Linear qwen3.5
    SSM_G_A                = enum.auto() # Kimi Linear
    SSM_G_B                = enum.auto() # Kimi Linear
    TIME_MIX_W0            = enum.auto()
    TIME_MIX_W1            = enum.auto()
    TIME_MIX_W2            = enum.auto()
    TIME_MIX_A0            = enum.auto()
    TIME_MIX_A1            = enum.auto()
    TIME_MIX_A2            = enum.auto()
    TIME_MIX_V0            = enum.auto()
    TIME_MIX_V1            = enum.auto()
    TIME_MIX_V2            = enum.auto()
    TIME_MIX_G1            = enum.auto()
    TIME_MIX_G2            = enum.auto()
    TIME_MIX_K_K           = enum.auto()
    TIME_MIX_K_A           = enum.auto()
    TIME_MIX_R_K           = enum.auto()
    TIME_MIX_LERP_X        = enum.auto()
    TIME_MIX_LERP_K        = enum.auto()
    TIME_MIX_LERP_V        = enum.auto()
    TIME_MIX_LERP_R        = enum.auto()
    TIME_MIX_LERP_G        = enum.auto()
    TIME_MIX_LERP_FUSED    = enum.auto()
    TIME_MIX_LERP_W        = enum.auto()
    TIME_MIX_FIRST         = enum.auto()
    TIME_MIX_DECAY         = enum.auto()
    TIME_MIX_DECAY_W1      = enum.auto()
    TIME_MIX_DECAY_W2      = enum.auto()
    TIME_MIX_KEY           = enum.auto()
    TIME_MIX_VALUE         = enum.auto()
    TIME_MIX_RECEPTANCE    = enum.auto()
    TIME_MIX_GATE          = enum.auto()
    TIME_MIX_LN            = enum.auto()
    TIME_MIX_OUTPUT        = enum.auto()
    CHANNEL_MIX_LERP_K     = enum.auto()
    CHANNEL_MIX_LERP_R     = enum.auto()
    CHANNEL_MIX_KEY        = enum.auto()
    CHANNEL_MIX_RECEPTANCE = enum.auto()
    CHANNEL_MIX_VALUE      = enum.auto()
    ATTN_Q_A               = enum.auto()
    ATTN_Q_B               = enum.auto()
    ATTN_KV_A_MQA          = enum.auto()
    ATTN_KV_B              = enum.auto()
    ATTN_K_B               = enum.auto()
    ATTN_V_B               = enum.auto()
    ATTN_Q_A_NORM          = enum.auto()
    ATTN_KV_A_NORM         = enum.auto()
    FFN_SUB_NORM           = enum.auto()
    ATTN_SUB_NORM          = enum.auto()
    DEC_ATTN_NORM          = enum.auto()
    DEC_ATTN_Q             = enum.auto()
    DEC_ATTN_K             = enum.auto()
    DEC_ATTN_V             = enum.auto()
    DEC_ATTN_OUT           = enum.auto()
    DEC_ATTN_REL_B         = enum.auto()
    DEC_CROSS_ATTN_NORM    = enum.auto()
    DEC_CROSS_ATTN_Q       = enum.auto()
    DEC_CROSS_ATTN_K       = enum.auto()
    DEC_CROSS_ATTN_V       = enum.auto()
    DEC_CROSS_ATTN_OUT     = enum.auto()
    DEC_CROSS_ATTN_REL_B   = enum.auto()
    DEC_FFN_NORM           = enum.auto()
    DEC_FFN_GATE           = enum.auto()
    DEC_FFN_DOWN           = enum.auto()
    DEC_FFN_UP             = enum.auto()
    DEC_OUTPUT_NORM        = enum.auto()
    ENC_ATTN_NORM          = enum.auto()
    ENC_ATTN_Q             = enum.auto()
    ENC_ATTN_K             = enum.auto()
    ENC_ATTN_V             = enum.auto()
    ENC_ATTN_OUT           = enum.auto()
    ENC_ATTN_REL_B         = enum.auto()
    ENC_FFN_NORM           = enum.auto()
    ENC_FFN_GATE           = enum.auto()
    ENC_FFN_DOWN           = enum.auto()
    ENC_FFN_UP             = enum.auto()
    ENC_OUTPUT_NORM        = enum.auto()
    CLS                    = enum.auto() # classifier
    CLS_OUT                = enum.auto() # classifier output projection
    CLS_NORM               = enum.auto()
    CONV1D                 = enum.auto()
    CONVNEXT_DW            = enum.auto()
    CONVNEXT_NORM          = enum.auto()
    CONVNEXT_PW1           = enum.auto()
    CONVNEXT_PW2           = enum.auto()
    CONVNEXT_GAMMA         = enum.auto()
    POSNET_CONV1           = enum.auto()
    POSNET_CONV2           = enum.auto()
    POSNET_NORM            = enum.auto()
    POSNET_NORM1           = enum.auto()
    POSNET_NORM2           = enum.auto()
    POSNET_ATTN_NORM       = enum.auto()
    POSNET_ATTN_Q          = enum.auto()
    POSNET_ATTN_K          = enum.auto()
    POSNET_ATTN_V          = enum.auto()
    POSNET_ATTN_OUT        = enum.auto()
    SHORTCONV_CONV         = enum.auto()
    SHORTCONV_INPROJ       = enum.auto()
    SHORTCONV_OUTPROJ      = enum.auto()
    VISEXP_ATTN_QKV        = enum.auto()
    VISEXP_ATTN_OUT        = enum.auto()
    VISEXP_GATE            = enum.auto()
    VISEXP_DOWN            = enum.auto()
    VISEXP_UP              = enum.auto()
    INDEXER_K_NORM         = enum.auto()
    INDEXER_PROJ           = enum.auto()
    INDEXER_ATTN_K         = enum.auto()
    INDEXER_ATTN_Q_B       = enum.auto()
    # vision
    V_MMPROJ               = enum.auto()
    V_MMPROJ_FC            = enum.auto()
    V_MMPROJ_MLP           = enum.auto()
    V_MMPROJ_PEG           = enum.auto()
    V_ENC_EMBD_CLS         = enum.auto()
    V_ENC_EMBD_PATCH       = enum.auto()
    V_ENC_EMBD_NORM        = enum.auto()
    V_ENC_EMBD_POS         = enum.auto()
    V_ENC_INPUT_NORM       = enum.auto()
    V_ENC_ATTN_QKV         = enum.auto()
    V_ENC_ATTN_Q           = enum.auto()
    V_ENC_ATTN_Q_NORM      = enum.auto()
    V_ENC_ATTN_K           = enum.auto()
    V_ENC_ATTN_K_NORM      = enum.auto()
    V_ENC_ATTN_V           = enum.auto()
    V_ENC_ATTN_O           = enum.auto()
    V_ENC_ATTN_O_NORM      = enum.auto()
    V_ENC_POST_ATTN_NORM   = enum.auto()
    V_ENC_FFN_UP           = enum.auto()
    V_ENC_FFN_GATE         = enum.auto()
    V_ENC_FFN_DOWN         = enum.auto()
    V_ENC_ATTN_POST_NORM   = enum.auto() # gemma4
    V_ENC_FFN_POST_NORM    = enum.auto()
    V_LAYER_SCALE_1        = enum.auto()
    V_LAYER_SCALE_2        = enum.auto()
    V_LAYER_OUT_SCALE      = enum.auto()
    V_PRE_NORM             = enum.auto()
    V_POST_NORM            = enum.auto()
    V_MM_PRE_NORM          = enum.auto() # hunyuanocr
    V_MM_POST_NORM         = enum.auto()
    V_MM_INP_NORM          = enum.auto()
    V_MM_INP_PROJ          = enum.auto() # gemma3
    V_MM_SOFT_EMB_NORM     = enum.auto() # gemma3
    V_MM_EMBEDDING         = enum.auto() # gemma3n
    V_MM_HARD_EMB_NORM     = enum.auto() # gemma3n
    V_ENC_CONV_STEM        = enum.auto() # gemma3n
    V_ENC_CONV_STEM_NORM   = enum.auto() # gemma3n
    V_ENC_MSFA_EXP         = enum.auto() # gemma3n
    V_ENC_MSFA_EXP_NORM    = enum.auto() # gemma3n
    V_ENC_MSFA_PROJ        = enum.auto() # gemma3n
    V_ENC_MSFA_PROJ_NORM   = enum.auto() # gemma3n
    V_ENC_MSFA_NORM        = enum.auto() # gemma3n
    V_RESMPL_POS_EMBD_K    = enum.auto() # minicpmv
    V_RESMPL_ATTN_Q        = enum.auto() # minicpmv
    V_RESMPL_ATTN_K        = enum.auto() # minicpmv
    V_RESMPL_ATTN_V        = enum.auto() # minicpmv
    V_RESMPL_ATTN_OUT      = enum.auto() # minicpmv
    V_RESMPL_KV            = enum.auto() # minicpmv
    V_RESMPL_KV_NORM       = enum.auto() # minicpmv
    V_RESMPL_POST_NORM     = enum.auto() # minicpmv
    V_RESMPL_Q_NORM        = enum.auto() # minicpmv
    V_RESMPL_PROJ          = enum.auto() # minicpmv
    V_RESMPL_QUERY         = enum.auto() # minicpmv
    V_TOK_EMBD_IMG_BREAK   = enum.auto() # pixtral
    V_MM_PATCH_MERGER      = enum.auto() # mistral small 3.1
    V_DS_NORM              = enum.auto() # qwen3vl
    V_DS_FC1               = enum.auto() # qwen3vl
    V_DS_FC2               = enum.auto() # qwen3vl
    V_MM_POST_FC_NORM      = enum.auto() # cogvlm
    V_MM_UP                = enum.auto() # cogvlm
    V_MM_DOWN              = enum.auto() # cogvlm
    V_MM_GATE              = enum.auto() # cogvlm
    V_TOK_BOI              = enum.auto() # cogvlm
    V_TOK_EOI              = enum.auto() # cogvlm
    V_TOK_IMG_BEGIN        = enum.auto() # hunyuanocr
    V_TOK_IMG_END          = enum.auto() # hunyuanocr
    V_STD_BIAS             = enum.auto() # gemma4
    V_STD_SCALE            = enum.auto() # gemma4
    V_SAM_POS_EMBD         = enum.auto() # Deepseek-OCR
    V_SAM_PATCH_EMBD       = enum.auto() # Deepseek-OCR
    V_SAM_PRE_NORM         = enum.auto() # Deepseek-OCR
    V_SAM_POST_NORM        = enum.auto() # Deepseek-OCR
    V_SAM_ATTN_POS_H       = enum.auto() # Deepseek-OCR
    V_SAM_ATTN_POS_W       = enum.auto() # Deepseek-OCR
    V_SAM_ATTN_QKV         = enum.auto() # Deepseek-OCR
    V_SAM_ATTN_OUT         = enum.auto() # Deepseek-OCR
    V_SAM_MLP_LIN_1        = enum.auto() # Deepseek-OCR
    V_SAM_MLP_LIN_2        = enum.auto() # Deepseek-OCR
    V_SAM_NECK             = enum.auto() # Deepseek-OCR
    V_SAM_NET_2            = enum.auto() # Deepseek-OCR
    V_SAM_NET_3            = enum.auto() # Deepseek-OCR
    V_ENC_EMBD_IMGNL       = enum.auto() # Deepseek-OCR
    V_ENC_EMBD_VSEP        = enum.auto() # Deepseek-OCR

    # audio (mtmd)
    A_ENC_EMBD_POS         = enum.auto()
    A_ENC_EMBD_NORM        = enum.auto()
    A_ENC_EMBD_TO_LOGITS   = enum.auto() # lfm2
    A_ENC_INP_PROJ         = enum.auto() # gemma4
    A_ENC_CONV1D           = enum.auto()
    A_ENC_CONV1D_NORM      = enum.auto() # gemma3n
    A_ENC_CONV2D           = enum.auto()
    A_ENC_CONV_OUT         = enum.auto()
    A_PRE_NORM             = enum.auto()
    A_POST_NORM            = enum.auto()
    A_ENC_LAYER_PRE_NORM   = enum.auto() # gemma3n
    A_ENC_ATTN_Q           = enum.auto()
    A_ENC_ATTN_K           = enum.auto()
    A_ENC_ATTN_V           = enum.auto()
    A_ENC_ATTN_POST_NORM   = enum.auto()
    A_ENC_ATTN_PRE_NORM    = enum.auto()
    A_ENC_ATTN_K_REL       = enum.auto() # gemma4
    A_ENC_PER_DIM_SCALE    = enum.auto() # gemma3n
    A_ENC_INPUT_NORM       = enum.auto()
    A_ENC_OUTPUT           = enum.auto() # TODO @ngxson: rename to ATTN_OUT
    A_ENC_OUTPUT_NORM      = enum.auto() # TODO @ngxson: rename to ATTN_OUT
    A_ENC_FFN_UP           = enum.auto()
    A_ENC_FFN_NORM         = enum.auto()
    A_ENC_FFN_POST_NORM    = enum.auto() # gemma3n
    A_ENC_FFN_SCALE        = enum.auto() # gemma3n
    A_ENC_FFN_GATE         = enum.auto()
    A_ENC_FFN_DOWN         = enum.auto()
    A_ENC_FFN_UP_1         = enum.auto() # lfm2, gemma3n
    A_ENC_FFN_NORM_1       = enum.auto() # lfm2, gemma3n (pre-norm)
    A_ENC_FFN_POST_NORM_1  = enum.auto() # gemma3n
    A_ENC_FFN_SCALE_1      = enum.auto() # gemma3n
    A_ENC_FFN_GATE_1       = enum.auto() # lfm2, gemma3n
    A_ENC_FFN_DOWN_1       = enum.auto() # lfm2, gemma3n
    A_MMPROJ               = enum.auto()
    A_MMPROJ_FC            = enum.auto()
    A_MM_NORM_PRE          = enum.auto()
    A_MM_NORM_MID          = enum.auto()
    A_MM_EMBEDDING         = enum.auto() # gemma3n
    A_MM_HARD_EMB_NORM     = enum.auto() # gemma3n
    A_MM_SOFT_EMB_NORM     = enum.auto() # gemma3n
    A_MM_INP_PROJ          = enum.auto() # gemma3n
    A_PER_DIM_K_SCALE      = enum.auto() # gemma4
    A_PER_DIM_SCALE        = enum.auto() # gemma4
    # nextn/mtp
    NEXTN_EH_PROJ          = enum.auto()
    NEXTN_EMBED_TOKENS     = enum.auto()
    NEXTN_ENORM            = enum.auto()
    NEXTN_HNORM            = enum.auto()
    NEXTN_SHARED_HEAD_HEAD = enum.auto()
    NEXTN_SHARED_HEAD_NORM = enum.auto()
    # lfm2 audio
    A_ENC_NORM_CONV        = enum.auto()
    A_ENC_LINEAR_POS       = enum.auto()
    A_ENC_POS_BIAS_U       = enum.auto()
    A_ENC_POS_BIAS_V       = enum.auto()
    A_ENC_OUT              = enum.auto()
    A_ENC_CONV_DW          = enum.auto() # SSM conv
    A_ENC_CONV_NORM        = enum.auto() # SSM conv
    A_ENC_CONV_PW1         = enum.auto()
    A_ENC_CONV_PW2         = enum.auto()
    A_CTC_OUT              = enum.auto()
    A_CTC_OUT_MID          = enum.auto()
    A_ENC_ATTN_REL_POS_EMB = enum.auto()
    # qformer projector
    A_QF_PROJ_QUERY        = enum.auto()
    A_QF_PROJ_NORM         = enum.auto()
    A_QF_PROJ_LINEAR       = enum.auto()
    A_QF_SELF_ATTN_Q       = enum.auto()
    A_QF_SELF_ATTN_K       = enum.auto()
    A_QF_SELF_ATTN_V       = enum.auto()
    A_QF_SELF_ATTN_O       = enum.auto()
    A_QF_SELF_ATTN_NORM    = enum.auto()
    A_QF_CROSS_ATTN_Q      = enum.auto()
    A_QF_CROSS_ATTN_K      = enum.auto()
    A_QF_CROSS_ATTN_V      = enum.auto()
    A_QF_CROSS_ATTN_O      = enum.auto()
    A_QF_CROSS_ATTN_NORM   = enum.auto()
    A_QF_FFN_UP            = enum.auto()
    A_QF_FFN_DOWN          = enum.auto()
    A_QF_FFN_NORM          = enum.auto()


MODEL_ARCH_NAMES: dict[MODEL_ARCH, str] = {
    MODEL_ARCH.MMPROJ:           'clip', # dummy arch for clip.cpp
    MODEL_ARCH.LLAMA:            'llama',
    MODEL_ARCH.LLAMA4:           'llama4',
    MODEL_ARCH.DECI:             'deci',
    MODEL_ARCH.FALCON:           'falcon',
    MODEL_ARCH.BAICHUAN:         'baichuan',
    MODEL_ARCH.GROK:             'grok',
    MODEL_ARCH.GPT2:             'gpt2',
    MODEL_ARCH.GPTJ:             'gptj',
    MODEL_ARCH.GPTNEOX:          'gptneox',
    MODEL_ARCH.MPT:              'mpt',
    MODEL_ARCH.STARCODER:        'starcoder',
    MODEL_ARCH.REFACT:           'refact',
    MODEL_ARCH.BERT:             'bert',
    MODEL_ARCH.MODERN_BERT:      'modern-bert',
    MODEL_ARCH.NOMIC_BERT:       'nomic-bert',
    MODEL_ARCH.NOMIC_BERT_MOE:   'nomic-bert-moe',
    MODEL_ARCH.NEO_BERT:         'neo-bert',
    MODEL_ARCH.JINA_BERT_V2:     'jina-bert-v2',
    MODEL_ARCH.JINA_BERT_V3:     'jina-bert-v3',
    MODEL_ARCH.EUROBERT:         'eurobert',
    MODEL_ARCH.BLOOM:            'bloom',
    MODEL_ARCH.STABLELM:         'stablelm',
    MODEL_ARCH.QWEN:             'qwen',
    MODEL_ARCH.QWEN2:            'qwen2',
    MODEL_ARCH.QWEN2MOE:         'qwen2moe',
    MODEL_ARCH.QWEN2VL:          'qwen2vl',
    MODEL_ARCH.QWEN3:            'qwen3',
    MODEL_ARCH.QWEN3MOE:         'qwen3moe',
    MODEL_ARCH.QWEN3NEXT:        'qwen3next',
    MODEL_ARCH.QWEN3VL:          'qwen3vl',
    MODEL_ARCH.QWEN3VLMOE:       'qwen3vlmoe',
    MODEL_ARCH.QWEN35:           'qwen35',
    MODEL_ARCH.QWEN35MOE:        'qwen35moe',
    MODEL_ARCH.PHI2:             'phi2',
    MODEL_ARCH.PHI3:             'phi3',
    MODEL_ARCH.PHIMOE:           'phimoe',
    MODEL_ARCH.PLAMO:            'plamo',
    MODEL_ARCH.PLAMO2:           'plamo2',
    MODEL_ARCH.PLAMO3:           'plamo3',
    MODEL_ARCH.CODESHELL:        'codeshell',
    MODEL_ARCH.ORION:            'orion',
    MODEL_ARCH.INTERNLM2:        'internlm2',
    MODEL_ARCH.MINICPM:          'minicpm',
    MODEL_ARCH.MINICPM3:         'minicpm3',
    MODEL_ARCH.GEMMA:            'gemma',
    MODEL_ARCH.GEMMA2:           'gemma2',
    MODEL_ARCH.GEMMA3:           'gemma3',
    MODEL_ARCH.GEMMA3N:          'gemma3n',
    MODEL_ARCH.GEMMA4:           'gemma4',
    MODEL_ARCH.GEMMA_EMBEDDING:  'gemma-embedding',
    MODEL_ARCH.STARCODER2:       'starcoder2',
    MODEL_ARCH.RWKV6:            'rwkv6',
    MODEL_ARCH.RWKV6QWEN2:       'rwkv6qwen2',
    MODEL_ARCH.RWKV7:            'rwkv7',
    MODEL_ARCH.ARWKV7:           'arwkv7',
    MODEL_ARCH.MAMBA:            'mamba',
    MODEL_ARCH.MAMBA2:           'mamba2',
    MODEL_ARCH.JAMBA:            'jamba',
    MODEL_ARCH.XVERSE:           'xverse',
    MODEL_ARCH.COMMAND_R:        'command-r',
    MODEL_ARCH.COHERE2:          'cohere2',
    MODEL_ARCH.DBRX:             'dbrx',
    MODEL_ARCH.OLMO:             'olmo',
    MODEL_ARCH.OLMO2:            'olmo2',
    MODEL_ARCH.OLMOE:            'olmoe',
    MODEL_ARCH.OPENELM:          'openelm',
    MODEL_ARCH.ARCTIC:           'arctic',
    MODEL_ARCH.DEEPSEEK:         'deepseek',
    MODEL_ARCH.DEEPSEEK2:        'deepseek2',
    MODEL_ARCH.DEEPSEEK2OCR:     'deepseek2-ocr',
    MODEL_ARCH.CHATGLM:          'chatglm',
    MODEL_ARCH.GLM4:             'glm4',
    MODEL_ARCH.GLM4_MOE:         'glm4moe',
    MODEL_ARCH.GLM_DSA:          'glm-dsa',
    MODEL_ARCH.BITNET:           'bitnet',
    MODEL_ARCH.T5:               't5',
    MODEL_ARCH.T5ENCODER:        't5encoder',
    MODEL_ARCH.JAIS:             'jais',
    MODEL_ARCH.JAIS2:            'jais2',
    MODEL_ARCH.NEMOTRON:         'nemotron',
    MODEL_ARCH.NEMOTRON_H:       'nemotron_h',
    MODEL_ARCH.NEMOTRON_H_MOE:   'nemotron_h_moe',
    MODEL_ARCH.EXAONE:           'exaone',
    MODEL_ARCH.EXAONE4:          'exaone4',
    MODEL_ARCH.EXAONE_MOE:       'exaone-moe',
    MODEL_ARCH.GRANITE:          'granite',
    MODEL_ARCH.GRANITE_MOE:      'granitemoe',
    MODEL_ARCH.GRANITE_HYBRID:   'granitehybrid',
    MODEL_ARCH.CHAMELEON:        'chameleon',
    MODEL_ARCH.WAVTOKENIZER_DEC: 'wavtokenizer-dec',
    MODEL_ARCH.PLM:              'plm',
    MODEL_ARCH.BAILINGMOE:       'bailingmoe',
    MODEL_ARCH.BAILINGMOE2:      'bailingmoe2',
    MODEL_ARCH.DOTS1:            'dots1',
    MODEL_ARCH.ARCEE:            'arcee',
    MODEL_ARCH.AFMOE:            'afmoe',
    MODEL_ARCH.ERNIE4_5:         'ernie4_5',
    MODEL_ARCH.ERNIE4_5_MOE:     'ernie4_5-moe',
    MODEL_ARCH.FALCON_H1:        'falcon-h1',
    MODEL_ARCH.HUNYUAN_MOE:      'hunyuan-moe',
    MODEL_ARCH.HUNYUAN_DENSE:    'hunyuan-dense',
    MODEL_ARCH.HUNYUAN_VL:       'hunyuan_vl',
    MODEL_ARCH.SMOLLM3:          'smollm3',
    MODEL_ARCH.GPT_OSS:          'gpt-oss',
    MODEL_ARCH.LFM2:             'lfm2',
    MODEL_ARCH.LFM2MOE:          'lfm2moe',
    MODEL_ARCH.DREAM:            'dream',
    MODEL_ARCH.SMALLTHINKER:     'smallthinker',
    MODEL_ARCH.LLADA:            'llada',
    MODEL_ARCH.LLADA_MOE:        'llada-moe',
    MODEL_ARCH.SEED_OSS:         'seed_oss',
    MODEL_ARCH.GROVEMOE:         'grovemoe',
    MODEL_ARCH.APERTUS:          'apertus',
    MODEL_ARCH.MINIMAXM2:        'minimax-m2',
    MODEL_ARCH.COGVLM:           'cogvlm',
    MODEL_ARCH.RND1:             'rnd1',
    MODEL_ARCH.PANGU_EMBED:      'pangu-embedded',
    MODEL_ARCH.MISTRAL3:         'mistral3',
    MODEL_ARCH.MISTRAL4:         'mistral4',
    MODEL_ARCH.PADDLEOCR:        'paddleocr',
    MODEL_ARCH.MIMO2:            'mimo2',
    MODEL_ARCH.STEP35:           'step35',
    MODEL_ARCH.LLAMA_EMBED:      'llama-embed',
    MODEL_ARCH.MAINCODER:        'maincoder',
    MODEL_ARCH.KIMI_LINEAR:      'kimi-linear',
}

VISION_PROJECTOR_TYPE_NAMES: dict[VISION_PROJECTOR_TYPE, str] = {
    VISION_PROJECTOR_TYPE.MLP:       'mlp',
    VISION_PROJECTOR_TYPE.LDP:       'ldp',
    VISION_PROJECTOR_TYPE.LDPV2:     'ldpv2',
    VISION_PROJECTOR_TYPE.RESAMPLER: 'resampler',
    VISION_PROJECTOR_TYPE.GLM_EDGE:  'adapter',
    VISION_PROJECTOR_TYPE.MERGER:    'qwen2vl_merger',
    VISION_PROJECTOR_TYPE.GEMMA3:    'gemma3',
    VISION_PROJECTOR_TYPE.QWEN3VL:   'qwen3vl_merger',
    VISION_PROJECTOR_TYPE.STEP3VL:   'step3vl',
}

TENSOR_NAMES: dict[MODEL_TENSOR, str] = {
    MODEL_TENSOR.TOKEN_EMBD:                'token_embd',
    MODEL_TENSOR.TOKEN_EMBD_NORM:           'token_embd_norm',
    MODEL_TENSOR.TOKEN_TYPES:               'token_types',
    MODEL_TENSOR.POS_EMBD:                  'position_embd',
    MODEL_TENSOR.OUTPUT_NORM:               'output_norm',
    MODEL_TENSOR.OUTPUT:                    'output',
    MODEL_TENSOR.DENSE_2_OUT:                'dense_2', # embeddinggemma 2_Dense
    MODEL_TENSOR.DENSE_3_OUT:                'dense_3', # embeddinggemma 2_Dense
    MODEL_TENSOR.ROPE_FREQS:                'rope_freqs',
    MODEL_TENSOR.ROPE_FACTORS_LONG:         'rope_factors_long',
    MODEL_TENSOR.ROPE_FACTORS_SHORT:        'rope_factors_short',
    MODEL_TENSOR.ATTN_NORM:                 'blk.{bid}.attn_norm',
    MODEL_TENSOR.ATTN_NORM_2:               'blk.{bid}.attn_norm_2',
    MODEL_TENSOR.ATTN_QKV:                  'blk.{bid}.attn_qkv',
    MODEL_TENSOR.ATTN_Q:                    'blk.{bid}.attn_q',
    MODEL_TENSOR.ATTN_K:                    'blk.{bid}.attn_k',
    MODEL_TENSOR.ATTN_V:                    'blk.{bid}.attn_v',
    MODEL_TENSOR.ATTN_OUT:                  'blk.{bid}.attn_output',
    MODEL_TENSOR.ATTN_ROT_EMBD:             'blk.{bid}.attn_rot_embd',
    MODEL_TENSOR.ATTN_SINKS:                'blk.{bid}.attn_sinks',
    MODEL_TENSOR.ATTN_GATE:                 'blk.{bid}.attn_gate',
    MODEL_TENSOR.ATTN_Q_NORM:               'blk.{bid}.attn_q_norm',
    MODEL_TENSOR.ATTN_K_NORM:               'blk.{bid}.attn_k_norm',
    MODEL_TENSOR.ATTN_OUT_NORM:             'blk.{bid}.attn_output_norm',
    MODEL_TENSOR.ATTN_POST_NORM:            'blk.{bid}.post_attention_norm',
    MODEL_TENSOR.FFN_GATE_INP:              'blk.{bid}.ffn_gate_inp',
    MODEL_TENSOR.FFN_GATE_INP_SHEXP:        'blk.{bid}.ffn_gate_inp_shexp',
    MODEL_TENSOR.FFN_NORM:                  'blk.{bid}.ffn_norm',
    MODEL_TENSOR.FFN_PRE_NORM:              'blk.{bid}.ffn_norm',
    MODEL_TENSOR.FFN_POST_NORM:             'blk.{bid}.post_ffw_norm',
    MODEL_TENSOR.FFN_PRE_NORM_2:            'blk.{bid}.pre_ffw_norm_2',  # gemma4
    MODEL_TENSOR.FFN_POST_NORM_1:           'blk.{bid}.post_ffw_norm_1', # gemma4
    MODEL_TENSOR.FFN_POST_NORM_2:           'blk.{bid}.post_ffw_norm_2', # gemma4
    MODEL_TENSOR.FFN_GATE:                  'blk.{bid}.ffn_gate',
    MODEL_TENSOR.FFN_DOWN:                  'blk.{bid}.ffn_down',
    MODEL_TENSOR.FFN_UP:                    'blk.{bid}.ffn_up',
    MODEL_TENSOR.FFN_GATE_SHEXP:            'blk.{bid}.ffn_gate_shexp',
    MODEL_TENSOR.FFN_DOWN_SHEXP:            'blk.{bid}.ffn_down_shexp',
    MODEL_TENSOR.FFN_UP_SHEXP:              'blk.{bid}.ffn_up_shexp',
    MODEL_TENSOR.FFN_GATE_CHEXP:            'blk.{bid}.ffn_gate_chexps',
    MODEL_TENSOR.FFN_DOWN_CHEXP:            'blk.{bid}.ffn_down_chexps',
    MODEL_TENSOR.FFN_UP_CHEXP:              'blk.{bid}.ffn_up_chexps',
    MODEL_TENSOR.FFN_ACT:                   'blk.{bid}.ffn',
    MODEL_TENSOR.FFN_NORM_EXP:              'blk.{bid}.ffn_norm_exps',
    MODEL_TENSOR.FFN_GATE_EXP:              'blk.{bid}.ffn_gate_exps',
    MODEL_TENSOR.FFN_DOWN_EXP:              'blk.{bid}.ffn_down_exps',
    MODEL_TENSOR.FFN_UP_EXP:                'blk.{bid}.ffn_up_exps',
    MODEL_TENSOR.FFN_GATE_UP_EXP:           'blk.{bid}.ffn_gate_up_exps',
    MODEL_TENSOR.FFN_EXP_PROBS_B:           'blk.{bid}.exp_probs_b',
    MODEL_TENSOR.MOE_LATENT_DOWN:           'blk.{bid}.ffn_latent_down',      # nemotron 3 super
    MODEL_TENSOR.MOE_LATENT_UP:             'blk.{bid}.ffn_latent_up',        # nemotron 3 super
    MODEL_TENSOR.LAYER_OUT_NORM:            'blk.{bid}.layer_output_norm',
    MODEL_TENSOR.LAYER_OUT_SCALE:           'blk.{bid}.layer_output_scale',
    MODEL_TENSOR.PER_LAYER_TOKEN_EMBD:      'per_layer_token_embd',           # gemma3n
    MODEL_TENSOR.PER_LAYER_MODEL_PROJ:      'per_layer_model_proj',           # gemma3n
    MODEL_TENSOR.PER_LAYER_PROJ_NORM:       'per_layer_proj_norm',            # gemma3n
    MODEL_TENSOR.ALTUP_UNEMBD_PROJ:         'altup_unembd_proj',              # gemma3n
    MODEL_TENSOR.ALTUP_PROJ:                'altup_proj',                     # gemma3n
    MODEL_TENSOR.PER_LAYER_INP_GATE:        'blk.{bid}.inp_gate',             # gemma3n
    MODEL_TENSOR.PER_LAYER_PROJ:            'blk.{bid}.proj',                 # gemma3n
    MODEL_TENSOR.PER_LAYER_POST_NORM:       'blk.{bid}.post_norm',            # gemma3n
    MODEL_TENSOR.ALTUP_CORRECT_COEF:        'blk.{bid}.altup_correct_coef',   # gemma3n
    MODEL_TENSOR.ALTUP_CORRECT_SCALE:       'blk.{bid}.altup_correct_scale',  # gemma3n
    MODEL_TENSOR.ALTUP_PREDICT_COEF:        'blk.{bid}.altup_predict_coef',   # gemma3n
    MODEL_TENSOR.ALTUP_ROUTER:              'blk.{bid}.altup_router',         # gemma3n
    MODEL_TENSOR.ALTUP_ROUTER_NORM:         'blk.{bid}.altup_router_norm',    # gemma3n
    MODEL_TENSOR.LAUREL_L:                  'blk.{bid}.laurel_l',             # gemma3n
    MODEL_TENSOR.LAUREL_R:                  'blk.{bid}.laurel_r',             # gemma3n
    MODEL_TENSOR.LAUREL_POST_NORM:          'blk.{bid}.laurel_post_norm',     # gemma3n
    MODEL_TENSOR.SSM_IN:                    'blk.{bid}.ssm_in',
    MODEL_TENSOR.SSM_CONV1D:                'blk.{bid}.ssm_conv1d',
    MODEL_TENSOR.SSM_X:                     'blk.{bid}.ssm_x',
    MODEL_TENSOR.SSM_DT:                    'blk.{bid}.ssm_dt',
    MODEL_TENSOR.SSM_DT_NORM:               'blk.{bid}.ssm_dt_norm',
    MODEL_TENSOR.SSM_A:                     'blk.{bid}.ssm_a',
    MODEL_TENSOR.SSM_B_NORM:                'blk.{bid}.ssm_b_norm',
    MODEL_TENSOR.SSM_C_NORM:                'blk.{bid}.ssm_c_norm',
    MODEL_TENSOR.SSM_D:                     'blk.{bid}.ssm_d',
    MODEL_TENSOR.SSM_NORM:                  'blk.{bid}.ssm_norm',
    MODEL_TENSOR.SSM_OUT:                   'blk.{bid}.ssm_out',
    MODEL_TENSOR.SSM_ALPHA:                 'blk.{bid}.ssm_alpha',            # qwen3.5
    MODEL_TENSOR.SSM_BETA_ALPHA:            'blk.{bid}.ssm_ba',
    MODEL_TENSOR.SSM_CONV1D_Q:              'blk.{bid}.ssm_conv1d_q',         # Kimi Linear
    MODEL_TENSOR.SSM_CONV1D_K:              'blk.{bid}.ssm_conv1d_k',         # Kimi Linear
    MODEL_TENSOR.SSM_CONV1D_V:              'blk.{bid}.ssm_conv1d_v',         # Kimi Linear
    MODEL_TENSOR.SSM_F_A:                   'blk.{bid}.ssm_f_a',              # Kimi Linear
    MODEL_TENSOR.SSM_F_B:                   'blk.{bid}.ssm_f_b',              # Kimi Linear
    MODEL_TENSOR.SSM_BETA:                  'blk.{bid}.ssm_beta',             # Kimi Linear qwen3.5
    MODEL_TENSOR.SSM_G_A:                   'blk.{bid}.ssm_g_a',              # Kimi Linear
    MODEL_TENSOR.SSM_G_B:                   'blk.{bid}.ssm_g_b',              # Kimi Linear
    MODEL_TENSOR.TIME_MIX_W0:               'blk.{bid}.time_mix_w0',
    MODEL_TENSOR.TIME_MIX_W1:               'blk.{bid}.time_mix_w1',
    MODEL_TENSOR.TIME_MIX_W2:               'blk.{bid}.time_mix_w2',
    MODEL_TENSOR.TIME_MIX_A0:               'blk.{bid}.time_mix_a0',
    MODEL_TENSOR.TIME_MIX_A1:               'blk.{bid}.time_mix_a1',
    MODEL_TENSOR.TIME_MIX_A2:               'blk.{bid}.time_mix_a2',
    MODEL_TENSOR.TIME_MIX_V0:               'blk.{bid}.time_mix_v0',
    MODEL_TENSOR.TIME_MIX_V1:               'blk.{bid}.time_mix_v1',
    MODEL_TENSOR.TIME_MIX_V2:               'blk.{bid}.time_mix_v2',
    MODEL_TENSOR.TIME_MIX_G1:               'blk.{bid}.time_mix_g1',
    MODEL_TENSOR.TIME_MIX_G2:               'blk.{bid}.time_mix_g2',
    MODEL_TENSOR.TIME_MIX_K_K:              'blk.{bid}.time_mix_k_k',
    MODEL_TENSOR.TIME_MIX_K_A:              'blk.{bid}.time_mix_k_a',
    MODEL_TENSOR.TIME_MIX_R_K:              'blk.{bid}.time_mix_r_k',
    MODEL_TENSOR.TIME_MIX_LERP_X:           'blk.{bid}.time_mix_lerp_x',
    MODEL_TENSOR.TIME_MIX_LERP_K:           'blk.{bid}.time_mix_lerp_k',
    MODEL_TENSOR.TIME_MIX_LERP_V:           'blk.{bid}.time_mix_lerp_v',
    MODEL_TENSOR.TIME_MIX_LERP_R:           'blk.{bid}.time_mix_lerp_r',
    MODEL_TENSOR.TIME_MIX_LERP_G:           'blk.{bid}.time_mix_lerp_g',
    MODEL_TENSOR.TIME_MIX_LERP_FUSED:       'blk.{bid}.time_mix_lerp_fused',
    MODEL_TENSOR.TIME_MIX_LERP_W:           'blk.{bid}.time_mix_lerp_w',
    MODEL_TENSOR.TIME_MIX_FIRST:            'blk.{bid}.time_mix_first',
    MODEL_TENSOR.TIME_MIX_DECAY:            'blk.{bid}.time_mix_decay',
    MODEL_TENSOR.TIME_MIX_DECAY_W1:         'blk.{bid}.time_mix_decay_w1',
    MODEL_TENSOR.TIME_MIX_DECAY_W2:         'blk.{bid}.time_mix_decay_w2',
    MODEL_TENSOR.TIME_MIX_KEY:              'blk.{bid}.time_mix_key',
    MODEL_TENSOR.TIME_MIX_VALUE:            'blk.{bid}.time_mix_value',
    MODEL_TENSOR.TIME_MIX_RECEPTANCE:       'blk.{bid}.time_mix_receptance',
    MODEL_TENSOR.TIME_MIX_GATE:             'blk.{bid}.time_mix_gate',
    MODEL_TENSOR.TIME_MIX_LN:               'blk.{bid}.time_mix_ln',
    MODEL_TENSOR.TIME_MIX_OUTPUT:           'blk.{bid}.time_mix_output',
    MODEL_TENSOR.CHANNEL_MIX_LERP_K:        'blk.{bid}.channel_mix_lerp_k',
    MODEL_TENSOR.CHANNEL_MIX_LERP_R:        'blk.{bid}.channel_mix_lerp_r',
    MODEL_TENSOR.CHANNEL_MIX_KEY:           'blk.{bid}.channel_mix_key',
    MODEL_TENSOR.CHANNEL_MIX_RECEPTANCE:    'blk.{bid}.channel_mix_receptance',
    MODEL_TENSOR.CHANNEL_MIX_VALUE:         'blk.{bid}.channel_mix_value',
    MODEL_TENSOR.ATTN_Q_A:                  'blk.{bid}.attn_q_a',
    MODEL_TENSOR.ATTN_Q_B:                  'blk.{bid}.attn_q_b',
    MODEL_TENSOR.ATTN_KV_A_MQA:             'blk.{bid}.attn_kv_a_mqa',
    MODEL_TENSOR.ATTN_KV_B:                 'blk.{bid}.attn_kv_b',
    MODEL_TENSOR.ATTN_K_B:                  'blk.{bid}.attn_k_b',
    MODEL_TENSOR.ATTN_V_B:                  'blk.{bid}.attn_v_b',
    MODEL_TENSOR.ATTN_Q_A_NORM:             'blk.{bid}.attn_q_a_norm',
    MODEL_TENSOR.ATTN_KV_A_NORM:            'blk.{bid}.attn_kv_a_norm',
    MODEL_TENSOR.ATTN_SUB_NORM:             'blk.{bid}.attn_sub_norm',
    MODEL_TENSOR.FFN_SUB_NORM:              'blk.{bid}.ffn_sub_norm',
    MODEL_TENSOR.DEC_ATTN_NORM:             'dec.blk.{bid}.attn_norm',
    MODEL_TENSOR.DEC_ATTN_Q:                'dec.blk.{bid}.attn_q',
    MODEL_TENSOR.DEC_ATTN_K:                'dec.blk.{bid}.attn_k',
    MODEL_TENSOR.DEC_ATTN_V:                'dec.blk.{bid}.attn_v',
    MODEL_TENSOR.DEC_ATTN_OUT:              'dec.blk.{bid}.attn_o',
    MODEL_TENSOR.DEC_ATTN_REL_B:            'dec.blk.{bid}.attn_rel_b',
    MODEL_TENSOR.DEC_CROSS_ATTN_NORM:       'dec.blk.{bid}.cross_attn_norm',
    MODEL_TENSOR.DEC_CROSS_ATTN_Q:          'dec.blk.{bid}.cross_attn_q',
    MODEL_TENSOR.DEC_CROSS_ATTN_K:          'dec.blk.{bid}.cross_attn_k',
    MODEL_TENSOR.DEC_CROSS_ATTN_V:          'dec.blk.{bid}.cross_attn_v',
    MODEL_TENSOR.DEC_CROSS_ATTN_OUT:        'dec.blk.{bid}.cross_attn_o',
    MODEL_TENSOR.DEC_CROSS_ATTN_REL_B:      'dec.blk.{bid}.cross_attn_rel_b',
    MODEL_TENSOR.DEC_FFN_NORM:              'dec.blk.{bid}.ffn_norm',
    MODEL_TENSOR.DEC_FFN_GATE:              'dec.blk.{bid}.ffn_gate',
    MODEL_TENSOR.DEC_FFN_DOWN:              'dec.blk.{bid}.ffn_down',
    MODEL_TENSOR.DEC_FFN_UP:                'dec.blk.{bid}.ffn_up',
    MODEL_TENSOR.DEC_OUTPUT_NORM:           'dec.output_norm',
    MODEL_TENSOR.ENC_ATTN_NORM:             'enc.blk.{bid}.attn_norm',
    MODEL_TENSOR.ENC_ATTN_Q:                'enc.blk.{bid}.attn_q',
    MODEL_TENSOR.ENC_ATTN_K:                'enc.blk.{bid}.attn_k',
    MODEL_TENSOR.ENC_ATTN_V:                'enc.blk.{bid}.attn_v',
    MODEL_TENSOR.ENC_ATTN_OUT:              'enc.blk.{bid}.attn_o',
    MODEL_TENSOR.ENC_ATTN_REL_B:            'enc.blk.{bid}.attn_rel_b',
    MODEL_TENSOR.ENC_FFN_NORM:              'enc.blk.{bid}.ffn_norm',
    MODEL_TENSOR.ENC_FFN_GATE:              'enc.blk.{bid}.ffn_gate',
    MODEL_TENSOR.ENC_FFN_DOWN:              'enc.blk.{bid}.ffn_down',
    MODEL_TENSOR.ENC_FFN_UP:                'enc.blk.{bid}.ffn_up',
    MODEL_TENSOR.ENC_OUTPUT_NORM:           'enc.output_norm',
    MODEL_TENSOR.CLS:                       'cls',
    MODEL_TENSOR.CLS_OUT:                   'cls.output',
    MODEL_TENSOR.CLS_NORM:                  'cls.norm',
    MODEL_TENSOR.CONV1D:                    'conv1d',
    MODEL_TENSOR.CONVNEXT_DW:               'convnext.{bid}.dw',
    MODEL_TENSOR.CONVNEXT_NORM:             'convnext.{bid}.norm',
    MODEL_TENSOR.CONVNEXT_PW1:              'convnext.{bid}.pw1',
    MODEL_TENSOR.CONVNEXT_PW2:              'convnext.{bid}.pw2',
    MODEL_TENSOR.CONVNEXT_GAMMA:            'convnext.{bid}.gamma',
    MODEL_TENSOR.POSNET_CONV1:              'posnet.{bid}.conv1',
    MODEL_TENSOR.POSNET_CONV2:              'posnet.{bid}.conv2',
    MODEL_TENSOR.POSNET_NORM:               'posnet.{bid}.norm',
    MODEL_TENSOR.POSNET_NORM1:              'posnet.{bid}.norm1',
    MODEL_TENSOR.POSNET_NORM2:              'posnet.{bid}.norm2',
    MODEL_TENSOR.POSNET_ATTN_NORM:          'posnet.{bid}.attn_norm',
    MODEL_TENSOR.POSNET_ATTN_Q:             'posnet.{bid}.attn_q',
    MODEL_TENSOR.POSNET_ATTN_K:             'posnet.{bid}.attn_k',
    MODEL_TENSOR.POSNET_ATTN_V:             'posnet.{bid}.attn_v',
    MODEL_TENSOR.POSNET_ATTN_OUT:           'posnet.{bid}.attn_output',
    MODEL_TENSOR.SHORTCONV_CONV:            'blk.{bid}.shortconv.conv',
    MODEL_TENSOR.SHORTCONV_INPROJ:          'blk.{bid}.shortconv.in_proj',
    MODEL_TENSOR.SHORTCONV_OUTPROJ:         'blk.{bid}.shortconv.out_proj',
    MODEL_TENSOR.VISEXP_ATTN_QKV:           'blk.{bid}.vis_attn_qkv',
    MODEL_TENSOR.VISEXP_ATTN_OUT:           'blk.{bid}.vis_attn_output',
    MODEL_TENSOR.VISEXP_GATE:               'blk.{bid}.vis_gate',
    MODEL_TENSOR.VISEXP_DOWN:               'blk.{bid}.vis_down',
    MODEL_TENSOR.VISEXP_UP:                 'blk.{bid}.vis_up',
    MODEL_TENSOR.INDEXER_K_NORM:            'blk.{bid}.indexer.k_norm',
    MODEL_TENSOR.INDEXER_PROJ:              'blk.{bid}.indexer.proj',
    MODEL_TENSOR.INDEXER_ATTN_K:            'blk.{bid}.indexer.attn_k',
    MODEL_TENSOR.INDEXER_ATTN_Q_B:          'blk.{bid}.indexer.attn_q_b',
    # vision
    MODEL_TENSOR.V_MMPROJ:                  'mm.{bid}',
    MODEL_TENSOR.V_MMPROJ_FC:               'mm.model.fc',
    MODEL_TENSOR.V_MMPROJ_MLP:              'mm.model.mlp.{bid}',
    MODEL_TENSOR.V_MMPROJ_PEG:              'mm.model.peg.{bid}',
    MODEL_TENSOR.V_ENC_EMBD_CLS:            'v.class_embd',
    MODEL_TENSOR.V_ENC_EMBD_PATCH:          'v.patch_embd',
    MODEL_TENSOR.V_ENC_EMBD_NORM:           'v.norm_embd',
    MODEL_TENSOR.V_ENC_EMBD_POS:            'v.position_embd',
    MODEL_TENSOR.V_ENC_ATTN_QKV:            'v.blk.{bid}.attn_qkv',
    MODEL_TENSOR.V_ENC_ATTN_Q:              'v.blk.{bid}.attn_q',
    MODEL_TENSOR.V_ENC_ATTN_Q_NORM:         'v.blk.{bid}.attn_q_norm',
    MODEL_TENSOR.V_ENC_ATTN_K:              'v.blk.{bid}.attn_k',
    MODEL_TENSOR.V_ENC_ATTN_K_NORM:         'v.blk.{bid}.attn_k_norm',
    MODEL_TENSOR.V_ENC_ATTN_V:              'v.blk.{bid}.attn_v',
    MODEL_TENSOR.V_ENC_INPUT_NORM:          'v.blk.{bid}.ln1',
    MODEL_TENSOR.V_ENC_ATTN_O:              'v.blk.{bid}.attn_out',
    MODEL_TENSOR.V_ENC_ATTN_O_NORM:         'v.blk.{bid}.attn_out_norm',
    MODEL_TENSOR.V_ENC_POST_ATTN_NORM:      'v.blk.{bid}.ln2',
    MODEL_TENSOR.V_ENC_FFN_UP:              'v.blk.{bid}.ffn_up',
    MODEL_TENSOR.V_ENC_FFN_GATE:            'v.blk.{bid}.ffn_gate',
    MODEL_TENSOR.V_ENC_FFN_DOWN:            'v.blk.{bid}.ffn_down',
    MODEL_TENSOR.V_ENC_ATTN_POST_NORM:      'v.blk.{bid}.attn_post_norm',
    MODEL_TENSOR.V_ENC_FFN_POST_NORM:       'v.blk.{bid}.ffn_post_norm',
    MODEL_TENSOR.V_LAYER_SCALE_1:           'v.blk.{bid}.ls1',
    MODEL_TENSOR.V_LAYER_SCALE_2:           'v.blk.{bid}.ls2',
    MODEL_TENSOR.V_LAYER_OUT_SCALE:         'v.blk.{bid}.out_scale',
    MODEL_TENSOR.V_PRE_NORM:                'v.pre_ln',
    MODEL_TENSOR.V_POST_NORM:               'v.post_ln',
    MODEL_TENSOR.V_MM_POST_NORM:            'mm.post_norm',
    MODEL_TENSOR.V_MM_INP_PROJ:             'mm.input_projection',
    MODEL_TENSOR.V_MM_INP_NORM:             'mm.input_norm',
    MODEL_TENSOR.V_MM_SOFT_EMB_NORM:        'mm.soft_emb_norm',         # gemma3n
    MODEL_TENSOR.V_MM_EMBEDDING:            'mm.embedding',             # gemma3n
    MODEL_TENSOR.V_MM_HARD_EMB_NORM:        'mm.hard_emb_norm',         # gemma3n
    MODEL_TENSOR.V_ENC_CONV_STEM:           'v.conv_stem.conv',         # gemma3n
    MODEL_TENSOR.V_ENC_CONV_STEM_NORM:      'v.conv_stem.bn',           # gemma3n
    MODEL_TENSOR.V_ENC_MSFA_EXP:            'v.msfa.ffn.pw_exp.conv',   # gemma3n
    MODEL_TENSOR.V_ENC_MSFA_EXP_NORM:       'v.msfa.ffn.pw_exp.bn',     # gemma3n
    MODEL_TENSOR.V_ENC_MSFA_PROJ:           'v.msfa.ffn.pw_proj.conv',  # gemma3n
    MODEL_TENSOR.V_ENC_MSFA_PROJ_NORM:      'v.msfa.ffn.pw_proj.bn',    # gemma3n
    MODEL_TENSOR.V_ENC_MSFA_NORM:           'v.msfa.norm',              # gemma3n
    MODEL_TENSOR.V_RESMPL_POS_EMBD_K:       'resampler.pos_embd_k',
    MODEL_TENSOR.V_RESMPL_ATTN_Q:           'resampler.attn.q',
    MODEL_TENSOR.V_RESMPL_ATTN_K:           'resampler.attn.k',
    MODEL_TENSOR.V_RESMPL_ATTN_V:           'resampler.attn.v',
    MODEL_TENSOR.V_RESMPL_ATTN_OUT:         'resampler.attn.out',
    MODEL_TENSOR.V_RESMPL_KV:               'resampler.kv',
    MODEL_TENSOR.V_RESMPL_KV_NORM:          'resampler.ln_kv',
    MODEL_TENSOR.V_RESMPL_POST_NORM:        'resampler.ln_post',
    MODEL_TENSOR.V_RESMPL_Q_NORM:           'resampler.ln_q',
    MODEL_TENSOR.V_RESMPL_PROJ:             'resampler.proj',
    MODEL_TENSOR.V_RESMPL_QUERY:            'resampler.query',
    MODEL_TENSOR.V_TOK_EMBD_IMG_BREAK:      'v.token_embd.img_break', # pixtral
    MODEL_TENSOR.V_MM_PATCH_MERGER:         'mm.patch_merger', # mistral small 3.1
    MODEL_TENSOR.V_DS_NORM:                 'v.deepstack.{bid}.norm',
    MODEL_TENSOR.V_DS_FC1:                  'v.deepstack.{bid}.fc1',
    MODEL_TENSOR.V_DS_FC2:                  'v.deepstack.{bid}.fc2',
    MODEL_TENSOR.V_MM_POST_FC_NORM:         'mm.post_fc_norm', # cogvlm
    MODEL_TENSOR.V_MM_UP:                   'mm.up',
    MODEL_TENSOR.V_MM_DOWN:                 'mm.down',
    MODEL_TENSOR.V_MM_GATE:                 'mm.gate',
    MODEL_TENSOR.V_TOK_BOI:                 'v.boi',
    MODEL_TENSOR.V_TOK_EOI:                 'v.eoi',
    MODEL_TENSOR.V_MM_PRE_NORM:             'mm.pre_norm',
    MODEL_TENSOR.V_TOK_IMG_BEGIN:           'mm.image_begin',
    MODEL_TENSOR.V_TOK_IMG_END:             'mm.image_end',
    MODEL_TENSOR.V_STD_BIAS:                'v.std_bias', # gemma4
    MODEL_TENSOR.V_STD_SCALE:               'v.std_scale', # gemma4
    # DeepSeek-OCR SAM
    MODEL_TENSOR.V_SAM_POS_EMBD:            'v.sam.pos_embd',
    MODEL_TENSOR.V_SAM_PATCH_EMBD:          'v.sam.patch_embd',
    MODEL_TENSOR.V_SAM_PRE_NORM:            'v.sam.blk.{bid}.pre_ln',
    MODEL_TENSOR.V_SAM_POST_NORM:           'v.sam.blk.{bid}.post_ln',
    MODEL_TENSOR.V_SAM_ATTN_POS_H:          'v.sam.blk.{bid}.attn.pos_h',
    MODEL_TENSOR.V_SAM_ATTN_POS_W:          'v.sam.blk.{bid}.attn.pos_w',
    MODEL_TENSOR.V_SAM_ATTN_QKV:            'v.sam.blk.{bid}.attn.qkv',
    MODEL_TENSOR.V_SAM_ATTN_OUT:            'v.sam.blk.{bid}.attn.out',
    MODEL_TENSOR.V_SAM_MLP_LIN_1:           'v.sam.blk.{bid}.mlp.lin1',
    MODEL_TENSOR.V_SAM_MLP_LIN_2:           'v.sam.blk.{bid}.mlp.lin2',
    MODEL_TENSOR.V_SAM_NECK:                'v.sam.neck.{bid}',
    MODEL_TENSOR.V_SAM_NET_2:               'v.sam.net_2',
    MODEL_TENSOR.V_SAM_NET_3:               'v.sam.net_3',
    MODEL_TENSOR.V_ENC_EMBD_IMGNL:          'v.image_newline', # Deepseek-OCR
    MODEL_TENSOR.V_ENC_EMBD_VSEP:           'v.view_seperator', # Deepseek-OCR
    # audio (mtmd)
    # note: all audio tensor names must use prefix "a." or "mm.a."
    MODEL_TENSOR.A_ENC_EMBD_POS:            'a.position_embd',
    MODEL_TENSOR.A_ENC_EMBD_NORM:           'a.position_embd_norm',
    MODEL_TENSOR.A_ENC_EMBD_TO_LOGITS:      'a.embd_to_logits',
    MODEL_TENSOR.A_ENC_INP_PROJ:            'a.input_projection',
    MODEL_TENSOR.A_ENC_CONV1D:              'a.conv1d.{bid}',
    MODEL_TENSOR.A_ENC_CONV2D:              'a.conv2d.{bid}',
    MODEL_TENSOR.A_ENC_CONV_OUT:            'a.conv_out',
    MODEL_TENSOR.A_ENC_CONV1D_NORM:         'a.conv1d.{bid}.norm',
    MODEL_TENSOR.A_PRE_NORM:                'a.pre_ln',
    MODEL_TENSOR.A_POST_NORM:               'a.post_ln',
    MODEL_TENSOR.A_ENC_LAYER_PRE_NORM:      'a.blk.{bid}.layer_pre_norm',
    MODEL_TENSOR.A_ENC_ATTN_Q:              'a.blk.{bid}.attn_q',
    MODEL_TENSOR.A_ENC_ATTN_K:              'a.blk.{bid}.attn_k',
    MODEL_TENSOR.A_ENC_ATTN_V:              'a.blk.{bid}.attn_v',
    MODEL_TENSOR.A_ENC_ATTN_POST_NORM:      'a.blk.{bid}.attn_post_norm',
    MODEL_TENSOR.A_ENC_ATTN_PRE_NORM:       'a.blk.{bid}.attn_pre_norm',
    MODEL_TENSOR.A_ENC_ATTN_K_REL:          'a.blk.{bid}.attn_k_rel',
    MODEL_TENSOR.A_ENC_PER_DIM_SCALE:       'a.blk.{bid}.per_dim_scale',
    MODEL_TENSOR.A_ENC_INPUT_NORM:          'a.blk.{bid}.ln1',
    MODEL_TENSOR.A_ENC_OUTPUT:              'a.blk.{bid}.attn_out',
    MODEL_TENSOR.A_ENC_OUTPUT_NORM:         'a.blk.{bid}.ln2',
    MODEL_TENSOR.A_ENC_FFN_NORM:            'a.blk.{bid}.ffn_norm',
    MODEL_TENSOR.A_ENC_FFN_POST_NORM:       'a.blk.{bid}.ffn_post_norm',
    MODEL_TENSOR.A_ENC_FFN_SCALE:           'a.blk.{bid}.ffn_scale',
    MODEL_TENSOR.A_ENC_FFN_UP:              'a.blk.{bid}.ffn_up',
    MODEL_TENSOR.A_ENC_FFN_GATE:            'a.blk.{bid}.ffn_gate',
    MODEL_TENSOR.A_ENC_FFN_DOWN:            'a.blk.{bid}.ffn_down',
    MODEL_TENSOR.A_ENC_FFN_NORM_1:          'a.blk.{bid}.ffn_norm_1',
    MODEL_TENSOR.A_ENC_FFN_POST_NORM_1:     'a.blk.{bid}.ffn_post_norm_1',
    MODEL_TENSOR.A_ENC_FFN_SCALE_1:         'a.blk.{bid}.ffn_scale_1',
    MODEL_TENSOR.A_ENC_FFN_UP_1:            'a.blk.{bid}.ffn_up_1',
    MODEL_TENSOR.A_ENC_FFN_GATE_1:          'a.blk.{bid}.ffn_gate_1',
    MODEL_TENSOR.A_ENC_FFN_DOWN_1:          'a.blk.{bid}.ffn_down_1',
    MODEL_TENSOR.A_MMPROJ:                  'mm.a.mlp.{bid}',
    MODEL_TENSOR.A_MMPROJ_FC:               'mm.a.fc',
    MODEL_TENSOR.A_MM_NORM_PRE:             'mm.a.norm_pre',
    MODEL_TENSOR.A_MM_NORM_MID:             'mm.a.norm_mid',
    MODEL_TENSOR.A_MM_INP_PROJ:             'mm.a.input_projection',      # gemma3n
    MODEL_TENSOR.A_MM_SOFT_EMB_NORM:        'mm.a.soft_emb_norm',         # gemma3n
    MODEL_TENSOR.A_MM_EMBEDDING:            'mm.a.embedding',             # gemma3n
    MODEL_TENSOR.A_MM_HARD_EMB_NORM:        'mm.a.hard_emb_norm',         # gemma3n
    MODEL_TENSOR.A_PER_DIM_K_SCALE:         'a.blk.{bid}.per_dim_k_scale', # gemma4
    MODEL_TENSOR.A_PER_DIM_SCALE:           'a.blk.{bid}.per_dim_scale',   # gemma4
    # lfm2 audio
    MODEL_TENSOR.A_ENC_NORM_CONV:           'a.blk.{bid}.norm_conv',
    MODEL_TENSOR.A_ENC_LINEAR_POS:          'a.blk.{bid}.linear_pos',
    MODEL_TENSOR.A_ENC_POS_BIAS_U:          'a.blk.{bid}.pos_bias_u',
    MODEL_TENSOR.A_ENC_POS_BIAS_V:          'a.blk.{bid}.pos_bias_v',
    MODEL_TENSOR.A_ENC_OUT:                 'a.pre_encode.out',
    MODEL_TENSOR.A_ENC_CONV_DW:             'a.blk.{bid}.conv_dw',
    MODEL_TENSOR.A_ENC_CONV_NORM:           'a.blk.{bid}.conv_norm',
    MODEL_TENSOR.A_ENC_CONV_PW1:            'a.blk.{bid}.conv_pw1',
    MODEL_TENSOR.A_ENC_CONV_PW2:            'a.blk.{bid}.conv_pw2',
    MODEL_TENSOR.A_CTC_OUT:                 'a.enc_ctc_out',
    MODEL_TENSOR.A_CTC_OUT_MID:             'a.enc_ctc_out_mid',
    MODEL_TENSOR.A_ENC_ATTN_REL_POS_EMB:    'a.blk.{bid}.attn_rel_pos_emb',
    # qformer projector
    MODEL_TENSOR.A_QF_PROJ_QUERY:           'a.proj_query',
    MODEL_TENSOR.A_QF_PROJ_NORM:            'a.proj_norm',
    MODEL_TENSOR.A_QF_PROJ_LINEAR:          'a.proj_linear',
    MODEL_TENSOR.A_QF_SELF_ATTN_Q:          'a.proj_blk.{bid}.self_attn_q',
    MODEL_TENSOR.A_QF_SELF_ATTN_K:          'a.proj_blk.{bid}.self_attn_k',
    MODEL_TENSOR.A_QF_SELF_ATTN_V:          'a.proj_blk.{bid}.self_attn_v',
    MODEL_TENSOR.A_QF_SELF_ATTN_O:          'a.proj_blk.{bid}.self_attn_out',
    MODEL_TENSOR.A_QF_SELF_ATTN_NORM:       'a.proj_blk.{bid}.self_attn_norm',
    MODEL_TENSOR.A_QF_CROSS_ATTN_Q:         'a.proj_blk.{bid}.cross_attn_q',
    MODEL_TENSOR.A_QF_CROSS_ATTN_K:         'a.proj_blk.{bid}.cross_attn_k',
    MODEL_TENSOR.A_QF_CROSS_ATTN_V:         'a.proj_blk.{bid}.cross_attn_v',
    MODEL_TENSOR.A_QF_CROSS_ATTN_O:         'a.proj_blk.{bid}.cross_attn_out',
    MODEL_TENSOR.A_QF_CROSS_ATTN_NORM:      'a.proj_blk.{bid}.cross_attn_norm',
    MODEL_TENSOR.A_QF_FFN_UP:               'a.proj_blk.{bid}.ffn_up',
    MODEL_TENSOR.A_QF_FFN_DOWN:             'a.proj_blk.{bid}.ffn_down',
    MODEL_TENSOR.A_QF_FFN_NORM:             'a.proj_blk.{bid}.ffn_norm',
    # NextN/MTP
    MODEL_TENSOR.NEXTN_EH_PROJ:             'blk.{bid}.nextn.eh_proj',
    MODEL_TENSOR.NEXTN_EMBED_TOKENS:        'blk.{bid}.nextn.embed_tokens',
    MODEL_TENSOR.NEXTN_ENORM:               'blk.{bid}.nextn.enorm',
    MODEL_TENSOR.NEXTN_HNORM:               'blk.{bid}.nextn.hnorm',
    MODEL_TENSOR.NEXTN_SHARED_HEAD_HEAD:    'blk.{bid}.nextn.shared_head_head',
    MODEL_TENSOR.NEXTN_SHARED_HEAD_NORM:    'blk.{bid}.nextn.shared_head_norm',
}

MODEL_TENSORS: dict[MODEL_ARCH, list[MODEL_TENSOR]] = {
    MODEL_ARCH.MMPROJ: [
        MODEL_TENSOR.V_MMPROJ,
        MODEL_TENSOR.V_MMPROJ_FC,
        MODEL_TENSOR.V_MMPROJ_MLP,
        MODEL_TENSOR.V_MMPROJ_PEG,
        MODEL_TENSOR.V_ENC_EMBD_CLS,
        MODEL_TENSOR.V_ENC_EMBD_PATCH,
        MODEL_TENSOR.V_ENC_EMBD_NORM,
        MODEL_TENSOR.V_ENC_EMBD_POS,
        MODEL_TENSOR.V_ENC_EMBD_IMGNL,
        MODEL_TENSOR.V_ENC_EMBD_VSEP,
        MODEL_TENSOR.V_ENC_INPUT_NORM,
        MODEL_TENSOR.V_ENC_ATTN_QKV,
        MODEL_TENSOR.V_ENC_ATTN_Q,
        MODEL_TENSOR.V_ENC_ATTN_Q_NORM,
        MODEL_TENSOR.V_ENC_ATTN_K,
        MODEL_TENSOR.V_ENC_ATTN_K_NORM,
        MODEL_TENSOR.V_ENC_ATTN_V,
        MODEL_TENSOR.V_ENC_ATTN_O,
        MODEL_TENSOR.V_ENC_ATTN_O_NORM,
        MODEL_TENSOR.V_ENC_POST_ATTN_NORM,
        MODEL_TENSOR.V_ENC_FFN_UP,
        MODEL_TENSOR.V_ENC_FFN_GATE,
        MODEL_TENSOR.V_ENC_FFN_DOWN,
        MODEL_TENSOR.V_ENC_ATTN_POST_NORM,
        MODEL_TENSOR.V_ENC_FFN_POST_NORM,
        MODEL_TENSOR.V_LAYER_SCALE_1,
        MODEL_TENSOR.V_LAYER_SCALE_2,
        MODEL_TENSOR.V_LAYER_OUT_SCALE,
        MODEL_TENSOR.V_PRE_NORM,
        MODEL_TENSOR.V_POST_NORM,
        MODEL_TENSOR.V_MM_POST_NORM,
        MODEL_TENSOR.V_MM_INP_PROJ,
        MODEL_TENSOR.V_MM_INP_NORM,
        MODEL_TENSOR.V_MM_SOFT_EMB_NORM,
        MODEL_TENSOR.V_MM_EMBEDDING,
        MODEL_TENSOR.V_MM_HARD_EMB_NORM,
        MODEL_TENSOR.V_ENC_CONV_STEM,
        MODEL_TENSOR.V_ENC_CONV_STEM_NORM,
        MODEL_TENSOR.V_ENC_MSFA_EXP,
        MODEL_TENSOR.V_ENC_MSFA_EXP_NORM,
        MODEL_TENSOR.V_ENC_MSFA_PROJ,
        MODEL_TENSOR.V_ENC_MSFA_PROJ_NORM,
        MODEL_TENSOR.V_ENC_MSFA_NORM,
        MODEL_TENSOR.V_RESMPL_POS_EMBD_K,
        MODEL_TENSOR.V_RESMPL_ATTN_Q,
        MODEL_TENSOR.V_RESMPL_ATTN_K,
        MODEL_TENSOR.V_RESMPL_ATTN_V,
        MODEL_TENSOR.V_RESMPL_ATTN_OUT,
        MODEL_TENSOR.V_RESMPL_KV,
        MODEL_TENSOR.V_RESMPL_KV_NORM,
        MODEL_TENSOR.V_RESMPL_POST_NORM,
        MODEL_TENSOR.V_RESMPL_Q_NORM,
        MODEL_TENSOR.V_RESMPL_PROJ,
        MODEL_TENSOR.V_RESMPL_QUERY,
        MODEL_TENSOR.V_TOK_EMBD_IMG_BREAK,
        MODEL_TENSOR.V_MM_PATCH_MERGER,
        MODEL_TENSOR.V_DS_NORM,
        MODEL_TENSOR.V_DS_FC1,
        MODEL_TENSOR.V_DS_FC2,
        MODEL_TENSOR.V_MM_POST_FC_NORM,
        MODEL_TENSOR.V_MM_UP,
        MODEL_TENSOR.V_MM_DOWN,
        MODEL_TENSOR.V_MM_GATE,
        MODEL_TENSOR.V_TOK_BOI,
        MODEL_TENSOR.V_TOK_EOI,
        MODEL_TENSOR.V_MM_PRE_NORM,
        MODEL_TENSOR.V_TOK_IMG_BEGIN,
        MODEL_TENSOR.V_TOK_IMG_END,
        MODEL_TENSOR.V_STD_BIAS,
        MODEL_TENSOR.V_STD_SCALE,
        MODEL_TENSOR.V_SAM_POS_EMBD,
        MODEL_TENSOR.V_SAM_PATCH_EMBD,
        MODEL_TENSOR.V_SAM_PRE_NORM,
        MODEL_TENSOR.V_SAM_POST_NORM,
        MODEL_TENSOR.V_SAM_ATTN_POS_H,
        MODEL_TENSOR.V_SAM_ATTN_POS_W,
        MODEL_TENSOR.V_SAM_ATTN_QKV,
        MODEL_TENSOR.V_SAM_ATTN_OUT,
        MODEL_TENSOR.V_SAM_MLP_LIN_1,
        MODEL_TENSOR.V_SAM_MLP_LIN_2,
        MODEL_TENSOR.V_SAM_NECK,
        MODEL_TENSOR.V_SAM_NET_2,
        MODEL_TENSOR.V_SAM_NET_3,
        # audio
        MODEL_TENSOR.A_ENC_EMBD_POS,
        MODEL_TENSOR.A_ENC_EMBD_NORM,
        MODEL_TENSOR.A_ENC_EMBD_TO_LOGITS,
        MODEL_TENSOR.A_ENC_INP_PROJ,
        MODEL_TENSOR.A_ENC_CONV1D,
        MODEL_TENSOR.A_ENC_CONV2D,
        MODEL_TENSOR.A_ENC_CONV_OUT,
        MODEL_TENSOR.A_ENC_CONV1D_NORM,
        MODEL_TENSOR.A_PRE_NORM,
        MODEL_TENSOR.A_POST_NORM,
        MODEL_TENSOR.A_ENC_LAYER_PRE_NORM,
        MODEL_TENSOR.A_ENC_ATTN_Q,
        MODEL_TENSOR.A_ENC_ATTN_K,
        MODEL_TENSOR.A_ENC_ATTN_V,
        MODEL_TENSOR.A_ENC_ATTN_POST_NORM,
        MODEL_TENSOR.A_ENC_ATTN_PRE_NORM,
        MODEL_TENSOR.A_ENC_ATTN_K_REL,
        MODEL_TENSOR.A_ENC_PER_DIM_SCALE,
        MODEL_TENSOR.A_ENC_INPUT_NORM,
        MODEL_TENSOR.A_ENC_OUTPUT,
        MODEL_TENSOR.A_ENC_OUTPUT_NORM,
        MODEL_TENSOR.A_ENC_FFN_NORM,
        MODEL_TENSOR.A_ENC_FFN_POST_NORM,
        MODEL_TENSOR.A_ENC_FFN_SCALE,
        MODEL_TENSOR.A_ENC_FFN_UP,
        MODEL_TENSOR.A_ENC_FFN_GATE,
        MODEL_TENSOR.A_ENC_FFN_DOWN,
        MODEL_TENSOR.A_ENC_FFN_NORM_1,
        MODEL_TENSOR.A_ENC_FFN_POST_NORM_1,
        MODEL_TENSOR.A_ENC_FFN_SCALE_1,
        MODEL_TENSOR.A_ENC_FFN_UP_1,
        MODEL_TENSOR.A_ENC_FFN_GATE_1,
        MODEL_TENSOR.A_ENC_FFN_DOWN_1,
        MODEL_TENSOR.A_MMPROJ,
        MODEL_TENSOR.A_MMPROJ_FC,
        MODEL_TENSOR.A_MM_NORM_PRE,
        MODEL_TENSOR.A_MM_NORM_MID,
        MODEL_TENSOR.A_ENC_NORM_CONV,
        MODEL_TENSOR.A_ENC_LINEAR_POS,
        MODEL_TENSOR.A_ENC_POS_BIAS_U,
        MODEL_TENSOR.A_ENC_POS_BIAS_V,
        MODEL_TENSOR.A_ENC_OUT,
        MODEL_TENSOR.A_ENC_CONV_DW,
        MODEL_TENSOR.A_ENC_CONV_NORM,
        MODEL_TENSOR.A_ENC_CONV_PW1,
        MODEL_TENSOR.A_ENC_CONV_PW2,
        MODEL_TENSOR.A_MM_INP_PROJ,
        MODEL_TENSOR.A_MM_SOFT_EMB_NORM,
        MODEL_TENSOR.A_MM_EMBEDDING,
        MODEL_TENSOR.A_MM_HARD_EMB_NORM,
        MODEL_TENSOR.A_PER_DIM_K_SCALE,
        MODEL_TENSOR.A_PER_DIM_SCALE,
        MODEL_TENSOR.A_CTC_OUT,
        MODEL_TENSOR.A_CTC_OUT_MID,
        MODEL_TENSOR.A_ENC_ATTN_REL_POS_EMB,
        # qformer projector
        MODEL_TENSOR.A_QF_PROJ_QUERY,
        MODEL_TENSOR.A_QF_PROJ_NORM,
        MODEL_TENSOR.A_QF_PROJ_LINEAR,
        MODEL_TENSOR.A_QF_SELF_ATTN_Q,
        MODEL_TENSOR.A_QF_SELF_ATTN_K,
        MODEL_TENSOR.A_QF_SELF_ATTN_V,
        MODEL_TENSOR.A_QF_SELF_ATTN_O,
        MODEL_TENSOR.A_QF_SELF_ATTN_NORM,
        MODEL_TENSOR.A_QF_CROSS_ATTN_Q,
        MODEL_TENSOR.A_QF_CROSS_ATTN_K,
        MODEL_TENSOR.A_QF_CROSS_ATTN_V,
        MODEL_TENSOR.A_QF_CROSS_ATTN_O,
        MODEL_TENSOR.A_QF_CROSS_ATTN_NORM,
        MODEL_TENSOR.A_QF_FFN_UP,
        MODEL_TENSOR.A_QF_FFN_DOWN,
        MODEL_TENSOR.A_QF_FFN_NORM,
    ],
    MODEL_ARCH.LLAMA: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
    ],
    MODEL_ARCH.LLAMA4: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_GATE_SHEXP,
        MODEL_TENSOR.FFN_DOWN_SHEXP,
        MODEL_TENSOR.FFN_UP_SHEXP,
    ],
    MODEL_ARCH.DECI: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
    ],
    MODEL_ARCH.GROK: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.ATTN_OUT_NORM,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_POST_NORM,
        MODEL_TENSOR.LAYER_OUT_NORM,
    ],
    MODEL_ARCH.GPTNEOX: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.FALCON: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_NORM_2,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.BAICHUAN: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.STARCODER: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.POS_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.BERT: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.TOKEN_EMBD_NORM,
        MODEL_TENSOR.TOKEN_TYPES,
        MODEL_TENSOR.POS_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.ATTN_OUT_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.LAYER_OUT_NORM,
        MODEL_TENSOR.CLS,
        MODEL_TENSOR.CLS_OUT,
    ],
    MODEL_ARCH.MODERN_BERT: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.TOKEN_EMBD_NORM,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.CLS,
        MODEL_TENSOR.CLS_OUT,
        MODEL_TENSOR.CLS_NORM,
    ],
    MODEL_ARCH.NOMIC_BERT: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.TOKEN_EMBD_NORM,
        MODEL_TENSOR.TOKEN_TYPES,
        MODEL_TENSOR.POS_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.ATTN_OUT_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.LAYER_OUT_NORM,
    ],
    MODEL_ARCH.NOMIC_BERT_MOE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.TOKEN_EMBD_NORM,
        MODEL_TENSOR.TOKEN_TYPES,
        MODEL_TENSOR.POS_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.ATTN_OUT_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.LAYER_OUT_NORM,
    ],
    MODEL_ARCH.NEO_BERT: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.ENC_OUTPUT_NORM,
        MODEL_TENSOR.CLS,
        MODEL_TENSOR.CLS_OUT,
    ],
    MODEL_ARCH.JINA_BERT_V2: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.TOKEN_EMBD_NORM,
        MODEL_TENSOR.TOKEN_TYPES,
        MODEL_TENSOR.ATTN_NORM_2,
        MODEL_TENSOR.ATTN_OUT_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.LAYER_OUT_NORM,
        MODEL_TENSOR.CLS,
    ],
    MODEL_ARCH.JINA_BERT_V3: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.TOKEN_EMBD_NORM,
        MODEL_TENSOR.TOKEN_TYPES,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.ATTN_OUT_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.LAYER_OUT_NORM,
    ],
    MODEL_ARCH.EUROBERT: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_DOWN,
    ],
    MODEL_ARCH.MPT: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_ACT,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.POS_EMBD,
    ],
    MODEL_ARCH.GPTJ: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.REFACT: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.BLOOM: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.TOKEN_EMBD_NORM,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.STABLELM: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K_NORM,
    ],
    MODEL_ARCH.QWEN: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.QWEN2: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.DREAM: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.LLADA: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.QWEN2VL: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.QWEN2MOE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_GATE_INP_SHEXP,
        MODEL_TENSOR.FFN_GATE_SHEXP,
        MODEL_TENSOR.FFN_DOWN_SHEXP,
        MODEL_TENSOR.FFN_UP_SHEXP,
    ],
    MODEL_ARCH.QWEN3: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.QWEN3MOE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
    ],
    MODEL_ARCH.QWEN3NEXT: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_POST_NORM,
        MODEL_TENSOR.ATTN_GATE,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_INP_SHEXP,
        MODEL_TENSOR.FFN_UP_SHEXP,
        MODEL_TENSOR.FFN_DOWN_SHEXP,
        MODEL_TENSOR.FFN_GATE_SHEXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_GATE_UP_EXP,
        MODEL_TENSOR.SSM_A,
        MODEL_TENSOR.SSM_CONV1D,
        MODEL_TENSOR.SSM_DT,
        MODEL_TENSOR.SSM_NORM,
        MODEL_TENSOR.SSM_IN,
        MODEL_TENSOR.SSM_BETA_ALPHA,
        MODEL_TENSOR.SSM_OUT,
    ],
    MODEL_ARCH.QWEN3VL: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.QWEN3VLMOE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
    ],
    MODEL_ARCH.QWEN35: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_POST_NORM,
        MODEL_TENSOR.ATTN_GATE,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.SSM_A,
        MODEL_TENSOR.SSM_CONV1D,
        MODEL_TENSOR.SSM_DT,
        MODEL_TENSOR.SSM_NORM,
        MODEL_TENSOR.SSM_BETA,
        MODEL_TENSOR.SSM_ALPHA,
        MODEL_TENSOR.SSM_OUT,
    ],
    MODEL_ARCH.QWEN35MOE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_POST_NORM,
        MODEL_TENSOR.ATTN_GATE,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_INP_SHEXP,
        MODEL_TENSOR.FFN_UP_SHEXP,
        MODEL_TENSOR.FFN_DOWN_SHEXP,
        MODEL_TENSOR.FFN_GATE_SHEXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_GATE_UP_EXP,
        MODEL_TENSOR.SSM_A,
        MODEL_TENSOR.SSM_CONV1D,
        MODEL_TENSOR.SSM_DT,
        MODEL_TENSOR.SSM_NORM,
        MODEL_TENSOR.SSM_BETA,
        MODEL_TENSOR.SSM_ALPHA,
        MODEL_TENSOR.SSM_OUT,
    ],
    MODEL_ARCH.PLAMO: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.PLAMO2: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_POST_NORM,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_POST_NORM,
        MODEL_TENSOR.SSM_IN,
        MODEL_TENSOR.SSM_CONV1D,
        MODEL_TENSOR.SSM_X,
        MODEL_TENSOR.SSM_DT,
        MODEL_TENSOR.SSM_A,
        MODEL_TENSOR.SSM_D,
        MODEL_TENSOR.SSM_OUT,
        MODEL_TENSOR.SSM_DT_NORM,
        MODEL_TENSOR.SSM_B_NORM,
        MODEL_TENSOR.SSM_C_NORM,
    ],
    MODEL_ARCH.PLAMO3: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_POST_NORM,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_POST_NORM,
    ],
    MODEL_ARCH.GPT2: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.POS_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.PHI2: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.PHI3: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FACTORS_LONG,
        MODEL_TENSOR.ROPE_FACTORS_SHORT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.PHIMOE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FACTORS_LONG,
        MODEL_TENSOR.ROPE_FACTORS_SHORT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
    ],
    MODEL_ARCH.CODESHELL: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.POS_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.ORION: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.INTERNLM2: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.MINICPM: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ROPE_FACTORS_LONG,
        MODEL_TENSOR.ROPE_FACTORS_SHORT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
    ],
    MODEL_ARCH.MINICPM3: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FACTORS_LONG,
        MODEL_TENSOR.ROPE_FACTORS_SHORT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q_A,
        MODEL_TENSOR.ATTN_Q_B,
        MODEL_TENSOR.ATTN_KV_A_MQA,
        MODEL_TENSOR.ATTN_KV_B,
        MODEL_TENSOR.ATTN_Q_A_NORM,
        MODEL_TENSOR.ATTN_KV_A_NORM,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.GEMMA: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_NORM,
    ],
    MODEL_ARCH.GEMMA2: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_POST_NORM,
        MODEL_TENSOR.FFN_PRE_NORM,
        MODEL_TENSOR.FFN_POST_NORM,
    ],
    MODEL_ARCH.GEMMA3: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_POST_NORM,
        MODEL_TENSOR.FFN_PRE_NORM,
        MODEL_TENSOR.FFN_POST_NORM,
    ],
    MODEL_ARCH.GEMMA3N: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_POST_NORM,
        MODEL_TENSOR.FFN_PRE_NORM,
        MODEL_TENSOR.FFN_POST_NORM,
        # altup / laurel
        MODEL_TENSOR.PER_LAYER_TOKEN_EMBD,
        MODEL_TENSOR.PER_LAYER_MODEL_PROJ,
        MODEL_TENSOR.PER_LAYER_INP_GATE,
        MODEL_TENSOR.PER_LAYER_PROJ,
        MODEL_TENSOR.PER_LAYER_PROJ_NORM,
        MODEL_TENSOR.PER_LAYER_POST_NORM,
        MODEL_TENSOR.ALTUP_PROJ,
        MODEL_TENSOR.ALTUP_UNEMBD_PROJ,
        MODEL_TENSOR.ALTUP_CORRECT_COEF,
        MODEL_TENSOR.ALTUP_CORRECT_SCALE,
        MODEL_TENSOR.ALTUP_PREDICT_COEF,
        MODEL_TENSOR.ALTUP_ROUTER,
        MODEL_TENSOR.ALTUP_ROUTER_NORM,
        MODEL_TENSOR.LAUREL_L,
        MODEL_TENSOR.LAUREL_R,
        MODEL_TENSOR.LAUREL_POST_NORM,
    ],
    MODEL_ARCH.GEMMA4: [
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_UP_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_POST_NORM,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_PRE_NORM,
        MODEL_TENSOR.FFN_PRE_NORM_2,
        MODEL_TENSOR.FFN_POST_NORM,
        MODEL_TENSOR.FFN_POST_NORM_1,
        MODEL_TENSOR.FFN_POST_NORM_2,
        MODEL_TENSOR.LAYER_OUT_SCALE,
        MODEL_TENSOR.PER_LAYER_TOKEN_EMBD,
        MODEL_TENSOR.PER_LAYER_MODEL_PROJ,
        MODEL_TENSOR.PER_LAYER_INP_GATE,
        MODEL_TENSOR.PER_LAYER_PROJ,
        MODEL_TENSOR.PER_LAYER_PROJ_NORM,
        MODEL_TENSOR.PER_LAYER_POST_NORM,
    ],
    MODEL_ARCH.GEMMA_EMBEDDING: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.DENSE_2_OUT,
        MODEL_TENSOR.DENSE_3_OUT,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_POST_NORM,
        MODEL_TENSOR.FFN_PRE_NORM,
        MODEL_TENSOR.FFN_POST_NORM,
    ],
    MODEL_ARCH.STARCODER2: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.RWKV6: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.TOKEN_EMBD_NORM,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_NORM_2,
        MODEL_TENSOR.TIME_MIX_W1,
        MODEL_TENSOR.TIME_MIX_W2,
        MODEL_TENSOR.TIME_MIX_LERP_X,
        MODEL_TENSOR.TIME_MIX_LERP_K,
        MODEL_TENSOR.TIME_MIX_LERP_V,
        MODEL_TENSOR.TIME_MIX_LERP_R,
        MODEL_TENSOR.TIME_MIX_LERP_G,
        MODEL_TENSOR.TIME_MIX_LERP_W,
        MODEL_TENSOR.TIME_MIX_LERP_FUSED,
        MODEL_TENSOR.TIME_MIX_FIRST,
        MODEL_TENSOR.TIME_MIX_DECAY,
        MODEL_TENSOR.TIME_MIX_DECAY_W1,
        MODEL_TENSOR.TIME_MIX_DECAY_W2,
        MODEL_TENSOR.TIME_MIX_KEY,
        MODEL_TENSOR.TIME_MIX_VALUE,
        MODEL_TENSOR.TIME_MIX_RECEPTANCE,
        MODEL_TENSOR.TIME_MIX_GATE,
        MODEL_TENSOR.TIME_MIX_LN,
        MODEL_TENSOR.TIME_MIX_OUTPUT,
        MODEL_TENSOR.CHANNEL_MIX_LERP_K,
        MODEL_TENSOR.CHANNEL_MIX_LERP_R,
        MODEL_TENSOR.CHANNEL_MIX_KEY,
        MODEL_TENSOR.CHANNEL_MIX_RECEPTANCE,
        MODEL_TENSOR.CHANNEL_MIX_VALUE,
    ],
    MODEL_ARCH.RWKV6QWEN2: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.TIME_MIX_W1,
        MODEL_TENSOR.TIME_MIX_W2,
        MODEL_TENSOR.TIME_MIX_LERP_X,
        MODEL_TENSOR.TIME_MIX_LERP_K,
        MODEL_TENSOR.TIME_MIX_LERP_V,
        MODEL_TENSOR.TIME_MIX_LERP_R,
        MODEL_TENSOR.TIME_MIX_LERP_G,
        MODEL_TENSOR.TIME_MIX_LERP_W,
        MODEL_TENSOR.TIME_MIX_LERP_FUSED,
        MODEL_TENSOR.TIME_MIX_FIRST,
        MODEL_TENSOR.TIME_MIX_DECAY,
        MODEL_TENSOR.TIME_MIX_DECAY_W1,
        MODEL_TENSOR.TIME_MIX_DECAY_W2,
        MODEL_TENSOR.TIME_MIX_KEY,
        MODEL_TENSOR.TIME_MIX_VALUE,
        MODEL_TENSOR.TIME_MIX_RECEPTANCE,
        MODEL_TENSOR.TIME_MIX_GATE,
        MODEL_TENSOR.TIME_MIX_LN,
        MODEL_TENSOR.TIME_MIX_OUTPUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.RWKV7: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.TOKEN_EMBD_NORM,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_NORM_2,
        MODEL_TENSOR.TIME_MIX_LERP_FUSED,
        MODEL_TENSOR.TIME_MIX_W0,
        MODEL_TENSOR.TIME_MIX_W1,
        MODEL_TENSOR.TIME_MIX_W2,
        MODEL_TENSOR.TIME_MIX_A0,
        MODEL_TENSOR.TIME_MIX_A1,
        MODEL_TENSOR.TIME_MIX_A2,
        MODEL_TENSOR.TIME_MIX_V0,
        MODEL_TENSOR.TIME_MIX_V1,
        MODEL_TENSOR.TIME_MIX_V2,
        MODEL_TENSOR.TIME_MIX_G1,
        MODEL_TENSOR.TIME_MIX_G2,
        MODEL_TENSOR.TIME_MIX_K_K,
        MODEL_TENSOR.TIME_MIX_K_A,
        MODEL_TENSOR.TIME_MIX_R_K,
        MODEL_TENSOR.TIME_MIX_KEY,
        MODEL_TENSOR.TIME_MIX_VALUE,
        MODEL_TENSOR.TIME_MIX_RECEPTANCE,
        MODEL_TENSOR.TIME_MIX_LN,
        MODEL_TENSOR.TIME_MIX_OUTPUT,
        MODEL_TENSOR.CHANNEL_MIX_LERP_K,
        MODEL_TENSOR.CHANNEL_MIX_KEY,
        MODEL_TENSOR.CHANNEL_MIX_VALUE,
    ],
    MODEL_ARCH.ARWKV7: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.TOKEN_EMBD_NORM,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.TIME_MIX_LERP_FUSED,
        MODEL_TENSOR.TIME_MIX_W0,
        MODEL_TENSOR.TIME_MIX_W1,
        MODEL_TENSOR.TIME_MIX_W2,
        MODEL_TENSOR.TIME_MIX_A0,
        MODEL_TENSOR.TIME_MIX_A1,
        MODEL_TENSOR.TIME_MIX_A2,
        MODEL_TENSOR.TIME_MIX_V0,
        MODEL_TENSOR.TIME_MIX_V1,
        MODEL_TENSOR.TIME_MIX_V2,
        MODEL_TENSOR.TIME_MIX_G1,
        MODEL_TENSOR.TIME_MIX_G2,
        MODEL_TENSOR.TIME_MIX_K_K,
        MODEL_TENSOR.TIME_MIX_K_A,
        MODEL_TENSOR.TIME_MIX_R_K,
        MODEL_TENSOR.TIME_MIX_KEY,
        MODEL_TENSOR.TIME_MIX_VALUE,
        MODEL_TENSOR.TIME_MIX_RECEPTANCE,
        MODEL_TENSOR.TIME_MIX_LN,
        MODEL_TENSOR.TIME_MIX_OUTPUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.MAMBA: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.SSM_IN,
        MODEL_TENSOR.SSM_CONV1D,
        MODEL_TENSOR.SSM_X,
        MODEL_TENSOR.SSM_DT,
        MODEL_TENSOR.SSM_A,
        MODEL_TENSOR.SSM_D,
        MODEL_TENSOR.SSM_OUT,
    ],
    MODEL_ARCH.MAMBA2: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.SSM_IN,
        MODEL_TENSOR.SSM_CONV1D,
        MODEL_TENSOR.SSM_DT,
        MODEL_TENSOR.SSM_A,
        MODEL_TENSOR.SSM_D,
        MODEL_TENSOR.SSM_NORM,
        MODEL_TENSOR.SSM_OUT,
    ],
    MODEL_ARCH.JAMBA: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.SSM_IN,
        MODEL_TENSOR.SSM_CONV1D,
        MODEL_TENSOR.SSM_X,
        MODEL_TENSOR.SSM_DT,
        MODEL_TENSOR.SSM_DT_NORM,
        MODEL_TENSOR.SSM_A,
        MODEL_TENSOR.SSM_B_NORM,
        MODEL_TENSOR.SSM_C_NORM,
        MODEL_TENSOR.SSM_D,
        MODEL_TENSOR.SSM_OUT,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
    ],
    MODEL_ARCH.XVERSE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.COMMAND_R: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_Q_NORM,
    ],
    MODEL_ARCH.COHERE2: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.DBRX: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_OUT_NORM,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
    ],
    MODEL_ARCH.OLMO: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.OLMO2: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_POST_NORM,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.FFN_POST_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.SEED_OSS: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_POST_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
    ],
    MODEL_ARCH.OLMOE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
    ],
    MODEL_ARCH.OPENELM: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.ARCTIC: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_NORM_EXP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
    ],
    MODEL_ARCH.DEEPSEEK: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_GATE_SHEXP,
        MODEL_TENSOR.FFN_DOWN_SHEXP,
        MODEL_TENSOR.FFN_UP_SHEXP,
    ],
    MODEL_ARCH.DEEPSEEK2: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_A,
        MODEL_TENSOR.ATTN_Q_B,
        MODEL_TENSOR.ATTN_KV_A_MQA,
        MODEL_TENSOR.ATTN_KV_B,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_B,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_V_B,
        MODEL_TENSOR.ATTN_Q_A_NORM,
        MODEL_TENSOR.ATTN_KV_A_NORM,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_GATE_SHEXP,
        MODEL_TENSOR.FFN_DOWN_SHEXP,
        MODEL_TENSOR.FFN_UP_SHEXP,
        MODEL_TENSOR.FFN_EXP_PROBS_B,
    ],
    MODEL_ARCH.DEEPSEEK2OCR: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_A,
        MODEL_TENSOR.ATTN_Q_B,
        MODEL_TENSOR.ATTN_KV_A_MQA,
        MODEL_TENSOR.ATTN_KV_B,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_B,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_V_B,
        MODEL_TENSOR.ATTN_Q_A_NORM,
        MODEL_TENSOR.ATTN_KV_A_NORM,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_GATE_UP_EXP,
        MODEL_TENSOR.FFN_GATE_SHEXP,
        MODEL_TENSOR.FFN_DOWN_SHEXP,
        MODEL_TENSOR.FFN_UP_SHEXP,
        MODEL_TENSOR.FFN_EXP_PROBS_B,
    ],
    MODEL_ARCH.ERNIE4_5_MOE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_GATE_SHEXP,
        MODEL_TENSOR.FFN_DOWN_SHEXP,
        MODEL_TENSOR.FFN_UP_SHEXP,
        MODEL_TENSOR.FFN_EXP_PROBS_B,
    ],
    MODEL_ARCH.PLM: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_KV_A_MQA,
        MODEL_TENSOR.ATTN_KV_A_NORM,
        MODEL_TENSOR.ATTN_KV_B,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_DOWN,
    ],
    MODEL_ARCH.CHATGLM : [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.GLM4 : [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.ATTN_POST_NORM,
        MODEL_TENSOR.FFN_POST_NORM,
        # NextN/MTP tensors - preserved but unused
        MODEL_TENSOR.NEXTN_EH_PROJ,
        MODEL_TENSOR.NEXTN_EMBED_TOKENS,
        MODEL_TENSOR.NEXTN_ENORM,
        MODEL_TENSOR.NEXTN_HNORM,
        MODEL_TENSOR.NEXTN_SHARED_HEAD_HEAD,
        MODEL_TENSOR.NEXTN_SHARED_HEAD_NORM,
    ],
    MODEL_ARCH.GLM4_MOE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_POST_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_GATE_SHEXP,
        MODEL_TENSOR.FFN_DOWN_SHEXP,
        MODEL_TENSOR.FFN_UP_SHEXP,
        MODEL_TENSOR.FFN_EXP_PROBS_B,
        # NextN/MTP tensors - preserved but unused
        MODEL_TENSOR.NEXTN_EH_PROJ,
        MODEL_TENSOR.NEXTN_EMBED_TOKENS,
        MODEL_TENSOR.NEXTN_ENORM,
        MODEL_TENSOR.NEXTN_HNORM,
        MODEL_TENSOR.NEXTN_SHARED_HEAD_HEAD,
        MODEL_TENSOR.NEXTN_SHARED_HEAD_NORM,
    ],
    MODEL_ARCH.GLM_DSA: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_A,
        MODEL_TENSOR.ATTN_Q_B,
        MODEL_TENSOR.ATTN_KV_A_MQA,
        MODEL_TENSOR.ATTN_KV_B,
        MODEL_TENSOR.ATTN_K_B,
        MODEL_TENSOR.ATTN_V_B,
        MODEL_TENSOR.ATTN_Q_A_NORM,
        MODEL_TENSOR.ATTN_KV_A_NORM,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_GATE_SHEXP,
        MODEL_TENSOR.FFN_DOWN_SHEXP,
        MODEL_TENSOR.FFN_UP_SHEXP,
        MODEL_TENSOR.FFN_EXP_PROBS_B,
        MODEL_TENSOR.INDEXER_K_NORM,
        MODEL_TENSOR.INDEXER_PROJ,
        MODEL_TENSOR.INDEXER_ATTN_K,
        MODEL_TENSOR.INDEXER_ATTN_Q_B,
        # NextN/MTP tensors - preserved but unused
        MODEL_TENSOR.NEXTN_EH_PROJ,
        MODEL_TENSOR.NEXTN_EMBED_TOKENS,
        MODEL_TENSOR.NEXTN_ENORM,
        MODEL_TENSOR.NEXTN_HNORM,
        MODEL_TENSOR.NEXTN_SHARED_HEAD_HEAD,
        MODEL_TENSOR.NEXTN_SHARED_HEAD_NORM,
    ],
    MODEL_ARCH.BITNET: [
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.ATTN_SUB_NORM,
        MODEL_TENSOR.FFN_SUB_NORM,
    ],
    MODEL_ARCH.T5: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.DEC_ATTN_NORM,
        MODEL_TENSOR.DEC_ATTN_Q,
        MODEL_TENSOR.DEC_ATTN_K,
        MODEL_TENSOR.DEC_ATTN_V,
        MODEL_TENSOR.DEC_ATTN_OUT,
        MODEL_TENSOR.DEC_ATTN_REL_B,
        MODEL_TENSOR.DEC_CROSS_ATTN_NORM,
        MODEL_TENSOR.DEC_CROSS_ATTN_Q,
        MODEL_TENSOR.DEC_CROSS_ATTN_K,
        MODEL_TENSOR.DEC_CROSS_ATTN_V,
        MODEL_TENSOR.DEC_CROSS_ATTN_OUT,
        MODEL_TENSOR.DEC_CROSS_ATTN_REL_B,
        MODEL_TENSOR.DEC_FFN_NORM,
        MODEL_TENSOR.DEC_FFN_GATE,
        MODEL_TENSOR.DEC_FFN_DOWN,
        MODEL_TENSOR.DEC_FFN_UP,
        MODEL_TENSOR.DEC_OUTPUT_NORM,
        MODEL_TENSOR.ENC_ATTN_NORM,
        MODEL_TENSOR.ENC_ATTN_Q,
        MODEL_TENSOR.ENC_ATTN_K,
        MODEL_TENSOR.ENC_ATTN_V,
        MODEL_TENSOR.ENC_ATTN_OUT,
        MODEL_TENSOR.ENC_ATTN_REL_B,
        MODEL_TENSOR.ENC_FFN_NORM,
        MODEL_TENSOR.ENC_FFN_GATE,
        MODEL_TENSOR.ENC_FFN_DOWN,
        MODEL_TENSOR.ENC_FFN_UP,
        MODEL_TENSOR.ENC_OUTPUT_NORM,
    ],
    MODEL_ARCH.T5ENCODER: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ENC_ATTN_NORM,
        MODEL_TENSOR.ENC_ATTN_Q,
        MODEL_TENSOR.ENC_ATTN_K,
        MODEL_TENSOR.ENC_ATTN_V,
        MODEL_TENSOR.ENC_ATTN_OUT,
        MODEL_TENSOR.ENC_ATTN_REL_B,
        MODEL_TENSOR.ENC_FFN_NORM,
        MODEL_TENSOR.ENC_FFN_GATE,
        MODEL_TENSOR.ENC_FFN_DOWN,
        MODEL_TENSOR.ENC_FFN_UP,
        MODEL_TENSOR.ENC_OUTPUT_NORM,
    ],
    MODEL_ARCH.JAIS: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.JAIS2: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.NEMOTRON: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.NEMOTRON_H: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.SSM_IN,
        MODEL_TENSOR.SSM_CONV1D,
        MODEL_TENSOR.SSM_DT,
        MODEL_TENSOR.SSM_A,
        MODEL_TENSOR.SSM_D,
        MODEL_TENSOR.SSM_NORM,
        MODEL_TENSOR.SSM_OUT,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.NEMOTRON_H_MOE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.SSM_IN,
        MODEL_TENSOR.SSM_CONV1D,
        MODEL_TENSOR.SSM_DT,
        MODEL_TENSOR.SSM_A,
        MODEL_TENSOR.SSM_D,
        MODEL_TENSOR.SSM_NORM,
        MODEL_TENSOR.SSM_OUT,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        # experts
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        # expert latent
        MODEL_TENSOR.MOE_LATENT_DOWN,
        MODEL_TENSOR.MOE_LATENT_UP,
        # shared expert
        MODEL_TENSOR.FFN_DOWN_SHEXP,
        MODEL_TENSOR.FFN_UP_SHEXP,
        MODEL_TENSOR.FFN_EXP_PROBS_B,
    ],
    MODEL_ARCH.EXAONE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.EXAONE4: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_POST_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_POST_NORM,
    ],
    MODEL_ARCH.EXAONE_MOE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_GATE_SHEXP,
        MODEL_TENSOR.FFN_DOWN_SHEXP,
        MODEL_TENSOR.FFN_UP_SHEXP,
        MODEL_TENSOR.FFN_EXP_PROBS_B,
        # NextN/MTP tensors - preserved but unused
        MODEL_TENSOR.NEXTN_EH_PROJ,
        MODEL_TENSOR.NEXTN_EMBED_TOKENS,
        MODEL_TENSOR.NEXTN_ENORM,
        MODEL_TENSOR.NEXTN_HNORM,
        MODEL_TENSOR.NEXTN_SHARED_HEAD_HEAD,
        MODEL_TENSOR.NEXTN_SHARED_HEAD_NORM,
    ],
    MODEL_ARCH.GRANITE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.GRANITE_MOE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_GATE_SHEXP,
        MODEL_TENSOR.FFN_UP_SHEXP,
        MODEL_TENSOR.FFN_DOWN_SHEXP,
    ],
    MODEL_ARCH.GRANITE_HYBRID: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.SSM_IN,
        MODEL_TENSOR.SSM_CONV1D,
        MODEL_TENSOR.SSM_DT,
        MODEL_TENSOR.SSM_A,
        MODEL_TENSOR.SSM_D,
        MODEL_TENSOR.SSM_NORM,
        MODEL_TENSOR.SSM_OUT,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        # MoE
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_GATE_SHEXP,
        MODEL_TENSOR.FFN_UP_SHEXP,
        MODEL_TENSOR.FFN_DOWN_SHEXP,
        # Dense
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.CHAMELEON: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.WAVTOKENIZER_DEC: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.TOKEN_EMBD_NORM,
        MODEL_TENSOR.CONV1D,
        MODEL_TENSOR.CONVNEXT_DW,
        MODEL_TENSOR.CONVNEXT_NORM,
        MODEL_TENSOR.CONVNEXT_PW1,
        MODEL_TENSOR.CONVNEXT_PW2,
        MODEL_TENSOR.CONVNEXT_GAMMA,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.POSNET_CONV1,
        MODEL_TENSOR.POSNET_CONV2,
        MODEL_TENSOR.POSNET_NORM,
        MODEL_TENSOR.POSNET_NORM1,
        MODEL_TENSOR.POSNET_NORM2,
        MODEL_TENSOR.POSNET_ATTN_NORM,
        MODEL_TENSOR.POSNET_ATTN_Q,
        MODEL_TENSOR.POSNET_ATTN_K,
        MODEL_TENSOR.POSNET_ATTN_V,
        MODEL_TENSOR.POSNET_ATTN_OUT,
    ],
    MODEL_ARCH.BAILINGMOE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_GATE_SHEXP,
        MODEL_TENSOR.FFN_DOWN_SHEXP,
        MODEL_TENSOR.FFN_UP_SHEXP,
    ],
    MODEL_ARCH.BAILINGMOE2: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_EXP_PROBS_B,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_GATE_SHEXP,
        MODEL_TENSOR.FFN_DOWN_SHEXP,
        MODEL_TENSOR.FFN_UP_SHEXP,
        MODEL_TENSOR.NEXTN_EH_PROJ,
        MODEL_TENSOR.NEXTN_EMBED_TOKENS,
        MODEL_TENSOR.NEXTN_ENORM,
        MODEL_TENSOR.NEXTN_HNORM,
        MODEL_TENSOR.NEXTN_SHARED_HEAD_HEAD,
        MODEL_TENSOR.NEXTN_SHARED_HEAD_NORM,
        MODEL_TENSOR.LAYER_OUT_NORM,
    ],
    MODEL_ARCH.DOTS1: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_EXP_PROBS_B,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_SHEXP,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_DOWN_SHEXP,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_UP_SHEXP,
    ],
    MODEL_ARCH.ARCEE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.AFMOE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_POST_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_GATE,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_GATE_SHEXP,
        MODEL_TENSOR.FFN_UP_SHEXP,
        MODEL_TENSOR.FFN_DOWN_SHEXP,
        MODEL_TENSOR.FFN_PRE_NORM,
        MODEL_TENSOR.FFN_POST_NORM,
        MODEL_TENSOR.FFN_EXP_PROBS_B,
    ],
    MODEL_ARCH.ERNIE4_5: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.PADDLEOCR: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.FALCON_H1: [
        # Token embedding
        MODEL_TENSOR.TOKEN_EMBD,

        # Input layernorm
        MODEL_TENSOR.ATTN_NORM,

        # Attention components
        MODEL_TENSOR.ATTN_Q,         # Query projection
        MODEL_TENSOR.ATTN_K,         # Key projection
        MODEL_TENSOR.ATTN_V,         # Value projection
        MODEL_TENSOR.ATTN_OUT,       # Output projection

        # SSM components (Mamba2 specific)
        MODEL_TENSOR.SSM_IN,         # Input projection for SSM
        MODEL_TENSOR.SSM_CONV1D,     # Convolution layer
        MODEL_TENSOR.SSM_DT,         # Delta time projection
        MODEL_TENSOR.SSM_A,          # A parameter (log form)
        MODEL_TENSOR.SSM_D,          # D parameter
        MODEL_TENSOR.SSM_NORM,       # Normalization in SSM
        MODEL_TENSOR.SSM_OUT,        # Output projection

        # Pre-feedforward layernorm
        MODEL_TENSOR.FFN_PRE_NORM,

        # Feed-forward network components
        MODEL_TENSOR.FFN_GATE,       # Gate projection (SwiGLU)
        MODEL_TENSOR.FFN_DOWN,       # Down projection
        MODEL_TENSOR.FFN_UP,         # Up projection

        # Post-feedforward layernorm
        MODEL_TENSOR.OUTPUT_NORM,    # Final layer norm
        MODEL_TENSOR.OUTPUT,         # Output projection (lm_head)
    ],
    MODEL_ARCH.HUNYUAN_MOE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_GATE_SHEXP,
        MODEL_TENSOR.FFN_DOWN_SHEXP,
        MODEL_TENSOR.FFN_UP_SHEXP,
    ],
    MODEL_ARCH.HUNYUAN_DENSE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.HUNYUAN_VL: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.SMOLLM3: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.GPT_OSS: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_POST_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_SINKS,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
    ],
    MODEL_ARCH.LFM2: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.TOKEN_EMBD_NORM,
        MODEL_TENSOR.SHORTCONV_CONV,
        MODEL_TENSOR.SHORTCONV_INPROJ,
        MODEL_TENSOR.SHORTCONV_OUTPROJ,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.ATTN_NORM, # operator_norm
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.DENSE_2_OUT, # LFM2-ColBert-350M
    ],
    MODEL_ARCH.LFM2MOE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.TOKEN_EMBD_NORM,
        MODEL_TENSOR.SHORTCONV_CONV,
        MODEL_TENSOR.SHORTCONV_INPROJ,
        MODEL_TENSOR.SHORTCONV_OUTPROJ,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.ATTN_NORM, # operator_norm
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_EXP_PROBS_B,
    ],
    MODEL_ARCH.SMALLTHINKER: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
    ],
    MODEL_ARCH.APERTUS: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.LLADA_MOE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
    ],
    MODEL_ARCH.GROVEMOE: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_GATE_CHEXP,
        MODEL_TENSOR.FFN_DOWN_CHEXP,
        MODEL_TENSOR.FFN_UP_CHEXP,
    ],
    MODEL_ARCH.MINIMAXM2: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_EXP_PROBS_B,
    ],
    MODEL_ARCH.COGVLM: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_QKV,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.VISEXP_ATTN_QKV,
        MODEL_TENSOR.VISEXP_ATTN_OUT,
        MODEL_TENSOR.VISEXP_GATE,
        MODEL_TENSOR.VISEXP_UP,
        MODEL_TENSOR.VISEXP_DOWN,
    ],
    MODEL_ARCH.RND1: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
    ],
    MODEL_ARCH.PANGU_EMBED: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.MISTRAL3: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
    ],
    MODEL_ARCH.MISTRAL4: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_A,
        MODEL_TENSOR.ATTN_Q_B,
        MODEL_TENSOR.ATTN_KV_A_MQA,
        MODEL_TENSOR.ATTN_KV_B,
        MODEL_TENSOR.ATTN_K_B,
        MODEL_TENSOR.ATTN_V_B,
        MODEL_TENSOR.ATTN_Q_A_NORM,
        MODEL_TENSOR.ATTN_KV_A_NORM,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_GATE_UP_EXP,
        MODEL_TENSOR.FFN_GATE_SHEXP,
        MODEL_TENSOR.FFN_DOWN_SHEXP,
        MODEL_TENSOR.FFN_UP_SHEXP,
        MODEL_TENSOR.FFN_EXP_PROBS_B,
    ],
    MODEL_ARCH.MIMO2: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_SINKS,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_EXP_PROBS_B,
    ],
    MODEL_ARCH.STEP35: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_GATE,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.FFN_UP_SHEXP,
        MODEL_TENSOR.FFN_GATE_SHEXP,
        MODEL_TENSOR.FFN_DOWN_SHEXP,
        MODEL_TENSOR.FFN_EXP_PROBS_B,
    ],
    MODEL_ARCH.LLAMA_EMBED: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_ROT_EMBD,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
    ],
    MODEL_ARCH.MAINCODER: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_Q_NORM,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_K_NORM,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
    ],
    MODEL_ARCH.KIMI_LINEAR: [
        MODEL_TENSOR.TOKEN_EMBD,
        MODEL_TENSOR.OUTPUT_NORM,
        MODEL_TENSOR.OUTPUT,
        MODEL_TENSOR.ATTN_NORM,
        MODEL_TENSOR.ATTN_Q,
        MODEL_TENSOR.ATTN_K,
        MODEL_TENSOR.ATTN_V,
        MODEL_TENSOR.ATTN_OUT,
        MODEL_TENSOR.ATTN_Q_A,
        MODEL_TENSOR.ATTN_Q_B,
        MODEL_TENSOR.ATTN_KV_A_MQA,
        MODEL_TENSOR.ATTN_KV_B,
        MODEL_TENSOR.ATTN_K_B,
        MODEL_TENSOR.ATTN_V_B,
        MODEL_TENSOR.ATTN_Q_A_NORM,
        MODEL_TENSOR.ATTN_KV_A_NORM,
        MODEL_TENSOR.FFN_NORM,
        MODEL_TENSOR.FFN_GATE,
        MODEL_TENSOR.FFN_DOWN,
        MODEL_TENSOR.FFN_UP,
        MODEL_TENSOR.FFN_GATE_INP,
        MODEL_TENSOR.FFN_GATE_EXP,
        MODEL_TENSOR.FFN_DOWN_EXP,
        MODEL_TENSOR.FFN_UP_EXP,
        MODEL_TENSOR.SSM_CONV1D_Q,
        MODEL_TENSOR.SSM_CONV1D_K,
        MODEL_TENSOR.SSM_CONV1D_V,
        MODEL_TENSOR.SSM_F_A,
        MODEL_TENSOR.SSM_F_B,
        MODEL_TENSOR.SSM_BETA,
        MODEL_TENSOR.SSM_A,
        MODEL_TENSOR.SSM_G_A,
        MODEL_TENSOR.SSM_G_B,
        MODEL_TENSOR.SSM_DT,
        MODEL_TENSOR.SSM_NORM,
        MODEL_TENSOR.FFN_EXP_PROBS_B,
        MODEL_TENSOR.FFN_GATE_SHEXP,
        MODEL_TENSOR.FFN_DOWN_SHEXP,
        MODEL_TENSOR.FFN_UP_SHEXP,
    ],
    # TODO
}

# tensors that will not be serialized
MODEL_TENSOR_SKIP: dict[MODEL_ARCH, list[MODEL_TENSOR]] = {
    MODEL_ARCH.LLAMA: [
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_ROT_EMBD,
    ],
    MODEL_ARCH.DECI: [
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_ROT_EMBD,
    ],
    MODEL_ARCH.BAICHUAN: [
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_ROT_EMBD,
    ],
    MODEL_ARCH.QWEN: [
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_ROT_EMBD,
    ],
    MODEL_ARCH.CODESHELL: [
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_ROT_EMBD,
    ],
    MODEL_ARCH.ORION: [
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_ROT_EMBD,
    ],
    MODEL_ARCH.STARCODER2: [
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_ROT_EMBD,
    ],
    MODEL_ARCH.XVERSE: [
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_ROT_EMBD,
    ],
    MODEL_ARCH.DEEPSEEK: [
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_ROT_EMBD,
    ],
    MODEL_ARCH.DEEPSEEK2: [
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_ROT_EMBD,
    ],
    MODEL_ARCH.DEEPSEEK2OCR: [
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_ROT_EMBD,
    ],
    MODEL_ARCH.CHATGLM: [
        MODEL_TENSOR.ROPE_FREQS,
    ],
    MODEL_ARCH.NEMOTRON: [
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_ROT_EMBD,
    ],
    MODEL_ARCH.BAILINGMOE: [
        MODEL_TENSOR.ROPE_FREQS,
    ],
    MODEL_ARCH.PANGU_EMBED: [
        MODEL_TENSOR.ROPE_FREQS,
        MODEL_TENSOR.ATTN_ROT_EMBD,
    ],
}

#
# types
#


class TokenType(enum.IntEnum):
    NORMAL       = 1
    UNKNOWN      = 2
    CONTROL      = 3
    USER_DEFINED = 4
    UNUSED       = 5
    BYTE         = 6


class RopeScalingType(enum.Enum):
    NONE     = 'none'
    LINEAR   = 'linear'
    YARN     = 'yarn'
    LONGROPE = 'longrope'


class PoolingType(enum.IntEnum):
    NONE = 0
    MEAN = 1
    CLS  = 2
    LAST = 3
    RANK = 4


class GGMLQuantizationType(enum.IntEnum):
    F32     = 0
    F16     = 1
    Q4_0    = 2
    Q4_1    = 3
    Q5_0    = 6
    Q5_1    = 7
    Q8_0    = 8
    Q8_1    = 9
    Q2_K    = 10
    Q3_K    = 11
    Q4_K    = 12
    Q5_K    = 13
    Q6_K    = 14
    Q8_K    = 15
    IQ2_XXS = 16
    IQ2_XS  = 17
    IQ3_XXS = 18
    IQ1_S   = 19
    IQ4_NL  = 20
    IQ3_S   = 21
    IQ2_S   = 22
    IQ4_XS  = 23
    I8      = 24
    I16     = 25
    I32     = 26
    I64     = 27
    F64     = 28
    IQ1_M   = 29
    BF16    = 30
    TQ1_0   = 34
    TQ2_0   = 35
    MXFP4   = 39
    NVFP4   = 40
    Q1_0    = 41


class ExpertGatingFuncType(enum.IntEnum):
    SOFTMAX  = 1
    SIGMOID  = 2


# TODO: add GGMLFileType from ggml_ftype in ggml.h


# from llama_ftype in llama.h
# ALL VALUES SHOULD BE THE SAME HERE AS THEY ARE OVER THERE.
class LlamaFileType(enum.IntEnum):
    ALL_F32              = 0
    MOSTLY_F16           = 1   # except 1d tensors
    MOSTLY_Q4_0          = 2   # except 1d tensors
    MOSTLY_Q4_1          = 3   # except 1d tensors
    # MOSTLY_Q4_1_SOME_F16 = 4   # tok_embeddings.weight and output.weight are F16
    # MOSTLY_Q4_2        = 5   # support has been removed
    # MOSTLY_Q4_3        = 6   # support has been removed
    MOSTLY_Q8_0          = 7   # except 1d tensors
    MOSTLY_Q5_0          = 8   # except 1d tensors
    MOSTLY_Q5_1          = 9   # except 1d tensors
    MOSTLY_Q2_K          = 10  # except 1d tensors
    MOSTLY_Q3_K_S        = 11  # except 1d tensors
    MOSTLY_Q3_K_M        = 12  # except 1d tensors
    MOSTLY_Q3_K_L        = 13  # except 1d tensors
    MOSTLY_Q4_K_S        = 14  # except 1d tensors
    MOSTLY_Q4_K_M        = 15  # except 1d tensors
    MOSTLY_Q5_K_S        = 16  # except 1d tensors
    MOSTLY_Q5_K_M        = 17  # except 1d tensors
    MOSTLY_Q6_K          = 18  # except 1d tensors
    MOSTLY_IQ2_XXS       = 19  # except 1d tensors
    MOSTLY_IQ2_XS        = 20  # except 1d tensors
    MOSTLY_Q2_K_S        = 21  # except 1d tensors
    MOSTLY_IQ3_XS        = 22  # except 1d tensors
    MOSTLY_IQ3_XXS       = 23  # except 1d tensors
    MOSTLY_IQ1_S         = 24  # except 1d tensors
    MOSTLY_IQ4_NL        = 25  # except 1d tensors
    MOSTLY_IQ3_S         = 26  # except 1d tensors
    MOSTLY_IQ3_M         = 27  # except 1d tensors
    MOSTLY_IQ2_S         = 28  # except 1d tensors
    MOSTLY_IQ2_M         = 29  # except 1d tensors
    MOSTLY_IQ4_XS        = 30  # except 1d tensors
    MOSTLY_IQ1_M         = 31  # except 1d tensors
    MOSTLY_BF16          = 32  # except 1d tensors
    # MOSTLY_Q4_0_4_4      = 33  # removed from gguf files, use Q4_0 and runtime repack
    # MOSTLY_Q4_0_4_8      = 34  # removed from gguf files, use Q4_0 and runtime repack
    # MOSTLY_Q4_0_8_8      = 35  # removed from gguf files, use Q4_0 and runtime repack
    MOSTLY_TQ1_0         = 36  # except 1d tensors
    MOSTLY_TQ2_0         = 37  # except 1d tensors
    MOSTLY_MXFP4_MOE     = 38  # except 1d tensors
    MOSTLY_NVFP4         = 39  # except 1d tensors
    MOSTLY_Q1_0          = 40  # except 1d tensors

    GUESSED              = 1024  # not specified in the model file


class GGUFEndian(enum.IntEnum):
    LITTLE = 0
    BIG = 1


class GGUFValueType(enum.IntEnum):
    UINT8   = 0
    INT8    = 1
    UINT16  = 2
    INT16   = 3
    UINT32  = 4
    INT32   = 5
    FLOAT32 = 6
    BOOL    = 7
    STRING  = 8
    ARRAY   = 9
    UINT64  = 10
    INT64   = 11
    FLOAT64 = 12

    @staticmethod
    def get_type(val: ta.Any) -> GGUFValueType:
        if isinstance(val, (str, bytes, bytearray)):
            return GGUFValueType.STRING
        elif isinstance(val, list):
            return GGUFValueType.ARRAY
        elif isinstance(val, float):
            return GGUFValueType.FLOAT32
        elif isinstance(val, bool):
            return GGUFValueType.BOOL
        elif isinstance(val, int):
            return GGUFValueType.INT32
        # TODO: need help with 64-bit types in Python
        else:
            raise TypeError(f'Unknown type: {type(val)}')


class VisionProjectorType:
    GEMMA3 = 'gemma3'
    GEMMA3NV = 'gemma3nv'
    GEMMA3NA = 'gemma3na'
    GEMMA4V = 'gemma4v'
    GEMMA4A = 'gemma4a'
    PHI4 = 'phi4'
    IDEFICS3 = 'idefics3'
    PIXTRAL = 'pixtral'
    LLAMA4 = 'llama4'
    QWEN2VL = 'qwen2vl_merger'
    QWEN25VL = 'qwen2.5vl_merger'
    QWEN3VL = 'qwen3vl_merger'
    STEP3VL = 'step3vl'
    ULTRAVOX = 'ultravox'
    INTERNVL = 'internvl'
    QWEN2A = 'qwen2a'  # audio
    QWEN3A = 'qwen3a'  # audio
    GLMA = 'glma'  # audio
    QWEN25O = 'qwen2.5o'  # omni
    VOXTRAL = 'voxtral'
    MERALION = 'meralion'  # audio: Whisper + gated MLP adaptor
    LFM2 = 'lfm2'
    KIMIVL = 'kimivl'
    PADDLEOCR = 'paddleocr'
    KIMIK25 = 'kimik25'
    LIGHTONOCR = 'lightonocr'
    COGVLM = 'cogvlm'
    JANUS_PRO = 'janus_pro'
    DOTSOCR = 'dots_ocr'
    DEEPSEEKOCR = 'deepseekocr'
    LFM2A = 'lfm2a'  # audio
    MUSIC_FLAMINGO = 'musicflamingo'  # audio
    GLM4V = 'glm4v'
    YOUTUVL = 'youtuvl'
    NEMOTRON_V2_VL = 'nemotron_v2_vl'
    HUNYUANOCR     = 'hunyuanocr'
    HUNYUANVL      = 'hunyuanvl'
    GRANITE_SPEECH = 'granite_speech'  # audio


# Items here are (block size, type size)
QK_K = 256
GGML_QUANT_SIZES: dict[GGMLQuantizationType, tuple[int, int]] = {
    GGMLQuantizationType.F32:     (1, 4),
    GGMLQuantizationType.F16:     (1, 2),
    GGMLQuantizationType.Q4_0:    (32, 2 + 16),
    GGMLQuantizationType.Q4_1:    (32, 2 + 2 + 16),
    GGMLQuantizationType.Q5_0:    (32, 2 + 4 + 16),
    GGMLQuantizationType.Q5_1:    (32, 2 + 2 + 4 + 16),
    GGMLQuantizationType.Q8_0:    (32, 2 + 32),
    GGMLQuantizationType.Q8_1:    (32, 4 + 4 + 32),
    GGMLQuantizationType.Q2_K:    (256, 2 + 2 + QK_K // 16 + QK_K // 4),
    GGMLQuantizationType.Q3_K:    (256, 2 + QK_K // 4 + QK_K // 8 + 12),
    GGMLQuantizationType.Q4_K:    (256, 2 + 2 + QK_K // 2 + 12),
    GGMLQuantizationType.Q5_K:    (256, 2 + 2 + QK_K // 2 + QK_K // 8 + 12),
    GGMLQuantizationType.Q6_K:    (256, 2 + QK_K // 2 + QK_K // 4 + QK_K // 16),
    GGMLQuantizationType.Q8_K:    (256, 4 + QK_K + QK_K // 8),
    GGMLQuantizationType.IQ2_XXS: (256, 2 + QK_K // 4),
    GGMLQuantizationType.IQ2_XS:  (256, 2 + QK_K // 4 + QK_K // 32),
    GGMLQuantizationType.IQ3_XXS: (256, 2 + QK_K // 4 + QK_K // 8),
    GGMLQuantizationType.IQ1_S:   (256, 2 + QK_K // 8 + QK_K // 16),
    GGMLQuantizationType.IQ4_NL:  (32, 2 + 16),
    GGMLQuantizationType.IQ3_S:   (256, 2 + QK_K // 4 + QK_K // 8 + QK_K // 32 + 4),
    GGMLQuantizationType.IQ2_S:   (256, 2 + QK_K // 4 + QK_K // 16),
    GGMLQuantizationType.IQ4_XS:  (256, 2 + 2 + QK_K // 2 + QK_K // 64),
    GGMLQuantizationType.I8:      (1, 1),
    GGMLQuantizationType.I16:     (1, 2),
    GGMLQuantizationType.I32:     (1, 4),
    GGMLQuantizationType.I64:     (1, 8),
    GGMLQuantizationType.F64:     (1, 8),
    GGMLQuantizationType.IQ1_M:   (256, QK_K // 8 + QK_K // 16  + QK_K // 32),
    GGMLQuantizationType.BF16:    (1, 2),
    GGMLQuantizationType.TQ1_0:   (256, 2 + 4 * 13),
    GGMLQuantizationType.TQ2_0:   (256, 2 + 64),
    GGMLQuantizationType.MXFP4:   (32, 1 + 16),
    GGMLQuantizationType.NVFP4:   (64, 4 + 32),
    GGMLQuantizationType.Q1_0:    (128, 2 + 16),
}


##
# Aliases for backward compatibility.


# general
KEY_GENERAL_ARCHITECTURE         = Keys.General.ARCHITECTURE
KEY_GENERAL_QUANTIZATION_VERSION = Keys.General.QUANTIZATION_VERSION
KEY_GENERAL_ALIGNMENT            = Keys.General.ALIGNMENT
KEY_GENERAL_NAME                 = Keys.General.NAME
KEY_GENERAL_AUTHOR               = Keys.General.AUTHOR
KEY_GENERAL_URL                  = Keys.General.URL
KEY_GENERAL_DESCRIPTION          = Keys.General.DESCRIPTION
KEY_GENERAL_LICENSE              = Keys.General.LICENSE
KEY_GENERAL_SOURCE_URL           = Keys.General.SOURCE_URL
KEY_GENERAL_FILE_TYPE            = Keys.General.FILE_TYPE

# LLM
KEY_VOCAB_SIZE            = Keys.LLM.VOCAB_SIZE
KEY_CONTEXT_LENGTH        = Keys.LLM.CONTEXT_LENGTH
KEY_EMBEDDING_LENGTH      = Keys.LLM.EMBEDDING_LENGTH
KEY_BLOCK_COUNT           = Keys.LLM.BLOCK_COUNT
KEY_FEED_FORWARD_LENGTH   = Keys.LLM.FEED_FORWARD_LENGTH
KEY_USE_PARALLEL_RESIDUAL = Keys.LLM.USE_PARALLEL_RESIDUAL
KEY_TENSOR_DATA_LAYOUT    = Keys.LLM.TENSOR_DATA_LAYOUT

# attention
KEY_ATTENTION_HEAD_COUNT        = Keys.Attention.HEAD_COUNT
KEY_ATTENTION_HEAD_COUNT_KV     = Keys.Attention.HEAD_COUNT_KV
KEY_ATTENTION_MAX_ALIBI_BIAS    = Keys.Attention.MAX_ALIBI_BIAS
KEY_ATTENTION_CLAMP_KQV         = Keys.Attention.CLAMP_KQV
KEY_ATTENTION_LAYERNORM_EPS     = Keys.Attention.LAYERNORM_EPS
KEY_ATTENTION_LAYERNORM_RMS_EPS = Keys.Attention.LAYERNORM_RMS_EPS

# RoPE
KEY_ROPE_DIMENSION_COUNT           = Keys.Rope.DIMENSION_COUNT
KEY_ROPE_FREQ_BASE                 = Keys.Rope.FREQ_BASE
KEY_ROPE_SCALING_TYPE              = Keys.Rope.SCALING_TYPE
KEY_ROPE_SCALING_FACTOR            = Keys.Rope.SCALING_FACTOR
KEY_ROPE_SCALING_ORIG_CTX_LEN      = Keys.Rope.SCALING_ORIG_CTX_LEN
KEY_ROPE_SCALING_FINETUNED         = Keys.Rope.SCALING_FINETUNED

# SSM
KEY_SSM_CONV_KERNEL    = Keys.SSM.CONV_KERNEL
KEY_SSM_INNER_SIZE     = Keys.SSM.INNER_SIZE
KEY_SSM_STATE_SIZE     = Keys.SSM.STATE_SIZE
KEY_SSM_TIME_STEP_RANK = Keys.SSM.TIME_STEP_RANK
KEY_SSM_GROUP_COUNT    = Keys.SSM.GROUP_COUNT
KEY_SSM_DT_B_C_RMS     = Keys.SSM.DT_B_C_RMS

# KDA
KEY_KDA_HEAD_DIM       = Keys.KDA.HEAD_DIM

# tokenization
KEY_TOKENIZER_MODEL      = Keys.Tokenizer.MODEL
KEY_TOKENIZER_PRE        = Keys.Tokenizer.PRE
KEY_TOKENIZER_LIST       = Keys.Tokenizer.LIST
KEY_TOKENIZER_TOKEN_TYPE = Keys.Tokenizer.TOKEN_TYPE
KEY_TOKENIZER_SCORES     = Keys.Tokenizer.SCORES
KEY_TOKENIZER_MERGES     = Keys.Tokenizer.MERGES
KEY_TOKENIZER_BOS_ID     = Keys.Tokenizer.BOS_ID
KEY_TOKENIZER_EOS_ID     = Keys.Tokenizer.EOS_ID
KEY_TOKENIZER_EOT_ID     = Keys.Tokenizer.EOT_ID
KEY_TOKENIZER_EOM_ID     = Keys.Tokenizer.EOM_ID
KEY_TOKENIZER_UNK_ID     = Keys.Tokenizer.UNK_ID
KEY_TOKENIZER_SEP_ID     = Keys.Tokenizer.SEP_ID
KEY_TOKENIZER_PAD_ID     = Keys.Tokenizer.PAD_ID
KEY_TOKENIZER_MASK_ID    = Keys.Tokenizer.MASK_ID
KEY_TOKENIZER_HF_JSON    = Keys.Tokenizer.HF_JSON
KEY_TOKENIZER_RWKV       = Keys.Tokenizer.RWKV

KEY_TOKENIZER_FIM_PRE_ID = Keys.Tokenizer.FIM_PRE_ID
KEY_TOKENIZER_FIM_SUF_ID = Keys.Tokenizer.FIM_SUF_ID
KEY_TOKENIZER_FIM_MID_ID = Keys.Tokenizer.FIM_MID_ID
KEY_TOKENIZER_FIM_PAD_ID = Keys.Tokenizer.FIM_PAD_ID
KEY_TOKENIZER_FIM_REP_ID = Keys.Tokenizer.FIM_REP_ID
KEY_TOKENIZER_FIM_SEP_ID = Keys.Tokenizer.FIM_SEP_ID

# deprecated
KEY_TOKENIZER_PREFIX_ID  = Keys.Tokenizer.PREFIX_ID
KEY_TOKENIZER_SUFFIX_ID  = Keys.Tokenizer.SUFFIX_ID
KEY_TOKENIZER_MIDDLE_ID  = Keys.Tokenizer.MIDDLE_ID
