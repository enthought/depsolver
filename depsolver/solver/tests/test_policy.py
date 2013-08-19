import six

if six.PY3:
    import unittest
else:
    import unittest2 as unittest

from depsolver.package \
    import \
        PackageInfo
from depsolver.pool \
    import \
        Pool
from depsolver.repository \
    import \
        Repository
from depsolver.solver.policy \
    import \
        DefaultPolicy

P = PackageInfo.from_string

class TestDefaultPolicy(unittest.TestCase):
    def setUp(self):
        self.mkl_10_3_0 = P("mkl-10.3.0")
        self.mkl_11_0_0 = P("mkl-11.0.0")

    def test_simple(self):
        """Ensure the policy returns the highest version across a set of
        packages with the same name."""
        pool = Pool([Repository([self.mkl_10_3_0, self.mkl_11_0_0])])
        policy = DefaultPolicy()

        queue = [self.mkl_10_3_0.id, self.mkl_11_0_0.id]

        candidates = policy.prefered_package_ids(pool, {}, queue)
        self.assertEqual(list(candidates), [self.mkl_11_0_0.id])

    def test_simple_fulfilled_installed(self):
        """Ensure the policy returns the installed version first if it fulfills
        the requirement, even if higher versions are available."""
        mkl_10_4_0 = P("mkl-10.4.0")
        remote_repository = Repository([self.mkl_10_3_0, self.mkl_11_0_0])
        installed_repository = Repository([mkl_10_4_0])

        pool = Pool([installed_repository, remote_repository])
        policy = DefaultPolicy()

        queue = [p.id for p in [mkl_10_4_0, self.mkl_10_3_0, self.mkl_11_0_0]]

        candidates = policy.prefered_package_ids(pool, {}, queue)
        self.assertEqual(list(candidates), [self.mkl_11_0_0.id])

        candidates = policy.prefered_package_ids(pool, {mkl_10_4_0.id: True}, queue)
        self.assertEqual(list(candidates), [mkl_10_4_0.id, self.mkl_11_0_0.id])

    def test_simple_fulfilled_installed(self):
        """Ensure the policy returns the installed version first if it fulfills
        the requirement, even if higher versions are available."""
        mkl_10_4_0 = P("mkl-10.4.0")
        remote_repository = Repository([self.mkl_10_3_0, self.mkl_11_0_0], "remote")
        installed_repository = Repository([mkl_10_4_0], "installed")

        pool = Pool([installed_repository, remote_repository])
        pool.set_repository_order("installed", "remote")
        policy = DefaultPolicy()

        queue = [p.id for p in [mkl_10_4_0, self.mkl_10_3_0, self.mkl_11_0_0]]

        candidates = policy.prefered_package_ids(pool, {}, queue)
        self.assertEqual(list(candidates), [self.mkl_11_0_0.id])

        candidates = policy.prefered_package_ids(pool, {mkl_10_4_0.id: True}, queue)
        self.assertEqual(list(candidates), [mkl_10_4_0.id, self.mkl_11_0_0.id])

    def test_cmp_by_priority_prefer_installed_same_repository_simple(self):
        """
        Check packages from a same repository are sorted by their id.
        """
        numpy_1_6_0 = P("numpy-1.6.0")
        numpy_1_6_1 = P("numpy-1.6.1")
        numpy_1_7_0 = P("numpy-1.7.0")

        remote_repository = Repository([numpy_1_7_0, numpy_1_6_1, numpy_1_6_0], "remote")
        r_sorted_packages = [numpy_1_7_0, numpy_1_6_1, numpy_1_6_0]

        pool = Pool([remote_repository])
        policy = DefaultPolicy()

        queue = [numpy_1_7_0, numpy_1_6_0, numpy_1_6_1]
        def _cmp(a, b):
            return policy.cmp_by_priority_prefer_installed(pool, {}, a, b)

        self.assertEqual(r_sorted_packages, sorted(queue, cmp=_cmp))

    def test_cmp_by_priority_prefer_installed_multi_repositories(self):
        """
        Check packages from multiple repositories are sorted accordingt to
        repository priority.
        """
        numpy_1_6_0 = P("numpy-1.6.0")
        numpy_1_6_1 = P("numpy-1.6.1")
        numpy_1_7_0 = P("numpy-1.7.0")
        i_numpy_1_6_0 = P("numpy-1.6.0")

        remote_repository = Repository([numpy_1_7_0, numpy_1_6_1, numpy_1_6_0], "remote")
        installed_repository = Repository([i_numpy_1_6_0], "installed")

        r_sorted_packages = [i_numpy_1_6_0, numpy_1_7_0, numpy_1_6_1, numpy_1_6_0]

        pool = Pool([installed_repository, remote_repository])
        pool.set_repository_order("installed", "remote")
        policy = DefaultPolicy()

        queue = [numpy_1_7_0, i_numpy_1_6_0, numpy_1_6_0, numpy_1_6_1]
        def _cmp(a, b):
            return policy.cmp_by_priority_prefer_installed(pool, {}, a, b)

        self.assertEqual(r_sorted_packages, sorted(queue, cmp=_cmp))

    def test_cmp_by_priority_prefer_installed_replace(self):
        """
        Check replaced packages take priority over replacing ones then they
        come from the same repository.
        """
        def _assert_sort_by_priority(package, r_sorted_packages):
            remote_repository = Repository(packages)
            pool = Pool([remote_repository])
            policy = DefaultPolicy()

            # We reverse the list to ensure queue is not originally in the
            # final order
            queue = reversed(packages)
            def _cmp(a, b):
                return policy.cmp_by_priority_prefer_installed(pool, {}, a, b)

            self.assertEqual(r_sorted_packages, sorted(queue, cmp=_cmp))

        scikits_0_12_0 = P("scikits_learn-0.12.0")
        sklearn_0_13_0 = P("sklearn-0.13.0")
        packages = [sklearn_0_13_0, scikits_0_12_0]
        r_sorted_packages = [sklearn_0_13_0, scikits_0_12_0]

        _assert_sort_by_priority(packages, r_sorted_packages)

        scikits_0_12_0 = P("scikits_learn-0.12.0")
        sklearn_0_13_0 = P("sklearn-0.13.0; replaces (scikits_learn < 0.13.0)")
        packages = [sklearn_0_13_0, scikits_0_12_0]
        r_sorted_packages = [scikits_0_12_0, sklearn_0_13_0]

        _assert_sort_by_priority(packages, r_sorted_packages)
