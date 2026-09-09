import io
import tarfile


##


def build_archive(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
        for name, contents in files.items():
            member = tarfile.TarInfo(f'package/{name}')
            member.size = len(contents)
            archive.addfile(member, io.BytesIO(contents))
    return buffer.getvalue()
