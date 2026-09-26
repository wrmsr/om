import enum
import typing as ta

from omcore import cached
from omcore import check
from omcore import collections as col
from omcore import dataclasses as dc
from omcore import lang


DateTime = ta.NewType('DateTime', str)
MillisecondDateTime = ta.NewType('MillisecondDateTime', str)

Timestamp = ta.NewType('Timestamp', str)


##


@dc.dataclass(frozen=True)
class Tag:
    key: str
    value: str


TagList: ta.TypeAlias = ta.Sequence[Tag]


##


class ValueType(lang.Abstract):
    pass


@dc.dataclass(frozen=True)
class ListValueType(ValueType):
    e: type


@dc.dataclass(frozen=True)
class MapValueType(ValueType):
    k: type
    v: type


##


class Enum(enum.Enum):
    pass


##


class SHAPE_NAME(lang.Marker):  # noqa
    pass


def common_metadata(
        *,
        shape_name: str | None = None,
) -> dict[ta.Any, ta.Any]:
    md = {}

    if shape_name is not None:
        md[SHAPE_NAME] = shape_name

    return md


##


class PAYLOAD_MEMBER(lang.Marker):  # noqa
    pass


def shape_metadata(
        *,
        payload_member: str | None = None,
        **kwargs: ta.Any,
) -> dict[ta.Any, ta.Any]:
    md = {**common_metadata(**kwargs)}

    if payload_member is not None:
        md[PAYLOAD_MEMBER] = payload_member

    return md


class ShapeInfo:
    def __init__(
            self,
            cls: type[Shape],
            metadata: ta.Mapping[ta.Any, ta.Any],
    ) -> None:
        super().__init__()

        self._cls = check.issubclass(cls, Shape)
        self._metadata = metadata

    @property
    def cls(self) -> type[Shape]:
        return self._cls

    @property
    def metadata(self) -> ta.Mapping[ta.Any, ta.Any]:
        return self._metadata

    @property
    def payload_member(self) -> str | None:
        """The member name of the field which is the whole HTTP body, if any."""

        return self._metadata.get(PAYLOAD_MEMBER)

    @cached.property
    def payload_field(self) -> dc.Field | None:
        if (pm := self.payload_member) is None:
            return None
        return self.fields_by_member_name[pm]

    #

    @cached.property
    def fields(self) -> ta.Sequence[dc.Field]:
        check.state(dc.is_immediate_dataclass(self._cls))
        fls = dc.fields(self._cls)
        return fls  # noqa

    @cached.property
    def fields_by_name(self) -> ta.Mapping[str, dc.Field]:
        return col.make_map_by(lambda fl: fl.name, self.fields, strict=True)

    @cached.property
    def fields_by_member_name(self) -> ta.Mapping[str, dc.Field]:
        return col.make_map(
            [(n, f) for f in self.fields if (n := f.metadata.get(MEMBER_NAME)) is not None],
            strict=True,
        )

    @cached.property
    def fields_by_serialization_name(self) -> ta.Mapping[str, dc.Field]:
        l = []
        for f in self.fields:
            if sn := f.metadata.get(SERIALIZATION_NAME):
                l.append((sn, f))
            elif mn := f.metadata.get(MEMBER_NAME):
                l.append((mn, f))
        return col.make_map(l, strict=True)


@dc.dataclass(frozen=True, kw_only=True)
class Shape:
    __shape__: ta.ClassVar[ShapeInfo]

    def __init_subclass__(
            cls,
            *,
            shape_name: str | None = None,
            payload_member: str | None = None,
            **kwargs: ta.Any,
    ) -> None:
        super().__init_subclass__(**kwargs)

        check.state(not hasattr(cls, '__shape__'))

        info = ShapeInfo(
            cls,
            shape_metadata(
                shape_name=shape_name,
                payload_member=payload_member,
            ),
        )

        cls.__shape__ = info


##


class MEMBER_NAME(lang.Marker):  # noqa
    pass


class SERIALIZATION_NAME(lang.Marker):  # noqa
    pass


class VALUE_TYPE(lang.Marker):  # noqa
    pass


# Where a member travels in a REST request or response: 'uri', 'querystring', 'header', 'headers' (a prefixed map of
# headers), or 'statusCode'. Absent means the body.
class LOCATION(lang.Marker):  # noqa
    pass


class XML_NAMESPACE(lang.Marker):  # noqa
    pass


class XML_FLATTENED(lang.Marker):  # noqa
    pass


class XML_ATTRIBUTE(lang.Marker):  # noqa
    pass


# The element name of the items of a non-flattened list.
class LIST_MEMBER_NAME(lang.Marker):  # noqa
    pass


class TIMESTAMP_FORMAT(lang.Marker):  # noqa
    pass


class STREAMING(lang.Marker):  # noqa
    pass


#


def field_metadata(
        *,
        member_name: str | None = None,
        serialization_name: str | None = None,
        value_type: ValueType | None = None,
        location: str | None = None,
        xml_namespace: str | None = None,
        xml_flattened: bool = False,
        xml_attribute: bool = False,
        list_member_name: str | None = None,
        timestamp_format: str | None = None,
        streaming: bool = False,
        **kwargs: ta.Any,
) -> dict[ta.Any, ta.Any]:
    md = {**common_metadata(**kwargs)}

    if member_name is not None:
        md[MEMBER_NAME] = member_name
    if serialization_name is not None:
        md[SERIALIZATION_NAME] = serialization_name
    if value_type is not None:
        md[VALUE_TYPE] = value_type
    if location is not None:
        md[LOCATION] = location
    if xml_namespace is not None:
        md[XML_NAMESPACE] = xml_namespace
    if xml_flattened:
        md[XML_FLATTENED] = True
    if xml_attribute:
        md[XML_ATTRIBUTE] = True
    if list_member_name is not None:
        md[LIST_MEMBER_NAME] = list_member_name
    if timestamp_format is not None:
        md[TIMESTAMP_FORMAT] = timestamp_format
    if streaming:
        md[STREAMING] = True

    return md


##


@dc.dataclass(frozen=True, eq=False, kw_only=True)
class Operation:
    name: str

    input: type[Shape] | None = None
    output: type[Shape] | None = None

    errors: ta.Sequence[type[Shape]] | None = None

    http_method: str | None = None
    http_request_uri: str | None = None  # e.g. '/{Bucket}/{Key+}', or '/{Bucket}?list-type=2'
    http_response_code: int | None = None
