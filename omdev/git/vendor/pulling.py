import os
import os.path
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from ..status import GitStatusItem
from ..status import GitStatusState
from ..status import get_git_status
from .errors import GitVendorDirtyError
from .errors import GitVendorMergeInProgressError
from .errors import GitVendorSubprocessError
from .errors import GitVendorUpstreamRevError
from .journals import CHANGING_GIT_VENDOR_FILE_DISPOSITIONS
from .journals import GitVendorFileDisposition
from .journals import GitVendorJournal
from .journals import GitVendorJournalEntry
from .journals import delete_vendor_journal
from .journals import load_live_vendor_journal
from .journals import save_vendor_journal
from .merging import run_git_merge_file
from .paths import is_path_under
from .runners import GitRunner
from .specs import load_vendor_spec
from .specs import save_vendor_spec
from .specs import vendor_spec_path
from .upstreams import git_upstream_source


##


_NULL_SHA = '0' * 40


class GitVendorPuller:
    """
    Pulls a vendored directory up to a given upstream rev via per-file three-way merges, using the spec's recorded rev
    as the merge base. Cleanly-merging files are written and staged; conflicting files get standard conflict markers
    plus real stage-1/2/3 index entries, so resolution works exactly like an ordinary git merge (`git status` /
    `git mergetool` / `git checkout --ours` / `git add`). All mutations are confined to paths under the vendored
    directory.
    """

    def __init__(
            self,
            repo_dir: str,
            vendor_dir: str,
            *,
            rev: str | None = None,
            from_path: str | None = None,
            allow_dirty: bool = False,
    ) -> None:
        super().__init__()

        self._repo_dir = repo_dir
        self._vendor_dir = vendor_dir.rstrip('/')
        self._rev = rev
        self._from_path = from_path
        self._allow_dirty = allow_dirty

        self._repo = GitRunner(repo_dir)
        self._abs_vendor_dir = os.path.join(repo_dir, self._vendor_dir)

    #

    @dc.dataclass(frozen=True, kw_only=True)
    class _PlannedFile:
        path: str
        disposition: GitVendorFileDisposition
        mode: str = '100644'
        content: bytes | None = None
        base: bytes | None = None
        ours: bytes | None = None
        theirs: bytes | None = None

    #

    def _item_paths(self, item: GitStatusItem) -> ta.Sequence[str]:
        return [p for p in (item.a, item.b) if p is not None]

    def _check_not_in_progress(self, git_dir: str, status: ta.Iterable[GitStatusItem]) -> None:
        if load_live_vendor_journal(self._repo, git_dir, self._vendor_dir) is None:
            return

        if any(
                any(is_path_under(p, self._vendor_dir) for p in self._item_paths(it))
                for it in status
        ):
            raise GitVendorMergeInProgressError(
                f'A vendor pull of {self._vendor_dir} is already in progress - commit your resolution or abort it '
                f'first',
            )

        # Live journal but nothing outstanding under the vendor dir - abandoned by hand.
        delete_vendor_journal(git_dir, self._vendor_dir)

    def _check_clean(self, status: ta.Iterable[GitStatusItem]) -> None:
        unmerged: list[str] = []
        blocking: list[str] = []

        for it in status:
            paths = self._item_paths(it)
            if it.is_unmerged:
                unmerged.extend(paths)
            elif any(is_path_under(p, self._vendor_dir) for p in paths):
                blocking.extend(paths)
            elif it.x is GitStatusState.UNTRACKED:
                pass
            else:
                blocking.extend(paths)

        # Unmerged entries anywhere are never acceptable, even with allow_dirty.
        if unmerged:
            raise GitVendorDirtyError(sorted(set(unmerged)))

        if blocking and not self._allow_dirty:
            raise GitVendorDirtyError(sorted(set(blocking)))

    #

    def _read_local(self, abs_path: str) -> bytes | None:
        try:
            with open(abs_path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            return None

    def _plan_file(
            self,
            upstream: GitRunner,
            *,
            path: str,
            old_rev: str | None,
            new_rev: str,
            rev_label: str,
    ) -> _PlannedFile:
        ours = self._read_local(os.path.join(self._abs_vendor_dir, path))
        base = upstream.try_read_blob(old_rev, path) if old_rev is not None else None
        theirs = upstream.try_read_blob(new_rev, path)
        mode = (upstream.tree_mode(new_rev, path) if theirs is not None else None) or '100644'

        disposition: GitVendorFileDisposition
        content: bytes | None = None

        if theirs is None:
            if ours is None:
                disposition = GitVendorFileDisposition.UNCHANGED
            elif base is None:
                disposition = GitVendorFileDisposition.LOCAL_ONLY
            elif ours == base:
                disposition = GitVendorFileDisposition.DELETED
            else:
                disposition = GitVendorFileDisposition.DELETE_CONFLICTED

        elif ours is None:
            disposition = GitVendorFileDisposition.ADDED
            content = theirs

        elif ours == theirs or base == theirs:
            disposition = GitVendorFileDisposition.UNCHANGED

        elif base is not None and ours == base:
            disposition = GitVendorFileDisposition.FAST_FORWARDED
            content = theirs

        else:
            mr = run_git_merge_file(
                base if base is not None else b'',
                ours,
                theirs,
                labels=(
                    'ours (local)',
                    f'base ({old_rev[:12] if old_rev is not None else "none"})',
                    f'theirs ({rev_label})',
                ),
            )
            disposition = (
                GitVendorFileDisposition.CONFLICTED
                if mr.conflicted
                else GitVendorFileDisposition.AUTO_MERGED
            )
            content = mr.content

        return self._PlannedFile(
            path=path,
            disposition=disposition,
            mode=mode,
            content=content,
            base=base,
            ours=ours,
            theirs=theirs,
        )

    #

    def _write_local(self, plan: _PlannedFile) -> None:
        abs_path = os.path.join(self._abs_vendor_dir, plan.path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'wb') as f:
            f.write(check.not_none(plan.content))
        if plan.mode == '100755':
            os.chmod(abs_path, 0o755)  # noqa: S103

    def _apply_planned_file(self, plan: _PlannedFile) -> None:
        rel_path = os.path.join(self._vendor_dir, plan.path)
        d = plan.disposition

        if d in (GitVendorFileDisposition.UNCHANGED, GitVendorFileDisposition.LOCAL_ONLY):
            return

        if d is GitVendorFileDisposition.DELETED:
            self._repo.run('rm', '-f', '-q', '--', rel_path)
            return

        if d in (
                GitVendorFileDisposition.ADDED,
                GitVendorFileDisposition.FAST_FORWARDED,
                GitVendorFileDisposition.AUTO_MERGED,
        ):
            self._write_local(plan)
            self._repo.run('add', '--', rel_path)
            return

        stage_datas: ta.Sequence[tuple[int, bytes | None]]
        if d is GitVendorFileDisposition.CONFLICTED:
            stage_datas = [(1, plan.base), (2, plan.ours), (3, plan.theirs)]
        elif d is GitVendorFileDisposition.DELETE_CONFLICTED:
            stage_datas = [(1, plan.base), (2, plan.ours)]
        else:
            raise TypeError(d)

        lines = [f'0 {_NULL_SHA}\t{rel_path}']
        for stage, data in stage_datas:
            if data is None:
                continue
            sha = self._repo.write_blob(data)
            lines.append(f'{plan.mode} {sha} {stage}\t{rel_path}')

        if d is GitVendorFileDisposition.CONFLICTED:
            # Write the marker-bearing merge result only after `ours` has been captured as a blob above.
            self._write_local(plan)

        self._repo.update_index_info(lines)

    #

    def pull(self) -> GitVendorJournal:
        git_dir = self._repo.output_str('rev-parse', '--absolute-git-dir')
        status = get_git_status(cwd=self._repo_dir)

        self._check_not_in_progress(git_dir, status)
        self._check_clean(status)

        spec = load_vendor_spec(self._abs_vendor_dir)
        requested = self._rev if self._rev is not None else (spec.ref if spec.ref is not None else 'HEAD')

        with git_upstream_source(spec.url, from_path=self._from_path) as upstream:
            try:
                new_rev = upstream.rev_parse(requested + '^{commit}')
            except GitVendorSubprocessError:
                raise GitVendorUpstreamRevError(
                    f'Cannot resolve rev {requested!r} in upstream {upstream.dir}',
                ) from None

            if spec.rev is not None and not upstream.has_object(spec.rev + '^{commit}'):
                raise GitVendorUpstreamRevError(
                    f'Base rev {spec.rev!r} is not present in upstream {upstream.dir}' +
                    (' - fetch it there first' if self._from_path is not None else ''),
                )

            rev_label = requested if requested != 'HEAD' else new_rev[:12]
            plans = [
                self._plan_file(
                    upstream,
                    path=p,
                    old_rev=spec.rev,
                    new_rev=new_rev,
                    rev_label=rev_label,
                )
                for p in spec.files
            ]

        ref_name = requested if requested != 'HEAD' and not new_rev.startswith(requested) else None
        journal = GitVendorJournal(
            vendor_dir=self._vendor_dir,
            pre_head=self._repo.rev_parse('HEAD'),
            old_rev=spec.rev,
            new_rev=new_rev,
            new_ref=ref_name,
            entries=[GitVendorJournalEntry(path=p.path, disposition=p.disposition) for p in plans],
        )

        if (
                not any(p.disposition in CHANGING_GIT_VENDOR_FILE_DISPOSITIONS for p in plans) and
                new_rev == spec.rev
        ):
            return journal

        save_vendor_journal(git_dir, journal)

        for p in plans:
            self._apply_planned_file(p)

        save_vendor_spec(self._abs_vendor_dir, dc.replace(spec, rev=new_rev, ref=ref_name))
        self._repo.run('add', '--', vendor_spec_path(self._vendor_dir))

        return journal
