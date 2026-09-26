import ast
import os
import re

from .... import blobs
from ..stores import R2_CONFIG
from ..stores import S3_MOCK_CONFIG
from ..stores import S3BlobStore


def test_default_is_aws():
    c = S3BlobStore.Config()
    assert c.capabilities == (
        blobs.BlobCapability.PUT_IF_ABSENT |
        blobs.BlobCapability.PUT_IF_MATCH |
        blobs.BlobCapability.DELETE_IF_MATCH
    )
    assert (c.copy_dst_if_none_match_header, c.copy_dst_if_match_header) == ('If-None-Match', 'If-Match')
    assert not (c.no_list_url_encoding or c.unsigned_payload or c.streamed_uploads)


def test_presets():
    copy_caps = blobs.BlobCapability.COPY_IF_ABSENT | blobs.BlobCapability.COPY_IF_MATCH
    assert not (S3_MOCK_CONFIG.capabilities & copy_caps)
    assert R2_CONFIG.capabilities & blobs.BlobCapability.COPY_IF_ABSENT
    assert not (R2_CONFIG.capabilities & blobs.BlobCapability.DELETE_IF_MATCH)
    assert R2_CONFIG.copy_dst_if_none_match_header == 'cf-copy-destination-if-none-match'


_PROVIDER_PAT = re.compile(r'(?i)\b(r2|s3mock|s3_mock|minio|cloudflare)\b')


def _code_words(src):
    """Identifiers and non-docstring string constants - where provider branching would have to show up."""

    tree = ast.parse(src)
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.body and isinstance(b := node.body[0], ast.Expr) and isinstance(b.value, ast.Constant):
                docstrings.add(id(b.value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            yield node.value
        elif isinstance(node, ast.Name):
            yield node.id
        elif isinstance(node, ast.Attribute):
            yield node.attr


def test_no_provider_branching():
    """Provider differences live only in the Config presets at the bottom of stores.py - never in code paths."""

    aws_dir = os.path.dirname(os.path.dirname(__file__))
    for fn in sorted(os.listdir(aws_dir)):
        if not fn.endswith('.py'):
            continue
        with open(os.path.join(aws_dir, fn)) as f:
            src = f.read()
        if fn == 'stores.py':
            src = src[:src.index('# Cloudflare R2.')]
        bad = [w for w in _code_words(src) if _PROVIDER_PAT.search(w)]
        assert not bad, (fn, bad)
