# jsvendor

`jsvendor` vendors audited browser ESM packages directly from pinned registry archives without a JavaScript package
manager or build step. It verifies archive integrity and licenses, extracts distributed modules, rewrites bare imports
to relative paths, verifies the resulting graph, and generates file hashes and third-party notices.

The source manifest contains only the application's root packages and their requested npm version ranges. The generated
`lock.json` contains that root snapshot plus the complete resolved closure: versions, licenses, SHA-512 integrity,
archive URLs, package requirements, and generated file hashes.

Resolution reads package and exact-version metadata directly from the configured npm registry. It chooses one global
version of every package which satisfies all ordinary and peer requirements, backtracking from newer versions when
necessary. Required peers join the closure; optional peers constrain a package only when another requirement includes
it. Development and optional dependencies are not included.

Generation honors package `exports` maps, including exact and wildcard subpaths, arrays, and nested browser, import,
module, and default conditions in declaration order. An explicit export map is an access boundary: imports of private
subpaths fail instead of guessing a filename. Packages without an export map use their browser or module entry, or an
ESM `main`, and retain legacy subpath behavior. The root entry of each resolved package plus every statically reachable
relative or exported module is materialized.

Static imports and re-exports are found with JavaScript-aware lexical parsing across multiline declarations, comments,
strings, regular expressions, and template expressions. Bare imports are rewritten through the selected export map.
Dynamic imports, escaped specifiers, external URLs, unresolved targets, and paths which escape the vendor tree are
rejected.

## Headless use

Load a manifest and pass immutable request values to the resolution, generation, or verification entry points:

```python
from omdev.js.vendor import ResolveRequest
from omdev.js.vendor import VendorRequest
from omdev.js.vendor import load_manifest
from omdev.js.vendor import resolve
from omdev.js.vendor import vendor

manifest = load_manifest('path/to/vendor.json')
resolved = resolve(ResolveRequest(manifest=manifest))

result = vendor(VendorRequest(
    manifest=manifest,
    lock=resolved.lock,
    destination='path/to/resources/vendor',
    cache_directory='.cache/jsvendor',
))
```

Generation and verification return result dataclasses. Only `jsvendor.cli` parses command-line arguments.

Root-management operations are headless as well. `add`, `update`, and `remove` accept immutable request dataclasses and
return a `ManifestUpdateResult` containing the proposed manifest and resolution lock. They perform no file writes;
`outdated` returns structured `OutdatedPackage` rows.

## CLI

The equivalent CLI form of the usage show above is shown below.

```bash
python -m omdev.js.vendor resolve \
    --manifest path/to/vendor.json \
    --destination path/to/resources/vendor

python -m omdev.js.vendor vendor \
    --manifest path/to/vendor.json \
    --destination path/to/resources/vendor

python -m omdev.js.vendor verify \
    --manifest path/to/vendor.json \
    --destination path/to/resources/vendor
```

Manage root intent with package arguments:

```bash
# Add latest as an exact root version, or preserve an explicit range.
python -m omdev.js.vendor add crelt @codemirror/lang-json@^6.0.0 \
    --manifest path/to/vendor.json --destination path/to/resources/vendor

# Advance every root to its latest tag, advance selected roots, or set a new range.
python -m omdev.js.vendor update \
    --manifest path/to/vendor.json --destination path/to/resources/vendor
python -m omdev.js.vendor update @codemirror/view @codemirror/state@^6.7.0 \
    --manifest path/to/vendor.json --destination path/to/resources/vendor

python -m omdev.js.vendor remove crelt \
    --manifest path/to/vendor.json --destination path/to/resources/vendor

python -m omdev.js.vendor outdated \
    --manifest path/to/vendor.json --destination path/to/resources/vendor
```

Package arguments accept unscoped or scoped names plus an optional npm range or dist-tag. A missing version and a bare
name passed to `update` both select the registry's `latest` tag and store its exact version. `update` with no package
arguments advances every root. `outdated` is read-only and reports Current, Wanted (highest matching the stored range),
Latest, and Requirement; optional package names restrict its report.

Run `vendor` after `resolve`, `add`, `update`, or `remove`; resolution intentionally clears stale generated file hashes.
The mutating root commands resolve successfully before writing either the manifest or lock. `vendor` remains
reproducible from the lock and does not look up registry metadata. `verify` is offline and rejects missing or unexpected
files. The archive cache defaults to `.cache/jsvendor`; the metadata registry defaults to
`https://registry.npmjs.org` and can be changed with `--registry`.

`vendor` builds and fully verifies a staging tree beside the destination before replacement. An existing tree is moved
to a temporary backup only for the final same-filesystem rename and is restored if installation fails. Manifest and
lock writes also use same-directory temporary files and atomic replacement.

Offline verification checks the canonical on-disk lock, normalized locked paths, the exact regular-file set, SHA-256
hashes, package identity/dependency/license metadata, root exports, third-party notices, dependency-closure membership,
and every static module edge. Symbolic links, special files, dynamic imports, bare imports, missing modules, unsafe
paths, unexpected files, and noncanonical locks fail verification.
