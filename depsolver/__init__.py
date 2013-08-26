try:
    from depsolver._version \
        import \
            __version__
except ImportError as e:
    __version__ = "no-built"

from depsolver.package \
    import\
        PackageInfo
from depsolver.pool \
    import\
        Pool
from depsolver.repository \
    import\
        Repository
from depsolver.request \
    import\
        Request
from depsolver.requirement \
    import\
        Requirement
from depsolver.solver.core \
    import\
        Solver
