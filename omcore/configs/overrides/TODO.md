- jq filters and `@file` / `ConstOpValue` values are held to the shape (see `conforming.py` and `jq.py`), but only as
  far as a value which is already typed can be:
  - They are checked, never re-typed. `.version = 1.10` has already become the float `1.1` by the time it is written,
    so it is rejected rather than taken as `'1.10'` the way the statement `version=1.10` is. Re-typing would need jq to
    hand literals over with their source text - the AST does keep their spans - and is probably not worth it: quoting
    it in the filter is the jq-ish thing to do anyway.
  - Nothing beneath an `AnyShape` or `UnknownShape` can be checked, whatever `guess_unknown` is.
  - A filter sees the tree as it stands, so something created by an earlier override has only the keys it was given
    and not yet its defaults - `layers.+.name=mid` followed by `.layers |= map(.dim *= 2)` fails multiplying null.
    Filling defaults in would mean an unmarshal / marshal round trip before each jq op, which fails on any intermediate
    state which isn't valid yet.
- Removal is never checked against the shape, for statements and filters alike, so it can leave behind things only the
  final unmarshal objects to - and it does so without a path: a fixed tuple short an element (`/opt.Adam.betas.0`), a
  wrapper-tagged map with no tag left in it (`/opt.Adam`), a required field with no default. A `conform_value` of the
  whole tree just before unmarshaling would locate the first two, and with a notion of required fields in
  `ObjectShape` the third.
