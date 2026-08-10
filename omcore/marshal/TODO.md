- streaming?
- datatypes
  - redacted
  - lang.Marker - class name, handle `type[Foo]`
  - pathlib.Path
  - decimal.Decimal
  - datetime.date, datetime.time
  - ipaddress
  - re.pattern
  - numpy types
- jackson switches
  - accept_case_insensitive_enums
  - accept_case_insensitive_properties
  - accept_case_insensitive_values
  - allow_coercion_of_scalars
  - use_base_type_as_default_impl
- codegen
- context-local switches
  - mutable_collections
- simple lite interop like inj - alt ObjMarshalerManager impl for Context
- bidirectional dc field embedding (currently unmarshal only)
- default options in config
- xml
- TaggedJson
- ta.AnyStr
- streaming?

- Demand-driven config-module discovery (planned, parked):
  - `msh.ConfigModuleManifest(modules=['.requirements'])` - manifest comment in the non-lite bridge module (e.g.
    `omdev/packaging/marshal.py`) declaring which origin modules it serves. Not a ModAttrManifest - no anchor def;
    loaded via `GlobalManifestLoader.load(classes=...)` so `LoadedManifest.module` gives the bridge's own module,
    against whose package the '.'-relative names resolve.
  - Runtime gains one optional seam: `config_module_imports: ConfigModuleImports | None`, checked in `_make` before
    reflection - near-free when the pending map (built lazily from the cached global manifests) is empty. Wired for the
    global runtime only; private registries stay isolated.
  - Ordering makes a separate ReflectOverrideManifest unnecessary: the demand trigger fires on the *containing class*
    (e.g. `ParsedRequirement`) before its first reflection, so the imported bridge's lazy init registers the
    ReflectOverride (and factories) traditionally, and the opaque field alias is never reflected/cached un-substituted
    (the mirror substitutor reads configs live).
  - Nested (under-runtime-lock) triggers are required for correctness - a container-nested encounter must not cache an
    incurable negative entry. Constrained path: import under the main lock, then run the just-registered lazy inits
    inline with the warm lock deliberately untouched (no lock-order inversion). This is the hairy bit.
  - Known edge (documented, accepted): a foreign module's class embedding a bare legacy alias doesn't trigger the
    foreign module declares its own manifest or imports the bridge explicitly.
  - Tests: subprocess-fresh acceptance for packaging (direct entry + nested-in-container), a manifesttest fixture
    config-module leg against a hand-wired private runtime via tests/manifestgen.py, isolation test.
  - Still zero omcore/manifests / omdev/manifests changes; IgnoredInGeneratedManifest still unneeded (the comment lives
    in non-lite code).

Audit:
- _StandardFactory._state is per-factory, not per-config (standard/factories.py, TODO already says "update to
  InternalState"). One StandardMarshalerFactory shared by two registries stays correct (the identity check is against
  the caller's cfg) but rebuilds the whole Multi/Recursive/TypeCache stack on every alternation. Same shape applies to
  _LazyInitRunningFactory._last_lis.
- Typecache staleness is config-identity keyed, not config-version keyed. InternalState.by_config keys on the registry
  object, which survives update(). Late direct registrations (e.g. a MarshalVia for a type already marshaled once,
  outside a lazy init) hit stale positive and negative cache entries forever. Lazy inits are exempt because invalidate()
  rebuilds the stack (fresh typecache identity). This matches the ReflectOverride docstring's "register before first
  reflection" contract, so I treated it as design, but it's the sharpest edge in the system.
- First-operation options ordering: DefaultOptions registered via LazyInit don't apply to the first operation -
  `new_*_context` builds effective options before `make_*` triggers lazy init. Verified: first unmarshal(…,
  `Sequence[int]`) gives tuple, second gives list. Fixable by pre-firing _pre_reflect in `new_*_context`, but that's a
  semantics call for you.
- First use mutates the registry: _get_fac auto-installs StandardMarshalerFactories config, so a sealed-before-first-use
  registry raises ConfigRegistrySealedError on marshal(5). Possibly intended ("seal only after warmup"), but worth
  documenting.
- Generic dataclasses don't substitute type args: marshal(Box(5), `Box[int]`) → UnhandledTypeError: T. The rty args are
  dropped in _DataclassMarshalerBuilder (only the runtime class is used), and generic_replaced_field_annotations maps T
  → Any - so generic_replace/generic_init gets you Any-typed fields, never int. Real substitution through
  rfl.Instance.args would be a feature, not a fix.
- OpenPolymorphism with zero registered impls dies with TypeError: 'NoneType' object is not iterable (open.py:75
  iterates the None from .get(OpenPolymorphismImpl)). Any error is arguably right here, but you may want a
  PolymorphismImplError.
- PolymorphismMetadataCache._lookup_union ends in raise NotImplementedError - a union of impls of a metadata-polymorphic
  root crashes rather than falling through to other factories (returning None would let the chain continue). Explicit
  placeholder, flagging per your NotImplementedError prediction.
- Union strictness: unmarshal(1, float | str) and marshal(True, int | str) both raise TypeError -
  PrimitiveUnionMarshaler does exact-type() checks with no coercion, unlike bare float which coerces via
  PrimitiveMarshalerUnmarshaler. Also dict input to an iterable type still unmarshals as its keys.
- is_single_field vs. embeds: my fix counts an embed field as one field; if you ever combine unwrap_if_single_field with
  embeds the right answer is debatable.
- Error-type hygiene: unknown object fields raise raw KeyError (unmarshal.py:111), enum name misses raise raw KeyError,
  wrapper-polymorphism on a non-1-key map raises raw ValueError - all escape as non-MarshalErrors.
- install_standard_factories ordering is uniformly "most recently installed wins" - including within one call's arg list
  (install(f1, f2) puts f2 first). Self-consistent, but easy to misread as preserving arg order.
- Dead code: singular/uuids.py:17 PATTERN (unused), SimpleMarshaling.get_internal_state_by_config (no callers),
  polymorphism/metadata.py:37 _get_polymorphism_metadata (no callers), and the unreachable third branch in
  ObjectUnmarshaler.unmarshal (unmarshal.py:79-80 - the second elif already catches every case the third could).
- ObjectMarshaler.marshal unknown-fields passthrough (ret.update(ukf)) and unknown-bucket values on unmarshal are stored
  raw - both already carry your FIXME: marshal? comments.
- PolymorphismMetadataCache bakes subclass sets permanently at first lookup - subclasses defined later are invisible
  (module TODO acknowledges).
- _lookup_union's guard also means check.isinstance(m, PolymorphismMarshaler) in typedvalues/unions.py:41 would fail if
  the nested make returns a recursive proxy - only reachable for recursive typed-value unions, which may be impossible
  in practice.

See:
- https://github.com/python-attrs/cattrs
- https://github.com/jcrist/msgspec
- https://github.com/Fatal1ty/mashumaro
- https://github.com/Kotlin/kotlinx.serialization/blob/master/docs/serializers.md#custom-serializers
- https://github.com/yukinarit/pyserde
- https://github.com/FasterXML/jackson
