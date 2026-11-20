# Repair the CSV category-total command

This little project has a library in `totals.py` and a CLI in `cli.py`. The CLI
currently splits raw commas, and the library performs money arithmetic with floats.
Fix both paths to implement the following behavior.

Library API: `totals.sum_amounts(rows)` accepts an iterable of mappings containing
`category` and `amount` strings. Strip surrounding whitespace from both fields;
reject empty categories and invalid or non-finite amounts with `ValueError`.
Use exact decimal arithmetic and return `dict[str, Decimal]`. Negative amounts
are valid. Categories remain case-sensitive. An empty input returns `{}`.
You may assume at most 1,000 rows, with amounts in ordinary decimal notation
(no exponent) and at most twelve integer digits and six fractional digits.

CLI API: `python cli.py [PATH]` reads UTF-8 CSV from PATH, or stdin when PATH is
omitted or `-`. The required header columns are `category` and `amount`, in any
order, with additional columns permitted. Use normal CSV quoting rules, including
commas and line breaks inside quoted fields. Reject missing required headers,
short/long rows, and invalid data.

Print one JSON object on success, sorting category keys and formatting each sum
as a string with exactly two digits after the decimal point. Round using decimal
ROUND_HALF_UP only after summing each category. For example, two amounts of
`0.005` in one category produce `"0.01"`. Preserve non-ASCII category text. Print
only the JSON object and a newline to stdout, and leave stderr empty on success.

On a bad input, print a concise diagnostic to stderr, exit with code 2, and leave
stdout empty. Use only the Python standard library. Fix the files in `/work`.
Run the existing basic checks with `python -m unittest -v test_visible`.
