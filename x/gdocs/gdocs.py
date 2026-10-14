"""
Create native Google Docs using only Python's standard library (Python 3.10+).

The one-time auth command uses a Desktop OAuth client, a loopback callback, PKCE, and state validation. Runtime commands
use a stored user refresh token. No Google SDKs, auth packages, curl/openssl commands, or local renderers are used. A
browser is needed only for the interactive consent step.

Creates are deliberately NOT retried: an ambiguous failure may have created a Doc. The upload implementation is
intentionally limited to small, in-memory requests.
"""
import argparse
import base64
import dataclasses as dc
import hashlib
import http.server
import json
import os
import secrets
import sys
import tempfile
import time
import typing as ta
import urllib.error
import urllib.parse
import urllib.request
import webbrowser


##


AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_URL = 'https://oauth2.googleapis.com/token'
DRIVE_URL = 'https://www.googleapis.com/drive/v3'
UPLOAD_URL = 'https://www.googleapis.com/upload/drive/v3/files'

DRIVE_FILE_SCOPE = 'https://www.googleapis.com/auth/drive.file'

GOOGLE_DOC_MIME_TYPE = 'application/vnd.google-apps.document'
INPUT_MIME_TYPES = {
    'text': 'text/plain',
    'html': 'text/html',
    'markdown': 'text/markdown',
}

# Conservative application limits, not claims about Google's maximum Doc size.
MAX_UPLOAD_BYTES = 5_000_000
MAX_RESPONSE_BYTES = 1_048_576


class GoogleApiError(RuntimeError):
    def __init__(self, status: int, body: bytes) -> None:
        self.status = status
        self.body = body
        super().__init__(f'Google HTTP {status}: {body.decode("utf-8", "replace")[:4000]}')


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(
            self,
            req,
            fp,
            code,
            msg,
            headers,
            newurl,
    ):
        # Never forward credentials through an unexpected redirect.
        return None


def _request_json(
        url: str,
        *,
        method: str = 'GET',
        data: bytes | None = None,
        headers: ta.Mapping[str, str] | None = None,
        timeout_s: float = 60.0,
) -> dict[str, ta.Any]:
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Accept': 'application/json', **(headers or {})},
        method=method,
    )

    opener = urllib.request.build_opener(_NoRedirectHandler())

    try:
        with opener.open(req, timeout=timeout_s) as resp:
            raw = resp.read(MAX_RESPONSE_BYTES + 1)

    except urllib.error.HTTPError as exc:
        try:
            body = exc.read(65_536)
        finally:
            exc.close()
        raise GoogleApiError(exc.code, body) from None

    if len(raw) > MAX_RESPONSE_BYTES:
        raise RuntimeError('Google JSON response exceeded the local size limit')

    result = json.loads(raw)

    if not isinstance(result, dict):
        raise ValueError('Expected a JSON object from Google')

    return result


def _required_string(obj: ta.Mapping[str, ta.Any], key: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f'Missing or invalid {key!r}')
    return value


def _check_granted_scope(tokens: ta.Mapping[str, ta.Any]) -> None:
    # OAuth permits omission when the granted scope is unchanged.
    if (scope := tokens.get('scope')) is not None:
        if not isinstance(scope, str):
            raise ValueError('Invalid scope in token response')

        if not {DRIVE_FILE_SCOPE, 'https://www.googleapis.com/auth/drive'}.intersection(scope.split()):
            raise ValueError('The requested Drive file access was not granted')

    if str(tokens.get('token_type', 'Bearer')).lower() != 'bearer':
        raise ValueError('Expected a Bearer access token')


@dc.dataclass(frozen=True)
class GoogleUserCredentials:
    client_id: str
    client_secret: str = dc.field(repr=False)
    refresh_token: str = dc.field(repr=False)


def load_credentials(path: str) -> GoogleUserCredentials:
    with open(os.path.expanduser(path), encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, dict) or data.get('type') != 'authorized_user':
        raise ValueError('Expected authorized_user credentials, not a service-account key')

    secret = data.get('client_secret', '')
    if not isinstance(secret, str):
        raise ValueError('Invalid client_secret')

    return GoogleUserCredentials(
        client_id=_required_string(data, 'client_id'),
        client_secret=secret,
        refresh_token=_required_string(data, 'refresh_token'),
    )


