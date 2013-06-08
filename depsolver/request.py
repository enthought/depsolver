class _Job(object):
    def __init__(self, packages, job_type, requirement):
        self.packages = packages
        self.job_type = job_type
        self.requirement = requirement

    def __eq__(self, other):
        if len(self.packages) != len(other.packages):
            return False
        else:
            for left, right in zip(self.packages, other.packages):
                if left != right:
                    return False
            return self.job_type == other.job_type \
                    and self.requirement == other.requirement

class Request(object):
    """A Request instance encompasses the set of jobs to be solved by the
    dependency solver.
    """
    def __init__(self, pool):
        self._pool = pool
        self.jobs = []

    def _add_job(self, requirement, job_type):
        packages = self._pool.what_provides(requirement)

        self.jobs.append(_Job(packages, job_type, requirement))

    def install(self, requirement):
        self._add_job(requirement, "install")

    def update(self, requirement):
        self._add_job(requirement, "update")

    def remove(self, requirement):
        self._add_job(requirement, "remove")

    def upgrade(self):
        self.jobs.append(_Job([], "upgrade", None))
