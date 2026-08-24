import os.path


##


def _main() -> None:
    from emoji import unicode_codes

    emoji = {
        k.lower().strip(':'): e
        for e, d in unicode_codes.EMOJI_DATA.items()
        for k in [d['en'], *d.get('alias', [])]
    }

    src = '\n'.join([
        'EMOJI = {',
        *[
            f'    {k!r}: {e!r},'
            for k, e in emoji.items()
        ],
        '}',
        '',
    ])

    with open(os.path.join(os.path.dirname(__file__), '../emoji.py'), 'w') as f:
        f.write(src)


if __name__ == '__main__':
    _main()
