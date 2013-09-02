import sys

if sys.version_info[:1] < (2, 7):
    from depsolver.compat._collections import OrderedDict

    def sorted_with_cmp(x, cmp):
        return sorted(x, cmp=cmp)
else:
    from collections import OrderedDict

    from functools import cmp_to_key
    def sorted_with_cmp(x, cmp):
        return sorted(x, key=cmp_to_key(cmp))

if sys.version_info[:1] < (2, 6):
    from depsolver.compat._itertools import izip_longest
else:
    from itertools import izip_longest
