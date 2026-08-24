import os.path


##


def _main() -> None:
    import wcwidth
    from wcwidth.table_vs16 import VS16_NARROW_TO_WIDE
    from wcwidth.table_wide import WIDE_EASTASIAN
    from wcwidth.table_zero import ZERO_WIDTH

    version = max(
        wcwidth.list_versions(),
        key=lambda v: tuple(map(int, v.split('.'))),
    )

    narrow_to_wide: set[str] = set()
    for start, end in VS16_NARROW_TO_WIDE['9.0.0']:
        narrow_to_wide.update(chr(codepoint) for codepoint in range(start, end + 1))

    table: list[tuple[int, int, int]] = []

    for start, end in WIDE_EASTASIAN.get(version, []):
        table.append((start, end, 2))

    for start, end in ZERO_WIDTH.get(version, []):
        table.append((start, end, 0))

    table.sort()

    src = '\n'.join([
        'from ..cells import CellTable',
        '',
        '',
        '##',
        '',
        '',
        'CELL_TABLE = CellTable(',
        f'    {version!r},',
        '    [',
        *[
            f'        {t!r},'
            for t in table
        ],
        '    ],',
        '    frozenset([',
        *[
            f'        {s!r},'
            for s in sorted(narrow_to_wide)
        ],
        '    ])',
        ')',
    ])

    with open(os.path.join(os.path.dirname(__file__), '../unicode.py'), 'w') as f:
        f.write(src)


if __name__ == '__main__':
    _main()
