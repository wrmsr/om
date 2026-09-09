import functools
import re

from omcore import dataclasses as dc


##


_VERSION_PATTERN = re.compile(
    r'^(?:v|=)?'
    r'(?P<major>0|[1-9][0-9]*)\.(?P<minor>0|[1-9][0-9]*)\.(?P<patch>0|[1-9][0-9]*)'
    r'(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?'
    r'(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$',
)

_PARTIAL_PATTERN = re.compile(
    r'^(?P<major>0|[1-9][0-9]*|[xX*])'
    r'(?:\.(?P<minor>0|[1-9][0-9]*|[xX*])'
    r'(?:\.(?P<patch>0|[1-9][0-9]*|[xX*])'
    r'(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?'
    r'(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?'
    r')?)?$',
)


@dc.dataclass(frozen=True)
class Version:
    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...] = ()
    build: tuple[str, ...] = ()


@dc.dataclass(frozen=True)
class _PartialVersion:
    major: int | None
    minor: int | None
    patch: int | None
    prerelease: tuple[str, ...]
    build: tuple[str, ...]


@dc.dataclass(frozen=True)
class _Comparator:
    operator: str
    version: Version


def _identifiers(value: str | None, /) -> tuple[str, ...]:
    if value is None:
        return ()

    identifiers = tuple(value.split('.'))
    if any(
            identifier.isdigit() and len(identifier) > 1 and identifier.startswith('0')
            for identifier in identifiers
    ):
        raise ValueError(f'Invalid numeric semantic-version identifier: {value}')

    return identifiers


def parse(value: str, /) -> Version:
    match = _VERSION_PATTERN.fullmatch(value.strip())
    if match is None:
        raise ValueError(f'Invalid semantic version: {value}')

    return Version(
        major=int(match['major']),
        minor=int(match['minor']),
        patch=int(match['patch']),
        prerelease=_identifiers(match['prerelease']),
        build=tuple(match['build'].split('.')) if match['build'] is not None else (),
    )


def compare(left: Version, right: Version, /) -> int:
    left_core = (left.major, left.minor, left.patch)
    right_core = (right.major, right.minor, right.patch)
    if left_core != right_core:
        return (left_core > right_core) - (left_core < right_core)

    if not left.prerelease or not right.prerelease:
        return (not left.prerelease) - (not right.prerelease)

    for left_identifier, right_identifier in zip(left.prerelease, right.prerelease, strict=False):
        if left_identifier == right_identifier:
            continue

        left_numeric = left_identifier.isdigit()
        right_numeric = right_identifier.isdigit()

        if left_numeric and right_numeric:
            return (int(left_identifier) > int(right_identifier)) - (int(left_identifier) < int(right_identifier))

        if left_numeric != right_numeric:
            return -1 if left_numeric else 1

        return (left_identifier > right_identifier) - (left_identifier < right_identifier)

    return (len(left.prerelease) > len(right.prerelease)) - (len(left.prerelease) < len(right.prerelease))


def sort_versions(values: list[str], /, *, reverse: bool = False) -> list[str]:
    parsed = {value: parse(value) for value in values}

    def compare_values(left: str, right: str) -> int:
        return compare(parsed[left], parsed[right])

    return sorted(
        values,
        key=functools.cmp_to_key(compare_values),
        reverse=reverse,
    )


def _partial_identifier(value: str | None, /) -> int | None:
    if value is None or value in {'x', 'X', '*'}:
        return None
    return int(value)


def _parse_partial(value: str, /) -> _PartialVersion:
    match = _PARTIAL_PATTERN.fullmatch(value.strip().removeprefix('v'))
    if match is None:
        raise ValueError(f'Invalid semantic-version range component: {value}')

    major = _partial_identifier(match['major'])
    minor = _partial_identifier(match['minor'])
    patch = _partial_identifier(match['patch'])

    if major is None and (minor is not None or patch is not None):
        raise ValueError(f'Invalid semantic-version wildcard: {value}')
    if minor is None and patch is not None:
        raise ValueError(f'Invalid semantic-version wildcard: {value}')
    if match['prerelease'] is not None and patch is None:
        raise ValueError(f'Prerelease requires a complete semantic version: {value}')

    return _PartialVersion(
        major=major,
        minor=minor,
        patch=patch,
        prerelease=_identifiers(match['prerelease']),
        build=tuple(match['build'].split('.')) if match['build'] is not None else (),
    )


def _minimum(partial: _PartialVersion, /) -> Version:
    return Version(
        major=partial.major or 0,
        minor=partial.minor or 0,
        patch=partial.patch or 0,
        prerelease=partial.prerelease,
        build=partial.build,
    )


def _partial_upper(partial: _PartialVersion, /) -> Version | None:
    if partial.major is None:
        return None
    if partial.minor is None:
        return Version(partial.major + 1, 0, 0)
    if partial.patch is None:
        return Version(partial.major, partial.minor + 1, 0)
    return None


