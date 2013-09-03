import os.path as op

from distutils.core import setup

VERSION = "0.0.2.dev1"

with open("README.rst", "rt") as fp:
    DESCRIPTION = fp.read()

with open(op.join("depsolver", "_version.py"), "wt") as fp:
    fp.write("__version__ = \"%s\"" % VERSION)

def run_setup():
    setup(name="depsolver", version=VERSION,
          packages=["depsolver",
              "depsolver.bundled",
              "depsolver.bundled.traitlets",
              "depsolver.compat",
              "depsolver.solver",
              "depsolver.solver.tests",
              "depsolver.solver.tests.scenarios",
              "depsolver.tests",
          ],
          license="BSD",
          author="David Cournapeau",
          author_email="cournape@gmail.com",
          url="http://github.com/enthought/depsolver",
          description="Depsolver is a library to deal with package dependencies.",
          long_description=DESCRIPTION,
    )

if __name__ == "__main__":
    run_setup()
