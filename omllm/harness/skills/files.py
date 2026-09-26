import os.path
import stat


##


def read_skill_file(directory: str, path: str, *, max_bytes: int = 262_144) -> str:
    """Reads a bounded UTF-8 resource within a configured host skill, including through symlinks."""

    root = os.path.realpath(directory)
    if not path or os.path.isabs(path):
        raise ValueError('Skill resource paths must be relative')
    resolved = os.path.realpath(os.path.join(root, path))
    if os.path.commonpath([root, resolved]) != root:
        raise ValueError('Skill resource escapes its directory')
    if not stat.S_ISREG(os.stat(resolved).st_mode):
        raise ValueError('Skill resources must be regular files')
    with open(resolved, 'rb') as f:
        content = f.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise ValueError(f'Skill resource exceeds {max_bytes} bytes')
    return content.decode('utf-8')