def save_credentials(path: str, credentials: GoogleUserCredentials) -> None:
    """Atomically replace a credentials file with a mode-0600 file on macOS/Linux."""

    path = os.path.abspath(os.path.expanduser(path))
    directory = os.path.dirname(path)

    os.makedirs(directory, mode=0o700, exist_ok=True)

    data = {
        'type': 'authorized_user',
        **dc.asdict(credentials),
        'scopes': [DRIVE_FILE_SCOPE],
    }

    fd, tmp = tempfile.mkstemp(prefix='.google-auth-', dir=directory)

    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp, path)

    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def refresh_access_token(
        credentials: GoogleUserCredentials,
        *,
        timeout_s: float = 60.0,
) -> str:
    """Get a fresh access token; this minimal helper does not maintain a token cache."""

    fields = {
        'grant_type': 'refresh_token',
        'client_id': credentials.client_id,
        'refresh_token': credentials.refresh_token,
    }

    if credentials.client_secret:
        fields['client_secret'] = credentials.client_secret

    tokens = _request_json(
        TOKEN_URL,
        method='POST',
        data=urllib.parse.urlencode(fields).encode('ascii'),
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout_s=timeout_s,
    )

    _check_granted_scope(tokens)

    return _required_string(tokens, 'access_token')


##


def _pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode('ascii')).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')


def _open_authorization_url(url: str) -> None:
    print(f'Open this URL in a browser on this machine:\n{url}', file=sys.stderr)

    try:
        webbrowser.open(url, new=1)
    except (webbrowser.Error, OSError):
        pass  # The printed URL remains available for manual opening.


class _LoopbackServer(http.server.HTTPServer):
    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(5.0)
        return connection, address


def authorize_desktop_client(
        client_config: ta.Mapping[str, ta.Any],
        *,
        login_hint: str | None = None,
        on_authorization_url: ta.Callable[[str], None] = _open_authorization_url,
        consent_timeout_s: float = 300.0,
        request_timeout_s: float = 60.0,
) -> GoogleUserCredentials:
    """Perform consent on the browser's machine using downloaded Desktop client JSON."""

    installed = client_config.get('installed')
    if not isinstance(installed, dict):
        raise ValueError('Download an OAuth client of type Desktop app (an "installed" JSON object)')

    client_id = _required_string(installed, 'client_id')
    client_secret = installed.get('client_secret', '')
    if not isinstance(client_secret, str):
        raise ValueError('Invalid client_secret')

    if consent_timeout_s <= 0:
        raise ValueError('consent_timeout_s must be positive')

    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    result: dict[str, str] = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # Callback URLs contain authorization codes. Never log them.

        def _reply(self, status: int, message: str) -> None:
            body = message.encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            parts = urllib.parse.urlsplit(self.path)
            if parts.path != '/':
                self._reply(404, 'Not found.\n')
                return

            try:
                query = urllib.parse.parse_qs(parts.query, keep_blank_values=True, max_num_fields=20)
            except ValueError:
                self._reply(400, 'Invalid callback.\n')
                return

            states = query.get('state', [])
            if len(states) != 1 or not secrets.compare_digest(states[0].encode('utf-8'), state.encode('ascii')):
                self._reply(400, 'Invalid OAuth state.\n')
                return

            errors = query.get('error', [])
            codes = query.get('code', [])

            if len(errors) == 1 and errors[0] and not codes:
                result['error'] = errors[0]
                self._reply(200, 'Authorization was declined. You may close this window.\n')

            elif len(codes) == 1 and codes[0] and not errors:
                result['code'] = codes[0]
                self._reply(200, 'Authorization response received. Return to the terminal for the result.\n')

            else:
                self._reply(400, 'Invalid callback.\n')

    with _LoopbackServer(('127.0.0.1', 0), Handler) as server:
        redirect_uri = f'http://127.0.0.1:{server.server_port}/'

        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': DRIVE_FILE_SCOPE,
            'state': state,
            'code_challenge': _pkce_challenge(verifier),
            'code_challenge_method': 'S256',
            'access_type': 'offline',
            'prompt': 'consent select_account',
        }

        if login_hint:
            params['login_hint'] = login_hint

        deadline = time.monotonic() + consent_timeout_s

        on_authorization_url(AUTH_URL + '?' + urllib.parse.urlencode(params))

        while not result:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('Timed out waiting for Google authorization')

            server.timeout = min(1.0, remaining)
            server.handle_request()

    if 'error' in result:
        raise RuntimeError(f'Google authorization failed: {result["error"]}')

    fields = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'code': result['code'],
        'code_verifier': verifier,
    }

    if client_secret:
        fields['client_secret'] = client_secret

    tokens = _request_json(
        TOKEN_URL,
        method='POST',
        data=urllib.parse.urlencode(fields).encode('ascii'),
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout_s=request_timeout_s,
    )

    _check_granted_scope(tokens)

    return GoogleUserCredentials(
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=_required_string(tokens, 'refresh_token'),
    )


