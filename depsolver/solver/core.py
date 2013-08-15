from depsolver.errors \
    import \
        DepSolverError
from depsolver.operations \
    import \
        Install, Remove, Update
from depsolver.solver.decisions \
    import \
        DecisionsSet
from depsolver.solver.policy \
    import \
        DefaultPolicy

def run_unit_propagation(clauses, variables):
    """Run unit propagation, i.e. for each unit clause, infer the corresponding
    literal and remove the clause from the clauses set.
    """
    iterate_over = clauses[:]
    for clause in iterate_over:
        is_unit, can_be_infered = variables.is_unit(clause)
        if is_unit:
            variables.infer(can_be_infered, clause)
            clauses = prune_satisfied_clauses(clauses, variables)
            if clauses is None:
                raise DepSolverError("Bug in unit propagation ?")

    return clauses

def prune_satisfied_clauses(clauses, variables):
    """Remove any clause that is already satisfied (i.e. is True) from the
    given clause set.

    Parameters
    ----------
    clauses: seq
        Sequence of clauses
    variables: dict
        variable name -> bool mapping

    Returns
    -------
    clauses: seq or None
        Sequence of clauses that are not yet satisfied. If None, it means at
        least one clause could not be satisfied
    """
    new_clauses = []

    for clause in clauses:
        evaluated_or_none = variables.satisfies_or_none(clause)
        if evaluated_or_none is None:
            new_clauses.append(clause)
        elif evaluated_or_none is False:
            return None

    return new_clauses

def prune_pure_literals(clauses, variables):
    new_clauses = []
    for clause in clauses:
        if len(clause.literals) == 1:
            literal = clause.literals[0]
            assert not literal.name in variables
            variables.infer(literal, clause)
        else:
            new_clauses.append(clause)

    return new_clauses

def _run_dpll_iteration(clauses, variables):
    # Return (should_continue, clauses) where:
    #   - should_continue is a bool on whether to continue or not
    #   - clauses is a set of clauses
    new_clauses = prune_satisfied_clauses(clauses, variables)
    if new_clauses is None:
        return False, clauses
    else:
        new_clauses = run_unit_propagation(new_clauses, variables)
        new_clauses = prune_pure_literals(new_clauses, variables)
        return True, new_clauses

def decide_from_assertion_rules(clauses, variables):
    for clause in clauses:
        if clause.is_assertion:
            variables.infer(clause.get_literal(), clause)

class Solver(object):
    def __init__(self, pool, installed_repository, policy=None):
        self.pool = pool
        self.installed_repository = installed_repository

        if policy is None:
            policy = DefaultPolicy()
        self.policy = policy

        self._id_to_installed_package = {}
        self._id_to_updated_state = {}

    def _compute_package_maps(self, request):
        """Compute installed and updated package mapping."""
        for package in self.installed_repository.iter_packages():
            self._id_to_installed_package[package.id] = package

        for job in request.jobs:
            if job.job_type == "update":
                for package in job.packages:
                    if package.id in self._id_to_installed_package:
                        self._id_to_updated_state[package.id] = True
            elif job.job_type == "upgrade":
                for package in self.installed_repository.iter_packages():
                    self._id_to_updated_state[package.id] = True
            elif job.job_type == "install":
                if len(job.packages) == 0:
                    raise NotImplementedError("Install wo job not supported yet")

    def _run_dpll(self, clauses, variables):
        while True:
            if len(clauses) == 0:
                break
            clause = clauses[0]
            satisfied_or_none = variables.satisfies_or_none(clause)
            if satisfied_or_none is True:
                clauses = clauses[1:]
                if len(clauses) < 1:
                    break
                else:
                    continue
            if satisfied_or_none is False:
                raise DepSolverError("Impossible situation ! And yet, it happned... (SAT bug ?)")

            # TODO: add function to find out set of undecided literals of a clause
            decision_queue = list(literal.name for literal in clause.literals if not
                    literal.name in variables)
            clauses = self._select_and_install(clause, clauses, decision_queue, variables)

    def _solve_job_clauses(self, clauses, job_clauses, variables):
        for job_clause in job_clauses:
            is_satisfied_or_none = variables.satisfies_or_none(job_clause)

            if is_satisfied_or_none is True:
                continue
            if is_satisfied_or_none is False:
                continue

            decision_queue = set(literal \
                    for literal in job_clause.literals \
                    if not literal.name in variables)

            if len(self._id_to_updated_package) > 0:
                raise NotImplementedError("update not yet implemented")
            if len(self._id_to_installed_package) > 0:
                old_decision_queue = decision_queue
                decision_queue = []
                for literal in job_clause.literals:
                    if literal.name in self._id_to_updated_package:
                        decision_queue = old_decision_queue
                        break
                    if literal.name in self._id_to_installed_package:
                        decision_queue.append(literal)
            if len(decision_queue) < 1:
                continue

            clauses = self._select_and_install(job_clause, clauses,
                    [l.name for l in decision_queue],
                    variables)

        return clauses

    def _select_and_install(self, clause, clauses, decision_queue, variables):
        candidates = self.policy.prefered_package_ids(self.pool,
                self._id_to_installed_package,
                decision_queue)
        while len(candidates) > 0:
            candidate = candidates.popleft()
            # FIXME: consolidate string vs object for literals
            l_candidate = PackageInfoLiteral(candidate, self.pool)
            assert not candidate in variables
            variables.infer(l_candidate, clause)
            status, new_clauses = _run_dpll_iteration(clauses, variables)
            if status is False:
                variables.pop()
                variables.infer(~l_candidate, clause)
                status, new_clauses = _run_dpll_iteration(clauses, variables)
                if status is False:
                    # FIXME: refactor solver parts that needs backtracking (and
                    # actuall implement backtracking !)
                    raise NotImplementedError("Backtracking not implemented yet")
            else:
                clauses = new_clauses
                break

        return clauses

    def solve(self, requirement):
        """Compute the set of operations to fulfill the given requirement.

        Parameters
        ----------
        requirement: Requirement
            The requirement to fulfill

        Returns
        --------
        operations: seq
            List of operations to apply to the system to fulfill the requirement.
        """
        clauses = create_install_rules(self.pool, requirement)
        job_clauses = clauses[:1]

        variables = DecisionsSet(self.pool)
        decide_from_assertion_rules(clauses, variables)

        clauses = self._solve_job_clauses(clauses, job_clauses, variables)

        if len(clauses) > 0:
            self._run_dpll(clauses, variables)

        return self._compute_operations(variables)

    def _compute_operations(self, variables):
        """Build the sequence of operations corresponding to the given
        variables."""
        operations = []

        update_package_ids = set()
        for literal_name, literal_value in variables.items():
            if literal_value is True and not literal_name in self._id_to_installed_package:
                package = self.pool.package_by_id(literal_name)
                if self.installed_repository.has_package_name(package.name):
                    to_update_packages = self.installed_repository.find_packages(package.name)
                    assert len(to_update_packages) == 1
                    to_update_package = to_update_packages[0]
                    update_package_ids.add(to_update_package.id)
                    operations.append(Update(to_update_package,
                                             self.pool.package_by_id(literal_name)))
                else:
                    operations.append(Install(self.pool.package_by_id(literal_name)))

        for literal_name, literal_value in variables.items():
            if literal_value is False and literal_name in self._id_to_installed_package and \
                    not literal_name in update_package_ids:
                operations.append(Remove(self.pool.package_by_id(literal_name)))

        operations.reverse()
        return operations
