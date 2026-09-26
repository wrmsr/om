"""
A generic, sans-IO serde for the AWS REST-XML protocol, driven entirely by the wire metadata on generated model shapes
and operations. Knows nothing of any particular service - S3's quirks live elsewhere.

Depends only on the stdlib, omcore, the generated model base, and the signer's URI encoding, so it can move into
ominfra.clouds.aws unchanged.
"""
import base64
import collections.abc
import enum
import re
import types
import typing as ta
import xml.etree.ElementTree as ET  # noqa

from omcore import check
from omcore import dataclasses as dc
from omcore import lang
from ominfra.clouds.aws import auth as aws_auth
from ominfra.clouds.aws.models import base as _base


##


@dc.dataclass(frozen=True, kw_only=True)
class RestXmlRequest:
    method: str
    path: str  # percent-encoded, starts with '/', uri labels expanded
    query: ta.Sequence[tuple[str, str | None]]  # decoded pairs; a None value is a valueless key ('uploads')
    headers: ta.Sequence[tuple[str, str]]
    body: bytes | None


@dc.dataclass(frozen=True, kw_only=True)
class RestXmlError:
    status: int
    code: str | None
    message: str | None
    request_id: str | None
    host_id: str | None
    raw: bytes


##


class RestXmlKind(enum.Enum):
    STR = enum.auto()
    INT = enum.auto()
    FLOAT = enum.auto()
    BOOL = enum.auto()
    BYTES = enum.auto()
    ENUM = enum.auto()
    SHAPE = enum.auto()
    LIST = enum.auto()
    MAP = enum.auto()
    UNSUPPORTED = enum.auto()  # fails only if a value is actually present


@dc.dataclass(frozen=True, kw_only=True)
class RestXmlType:
    kind: RestXmlKind
    cls: type | None = None  # the enum or shape class
    elem: RestXmlType | None = None  # list element / map value
    key: RestXmlType | None = None  # map key


@dc.dataclass(frozen=True, kw_only=True)
class RestXmlField:
    name: str  # the dataclass field name
    member_name: str
    wire_name: str  # serialization name, else member name
    type: RestXmlType
    location: str | None
    xml_namespace: str | None
    xml_flattened: bool
    xml_attribute: bool
    list_member_name: str | None
    required: bool


def _unwrap_optional(t: ta.Any) -> ta.Any:
    if ta.get_origin(t) in (types.UnionType, ta.Union):
        return check.single([a for a in ta.get_args(t) if a is not type(None)])
    return t


def _analyze_type(t: ta.Any) -> RestXmlType:
    t = _unwrap_optional(t)
    while isinstance(t, ta.NewType):
        t = t.__supertype__
    if isinstance(t, type):
        if issubclass(t, _base.Shape):
            return RestXmlType(kind=RestXmlKind.SHAPE, cls=t)
        if issubclass(t, enum.Enum):
            return RestXmlType(kind=RestXmlKind.ENUM, cls=t)
        if issubclass(t, bool):
            return RestXmlType(kind=RestXmlKind.BOOL)
        if issubclass(t, int):
            return RestXmlType(kind=RestXmlKind.INT)
        if issubclass(t, float):
            return RestXmlType(kind=RestXmlKind.FLOAT)
        if issubclass(t, bytes):
            return RestXmlType(kind=RestXmlKind.BYTES)
        if issubclass(t, str):
            return RestXmlType(kind=RestXmlKind.STR)
    origin = ta.get_origin(t)
    if isinstance(origin, type):
        args = ta.get_args(t)
        if issubclass(origin, collections.abc.Mapping):
            k, v = args
            return RestXmlType(kind=RestXmlKind.MAP, key=_analyze_type(k), elem=_analyze_type(v))
        if issubclass(origin, collections.abc.Sequence):
            return RestXmlType(kind=RestXmlKind.LIST, elem=_analyze_type(check.single(args)))
    return RestXmlType(kind=RestXmlKind.UNSUPPORTED, cls=t if isinstance(t, type) else None)


