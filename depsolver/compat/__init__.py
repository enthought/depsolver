import sys

if sys.version_info[:1] < (2, 7):
    from depsolver.compat._collections import OrderedDict
else:
    from collections import OrderedDict
