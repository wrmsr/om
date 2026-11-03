Scattered notes about our harness. Clean this up into a real doc when ready lol.

- We generally lean minimal and strongly lean self-contained:
  - mcp support is a todo but still hasn't had a usecase worthy of actually implementing it.
- Unless **explicitly** told to by the user, we do **not** by default honor `AGENTS.md` / `CLAUDE.md`, load in-repo
  skills, or any other such directives present in our cwd.
- The preferred means of operation is the harness (`om llm`) running unsandboxed directly on the host, but all tool
  execution (and thus the models' view of the world) happening in a 'dockerdev'.
  - docker provides reasonable safeguards against accidents, but does not pretend to defend against truly malicious
    actors. Tools running in dockerdevs run unsandboxed, and it is assumed inputs are reasonably trusted.
- Running tools natively on the host is supported, and basic bwrap/seatbelt sandboxing is present, but it's much less
  built up than dockerdev usage.
