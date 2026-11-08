# ruff: noqa: SLF001
# @om-lite
import ssl
import unittest

from .....io.pipelines.ssl.handlers import SslIoPipelineHandler
from ...base import HttpClientRequest
from ..sync import IoPipelineHttpClient


class TestIoPipelineHttpClientRequests(unittest.TestCase):
    def setUp(self) -> None:
        self._client = IoPipelineHttpClient()

    def test_non_default_port_is_in_host_header(self) -> None:
        prepared = self._client._prepare_request(HttpClientRequest('http://example.com:8080/path'))

        self.assertEqual(prepared.parsed_url.host, 'example.com')
        self.assertEqual(prepared.parsed_url.port, 8080)
        self.assertEqual(prepared.parsed_url.authority, 'example.com:8080')
        self.assertEqual(prepared.full_request.head.target, '/path')
        self.assertEqual(prepared.full_request.head.headers.single.get('host'), 'example.com:8080')

    def test_query_without_explicit_path_and_fragment(self) -> None:
        prepared = self._client._prepare_request(HttpClientRequest(
            'http://example.com?query=yes#not-sent',
        ))

        self.assertEqual(prepared.parsed_url.host, 'example.com')
        self.assertEqual(prepared.parsed_url.port, 80)
        self.assertEqual(prepared.parsed_url.authority, 'example.com')
        self.assertEqual(prepared.full_request.head.target, '/?query=yes')
        self.assertEqual(prepared.full_request.head.headers.single.get('host'), 'example.com')

    def test_ipv6_authority(self) -> None:
        prepared = self._client._prepare_request(HttpClientRequest('http://[::1]:8080/path'))

        self.assertEqual(prepared.parsed_url.host, '::1')
        self.assertEqual(prepared.parsed_url.port, 8080)
        self.assertEqual(prepared.parsed_url.authority, '[::1]:8080')
        self.assertEqual(prepared.full_request.head.headers.single.get('host'), '[::1]:8080')

    def test_explicit_default_port_is_preserved_in_authority(self) -> None:
        prepared = self._client._prepare_request(HttpClientRequest('https://example.com:443/'))

        self.assertEqual(prepared.parsed_url.port, 443)
        self.assertEqual(prepared.parsed_url.authority, 'example.com:443')
        self.assertEqual(prepared.full_request.head.headers.single.get('host'), 'example.com:443')

    def test_explicit_host_header_is_preserved(self) -> None:
        prepared = self._client._prepare_request(HttpClientRequest(
            'http://example.com:8080/',
            headers={'Host': 'virtual.example'},
        ))

        self.assertEqual(prepared.full_request.head.headers.single.get('host'), 'virtual.example')

    def test_provided_ssl_context_is_used(self) -> None:
        ssl_ctx = ssl.create_default_context()
        SslIoPipelineHandler.configure_ssl_context(ssl_ctx, SslIoPipelineHandler.Config.DEFAULT)
        prepared = IoPipelineHttpClient(ssl_ctx=ssl_ctx)._prepare_request(HttpClientRequest('https://example.com/'))

        ssl_handler = next(h for h in prepared.pipeline_spec.handlers if isinstance(h, SslIoPipelineHandler))
        self.assertIs(ssl_handler._ssl_ctx, ssl_ctx)

    def test_rejects_unsupported_urls(self) -> None:
        for url in (
                '/relative',
                'ftp://example.com/',
                'http://user:password@example.com/',
                'http://example.com:0/',
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                self._client._prepare_request(HttpClientRequest(url))
