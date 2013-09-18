import collections

from depsolver.bundled.traitlets \
    import \
        HasTraits, Instance, List, Long
from depsolver.compat \
    import \
        OrderedDict
from depsolver.solver.rule \
    import \
        PackageRule

class WatchChain(HasTraits):
    _data = Instance(collections.deque)

    def __init__(self, data, **kw):
        super(WatchChain, self).__init__(_data=collections.deque(data), **kw)

class RuleWatchNode(HasTraits):
    rule = Instance(PackageRule)

    _watch1 = Long(-1)
    _watch2 = Long(-1)

    @property
    def literals(self):
        return self.rule.literals

    @property
    def watch1(self):
        return self._watch1

    @property
    def watch2(self):
        return self._watch2

    def __init__(self, rule, **kw):
        super(RuleWatchNode, self).__init__(rule=rule, **kw)
        if len(self.literals) > 0:
            self._watch1 = self.literals[0]
        else:
            self._watch1 = 0

        if len(self.literals) > 1:
            self._watch2 = self.literals[1]
        else:
            self._watch2 = 0

    def watch2_on_highest(self, decisions):
        """
        Places the second watch on the rule's literal, decided at the highest level
        """
        if len(rule.literals) >= 3:
            watch_level = 0
            for literal in self.literals:
                level = decisions.decision_level(literal)

                if level > watch_level:
                    self._watch2 = literal
                    watch_level = level

    def other_watch(self, literal):
        """
        Given one watched literal, this method returns the other watched
        literal
        """
        if self._watch1 == literal:
            return self._watch2
        else:
            return self._watch1

    def move_watch(self, from_literal, to_literal):
        """
        Moves a watch from one literal to another
        """
        if self._watch1 == from_literal:
            self._watch1 = to_literal
        else:
            self._watch2 = to_literal

class RulesWatchGraph(HasTraits):
    """
    The RulesWatchGraph efficiently propagates decisions to other rules
    """
    _watch_chains = Instance(OrderedDict)

    def __init__(self, **kw):
        super(RulesWatchGraph, self).__init__(_watch_chains=OrderedDict(), **kw)

    def insert(self, node):
        if not node.rule.is_assertion:
            for literal in (node.watch1, node.watch2):
                print("insert literal {}".format(literal))
                if not literal in self._watch_chains:
                    self._watch_chains[literal] = collections.deque()

                self._watch_chains[literal].appendleft(node)

    def propagate_literal(self, decided_literal, level, decisions):
        """
        Propagates a decision on a literal to all rules watching the literal

        If a decision, e.g. +A has been made, then all rules containing -A, e.g.
        (-A|+B|+C) now need to satisfy at least one of the other literals, so
        that the rule as a whole becomes true, since with +A applied the rule
        is now (false|+B|+C) so essentially (+B|+C).

        This means that all rules watching the literal -A need to be updated to
        watch 2 other literals which can still be satisfied instead. So literals
        that conflict with previously made decisions are not an option.

        Alternatively it can occur that a unit clause results: e.g. if in the
        above example the rule was (-A|+B), then A turning true means that
        B must now be decided true as well.

        Parameters
        ----------
        decided_literal: int
            The literal which was decided (A in our example)
        level: int
            The level at which the decision took place and at which all
            resulting decisions should be made.
        decisions: DecisionsSet
            Used to check previous decisions and to register decisions
            resulting from propagation

        Returns
        -------
        Rule|null If a conflict is found the conflicting rule is returned
        """
        print("propagate {} @ level {}".format(decided_literal, level))
        # we invert the decided literal here, example:
        # A was decided => (-A|B) now requires B to be true, so we look for
        # rules which are fulfilled by -A, rather than A.
        literal = -decided_literal

        chain = self._watch_chains.get(literal, [])
        while len(chain) > 0:
            node = chain.popleft()
            other_watch = node.other_watch(literal)

            if node.rule.enabled and not decisions.satisfy(other_watch):
                rule_literals = node.rule.literals

                def _filtre(rule_literal):
                    return literal != rule_literal and other_watch != rule_literal \
                            and not decisions.conflict(rule_literal)
                alternative_literals = [rule_literal for rule_literal in rule_literals if _filtre(rule_literal)]

                if len(alternative_literals) > 0:
                    self.move_watch(literal, alternative_literals[0], node)
                    continue

                if decisions.conflict(other_watch):
                    return node.rule

                decisions.decide(other_watch, level, node.rule)

        return None

    def move_watch(self, from_literal, to_literal, node):
        """
        Moves a rule node from one watch chain to another

        The rule node's watched literals are updated accordingly.

        Parameters
        ----------
        from_literal:
            A literal the node used to watch
        to_literal:
            A literal the node should watch now
        node:
            The rule node to be moved
        """
        print("moving from {} to {}".format(from_literal, to_literal))
        if not to_literal in self._watch_chains:
            self._watch_chains[to_literal] = collections.deque()

        node.move_watch(from_literal, to_literal)
        print "removing @ offset {}".format(len(self._watch_chains[from_literal])-1)
        self._watch_chains[from_literal].pop()
        self._watch_chains[to_literal].appendleft(node)
