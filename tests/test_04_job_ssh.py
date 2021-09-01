###############################################################
# cms set host='juliet.futuresystems.org'
# cms set user=$USER
#
# pytest -v --capture=no tests/test_04_job_ssh.py
# pytest -v  tests/test_04_job_ssh.py
# pytest -v --capture=no  tests/test_04_job_ssh.py::TestSSHJob::<METHODNAME>
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
from cloudmesh.queue.jobqueue import Job
from cloudmesh.queue.jobqueue import Host

import oyaml as yaml
import re
import time
import getpass

Benchmark.debug()

#variables = Variables()
#print(variables)
#variables["jobset"] = path_expand("./a.yaml")

#configured_jobset = variables["jobset"]
#remote_host_ip = variables['host'] or 'juliet.futuresystems.org'
#remote_host_user = variables['user'] or getpass.getuser()

host = "dgx"
user = "gregor"
directory = "./experiment"
job1 = None
job2 = None
job3 = None

@pytest.mark.incremental
class TestJob:

    def test_hostname(self):
        HEADING()

        global job1

        Benchmark.Start()
        job1 = Job(name="job1",
                   command = "uname -u",
                   user=user,
                   host=host,
                   directory=directory)
        Benchmark.Stop()
        print(job1)

    def test_ls(self):
        HEADING()

        global job2

        Benchmark.Start()
        job2 = Job(name="job2",
                   command="ls",
                   user=user,
                   host=host,
                   directory=directory)
        Benchmark.Stop()
        print (job2)

    def test_sleep(self):
        HEADING()

        global job3

        Benchmark.Start()
        job3 = Job(name="job3",
                   command="/usr/bin/sleep 10",
                   user=user,
                   host=host,
                   directory=directory)
        Benchmark.Stop()
        print(job3)

    def test_sync(self):
        HEADING()
        Benchmark.Start()
        result = Host.sync(user, host, "experiment")
        Benchmark.Stop()
        assert result
        print(result)

    def test_run_job3(self):
        HEADING()

        global job3

        Benchmark.Start()
        result = job3.run()
        Benchmark.Stop()
        print(result)

    def test_state_job3(self):
        HEADING()

        global job3

        Benchmark.Start()
        result = "undefined"
        while result not in ["end"]:
            result = job3.state
            print (result)
            time.sleep(1)
        Benchmark.Stop()
        print(result)



class a:

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

        time.sleep(10)

        spec1 = Configuration(configured_jobset)
        jobs1 = spec1['cloudmesh.jobset.jobs'].keys()

        assert 'pytest_job' in jobs1


    def test_benchmark(self):
        HEADING()
        Benchmark.print(csv=True)
