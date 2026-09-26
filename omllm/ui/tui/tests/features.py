import asyncio

from ....core import ui


##


class RecordingTextDisplayer(ui.TextDisplayer):
    def __init__(self):
        super().__init__()

        self.lines = []
        self.displayed = asyncio.Event()

    async def display_text(self, *texts):
        self.lines.append(ui.Text.str_of(list(texts)))
        self.displayed.set()


def write_verification_skill(root, phrase):
    directory = root / 'verification'
    directory.mkdir(parents=True)
    (directory / 'SKILL.md').write_text(
        '---\nname: verification\ndescription: Retrieves a verification phrase from a bundled resource.\n---\n\n'
        'Read reference/phrase.txt with read_skill, then return its phrase exactly.\n',
    )
    (directory / 'reference').mkdir()
    (directory / 'reference' / 'phrase.txt').write_text(phrase)
    return directory