@lang.cached_function
def analyze_shape(cls: type[_base.Shape]) -> ta.Sequence[RestXmlField]:
    hints = ta.get_type_hints(cls)
    out: list[RestXmlField] = []
    for f in dc.fields(cls):
        md = f.metadata
        mn = md[_base.MEMBER_NAME]
        out.append(RestXmlField(
            name=f.name,
            member_name=mn,
            wire_name=md.get(_base.SERIALIZATION_NAME) or mn,
            type=_analyze_type(hints[f.name]),
            location=md.get(_base.LOCATION),
            xml_namespace=md.get(_base.XML_NAMESPACE),
            xml_flattened=bool(md.get(_base.XML_FLATTENED)),
            xml_attribute=bool(md.get(_base.XML_ATTRIBUTE)),
            list_member_name=md.get(_base.LIST_MEMBER_NAME),
            required=f.default is dc.MISSING and f.default_factory is dc.MISSING,
        ))
    return out


##


def _scalar_str(t: RestXmlType, v: ta.Any) -> str:
    match t.kind:
        case RestXmlKind.BOOL:
            return 'true' if v else 'false'
        case RestXmlKind.ENUM:
            return v.value if isinstance(v, enum.Enum) else str(v)
        case RestXmlKind.BYTES:
            return base64.b64encode(v).decode('ascii')
        case RestXmlKind.STR | RestXmlKind.INT | RestXmlKind.FLOAT:
            return str(v)
        case _:
            raise TypeError(f'not a scalar: {t!r}')


def _scalar_parse(t: RestXmlType, s: str) -> ta.Any:
    match t.kind:
        case RestXmlKind.STR:
            return s
        case RestXmlKind.INT:
            return int(s)
        case RestXmlKind.FLOAT:
            return float(s)
        case RestXmlKind.BOOL:
            return s.strip().lower() == 'true'
        case RestXmlKind.BYTES:
            return base64.b64decode(s)
        case RestXmlKind.ENUM:
            try:
                return check.not_none(t.cls)(s)
            except ValueError:
                # Services add enum values faster than models are regenerated - keep the raw value.
                return s
        case _:
            raise TypeError(f'not a scalar: {t!r}')


def _to_xml(parent: ET.Element, f: RestXmlField, t: RestXmlType, name: str, v: ta.Any) -> None:
    if t.kind == RestXmlKind.SHAPE:
        el = ET.SubElement(parent, name)
        _shape_to_xml(el, v)
    elif t.kind == RestXmlKind.LIST:
        elem = check.not_none(t.elem)
        if f.xml_flattened:
            for x in v:
                _to_xml(parent, f, elem, name, x)
        else:
            wrapper = ET.SubElement(parent, name)
            for x in v:
                _to_xml(wrapper, f, elem, f.list_member_name or 'member', x)
    elif t.kind == RestXmlKind.MAP:
        raise NotImplementedError('rest-xml map bodies')
    else:
        ET.SubElement(parent, name).text = _scalar_str(t, v)


def _shape_to_xml(el: ET.Element, shape: _base.Shape) -> None:
    for f in analyze_shape(type(shape)):
        if (v := getattr(shape, f.name)) is None:
            continue
        if f.location is not None:
            raise NotImplementedError(f'located member inside an xml body: {f.member_name}')
        if f.xml_attribute:
            el.set(f.wire_name, _scalar_str(f.type, v))
        else:
            _to_xml(el, f, f.type, f.wire_name, v)


_URI_LABEL_PAT = re.compile(r'\{([^}+]+)(\+?)\}')


