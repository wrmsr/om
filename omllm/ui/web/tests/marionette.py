"""
Test support: just enough of Firefox's Marionette protocol to drive a headless browser at the web frontend - load a
page, run script in it, type, click, and take screenshots. Speaks the protocol directly - length-prefixed json over tcp
- as there is no geckodriver or selenium to lean on, nor any want of one.

Blocking: from async code, call it from a thread.
"""
import base64
import contextlib
import json
import os.path
import shutil
import socket
import subprocess
import tempfile
import time
import typing as ta


##


class MarionetteError(Exception):
    pass


class Marionette:
    def __init__(self, port: int, *, timeout_s: float = 30.) -> None:
        super().__init__()

        self._sock = socket.create_connection(('127.0.0.1', port), timeout=timeout_s)
        self._buf = b''
        self._id = 0

        self._recv()  # The server's hello.

    def close(self) -> None:
        self._sock.close()

    def _recv(self) -> ta.Any:
        while b':' not in self._buf:
            if not (data := self._sock.recv(65536)):
                raise EOFError
            self._buf += data

        n, _, rest = self._buf.partition(b':')
        while len(rest) < int(n):
            if not (data := self._sock.recv(65536)):
                raise EOFError
            rest += data

        msg, self._buf = rest[:int(n)], rest[int(n):]
        return json.loads(msg)

    def command(self, name: str, params: ta.Mapping[str, ta.Any] | None = None) -> ta.Any:
        self._id += 1
        payload = json.dumps([0, self._id, name, params or {}]).encode()
        self._sock.sendall(str(len(payload)).encode() + b':' + payload)

        while True:
            resp = self._recv()
            if resp[0] == 1 and resp[1] == self._id:
                break

        if resp[2] is not None:
            raise MarionetteError(resp[2])

        return resp[3]

    #

    def navigate(self, url: str) -> None:
        self.command('WebDriver:Navigate', {'url': url})

    def set_window_size(self, width: int, height: int) -> None:
        self.command('WebDriver:SetWindowRect', {'width': width, 'height': height})

    def js(self, script: str, *args: ta.Any) -> ta.Any:
        return self.command('WebDriver:ExecuteScript', {'script': script, 'args': list(args)}).get('value')

    def wait_js(self, script: str, *args: ta.Any, timeout_s: float = 10.) -> ta.Any:
        """Runs the script until it returns something truthy, and returns that."""

        deadline = time.monotonic() + timeout_s
        while not (v := self.js(script, *args)):
            if time.monotonic() > deadline:
                raise TimeoutError(script)
            time.sleep(.05)
        return v

    def find(self, css: str) -> str:
        ref = self.command('WebDriver:FindElement', {'using': 'css selector', 'value': css})['value']
        return next(iter(ref.values()))

    def send_keys(self, css: str, text: str) -> None:
        self.command('WebDriver:ElementSendKeys', {'id': self.find(css), 'text': text})

    def click(self, css: str) -> None:
        self.command('WebDriver:ElementClick', {'id': self.find(css)})

    def screenshot(self, path: str) -> None:
        with open(path, 'wb') as f:
            f.write(base64.b64decode(self.command('WebDriver:TakeScreenshot', {'full': False})['value']))


##


ENTER_KEY = '\ue007'
ESCAPE_KEY = '\ue00c'


def find_firefox() -> str | None:
    return shutil.which('firefox')


def _find_free_port() -> int:
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def headless_firefox(
        *,
        width: int = 1000,
        height: int = 1000,
        startup_timeout_s: float = 30.,
) -> ta.Iterator[Marionette]:
    exe = find_firefox()
    if exe is None:
        raise FileNotFoundError('firefox')

    port = _find_free_port()

    with tempfile.TemporaryDirectory(prefix='marionette-') as profile:
        with open(os.path.join(profile, 'user.js'), 'w') as f:
            f.write(f'user_pref("marionette.port", {port});\n')
            f.write('user_pref("browser.shell.checkDefaultBrowser", false);\n')

        proc = subprocess.Popen(  # noqa: S603
            [exe, '--headless', '--marionette', '--no-remote', '--profile', profile],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        try:
            deadline = time.monotonic() + startup_timeout_s
            while True:
                try:
                    m = Marionette(port)
                    break
                except OSError:
                    if time.monotonic() > deadline:
                        raise
                    time.sleep(.2)

            try:
                m.command('WebDriver:NewSession', {'capabilities': {}})
                m.set_window_size(width, height)
                yield m
            finally:
                m.close()

        finally:
            proc.terminate()
            try:
                proc.wait(10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
