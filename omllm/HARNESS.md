Scattered notes about our harness. Clean this up into a real doc when ready lol.

- We generally lean minimal and strongly lean self-contained:
  - mcp support is a todo but still hasn't had a usecase worthy of actually implementing it.
- We want a small number of tools, but will steer models to use builtin tools over more general ones when provided.
  - For example fs ops all have explicit tools (ls/glob/read/write/edit), and it's strongly encouraged for models to use
    these even when they'd otherwise use bash, even when present and permitted.
  - A small number of specific external tools (`ripgrep` and `fdfind` currently) have dedicated agent tools - they're
    just too fast and well known by models to be ignored. Models are also strongly encouraged to use them over invoking
    them over bash. They still run sandboxed (if configured), but special-casing them allows for tighter sandboxing
    rules, which then allows for them to run with separate more permissive permissions (always allow) vs fully
    generalized bash (always ask). Additionally it allows best-effort parsing their given args to try to understand what
    the model means, maybe to fail early or provide feedback to it (but never leaned on as a true means of security).
- Unless **explicitly** told to by the user, we do **not** by default honor `AGENTS.md` / `CLAUDE.md`, load in-repo
  skills, or any other such directives present in our cwd.
- The preferred means of operation is the harness (`om llm`) running unsandboxed directly on the host, but all tool
  execution (and thus the models' view of the world) happening in a 'dockerdev'.
  - docker provides reasonable safeguards against accidents, but does not pretend to defend against truly malicious
    actors. Tools running in dockerdevs run unsandboxed, and it is assumed inputs are reasonably trusted.
- Running tools natively on the host is supported, and basic bwrap/seatbelt sandboxing is present, but it's much less
  built up than dockerdev usage.
- The codebase is built around dependency injection. However, all directly injector related code is strictly kept
  quarantined in specific 'inject' modules and packages. The code all remains fully usable without any reference to or
  involvement of `omcore.inject`, via good old-fashioned manual kwarg threading.
- Despite the obvious extreme extensibility the code layout gives us, it is not nor will it ever be a goal to have any
  kind of "plugin marketplace". All the functionality necessary for this to be used comfortably like any other modern
  agent coding harness should be present internally. Nothing prevents external code from reaching in and overriding
  whatever it wants, but any kind of formalization of 'plugin' for external extension is strictly and perpetually out of
  scope.
  - Some internal concept of 'bundles' or something would probably be nice, but only for internal organization, not
    intended as a point of external extension.
