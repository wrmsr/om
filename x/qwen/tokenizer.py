"""
Byte-level BPE tokenizer for Qwen (GPT-2 style), built from a GGUF's `tokenizer.ggml.*` metadata or from an HF
`tokenizer.json`. Only dependency: `regex` (for \\p{L} classes).

Matches llama.cpp's `LLAMA_VOCAB_PRE_TYPE_QWEN35` / `QWEN2` pre-tokenizers.
"""
import functools

import regex


##


PRE_REGEX = {
    'qwen2': r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}| ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+",
    'qwen35': r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?[\p{L}\p{M}]+|\p{N}| ?[^\s\p{L}\p{M}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+",
}

# GGUF token types (gguf.TokenType)
TT_NORMAL, TT_UNKNOWN, TT_CONTROL, TT_USER_DEFINED, TT_UNUSED, TT_BYTE = (
    1,
    2,
    3,
    4,
    5,
    6,
)


@functools.lru_cache(maxsize=1)
def bytes_to_unicode() -> dict[int, str]:
    bs = (
        list(range(ord('!'), ord('~') + 1))
        + list(range(ord('¡'), ord('¬') + 1))
        + list(range(ord('®'), ord('ÿ') + 1))
    )
    cs = bs[:]
    n = 0
    for b in range(256):
        if b not in bs:
            bs.append(b)
            cs.append(256 + n)
            n += 1
    return dict(zip(bs, [chr(c) for c in cs]))


