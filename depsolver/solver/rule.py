import hashlib
import re

import six

from depsolver.bundled.traitlets \
    import \
        HasTraits, Bool, Enum, Instance, List, Long, Unicode
from depsolver.errors \
    import \
        MissingPackageInfoInPool
from depsolver.package \
    import \
        PackageInfo
from depsolver.pool \
    import \
        Pool
from depsolver.request \
    import \
        _Job
from depsolver.version \
    import \
        Version

_IS_VALID_LITERAL = re.compile("[a-zA-Z_0-9][-+.\w\d]*")

class Literal(object):
    """Creates a simple Literal to be used within clauses.

    Parameters
    ----------
    name: str
        Name of the literal (must consists of alphanumerical characters only)
    """
    def __init__(self, name):
        if not _IS_VALID_LITERAL.match(name):
            raise ValueError("Invalid literal name: %s" % name)
        self._name = name

    @property
    def name(self):
        return self._name

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.name == other._name

    def __hash__(self):
        return hash(repr(self))

    def __repr__(self):
        return "L('%s')" % self.name

    def __or__(self, other):
        return Rule([self, other])

    def __invert__(self):
        return Not(self.name)

    def evaluate(self, values):
        if not self.name in values:
            raise ValueError("literal %s is undefined" % self.name)
        else:
            return values[self.name]

class Not(Literal):
    def __repr__(self):
        return "L('~%s')" % self.name

    def evaluate(self, values):
        return not super(Not, self).evaluate(values)

class Rule(object):
    @classmethod
    def from_string(cls, clause_string):
        literals = []
        for literal_string in clause_string.split("|"):
            literal_string = literal_string.strip()
            if literal_string.startswith("~"):
                if len(literal_string) < 2:
                    raise ValueError("Invalid literal string: %r" % literal_string)
                else:
                    literals.append(Not(literal_string[1:]))
            else:
                literals.append(Literal(literal_string))
        return cls(literals)

    def __init__(self, literals):
        def key(literal):
            # FIXME: hack to sort not literal before the others
            if isinstance(literal, Not):
                return "\0%s" % literal.name
            else:
                return literal.name
        self.literals = tuple(sorted(set(literals), key=key))
        self.literal_names = tuple(l.name for l in self.literals)

        self._name_to_literal = dict((literal.name, literal) for literal in literals)

    @property
    def is_assertion(self):
        return len(self.literals) == 1

    def get_literal(self):
        if self.is_assertion:
            return six.advance_iterator(iter(self.literals))
        else:
            raise ValueError("Cannot get literal from non-assertion clause !")

    def evaluate(self, values):
        ret = False
        for literal in self.literals:
            if not literal.name in values:
                raise ValueError("literal %s value is undefined" % (literal.name,))
            else:
                ret |= literal.evaluate(values)
        return ret

    def satisfies_or_none(self, values):
        """Return True if the clause is satisfied, False if not, None if it
        cannot be evaluated."""
        unset_literals = []
        for literal in self.literals:
            if literal.name in values:
                if literal.evaluate(values):
                    return True
            else:
                unset_literals.append(literal)
        if len(unset_literals) > 0:
            return None
        else:
            return False

    def __or__(self, other):
        if isinstance(other, Rule):
            literals = set(self.literals)
            literals.update(other.literals)
            return Rule(literals)
        elif isinstance(other, Literal):
            literals = set([other])
            literals.update(self.literals)
            return Rule(literals)
        else:
            raise TypeError("unsupported type %s" % type(other))

    def __repr__(self):
        def _simple_literal(l):
            return "~%s" % l.name if isinstance(l, Not) else l.name
        return "C({})".format(" | ".join(_simple_literal(l) for l in self.literals))

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.literals == other.literals

    def __hash__(self):
        return hash(self.literals)

    def is_unit(self, variables):
        """Computes whether this clause is decidable with the given variables,
        and if so, return the variable that can be decided.

        A clause is a unit if all literals but one are False for the given
        variables. If this is the case, the last literal has to be True for the
        clause to be True, and hence

        Parameters
        ----------
        variables: dict
            variable name -> bool mapping

        Returns
        -------
        is_unit: bool
            True if the rule is a unit, False otherwise
        inferred: Literal or None
            If not None, a literal instance representing the literal that can
            be inferred. If is_unit is True and inferred is None, it means the
            clause cannot be True with the given variables.

        Example
        -------
        >>> a = Rule.from_string("A | ~B | ~C")
        >>> a.is_unit({"B": True, "C": True})
        (True, L('A'))
        """
        false_literals = []
        can_be_infered = None
        for literal in self.literals:
            if literal.name in variables and not literal.evaluate(variables):
                false_literals.append(literal)
            elif not literal.name in variables:
                can_be_infered = literal

        if len(false_literals) == len(self.literals):
            return True, None
        elif len(false_literals) == len(self.literals) - 1:
            return True, can_be_infered
        else:
            return False, None

