import contextlib
import functools
import http.server
import io
import tarfile
import threading
import typing as ta


##


def build_archive(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
        for name, contents in files.items():
            member = tarfile.TarInfo(f'package/{name}')
            member.size = len(contents)
            archive.addfile(member, io.BytesIO(contents))
    return buffer.getvalue()


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: ta.Any) -> None:  # noqa: A002
        pass


@contextlib.contextmanager
def serve_directory(directory: str) -> ta.Iterator[str]:
    """Serves a directory over loopback HTTP, yielding its base URL."""

    server = http.server.ThreadingHTTPServer(
        ('127.0.0.1', 0),
        functools.partial(_QuietHandler, directory=directory),
    )
    # The default half-second poll interval would otherwise dominate each test's runtime at shutdown.
    thread = threading.Thread(target=functools.partial(server.serve_forever, poll_interval=0.01), daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_address[1]}'
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
