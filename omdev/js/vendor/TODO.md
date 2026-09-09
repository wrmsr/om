# jsvendor TODO

## Known / unresolved issues

### Stripping `dist/` from output paths is lossy

Output paths drop a leading `dist/`, but only relocated modules have their relative imports rewritten. Any relative
import which crosses the `dist/` boundary therefore breaks:

- A root `index.js` re-exporting from `./dist/impl.js` fails with "Required browser module is not present", since the
  target was written as `impl.js`.
- A `dist/index.js` importing `../shared.js` resolves to `packages/shared.js`. That is outside the package but inside
  the vendor tree, so the escape check in generation misses it and the failure is reported as a missing module.

A fix likely means either rewriting every module's relative imports against the output layout, or abandoning the
`dist/` strip in favor of preserving archive paths.

### The `dist/index.js` root alias collides or silently overwrites

When the root entry is not already `index.js`, its content is aliased to `dist/index.js` so the output root is
`index.js`.

- Legacy packages with a root `index.js` plus a different ESM entry, such as `module: index.mjs`, fail with "Multiple
  archive files produce the same vendor path".
- Under an export map, if a subpath export points at a real `dist/index.js` while the root points at `dist/index.mjs`,
  the alias overwrites the real file in the extracted set and the subpath export silently serves the root module's
  content.

### Subpath-only packages produce nothing as roots

A package with no `.` export, such as `@codemirror/legacy-modes`, fails verification as a root with "Root package has
no browser export". As a dependency it works, since imported subpaths are materialized lazily, but the manifest has no
way to request a subpath export the application itself needs. A root entry would need an optional list of required
subpaths, and verification would need to check those instead of the root export.

### Tarball layout is assumed to use a `package/` top-level directory

Archive members are only extracted from under `package/`. npm accepts any single top-level directory name, so such
archives fail with "Invalid package metadata" once no `package.json` is found.
