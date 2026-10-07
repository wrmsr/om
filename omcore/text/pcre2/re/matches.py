import operator
import typing as ta

from .... import lang
from .groups import GroupInfo
from .subjects import Subject
from .templates import expand_template
from .templates import parse_template


if ta.TYPE_CHECKING:
    from .patterns import Pattern


##


class Match(lang.Final, ta.Generic[ta.AnyStr]):
    """
    The counterpart of `re.Match`: what a pattern matched, and where.

    It holds the offsets PCRE2 reported, which for a str subject are offsets into its UTF-8, and translates them into
    what `re` reports - characters - only when they are asked for.
    """

    def __init__(
            self,
            pattern: Pattern[ta.AnyStr],
            groups: GroupInfo,
            subject: Subject,
            ovector: ta.Sequence[int],
            *,
            pos: int,
            endpos: int,
    ) -> None:
        super().__init__()

        self._pattern: Pattern[ta.AnyStr] = pattern
        self._groups = groups
        self._subject = subject
        self._ovector = ovector
        self._pos = pos
        self._endpos = endpos

    #

    @property
    def re(self) -> Pattern[ta.AnyStr]:
        return self._pattern

    @property
    def string(self) -> ta.AnyStr:
        return self._subject.string

    @property
    def pos(self) -> int:
        return self._pos

    @property
    def endpos(self) -> int:
        return self._endpos

    #

    def _resolve_group(self, group: ta.Any) -> int:
        if isinstance(group, str):
            try:
                return self._groups.index[group]
            except KeyError:
                raise IndexError('no such group') from None

        try:
            number = operator.index(group)
        except TypeError:
            raise IndexError('no such group') from None
        if not (0 <= number <= self._groups.num_groups):
            raise IndexError('no such group')
        return number

    def _get_group(self, number: int) -> ta.Any:
        start = self._ovector[2 * number]
        if start < 0:
            return None
        return self._subject.slice(start, self._ovector[2 * number + 1])

    def group(self, *groups: ta.Any) -> ta.Any:
        if not groups:
            return self._get_group(0)
        if len(groups) == 1:
            return self._get_group(self._resolve_group(groups[0]))
        return tuple(self._get_group(self._resolve_group(group)) for group in groups)

    def __getitem__(self, group: ta.Any) -> ta.Any:
        return self._get_group(self._resolve_group(group))

    def groups(self, default: ta.Any = None) -> tuple[ta.Any, ...]:
        return tuple(
            default if (value := self._get_group(number)) is None else value
            for number in range(1, self._groups.num_groups + 1)
        )

    def groupdict(self, default: ta.Any = None) -> dict[str, ta.Any]:
        return {
            name: default if (value := self._get_group(number)) is None else value
            for name, number in self._groups.index.items()
        }

    #

    def start(self, group: ta.Any = 0) -> int:
        start = self._ovector[2 * self._resolve_group(group)]
        return self._subject.to_offset(start) if start >= 0 else -1

    def end(self, group: ta.Any = 0) -> int:
        end = self._ovector[2 * self._resolve_group(group) + 1]
        return self._subject.to_offset(end) if end >= 0 else -1

    def span(self, group: ta.Any = 0) -> tuple[int, int]:
        return (self.start(group), self.end(group))

    @property
    def regs(self) -> tuple[tuple[int, int], ...]:
        return tuple(self.span(number) for number in range(self._groups.num_groups + 1))

    #

    @property
    def lastindex(self) -> int | None:
        # The group which closed last is not something PCRE2 reports, but it can be told from what it does: the group
        # must have taken part, none which did can end after it, and of those ending where it does the one closing
        # last is the one whose closing parenthesis comes last in the pattern.
        best: tuple[int, int] | None = None
        last: int | None = None
        for number in range(1, self._groups.num_groups + 1):
            if self._ovector[2 * number] < 0:
                continue
            key = (self._ovector[2 * number + 1], self._groups.close_ranks[number - 1])
            if best is None or key > best:
                best = key
                last = number
        return last

    @property
    def lastgroup(self) -> str | None:
        if (last := self.lastindex) is None:
            return None
        return self._groups.names.get(last)

    #

    def expand(self, template: ta.AnyStr) -> ta.AnyStr:
        parsed = parse_template(
            template,
            num_groups=self._groups.num_groups,
            group_index=self._groups.index,
        )
        return expand_template(parsed, self._get_group, is_str=isinstance(template, str))

    #

    def __repr__(self) -> str:
        package = type(self).__module__.rpartition('.')[0]
        return f'<{package}.{type(self).__qualname__} object; span={self.span()!r}, match={self.group()!r}>'

    def __copy__(self) -> ta.Self:
        return self

    def __deepcopy__(self, memo: ta.Any) -> ta.Self:
        return self
