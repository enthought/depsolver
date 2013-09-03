.. image:: https://secure.travis-ci.org/enthought/depsolver.png
    :alt: Travis CI Build Status

depsolver is a package dependency solver in python.

Example::

    # Simple scenario: nothing installed, install numpy, 2 versions available
    # in the repository
    from depsolver import PackageInfo, Pool, Repository, Request, Requirement, Solver

    numpy_1_6_1 = PackageInfo.from_string("numpy-1.6.1")
    numpy_1_7_0 = PackageInfo.from_string("numpy-1.7.0")

    repo = Repository([numpy_1_6_1, numpy_1_7_0])
    installed_repo = Repository()
    pool = Pool([repo, installed_repo])

    # only one operation here: install numpy (most recent available version
    # automatically picked up)
    request = Request(pool)
    request.install(Requirement.from_string("numpy"))
    for operation in Solver(pool, installed_repo).solve(request):
        print operation

Its main features:

        - pure python. Both >= 2.5 and >= 3.2 are supported from a single
          codebase.
        - only depends on the six library
        - use SAT solver to solve dependencies
        - handle dependencies, provides, conflict and replaces
        - supports multiple version formats (semver
          `semantic versions RFC <http://www.semver.org>`_ and debian formats
          currently supported)
        - reasonably well tested (> 90 % coverage)

It is still experimental, and subject to arbitrary changes.

The design is strongly inspired from `PHP Composer packager
<http://getcomposer.org>`_, itself started as a port of libsolver.

Thanks to Enthought to let me open source this project !
