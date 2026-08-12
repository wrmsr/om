import http.client
import urllib.error
import urllib.parse
import urllib.request

from .. import dataclasses as dc
from .waiting import Wait
from .waiting import Waiter
from .waiting import waiter_for


##


class HttpWait(Wait, kw_only=True):
    """Readiness probe requiring an HTTP endpoint to return the expected status and optional body."""

    url: str
    method: str = 'GET'
    expected_status: int = 200
    expected_body: bytes | None = None
    timeout_s: float = 1.

    def __post_init__(self) -> None:
        parsed = urllib.parse.urlsplit(self.url)
        if parsed.scheme not in {'http', 'https'} or not parsed.hostname:
            raise ValueError(f'HTTP readiness URL must use http or https: {self.url!r}')
        if not self.method:
            raise ValueError('HTTP readiness method must not be empty')
        if not 100 <= self.expected_status <= 599:
            raise ValueError(f'Invalid HTTP readiness status: {self.expected_status!r}')
        if self.timeout_s <= 0.:
            raise ValueError(f'HTTP readiness timeout must be positive: {self.timeout_s!r}')


class HttpWaiter(Waiter, dc.Frozen):
    wait: HttpWait

    def do_wait(self) -> bool:
        request = urllib.request.Request(  # noqa: S310 - HttpWait validates the scheme.
            self.wait.url,
            method=self.wait.method,
        )
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        try:
            try:
                response = opener.open(request, timeout=self.wait.timeout_s)
            except urllib.error.HTTPError as exc:
                response = exc

            with response:
                if response.status != self.wait.expected_status:
                    return False
                if (expected_body := self.wait.expected_body) is not None:
                    return response.read() == expected_body
                return True

        except (OSError, TimeoutError, urllib.error.URLError, http.client.HTTPException):
            return False


@waiter_for.register
def _(wait: HttpWait) -> HttpWaiter:
    return HttpWaiter(wait)
