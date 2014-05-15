import sys

if sys.version_info < (2, 7):
    from ._collections import OrderedDict

    def sorted_with_cmp(x, cmp):
        return sorted(x, cmp=cmp)

    import unittest2 as unittest
else:
    from collections import OrderedDict

    from functools import cmp_to_key
    def sorted_with_cmp(x, cmp):
        return sorted(x, key=cmp_to_key(cmp))
    import unittest

from ._itertools import izip_longest

__all__ = ["OrderedDict", "sorted_with_cmp", "unittest", "izip_longest"]
