import unittest

from depsolver.package \
    import \
        Package
from depsolver.pool \
    import \
        Pool
from depsolver.repository \
    import \
        Repository
from depsolver.request \
    import \
        _Job, Request
from depsolver.requirement \
    import \
        Requirement
from depsolver.version \
    import \
        Version

V = Version.from_string
R = Requirement.from_string

mkl_10_3_0 = Package("mkl", V("10.3.0"))
mkl_11_0_0 = Package("mkl", V("11.0.0"))

numpy_1_7_0 = Package("numpy", V("1.7.0"), dependencies=[R("mkl >= 11.0.0")])

scipy_0_12_0 = Package("scipy", V("0.12.0"), dependencies=[R("numpy >= 1.7.0")])

class TestRequest(unittest.TestCase):
    def setUp(self):
        repo = Repository([mkl_10_3_0, mkl_11_0_0, numpy_1_7_0, scipy_0_12_0])
        self.pool = Pool([repo])

    def test_simple_install(self):
        r_jobs = [
            _Job([scipy_0_12_0], "install", R("scipy")),
            _Job([numpy_1_7_0], "install", R("numpy")),
        ]

        request = Request(self.pool)
        request.install(R("scipy"))
        request.install(R("numpy"))

        self.assertEqual(request.jobs, r_jobs)

    def test_simple_update(self):
        r_jobs = [
            _Job([numpy_1_7_0], "update", R("numpy")),
        ]

        request = Request(self.pool)
        request.update(R("numpy"))

        self.assertEqual(request.jobs, r_jobs)

    def test_simple_remove(self):
        r_jobs = [
            _Job([numpy_1_7_0], "remove", R("numpy")),
        ]

        request = Request(self.pool)
        request.remove(R("numpy"))

        self.assertEqual(request.jobs, r_jobs)

    def test_simple_upgrade(self):
        r_jobs = [_Job([], "upgrade", None)]

        request = Request(self.pool)
        request.upgrade()

        self.assertEqual(request.jobs, r_jobs)