##


def _encode_multipart_related(
        metadata: ta.Mapping[str, ta.Any],
        content: bytes,
        content_type: str,
) -> tuple[bytes, str]:
    metadata_bytes = json.dumps(metadata, ensure_ascii=False).encode('utf-8')

    while True:
        boundary = ('gdoc_' + secrets.token_hex(16)).encode('ascii')
        if boundary not in metadata_bytes and boundary not in content:
            break

    body = b''.join([
        b'--' + boundary + b'\r\n',
        b'Content-Type: application/json; charset=UTF-8\r\n\r\n',
        metadata_bytes,
        b'\r\n--' + boundary + b'\r\n',
        b'Content-Type: ' + content_type.encode('ascii') + b'; charset=UTF-8\r\n\r\n',
        content,
        b'\r\n--' + boundary + b'--\r\n',
    ])

    return body, f'multipart/related; boundary="{boundary.decode("ascii")}"'


@dc.dataclass(frozen=True)
class CreatedGoogleDoc:
    document_id: str
    title: str
    url: str


def get_import_formats(access_token: str, *, timeout_s: float = 60.0) -> list[str]:
    """Return this account's input MIME types that can be converted to Google Docs."""

    response = _request_json(
        DRIVE_URL + '/about?fields=importFormats',
        headers={'Authorization': f'Bearer {access_token}'},
        timeout_s=timeout_s,
    )

    formats = response.get('importFormats')
    if not isinstance(formats, dict):
        raise ValueError('Missing importFormats in Google response')

    return sorted(k for k, v in formats.items() if isinstance(v, list) and GOOGLE_DOC_MIME_TYPE in v)


def create_google_doc(
        access_token: str,
        title: str,
        text: str,
        *,
        input_mime_type: str = 'text/plain',
        parent_id: str | None = None,
        timeout_s: float = 60.0,
) -> CreatedGoogleDoc:
    """Create in My Drive by default. This does not add sharing permissions or retry."""

    if not title:
        raise ValueError('title must not be empty')
    if input_mime_type not in INPUT_MIME_TYPES.values():
        raise ValueError('Use text/plain, text/html, or text/markdown')
    if parent_id is not None and not parent_id:
        raise ValueError('parent_id must not be empty')

    metadata: dict[str, ta.Any] = {'name': title, 'mimeType': GOOGLE_DOC_MIME_TYPE}
    if parent_id is not None:
        metadata['parents'] = [parent_id]

    query = {
        'fields': 'id,name,mimeType,webViewLink',
        # Bypass domain-wide default visibility; parent permissions still apply.
        'ignoreDefaultVisibility': 'true',
    }

    if text:
        body, content_type = _encode_multipart_related(
            metadata,
            text.encode('utf-8'),
            input_mime_type,
        )
        query['uploadType'] = 'multipart'
        base_url = UPLOAD_URL

    else:
        # An empty Doc needs no upload or import operation.
        body = json.dumps(metadata).encode('utf-8')
        content_type = 'application/json; charset=utf-8'
        base_url = DRIVE_URL + '/files'

    if len(body) > MAX_UPLOAD_BYTES:
        raise ValueError('Request exceeds this helper\'s 5 MB cap; use a resumable upload implementation')

    response = _request_json(
        base_url + '?' + urllib.parse.urlencode(query),
        method='POST',
        data=body,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': content_type,
        },
        timeout_s=timeout_s,
    )

    document_id = _required_string(response, 'id')

    if response.get('mimeType') != GOOGLE_DOC_MIME_TYPE:
        raise RuntimeError(f'File {document_id!r} was created but was not returned as a native Google Doc')

    url = response.get('webViewLink')
    if not isinstance(url, str) or not url:
        url = f'https://docs.google.com/document/d/{urllib.parse.quote(document_id, safe="")}/edit'

    return CreatedGoogleDoc(document_id=document_id, title=response.get('name', title), url=url)


