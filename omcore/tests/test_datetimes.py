# ruff: noqa: PT009 UP017
# @om-lite
import datetime
import unittest

from ..datetimes import months_ago
from ..datetimes import parse_date
from ..datetimes import parse_timedelta
from ..datetimes import to_seconds


class TestDatetimes(unittest.TestCase):
    def test_to_seconds(self):
        for value in [
            datetime.timedelta(),
            datetime.timedelta(days=2, seconds=3, microseconds=4),
            datetime.timedelta(microseconds=-1),
        ]:
            self.assertEqual(to_seconds(value), value.total_seconds())

    def test_months_ago(self):
        date = datetime.date(2024, 1, 31)
        self.assertEqual(months_ago(date, 1), datetime.date(2023, 12, 1))
        self.assertEqual(months_ago(date, 13), datetime.date(2022, 12, 1))
        self.assertEqual(months_ago(date, -13), datetime.date(2025, 2, 1))

    def test_parse_date(self):
        self.assertEqual(parse_date('2024-02-29'), datetime.date(2024, 2, 29))

        before = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(days=2)
        parsed = parse_date('2 days ago', tz=datetime.timezone.utc)
        after = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(days=2)
        parsed_date = parsed.date() if isinstance(parsed, datetime.datetime) else parsed
        self.assertLessEqual(before.date(), parsed_date)
        self.assertLessEqual(parsed_date, after.date())

    def test_parse_timedelta(self):
        values = {
            '1 day, 2:03:04.5': datetime.timedelta(days=1, hours=2, minutes=3, seconds=4.5),
            '-1 day, 23:59:59': datetime.timedelta(seconds=-1),
            '1d, 2h, 3m, 4.5s': datetime.timedelta(days=1, hours=2, minutes=3, seconds=4.5),
            '-1h 30m': -datetime.timedelta(hours=1, minutes=30),
        }
        for value, expected in values.items():
            self.assertEqual(parse_timedelta(value), expected)

        for value in ['', '1', 'nonsense']:
            with self.assertRaises(ValueError):
                parse_timedelta(value)