def _expand_partial(partial: _PartialVersion, /) -> tuple[_Comparator, ...]:
    upper = _partial_upper(partial)

    if upper is None:
        if partial.major is None:
            return ()

        return (_Comparator('=', _minimum(partial)),)

    return (_Comparator('>=', _minimum(partial)), _Comparator('<', upper))


def _expand_caret(partial: _PartialVersion, /) -> tuple[_Comparator, ...]:
    if partial.major is None:
        return ()

    lower = _minimum(partial)

    if partial.major > 0:
        upper = Version(partial.major + 1, 0, 0)

    elif partial.minor is None:
        upper = Version(1, 0, 0)

    elif partial.minor > 0:
        upper = Version(0, partial.minor + 1, 0)

    elif partial.patch is None:
        upper = Version(0, 1, 0)

    else:
        upper = Version(0, 0, partial.patch + 1)

    return (_Comparator('>=', lower), _Comparator('<', upper))


def _expand_tilde(partial: _PartialVersion, /) -> tuple[_Comparator, ...]:
    if partial.major is None:
        return ()

    lower = _minimum(partial)

    if partial.minor is None:
        upper = Version(partial.major + 1, 0, 0)

    else:
        upper = Version(partial.major, partial.minor + 1, 0)

    return (_Comparator('>=', lower), _Comparator('<', upper))


def _expand_primitive(operator: str, partial: _PartialVersion, /) -> tuple[_Comparator, ...]:
    if operator in {'', '='}:
        return _expand_partial(partial)

    minimum = _minimum(partial)
    upper = _partial_upper(partial)

    if operator == '>':
        if partial.major is None:
            raise ValueError('An open lower bound cannot be a wildcard')
        return (_Comparator('>=', upper),) if upper is not None else (_Comparator('>', minimum),)

    if operator == '>=':
        if partial.major is None:
            return ()
        return (_Comparator('>=', minimum),)

    if operator == '<':
        if partial.major is None:
            raise ValueError('An upper bound cannot be a wildcard')
        return (_Comparator('<', minimum),)

    if operator == '<=':
        if partial.major is None:
            return ()
        return (_Comparator('<', upper),) if upper is not None else (_Comparator('<=', minimum),)

    raise ValueError(f'Invalid semantic-version operator: {operator}')


def _expand_simple(value: str, /) -> tuple[_Comparator, ...]:
    if value.startswith('^'):
        return _expand_caret(_parse_partial(value[1:]))
    if value.startswith('~'):
        return _expand_tilde(_parse_partial(value[1:]))

    match = re.fullmatch(r'(<=|>=|<|>|=)?(.+)', value)
    if match is None:
        raise ValueError(f'Invalid semantic-version range component: {value}')
    return _expand_primitive(match[1] or '', _parse_partial(match[2]))


def _expand_hyphen(lower_value: str, upper_value: str, /) -> tuple[_Comparator, ...]:
    lower = _parse_partial(lower_value)
    upper = _parse_partial(upper_value)
    comparators: list[_Comparator] = []

    if lower.major is not None:
        comparators.append(_Comparator('>=', _minimum(lower)))

    upper_limit = _partial_upper(upper)

    if upper_limit is not None:
        comparators.append(_Comparator('<', upper_limit))

    elif upper.major is not None:
        comparators.append(_Comparator('<=', _minimum(upper)))

    return tuple(comparators)


def _parse_set(value: str, /) -> tuple[_Comparator, ...]:
    value = re.sub(r'([~^]|<=|>=|<|>|=)\s+', r'\1', value.strip())
    hyphen = re.fullmatch(r'(.+?)\s+-\s+(.+)', value)
    if hyphen is not None:
        return _expand_hyphen(hyphen[1], hyphen[2])
    if not value:
        return ()
    return tuple(comparator for token in value.split() for comparator in _expand_simple(token))


def _test_comparator(version: Version, comparator: _Comparator, /) -> bool:
    difference = compare(version, comparator.version)
    return {
        '=': difference == 0,
        '>': difference > 0,
        '>=': difference >= 0,
        '<': difference < 0,
        '<=': difference <= 0,
    }[comparator.operator]


def satisfies(version: str | Version, expression: str, /) -> bool:
    parsed = parse(version) if isinstance(version, str) else version

    for range_value in expression.split('||'):
        comparators = _parse_set(range_value)

        if not all(_test_comparator(parsed, comparator) for comparator in comparators):
            continue

        if parsed.prerelease and not any(
                comparator.version.prerelease and
                (comparator.version.major, comparator.version.minor, comparator.version.patch) ==
                (parsed.major, parsed.minor, parsed.patch)
                for comparator in comparators
        ):
            continue

        return True

    return False
