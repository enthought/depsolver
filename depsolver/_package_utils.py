import re

from depsolver.errors \
    import \
        DepSolverError

_FULL_PACKAGE_RE = re.compile("""\
                              (?P<name>[^-.]+)
                              -
                              (?P<version>(.*))
                              $""", re.VERBOSE)

def parse_package_full_name(full_name):
    """
    Parse a package full name (e.g. 'numpy-1.6.0') into a (name,
    version_string) pair.
    """
    m = _FULL_PACKAGE_RE.match(full_name)
    if m:
        return m.group("name"), m.group("version")
    else:
        raise DepSolverError("Invalid package full name %s" % (full_name,))

