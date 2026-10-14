"""Local tests: pytest is the only third-party dependency; no Google credentials are used."""
import dataclasses as dc
import email.message
import email.parser
import email.policy
import http.server
import json
import pathlib
import stat
import threading
import types
import typing as ta
import unittest.mock
import urllib.error
import urllib.parse
import urllib.request

import pytest

from .. import gdocs as g


##


CREDS = g.GoogleUserCredentials('client-id', 'client-secret', 'refresh-token')

CLIENT_CONFIG = {'installed': {'client_id': 'client-id', 'client_secret': 'client-secret'}}

DOC_RESPONSE = {
    'id': 'doc-123',
    'name': 'Title',
    'mimeType': g.GOOGLE_DOC_MIME_TYPE,
    'webViewLink': 'https://docs.google.com/document/d/doc-123/edit',
}


@pytest.fixture
def mock_request_json(monkeypatch: pytest.MonkeyPatch) -> unittest.mock.Mock:
    request = unittest.mock.Mock(spec=g._request_json, return_value=DOC_RESPONSE.copy())
    monkeypatch.setattr(g, '_request_json', request)
    return request


def _parse_upload(call: ta.Any) -> tuple[email.message.EmailMessage, list[email.message.EmailMessage]]:
    headers = call.kwargs['headers']
    message = email.parser.BytesParser(policy=email.policy.default).parsebytes(
        b'MIME-Version: 1.0\r\nContent-Type: '
        + headers['Content-Type'].encode('ascii')
        + b'\r\n\r\n'
        + call.kwargs['data'],
    )
    return message, list(message.iter_parts())


##


def test_pkce_rfc_7636_vector() -> None:
    assert (
        g._pkce_challenge('dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk')
        == 'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM'
    )


def test_secret_repr() -> None:
    assert 'client-secret' not in repr(CREDS)
    assert 'refresh-token' not in repr(CREDS)


def test_private_atomic_storage(tmp_path: pathlib.Path) -> None:
    path = tmp_path / 'credentials.json'
    path.write_text('old content', encoding='utf-8')
    path.chmod(0o644)

    g.save_credentials(str(path), CREDS)

    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert g.load_credentials(str(path)) == CREDS
    raw = json.loads(path.read_text(encoding='utf-8'))
    assert 'access_token' not in raw
    assert raw['scopes'] == [g.DRIVE_FILE_SCOPE]
    assert list(tmp_path.iterdir()) == [path]


def test_service_account_is_rejected(tmp_path: pathlib.Path) -> None:
    path = tmp_path / 'wrong.json'
    path.write_text(json.dumps({'type': 'service_account'}), encoding='utf-8')

    with pytest.raises(ValueError, match='authorized_user'):
        g.load_credentials(str(path))


def test_refresh_request(mock_request_json: unittest.mock.Mock) -> None:
    creds = g.GoogleUserCredentials('client+/&', 'secret+=&', 'refresh/token+=')
    mock_request_json.return_value = {
        'access_token': 'access',
        'scope': g.DRIVE_FILE_SCOPE,
        'token_type': 'Bearer',
    }

    assert g.refresh_access_token(creds) == 'access'

    assert mock_request_json.call_count == 1
    call = mock_request_json.call_args
    assert call.args == (g.TOKEN_URL,)
    assert call.kwargs['method'] == 'POST'
    assert call.kwargs['headers']['Content-Type'] == 'application/x-www-form-urlencoded'
    assert urllib.parse.parse_qs(call.kwargs['data'].decode('ascii')) == {
        'grant_type': ['refresh_token'],
        'client_id': [creds.client_id],
        'client_secret': [creds.client_secret],
        'refresh_token': [creds.refresh_token],
    }


def test_refresh_without_optional_scope_and_secret(mock_request_json: unittest.mock.Mock) -> None:
    mock_request_json.return_value = {'access_token': 'access'}

    assert g.refresh_access_token(g.GoogleUserCredentials('c', '', 'r')) == 'access'

    assert mock_request_json.call_count == 1
    fields = urllib.parse.parse_qs(mock_request_json.call_args.kwargs['data'].decode('ascii'))
    assert 'client_secret' not in fields


def test_ungranted_scope(mock_request_json: unittest.mock.Mock) -> None:
    mock_request_json.return_value = {'scope': 'openid', 'access_token': 'x'}

    with pytest.raises(ValueError, match='not granted'):
        g.refresh_access_token(CREDS)


