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

    installed_map = Instance(OrderedDict)
    update_map = Instance(OrderedDict)

    def __init__(self, pool, installed_repository, **kw):
        policy = DefaultPolicy()
        installed_map = OrderedDict()
        update_map = OrderedDict()
        super(Solver, self).__init__(self, policy=policy, pool=pool,
                installed_repository=installed_repository,
                installed_map=installed_map,
                update_map=update_map, **kw)

    def solve(self, request):
        decisions, rules_set = self._prepare_solver(request)
        self._make_assertion_rules_decisions(decisions, rules_set)

        return decisions

    def _setup_install_map(self, jobs):
        for package in self.installed_repository.iter_packages():
            self.installed_map[package.id] = package

        for job in jobs:
            if job.job_type == "update":
                for package in job.packages:
                    if package.id in self.installed_map:
                        self.update_map[package.id] = True
            elif job.job_type == "upgrade":
                for package in self.installed_map:
                    self.update_map[package.id] = True
            elif job.job_type == "install":
                if len(job.packages) < 1:
                    raise NotImplementedError()

    def _prepare_solver(self, request):
        self._setup_install_map(request.jobs)

        decisions = DecisionsSet(self.pool)

        rules_generator = RulesGenerator(self.pool, request, self.installed_map)
        return decisions, rules_generator.iter_rules()

    def _make_assertion_rules_decisions(self, decisions, rules_generator):
        decision_start = len(decisions) - 1

        for rule in rules_generator:
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