def serialize_rest_xml_request(op: _base.Operation, req: _base.Shape) -> RestXmlRequest:
    uri = check.not_none(op.http_request_uri)
    path_tmpl, _, static_query = uri.partition('?')

    query: list[tuple[str, str | None]] = []
    for part in static_query.split('&') if static_query else []:
        k, eq, v = part.partition('=')
        query.append((k, v if eq else None))

    labels: dict[str, str] = {}
    headers: list[tuple[str, str]] = []
    body: bytes | None = None

    pm = type(req).__shape__.payload_member
    for f in analyze_shape(type(req)):
        if (v := getattr(req, f.name)) is None:
            continue

        if f.location == 'uri':
            labels[f.wire_name] = _scalar_str(f.type, v)

        elif f.location == 'querystring':
            if f.type.kind == RestXmlKind.LIST:
                query.extend((f.wire_name, _scalar_str(check.not_none(f.type.elem), x)) for x in v)
            elif f.type.kind == RestXmlKind.MAP:
                query.extend((str(k), _scalar_str(check.not_none(f.type.elem), x)) for k, x in v.items())
            else:
                query.append((f.wire_name, _scalar_str(f.type, v)))

        elif f.location == 'header':
            if f.type.kind == RestXmlKind.LIST:
                headers.append((f.wire_name, ','.join(_scalar_str(check.not_none(f.type.elem), x) for x in v)))
            else:
                headers.append((f.wire_name, _scalar_str(f.type, v)))

        elif f.location == 'headers':
            headers.extend((f.wire_name + str(k), _scalar_str(check.not_none(f.type.elem), x)) for k, x in v.items())

        elif f.location is None and f.member_name == pm:
            if f.type.kind == RestXmlKind.BYTES:
                body = bytes(v)
            elif f.type.kind == RestXmlKind.STR:
                body = v.encode('utf-8')
            elif f.type.kind == RestXmlKind.SHAPE:
                root = ET.Element(f.wire_name)
                if f.xml_namespace is not None:
                    root.set('xmlns', f.xml_namespace)
                _shape_to_xml(root, v)
                body = ET.tostring(root, encoding='utf-8', xml_declaration=False)
            else:
                raise TypeError(f'unsupported payload type: {f.type!r}')

        elif f.location is None:
            raise NotImplementedError(f'non-payload body member: {f.member_name}')

        else:
            raise NotImplementedError(f'unsupported location {f.location!r}: {f.member_name}')

    def render_label(m: re.Match) -> str:
        name, greedy = m[1], bool(m[2])
        try:
            v = labels[name]
        except KeyError:
            raise ValueError(f'missing uri label: {name}') from None
        return aws_auth.aws_uri_encode(v, encode_slash=not greedy)

    return RestXmlRequest(
        method=check.not_none(op.http_method),
        path=_URI_LABEL_PAT.sub(render_label, path_tmpl),
        query=query,
        headers=headers,
        body=body,
    )


##


def _strip_ns(tag: str) -> str:
    return tag.rpartition('}')[2]


def _children_by_tag(el: ET.Element) -> dict[str, list[ET.Element]]:
    out: dict[str, list[ET.Element]] = {}
    for c in el:
        out.setdefault(_strip_ns(c.tag), []).append(c)
    return out


def _from_xml(t: RestXmlType, el: ET.Element) -> ta.Any:
    if t.kind == RestXmlKind.SHAPE:
        return shape_from_xml(check.not_none(t.cls), el)
    return _scalar_parse(t, el.text or '')


def _attr(el: ET.Element, name: str) -> str | None:
    local = name.rpartition(':')[2]
    for k, v in el.attrib.items():
        if _strip_ns(k) == local:
            return v
    return None


def shape_from_xml(cls: type[_base.Shape], el: ET.Element) -> ta.Any:
    kids = _children_by_tag(el)
    kw: dict[str, ta.Any] = {}
    for f in analyze_shape(cls):
        if f.location is not None:
            continue
        if f.xml_attribute:
            if (a := _attr(el, f.wire_name)) is not None:
                kw[f.name] = _scalar_parse(f.type, a)
            continue
        if (cs := kids.get(f.wire_name)) is None:
            continue
        if f.type.kind == RestXmlKind.LIST:
            elem = check.not_none(f.type.elem)
            if f.xml_flattened:
                items = cs
            else:
                mn = f.list_member_name or 'member'
                items = [c for c in cs[0] if _strip_ns(c.tag) == mn]
            kw[f.name] = [_from_xml(elem, c) for c in items]
        elif f.type.kind == RestXmlKind.MAP:
            raise NotImplementedError('rest-xml map bodies')
        else:
            kw[f.name] = _from_xml(f.type, cs[0])
    return cls(**kw)


