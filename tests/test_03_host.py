###############################################################
# cms set host='juliet.futuresystems.org'
# cms set user=$USER
#
# pytest -v --capture=no tests/test_03_host.py
# pytest -v  tests/test_03 _queue.py
# pytest -v --capture=no  tests/test_03 _queue.py::TestSSHJob::<METHODNAME>
###############################################################
import getpass
from pprint import pprint

import pytest
from cloudmesh.common.Benchmark import Benchmark
from cloudmesh.common.util import HEADING
from cloudmesh.common.util import banner
from cloudmesh.common.util import readfile

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
    ip = '192.168.1.16'
else:
    host = "localhost"
    user = getpass.getuser()

directory = "./experiment"
hosts = []
i = -1


@pytest.mark.incremental
class TestHost:

    def create_host(self, name):
        global hosts
        Benchmark.Start()
        host = Host(name=name)
        hosts.append(host)
        Benchmark.Stop()

    def test_create(self):
        HEADING()
        global hosts

        Benchmark.Start()

        self.create_host("localhost")
        self.create_host("a")

        print (hosts)

        Benchmark.Stop()

        assert "name='localhost'" in str(hosts)
        assert "name='a'" in str(hosts)

    def test_info(self):
        HEADING()
        global hosts

        Benchmark.Start()

        host = hosts[0]

        print(host.info())

        Benchmark.Stop()

    def test_benchmark(self):
        HEADING()
        Benchmark.print(sysinfo=sysinfo, csv=True)

    def test_ping(self):
        HEADING()
        Benchmark.Start()
        if not remote:
            result, time = hosts[0].ping()
            assert hosts[0].ping_status == result
            assert hosts[0].ping_time == time
        else:
            rhost = Host(name=host,ip=ip)
            result, time = rhost.ping()
            assert rhost.ping_status == result
            assert rhost.ping_time == time
        print(f"Ping success: {result}")
        print(f"datetime: {time}")

        Benchmark.Stop()

