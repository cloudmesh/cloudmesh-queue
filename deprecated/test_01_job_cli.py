###############################################################
# cms set host='juliet.futuresystems.org'
# cms set user=$USER
#
# pytest -v --capture=no tests/test_01_job_cli.py
# pytest -v  tests/test_01_job_cli.py
# pytest -v --capture=no  tests/test_01_job_cli.py::TestJob::<METHODNAME>
###############################################################
import pytest
from cloudmesh.common.Shell import Shell
from cloudmesh.common.debug import VERBOSE
from cloudmesh.common.util import HEADING
from cloudmesh.common.Benchmark import Benchmark
from cloudmesh.common.variables import Variables
from cloudmesh.configuration.Configuration import Configuration
from textwrap import dedent
from cloudmesh.common.util import path_expand

import oyaml as yaml
import re
import time
import getpass

Benchmark.debug()

variables = Variables()
print(variables)
variables["jobset"] = path_expand("./a.yaml")

configured_jobset = variables["jobset"]
remote_host_ip = variables['host'] or 'juliet.futuresystems.org'
remote_host_user = variables['user'] or getpass.getuser()


@pytest.mark.incremental
class TestJob:

    def test_help(self):
        HEADING()

        Benchmark.Start()
        result = Shell.execute("cms job help", shell=True)
        Benchmark.Stop()
        VERBOSE(result)

        assert "Usage" in result
        assert "Description" in result

    def test_info(self):
        HEADING()

        Benchmark.Start()
        variables = Variables()
        configured_jobset = variables["jobset"]
        result = Shell.execute("cms job info", shell=True)
        Benchmark.Stop()
        VERBOSE(result)

        assert configured_jobset in result

    def test_template(self):
        HEADING()

        Benchmark.Start()
        result = Shell.execute("cms job template --name='job[1-2]'", shell=True)
        Benchmark.Stop()
        VERBOSE(result)

        spec = Configuration(configured_jobset)

        assert spec['cloudmesh.jobset.hosts'] is not None
        jobs = spec['cloudmesh.jobset.jobs'].keys()
        assert 'job1' in jobs
        assert 'job2' in jobs

    def test_add_file(self):
        HEADING()

        job_str = dedent("""
              pytest_job:
                name: pytest_job
                directory: .
                ip: local
                input: ./data
                output: ./output/abcd
                status: ready
                gpu: ' '
                user: user
                arguments: -lisa
                executable: ls
                shell: bash
        """).strip()

        job = yaml.safe_load(job_str)

        with open('../tests/other.yaml', 'w') as fo:
            yaml.safe_dump(job, fo)

        Benchmark.Start()
        result = Shell.execute("cms job add 'other.yaml'", shell=True)
        Benchmark.Stop()
        VERBOSE(result)

        time.sleep(10)

        spec1 = Configuration(configured_jobset)
        jobs1 = spec1['cloudmesh.jobset.jobs'].keys()

        assert 'pytest_job' in jobs1

    def test_add_cli(self):
        HEADING()

        Benchmark.Start()
        result = Shell.execute("cms job add --name='pytest_job1' " 
                               f"--ip={remote_host_ip} " 
                               "--executable='ls' " 
                               "--arguments='-lisa' " 
                               f"--user='{remote_host_user}' ",
                               shell=True)
        Benchmark.Stop()
        VERBOSE(result)

        spec = Configuration(configured_jobset)
        jobs = spec['cloudmesh.jobset.jobs'].keys()
        assert 'pytest_job1' in jobs

    def test_list(self):
        HEADING()

        Benchmark.Start()
        result = Shell.execute("cms job list", shell=True)
        Benchmark.Stop()

        job_count_1 = len(re.findall(r"\|\s\d+\s+\|", result, re.MULTILINE))

        VERBOSE(result)

        spec = Configuration(configured_jobset)
        job_count_2 = len(spec['cloudmesh.jobset.jobs'].keys())

        assert job_count_1 == job_count_2

    def test_add_host(self):
        HEADING()

        Benchmark.Start()
        result = Shell.execute("cms job hosts add --hostname='juliet' "
                               f"--ip='{remote_host_ip}' "
                               "--cpu_count='12'", shell=True)
        VERBOSE(result)

        spec = Configuration(configured_jobset)
        host_list = spec['cloudmesh.jobset.hosts'].keys()

        assert 'juliet' in host_list

    def test_run(self):
        HEADING()

        Benchmark.Start()
        result = Shell.execute("cms job run --name='pytest_job1'", shell=True)
        Benchmark.Stop()
        VERBOSE(result)

        time.sleep(10)
        spec = Configuration(configured_jobset)
        job_status = spec['cloudmesh.jobset.jobs.pytest_job1.status']

        assert job_status == 'submitted'
        assert spec['cloudmesh.jobset.jobs.pytest_job1.submitted_to_ip'] \
               is not None

    def test_kill(self):
        HEADING()

        Benchmark.Start()
        result = Shell.execute("cms job kill --name='pytest_job1'", shell=True)
        Benchmark.Stop()
        VERBOSE(result)

        time.sleep(10)
        spec = Configuration(configured_jobset)
        job_status = spec['cloudmesh.jobset.jobs.pytest_job1.status']

        assert job_status == 'killed'

    def test_reset(self):
        HEADING()

        Benchmark.Start()
        result = Shell.execute("cms job reset --name='pytest_job1'", shell=True)
        Benchmark.Stop()
        VERBOSE(result)

        time.sleep(5)
        spec = Configuration(configured_jobset)
        job_status = spec['cloudmesh.jobset.jobs.pytest_job1.status']

        assert job_status == 'ready'

    def test_delete(self):
        HEADING()

        Benchmark.Start()
        result = Shell.execute("cms job delete --name='pytest_job1'",
                               shell=True)
        Benchmark.Stop()
        VERBOSE(result)

        time.sleep(5)
        spec = Configuration(configured_jobset)
        jobs = spec['cloudmesh.jobset.jobs'].keys()

        assert 'pytest_job1' not in jobs

    def test_benchmark(self):
        HEADING()
        Benchmark.print(csv=True)
