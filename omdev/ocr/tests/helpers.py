import os
import os.path
import sys
import textwrap


##


class PngImage:
    def __init__(self, data=b'\x89PNG\r\n\x1a\n'):
        super().__init__()
        self.data = data

    def save(self, out, *, format):  # noqa: A002
        assert format == 'PNG'
        out.write(self.data)


def make_python_executable(directory, name, source):
    path = os.path.join(str(directory), name)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'#!{sys.executable}\n')
        f.write(textwrap.dedent(source))
    os.chmod(path, 0o755)  # noqa
    return path
