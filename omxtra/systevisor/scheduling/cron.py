# ruff: noqa: UP006 UP007 UP017 UP045
import dataclasses as dc
import datetime
import typing as ta


##


_SYSTEVISOR_CRON_SEARCH_YEARS = 8


class SystevisorCronError(ValueError):
    pass


@dc.dataclass(frozen=True)
class SystevisorCronField:
    values: ta.AbstractSet[int]
    wildcard: bool

    def matches(self, value: int) -> bool:
        return value in self.values


@dc.dataclass(frozen=True)
class SystevisorCronExpression:
    source: str
    minute: SystevisorCronField
    hour: SystevisorCronField
    day_of_month: SystevisorCronField
    month: SystevisorCronField
    day_of_week: SystevisorCronField

    def _matches_day(self, value: datetime.datetime) -> bool:
        cron_weekday = (value.weekday() + 1) % 7
        day_of_month_matches = self.day_of_month.matches(value.day)
        day_of_week_matches = self.day_of_week.matches(cron_weekday)
        if self.day_of_month.wildcard and self.day_of_week.wildcard:
            return True
        if self.day_of_month.wildcard:
            return day_of_week_matches
        if self.day_of_week.wildcard:
            return day_of_month_matches
        return day_of_month_matches or day_of_week_matches

    def matches_datetime(self, value: datetime.datetime) -> bool:
        return (
            self.minute.matches(value.minute) and
            self.hour.matches(value.hour) and
            self.month.matches(value.month) and
            self._matches_day(value)
        )

    # Both searches move a whole field at a time - past a month, a day, an hour - rather than a minute at a time, so
    # their cost does not depend on how sparse the expression is or how far away the answer lies. Eight years covers
    # the longest gap a satisfiable expression can have, between two leap days across a skipped leap year.

    def next_after(self, wall_time: float) -> float:
        """The first occurrence in a minute later than the one containing the given time."""

        minute = datetime.timedelta(minutes=1)
        try:
            current = datetime.datetime.fromtimestamp(wall_time, datetime.timezone.utc)
            current = current.replace(second=0, microsecond=0) + minute
            limit_year = current.year + _SYSTEVISOR_CRON_SEARCH_YEARS
            while current.year <= limit_year:
                if not self.month.matches(current.month):
                    current = (current.replace(day=1, hour=0, minute=0) + datetime.timedelta(days=32)).replace(day=1)
                elif not self._matches_day(current):
                    current = current.replace(hour=0, minute=0) + datetime.timedelta(days=1)
                elif not self.hour.matches(current.hour):
                    current = current.replace(minute=0) + datetime.timedelta(hours=1)
                elif not self.minute.matches(current.minute):
                    current += minute
                else:
                    return current.timestamp()
        except (OverflowError, OSError, ValueError) as exc:
            raise SystevisorCronError(f'time is out of range for {self.source!r}: {wall_time!r}') from exc
        raise SystevisorCronError(f'no occurrence found within eight years for {self.source!r}')

    def previous_at_or_before(self, wall_time: float) -> float:
        """The last occurrence in a minute no later than the one containing the given time."""

        minute = datetime.timedelta(minutes=1)
        try:
            current = datetime.datetime.fromtimestamp(wall_time, datetime.timezone.utc)
            current = current.replace(second=0, microsecond=0)
            limit_year = current.year - _SYSTEVISOR_CRON_SEARCH_YEARS
            while current.year >= limit_year:
                if not self.month.matches(current.month):
                    current = current.replace(day=1, hour=0, minute=0) - minute
                elif not self._matches_day(current):
                    current = current.replace(hour=0, minute=0) - minute
                elif not self.hour.matches(current.hour):
                    current = current.replace(minute=0) - minute
                elif not self.minute.matches(current.minute):
                    current -= minute
                else:
                    return current.timestamp()
        except (OverflowError, OSError, ValueError) as exc:
            raise SystevisorCronError(f'time is out of range for {self.source!r}: {wall_time!r}') from exc
        raise SystevisorCronError(f'no occurrence found within eight years for {self.source!r}')


def _systevisor_cron_parse_int(value: str, minimum: int, maximum: int, field_name: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise SystevisorCronError(f'invalid {field_name} value: {value!r}') from exc
    if not minimum <= number <= maximum:
        raise SystevisorCronError(
            f'{field_name} value {number} is outside {minimum}..{maximum}',
        )
    return number


def _systevisor_cron_parse_field(
        source: str,
        minimum: int,
        maximum: int,
        field_name: str,
        *,
        sunday_seven: bool = False,
) -> SystevisorCronField:
    if not source:
        raise SystevisorCronError(f'empty {field_name} field')
    values: ta.Set[int] = set()
    wildcard = source == '*'
    for part in source.split(','):
        base, separator, step_source = part.partition('/')
        step = _systevisor_cron_parse_int(step_source, 1, maximum - minimum + 1, field_name) if separator else 1
        if base == '*':
            start, end = minimum, maximum
        elif '-' in base:
            start_source, end_source = base.split('-', 1)
            start = _systevisor_cron_parse_int(start_source, minimum, maximum, field_name)
            end = _systevisor_cron_parse_int(end_source, minimum, maximum, field_name)
            if end < start:
                raise SystevisorCronError(f'descending {field_name} range: {base!r}')
        else:
            start = _systevisor_cron_parse_int(base, minimum, maximum, field_name)
            end = maximum if separator else start
        values.update(range(start, end + 1, step))
    if sunday_seven and 7 in values:
        values.remove(7)
        values.add(0)
    return SystevisorCronField(values=frozenset(values), wildcard=wildcard)


def systevisor_parse_cron(source: str) -> SystevisorCronExpression:
    fields = source.split()
    if len(fields) != 5:
        raise SystevisorCronError('cron expression must contain minute, hour, day-of-month, month, and day-of-week')
    return SystevisorCronExpression(
        source=source,
        minute=_systevisor_cron_parse_field(fields[0], 0, 59, 'minute'),
        hour=_systevisor_cron_parse_field(fields[1], 0, 23, 'hour'),
        day_of_month=_systevisor_cron_parse_field(fields[2], 1, 31, 'day-of-month'),
        month=_systevisor_cron_parse_field(fields[3], 1, 12, 'month'),
        day_of_week=_systevisor_cron_parse_field(fields[4], 0, 7, 'day-of-week', sunday_seven=True),
    )
