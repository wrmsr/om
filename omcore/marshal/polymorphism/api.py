import dataclasses as dc
import typing as ta

from ... import check
from ... import lang
from ... import metadata as md
from ..api.configs import Config
from ..api.errors import MarshalError
from ..api.naming import Naming
from ..api.naming import as_naming
from ..api.naming import translate_name


T = ta.TypeVar('T')


##


class PolymorphismTagError(MarshalError):
    pass


class PolymorphismSuffixError(MarshalError):
    pass


class PolymorphismSubtypeError(MarshalError):
    pass


class PolymorphismTaggingError(MarshalError):
    pass


##


@dc.dataclass(frozen=True)
class TypeTagging(Config, lang.Abstract, lang.Sealed):
    pass


@dc.dataclass(frozen=True)
class WrapperTypeTagging(TypeTagging, lang.Final):
    pass


@dc.dataclass(frozen=True)
class FieldTypeTagging(TypeTagging, lang.Final):
    field: str


#


SimpleTypeTagging: ta.TypeAlias = ta.Literal[
    'wrapper',
]


_SIMPLE_TYPE_TAGGING_MAP: ta.Mapping[SimpleTypeTagging, TypeTagging] = {
    'wrapper': WrapperTypeTagging(),
}


@ta.overload
def as_type_tagging(type_tagging: TypeTagging | SimpleTypeTagging) -> TypeTagging: ...


@ta.overload
def as_type_tagging(type_tagging: TypeTagging | SimpleTypeTagging | None) -> TypeTagging | None: ...


def as_type_tagging(type_tagging):
    if type_tagging is None:
        return None
    elif isinstance(type_tagging, TypeTagging):
        return type_tagging
    else:
        return _SIMPLE_TYPE_TAGGING_MAP[type_tagging]


##


SuffixStrippingMode: ta.TypeAlias = ta.Literal[
    'required',
    'if_all',
    'if_present',
]


@dc.dataclass(frozen=True)
class SuffixStripping(Config, lang.Final):
    suffix: str | None = None  # If `None` then the suffix will implicitly be the full base name

    _: dc.KW_ONLY

    mode: SuffixStrippingMode = 'if_all'  # Matches previous 'auto' behavior


#


SimpleSuffixStripping: ta.TypeAlias = ta.Literal[
    'required',
    'if_all',
    'if_present',
]


_SIMPLE_SUFFIX_STRIPPING_MAP: ta.Mapping[SimpleSuffixStripping, SuffixStripping] = {
    'required': SuffixStripping(mode='required'),
    'if_all': SuffixStripping(mode='if_all'),
    'if_present': SuffixStripping(mode='if_present'),
}


@ta.overload
def as_suffix_stripping(suffix_stripping: SuffixStripping | SimpleSuffixStripping) -> SuffixStripping: ...


@ta.overload
def as_suffix_stripping(suffix_stripping: SuffixStripping | SimpleSuffixStripping | None) -> SuffixStripping | None: ...


def as_suffix_stripping(suffix_stripping):
    if suffix_stripping is None:
        return None
    elif isinstance(suffix_stripping, SuffixStripping):
        return suffix_stripping
    else:
        return _SIMPLE_SUFFIX_STRIPPING_MAP[suffix_stripping]


##


@dc.dataclass(frozen=True)
class LazySubtype(lang.Final):
    """
    A not-yet-imported subtype: its fqcn (statically known, e.g. from its manifest) plus the thunk that loads it.
    Resolution is deferred all the way to first use of its wire tag - carrying one of these must never trigger an
    import.
    """

    fqcn: str
    resolve: ta.Callable[[], type]

    def __post_init__(self) -> None:
        check.non_empty_str(self.fqcn)


@dc.dataclass(frozen=True)
class SubtypeInfo(lang.Final):
    """One participant in a polymorphism - loaded or lazily declared - bound to its wire tag."""

    ty: type | LazySubtype
    tag: str
    alts: ta.AbstractSet[str] = frozenset()

    def __post_init__(self) -> None:
        if isinstance(self.ty, type):
            check.state(not lang.is_abstract(self.ty))
        else:
            check.isinstance(self.ty, LazySubtype)
        check.non_empty_str(self.tag)

        if not isinstance(self.alts, frozenset):
            object.__setattr__(self, 'alts', frozenset(check.not_isinstance(self.alts, str)))

    @property
    def cls(self) -> type | None:
        return self.ty if isinstance(self.ty, type) else None

    @property
    def fqcn(self) -> str | None:
        if isinstance(self.ty, LazySubtype):
            return self.ty.fqcn
        return lang.get_cls_fqcn(self.ty, optional=True)

    def resolve(self) -> type:
        if isinstance(self.ty, type):
            return self.ty
        return check.isinstance(self.ty.resolve(), type)


