##


def split_newlines(text: str, *, keepends: bool = False) -> list[str]:
    """
    Splits text into lines as a unified diff has them: at newlines only. Python's `str.splitlines` also breaks at form
    feeds, vertical tabs and unicode separators, which a line of a diff - or of the file it was made from - can contain.

    Without `keepends` a line also loses a carriage return ending it, as a diff's parser takes them off its lines.
    """

    lines = text.split('\n')

    # What follows the last newline: nothing, when the text ends with one.
    tail = lines.pop()

    if keepends:
        out = [line + '\n' for line in lines]
    else:
        out = [line.removesuffix('\r') for line in lines]

    if tail:
        out.append(tail if keepends else tail.removesuffix('\r'))

    return out
