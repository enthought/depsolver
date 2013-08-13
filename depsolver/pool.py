import collections

from depsolver.bundled.traitlets \
    import \
        HasTraits, Dict, Instance, List, Long, Unicode
from depsolver.errors \
    import \
        MissingPackageInfoInPool
from depsolver.package \
    import \
        PackageInfo
from depsolver.repository \
    import \
        Repository
from depsolver.requirement \
    import \
        Requirement

MATCH_NAME = 1
MATCH = 2
MATCH_PROVIDE = 3

class Pool(HasTraits):
    """Pool objects model a pool of repositories.

    Pools are able to find packages that provide a given requirements (handling
    the provides concept from package metadata).
    """
    repositories = List(Instance(Repository))

    _packages_by_id = Dict()
    _packages_by_name = Dict()

    _id = Long(1)

    def __init__(self, repositories=None, **kw):
        super(Pool, self).__init__(self, **kw)
        if repositories is None:
            repositories = []

        # provide.name -> package mapping
        self._packages_by_name = collections.defaultdict(list)

        if len(repositories) > 0:
            for repository in repositories:
                self.add_repository(repository)

    def has_package(self, package):
        package_id = package.id
        return package_id in self._packages_by_id

    def add_repository(self, repository):
        """Add a repository to this pool.

        Arguments
        ---------
        repository: Repository
            repository to add
        """
        self.repositories.append(repository)

        for package in repository.iter_packages():
            package.id = self._id
            self._id += 1
            self._packages_by_id[package.id] = package

            self._packages_by_name[package.name].append(package)
            for provide in package.provides:
                self._packages_by_name[provide.name].append(package)

    def package_by_id(self, package_id):
        """Retrieve a package from its id.

        Arguments
        ---------
        package_id: str
            A package id
        """
        try:
            return self._packages_by_id[package_id]
        except KeyError:
            raise MissingPackageInfoInPool(package_id)

    def what_provides(self, requirement, mode='composer'):
        """Returns a list of packages that provide the given requirement.

        Arguments
        ---------
        requirement: Requirement
            the requirement to match
        mode: str
            One of the following string:

                - 'composer': behaves like Composer does, i.e. only returns
                  packages that match this requirement directly, unless no
                  match is found in which case packages that provide the
                  requirement indirectly are returned.
                - 'direct_only': only returns packages that match this
                  requirement directly (i.e. provides are ignored).
                - 'include_indirect': only returns packages that match this
                  requirement directly or indirectly (i.e. includes packages
                  that provides this package)
                - 'any': returns any version of the package regardless of the
                  version, includes packages matching directly and indirectly.
        """
        # FIXME: this is conceptually copied from whatProvides in Composer, but
        # I don't understand why the policy of preferring non-provided over
        # provided packages is handled here.
        if not mode in ['composer', 'direct_only', 'include_indirect', 'any']:
            raise ValueError("Invalid mode %r" % mode)

        any_matches = []
        strict_matches = []
        provided_match = []

        for package in self._packages_by_name[requirement.name]:
            match = self.matches(package, requirement)
            if match == MATCH_NAME:
                any_matches.append(package)
            elif match == MATCH:
                strict_matches.append(package)
            elif match == MATCH_PROVIDE:
                provided_match.append(package)
            else:
                raise ValueError("Invalid match type: {}".format(match))

        if mode == 'composer':
            if len(any_matches) > 0 or len(strict_matches) > 0:
                return strict_matches
            else:
                return provided_match
        elif mode == 'direct_only':
            return strict_matches
        elif mode == 'include_indirect':
            return strict_matches + provided_match
        elif mode == 'any':
            return strict_matches + provided_match + any_matches

    def matches(self, candidate, requirement):
        """Checks whether the candidate package matches the requirement, either
        directly or through provides.

        Arguments
        ---------
        candidate: PackageInfo
            Candidate package
        requirement: Requirement
            The requirement to match

        Returns
        -------
        match_type: _Match or False
            An instance of Match, that specified the type of match:

                - if only the name matches, will be MATCH_NAME
                - if the name and version actually match, will be MATCH
                - if the match is through the package's provides, will be MATCH_PROVIDE
                - if no match at all, will be False

        Examples
        --------
        >>> from depsolver import PackageInfo, Requirement
        >>> R = Requirement.from_string
        >>> pool = Pool()
        >>> pool.matches(PackageInfo.from_string('numpy-1.3.0'), R('numpy >= 1.2.0')) == MATCH
        True
        """
        if requirement.name == candidate.name:
            candidate_requirement_string = "%s == %s" % (candidate.name, candidate.version)
            candidate_requirement = Requirement.from_string(candidate_requirement_string)
            if requirement.matches(candidate_requirement):
                return MATCH
            else:
                return MATCH_NAME

        for provide in candidate.provides:
            if requirement.matches(provide):
                return MATCH_PROVIDE

        return False

    def id_to_string(self, package_id):
        """
        Convert a package id to a nice string representation.
        """
        package = self.package_by_id(abs(package_id))
        if package_id > 0:
            return "+" + str(package)
        else:
            return "-" + str(package)