class Tokenizer:
    def __init__(
        self,
        tokens: list[str],
        merges: list[tuple[str, str]],
        special: dict[str, int],
        pre: str = 'qwen35',
        eos_id: int | None = None,
        bos_id: int | None = None,
        add_bos: bool = False,
        chat_template: str | None = None,
    ):
        self.tokens = tokens
        self.vocab = {t: i for i, t in enumerate(tokens)}
        self.ranks = {pair: i for i, pair in enumerate(merges)}
        self.special = special  # literal text -> id (control / user-defined tokens)
        self.special_ids = set(special.values())
        self.pre = pre
        self.pattern = regex.compile(PRE_REGEX[pre])
        self.eos_id = eos_id
        self.bos_id = bos_id
        self.add_bos = add_bos
        self.chat_template = chat_template
        b2u = bytes_to_unicode()
        self.b2u = b2u
        self.u2b = {v: k for k, v in b2u.items()}
        if special:
            alts = sorted(special.keys(), key=len, reverse=True)
            self.special_re = regex.compile(
                '(' + '|'.join(regex.escape(s) for s in alts) + ')',
            )
        else:
            self.special_re = None
        self._cache: dict[str, tuple[str, ...]] = {}

    # construction

    @classmethod
    def from_spec(cls, spec: dict) -> "Tokenizer":
        if spec['kind'] == 'gguf':
            return cls.from_gguf_spec(spec)
        return cls.from_hf(
            spec['tokenizer_json'], spec.get('tokenizer_config'), spec.get('eos_id'),
        )

    @classmethod
    def from_gguf_spec(cls, spec: dict) -> "Tokenizer":
        assert spec['model'] == 'gpt2', f"unsupported tokenizer model {spec['model']!r}"
        tokens = spec['tokens']
        types = spec['token_type'] or [TT_NORMAL] * len(tokens)
        merges = [tuple(m.split(' ', 1)) for m in spec['merges']]
        special = {
            t: i
            for i, (t, ty) in enumerate(zip(tokens, types))
            if ty in (TT_CONTROL, TT_USER_DEFINED)
        }
        pre = spec.get('pre') or 'qwen2'
        if pre not in PRE_REGEX:
            pre = 'qwen35' if len(tokens) > 200_000 else 'qwen2'
        return cls(
            tokens,
            merges,
            special,
            pre=pre,
            eos_id=spec.get('eos_id'),
            bos_id=spec.get('bos_id'),
            add_bos=bool(spec.get('add_bos')),
            chat_template=spec.get('chat_template'),
        )

    @classmethod
    def from_hf(
        cls, tj: dict, tcfg: dict | None = None, eos_id: int | None = None,
    ) -> "Tokenizer":
        model = tj['model']
        assert model.get('type') == 'BPE'
        vocab: dict[str, int] = model['vocab']
        n = max(vocab.values()) + 1
        tokens = [''] * n
        for t, i in vocab.items():
            tokens[i] = t
        special = {}
        for at in tj.get('added_tokens', []):
            i = at['id']
            if i >= len(tokens):
                tokens.extend([''] * (i + 1 - len(tokens)))
            tokens[i] = at['content']
            special[at['content']] = i
        merges = []
        for m in model['merges']:
            merges.append(tuple(m) if isinstance(m, list) else tuple(m.split(' ', 1)))
        pre = 'qwen35'
        # prefer the regex shipped in tokenizer.json when it is one we know
        try:
            for p in tj['pre_tokenizer']['pretokenizers']:
                pat = p.get('pattern', {}).get('Regex')
                if pat:
                    for k, v in PRE_REGEX.items():
                        if pat == v:
                            pre = k
        except (KeyError, TypeError):
            pass
        chat_template = (tcfg or {}).get('chat_template')
        eos_tok = (tcfg or {}).get('eos_token')
        if eos_id is None and isinstance(eos_tok, str) and eos_tok in special:
            eos_id = special[eos_tok]
        if isinstance(eos_id, list):
            eos_id = eos_id[0]
        return cls(
            tokens, merges, special, pre=pre, eos_id=eos_id, chat_template=chat_template,
        )

    # BPE core

    def _bpe(self, word: str) -> tuple[str, ...]:
        cached = self._cache.get(word)
        if cached is not None:
            return cached
        syms = tuple(word)
        ranks = self.ranks
        while len(syms) > 1:
            best, best_rank = None, None
            for i in range(len(syms) - 1):
                r = ranks.get((syms[i], syms[i + 1]))
                if r is not None and (best_rank is None or r < best_rank):
                    best, best_rank = (syms[i], syms[i + 1]), r
            if best is None:
                break
            first, second = best
            out = []
            i = 0
            while i < len(syms):
                if i < len(syms) - 1 and syms[i] == first and syms[i + 1] == second:
                    out.append(first + second)
                    i += 2
                else:
                    out.append(syms[i])
                    i += 1
            syms = tuple(out)
        if len(self._cache) < 100_000:
            self._cache[word] = syms
        return syms

    def _encode_plain(self, text: str) -> list[int]:
        ids: list[int] = []
        vocab = self.vocab
        b2u = self.b2u
        for piece in self.pattern.findall(text):
            word = ''.join(b2u[b] for b in piece.encode('utf-8'))
            for sym in self._bpe(word):
                i = vocab.get(sym)
                if i is None:  # should not happen with a complete byte vocab
                    ids.extend(vocab[c] for c in sym)
                else:
                    ids.append(i)
        return ids

    # public API

    def encode(
        self, text: str, add_bos: bool | None = None, parse_special: bool = True,
    ) -> list[int]:
        ids: list[int] = []
        if (self.add_bos if add_bos is None else add_bos) and self.bos_id is not None:
            ids.append(self.bos_id)
        if parse_special and self.special_re is not None:
            for chunk in self.special_re.split(text):
                if not chunk:
                    continue
                sid = self.special.get(chunk)
                if sid is not None:
                    ids.append(sid)
                else:
                    ids.extend(self._encode_plain(chunk))
        else:
            ids.extend(self._encode_plain(text))
        return ids

    def token_bytes(self, i: int) -> bytes:
        t = self.tokens[i]
        if i in self.special_ids:
            return t.encode('utf-8')
        try:
            return bytes(self.u2b[c] for c in t)
        except KeyError:  # not a byte-level string (e.g. odd added token)
            return t.encode('utf-8')

    def decode(self, ids: list[int], skip_special: bool = False) -> str:
        buf = b''.join(
            self.token_bytes(i)
            for i in ids
            if not (skip_special and i in self.special_ids)
        )
        return buf.decode('utf-8', errors='replace')

    class Streamer:
        """Incremental decoder that only emits complete UTF-8 sequences."""

        def __init__(self, tok: "Tokenizer"):
            self.tok, self.buf = tok, b''

        def push(self, i: int) -> str:
            self.buf += self.tok.token_bytes(i)
            try:
                s = self.buf.decode('utf-8')
                self.buf = b''
                return s
            except UnicodeDecodeError as e:
                s = (
                    self.buf[: e.start].decode('utf-8', errors='replace')
                    if e.start
                    else ''
                )
                self.buf = self.buf[e.start :]
                return s

        def flush(self) -> str:
            s, self.buf = self.buf.decode('utf-8', errors='replace'), b''
            return s

    # chat

    def apply_chat(self, messages: list[dict], think: bool = False) -> str:
        """Minimal Qwen3.5 ChatML rendering (no tools). Set think=False to disable reasoning."""

        out = []
        for m in messages:
            out.append(f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n")
        out.append('<|im_start|>assistant\n')
        if not think:
            out.append('<think>\n\n</think>\n\n')
        return ''.join(out)
