- jq ops are not shape-aware: the shape is never consulted for them, so their output only meets the types at the final
  unmarshal - which is exactly the lenient path statements were built to avoid.
  - Observed, against a config with `version: str`, `debug: bool`, and a wrapper-tagged `opt: Opt = Adam()`:
    - `.version = 1.10` -> `'1.1'`, silently (the statement `version=1.10` gives `'1.10'`).
    - `.debug = "false"` -> `True`, silently (the statement `debug="false"` is rejected).
    - `.vresion = "2"` -> a bare `KeyError('vresion')` out of unmarshal, with no path and no suggestion.
    - `.opt.Sgd.lr = 1` -> a bare `ValueError` out of unmarshal: the wrapper now has both an `Adam` and a `Sgd` key
      (the statement `opt.Sgd.lr=1` displaces `Adam`).
  - Why: `_apply_jq` hands the whole tree to the filter and takes whatever comes back as the new root. jq values are
    already typed by jq's own literal syntax, so there is no raw text left to type by shape, and the primitive
    unmarshalers coerce between primitive types rather than reject (`str(1.1)`, `bool('false')`).
  - The same hole exists, more narrowly, for `@file` and `ConstOpValue` values: they are taken as already concrete and
    are never checked against the shape either (a json file with `"version": 1.10` goes the same way). Merging one
    map-into-map does at least step through the shape key by key, so unknown keys are caught there - but not for a
    plain set, and never for the values themselves.
  - Proposed: a `check_tree(tree, shape)` which walks a tree in step with its shape (reusing `step_shape`) and raises
    located errors, run on the output of every jq op and on every concrete value as it is set. It would reject:
    - keys an `ObjectShape` doesn't have (with the usual suggestions), and tags a `TaggedShape` doesn't have.
    - scalars of the wrong type for a `ScalarShape` / `ChoiceShape` - exact type, as the primitive union unmarshaler
      already demands, except an int where a float is called for.
    - wrapper-tagged maps without exactly one key, and fixed tuples of the wrong length.
    - containers where scalars are called for and vice versa.
  - Limits of that:
    - It can only reject, not re-type: once jq has produced `1.1` the `1.10` is gone. The message should say to quote
      it in the filter.
    - Nothing beneath an `AnyShape` or `UnknownShape` can be checked, and it must not raise for the latter whatever
      `guess_unknown` is - no value is being guessed, it was given.
    - It is a walk of the whole tree per jq op (and it forces derivation of every lazy shape the tree reaches). Diffing
      the tree before and after to check only what changed is possible but probably not worth it at config sizes.
    - Running it once more just before the final unmarshal would give located errors for everything unmarshal
      currently reports bare, whatever produced them.
  - Alternatives considered:
    - A values abstraction for jq, like jmespath's, so literals could carry their source text and be typed by shape.
      `JqValueOps` is a concrete class constructed directly by `JqProgram`, so there is nowhere to put one today, and
      it would only cover literals written in the filter - not anything computed.
    - A strict mode for the primitive unmarshalers (`allow_coercion_of_scalars` is already on the marshal TODO list).
      That fixes the silent rows at the source and for every other user of marshal, but still gives unlocated errors.
  - Related, and also jq-only: a filter sees the tree as it stands, so something created by an earlier override has
    only the keys it was given and not yet its defaults - `layers.+.name=mid` followed by `.layers |= map(.dim *= 2)`
    fails multiplying null. Filling defaults in would mean an unmarshal / marshal round trip before each jq op, which
    fails on any intermediate state which isn't valid yet.
