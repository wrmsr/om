# Development 01: configuration transactions

## Intent

Make configuration a real transactional boundary before any process runtime exists. A candidate should be fully
discoverable, parseable, mergeable, typed, semantically valid, normalized, and hashable before the future reconciler
can observe it.

## Initial implementation

- Added a fine-grained, frozen dataclass model for manager, API, unit execution, identity, restart/stop policy, stdio,
  dependencies, health probes, collections, and root config.
- Kept argv literal and structured. Minja is deliberately absent from implicit config loading; its future use will be
  an explicit snapshot compilation stage.
- Added deterministic file discovery for JSON, TOML, YAML, and YML. Directory entries are lexically ordered;
  recursion is explicit; duplicate canonical files are ignored.
- Added strict recursive merging. Different files may contribute different mapping branches, which supports layouts
  such as `web.yml` and `database.yml`, but two files cannot silently overlay the same value.
- Retained leaf-level source provenance and all source paths in the desired snapshot.
- Added strict `omcore.lite.marshal` unmarshalling and semantic validation that accumulates independent errors after a
  shape is successfully decoded.
- Added a package-local lite marshaler for config enums. Wire values are the natural lowercase spellings while enum
  member spellings remain conventional; uppercase member names remain accepted for compatibility.
- Added dependency-reference and ordering-cycle validation, health probe shape checks, and collection checks.
- Expanded replicas into stable `unit:slot` instance identities and calculated source-independent SHA-256 digests for
  unit specs and the complete normalized config.

## Deliberate constraints

- A repeated branch is an error, not an overlay. Explicitly ordered overlay sources may be introduced later as a
  visibly different source type.
- No last-good persistence or daemon startup policy is implemented in this phase. The compile result has the shape
  needed for both: either one complete snapshot or structured diagnostics, never a partial config.

## Next

Verify all formats and Python 3.8 behavior, then feed snapshots into the deterministic reconciliation engine. That
engine will assign application generations; generations are intentionally not part of content-addressed snapshots.
