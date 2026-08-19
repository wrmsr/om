import sys
import typing as ta

import pytest
import transformers as tfm

from omcore import check
from omcore import lang
from omcore.testing import pytest as ptu

from ..filecache import file_cache_patch_context


class BaseTransformersChatChoicesService(lang.ExitStacked):
    DEFAULT_MODEL: ta.ClassVar[str] = (
        'meta-llama/Llama-3.2-1B-Instruct'
    )

    def __init__(
            self,
            model_path: str,
            **model_kwargs: ta.Any,
    ) -> None:
        super().__init__()

        self._model_path = model_path
        self._model_kwargs = model_kwargs

    @lang.cached_function(transient=True)
    def _load_pipeline(self) -> tfm.Pipeline:
        # FIXME: unload
        check.not_none(self._exit_stack)

        pkw: dict[str, ta.Any] = dict(
            model=self._model_path,
            device='mps' if sys.platform == 'darwin' else 'cuda',
        )

        # if self._huggingface_hub_token is not None:
        #     pkw.update(token=self._huggingface_hub_token.reveal())
        # for pkw_cfg in self._pipeline_kwargs:
        #     pkw.update(pkw_cfg.v)

        with file_cache_patch_context(
                local_first=True,
                local_config_present_is_authoritative=True,
        ):
            return tfm.pipeline(
                'text-generation',
                **pkw,
            )


class TransformersChatChoicesService(BaseTransformersChatChoicesService):
    async def invoke(self, request):
        pipeline = self._load_pipeline()

        inputs = [
            {'role': 'user', 'content': request},
        ]

        outputs = pipeline(inputs)

        gts = check.single(outputs)['generated_text']
        ugt, agt = gts
        check.state(ugt['role'] == 'user')
        check.state(agt['role'] == 'assistant')

        return agt['content']


@pytest.mark.not_docker_guest
@pytest.mark.high_mem
@ptu.skip.if_cant_import('torch')
def test_transformers_chat():
    with TransformersChatChoicesService(
        'meta-llama/Llama-3.2-1B-Instruct',
        max_new_tokens=20,
    ) as llm:
        resp = lang.sync_await(llm.invoke('Is water dry?'))
        print(resp)
        assert resp