@dc.dataclass(frozen=True)
class SubtypeInfos(lang.Final):
    """Collection of subtype infos with cached lookups."""

    lst: ta.Sequence[SubtypeInfo]

    def __post_init__(self) -> None:
        if not isinstance(self.lst, tuple):
            object.__setattr__(self, 'lst', tuple(self.lst))
        for i in self.lst:
            check.isinstance(i, SubtypeInfo)

    def __iter__(self) -> ta.Iterator[SubtypeInfo]:
        return iter(self.lst)

    def __len__(self) -> int:
        return len(self.lst)

    def __bool__(self) -> bool:
        return bool(self.lst)

    # The index properties are lazily built and cached - this module is api-light and cannot afford the heavy
    # dataclass/caching machinery the analogous objects FieldInfos uses.

    @property
    def by_ty(self) -> ta.Mapping[type, SubtypeInfo]:
        """Concrete entries only - lazy entries have no type until resolved; see `lazy_by_fqcn`."""

        try:
            return self._by_ty  # type: ignore[attr-defined]
        except AttributeError:
            pass

        dct: dict[type, SubtypeInfo] = {}
        for i in self.lst:
            if (c := i.cls) is None:
                continue
            if c in dct:
                raise PolymorphismSubtypeError(f'Duplicate subtype: {c!r}')
            dct[c] = i

        object.__setattr__(self, '_by_ty', dct)
        return dct

    @property
    def lazy_by_fqcn(self) -> ta.Mapping[str, SubtypeInfo]:
        """Lazy entries only, by fqcn - concrete entries sharing a declared fqcn are a collection error."""

        try:
            return self._lazy_by_fqcn  # type: ignore[attr-defined]
        except AttributeError:
            pass

        cfs = {f for i in self.lst if i.cls is not None and (f := i.fqcn) is not None}

        dct: dict[str, SubtypeInfo] = {}
        for i in self.lst:
            if i.cls is not None:
                continue
            f = check.not_none(i.fqcn)
            if f in dct or f in cfs:
                raise PolymorphismSubtypeError(f'Duplicate subtype fqcn: {f!r}')
            dct[f] = i

        object.__setattr__(self, '_lazy_by_fqcn', dct)
        return dct

    @property
    def by_tag(self) -> ta.Mapping[str, SubtypeInfo]:
        try:
            return self._by_tag  # type: ignore[attr-defined]
        except AttributeError:
            pass

        dct: dict[str, SubtypeInfo] = {}
        for i in self.lst:
            for t in (i.tag, *i.alts):
                if t in dct:
                    raise PolymorphismSubtypeError(f'Duplicate subtype tag {t!r}: {dct[t].ty!r}, {i.ty!r}')
                dct[t] = i

        object.__setattr__(self, '_by_tag', dct)
        return dct


@dc.dataclass(frozen=True)
class Polymorphism(lang.Final):
    """The resolved product: a root and its tagged subtypes."""

    # Usually the root class, but reflected types (aliases and the like) remain legal for explicit-flavor matching.
    root: ta.Any

    subtypes: SubtypeInfos

    def __post_init__(self) -> None:
        check.isinstance(self.subtypes, SubtypeInfos)

        if isinstance(ty := self.root, type):
            # Lazy entries are necessarily unverifiable here - their targets are checked at resolve time.
            for i in self.subtypes:
                if (c := i.cls) is not None:
                    check.issubclass(c, ty)


