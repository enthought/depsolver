import hashlib
import re

from depsolver._package_utils \
    import \
        parse_package_full_name
from depsolver.requirement \
    import \
        Requirement
from depsolver.version \
    import \
        Version
from depsolver.bundled.traitlets \
    import \
        HasTraits, Instance, List, Long, Unicode
from depsolver.errors \
    import \
        DepSolverError

R = Requirement.from_string
V = Version.from_string

_SECTION_RE = re.compile("(depends|provides|replaces|conflicts|suggests)\s*\((.*)\)")

def _parse_name_version_part(name_version, loose):
    name, version_string = parse_package_full_name(name_version)
    if loose:
        version = Version.from_loose_string(version_string)
    else:
        version = V(version_string)

    return name, version

def _parse_requirements_string(s):
    m = _SECTION_RE.search(s)
    if m is None:
        raise ValueError("invalid requirement string: %r" % s)
    else:
        requirements_string = m.groups()[1]
        requirements = set()
        for requirement_string in requirements_string.split(","):
            requirements.add(R(requirement_string))
        return requirements

def parse_package_string(package_string, loose=False):
    parts = package_string.split(";")

    if len(parts) < 1:
        raise ValueError("YO")

    name, version = _parse_name_version_part(parts[0], loose)

    dependencies = set()
    provides = set()
    conflicts = set()
    replaces = set()
    suggests = set()

    if len(parts) > 1:
        for part in parts[1:]:
            part = part.strip()
            if part.startswith("depends"):
                dependencies = _parse_requirements_string(part)
            elif part.startswith("provides"):
                provides = _parse_requirements_string(part)
            elif part.startswith("conflicts"):
                conflicts = _parse_requirements_string(part)
            elif part.startswith("replaces"):
                replaces = _parse_requirements_string(part)
            elif part.startswith("suggests"):
                suggests = _parse_requirements_string(part)
            else:
                raise ValueError("syntax error: %r" % part)

    return name, version, provides, dependencies, conflicts, replaces, suggests

class PackageInfo(HasTraits):
    """
    PackageInfoInfo instances contain exactly all the metadata needed for the
    dependency management.

    Parameters
    ----------
    name: str
        Name of the package (i.e. distribution name)
    version: object
        Instance of Version
    provides: None or sequence
        Sequence of Requirements.
    dependencies: None or sequence
        Sequence of Requirements.
    """
    name = Unicode()
    version = Instance(Version)

    dependencies = List(Instance(Requirement))
    provides = List(Instance(Requirement))
    conflicts = List(Instance(Requirement))
    replaces = List(Instance(Requirement))
    suggests = List(Instance(Requirement))

    id = Long(-1)

    _repository = Instance("depsolver.repository.Repository")

    @classmethod
    def from_string(cls, package_string):
        """Create a new package from a string.

        Example
        -------
        >>> P = PackageInfo.from_string
        >>> P("numpy-1.3.0; depends (mkl <= 10.4.0, mkl >= 10.3.0)")
        PackageInfo(u'numpy-1.3.0; depends (mkl >= 10.3.0, mkl <= 10.4.0)')
        >>> numpy_1_3_0 = PackageInfo("numpy", Version.from_string("1.3.0"))
        >>> P("numpy-1.3.0") == numpy_1_3_0
        True
        """
        name, version, provides, dependencies, conflicts, replaces, suggests \
                = parse_package_string(package_string)
        return cls(name=name, version=version, provides=list(provides),
                   dependencies=list(dependencies), conflicts=list(conflicts),
                   replaces=list(replaces), suggests=list(suggests))

    def __init__(self, name, version, dependencies=None, provides=None, conflicts=None,
                 replaces=None, suggests=None, **kw):
        if dependencies is None:
            dependencies = []
        if provides is None:
            provides = []
        if conflicts is None:
            conflicts = []
        if replaces is None:
            replaces = []
        if suggests is None:
            suggests = []
        super(PackageInfo, self).__init__(name=name, version=version,
                                          dependencies=dependencies,
                                          provides=provides,
                                          conflicts=conflicts,
                                          replaces=replaces,
                                          suggests=suggests,
                                          **kw)
    @property
    def unique_name(self):
        return self.name + "-" + str(self.version)

    @property
    def package_string(self):
        strings = ["%s-%s" % (self.name, self.version)]
        if self.dependencies:
            strings.append("depends (%s)" % ", ".join(str(s) for s in self.dependencies))
        if self.provides:
            strings.append("provides (%s)" % ", ".join(str(s) for s in self.provides))
        if self.conflicts:
            strings.append("conflicts (%s)" % ", ".join(str(s) for s in self.conflicts))
        if self.replaces:
            strings.append("replaces (%s)" % ", ".join(str(s) for s in self.replaces))
        if self.suggests:
            strings.append("suggests (%s)" % ", ".join(str(s) for s in self.suggests))
        return "; ".join(strings)

    @property
    def repository(self):
        return self._repository

    @repository.setter
    def repository(self, repository):
        if self._repository is not None:
            raise ValueError("Repository for this package is already set to %s!" % \
                             format(self._repository))
        self._repository = repository

    def __repr__(self):
        return "PackageInfo(%r)" % self.package_string

    def __str__(self):
        return self.unique_name

    def __eq__(self, other):
        return self.name == other.name and self.version == other.version \
                and self.provides == other.provides \
                and self.dependencies == other.dependencies \
                and self.id == other.id

    def __hash__(self):
        return hash("%s%d" % (str(self), self.id))
