import enum
import os
import os.path
import typing as ta
import urllib.parse

from omcore import dataclasses as dc
from omcore import lang
from omcore.formats.json import all as json

from .runners import GitRunner


with lang.auto_proxy_import(globals()):
    from omcore import marshal as msh


##


class GitVendorFileDisposition(enum.Enum):
    UNCHANGED = 'unchanged'
    LOCAL_ONLY = 'local-only'
    ADDED = 'added'
    DELETED = 'deleted'
    FAST_FORWARDED = 'fast-forwarded'
    AUTO_MERGED = 'auto-merged'
    CONFLICTED = 'conflicted'
    DELETE_CONFLICTED = 'delete-conflicted'


CHANGING_GIT_VENDOR_FILE_DISPOSITIONS: ta.AbstractSet[GitVendorFileDisposition] = frozenset([
    GitVendorFileDisposition.ADDED,
    GitVendorFileDisposition.DELETED,
    GitVendorFileDisposition.FAST_FORWARDED,
    GitVendorFileDisposition.AUTO_MERGED,
    GitVendorFileDisposition.CONFLICTED,
    GitVendorFileDisposition.DELETE_CONFLICTED,
])

CONFLICTED_GIT_VENDOR_FILE_DISPOSITIONS: ta.AbstractSet[GitVendorFileDisposition] = frozenset([
    GitVendorFileDisposition.CONFLICTED,
    GitVendorFileDisposition.DELETE_CONFLICTED,
])


@dc.dataclass(frozen=True, kw_only=True)
class GitVendorJournalEntry:
    path: str
    disposition: GitVendorFileDisposition


@dc.dataclass(frozen=True, kw_only=True)
class GitVendorJournal:
    """
    A record of an in-progress vendor pull, written before any repo mutation is performed.

    Stored under the repo's git dir (never the worktree) so it can never be staged, committed, or pushed. `vendor_dir`
    is relative to the repo root, `pre_head` is the commit HEAD pointed at when the pull began, and entry paths are
    relative to the vendor dir.
    """

    vendor_dir: str
    pre_head: str
    old_rev: str | None = None
    new_rev: str
    new_ref: str | None = None
    entries: ta.Sequence[GitVendorJournalEntry] = ()

    @property
    def conflicted_entries(self) -> ta.Sequence[GitVendorJournalEntry]:
        return [e for e in self.entries if e.disposition in CONFLICTED_GIT_VENDOR_FILE_DISPOSITIONS]


##


def vendor_journal_path(git_dir: str, vendor_dir: str) -> str:
    return os.path.join(git_dir, 'om-vendor', urllib.parse.quote(vendor_dir, safe='') + '.json')


def load_vendor_journal(git_dir: str, vendor_dir: str) -> GitVendorJournal | None:
    try:
        with open(vendor_journal_path(git_dir, vendor_dir)) as f:
            buf = f.read()
    except FileNotFoundError:
        return None

    return msh.unmarshal(json.loads(buf), GitVendorJournal)


def save_vendor_journal(git_dir: str, journal: GitVendorJournal) -> None:
    path = vendor_journal_path(git_dir, journal.vendor_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(json.dumps_pretty(msh.marshal(journal)) + '\n')


def delete_vendor_journal(git_dir: str, vendor_dir: str) -> None:
    try:
        os.unlink(vendor_journal_path(git_dir, vendor_dir))
    except FileNotFoundError:
        pass


def load_live_vendor_journal(repo: GitRunner, git_dir: str, vendor_dir: str) -> GitVendorJournal | None:
    """
    Loads the journal for a genuinely in-progress pull, if any. A journal whose pull was subsequently committed -
    detected by commits since its pre_head touching the vendor dir - is stale, and is deleted rather than returned.
    """

    journal = load_vendor_journal(git_dir, vendor_dir)
    if journal is None:
        return None

    head = repo.rev_parse('HEAD')
    if (
            head != journal.pre_head and
            bool(repo.output_str('diff', '--name-only', journal.pre_head, head, '--', vendor_dir))
    ):
        delete_vendor_journal(git_dir, vendor_dir)
        return None

    return journal