@dc.dataclass(frozen=True)
class DisjointPolymorphism(lang.Final):
    """
    A merger of polymorphisms with unrelated roots, presenting their combined subtype and tag spaces as one - the
    `llm.Message | AgentMessage`-style union case. Constituent subtype resolution (and thus tag derivation) is entirely
    per-root, so a subtype's wire form is identical whether marshaled through its own root or through the merger. Root
    distinctness is lightly enforced here; the deep invariants - disjoint subtype sets and a collision-free combined tag
    space - are enforced by `merge_subtypes`.
    """

    polymorphisms: ta.Sequence[Polymorphism]

    def __post_init__(self) -> None:
        if not isinstance(self.polymorphisms, tuple):
            object.__setattr__(self, 'polymorphisms', tuple(self.polymorphisms))
        for p in self.polymorphisms:
            check.isinstance(p, Polymorphism)
        check.arg(len(self.polymorphisms) > 1)

        if len({id(p.root) for p in self.polymorphisms}) != len(self.polymorphisms):
            raise PolymorphismSubtypeError(f'Duplicate roots: {[p.root for p in self.polymorphisms]!r}')

    def merge_subtypes(self) -> SubtypeInfos:
        # Entries unify best-effort by fqcn when one is available (letting a lazy declaration collapse with its
        # already-loaded class - preferring the concrete side, and *never* resolving) and by type identity otherwise.
        # Identical claims arriving through multiple constituents collapse silently; a subtype claimed with differing
        # tags - including two distinct concrete classes sharing an fqcn - is a real conflict.
        merged: dict[str | lang.Identity, SubtypeInfo] = {}
        for p in self.polymorphisms:
            for i in p.subtypes:
                k: str | lang.Identity = i.fqcn or lang.Identity(i.ty)
                if (x := merged.get(k)) is None:
                    merged[k] = i
                    continue

                if (x.tag, x.alts) != (i.tag, i.alts) or (
                        x.cls is not None and i.cls is not None and x.cls is not i.cls
                ):
                    raise PolymorphismSubtypeError(f'Conflicting subtype merger for {k!r}: {x!r}, {i!r}')

                if x.cls is None and i.cls is not None:
                    merged[k] = i

        sts = SubtypeInfos(list(merged.values()))
        sts.by_tag  # noqa  # Eagerly force cross-constituent tag collision detection.
        return sts


##


def _strip_suffixes(
        suffix_stripping: SuffixStripping,
        parent_name: str,
        child_names: ta.Iterable[str],
) -> dict[str, str]:
    child_names = set(check.not_isinstance(child_names, str))
    suffix = check.non_empty_str(lang.coalesce(suffix_stripping.suffix, parent_name))

    if child_names_without := {cn for cn in child_names if not cn.endswith(suffix)}:
        match suffix_stripping.mode:
            case 'required':
                raise PolymorphismSuffixError(suffix, child_names_without)  # noqa
            case 'if_all':
                return {cn: cn for cn in child_names}

    return {cn: cn.removesuffix(suffix) for cn in child_names}


def _suffix_stripper(
        suffix_stripping: SuffixStripping | None,
        parent_name: str,
        child_names: ta.Iterable[str],
) -> ta.Callable[[str], str]:
    if suffix_stripping is None:
        return lang.identity

    return _strip_suffixes(
        suffix_stripping,
        parent_name,
        child_names,
    ).__getitem__


##


def polymorphism_from_subtypes(
        ty: type,
        subtype_tys: ta.Iterable[type],
        *,
        naming: Naming | None = None,
        suffix_stripping: SuffixStripping | None = None,
) -> Polymorphism:
    subtype_tys = set(subtype_tys)

    strip_suffix = _suffix_stripper(
        suffix_stripping,
        ty.__name__,
        {c.__name__ for c in subtype_tys},
    )

    dct: dict[str, SubtypeInfo] = {}
    for cur in subtype_tys:
        name = strip_suffix(cur.__name__)
        if naming is not None:
            name = translate_name(name, naming)
        if name in dct:
            raise PolymorphismSubtypeError(f'Duplicate subtype tag {name!r}: {dct[name].ty!r}, {cur!r}')

        dct[name] = SubtypeInfo(
            cur,
            name,
        )

    return Polymorphism(
        ty,
        SubtypeInfos(list(dct.values())),
    )


def polymorphism_from_subclasses(
        ty: type,
        *,
        naming: Naming | lang.NamedStringCasing | None = None,
        suffix_stripping: SuffixStripping | SimpleSuffixStripping | None = None,
) -> Polymorphism:
    return polymorphism_from_subtypes(
        ty,
        set(lang.deep_subclasses(ty, concrete_only=True)),
        naming=as_naming(naming),
        suffix_stripping=as_suffix_stripping(suffix_stripping),
    )


##


@dc.dataclass(frozen=True)
class SubtypeConfig(Config, lang.Final):
    """
    Registers a class as a subtype of a polymorphic root by updating a config registry under the root's key. Resolved
    by ConfigSubtypeSource - late registrations invalidate affected handlers through the config footprint mechanism.
    """

    ty: type

    _: dc.KW_ONLY

    tag: str | None = None
    alts: ta.Sequence[str] | None = None

    def __post_init__(self) -> None:
        if self.alts is not None and not isinstance(self.alts, tuple):
            object.__setattr__(self, 'alts', tuple(check.not_isinstance(self.alts, str)))


