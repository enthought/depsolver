import sys

if sys.version_info[:2] < (2, 7):
    import unittest2 as unittest
else:
    import unittest

from depsolver.debian_version \
    import \
        DebianVersion, is_valid_debian_version

V = DebianVersion.from_string

class TestVersionParsing(unittest.TestCase):
    def test_valid_versions(self):
        versions = ["1.2.0", "1.2.3~1", "0:1.2.3~1"]

        for version in versions:
            self.assertTrue(is_valid_debian_version(version))

class TestVersionComparison(unittest.TestCase):
    def test_eq(self):
        self.assertTrue(V("1.2.3") == V("0:1.2.3"))
        self.assertTrue(V("1.2.3") == V("1.2.3~0"))
        self.assertFalse(V("1.2.3") == V("1:1.2.3"))