class PackageInfoLiteral(Literal):
    """A Literal whose name is a package id attached to a pool."""
    @classmethod
    def from_string(cls, literal_string, pool):
        if literal_string.startswith("-"):
            is_not = True
            _, name, version = literal_string.split("-", 2)
        else:
            is_not = False
            name, version = literal_string.split("-")
        package = PackageInfo(name, Version.from_string(version))
        if not pool.has_package(package):
            raise MissingPackageInfoInPool(package)
        if is_not:
            return PackageInfoNot(package.id, pool)
        else:
            return PackageInfoLiteral(package.id, pool)

    @classmethod
    def from_package(cls, package, pool):
        return cls(package.id, pool)

    def __init__(self, name, pool):
        super(PackageInfoLiteral, self).__init__(name)
        self._pool = pool

    def __repr__(self):
        return str(self._pool.package_by_id(self.name))

    def __or__(self, other):
        if not self._pool == other._pool:
            raise ValueError("Cannot or pakage literals which don't share the same pool.")
        else:
            return PackageInfoRule([self, other], self._pool)

class PackageInfoNot(PackageInfoLiteral, Not):
    def __repr__(self):
        package = self._pool.package_by_id(self.name)
        return "-%s" % package


_RULE_REASONS = [
    "internal_allow_update",
    "job_install",
    "job_remove",
    "package_conflict",
    "package_requires",
    "package_obsoletes",
    "rule_installed_package_obsoletes",
    "rule_package_same_name",
    "rule_package_implicit_obsoletes",
    "rule_learned",
    "rule_package_alias",
]

class PackageRule(HasTraits):
    """A Rule where literals are package ids attached to a pool.

    It essentially allows for pretty-printing package names instead of internal
    ids as used by the SAT solver underneath.
    """
    pool = Instance(Pool)
    literals = List(Long)

    reason = Enum(_RULE_REASONS)
    reason_details = Unicode("")

    job = Instance(_Job)

    enabled = Bool(True)

    _rule_hash = Unicode("")

    @classmethod
    def from_packages(cls, pool, packages, reason, reason_details="", job=None):
        literals = [p.id for p in packages]
        return cls(pool, literals, reason, reason_details, job)

    def __init__(self, pool, literals, reason, reason_details="", job=None, **kw):
        literals = sorted(literals)
        super(PackageRule, self).__init__(pool=pool, literals=literals,
                reason=reason, reason_details=reason_details, job=job, **kw)

    @property
    def rule_hash(self):
        # The exact rule hash algorithm is copied from composer
        return hashlib.md5(",".join(str(i) for i in self.literals)).hexdigest()[:5]

    def is_equivalent(self, other):
        """Two rules are considered equivalent if they have the same
        literals."""
        if not isinstance(other, PackageRule):
            return NotImplemented
        return self.literals == other.literals

    def __or__(self, other):
        if isinstance(other, PackageInfoRule):
            literals = set(self.literals)
            literals.update(other.literals)
            return PackageInfoRule(literals, self._pool)
        elif isinstance(other, Literal):
            literals = set([other])
            literals.update(self.literals)
            return PackageInfoRule(literals, self._pool)
        else:
            raise TypeError("unsupported type %s" % type(other))

    def __repr__(self):
        return "(%s)" % " | ".join(self.pool.id_to_string(l) for l in self.literals)
