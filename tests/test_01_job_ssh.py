###############################################################
# pytest -v --capture=no tests/test_01_job_ssh.py
# pytest -v  tests/test_01_job_ssh.py
# pytest -v --capture=no  tests/test_01_job_ssh.py::TestSSHJob::<METHODNAME>
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
from cloudmesh.common.systeminfo import os_is_windows, os_is_mac

import oyaml as yaml
import re
import time
import getpass
import os
from cloudmesh.common.Printer import Printer

Benchmark.debug()

# variables = Variables()
# print(variables)
# variables["jobset"] = path_expand("./a.yaml")

# configured_jobset = variables["jobset"]
# remote_host_ip = variables['host'] or 'juliet.futuresystems.org'
# remote_host_user = variables['user'] or getpass.getuser()

remote = False
crash_host_test = True

crash_host = 'unkonwn-host'
crash_user = 'unkonw-user'

if remote:
    host = "red"
    user = "pi"
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

    def test_set_vars(self):
        HEADING()
        Shell.run(f"cms set host={host}")
        Shell.run(f"cms set user={user}")

    def test_command_create(self):
        HEADING()
        if os_is_windows():
            raise NotImplementedError("implement me")
        elif os_is_mac():
            sleep = "/bin/sleep"
        else:
            sleep = "/usr/bin/sleep"
        self.create_command("uname")
        self.create_command("ls")
        self.create_command(f"{sleep} 10")
        self.create_command("which python")
        self.create_command(f"{sleep} infinity")
        self.create_command(f"{sleep} infinity")
        self.create_command(f"{sleep} infinity")
        for job in jobs:
            print(job)
        assert len(jobs) == 7

    def test_sync(self):
        HEADING()
        global crash_host
        global crash_user
        Benchmark.Start()
        result = Host.sync(user, host, "experiment")
        assert result

        if crash_host_test:
            result = Host.sync(crash_user, crash_host, "experiment")
        Benchmark.Stop()
        assert not result
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
        while result not in ["end", "kill"]:
            result = job.state
            print("Job info:", job.pid, result, job.ps(), job.command)
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

    def test_kill_job(self):
        HEADING()
        self.run_job(4)
        r = jobs[4].kill()
        self.monitor_job_state(4)
        assert r == 0
        assert jobs[4].status == 'kill'

    def test_state_env3_job(self):
        HEADING()
        jobs[5].run()

    def test_running(self):
        HEADING()
        jobs[6].run()
        running = jobs[6].check_running()
        print(f'Runningd: {running}')
        assert running is True
        jobs[6].kill()
        running = jobs[6].check_running()
        print(f'Running: {running}')
        assert running is False

    def test_crashed(self):
        HEADING()
        job = jobs[7]
        job.run()
        running = job.check_running()
        print(f'Running: {running}')
        assert running is True
        crashed = job.check_crashed()
        print(f'Crashed: {crashed}')
        assert crashed is False
        command = f'kill -9 $(ps -o pid= --ppid {job.pid});' + \
                  f'kill -9 {job.pid};'
        command = f"ssh {job.user}@{job.host} \"{command}\""
        Shell.run(command)
        running = job.check_running()
        print(f'Running: {running}')
        assert running is False
        crashed = job.check_crashed()
        print(f'Crashed: {crashed}')
        assert crashed is True
        assert job.state == 'crash'

    def test_crashed_host(self):
        if crash_host_test and remote:
            HEADING()
            job = jobs[8]
            job.host = crash_host
            job.user = crash_user
            job.generate_command()
            job.run()
            running = job.check_running()
            print(f'Running: {running}')
            assert running is True
            crashed = job.check_crashed()
            print(f'Crashed: {crashed}')
            assert crashed is False
            command = f'sudo shutdown -h now'
            command = f"ssh {job.user}@{job.host} \"{command}\""
            Shell.run(command)
            time.sleep(5)
            running = job.check_running()
            print(f'Running: {running}')
            assert running is False
            crashed = job.check_crashed()
            print(f'Crashed: {crashed}')
            assert crashed is True
            assert job.state == 'crash'


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
