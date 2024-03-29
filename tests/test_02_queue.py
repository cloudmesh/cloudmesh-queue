###############################################################
# cms set host='juliet.futuresystems.org'
# cms set user=$USER
#
# pytest -v --capture=no tests/test_02_queue.py
# pytest -v  tests/test_02_queue.py
# pytest -v --capture=no  tests/test_02_queue.py::TestSSHJob::<METHODNAME>
###############################################################
import getpass
from pprint import pprint

import pytest
from cloudmesh.common.Benchmark import Benchmark
from cloudmesh.common.util import HEADING
from cloudmesh.common.util import banner
from cloudmesh.common.util import readfile

from cloudmesh.queue.jobqueue import Job
from cloudmesh.queue.jobqueue import Queue
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
queue = Queue(name="a")
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

    def test_delete_job(self):
        HEADING()
        Host.sync(user, host, "experiment")
        job = jobs[4]
        job.run()
        queue.set(job)
        job = queue.delete(job.name)
        assert job.status == 'kill'
        assert job.name not in queue.to_dict()['jobs'].keys()

    def test_refresh(self):
        HEADING()
        job = jobs[0]
        job.run()
        job = jobs[1]
        job.run()
        queue.refresh()
        result = queue.info(banner="Queue", kind="jobs")
        print(result)
        assert 'job0 | end ' in result
        assert 'job1 | end ' in result

    def test_empty_queue(self):
        HEADING()
        empty = Queue(name="b", experiment="b_experiment")
        empty.save()
        content = readfile("./b_experiment/b-queue.yaml")
        print("Content", content)
        print("YAML ", empty.to_yaml())
        empty = Queue(name="b", experiment="b_experiment")
        empty.load()
        empty.add(jobs[0])
        content = readfile("./b_experiment/b-queue.yaml")
        assert content != '{}\n'
        empty.delete(jobs[0].name)
        content = readfile("./b_experiment/b-queue.yaml")
        assert content == '{}\n'

class rest:
    def test_converters(self):
        HEADING()
        Benchmark.Start()
        banner("dict")
        pprint(queue.to_dict())
        banner("yaml")
        print(queue.to_yaml())
        banner("json")
        print(queue.to_json())
        Benchmark.Stop()

    def test_save(self):
        HEADING()
        Benchmark.Start()
        queue.save()
        content = readfile("./experiment/a-queue.yaml")
        Benchmark.Stop()
        assert "job3:" in content
        assert "name: job3" in content

    def test_load_from_file(self):
        HEADING()
        Benchmark.Start()
        q = Queue(name="c")
        q.load(filename="./experiment/a-queue.yaml")
        Benchmark.Stop()
        print(q.to_yaml())
        assert "filename: ./experiment/c-queue.yaml" in q.to_yaml()

    def test_load_with_jobs(self):
        HEADING()
        Benchmark.Start()
        q = Queue(name="d", jobs=jobs)
        q.load(filename="./experiment/d-queue.yaml")
        Benchmark.Stop()
        print(q.to_yaml())
        print("LLL", len(q))
        assert len(q) == len(jobs)
        assert "filename: ./experiment/d-queue.yaml" in q.to_yaml()

    def test_load_queue(self):
        HEADING()
        Benchmark.Start()
        queue = Queue(name='a')
        banner("Jobs")
        print(queue.to_yaml())
        Benchmark.Stop()

    def test_benchmark(self):
        HEADING()
        Benchmark.print(sysinfo=sysinfo, csv=True)


class broken:
    def test_empty_queue(self):
        HEADING()
        empty = Queue(name="b", experiment="b_experiment")
        empty.save()
        content = readfile("./b_experiment/b-queue.yaml")
        print("Content", content)
        queue_str = queue_file.read()
        assert queue.to_yaml() == queue_str
