## Layout

- In contrast to the other `om*` root packages, this root package is laid out as a somewhat cohesive, multi-tiered
  platform of a `omllm`-root-level packages:
  - `core` - `omllm`-wide abstractions like `sayncs`, `processes`, `registry`, and `ui`.
  - `llm` - llm backend code: `llm.Message`, `llm.Model`, `llm.Tool`, etc.
  - `agent` - agent implementation: `agn.Agent`, `agn.PermissionTarget`, `agn.Session`, etc.
  - `ui` - the agent ui's, intended to be executed not imported.
- `llm` and `agent` are intended to be imported as whole single packages, with everything a user would generally want
  available through the large collection of lazy-imports offered by their `__init__` modules. `core` has a number of
  similar such packages within it like `ui` (to be used via `from ..core import ui`).
- Internal imports within such a package (from itself to itself) must *not* reference the all-in-one `__init__` module:
  each internal item must be imported individually from its relative module:
  - From *outside* of `omllm.agent` it'd be `from .. import agent as agn; agn.Context(...`
  - From *inside* of `omllm.agent` it'd be `from ..types.context import Context; Context(...`

## Injection

- All injection machinery **must** remain strictly isolated from general logic and implementation code - away from
  anything not specifically directly injection-related. It's forbidden to even import `omcore.inject` outside of a
  specifically-injection related module.
- In contrast to the general import discipline described above, it *is* permitted and encouraged to import the
  all-in-one `__init__` module of the containing package for use in `inject` modules: they take care of lazily importing
  only things needed for whatever is being bound by the caller. It's important that `inject` modules don't eagerly
  import everything - they contain the wiring for everything in a package, so they will likely reference everything in
  the package - but if they eagerly import everything unconditionally then it'd defeat the whole point of the lazy
  importing `__init__` facades!

## Config

- Outside of (currently) `omllm.ui`, large cross-cutting config objects are forbidden. If a chunk of code needs some
  config it should have a dataclass just for it declared before or within it, which callers can instantiate and pass
  directly to it (or rely on injection to do that).
- The only code written for 'non-code' users is in `omllm.ui` - everything else is written solely for use by other
  python code. That is to say: no consideration should be given to making configuration easy to thread up to some
  `argparse` parser, or pulled out of thin air via an env var. Code should be written expecting to be magically given
  precisely what it needs, where it needs it, in the format it wants natively.