##


def test_plaintext_unicode_and_newlines(mock_request_json: unittest.mock.Mock) -> None:
    text = 'Hello, \U0001f680 and café.\r\nNext line\n'

    doc = g.create_google_doc('access', 'Títle', text)

    assert doc.document_id == 'doc-123'
    assert doc.url == DOC_RESPONSE['webViewLink']
    assert mock_request_json.call_count == 1
    call = mock_request_json.call_args
    assert call.kwargs['method'] == 'POST'
    url = urllib.parse.urlsplit(call.args[0])
    assert url.path == '/upload/drive/v3/files'
    query = urllib.parse.parse_qs(url.query)
    assert query['uploadType'] == ['multipart']
    assert query['ignoreDefaultVisibility'] == ['true']
    assert 'webViewLink' in query['fields'][0]
    assert call.kwargs['headers']['Authorization'] == 'Bearer access'
    message, parts = _parse_upload(call)
    assert message.get_content_type() == 'multipart/related'
    assert len(parts) == 2
    assert json.loads(parts[0].get_payload(decode=True)) == {
        'name': 'Títle',
        'mimeType': g.GOOGLE_DOC_MIME_TYPE,
    }
    assert parts[1].get_content_type() == 'text/plain'
    assert parts[1].get_payload(decode=True) == text.encode('utf-8')
    assert parts[1].get('Content-Disposition') is None


@pytest.mark.parametrize(('mime', 'text'), [
    pytest.param('text/html', '<h1>Hello</h1>', id='html'),
    pytest.param('text/markdown', '# Hello\n', id='markdown'),
])
def test_html_markdown_and_parent(mock_request_json: unittest.mock.Mock, mime: str, text: str) -> None:
    g.create_google_doc('access', 'Title', text, input_mime_type=mime, parent_id='parent-id')

    assert mock_request_json.call_count == 1
    _, parts = _parse_upload(mock_request_json.call_args)
    assert parts[1].get_content_type() == mime
    assert parts[1].get_payload(decode=True) == text.encode('utf-8')
    assert json.loads(parts[0].get_payload(decode=True))['parents'] == ['parent-id']


def test_blank_document(mock_request_json: unittest.mock.Mock) -> None:
    g.create_google_doc('access', 'Title', '')

    assert mock_request_json.call_count == 1
    call = mock_request_json.call_args
    assert urllib.parse.urlsplit(call.args[0]).path == '/drive/v3/files'
    assert 'uploadType' not in call.args[0]
    assert json.loads(call.kwargs['data'])['mimeType'] == g.GOOGLE_DOC_MIME_TYPE


def test_link_fallback(mock_request_json: unittest.mock.Mock) -> None:
    mock_request_json.return_value = {k: v for k, v in DOC_RESPONSE.items() if k != 'webViewLink'}

    assert g.create_google_doc('access', 'Title', 'body').url == DOC_RESPONSE['webViewLink']


def test_conversion_failure_mentions_created_id(mock_request_json: unittest.mock.Mock) -> None:
    mock_request_json.return_value = {**DOC_RESPONSE, 'mimeType': 'text/plain'}

    with pytest.raises(RuntimeError, match='doc-123'):
        g.create_google_doc('access', 'Title', 'body')


def test_reject_bad_mime_type(mock_request_json: unittest.mock.Mock) -> None:
    with pytest.raises(ValueError):
        g.create_google_doc('access', 'Title', 'body', input_mime_type='text/plain\r\nEvil: yes')

    assert not mock_request_json.called


