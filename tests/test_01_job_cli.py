###############################################################
# pytest -v --capture=no tests/test_01_job_cli.py
# pytest -v  tests/test_01_job_cli.py
# pytest -v --capture=no  tests/test_01_job_cli.py::TestJob::<METHODNAME>
###############################################################
import pytest
from cloudmesh.common.Shell import Shell
from cloudmesh.common.debug import VERBOSE
from cloudmesh.common.util import HEADING
from cloudmesh.common3.Benchmark import Benchmark
from cloudmesh.common.variables import Variables
from cloudmesh.configuration.Config import Config
from textwrap import dedent
import oyaml as yaml
import re, time

Benchmark.debug()


@pytest.mark.incremental
class TestJob:

    variables = Variables()
    configured_jobset = variables["jobset"]

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

        spec = Config(TestJob.configured_jobset)
        assert spec['cloudmesh.hosts'] is not None
        jobs = spec['jobs'].keys()
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

        with open('other.yaml', 'w') as fo:
            yaml.safe_dump(job, fo)

        Benchmark.Start()
        result = Shell.execute("cms job add 'other.yaml'", shell=True)
        Benchmark.Stop()
        VERBOSE(result)

        spec = Config(TestJob.configured_jobset)
        jobs = spec['jobs'].keys()
        assert 'pytest_job' in jobs

    def test_add_cli(self):
        HEADING()

        Benchmark.Start()
        result = Shell.execute('cms job add --name=\'pytest_job1\' ' \
                               '--ip=juliet.futuresystems.org ' \
                               '--executable=\'ls\' ' \
                               '--arguments=\'-lisa\' ' \
                               '--user=\'ketanp\' ',
                               shell=True)
        Benchmark.Stop()
        VERBOSE(result)

        spec = Config(TestJob.configured_jobset)
        jobs = spec['jobs'].keys()
        assert 'pytest_job1' in jobs

    def test_list(self):
        HEADING()

        Benchmark.Start()
        result = Shell.execute("cms job list", shell=True)
        Benchmark.Stop()

        job_count_1 = len(re.findall(r"\|\s\d+\s+\|", result, re.MULTILINE))

        VERBOSE(result)

        spec = Config(TestJob.configured_jobset)
        job_count_2 = len(spec['jobs'].keys())

        assert job_count_1 == job_count_2

    def test_run(self):
        HEADING()

        Benchmark.Start()
        result = Shell.execute("cms job run --name='pytest_job1'", shell=True)
        Benchmark.Stop()
        VERBOSE(result)

        time.sleep(10)
        spec = Config(TestJob.configured_jobset)
        job_status = spec['jobs.pytest_job1.status']

        assert job_status == 'submitted'
        assert spec['jobs.pytest_job1.submitted_to_ip'] is not None

    def test_kill(self):
        HEADING()

        Benchmark.Start()
        result = Shell.execute("cms job kill --name='pytest_job1'", shell=True)
        Benchmark.Stop()
        VERBOSE(result)

        time.sleep(10)
        spec = Config(TestJob.configured_jobset)
        job_status = spec['jobs.pytest_job1.status']

        assert job_status == 'killed'



    # def test_vm(self):
    #     HEADING()
    #     Benchmark.Start()
    #     result = Shell.execute("cms help vm", shell=True)
    #     Benchmark.Stop()
    #     VERBOSE(result)
    #
    #     assert "['sample1', 'sample2', 'sample3', 'sample18']" in result
    #
    # def test_help_again(self):
    #     HEADING()
    #
    #     Benchmark.Start()
    #     result = Shell.execute("cms help", shell=True)
    #     Benchmark.Stop()
    #     VERBOSE(result)
    #
    #     assert "quit" in result
    #     assert "clear" in result
    #
    def test_benchmark(self):
        HEADING()
        Benchmark.print(csv=True)
