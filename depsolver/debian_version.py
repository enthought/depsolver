import re

from depsolver.errors \
    import \
        InvalidVersion
from depsolver.version \
    import \
        Version

_EPOCH_RE = re.compile("\d")

_UPSTREAM_VERSION_RE = re.compile("\d[a-zA-Z0-9.+-:~]*")

_DEBIAN_REVISION_RE = re.compile("[a-zA-Z0-9+.~]+")

def parse_version_string(version):
    epoch = "0"
    revision = "0"

    if ":" in version:
        epoch, version = version.split(":", 1)
    if "~" in version:
        version, revision = version.split("~", 1)

    if not _EPOCH_RE.match(epoch):
        raise InvalidVersion("Invalid epoch for debian version: '%s'" % epoch)
    if not _UPSTREAM_VERSION_RE.match(version):
        raise InvalidVersion("Invalid upstream version for debian version: '%s'" % version)
    if not _DEBIAN_REVISION_RE.match(revision):
        raise InvalidVersion("Invalid debian revision for debian version: '%s'" % revision)

    return epoch, version, revision

def is_valid_debian_version(version):
    try:
        parse_version_string(version)
        return True
    except InvalidVersion:
        return False

class DebianVersion(Version):
    @classmethod
    def from_string(cls, version):
        epoch, upstream, revision = parse_version_string(version)
        return cls(upstream, revision, epoch)

    def __init__(self, upstream, revision=None, epoch=None):
        self.upstream = upstream
        self.revision = revision
        self.epoch = epoch

        comparable_parts = []
        if epoch is None:
            comparable_parts.append(0)
        else:
            comparable_parts.append(int(epoch))
        comparable_parts.append(upstream)
        if revision is None:
            comparable_parts.append("0")
        else:
            comparable_parts.append(revision)
        self._comparable_parts = comparable_parts

    def __str__(self):
        s = self.upstream
        if self.epoch:
            s = self.epoch + ":" + s
        if self.revision:
            s += "~" + self.revision
        return s

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if other is None:
            return False
        if isinstance(other, DebianVersion):
            return self._comparable_parts == other._comparable_parts
        else:
            return NotImplemented
