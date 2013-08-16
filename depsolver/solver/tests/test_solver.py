import six

if not six.PY3:
    import unittest2 as unittest
else:
    import unittest

from depsolver.pool \
    import \
        Pool
from depsolver.package \
    import \
        PackageInfo
from depsolver.repository \
    import \
        Repository
from depsolver.request \
    import \
        Request
from depsolver.requirement \
    import \
        Requirement
from depsolver.solver.core \
    import \
        Solver

P = PackageInfo.from_string
R = Requirement.from_string

class TestInstallMapCase(unittest.TestCase):
    def _create_solver(self, installed_packages, remote_packages):
        installed_repo = Repository(installed_packages)
        remote_repo = Repository(remote_packages)
        pool = Pool([installed_repo, remote_repo])

        return Solver(pool, installed_repo)

    def test_empty_installed_set(self):
        installed_packages = []
        remote_packages = [P("mkl-11.0.0")]

        solver = self._create_solver(installed_packages, remote_packages)

        request = Request(solver.pool)
        request.install(R("mkl"))

        solver._compute_package_maps(request)
        self.assertEqual(solver._id_to_installed_package, {})
        self.assertEqual(solver._id_to_updated_state, {})

    @unittest.expectedFailure
    def test_simple_install(self):
        installed_packages = [P("mkl-11.0.0")]
        remote_packages = [P("mkl-11.0.0")]

        solver = self._create_solver(installed_packages, remote_packages)

        request = Request(solver.pool)
        request.install(R("mkl"))

        solver._compute_package_maps(request)
        self.assertEqual(solver._id_to_installed_package, {1: P("mkl-11.0.0")})
        self.assertEqual(solver._id_to_updated_state, {})

    @unittest.expectedFailure
    def test_simple_update(self):
        installed_packages = [P("mkl-10.2.0")]
        remote_packages = [P("mkl-11.0.0")]

        solver = self._create_solver(installed_packages, remote_packages)

        request = Request(solver.pool)
        request.update(R("mkl"))

        solver._compute_package_maps(request)
        self.assertEqual(solver._id_to_installed_package, {1: P("mkl-10.2.0")})
        self.assertEqual(solver._id_to_updated_state, {1: True})

    @unittest.expectedFailure
    def test_simple_update_all(self):
        installed_packages = [P("mkl-10.2.0"), P("numpy-1.7.0")]
        remote_packages = [P("mkl-11.0.0"), P("numpy-1.7.1")]

        solver = self._create_solver(installed_packages, remote_packages)

        request = Request(solver.pool)
        request.upgrade()

        solver._compute_package_maps(request)
        self.assertEqual(solver._id_to_installed_package,
                         {1: P("mkl-10.2.0"), 2: P("numpy-1.7.0")})
        self.assertEqual(solver._id_to_updated_state, {1: True, 2: True})
