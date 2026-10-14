DEFAULT_PS_FORMAT_KEYS = [
    'ID',
    'Image',
    'Command',
    'RunningFor',
    'Status',
    'Ports',
    'Names',
]

DEFAULT_PS_FORMAT_STR = '\t'.join([f'{{{{.{k}}}}}' for k in DEFAULT_PS_FORMAT_KEYS])
