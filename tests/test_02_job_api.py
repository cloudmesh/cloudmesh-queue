###############################################################
# cms set host='juliet.futuresystems.org'
# cms set user=$USER
#
# pytest -v --capture=no tests/test_02_job_api.py
# pytest -v  tests/test_02_job_api.py
# pytest -v --capture=no  tests/test_02_job_api.py::TestJob::<METHODNAME>
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
from cloudmesh.job.jobqueue import JobQueue
from cloudmesh.job.command.job import QueueCommand
from cloudmesh.common.dotdict import dotdict

import oyaml as yaml
import re
import time
import getpass

Benchmark.debug()

variables = Variables()
variables["jobset"] = path_expand("./a.yaml")

configured_jobset = variables["jobset"]
jobqueue = JobQueue(configured_jobset)


configured_jobset = variables["jobset"]
remote_host_ip = variables['host'] or 'juliet.futuresystems.org'
remote_host_name = variables['hostname'] or 'juliet'

remote_host_user = variables['user'] or getpass.getuser()


@pytest.mark.incremental
class TestJob:

    def test_help(self):
        HEADING()

        Benchmark.Start()
        result = QueueCommand.do_job.__doc__
        Benchmark.Stop()
        VERBOSE(result)

        assert "Usage" in result
        assert "Description" in result

    def test_template(self):
        HEADING()

        Benchmark.Start()
        names = ["job1", "job2"]
        template = dict()

        for name in names:
            template.update(jobqueue.template(name=name))
            jobqueue.add_template(template)

        Benchmark.Stop()

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

        with open('other.yaml', 'w') as fo:
            yaml.safe_dump(job, fo)

        Benchmark.Start()

        jobqueue.add(job)
        Benchmark.Stop()

        time.sleep(5)

        spec1 = Configuration(configured_jobset)
        jobs1 = spec1['cloudmesh.jobset.jobs'].keys()

        assert 'pytest_job' in jobs1

    def test_add_cli(self):
        HEADING()

        Benchmark.Start()
        arguments = dict()

        arguments['executable'] = 'ls'
        arguments['status'] = 'ready'
        arguments['shell'] = 'bash'
        arguments['directory'] = './'
        arguments['names'] = ['pytest_job1']
        arguments['gpu_list'] = [' ']
        arguments['ip_list'] = [remote_host_ip]
        arguments['user'] = remote_host_user
        arguments['arguments_list'] = ['-lisa']
        arguments['input_list'] = ['./data']
        arguments['output_list'] = ['./data']

        jobqueue.update_spec(arguments, configured_jobset)

        Benchmark.Stop()

        spec = Configuration(configured_jobset)
        jobs = spec['cloudmesh.jobset.jobs'].keys()
        assert 'pytest_job1' in jobs

    def test_list(self):
        HEADING()

        Benchmark.Start()
        result = jobqueue.print_jobs()
        Benchmark.Stop()

        job_count_1 = len(re.findall(r"\|\s\d+\s+\|", str(result),
                                     re.MULTILINE))
        Benchmark.Stop()
        VERBOSE(result)

        spec = Configuration(configured_jobset)
        job_count_2 = len(spec['cloudmesh.jobset.jobs'].keys())

        assert job_count_1 == job_count_2

    def test_add_host(self):
        HEADING()

        Benchmark.Start()
        arguments = dict()

        arguments['hostname'] = remote_host_name
        arguments['ip'] = remote_host_ip
        arguments['cpu_count'] = '12'
        arguments['status'] = 'free'
        arguments['job_counter'] = '0'

        dotdict()
        jobqueue.addhost(dotdict(arguments))
        Benchmark.Stop()

        spec = Configuration(configured_jobset)
        host_list = spec['cloudmesh.jobset.hosts'].keys()

        assert remote_host_name in host_list

    def test_run(self):
        HEADING()

        Benchmark.Start()
        result = jobqueue.run_job(['pytest_job1'])
        Benchmark.Stop()
        VERBOSE(result)

        time.sleep(5)
        spec = Configuration(configured_jobset)
        job_status = spec['cloudmesh.jobset.jobs.pytest_job1.status']

        assert job_status == 'submitted'
        assert spec['cloudmesh.jobset.jobs.pytest_job1.submitted_to_ip'] \
               is not None

    def test_kill(self):
        HEADING()

        Benchmark.Start()
        result = jobqueue.kill_job(['pytest_job1'])
        Benchmark.Stop()
        VERBOSE(result)

        time.sleep(5)
        spec = Configuration(configured_jobset)
        job_status = spec['cloudmesh.jobset.jobs.pytest_job1.status']

        assert job_status == 'killed'

    def test_delete(self):
        HEADING()

        Benchmark.Start()
        result = jobqueue.delete_job(['pytest_job1'])
        Benchmark.Stop()
        VERBOSE(result)

        time.sleep(5)
        spec = Configuration(configured_jobset)
        jobs = spec['cloudmesh.jobset.jobs'].keys()

        assert 'pytest_job1' not in jobs

    def test_benchmark(self):
        HEADING()
        Benchmark.print(csv=True, sysinfo=False)
