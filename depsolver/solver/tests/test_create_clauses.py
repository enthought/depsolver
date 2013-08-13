import unittest

from depsolver.package \
    import \
        PackageInfo
from depsolver.pool \
    import \
        Pool
from depsolver.repository \
    import \
        Repository
from depsolver.requirement \
    import \
        Requirement

from depsolver.solver.create_clauses \
    import \
        create_depends_rule, create_install_rules, iter_conflict_rules
from depsolver.solver.rule \
    import \
        PackageInfoLiteral, PackageInfoNot, PackageInfoRule

P = PackageInfo.from_string
R = Requirement.from_string

class TestPackageInfoRule(unittest.TestCase):
    def setUp(self):
        self.mkl_10_1_0 = P("mkl-10.1.0")
        self.mkl_10_2_0 = P("mkl-10.2.0")
        self.mkl_10_3_0 = P("mkl-10.3.0")
        self.mkl_11_0_0 = P("mkl-11.0.0")

        self.numpy_1_6_0 = P("numpy-1.6.0; depends (mkl)")
        self.numpy_1_6_1 = P("numpy-1.6.1; depends (mkl)")
        self.numpy_1_7_0 = P("numpy-1.7.0; depends (mkl)")

        self.nomkl_numpy_1_6_0 = P("nomkl_numpy-1.6.0; provides(numpy == 1.6.0)")
        self.nomkl_numpy_1_6_1 = P("nomkl_numpy-1.6.1; provides(numpy == 1.6.1)")
        self.nomkl_numpy_1_7_0 = P("nomkl_numpy-1.7.0; provides(numpy == 1.7.0)")

        self.mkl_numpy_1_6_1 = P("mkl_numpy-1.6.1; provides(numpy == 1.6.1); depends (mkl)")
        self.mkl_numpy_1_7_0 = P("mkl_numpy-1.7.0; provides(numpy == 1.7.0); depends (mkl)")

        self.scipy_0_11_0 = P("scipy-0.11.0; depends (numpy >= 1.4.0)")
        self.scipy_0_12_0 = P("scipy-0.12.0; depends (numpy >= 1.4.0)")

        self.matplotlib_1_2_0 = P("matplotlib-1.2.0; depends (numpy >= 1.6.0)")

        repo = Repository([self.mkl_10_1_0, self.mkl_10_2_0, self.mkl_10_3_0,
                           self.mkl_11_0_0, self.numpy_1_6_0])
        pool = Pool()
        pool.add_repository(repo)

        self.pool = pool

    @unittest.expectedFailure
    def test_or(self):
        rule = PackageInfoRule.from_packages([mkl_10_1_0, mkl_10_2_0], self.pool)
        rule |= PackageInfoNot.from_package(mkl_11_0_0, self.pool)

        self.assertTrue(rule.literals, set([mkl_11_0_0.id, mkl_10_1_0.id, mkl_10_2_0.id]))

    @unittest.expectedFailure
    def test_repr(self):
        rule_repr = repr(PackageInfoRule.from_packages([mkl_11_0_0, mkl_10_1_0, mkl_10_2_0], self.pool))
        self.assertEqual(rule_repr, "(+mkl-10.1.0 | +mkl-10.2.0 | +mkl-11.0.0)")

        rule_repr = repr(PackageInfoRule([PackageInfoNot.from_package(mkl_10_2_0, self.pool)], self.pool) \
                | PackageInfoRule.from_packages([mkl_11_0_0], self.pool))
        self.assertEqual(rule_repr, "(-mkl-10.2.0 | +mkl-11.0.0)")

    @unittest.expectedFailure
    def test_from_package_string(self):
        rule = PackageInfoRule.from_string("mkl-11.0.0", self.pool)
        self.assertEqual(rule, PackageInfoRule.from_packages([mkl_11_0_0], self.pool))

        rule = PackageInfoRule.from_string("mkl-10.2.0 | mkl-11.0.0", self.pool)
        self.assertEqual(rule, PackageInfoRule.from_packages([mkl_10_2_0, mkl_11_0_0], self.pool))

        rule = PackageInfoRule.from_string("-mkl-10.2.0 | mkl-11.0.0", self.pool)
        self.assertEqual(rule,
                PackageInfoRule([PackageInfoNot.from_package(mkl_10_2_0, self.pool),
                             PackageInfoLiteral.from_package(mkl_11_0_0, self.pool)], self.pool))

        rule = PackageInfoRule.from_string("-mkl-10.2.0 | -mkl-11.0.0", self.pool)
        self.assertEqual(rule,
                PackageInfoRule([PackageInfoNot.from_package(mkl_10_2_0, self.pool),
                             PackageInfoNot.from_package(mkl_11_0_0, self.pool)],
                            self.pool))

