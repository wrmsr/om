# Config overrides

Small `PATH OP VALUE` statements for overriding parts of a structured config - nested dataclasses, usually - from
somewhere flat, like commandline arguments.

```python
from omcore.configs import overrides as ovr

cfg = ovr.override_config(Config(), ['model.opt.lr=3e-4', 'layers[name=enc].dim=3', '/model.dropout'])
```

Overrides are never applied to config objects themselves, only to their plain tree form (dicts, lists, scalars):
defaults are marshaled to a tree, the overrides are applied to it in order, and the result is unmarshaled.

## Statements

```
model.opt.lr=3e-4                           replace
model.opt+={lr: 3e-4, betas: [0.9, 0.99]}   deep-merge a map / extend a list
data.transforms.+={kind: flip}              append one element          (or data.transforms[+]=...)
data.transforms.-1.p=0.2                    index, negatives ok         (or data.transforms[-1].p=...)
layers[name=enc].dim=3                      the single element with a matching value
/model.dropout                              remove / reset to default
model.encoder=@enc.json                     value from a file
@experiment.json                            merge a file at the root
```

- **Paths** are keys separated by dots. A key which isn't just letters, digits, `_` and `-` must be quoted: `a."b c"`
  or `a["b c"]`. The empty path is the root (`+={a: 1}`).
- **Indices** are `[0]` or `.0`. The dotted spelling is a key which is treated as an index only when applied to a list,
  so it needs no quoting from a shell. **Append** is `[+]` or `.+`.
- **Selectors** (`[name=enc]`, `[spec.id=3]`) pick the one element of a list having that value at those keys, and fail
  unless exactly one does.
- **`=`** always replaces, creating whatever leads up to its path. **`+=`** merges: a map into a map (recursively, with
  lists nested in the merged map *replacing* rather than extending), or a list onto the end of a list.
- **`/`** removes. A missing key unmarshals to its field's default, so removing a field resets it.
- **`@path`** as a value is the contents of a json, toml, yaml or ini file.

Anything they can't express is a job for a jq filter, as a `JqOp`: it is given the whole tree and must output exactly
one new one. It sees the tree as it stands - something created by an earlier override has only the keys it was given,
not yet its defaults. jq is not imported until one is applied.

Filters are held to the shape just as statements are: whatever one writes into the tree is checked where it lands, so
`.vresion = "2"` and `.layers[0].dim = "8"` fail then and there, with a path, and `.opt.Sgd.lr = 1` switches subtypes.

## Values

Values are kept as text until applied, when the *shape* of their target decides what they are:

| Target | `x=5` | `x="5"` | `x=1.10` | `x=null` |
|---|---|---|---|---|
| string | `'5'` | `'5'` | `'1.10'` | `'null'` |
| int | `5` | error | error | error |
| float | `5.0` | error | `1.1` | error |
| optional string | `'5'` | `'5'` | `'1.10'` | `None` |
| `int \| str` | `5` | `'5'` | `'1.10'` | `'null'` |
| anything | `5` | `'5'` | `1.1` | `None` |

- A quoted value is always a string. A bare one is whatever its target says it is.
- Where the target is anything (`ta.Any`, or there is no shape at all) bare values are guessed json5-style: `null`,
  `true`, `false` and numbers are themselves and everything else is a string.
- Lists and maps are written json5-ish with bare scalars: `{name: enc, dims: [1, 2], note: "a, b"}`. Text which looks
  like one but isn't well-formed is a string, as is anything at all given to a string target (`pattern=[a-z]+`).
- Booleans are `true` and `false`. Enums are their names, literals their values.

Values from files and jq filters are different: they arrive already typed, so they are checked against the shape of
their target but never reinterpreted. A number is not taken for a string (`.version = 1.10` is an error - write
`.version = "1.10"`), nor a string for a boolean. The one liberty taken is between ints and floats of the same value,
which neither JSON nor jq tells apart.

## Shapes

The engine (`OverrideApplier`) needs no knowledge of what it's operating on, and works on any tree. Given a `Shape` it
walks it in step with the tree to type values as above, to reject unknown keys (with suggestions), and to know that
the tags of a wrapper-tagged polymorphic value displace one another (`opt.Sgd.lr=1` replaces `{Adam: {...}}`).

`ConfigOverrider` derives shapes from the marshal system by inspecting the unmarshalers it constructs. It understands
only the commonplace ones: objects, primitives, optionals, lists, tuples, string-keyed maps, enums, literals, primitive
and literal unions, and polymorphism. Anything else is an `UnknownShape`, which is harmless until an override needs a
value produced for one - at which point it raises `UnhandledOverrideShapeError`, or with `guess_unknown=True` guesses
as it would for anything. Removing things, jq, and values from files never need a value produced.

## Arguments

```python
parser = argparse.ArgumentParser()
ovr.add_override_arguments(parser)  # -s/--set OVERRIDE, --jq FILTER, --dump[=json]
args = parser.parse_args()

overrider = ovr.ConfigOverrider(Config)
tree = overrider.apply(overrider.marshal(Config()), args.overrides or [])
if args.dump:
    print(overrider.dump(tree, args.dump))
cfg = overrider.unmarshal(tree)
```

Statements and filters are collected into one list in the order given, whichever flag gave them. `--dump` prints the
tree in the override grammar itself - every line a valid statement which changes nothing, to be grepped for, edited and
passed back - and `--dump=json` prints it as json, which is valid `@file` input.