##


class SubtypeSource(lang.Abstract):
    """Sources are values: immutable, hashable, compared by value."""


@ta.final
@dc.dataclass(frozen=True)
class ExplicitSubtypeSource(SubtypeSource, lang.Final):
    """Carries final, already-tagged subtype infos - passes through tag derivation untouched."""

    subtypes: SubtypeInfos


@ta.final
@dc.dataclass(frozen=True)
class SubclassesSubtypeSource(SubtypeSource, lang.Final):
    """
    Deep-scans the root's subclasses at resolve time. Note the sharp edge: subclasses imported after handler
    construction are invisible until something invalidates the handler (a config change observed in its footprint, or
    a Runtime.flush()).
    """


@ta.final
@dc.dataclass(frozen=True)
class ConfigsSubtypeSource(SubtypeSource, lang.Final):
    """
    Reads `SubtypeConfig` configs registered under the root's key. The read lands in the handler's config footprint,
    so late registrations invalidate and rebuild affected handlers.
    """


@ta.final
@dc.dataclass(frozen=True)
class ManifestsSubtypeSource(SubtypeSource, lang.Final):
    """
    Collects `SubtypeManifest` entries whose (resolved) base path names the root - letting subtypes scattered across
    lazily-imported modules be discovered without importing them. Matched entries' modules are imported eagerly at
    handler construction; tags are derived from the manifests' attr (class name) strings per the spec's naming
    configuration unless explicitly overridden on the manifest.
    """


#


SimpleSubtypeSource: ta.TypeAlias = ta.Literal[
    'subclasses',
    'configs',
    'manifests',
]


_SIMPLE_SUBTYPE_SOURCE_MAP: ta.Mapping[SimpleSubtypeSource, SubtypeSource] = {
    'subclasses': SubclassesSubtypeSource(),
    'configs': ConfigsSubtypeSource(),
    'manifests': ManifestsSubtypeSource(),
}


def as_subtype_sources(
        *,
        source: SubtypeSource | SimpleSubtypeSource | None = None,
        sources: ta.Sequence[SubtypeSource | SimpleSubtypeSource] | None = None,
) -> ta.Sequence[SubtypeSource] | None:
    if source is not None and sources is not None:
        raise ValueError('Must not specify both `source` and `sources')
    elif source is not None:
        sources = [source]
    elif sources is None:
        return None

    return check.not_empty(tuple(
        sts if isinstance(sts, SubtypeSource) else _SIMPLE_SUBTYPE_SOURCE_MAP[sts] for sts in sources
    ))


##


@dc.dataclass(frozen=True, kw_only=True)
class _PolymorphismMetadata(md.ClassDecoratorObjectMetadata, lang.Final):
    sources: ta.Sequence[SubtypeSource]

    type_tagging: TypeTagging = WrapperTypeTagging()
    naming: Naming | None = None
    suffix_stripping: SuffixStripping | None = None


#


DEFAULT_POLYMORPHIC_SOURCE: ta.Final[SubtypeSource] = SubclassesSubtypeSource()
DEFAULT_POLYMORPHIC_TYPE_TAGGING: ta.Final[TypeTagging] = WrapperTypeTagging()


def set_polymorphic(
        *,
        source: SubtypeSource | SimpleSubtypeSource | None = None,
        sources: ta.Sequence[SubtypeSource | SimpleSubtypeSource] | None = None,

        type_tagging: TypeTagging | SimpleTypeTagging | None = None,
        naming: Naming | lang.NamedStringCasing | None = None,
        suffix_stripping: SuffixStripping | SimpleSuffixStripping | None = None,
) -> ta.Callable[[type[T]], type[T]]:
    sources_ = lang.coalesce(
        as_subtype_sources(source=source, sources=sources),
        (DEFAULT_POLYMORPHIC_SOURCE,),
    )

    type_tagging_ = lang.coalesce(
        as_type_tagging(type_tagging),
        DEFAULT_POLYMORPHIC_TYPE_TAGGING,
    )

    naming_ = as_naming(naming)

    suffix_stripping_ = as_suffix_stripping(suffix_stripping)

    def inner(cls):
        _PolymorphismMetadata(
            sources=sources_,
            type_tagging=type_tagging_,
            naming=naming_,
            suffix_stripping=suffix_stripping_,
        )(cls)

        return cls

    return inner
