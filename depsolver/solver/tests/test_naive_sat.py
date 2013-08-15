import collections

import unittest

from depsolver.solver.naive_sat \
    import \
        is_satisfiable

class TestSAT(unittest.TestCase):
    @unittest.expectedFailure
    def test_simple(self):
        clause = Literal("a") | Literal("b")

        res, variables = is_satisfiable(set([clause]))
        self.assertTrue(res)
        self.assertTrue(variables in [{"a": True, "b": True}, {"a": True, "b": False},
                                      {"a": False, "b": True}])

        clause = Literal("a") | ~Literal("b")

        res, variables = is_satisfiable(set([clause]))
        self.assertTrue(res)
        self.assertTrue(variables in [{"a": True, "b": True}, {"a": True, "b": False},
                                      {"a": False, "b": False}])

    @unittest.expectedFailure
    def test_clauses(self):
        clause1 = Rule([Literal("a")])
        clause2 = Rule([~Literal("a")])

        res, variables = is_satisfiable(set([clause1, clause2]))
        self.assertFalse(res)

        clause1 = Rule([Literal("a"), Literal("b")])
        clause2 = Rule([~Literal("a")])

        res, variables = is_satisfiable(set([clause1, clause2]))
        self.assertTrue(res)
        self.assertTrue(variables, {"a": False, "b": True})

    @unittest.expectedFailure
    def test_existing_variables(self):
        clause1 = Rule([Literal("a"), Literal("b")])
        clause2 = Rule([~Literal("a")])

        res, variables = is_satisfiable(set([clause1, clause2]))
        self.assertTrue(res)

        res, variables = is_satisfiable(set([clause1, clause2]),
                collections.OrderedDict({"a": True}))
        self.assertFalse(res)
