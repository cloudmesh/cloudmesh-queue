###############################################################
# cms set host='juliet.futuresystems.org'
# cms set user=$USER
#
# pytest -v --capture=no tests/test_06_cluster.py
# pytest -v  tests/test_06_cluster.py
# pytest -v --capture=no  tests/test_06_cluster.py::TestSSHHost::<METHODNAME>
###############################################################
import getpass
from pprint import pprint

import pytest
from cloudmesh.common.Benchmark import Benchmark
from cloudmesh.common.util import HEADING
from cloudmesh.common.util import banner
from cloudmesh.common.util import readfile

from cloudmesh.queue.jobqueue import Host
from cloudmesh.queue.jobqueue import Cluster

Benchmark.debug()

# variables = Variables()
# print(variables)
# variables["hostset"] = path_expand("./a.yaml")

# configured_hostset = variables["hostset"]
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
hosts = []
cluster = Cluster(name="a")
i = -1


@pytest.mark.incremental
class TestCluster:

    def create_host(self):
        global hosts, i
        i = i + 1

        Benchmark.Start()
        host = Host(name=f"host{i}")
        hosts.append(host)
        Benchmark.Stop()
        print(host)

    def test_create_hosts(self):
        HEADING()
        Benchmark.Start()
        self.create_host()
        self.create_host()
        self.create_host()
        self.create_host()
        Benchmark.Stop()

    def test_add_to_cluster(self):
        HEADING()
        global hosts
        Benchmark.Start()
        for host in hosts:
            cluster.add(host)
        cluster.save()
        Benchmark.Stop()

        banner("print")
        print(cluster)

    def test_converters(self):
        HEADING()
        Benchmark.Start()
        banner("dict")
        pprint(cluster.to_dict())
        banner("yaml")
        print(cluster.to_yaml())
        banner("json")
        print(cluster.to_json())
        Benchmark.Stop()

    def test_save(self):
        HEADING()
        Benchmark.Start()
        cluster.save()
        content = readfile("./experiment/a-cluster.yaml")
        Benchmark.Stop()
        assert "host3:" in content
        assert "name: host3" in content

    def test_load_from_file(self):
        HEADING()
        Benchmark.Start()
        q = Cluster(name="c")
        q.load(filename="./experiment/a-cluster.yaml")
        Benchmark.Stop()
        print(q.to_yaml())
        assert "filename: ./experiment/c-cluster.yaml" in q.to_yaml()

    def test_load_with_hosts(self):
        HEADING()
        Benchmark.Start()
        q = Cluster(name="d", hosts=hosts)
        q.load(filename="./experiment/d-cluster.yaml")
        Benchmark.Stop()
        print(q.to_yaml())
        print("LLL", len(q))
        assert len(q) == len(hosts)
        assert "filename: ./experiment/d-cluster.yaml" in q.to_yaml()

    def test_load_cluster(self):
        HEADING()
        Benchmark.Start()
        cluster = Cluster(name='a')
        banner("Hosts")
        print(cluster.to_yaml())
        Benchmark.Stop()

    def test_info(self):
        HEADING()
        Benchmark.Start()
        cluster = Cluster(name='a')
        print(cluster.info())
        print(cluster.info(banner="Host by name host0", host="host0"))
        print(cluster.info(banner="Host by id 0", host=0))
        print(cluster.info(banner="Host by id 0 in yaml", host=0, output="yaml"))

        Benchmark.Stop()

    def test_benchmark(self):
        HEADING()
        Benchmark.print(sysinfo=sysinfo, csv=True)


