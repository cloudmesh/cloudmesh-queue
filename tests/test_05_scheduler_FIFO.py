###############################################################
# cms set host='juliet.futuresystems.org'
# cms set user=$USER
#
# pytest -v --capture=no tests/test_05_scheduler_FIFO.py
# pytest -v  tests/test_05_scheduler_FIFO.py
# pytest -v --capture=no  tests/test_05_scheduler_FIFO.py::TestSSHJob::<METHODNAME>
###############################################################
import getpass
from pprint import pprint

import pytest
from cloudmesh.common.Benchmark import Benchmark
from cloudmesh.common.util import HEADING
from cloudmesh.common.util import banner
from cloudmesh.common.util import readfile

from cloudmesh.queue.jobqueue import Job
from cloudmesh.queue.jobqueue import SchedulerById
from cloudmesh.queue.jobqueue import Host

Benchmark.debug()

# variables = Variables()
# print(variables)
# variables["jobset"] = path_expand("./a.yaml")

# configured_jobset = variables["jobset"]
# remote_host_ip = variables['host'] or 'juliet.futuresystems.org'
# remote_host_user = variables['user'] or getpass.getuser()

remote = False
sysinfo = False

if remote:
    host = "dgx"
    user = "gregor"
else:
    host = "localhost"
    user = getpass.getuser()

directory = "./experiment"
jobs = []
queue = SchedulerFIFO(name="a")
i = -1


@pytest.mark.incremental
class TestQueue:

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
        Benchmark.Start()
        self.create_command("uname")
        Benchmark.Stop()

    def test_ls(self):
        HEADING()
        Benchmark.Start()

        self.create_command("ls")
        Benchmark.Stop()

    def test_sleep(self):
        HEADING()
        Benchmark.Start()
        self.create_command("/usr/bin/sleep 10")
        Benchmark.Stop()

    def test_which_python(self):
        HEADING()
        Benchmark.Start()
        self.create_command("which python")
        Benchmark.Stop()

    def test_sleep_infinity(self):
        HEADING()
        self.create_command("/usr/bin/sleep infinity")

    def test_add_to_queue(self):
        HEADING()
        global jobs
        Benchmark.Start()
        for job in jobs:
            queue.add(job)
        queue.save()
        print(queue.info(banner="Jobs"))
        print(queue.info(banner="Queue", kind="queue"))

        Benchmark.Stop()

        banner("print")
        print(queue)

    def test_get_info(self):
        HEADING()
        global jobs
        Benchmark.Start()
        print(queue.info(banner="info by id 0", job=0))
        print(queue.info(banner="info by name job0", job="job0"))
        Benchmark.Stop()

    def test_queue_test(self):
        HEADING()
        global jobs
        Benchmark.Start()

        print(queue.info(banner="info by id 0"))
        print()
        print ("LLLL", len(queue))
        print()
        print("queue[0]", queue[0])
        print()
        print ("keys", queue.keys())
        print()
        print("items", queue.items())

        for job in queue.items():
            print (job)
        Benchmark.Stop()