def test_size_limit_before_request(
        mock_request_json: unittest.mock.Mock,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(g, 'MAX_UPLOAD_BYTES', 10)

    with pytest.raises(ValueError, match='cap'):
        g.create_google_doc('access', 'Title', 'body')

    assert not mock_request_json.called


def test_boundary_collision(monkeypatch: pytest.MonkeyPatch) -> None:
    token_hex = unittest.mock.Mock(side_effect=['collision', 'safe'])
    monkeypatch.setattr(g.secrets, 'token_hex', token_hex)

    body, content_type = g._encode_multipart_related({}, b'gdoc_collision', 'text/plain')

    assert 'gdoc_safe' in content_type
    assert body.startswith(b'--gdoc_safe\r\n')
    assert token_hex.call_count == 2


def test_ambiguous_create_is_not_retried(mock_request_json: unittest.mock.Mock) -> None:
    mock_request_json.side_effect = urllib.error.URLError('connection lost')

    with pytest.raises(urllib.error.URLError):
        g.create_google_doc('access', 'Title', 'body')

    assert mock_request_json.call_count == 1


def test_import_formats(mock_request_json: unittest.mock.Mock) -> None:
    mock_request_json.return_value = {'importFormats': {
        'text/html': [g.GOOGLE_DOC_MIME_TYPE],
        'text/markdown': [g.GOOGLE_DOC_MIME_TYPE],
        'text/csv': ['application/vnd.google-apps.spreadsheet'],
    }}

    assert g.get_import_formats('access') == ['text/html', 'text/markdown']


##


@dc.dataclass
class _OAuthBrowser:
    deny: bool = False
    auth: dict[str, str] = dc.field(default_factory=dict)
    statuses: list[int] = dc.field(default_factory=list)
    thread_errors: list[BaseException] = dc.field(default_factory=list)
    threads: list[threading.Thread] = dc.field(default_factory=list)

    def open_url(self, url: str) -> None:
        self.auth.update({k: v[0] for k, v in urllib.parse.parse_qs(urllib.parse.urlsplit(url).query).items()})

        def browser() -> None:
            try:
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

                def get(url: str) -> None:
                    try:
                        with opener.open(url, timeout=2) as response:
                            self.statuses.append(response.status)
                            response.read()
                    except urllib.error.HTTPError as exc:
                        self.statuses.append(exc.code)
                        exc.close()

                root = self.auth['redirect_uri']
                get(root + 'favicon.ico')
                get(root + '?' + urllib.parse.urlencode({'state': 'wrong', 'code': 'bad'}))
                get(root + '?' + urllib.parse.urlencode({'state': 'é', 'code': 'bad'}))
                get(root + '?' + urllib.parse.urlencode([
                    ('state', self.auth['state']), ('state', self.auth['state']), ('code', 'bad'),
                ]))
                value = {'error': 'access_denied'} if self.deny else {'code': 'test+code=&'}
                get(root + '?' + urllib.parse.urlencode({'state': self.auth['state'], **value}))
            except BaseException as exc:
                # Propagate worker failures through fixture teardown rather than losing them in the thread.
                self.thread_errors.append(exc)

        thread = threading.Thread(target=browser, daemon=True)
        self.threads.append(thread)
        thread.start()

    def join(self) -> None:
        for thread in self.threads:
            thread.join(3)
        assert all(not thread.is_alive() for thread in self.threads), 'OAuth browser thread did not finish'
        assert not self.thread_errors, f'OAuth browser thread failed: {self.thread_errors!r}'


@pytest.fixture
def oauth_browser() -> ta.Iterator[_OAuthBrowser]:
    browser = _OAuthBrowser()
    try:
        yield browser
    finally:
        # Always clean up, even when an assertion or the authorization call fails.
        browser.join()


def test_full_loopback_flow(mock_request_json: unittest.mock.Mock, oauth_browser: _OAuthBrowser) -> None:
    mock_request_json.return_value = {
        'refresh_token': 'refresh',
        'access_token': 'access',
        'scope': g.DRIVE_FILE_SCOPE,
    }

    credentials = g.authorize_desktop_client(
        CLIENT_CONFIG,
        login_hint='me@example.com',
        on_authorization_url=oauth_browser.open_url,
        consent_timeout_s=5,
    )
    oauth_browser.join()

    assert credentials == g.GoogleUserCredentials('client-id', 'client-secret', 'refresh')
    assert mock_request_json.call_count == 1
    call = mock_request_json.call_args
    assert call.args == (g.TOKEN_URL,)
    assert call.kwargs['method'] == 'POST'
    fields = urllib.parse.parse_qs(call.kwargs['data'].decode('ascii'))
    auth = oauth_browser.auth
    assert fields['grant_type'] == ['authorization_code']
    assert fields['code'] == ['test+code=&']
    assert fields['client_id'] == ['client-id']
    assert fields['client_secret'] == ['client-secret']
    assert fields['redirect_uri'] == [auth['redirect_uri']]
    assert g._pkce_challenge(fields['code_verifier'][0]) == auth['code_challenge']
    assert auth['code_challenge_method'] == 'S256'
    assert auth['scope'] == g.DRIVE_FILE_SCOPE
    assert auth['access_type'] == 'offline'
    assert auth['login_hint'] == 'me@example.com'
    assert 'consent' in auth['prompt']
    assert 'client_secret' not in auth
    assert oauth_browser.statuses == [404, 400, 400, 400, 200]


def test_consent_denial(mock_request_json: unittest.mock.Mock, oauth_browser: _OAuthBrowser) -> None:
    oauth_browser.deny = True

    with pytest.raises(RuntimeError, match='access_denied'):
        g.authorize_desktop_client(
            CLIENT_CONFIG,
            on_authorization_url=oauth_browser.open_url,
            consent_timeout_s=5,
        )
    oauth_browser.join()

    assert not mock_request_json.called
    assert oauth_browser.statuses == [404, 400, 400, 400, 200]


def test_client_type(mock_request_json: unittest.mock.Mock) -> None:
    with pytest.raises(ValueError, match='Desktop'):
        g.authorize_desktop_client({'web': CLIENT_CONFIG['installed']})

    assert not mock_request_json.called


def test_timeout(mock_request_json: unittest.mock.Mock, monkeypatch: pytest.MonkeyPatch) -> None:
    ticks = iter([0, 10])
    # Replace only this module's clock, not the process-wide time.monotonic used by pytest and other code.
    monkeypatch.setattr(g, 'time', types.SimpleNamespace(monotonic=lambda: next(ticks)))  # noqa

    with pytest.raises(TimeoutError):
        g.authorize_desktop_client(CLIENT_CONFIG, on_authorization_url=lambda url: None, consent_timeout_s=1)

    assert not mock_request_json.called


##


@pytest.fixture
def local_server(monkeypatch: pytest.MonkeyPatch) -> ta.Iterator[tuple[str, list[ta.Any]]]:
    # Keep actual HTTP requests on loopback even when the environment configures a proxy.
    monkeypatch.setenv('no_proxy', '127.0.0.1')
    monkeypatch.setenv('NO_PROXY', '127.0.0.1')
    seen: list[ta.Any] = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: ta.Any) -> None:
            pass

        def do_GET(self) -> None:
            seen.append(self.path)
            if self.path == '/redirect':
                self.send_response(302)
                self.send_header('Location', '/should-not-be-followed')
                self.end_headers()
            elif self.path == '/error':
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b'{"error":{"message":"permission denied"}}')
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"ok":true}')

        def do_POST(self) -> None:
            seen.append({
                'path': self.path,
                'headers': self.headers,
                'body': self.rfile.read(int(self.headers['Content-Length'])),
            })
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok":true}')

    with http.server.HTTPServer(('127.0.0.1', 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
        thread.start()
        try:
            yield f'http://127.0.0.1:{server.server_port}', seen
        finally:
            server.shutdown()
            thread.join(2)
            assert not thread.is_alive(), 'Local HTTP server thread did not stop'


def test_real_stdlib_post(local_server: tuple[str, list[ta.Any]]) -> None:
    url, seen = local_server

    result = g._request_json(url, method='POST', data='café'.encode('utf-8'), headers={'Authorization': 'Bearer fake'})

    assert result == {'ok': True}
    assert len(seen) == 1
    assert seen[0]['body'] == 'café'.encode('utf-8')
    assert seen[0]['headers']['Authorization'] == 'Bearer fake'


def test_no_redirect(local_server: tuple[str, list[ta.Any]]) -> None:
    url, seen = local_server

    with pytest.raises(g.GoogleApiError) as raised:
        g._request_json(url + '/redirect', headers={'Authorization': 'Bearer fake'})

    assert raised.value.status == 302
    assert seen == ['/redirect']


def test_http_error_body(local_server: tuple[str, list[ta.Any]]) -> None:
    url, _ = local_server

    with pytest.raises(g.GoogleApiError, match='permission denied') as raised:
        g._request_json(url + '/error')

    assert raised.value.status == 403


def test_response_limit(local_server: tuple[str, list[ta.Any]], monkeypatch: pytest.MonkeyPatch) -> None:
    url, _ = local_server
    monkeypatch.setattr(g, 'MAX_RESPONSE_BYTES', 4)

    with pytest.raises(RuntimeError, match='size limit'):
        g._request_json(url)
