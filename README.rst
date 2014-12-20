.. image:: https://secure.travis-ci.org/enthought/depsolver.png?branch=master
    :target: https://travis-ci.org/enthought/depsolver

.. note:: the work on depsolver is temporarily handed over to the
  enstaller project (in enstaller.new_solver), to ease the integration
  with our needs at Enthought. Once the integration is over, we will
  extract back the solver into depsolver.

depsolver is a package dependency solver in python.

Examples::

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

A more complex scenario which currently fails with pip
(https://github.com/pypa/pip/issues/174)::

    #  - A requires B and C
    #  - B requires D <= 1.1
    #  - C requires D <= 0.9

    a_1_0_0 = PackageInfo.from_string("A-1.0.0; depends (B, C)")
    b_1_0_0 = PackageInfo.from_string("B-1.0.0; depends (D <= 1.1.0)")
    c_1_0_0 = PackageInfo.from_string("C-1.0.0; depends (D <= 0.9.0)")
    d_1_1_0 = PackageInfo.from_string("D-1.1.0")
    d_0_9_0 = PackageInfo.from_string("D-0.9.0")

    repo = Repository([a_1_0_0, b_1_0_0, c_1_0_0, d_1_1_0, d_0_9_0])
    installed_repo = Repository()
    pool = Pool([repo, installed_repo])

    # despolver resolves each dependency 'globally', and does not install
    # D-1.1.0 as pip currently does
    request = Request(pool)
    request.install(Requirement.from_string("A"))
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
