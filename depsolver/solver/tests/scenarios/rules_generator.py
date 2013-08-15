import collections
import glob
import json
import subprocess
import tempfile

import os.path as op

import tempita
import yaml

from depsolver._package_utils \
    import \
        parse_package_full_name
from depsolver.package \
    import \
        parse_package_string, PackageInfo
from depsolver.pool \
    import \
        Pool
from depsolver.repository \
    import \
        Repository
from depsolver.request \
    import \
        Request
from depsolver.requirement \
    import \
        Requirement
from depsolver.solver.rules_generator \
    import \
        RulesGenerator
from depsolver.version \
    import \
        Version

from depsolver.bundled.traitlets \
    import \
        HasTraits, Dict, Instance, List, Long, Unicode

from depsolver.solver.tests.scenarios.common \
    import \
        COMMON_IMPORTS, COMPOSER_PATH, packages_list_to_php_json, \
        requirement_to_php_string, requirement_string_to_php_constraints

DATA = op.join(op.dirname(__file__), "data", "rules_generator")

P = PackageInfo.from_string
R = Requirement.from_string
V = Version.from_string

TEMPLATE = """\
<?php
require {{bootstrap_path}};

{{common_imports}}

$loader = new ArrayLoader();

/* Remote repository definition */
$remote_repo_json = '
{{remote_repo_json_string}}
';

$packages = JsonFile::parseJson($remote_repo_json);

$remote_repo = new WritableArrayRepository();
foreach ($packages as $packageData) {
    $package = $loader->load($packageData);
    $remote_repo->addPackage($package);
}

/* Installed repository definition */
$repo_json = '
{{installed_repo_json_string}}
';

$packages = JsonFile::parseJson($repo_json);

$installed_repo = new WritableArrayRepository();
foreach ($packages as $packageData) {
    $package = $loader->load($packageData);
    $installed_repo->addPackage($package);
}

/* Pool definition */
$pool = new Pool();
$pool->addRepository($remote_repo);
$pool->addRepository($installed_repo);

$request = new Request($pool);
{{for operation, requirement_name, constraints in request}}
$constraints = array(
    {{constraints}}
);
$request_constraints = new MultiConstraint($constraints);
$request->{{operation}}("{{requirement_name}}", $request_constraints);
{{endfor}}

class DebuggingSolver extends Solver
{
    public function printRules(Request $request)
    {
        $this->jobs = $request->getJobs();

        $this->setupInstalledMap();

        $this->decisions = new Decisions($this->pool);

        $this->rules = $this->ruleSetGenerator->getRulesFor($this->jobs, $this->installedMap);
        $this->watchGraph = new RuleWatchGraph;

        foreach ($this->rules as $rule) {
            printf("%s\\n", $rule);
        }
    }
}

$policy = new DefaultPolicy();

$solver = new DebuggingSolver($policy, $pool, $installed_repo);
$solver->printRules($request);
"""

class RulesGeneratorScenario(HasTraits):
    remote_repository = Instance(Repository)
    installed_repository = Instance(Repository)

    pool = Instance(Pool)
    request = Instance(Request)

    @classmethod
    def from_yaml(cls, filename):
        with open(filename, "rt") as fp:
            raw_data = yaml.load(fp)

        packages = [P(s) for s in raw_data.get("packages", [])]
        package_name_to_package = {}
        for package in packages:
            package_name_to_package[package.unique_name] = package

        raw_installed_packages = raw_data.get("installed_repository", []) or []
        installed_packages = [package_name_to_package[package_name] \
                                for package_name in raw_installed_packages]
            
        raw_remote_packages = raw_data.get("remote_repository", []) or []
        remote_packages = [package_name_to_package[package_name] \
                             for package_name in raw_remote_packages]

        request_data = [(r["operation"], r["requirement"]) \
                        for r in raw_data.get("request", []) or []]

        return cls.from_data(remote_packages=remote_packages,
                installed_packages=installed_packages,
                request_jobs=request_data)

    @classmethod
    def from_data(cls, remote_packages, installed_packages, request_jobs):
        remote_repository = Repository(packages=[P(p.package_string) for p in remote_packages])
        installed_repository = Repository(packages=[P(p.package_string) for p in installed_packages])

        pool = Pool([remote_repository, installed_repository])
        request = Request(pool)
        for name, requirement_string in request_jobs:
            getattr(request, name)(R(requirement_string))

        return cls(remote_repository=remote_repository,
                   installed_repository=installed_repository,
                   pool=pool, request=request)

    def compute_rules(self):
        installed_map = collections.OrderedDict()
        for package in self.installed_repository.iter_packages():
            installed_map[package.id] = package
        rules_generator = RulesGenerator(self.pool, self.request, installed_map)
        return list(rules_generator.iter_rules())

    def to_php(self, filename="test_installed_map.php", composer_location=None):
        if composer_location is None:
            bootstrap_path = "__DIR__.'/src/bootstrap.php'"
        else:
            bootstrap_path = "'%s'" % op.join(composer_location, "src", "bootstrap.php")

        template = tempita.Template(TEMPLATE)

        remote_packages = self.remote_repository.list_packages()
        installed_packages = self.installed_repository.list_packages()


        def job_to_php_constraints(job):
            s = str(job.requirement)

            constraints = ['new VersionConstraint("%s", "%s")' % \
                           (ret[0], ret[1]) \
                            for ret in requirement_string_to_php_constraints(s)]
            return ',\n'.join(constraints)

        variables = {
                "bootstrap_path": bootstrap_path,
                "remote_repo_json_string": packages_list_to_php_json(remote_packages),
                "installed_repo_json_string": packages_list_to_php_json(installed_packages),
                "request": [(job.job_type, job.requirement.name, job_to_php_constraints(job)) \
                            for job in self.request.jobs],
                "common_imports": COMMON_IMPORTS,
        }
        with open(filename, "wt") as fp:
            fp.write(template.substitute(variables))

def post_process(output):
    """Crappy function to convert php rule string to depsolver ones."""
    lines = []
    for line in output.splitlines():
        new_parts = []
        parts = [p.strip() for p in line[1:-1].split("|")]
        for part in parts:
            if part.startswith("-"):
                part = part[1:-2]
                name, version = parse_package_full_name(part)
                new_part = "-" + "%s-%s" % (name, str(version))
            else:
                part = part[:-2]
                name, version = parse_package_full_name(part)
                new_part = "%s-%s" % (name, str(version))
            new_parts.append(new_part)
        lines.append("(" + " | ".join(new_parts) + ")")
    lines.append("")
    return "\n".join(lines)

if __name__ == "__main__":
    d = op.join(op.dirname(__file__), "data", "rules_generator")

    for path in glob.glob(op.join(d, "*.yaml")):
        print path
        php_file = op.splitext(path)[0] + ".php"

        scenario = RulesGeneratorScenario.from_yaml(path)
        scenario.to_php(php_file, composer_location=COMPOSER_PATH)
        with tempfile.NamedTemporaryFile(suffix=".php") as fp:
            scenario.to_php(fp.name, composer_location=COMPOSER_PATH)

            with open(op.splitext(path)[0] + ".test", "wt") as ofp:
                output = subprocess.check_output(["php", fp.name])
                ofp.write(post_process(output))