class TestCreateClauses(unittest.TestCase):
    def setUp(self):
        self.mkl_10_1_0 = P("mkl-10.1.0")
        self.mkl_10_2_0 = P("mkl-10.2.0")
        self.mkl_10_3_0 = P("mkl-10.3.0")
        self.mkl_11_0_0 = P("mkl-11.0.0")

        self.numpy_1_6_0 = P("numpy-1.6.0; depends (mkl)")

        repo = Repository([self.mkl_10_1_0, self.mkl_10_2_0, self.mkl_10_3_0,
            self.mkl_11_0_0, self.numpy_1_6_0])
        pool = Pool()
        pool.add_repository(repo)

        self.pool = pool

    @unittest.expectedFailure
    def test_create_depends_rule(self):
        r_rule = PackageInfoRule.from_string(
                    "-numpy-1.6.0 | mkl-10.1.0 | mkl-10.2.0 | mkl-10.3.0 | mkl-11.0.0",
                    self.pool)
        rule = create_depends_rule(self.pool, numpy_1_6_0, R("mkl"))

        self.assertEqual(rule, r_rule)

    @unittest.expectedFailure
    def test_iter_conflict_rules(self):
        # Making sure single package corner-case works
        self.assertEqual(set(), set(iter_conflict_rules(self.pool, [mkl_10_1_0])))

        # 3 packages conflicting with each other -> 3 rules (C_3^2)
        r_rules = set()
        r_rules.add(PackageInfoRule.from_string("-mkl-10.1.0 | -mkl-10.2.0", self.pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.1.0 | -mkl-10.3.0", self.pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.2.0 | -mkl-10.3.0", self.pool))

        self.assertEqual(r_rules,
                set(iter_conflict_rules(self.pool, [mkl_10_1_0, mkl_10_2_0, mkl_10_3_0])))

