import hashlib
import unittest

import six

from depsolver.package \
    import \
        PackageInfo
from depsolver.repository \
    import \
        Repository
from depsolver.requirement \
    import \
        Requirement
from depsolver.version \
    import \
        Version

V = Version.from_string
R = Requirement.from_string

class TestPackageInfo(unittest.TestCase):
    def test_simple_construction(self):
        r_provides = []

        package = PackageInfo("numpy", V("1.3.0"))
        self.assertEqual(package.provides, r_provides)
        self.assertEqual(package.dependencies, [])
        self.assertEqual(package.id, -1)

        r_provides = [R("numpy == 1.3.0")]
        r_id = -1

        package = PackageInfo("nomkl_numpy", V("1.3.0"), provides=r_provides)
        self.assertEqual(package.provides, r_provides)
        self.assertEqual(package.id, r_id)

    def test_construction(self):
        r_provides = []

        package = PackageInfo(name="numpy", version=V("1.3.0"))
        self.assertEqual(package.provides, r_provides)
        self.assertEqual(package.dependencies, [])
        self.assertEqual(package.id, -1)

        r_provides = [R("numpy == 1.3.0")]
        r_id = -1

        package = PackageInfo(name="nomkl_numpy", version=V("1.3.0"), provides=r_provides)
        self.assertEqual(package.provides, r_provides)
        self.assertEqual(package.id, r_id)

    def test_unique_name(self):
        package = PackageInfo(name="numpy", version=V("1.3.0"))
        self.assertEqual(package.unique_name, "numpy-1.3.0")

    def test_str(self):
        provides = [R("numpy == 1.3.0")]
        package = PackageInfo(name="nomkl_numpy", version=V("1.3.0"), provides=provides)
        self.assertEqual(str(package), "nomkl_numpy-1.3.0")

    def test_repr(self):
        package = PackageInfo(name="numpy", version=V("1.3.0"))
        self.assertEqual(repr(package), "PackageInfo(u'numpy-1.3.0')")

        package = PackageInfo(name="numpy", version=V("1.6.0"), dependencies=[R("mkl >= 10.3.0")])
        self.assertEqual(repr(package), "PackageInfo(u'numpy-1.6.0; depends (mkl >= 10.3.0)')")

    def test_set_repository(self):
        package = PackageInfo(name="numpy", version=V("1.3.0"))
        package.repository = Repository()

        def set_repository():
            package.repository = Repository()
        self.assertRaises(ValueError, set_repository)

class TestPackageInfoFromString(unittest.TestCase):
    def test_simple(self):
        r_package = PackageInfo(name="numpy", version=V("1.3.0"))

        self.assertEqual(PackageInfo.from_string("numpy-1.3.0"), r_package)
        self.assertRaises(ValueError, lambda: PackageInfo.from_string("numpy 1.3.0"))

    def test_dependencies(self):
        r_package = PackageInfo(name="numpy", version=V("1.6.0"), dependencies=[R("mkl >= 10.3.0")])
        package = PackageInfo.from_string("numpy-1.6.0; depends (mkl >= 10.3.0)")

        self.assertEqual(package, r_package)

    def test_provides(self):
        r_package = PackageInfo(name="nomkl_numpy", version=V("1.6.0"), provides=[R("numpy == 1.6.0")])
        package = PackageInfo.from_string("nomkl_numpy-1.6.0; provides (numpy == 1.6.0)")

        self.assertEqual(package, r_package)
