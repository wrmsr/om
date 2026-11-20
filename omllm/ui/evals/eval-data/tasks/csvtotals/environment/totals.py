import typing as ta


##


def sum_amounts(rows: ta.Iterable[ta.Mapping[str, str]]) -> dict[str, float]:
    result: dict[str, float] = {}
    for row in rows:
        category = row['category']
        result[category] = result.get(category, 0.0) + float(row['amount'])
    return result
