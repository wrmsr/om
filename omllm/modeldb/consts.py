import typing as ta


##


MODELS_URL: ta.Final = 'https://models.dev/api.json'


DEFAULT_PRIMARY_PROVIDERS: ta.Final[ta.Sequence[str]] = (
    'anthropic',
    'cerebras',
    'google',
    'groq',
    'openai',
    'openrouter',
)


_OTHER_PROVIDERS_KEY: ta.Final = '__other__'

_CACHE_FILE_SUFFIX: ta.Final = '.json.zstd'
