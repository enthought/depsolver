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
from depsolver.solver.rule \
    import \
        Rule, Literal, PackageRule

P = PackageInfo.from_string

class TestLiteral(unittest.TestCase):
    def test_simple(self):
        a = Literal("a")
        self.assertTrue(a.evaluate({"a": True}))
        self.assertFalse(a.evaluate({"a": False}))

        self.assertFalse((~a).evaluate({"a": True}))
        self.assertTrue((~a).evaluate({"a": False}))

        self.assertRaises(ValueError, lambda: a.evaluate({}))

    def test_invalid_literal_name(self):
        self.assertRaises(ValueError, lambda: Literal("~a"))

    def test_repr(self):
        a = Literal("a")
        self.assertEqual(repr(a), "L('a')")
        self.assertEqual(repr(~a), "L('~a')")

    def test_clause(self):
        a = Literal("a")
        b = Literal("b")

        clause = a | b
        self.assertTrue(clause.evaluate({"a": True, "b": True}))
        self.assertTrue(clause.evaluate({"a": True, "b": False}))
        self.assertTrue(clause.evaluate({"a": False, "b": True}))
        self.assertFalse(clause.evaluate({"a": False, "b": False}))

class TestRule(unittest.TestCase):
    def test_simple(self):
        a = Literal("a")
        b = Literal("b")
        clause = Rule([a, b])

        self.assertEqual(clause.literal_names, ("a", "b"))
        self.assertFalse(clause.is_assertion)

        clause = Rule([a])

        self.assertTrue(clause.is_assertion)

    def test_create_from_string(self):
        clause = Rule.from_string("a | b | ~c")

        self.assertEqual(clause.literal_names, ("c", "a", "b"))
        self.assertTrue(clause.evaluate({"a": False, "b": False, "c": False}))

        clause = Rule.from_string("a | b | c")

        self.assertEqual(clause.literal_names, ("a", "b", "c"))
        self.assertFalse(clause.evaluate({"a": False, "b": False, "c": False}))

    def test_or(self):
        a = Literal("a")
        b = Literal("b")
        clause = Rule([a, b])
        clause |= Literal("c")

        self.assertEqual(clause.literal_names, ("a", "b", "c"))

        a = Literal("a")
        b = Literal("b")
        clause = Rule([a, b])

        c = Literal("c")
        d = Literal("d")
        clause |= Rule([c, d])

        self.assertEqual(clause.literal_names, ("a", "b", "c", "d"))

    def test_repr(self):
        a = Literal("a")
        b = Literal("b")
        clause = Rule([a, b])

        self.assertEqual(repr(clause), "C(a | b)")

        a = Literal("a")
        b = ~Literal("b")
        clause = Rule([a, b])

        self.assertEqual(clause, Rule.from_string("a | ~b"))

    def test_evaluate(self):
        a = Literal("a")
        b = Literal("b")
        clause = Rule([a, b])

        self.assertTrue(clause.evaluate({"a": True, "b": True}))
        self.assertFalse(clause.evaluate({"a": False, "b": False}))

        self.assertRaises(ValueError, lambda: clause.evaluate({"a": False}))

    def test_satisfies_or_none(self):
        clause = Rule.from_string("a | b")

        self.assertTrue(clause.satisfies_or_none({"a": True}))
        self.assertTrue(clause.satisfies_or_none({"b": True}))
        self.assertTrue(clause.satisfies_or_none({}) is None)
        self.assertTrue(clause.satisfies_or_none({"a": False}) is None)
        self.assertTrue(clause.satisfies_or_none({"a": False, "b": False}) is False)

class TestPackageRule(unittest.TestCase):
    def test_ctor_simple(self):
        repository = Repository([P("mkl-10.1.0"),
                                 P("numpy-1.7.0; depends (MKL >= 10.1.0)"),
                                 P("scipy-0.12.0; depends (numpy >= 1.7.0)")])
        pool = Pool([repository])

        rule = PackageRule(pool, [1, 2], "job_install")

        self.assertEqual(rule.enabled, True)
        self.assertEqual(rule.literals, [1, 2])
        self.assertEqual(rule.reason, "job_install")
        self.assertEqual(rule.rule_hash, "05cf2")

    def test_from_packages_simple(self):
        mkl = P("mkl-10.1.0")
        numpy = P("numpy-1.7.0; depends (MKL >= 10.1.0)")
        scipy = P("scipy-0.12.0; depends (numpy >= 1.7.0)")
        remote_repository = [mkl, numpy, scipy]

        i_mkl = P("mkl-10.1.0")
        installed_repository = [i_mkl]

        pool = Pool([Repository(remote_repository), Repository(installed_repository)])

        rule = PackageRule.from_packages(pool, [mkl, i_mkl], "job_install")

        self.assertEqual(rule.enabled, True)
        self.assertEqual(rule.literals, [mkl.id, i_mkl.id])
        self.assertEqual(rule.reason, "job_install")

    def test_repr_simple(self):
        repository = Repository([P("mkl-10.1.0"),
                                 P("numpy-1.7.0; depends (MKL >= 10.1.0)"),
                                 P("scipy-0.12.0; depends (numpy >= 1.7.0)")])
        pool = Pool([repository])

        rule = PackageRule(pool, [1, 2], "job_install")

        self.assertEqual(repr(rule), "(+mkl-10.1.0 | +numpy-1.7.0)")

        rule = PackageRule(pool, [-1, 2], "job_install")

        self.assertEqual(repr(rule), "(-mkl-10.1.0 | +numpy-1.7.0)")
