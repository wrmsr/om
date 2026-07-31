# ruff: noqa: PT009
# @om-lite
import unittest

from ..linux import LinuxOsRelease


class TestLinuxOsRelease(unittest.TestCase):
    def test_variant_id(self):
        release = LinuxOsRelease({'VARIANT_ID': 'server'})

        self.assertEqual(release.variant_id, 'server')
