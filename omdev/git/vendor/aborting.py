import os
import os.path

from ..status import GitStatusState
from ..status import get_git_status
from .errors import GitVendorNoMergeInProgressError
from .journals import GitVendorJournal
from .journals import delete_vendor_journal
from .journals import load_live_vendor_journal
from .paths import is_path_under
from .runners import GitRunner
from .specs import vendor_spec_path


##


class GitVendorAborter:
    """
    Rolls back an in-progress vendor pull, restoring the vendored directory - index and working tree - to its
    pre-pull state. Only paths under the vendored directory are ever touched: edits made anywhere else in the repo,
    staged or not, are preserved untouched. A pull that has already been committed is no longer in progress and cannot
    be aborted - that's what `git revert` is for.
    """

    def __init__(
            self,
            repo_dir: str,
            vendor_dir: str,
    ) -> None:
        super().__init__()

        self._repo_dir = repo_dir
        self._vendor_dir = vendor_dir.rstrip('/')

        self._repo = GitRunner(repo_dir)

    def _try_unlink(self, rel_path: str) -> None:
        try:
            os.unlink(os.path.join(self._repo_dir, rel_path))
        except FileNotFoundError:
            pass

    def abort(self) -> GitVendorJournal:
        git_dir = self._repo.output_str('rev-parse', '--absolute-git-dir')

        journal = load_live_vendor_journal(self._repo, git_dir, self._vendor_dir)
        if journal is None:
            raise GitVendorNoMergeInProgressError(f'No vendor pull of {self._vendor_dir} is in progress')

        rel_paths = [os.path.join(self._vendor_dir, e.path) for e in journal.entries]
        rel_paths.append(vendor_spec_path(self._vendor_dir))

        for rel_path in rel_paths:
            if self._repo.has_object(f'{journal.pre_head}:{rel_path}'):
                # Restores both index and working tree, clearing any conflict stages for the path as it goes.
                self._repo.run('checkout', journal.pre_head, '--', rel_path)
            else:
                self._repo.run('update-index', '--force-remove', '--', rel_path)
                self._try_unlink(rel_path)

        # The clean-tree gate at pull time means anything untracked under the vendor dir appeared during the merge
        # (mergetool backups and the like) - sweep them.
        for it in get_git_status(cwd=self._repo_dir):
            if it.x is GitStatusState.UNTRACKED and is_path_under(it.a, self._vendor_dir):
                self._try_unlink(it.a)

        self._repo.run('update-index', '--clear-resolve-undo', check_rc=False)

        delete_vendor_journal(git_dir, self._vendor_dir)

        return journal
