import argparse
import csv
import decimal
import json
import sys
import typing as ta

from totals import sum_amounts


##


def _read_rows(file: ta.TextIO) -> list[dict[str, str]]:
    reader = csv.DictReader(file, strict=True)
    if reader.fieldnames is None or not {'category', 'amount'} <= set(reader.fieldnames):
        raise ValueError('expected category and amount headers')

    rows = []
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise ValueError('incorrect number of columns')
        rows.append(row)
    return rows


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('path', nargs='?', default='-')
    args = parser.parse_args()

    try:
        if args.path == '-':
            rows = _read_rows(sys.stdin)
        else:
            with open(args.path, encoding='utf-8', newline='') as file:
                rows = _read_rows(file)
        totals = sum_amounts(rows)
        formatted = {
            key: format(value.quantize(decimal.Decimal('0.01'), rounding=decimal.ROUND_HALF_UP), '.2f')
            for key, value in totals.items()
        }
    except (OSError, UnicodeError, ValueError, csv.Error, decimal.DecimalException) as exc:
        print(f'invalid input: {exc}', file=sys.stderr)
        raise SystemExit(2) from None

    print(json.dumps(formatted, sort_keys=True, ensure_ascii=False))


if __name__ == '__main__':
    _main()
