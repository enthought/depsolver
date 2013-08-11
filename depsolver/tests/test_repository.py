import unittest

from depsolver.package \
    import \
        PackageInfo
from depsolver.repository \
    import \
        Repository
from depsolver.version \
    import \
        Version

numpy_1_6_1 = PackageInfo("numpy", Version.from_string("1.6.1"))
numpy_1_7_0 = PackageInfo("numpy", Version.from_string("1.7.0"))

scipy_0_11_0 = PackageInfo("scipy", Version.from_string("0.11.0"))

class TestRepository(unittest.TestCase):
    def test_simple_construction(self):
        repo = Repository()
        self.assertEqual(repo.list_packages(), [])

        r_packages = [numpy_1_6_1, numpy_1_7_0, scipy_0_11_0]

        repo = Repository(r_packages)
        packages = set(repo.iter_packages())
        self.assertEqual(packages, set(r_packages))

    @unittest.expectedFailure
    def test_has_package(self):
        packages = [numpy_1_6_1, numpy_1_7_0, scipy_0_11_0]
        repo = Repository(packages)

        self.assertTrue(repo.has_package(numpy_1_6_1))
        self.assertTrue(repo.has_package_name("numpy"))
        self.assertFalse(repo.has_package_name("floupi") is None)

    @unittest.expectedFailure
    def test_find_package(self):
        packages = [numpy_1_6_1, numpy_1_7_0, scipy_0_11_0]
        repo = Repository(packages)

        self.assertTrue(repo.find_package("numpy", "1.6.1"))
        self.assertTrue(repo.find_package("numpy", "1.7.0"))
        self.assertTrue(repo.find_package("numpy", "1.7.1") is None)

    @unittest.expectedFailure
    def test_add_package(self):
        packages = [numpy_1_6_1, numpy_1_7_0, scipy_0_11_0]

        repo = Repository()
        for package in packages:
            repo.add_package(package)

        self.assertTrue(repo.has_package(numpy_1_6_1))
        self.assertTrue(repo.has_package_name("numpy"))
