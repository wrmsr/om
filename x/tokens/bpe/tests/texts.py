# @om-precheck-allow-any-unicode
"""Text to train and encode: a fixed handful of samples picked to be awkward to split, and as much more as is asked."""
import random


##


SAMPLES = [
    "Hello world! I'm fine, you're not. We've been, they'll go, he'd say, it's 'quoted'.",
    "SHOUTING DON'T WON'T I'LL WE'VE YOU'RE HE'D IT'S I'M",
    'The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog again.',
    'def encode(self, text):\n    return [self.merges[p] for p in pairs(text)]\n',
    'for (size_t i = 0; i + 1 < size; i++) { ranks[i] = merge_rank(model, tokens[i], tokens[i + 1]); }',
    '3.14159 26535 8979 323 84 6 1,000,000 0x7fff 1e-9 2026-10-08T03:02:00Z',
    'x = 1;  y = 22;   z = 333;\tw = 4444;\t\tv = 55555;',
    'line one\r\n\r\n  line two   \n\n\n   \nline three\r',
    '   leading and trailing   ',
    'tabs\tand\x0bvertical\x0cfeeds\x1cand\x85next',
    '!!! ??? ... --- *** ((( ))) [[[ ]]] {{{ }}} <<< >>> === !=!= <=> ->-> ::',
    'https://example.com/a/b/c?d=e&f=g#h user@example.com /usr/local/bin ~/.config',
    '中文分词是一个难题，没有空格可以依靠。这是第二句话！',
    'ひらがなとカタカナと漢字が混ざった文章です。',
    '한국어 문장은 띄어쓰기를 합니다.',
    'Привет, мир! Как дела? Всё хорошо, спасибо.',
    'Καλημέρα κόσμε, τι κάνεις;',
    'مرحبا بالعالم، كيف حالك؟',
    'שלום עולם, מה שלומך?',
    'नमस्ते दुनिया, आप कैसे हैं?',
    'สวัสดีชาวโลก สบายดีไหม',
    'naïve café résumé Zürich Ångström Łódź',
    'cafe\u0301 with a combining accent, and a\u0308\u0304 with two',
    '🙃 😀👍🏽 👨\u200d👩\u200d👧\u200d👦 🇯🇵 ❤\ufe0f',
    '１２３４５ fullwidth ＡＢＣ and ⅣⅫ roman and ²³ superscripts and ½ fractions',
    'non\u00a0breaking, thin\u2009space, ideographic\u3000space, line\u2028separator, zero\u200bwidth',
    "it'ſ the long s, and the Kelvin \u212a, and the dotless ı and dotted İ",
    'nul\x00byte and \x7f delete and \x1b escape',
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    'abababababababababababababababab abcabcabcabcabcabcabcabc aabbaabbaabbaabb',
    '',
    ' ',
    '\n',
    'a',
]


WORDS = [
    'the', 'of', 'and', 'to', 'in', 'is', 'that', 'it', 'was', 'for', 'on', 'are', 'as', 'with', 'his', 'they', 'at',
    'be', 'this', 'from', 'have', 'or', 'by', 'one', 'had', 'not', 'but', 'what', 'all', 'were', 'when', 'we', 'there',
    'can', 'an', 'your', 'which', 'their', 'said', 'if', 'do', 'will', 'each', 'about', 'how', 'up', 'out', 'them',
    'then', 'she', 'many',
    "don't", "it's", "I'm", "we'll", "they've", "you're", "he'd",
    'tokenizer', 'encode', 'decode', 'merge', 'pair', 'vocab', 'regex', 'unicode', 'byte',
    'Hello', 'World', 'THE', 'AND', 'CamelCase', 'snake_case', 'kebab-case',
    '0', '1', '12', '123', '1234', '12345', '2026', '3.14', '0x1f',
    '中文', '分词', '日本語', 'ひらがな', '한국어', 'Привет', 'мир', 'κόσμε', 'مرحبا', 'שלום', 'नमस्ते', 'สวัสดี',
    'naïve', 'café', 'cafe\u0301', '🙃', '👍🏽', '１２３',
    '!', '?', '...', '--', '==', '!=', '()', '[]', '{}', '->', '::', '#', '@', '$',
]

SEPARATORS = [
    *([' '] * 12),
    '  ', '   ', '\n', '\n\n', '\r\n', '\t', ', ', '. ', '; ', ': ', ' - ', '\u00a0', '\u3000', '',
]


def make_text(seed, num_words):
    rng = random.Random(seed)
    parts = []
    for _ in range(num_words):
        parts.append(rng.choice(WORDS))
        parts.append(rng.choice(SEPARATORS))
    return ''.join(parts)


def make_texts(seed, num_texts, num_words):
    return [make_text(seed * 1_000_003 + i, num_words) for i in range(num_texts)]
