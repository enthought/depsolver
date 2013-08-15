import collections

from depsolver.errors \
    import \
        DepSolverError, UndefinedDecision

class DecisionsSet(object):
    """A DecisionsSet instance keeps track of decided literals (and the
    rational for each decision), and can infer new literals depending on
    their type."""
    def __init__(self, pool):
        self.pool = pool
        self._decision_map = collections.OrderedDict()
        self._decision_queue = {}

    def inference_rule(self, literal):
        """Returns the reason/why for the given literal inference."""
        decision = self._decision_queue.get(literal.name, None)
        if decision is not None:
            return decision
        else:
            raise UndefinedDecision("literal %s not decided" % literal.name)

    def infer(self, literal, why):
        """Set the decision set such as it satisfies the given literal.

        For any undecided literal::

            decisision.infer(literal, "some string")

        means the following is True::

            decisions.satisfies(literal)

        Parameter
        ---------
        literal: Literal
            a literal object
        why: str
            An explanation for the decision
        """
        self._add_decision(literal)
        self._decision_queue[literal.name] = why

    def is_decided(self, literal):
        """Return true if the given literal has already been inferred."""
        return literal.name in self._decision_map

    def is_unit(self, rule):
        return rule.is_unit(self._decision_map)

    def items(self):
        return self._decision_map.items()

    def satisfies(self, literal):
        """Return True if the literal has been decided and is satisfied
        under the current decision set.

        A literal is satisfied iif it is a Not literal and decided to False
        or a Literal and decided to True. An undecided literal is always
        unsatisfied.

        Parameters
        ----------
        literal: Literal
            A literal instance
        """
        if self.is_decided(literal):
            if isinstance(literal, Not):
                return not self._decision_map[literal.name]
            else:
                return self._decision_map[literal.name]
        else:
            return False

    def popitem(self):
        """Pop the last decision made."""
        literal_name, decision = self._decision_map.popitem()
        del self._decision_queue[literal_name]
        return literal_name, decision

    def satisfies_or_none(self, rule):
        return rule.satisfies_or_none(self._decision_map)

    def _add_decision(self, literal):
        literal_name = literal.name
        if literal_name in self._decision_map:
            raise DepSolverError("literal name %s already decided !" % literal_name)
        if isinstance(literal, Not):
            self._decision_map[literal_name] = False
        else:
            self._decision_map[literal_name] = True

    # Mapping protocol
    def __contains__(self, literal_name):
        return literal_name in self._decision_map

    def __len__(self):
        return len(self._decision_map)
