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
from cloudmesh.common.util import banner
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

remote = False

if remote:
    host = "dgx"
    user = "gregor"
else:
    host = "localhost"
    user = getpass.getuser()

directory = "./experiment"
jobs = []
i = -1


@pytest.mark.incremental
class TestJob:

    def create_command(self, command):
        global jobs, i
        i = i + 1

        Benchmark.Start()
        job = Job(name=f"job{i}",
                  command=command,
                  user=user,
                  host=host,
                  directory=directory)
        jobs.append(job)
        Benchmark.Stop()
        print(job)

    def test_hostname(self):
        HEADING()
        self.create_command("uname")

    def test_ls(self):
        HEADING()
        self.create_command("ls")

    def test_sleep(self):
        HEADING()
        self.create_command("/usr/bin/sleep 10")

    def test_which_python(self):
        HEADING()
        self.create_command("which python")

    def test_sync(self):
        HEADING()
        Benchmark.Start()
        result = Host.sync(user, host, "experiment")
        Benchmark.Stop()
        assert result
        print(result)

    def run_job(self, i):
        global jobs

        job = jobs[i]
        Benchmark.Start()
        result = job.run()
        Benchmark.Stop()
        print(result)

    def monitor_job_state(self, i):
        global jobs
        job = jobs[i]

        Benchmark.Start()
        result = "undefined"
        while result not in ["end"]:
            result = job.state
            print ("Job info:", job.pid, result, job.ps())
            time.sleep(1)
        Benchmark.Stop()
        print(result)
        banner("Log")
        print(job.get_log())
        banner("Log Nohup")
        print(job.get_log_nohup())
        banner("Out")
        print(job.get_output())


    def test_state_job2(self):
        HEADING()
        self.run_job(2)
        self.monitor_job_state(2)

    def test_state_job0(self):
        HEADING()
        self.run_job(0)
        self.monitor_job_state(0)


class gg:
    def test_yaml_job2(self):
        HEADING()

        global jobs
        job = jobs[2]

        Benchmark.Start()
        result = job.to_yaml()
        Benchmark.Stop()
        print(result)


    def test_read_from_string(self):
        HEADING()

        HEADING()

        global jobs
        job = jobs[2]

        job_str = dedent("""
              pytest_job:
                name: pytest_job
                experiment: experiment
                user: user
                host: dgx
                command: ls -lisa
                shell: bash
        """)

        Benchmark.Start()

        job_sleep = Job().load_from_yaml(job_str)

        Benchmark.Stop()
        print(job_sleep)

    def test_read_from_flat_string(self):
        HEADING()

        HEADING()

        global jobs
        job = jobs[2]

        job_str = dedent("""
                name: pytest_job
                experiment: experiment
                user: user
                host: dgx
                command: ls -lisa
                shell: bash
        """)

        Benchmark.Start()

        job_sleep = Job().load_from_yaml(job_str, with_key=False)

        Benchmark.Stop()
        print(job_sleep)



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
