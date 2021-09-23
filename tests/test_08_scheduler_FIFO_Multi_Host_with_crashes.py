###############################################################
# cms set host='juliet.futuresystems.org'
# cms set user=$USER
#
# pytest -v --capture=no tests/test_08_scheduler_FIFO_Multi_Host_with_crashes.py
# pytest -v  tests/test_08_scheduler_FIFO_Multi_Host_with_crashes.py
# pytest -v --capture=no  tests/test_06_scheduler_FIFO_Multi_Host_with_crashes.py::TestSSHJob::<METHODNAME>
###############################################################
import getpass
from pprint import pprint

import pytest
from cloudmesh.common.Benchmark import Benchmark
from cloudmesh.common.util import HEADING
from cloudmesh.common.util import banner
from cloudmesh.common.util import readfile

from cloudmesh.queue.jobqueue import Job
from cloudmesh.queue.jobqueue import SchedulerFIFOMultiHost
from cloudmesh.queue.jobqueue import Host
from cloudmesh.common.console import Console
from cloudmesh.common.Shell import Shell

Benchmark.debug()

# variables = Variables()
# print(variables)
# variables["jobset"] = path_expand("./a.yaml")

# configured_jobset = variables["jobset"]
# remote_host_ip = variables['host'] or 'juliet.futuresystems.org'
# remote_host_user = variables['user'] or getpass.getuser()

# THIS TEST REQUIRES MANUAL INTERVENTION TO DETECT PROCESS AND HOST CRASHES
# Three jobs must be manuall killed or have the host shutdown for the queue
# to finish the run

remote = True
sysinfo = False

if remote:
    host = "red"
    user = "pi"
    host2 = "red01"
    user2 = "pi"
    host3 = 'red03'
    user3 = 'pi'
else:
    host = "localhost"
    user = getpass.getuser()
    host2 = "localhost"
    user2 = getpass.getuser()

directory = "./experiment"
jobs = []
hosts = []
for i in range(4):
    ahost = Host(name=host, user=user, ip=None)
    hosts.append(ahost)
ahost = Host(name=host2,user=user2, ip=None)
hosts.append(ahost)
if remote:
    # tests down worker
    ahost = Host(name=host3,user=user3, ip=None)
    hosts.append(ahost)
queue = SchedulerFIFOMultiHost(name="a",hosts=hosts)
i = -1


@pytest.mark.incremental
class TestQueue:

    def create_command(self, command):
        global jobs, i
        i = i + 1

        Benchmark.Start()
        job = Job(name=f"job{i}",
                  command=command,
                  # user=user,
                  # host=host,
                  directory=directory)
        jobs.append(job)
        Benchmark.Stop()
        print(job)

    def create_command_unassigned(self, command):
        global jobs, i
        i = i + 1

        Benchmark.Start()
        job = Job(name=f"job{i}",
                  command=command,
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

    def test_sleep1(self):
        HEADING()
        Benchmark.Start()
        self.create_command_unassigned("/usr/bin/sleep 10")
        Benchmark.Stop()

    def test_sleep2(self):
        HEADING()
        Benchmark.Start()
        self.create_command("/usr/bin/sleep 10")
        Benchmark.Stop()

    def test_sleep3(self):
        HEADING()
        Benchmark.Start()
        self.create_command("/usr/bin/sleep 10")
        Benchmark.Stop()

    def test_sleep4(self):
        HEADING()
        Benchmark.Start()
        self.create_command("/usr/bin/sleep 10")
        Benchmark.Stop()

    def test_sleep_infinity_crash1(self):
        HEADING()
        self.create_command("/usr/bin/sleep infinity")

    def test_sleep_infinity_crash2(self):
        HEADING()
        self.create_command("/usr/bin/sleep infinity")

    def test_sleep_infinity_crash3(self):
        HEADING()
        self.create_command("/usr/bin/sleep infinity")

    def test_sleep_infinity_crash4(self):
        HEADING()
        self.create_command("/usr/bin/sleep infinity")

    def test_sleep_infinity_crash5(self):
        HEADING()
        self.create_command("/usr/bin/sleep infinity")

    def test_hostname2(self):
        HEADING()
        Benchmark.Start()
        self.create_command("uname")
        Benchmark.Stop()

    def test_sync(self):
        HEADING()
        Benchmark.Start()
        result = Host.sync(user, host, "experiment")
        result = Host.sync(user2, host2, "experiment")
        Benchmark.Stop()
        assert result
        print(result)

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

    def test_queue_run(self):
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
            print()
            print (job)
            print()

        if len(hosts) == 1:
            #skip job 4 since it never ends
            job4 = queue.get('job4')
            job4 = Job(**job4)
            job4.status = 'skip'
            queue.set(job4)

        ran_jobs = queue.run()
        Console.info(f"Ran Jobs: {ran_jobs}")

        for i in range(9):
            if i !=4:
                assert f'job{i}' in ran_jobs
            elif len(hosts) > 1 and i == 4:
                assert f'job4' in ran_jobs
            else:
                assert f'job{i}' not in ran_jobs

        # test deleting a job
        queue.delete('job4')

        # At end the queue will fill with 5 sleep infinity jobs
        # crash these jobs and make sure queue continues to process jobs

        for i in range(9,14):
            job = Job(**queue.get(f'job{i}'))
            print(f'{job.name} {job.host} {job.pid}')
            command = f'kill -9 $(ps -o pid= --ppid {job.pid});' + \
                      f'kill -9 {job.pid};'
            command = f"ssh {job.user}@{job.host} \"{command}\""
            Shell.run(command)

        completed_jobs = queue.wait_on_running()
        Console.info(f"Completed Jobs: {completed_jobs}")

        for i in range(15):
            if i !=4 and i!=9 and i!=10 and i!=11 and i!=12 and i!=13:
                assert f'job{i}' in completed_jobs
            else:
                # job 4 was deleted from queue
                # job 9-13 were crashed
                assert f'job{i}' not in completed_jobs

        print(queue.info(banner="info by id 0"))

        Benchmark.Stop()



