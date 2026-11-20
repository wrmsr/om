import decimal
import typing as ta


##


def sum_amounts(rows: ta.Iterable[ta.Mapping[str, str]]) -> dict[str, decimal.Decimal]:
    result: dict[str, decimal.Decimal] = {}
    for row in rows:
        category = row['category'].strip()
        if not category:
            raise ValueError('empty category')
        try:
            amount = decimal.Decimal(row['amount'].strip())
        except decimal.InvalidOperation as exc:
            raise ValueError('invalid amount') from exc
        if not amount.is_finite():
            raise ValueError('non-finite amount')
        result[category] = result.get(category, decimal.Decimal(0)) + amount
    return result
