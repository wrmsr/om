# @om-precheck-allow-any-unicode
"""
What test_tokenizers checks against a download, checked against a few lines of text given here: that a vocabulary
trained by the bpe extension is one tiktoken can take, and encodes with as the extension itself does.
"""
import os.path

from omcore import lang
from omcore.testing import pytest as ptu

from ...bpe import _bpe
from ..tokenizers import SPECIAL_TOKENS
from ..tokenizers import SPLIT_PATTERN
from ..tokenizers import RustBPETokenizer


with lang.auto_proxy_import(globals()):
    import tiktoken


##


TEXTS = [
    "Hello world! I'm fine, you're not. We've been, they'll go, he'd say, it's 'quoted'.",
    'The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog again.',
    'def encode(self, text):\n    return [self.merges[p] for p in pairs(text)]\n',
    '3.14159 26535 8979 323 84 6 1,000,000 0x7fff 1e-9 2026-10-08T03:02:00Z',
    'line one\r\n\r\n  line two   \n\n\n   \nline three\r',
    '中文分词是一个难题，没有空格可以依靠。这是第二句话！',
    'ひらがなとカタカナと漢字が混ざった文章です。',
    'Привет, мир! Как дела? Всё хорошо, спасибо.',
    'naïve café résumé Zürich, cafe\u0301 with a combining accent',
    '🙃 😀👍🏽 👨\u200d👩\u200d👧\u200d👦 🇯🇵',
    'non\u00a0breaking, ideographic\u3000space, line\u2028separator',
] * 3

UNSEEN_TEXTS = [
    'Hello again, world: the lazy fox was not quoted in 2026.',
    'return [encode(text) for text in lines]',
    '中文和ひらがな、そして Привет!',
    '',
    ' ',
]


@ptu.skip.if_cant_import('tiktoken')
def test_export():
    for pattern in (None, SPLIT_PATTERN):
        tok = _bpe.Tokenizer()
        tok.train_from_iterator(TEXTS, 500, pattern=pattern)
        assert tok.vocab_size == 500

        enc = tiktoken.Encoding(
            name='bpe',
            pat_str=tok.get_pattern(),
            mergeable_ranks=dict(tok.get_mergeable_ranks()),
            special_tokens={},
        )
        assert enc.n_vocab == 500

        for text in [*TEXTS, *UNSEEN_TEXTS]:
            ids = tok.encode(text)
            assert enc.encode_ordinary(text) == ids
            assert enc.decode(ids) == text
            assert tok.decode(enc.encode_ordinary(text)) == text
        assert enc.encode_ordinary_batch(UNSEEN_TEXTS) == tok.batch_encode(UNSEEN_TEXTS)


@ptu.skip.if_cant_import('tiktoken')
def test_tokenizer(tmp_path):
    vocab_size = 400
    tok = RustBPETokenizer.train_from_iterator(iter(TEXTS), vocab_size)
    assert tok.get_vocab_size() == vocab_size
    assert tok.get_special_tokens() == set(SPECIAL_TOKENS)

    # The special tokens come after everything trained, and the first of them is the one documents begin with.
    bos = tok.get_bos_token_id()
    assert bos == vocab_size - len(SPECIAL_TOKENS)
    assert [tok.encode_special(name) for name in SPECIAL_TOKENS] == list(range(bos, vocab_size))

    trained = _bpe.Tokenizer()
    trained.train_from_iterator(TEXTS, bos, pattern=SPLIT_PATTERN)
    for text in [*TEXTS, *UNSEEN_TEXTS]:
        ids = tok.encode(text)
        assert ids == trained.encode(text)
        assert tok.decode(ids) == text
        assert tok.encode(text, prepend='<|bos|>', append=bos) == [bos, *ids, bos]
    assert tok.encode(UNSEEN_TEXTS) == trained.batch_encode(UNSEEN_TEXTS)

    tok.save(str(tmp_path))
    assert os.path.isfile(os.path.join(tmp_path, 'tokenizer.pkl'))
    reloaded = RustBPETokenizer.from_directory(str(tmp_path))
    assert reloaded.get_vocab_size() == vocab_size
    assert reloaded.encode(UNSEEN_TEXTS) == tok.encode(UNSEEN_TEXTS)


@ptu.skip.if_cant_import('tiktoken')
def test_render_conversation():
    tok = RustBPETokenizer.train_from_iterator(TEXTS, 400)
    conversation = {
        'messages': [
            {'role': 'system', 'content': 'Be brief.'},
            {'role': 'user', 'content': 'Hello world!'},
            {'role': 'assistant', 'content': 'The quick brown fox.'},
        ],
    }

    ids, mask = tok.render_conversation(conversation)
    assert len(ids) == len(mask)
    assert tok.decode(ids) == ''.join([
        '<|bos|>',
        '<|user_start|>Be brief.\n\nHello world!<|user_end|>',
        '<|assistant_start|>The quick brown fox.<|assistant_end|>',
    ])

    # Only what the assistant says, and its saying that it is done, is trained on.
    assistant_start = ids.index(tok.encode_special('<|assistant_start|>'))
    assert mask == [0] * (assistant_start + 1) + [1] * (len(ids) - assistant_start - 1)

    assert tok.render_for_completion(conversation) == ids[:assistant_start + 1]