class TestCreateInstallClauses(unittest.TestCase):
    def setUp(self):
        self.mkl_10_1_0 = P("mkl-10.1.0")
        self.mkl_10_2_0 = P("mkl-10.2.0")
        self.mkl_10_3_0 = P("mkl-10.3.0")
        self.mkl_11_0_0 = P("mkl-11.0.0")

        self.numpy_1_6_0 = P("numpy-1.6.0; depends (mkl)")
        self.numpy_1_6_1 = P("numpy-1.6.1; depends (mkl)")
        self.numpy_1_7_0 = P("numpy-1.7.0; depends (mkl)")

        self.mkl_numpy_1_6_0 = P("mkl_numpy-1.6.0; depends (mkl); provides (numpy == 1.6.0)")
        self.mkl_numpy_1_6_1 = P("mkl_numpy-1.6.1; depends (mkl); provides (numpy == 1.6.1)")
        self.mkl_numpy_1_7_0 = P("mkl_numpy-1.7.0; depends (mkl); provides (numpy == 1.7.0)")

        repo = Repository([self.mkl_10_1_0, self.mkl_10_2_0, self.mkl_10_3_0,
            self.mkl_11_0_0, self.numpy_1_6_0, self.numpy_1_6_1, self.numpy_1_7_0])
        pool = Pool()
        pool.add_repository(repo)

        self.pool = pool

    @unittest.expectedFailure
    def test_create_install_rules_simple(self):
        r_rules = set()
        r_rules.add(PackageInfoRule.from_string(
            "mkl-10.1.0 | mkl-10.2.0 | mkl-10.3.0 | mkl-11.0.0", self.pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.1.0 | -mkl-10.2.0", self.pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.1.0 | -mkl-10.3.0", self.pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.1.0 | -mkl-11.0.0", self.pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.2.0 | -mkl-10.3.0", self.pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.2.0 | -mkl-11.0.0", self.pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.3.0 | -mkl-11.0.0", self.pool))

        self.assertEqual(r_rules,
                set(create_install_rules(self.pool, R("mkl"))))

    @unittest.expectedFailure
    def test_create_install_rules_simple_dependency(self):
        # Installed requirement has only one provide
        repo = Repository([mkl_10_1_0, mkl_10_2_0, mkl_10_3_0, mkl_11_0_0, numpy_1_7_0])
        pool = Pool()
        pool.add_repository(repo)

        r_rules = set()
        r_rules.add(PackageInfoRule.from_string("numpy-1.7.0", pool))
        r_rules.add(PackageInfoRule.from_string(
            "-numpy-1.7.0 | mkl-10.1.0 | mkl-10.2.0 | mkl-10.3.0 | mkl-11.0.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.1.0 | -mkl-10.2.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.1.0 | -mkl-10.3.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.1.0 | -mkl-11.0.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.2.0 | -mkl-10.3.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.2.0 | -mkl-11.0.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.3.0 | -mkl-11.0.0", pool))

        self.assertEqual(r_rules,
                set(create_install_rules(pool, R("numpy"))))

    @unittest.expectedFailure
    def test_multiple_install_provides(self):
        # Installed requirement has > 1 one provide
        repo = Repository([mkl_10_1_0, mkl_10_2_0, mkl_10_3_0, mkl_11_0_0,
            numpy_1_6_1, numpy_1_7_0])
        pool = Pool()
        pool.add_repository(repo)

        r_rules = set()
        r_rules.add(PackageInfoRule.from_string("numpy-1.7.0 | numpy-1.6.1", pool))
        r_rules.add(PackageInfoRule.from_string("-numpy-1.7.0 | -numpy-1.6.1", pool))
        r_rules.add(PackageInfoRule.from_string(
            "-numpy-1.7.0 | mkl-10.1.0 | mkl-10.2.0 | mkl-10.3.0 | mkl-11.0.0", pool))
        r_rules.add(PackageInfoRule.from_string(
            "-numpy-1.6.1 | mkl-10.1.0 | mkl-10.2.0 | mkl-10.3.0 | mkl-11.0.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.1.0 | -mkl-10.2.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.1.0 | -mkl-10.3.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.1.0 | -mkl-11.0.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.2.0 | -mkl-10.3.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.2.0 | -mkl-11.0.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.3.0 | -mkl-11.0.0", pool))

        self.assertEqual(r_rules,
                set(create_install_rules(pool, R("numpy"))))

    @unittest.expectedFailure
    def test_multiple_provided_names_single_install_provide(self):
        # Installed requirement has 1 one provide, but multiple provides for
        # the same name are available in the pool
        repo = Repository([mkl_10_1_0, mkl_10_2_0, mkl_10_3_0, mkl_11_0_0,
            numpy_1_6_1, numpy_1_7_0])
        pool = Pool()
        pool.add_repository(repo)

        r_rules = set()
        r_rules.add(PackageInfoRule.from_string("numpy-1.7.0", pool))
        r_rules.add(PackageInfoRule.from_string("-numpy-1.7.0 | -numpy-1.6.1", pool))
        r_rules.add(PackageInfoRule.from_string(
            "-numpy-1.7.0 | mkl-10.1.0 | mkl-10.2.0 | mkl-10.3.0 | mkl-11.0.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.1.0 | -mkl-10.2.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.1.0 | -mkl-10.3.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.1.0 | -mkl-11.0.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.2.0 | -mkl-10.3.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.2.0 | -mkl-11.0.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.3.0 | -mkl-11.0.0", pool))

        self.assertEqual(r_rules,
                set(create_install_rules(pool, R("numpy == 1.7.0"))))

    @unittest.expectedFailure
    def test_already_installed_indirect_provided(self):
        # Installed requirement has one dependency with multiple provides for
        # the same name available in the pool, one of which is already
        # installed. Here: scipy depends on numpy, nomkl_numpy is also
        # available and already installed
        repo = Repository([mkl_11_0_0, nomkl_numpy_1_7_0, numpy_1_7_0, scipy_0_11_0])
        pool = Pool()
        pool.add_repository(repo)

        r_rules = set()
        r_rules.add(PackageInfoRule.from_string("scipy-0.11.0", pool))
        r_rules.add(PackageInfoRule.from_string("-scipy-0.11.0 | numpy-1.7.0 | nomkl_numpy-1.7.0", pool))
        r_rules.add(PackageInfoRule.from_string("-numpy-1.7.0 | -nomkl_numpy-1.7.0", pool))
        r_rules.add(PackageInfoRule.from_string(
            "-numpy-1.7.0 | mkl-11.0.0", pool))

        self.assertEqual(r_rules,
                set(create_install_rules(pool, R("scipy"))))

    @unittest.expectedFailure
    def test_complex_scenario_1(self):
        repo = Repository([mkl_10_1_0, mkl_10_2_0, mkl_10_3_0, mkl_11_0_0,
            numpy_1_6_0, numpy_1_6_1, numpy_1_7_0, scipy_0_11_0, scipy_0_12_0])
        pool = Pool()
        pool.add_repository(repo)

        r_rules = set()
        r_rules.add(PackageInfoRule.from_string("scipy-0.11.0 | scipy-0.12.0", pool))
        r_rules.add(PackageInfoRule.from_string("-scipy-0.11.0 | -scipy-0.12.0", pool))
        r_rules.add(PackageInfoRule.from_string(
                    "-scipy-0.11.0 | numpy-1.6.0 | numpy-1.6.1 | numpy-1.7.0",
                    pool))
        r_rules.add(PackageInfoRule.from_string(
                    "-scipy-0.12.0 | numpy-1.6.0 | numpy-1.6.1 | numpy-1.7.0",
                    pool))
        r_rules.add(PackageInfoRule.from_string("-numpy-1.7.0 | -numpy-1.6.1", pool))
        r_rules.add(PackageInfoRule.from_string("-numpy-1.7.0 | -numpy-1.6.0", pool))
        r_rules.add(PackageInfoRule.from_string("-numpy-1.6.0 | -numpy-1.6.1", pool))
        r_rules.add(PackageInfoRule.from_string(
            "-numpy-1.7.0 | mkl-10.1.0 | mkl-10.2.0 | mkl-10.3.0 | mkl-11.0.0", pool))
        r_rules.add(PackageInfoRule.from_string(
            "-numpy-1.6.1 | mkl-10.1.0 | mkl-10.2.0 | mkl-10.3.0 | mkl-11.0.0", pool))
        r_rules.add(PackageInfoRule.from_string(
            "-numpy-1.6.0 | mkl-10.1.0 | mkl-10.2.0 | mkl-10.3.0 | mkl-11.0.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.1.0 | -mkl-10.2.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.1.0 | -mkl-10.3.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.1.0 | -mkl-11.0.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.2.0 | -mkl-10.3.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.2.0 | -mkl-11.0.0", pool))
        r_rules.add(PackageInfoRule.from_string("-mkl-10.3.0 | -mkl-11.0.0", pool))

        self.assertEqual(r_rules,
                set(create_install_rules(pool, R("scipy"))))

    @unittest.expectedFailure
    def test_complex_scenario_2(self):
        repository = Repository([mkl_10_1_0, mkl_10_2_0, mkl_10_3_0, mkl_11_0_0,
            mkl_numpy_1_6_1, mkl_numpy_1_7_0, nomkl_numpy_1_7_0, matplotlib_1_2_0])
        pool = Pool()
        pool.add_repository(repository)

        installed_repository = Repository()
        installed_repository.add_package(mkl_10_3_0)
        installed_repository.add_package(mkl_numpy_1_7_0)
        pool.add_repository(installed_repository)

        R = PackageInfoRule.from_string
        r_rules = set()
        r_rules.add(R("mkl_numpy-1.6.1 | mkl_numpy-1.7.0 | nomkl_numpy-1.7.0", pool))
        r_rules.add(R("-mkl_numpy-1.6.1 | -nomkl_numpy-1.7.0", pool))
        r_rules.add(R("-mkl_numpy-1.7.0 | -nomkl_numpy-1.7.0", pool))
        r_rules.add(R("-mkl_numpy-1.6.1 | -mkl_numpy-1.7.0", pool))
        r_rules.add(R("-mkl_numpy-1.6.1 | mkl-10.1.0 | mkl-10.2.0 | mkl-10.3.0 | mkl-11.0.0", pool))
        r_rules.add(R("-mkl-10.1.0 | -mkl-11.0.0", pool))
        r_rules.add(R("-mkl-10.2.0 | -mkl-11.0.0", pool))
        r_rules.add(R("-mkl-10.3.0 | -mkl-11.0.0", pool))
        r_rules.add(R("-mkl-10.1.0 | -mkl-10.2.0", pool))
        r_rules.add(R("-mkl-10.1.0 | -mkl-10.3.0", pool))
        r_rules.add(R("-mkl-10.2.0 | -mkl-10.3.0", pool))
        r_rules.add(R("-mkl_numpy-1.7.0 | mkl-10.1.0 | mkl-10.2.0 | mkl-10.3.0 | mkl-11.0.0",
                    pool))

        self.assertEqual(r_rules,
                set(create_install_rules(pool, Requirement.from_string("numpy"))))
