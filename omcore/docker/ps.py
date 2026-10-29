import typing as ta


##


def build_ps_format_str(keys: str | ta.Sequence[str]) -> str:
    return '\t'.join([f'{{{{.{k}}}}}' for k in ([keys] if isinstance(keys, str) else keys)])


##


DEFAULT_PS_FORMAT_KEYS = [
    'ID',
    'Image',
    'Command',
    'RunningFor',
    'Status',
    'Ports',
    'Names',
]


DEFAULT_PS_FORMAT_STR = build_ps_format_str(DEFAULT_PS_FORMAT_KEYS)
