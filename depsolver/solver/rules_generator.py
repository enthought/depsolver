import itertools

from depsolver.bundled.traitlets \
    import \
        HasTraits, Dict, Enum, Instance, List, Long, Unicode
from depsolver.errors \
    import \
        MissingRequirementInPool
from depsolver.solver.policy \
    import \
        DefaultPolicy
from depsolver.pool \
    import \
        Pool
from depsolver.solver.rule \
    import \
        PackageInfoLiteral, PackageInfoNot, PackageRule

# FIXME: all that code below is a lot of crap
def iter_conflict_rules(pool, packages):
    """Create an iterator that yield every rule to fulfill the constraint that
    each package in the packages list conflicts with each other.

    The generated rules are of the form (-A | -B) for every (A, B) in the
    packages sequence (C_2^n / 2 = n(n-1)/2 for n packages)
    """
    for left, right in itertools.combinations(packages, 2):
        yield PackageInfoNot.from_package(left, pool) \
              | PackageInfoNot.from_package(right, pool)

def create_depends_rule(pool, package, dependency_req):
    """Creates the rule encoding that package depends on the dependency
    fulfilled by requirement.

    This dependency is of the form (-A | R1 | R2 | R3) where R* are the set of
    packages provided by the dependency requirement."""
    provided_dependencies = pool.what_provides(dependency_req, 'include_indirect')
    rule = PackageInfoNot.from_package(package, pool)
    for provided in provided_dependencies:
       rule |= PackageInfoLiteral.from_package(provided, pool)
    return rule

def create_install_rules(pool, req):
    """Creates the list of rules for the given install requirement."""
    clauses = []
    clauses_set = set()

    def _append_rule(rule):
        if not rule in clauses_set:
            clauses_set.add(rule)
            clauses.append(rule)

    def _extend_rules(rules):
        for rule in rules:
            _append_rule(rule)

    def _add_dependency_rules(req):
        provided = pool.what_provides(req, 'include_indirect')
        if len(provided) < 1:
            raise MissingRequirementInPool(req)
        else:
            obsolete_provided = pool.what_provides(req, 'any')
            _extend_rules(iter_conflict_rules(pool, obsolete_provided))

            for candidate in provided:
                for dependency_req in candidate.dependencies:
                    _append_rule(create_depends_rule(pool, candidate, dependency_req))
                    _extend_rules(_add_dependency_rules(dependency_req))
            return clauses

    provided = pool.what_provides(req)
    rule = PackageRule.from_packages(provided, pool)
    _append_rule(rule)
    return _add_dependency_rules(req)

class RulesSet(HasTraits):
    """
    Simple container of rules
    """
    unknown_rules = List(Instance(PackageRule))
    package_rules = List(Instance(PackageRule))
    job_rules = List(Instance(PackageRule))
    learnt_rules = List(Instance(PackageRule))

    rule_types = Enum(["unknown", "packages", "job", "learnt"])

    rules_by_hash = Dict()
    rules_by_id = List(Instance(PackageRule))

    def __init__(self, **kw):
        super(RulesSet, self).__init__(**kw)

    def __len__(self):
        return len(self.rules_by_id)

    def add_rule(self, rule, rule_type):
        if rule_type == "unknown":
            self.unknown_rules.append(rule)
        elif rule_type == "package":
            self.package_rules.append(rule)
        elif rule_type == "job":
            self.job_rules.append(rule)
        elif rule_type == "learnt":
            self.learnt_rules.append(rule)
        else:
            raise DepSolverError("Invalid rule_type %s" % (rule_type,))

        rule.id = len(self.rules_by_id)
        self.rules_by_id.append(rule)

        rules = self.rules_by_hash.get(rule.rule_hash, [])
        rules.append(rule)
        self.rules_by_hash[rule.rule_hash] = rules