def _lower_headers(headers: ta.Mapping[str, ta.Sequence[str]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for k, vs in headers.items():
        out.setdefault(k.lower(), []).extend([vs] if isinstance(vs, str) else vs)
    return out


def deserialize_rest_xml_response(
        op: _base.Operation,
        *,
        status: int,
        headers: ta.Mapping[str, ta.Sequence[str]],
        body: bytes,
) -> ta.Any:
    """Returns an instance of the operation's output shape, or None if it has none."""

    if (cls := op.output) is None:
        return None

    lh = _lower_headers(headers)
    pm = cls.__shape__.payload_member
    kw: dict[str, ta.Any] = {}
    body_fields: list[RestXmlField] = []

    for f in analyze_shape(cls):
        if f.location == 'header':
            if (vs := lh.get(f.wire_name.lower())) is not None:
                if f.type.kind == RestXmlKind.LIST:
                    elem = check.not_none(f.type.elem)
                    kw[f.name] = [_scalar_parse(elem, x.strip()) for v in vs for x in v.split(',')]
                else:
                    kw[f.name] = _scalar_parse(f.type, ','.join(vs))

        elif f.location == 'headers':
            prefix = f.wire_name.lower()
            elem = check.not_none(f.type.elem)
            m = {k[len(prefix):]: _scalar_parse(elem, ','.join(vs)) for k, vs in lh.items() if k.startswith(prefix)}
            if m:
                kw[f.name] = m

        elif f.location == 'statusCode':
            kw[f.name] = status

        elif f.location is None:
            if f.member_name == pm:
                if f.type.kind == RestXmlKind.BYTES:
                    kw[f.name] = body
                elif f.type.kind == RestXmlKind.STR:
                    kw[f.name] = body.decode('utf-8')
                elif f.type.kind == RestXmlKind.SHAPE:
                    if body.strip():
                        kw[f.name] = shape_from_xml(check.not_none(f.type.cls), ET.fromstring(body))  # noqa: S314
                else:
                    raise TypeError(f'unsupported payload type: {f.type!r}')
            else:
                body_fields.append(f)

    if body_fields and body.strip():
        root = ET.fromstring(body)  # noqa: S314
        parsed = shape_from_xml(cls, root)
        for f in body_fields:
            if (v := getattr(parsed, f.name)) is not None:
                kw[f.name] = v

    return cls(**kw)


##


def parse_rest_xml_error(*, status: int, headers: ta.Mapping[str, ta.Sequence[str]], body: bytes) -> RestXmlError:
    code = message = request_id = host_id = None
    if body.strip():
        try:
            root = ET.fromstring(body)  # noqa: S314
        except ET.ParseError:
            root = None
        if root is not None:
            err = root if _strip_ns(root.tag) == 'Error' else next(
                (c for c in root.iter() if _strip_ns(c.tag) == 'Error'),
                None,
            )
            if err is not None:
                kids = _children_by_tag(err)

                def text(n: str) -> str | None:
                    return kids[n][0].text if n in kids else None

                code = text('Code')
                message = text('Message')
                request_id = text('RequestId')
                host_id = text('HostId')

    lh = _lower_headers(headers)
    if request_id is None and (v := lh.get('x-amz-request-id')):
        request_id = v[0]
    if host_id is None and (v := lh.get('x-amz-id-2')):
        host_id = v[0]

    return RestXmlError(
        status=status,
        code=code,
        message=message,
        request_id=request_id,
        host_id=host_id,
        raw=body,
    )
