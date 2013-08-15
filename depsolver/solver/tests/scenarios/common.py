import json

from depsolver.constraints \
    import \
        Any, GEQ, LT
from depsolver.requirement_parser \
    import \
        RawRequirementParser

def requirement_to_php_string(req):
    s = str(req)
    parts = (part.split() for part in s.split(","))

    ret = []
    for part in parts:
        ret.append(" ".join(part[1:]))
    return ", ".join(ret)

def packages_list_to_php_json(packages):
    res = []
    for package in packages:
        version_normalized = str(package.version) + ".0"
        res.append({
                "name": package.name,
                "version": str(package.version),
                "version_normalized": version_normalized,
                "provide": dict((dep.name, requirement_to_php_string(dep))
                                  for dep in package.provides),
                "require": dict((dep.name, requirement_to_php_string(dep))
                                 for dep in package.dependencies),
                "conflict": dict((dep.name, requirement_to_php_string(dep))
                                  for dep in package.conflicts),
                "replace": dict((dep.name, requirement_to_php_string(dep))
                                 for dep in package.replaces),
        })
    return json.dumps(res, indent=4)

def requirement_string_to_php_constraints(req):
    ret = []

    parser = RawRequirementParser()
    reqs = parser.parse(req).items()
    if not len(reqs) == 1:
        raise ValueError()

    for name, constraints in reqs:
        for constraint in constraints:
            if isinstance(constraint, GEQ):
                ret.append((">=", constraint.version))
            elif isinstance(constraint, LT):
                ret.append(("<", constraint.version))
            elif isinstance(constraint, Any):
                pass
            else:
                raise ValueError("Unsupported constraint: %s" % constraint)

    return ret

COMMON_IMPORTS = """\
use Composer\DependencyResolver\Decisions;
use Composer\DependencyResolver\DefaultPolicy;
use Composer\DependencyResolver\Pool;
use Composer\DependencyResolver\Request;
use Composer\DependencyResolver\RuleWatchGraph;
use Composer\DependencyResolver\Solver;
use Composer\Json\JsonFile;
use Composer\Package\CompletePackage;
use Composer\Package\Link;
use Composer\Package\LinkConstraint\MultiConstraint;
use Composer\Package\LinkConstraint\VersionConstraint;
use Composer\Package\Loader\ArrayLoader;
use Composer\Repository\ArrayRepository;
use Composer\Repository\FilesystemRepository;
use Composer\Repository\InstalledFilesystemRepository;
use Composer\Repository\WritableArrayRepository;

"""

COMPOSER_PATH = "/Users/cournape/src/dev/composer/composer-git"