##


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='command', required=True)

    auth_parser = subparsers.add_parser(
        'auth',
        help='One-time browser consent on this machine',
    )
    auth_parser.add_argument(
        '--client',
        required=True,
        help='Downloaded Desktop OAuth client JSON',
    )
    auth_parser.add_argument(
        '--credentials',
        required=True,
        help='Output refresh-token credentials JSON',
    )
    auth_parser.add_argument(
        '--login-hint',
        help='Optional account email hint, not an identity check',
    )
    auth_parser.add_argument(
        '--no-browser',
        action='store_true',
        help='Print URL without launching a browser',
    )

    create_parser = subparsers.add_parser(
        'create',
        help='Create a Doc and print its URL',
    )
    create_parser.add_argument(
        '--credentials',
        required=True,
    )
    create_parser.add_argument(
        '--title',
        required=True,
    )
    create_parser.add_argument(
        '--format',
        choices=tuple(INPUT_MIME_TYPES),
        default='text',
    )
    create_parser.add_argument(
        '--parent',
        help='An app-accessible My Drive folder ID; may inherit sharing',
    )
    create_parser.add_argument(
        '--json',
        action='store_true',
        help='Print ID, title, and URL as JSON',
    )
    create_parser.add_argument(
        'input',
        nargs='?',
        default='-',
        help='UTF-8 input file, or - for stdin',
    )

    formats_parser = subparsers.add_parser(
        'formats',
        help='List input MIME types for Google Doc conversion',
    )
    formats_parser.add_argument(
        '--credentials',
        required=True,
    )

    args = parser.parse_args()
    try:
        if args.command == 'auth':
            with open(os.path.expanduser(args.client), encoding='utf-8') as f:
                client_config = json.load(f)
            if not isinstance(client_config, dict):
                raise ValueError('Expected a Desktop client JSON object')

            callback = _open_authorization_url
            if args.no_browser:
                callback = lambda url: print(url, file=sys.stderr)

            credentials = authorize_desktop_client(
                client_config,
                login_hint=args.login_hint,
                on_authorization_url=callback,
            )

            save_credentials(args.credentials, credentials)

            print(f'Saved credentials to {args.credentials}', file=sys.stderr)

        else:
            credentials = load_credentials(args.credentials)

            if args.command == 'formats':
                token = refresh_access_token(credentials)
                print('\n'.join(get_import_formats(token)))

            else:
                if args.input == '-':
                    raw = sys.stdin.buffer.read(MAX_UPLOAD_BYTES + 1)
                else:
                    with open(os.path.expanduser(args.input), 'rb') as f:
                        raw = f.read(MAX_UPLOAD_BYTES + 1)
                if len(raw) > MAX_UPLOAD_BYTES:
                    raise ValueError('Input exceeds this helper\'s 5 MB cap')

                text = raw.decode('utf-8')
                token = refresh_access_token(credentials)

                doc = create_google_doc(
                    token,
                    args.title,
                    text,
                    input_mime_type=INPUT_MIME_TYPES[args.format],
                    parent_id=args.parent,
                )

                print(json.dumps(dc.asdict(doc), ensure_ascii=False) if args.json else doc.url)

    except (GoogleApiError, RuntimeError, ValueError, OSError) as exc:
        parser.exit(1, f'error: {exc}\n')


if __name__ == '__main__':
    _main()
