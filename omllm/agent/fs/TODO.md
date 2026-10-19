# Filesystem TODO

Open questions left by moving the fs tools from a working-directory boundary to per-path permissions, and the costs of
the choices made along the way. The permissions themselves are in `permissions.py`; the tools ask about a path's
resolved form, spelled bare, and a glob asks about its root and then about every match.


## Design questions

- **ls and glob disagree on symlinks.** Glob hides a match whose resolved target is refused. ls makes one decision
  about the directory and then prints every name in it, so a symlink inside an allowed directory which points outside
  it is listed by ls and hidden by glob. The same per-entry loop would make ls consistent, at one decision per entry.
  Decide whether a listing is a read of the directory alone, or of each thing it names.
- **Glob prints the pattern's spelling of each match.** A pattern through a symlink, or containing `..`, yields paths
  which `read` then refuses as non-canonical, while the permission check was made on the resolved path. Either require
  the pattern's literal prefix to be canonical, as the other tools require of their paths, or print each match's
  resolved path.
- **The match cap is applied before the per-match checks.** `fs.glob` stops at `MAX_MATCHES`, and only then is each
  match asked about, so a glob with many refused matches comes back short and still says there were too many. Fetch in
  larger batches until the cap is met by allowed matches, under some ceiling on the work done.
- **Ask storms.** Under an `ask` rule one glob can prompt up to `MAX_MATCHES` times in sequence, one match at a time.
  The asker could offer to allow or deny the rest of the call, or to add a rule covering the pattern's root; both live
  in the ui, not here.
- **The trailing `/**` convention.** A glob rule ending in `/**` also matches the directory it names, so that a tree
  grant covers listing its own root. It is the one convention left in the matcher after bare spelling was made the
  rule for targets and globs alike; keep it in mind if the matcher grows other forms.


## Known costs

- **Listing is heavier than it was.** `list_dir` returns a full `FsEntry` for each name: an lstat, a stat for a
  symlink, and a realpath, where `os.scandir` had the type cached. Over the remote protocol each entry carries every
  stat field. Fine for ordinary directories, noticeably more for very large ones.
- **A dangling symlink resolves to nowhere.** Its `resolved_path` is where it points, so a tool asks about a path which
  does not exist. That is the right question, since reading the link would reach that path, but it reads oddly in a
  prompt.
- **Glob matches are stat'ed one by one.** Each match costs the same calls as a listed entry, bounded by `MAX_MATCHES`.
