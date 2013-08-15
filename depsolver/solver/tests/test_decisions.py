import unittest

from depsolver.errors \
    import \
        UndefinedDecision
from depsolver.package \
    import \
        PackageInfo
from depsolver.pool \
    import \
        Pool
from depsolver.repository \
    import \
        Repository
from depsolver.solver.decisions \
    import \
        DecisionsSet

P = PackageInfo.from_string

mkl_10_1_0 = P("mkl-10.1.0")
mkl_10_2_0 = P("mkl-10.2.0")
mkl_10_3_0 = P("mkl-10.3.0")
mkl_11_0_0 = P("mkl-11.0.0")

class TestDecisionsSet(unittest.TestCase):
    @unittest.expectedFailure
    def test_decided(self):
        pool = Pool([Repository([mkl_10_1_0, mkl_10_2_0, mkl_10_3_0, mkl_11_0_0])])
        decisions = DecisionsSet(pool)

        literal = PackageInfoLiteral.from_string("mkl-11.0.0", pool)
        not_literal = PackageInfoLiteral.from_string("-mkl-11.0.0", pool)
        another_literal = PackageInfoLiteral.from_string("mkl-10.3.0", pool)

        self.assertFalse(decisions.is_decided(literal))
        self.assertFalse(decisions.is_decided(not_literal))

        decisions.infer(literal, "dummy")

        self.assertTrue(decisions.is_decided(literal))
        self.assertTrue(decisions.is_decided(not_literal))

        self.assertFalse(decisions.is_decided(another_literal))

    @unittest.expectedFailure
    def test_infer(self):
        pool = Pool([Repository([mkl_10_1_0, mkl_10_2_0, mkl_10_3_0, mkl_11_0_0])])

        literal = PackageInfoLiteral.from_string("mkl-11.0.0", pool)
        not_literal = PackageInfoLiteral.from_string("-mkl-11.0.0", pool)
        another_literal = PackageInfoLiteral.from_string("mkl-10.3.0", pool)

        decisions = DecisionsSet(pool)
        decisions.infer(literal, "dummy")

        self.assertTrue(decisions.satisfies(literal))
        self.assertFalse(decisions.satisfies(not_literal))

        decisions = DecisionsSet(pool)
        decisions.infer(not_literal, "dummy")

        self.assertFalse(decisions.satisfies(literal))
        self.assertTrue(decisions.satisfies(not_literal))
        self.assertFalse(decisions.satisfies(another_literal))

    @unittest.expectedFailure
    def test_decision_rule(self):
        pool = Pool([Repository([mkl_10_1_0, mkl_10_2_0, mkl_10_3_0, mkl_11_0_0])])

        literal = PackageInfoLiteral.from_string("mkl-11.0.0", pool)
        another_literal = PackageInfoLiteral.from_string("mkl-10.3.0", pool)

        decisions = DecisionsSet(pool)
        decisions.infer(literal, "dummy")

        self.assertEqual(decisions.inference_rule(literal), "dummy")
        self.assertRaises(UndefinedDecision, lambda: decisions.inference_rule(another_literal))

    @unittest.expectedFailure
    def test_length(self):
        pool = Pool([Repository([mkl_10_1_0, mkl_10_2_0, mkl_10_3_0, mkl_11_0_0])])

        literal = PackageInfoLiteral.from_string("mkl-11.0.0", pool)
        another_literal = PackageInfoLiteral.from_string("mkl-10.3.0", pool)

        decisions = DecisionsSet(pool)

        self.assertEqual(len(decisions), 0)
        decisions.infer(literal, "dummy")
        self.assertEqual(len(decisions), 1)
        decisions.infer(another_literal, "dummy")
        self.assertEqual(len(decisions), 2)

    @unittest.expectedFailure
    def test_pop(self):
        pool = Pool([Repository([mkl_10_1_0, mkl_10_2_0, mkl_10_3_0, mkl_11_0_0])])

        literal = PackageInfoLiteral.from_string("mkl-11.0.0", pool)
        another_literal = PackageInfoLiteral.from_string("mkl-10.3.0", pool)

        decisions = DecisionsSet(pool)
        decisions.infer(literal, "dummy")
        decisions.infer(another_literal, "dummy")
        self.assertEqual(len(decisions), 2)
        decisions.popitem()
        self.assertEqual(len(decisions), 1)
        decisions.popitem()
        self.assertEqual(len(decisions), 0)

