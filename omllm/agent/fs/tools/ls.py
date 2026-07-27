import io
import os


##


async def ls(
        dir_path: str,
) -> str:
    """
    Lists the contents of the specified dir.

    Args:
        dir_path: The dir to list the contents of. Must be an absolute path.
    """

    out = io.StringIO()
    out.write('<dir>\n')
    for e in sorted(os.scandir(dir_path), key=lambda e: e.name):  # noqa
        out.write(f'{e.name}{"/" if e.is_dir() else ""}\n')
    out.write('</dir>\n')

    return out.getvalue()
