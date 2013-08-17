import six

from depsolver.errors \
    import \
        DepSolverError

from depsolver.compat \
    import \
        OrderedDict
from depsolver.bundled.traitlets \
    import \
        HasTraits, Instance

from depsolver.solver.decisions \
    import \
        DecisionsSet
from depsolver.operations \
    import \
        Install, Remove, Update
from depsolver.pool \
    import \
        Pool
from depsolver.repository \
    import \
        Repository
from depsolver.request \
    import \
        Request
from depsolver.solver.policy \
    import \
        DefaultPolicy
from depsolver.solver.rules_generator \
    import \
        RulesGenerator

# FIXME: the php model for this class is pretty broken as many attributes are
# initialized outside the ctor. Fix this.
class Solver(HasTraits):
    policy = Instance(DefaultPolicy)
    pool = Instance(Pool)
    installed_repository = Instance(Repository)

    def __init__(self, pool, installed_repository, **kw):
        policy = DefaultPolicy()
        super(Solver, self).__init__(self, policy=policy, pool=pool,
                installed_repository=installed_repository, **kw)

    def solve(self, request):
        decision, rules = self._prepare_solver(request)
        self._make_assertion_rules_decisions(decisions, rules)

        return decisions

    def _setup_install_map(self, jobs):
        installed_map = OrderedDict()
        for package in self.installed_repository.iter_packages():
            installed_map[package.id] = package

        for job in jobs:
            if job.job_type == "update":
                raise NotImplementedError()
            elif job.job_type == "upgrade":
                raise NotImplementedError()
            elif job.job_type == "install":
                if len(job.packages) < 1:
                    raise NotImplementedError()

        return installed_map

    def _prepare_solver(self, request):
        installed_map = self._setup_install_map(request.jobs)

        decisions = DecisionsSet(self.pool)

        rules_generator = RulesGenerator(self.pool, request, installed_map)
        rules = list(rules_generator.iter_rules())

        return decisions, rules

    def _make_assertion_rules_decisions(self, decisions, rules):
        decision_start = len(decisions) - 1

        rule_index = 0
        while rule_index < len(rules):
            rule = rules[rule_index]
            rule_index += 1

            if not rule.is_assertion or not rule.enabled:
                continue

            literals = rule.literals
            literal = literals[0]

            if not decisions.is_decided(abs(literal)):
                decisions.decide(literal, 1, rule)
                continue;

            if decisions.satisfy(literal):
                continue

            if rule.rule_type == "learnt":
                rule.enable = False
                continue

            raise NotImplementedError()
