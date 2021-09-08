import json
import multiprocessing
import os
import shlex
import sys
# import time
import uuid
from dataclasses import dataclass
from datetime import datetime
# from pathlib import Path
from textwrap import dedent
from typing import List

import oyaml as yaml

from cloudmesh.common.Host import Host as commonHost
from cloudmesh.common.Printer import Printer
from cloudmesh.common.Shell import Shell
from cloudmesh.common.console import Console
# from cloudmesh.common.parameter import Parameter
from cloudmesh.common.util import banner
from cloudmesh.common.util import is_local
# from cloudmesh.common.util import path_expand
from cloudmesh.common.util import readfile
from cloudmesh.common.util import str_banner
from yamldb.YamlDB import YamlDB

# from cloudmesh.common.variables import Variables
# from cloudmesh.configuration.Configuration import Configuration

Console.init()


def sysinfo():
    # this may already exist in common, if not it should be updated or integrated.

    """
    Returns value of system user from environment variables
    :return: User name
    """
    user = None
    if sys.platform == "win32":
        user = os.environ.get("USERNAME")
        hostname = os.environ.get("COMPUTERNAME")
    else:
        user = os.environ.get("USER")
        hostname = os.environ.get("HOSTNAME")
    cpus = multiprocessing.cpu_count()
    return user, hostname, cpus


def _to_string(obj, msg):
    result = [str_banner(msg)]
    for field in obj.__dataclass_fields__:
        try:
            value = getattr(obj, field)
            result.append(f"{field:<20}: {value}")
        except:
            pass
    return "\n".join(result) + "\n"


def _to_dict(obj):
    result = {}
    for field in obj.__dataclass_fields__:
        try:
            value = getattr(obj, field)
            result[str(field)] = value
        except:
            pass
    return result


@dataclass
class Job:
    """
    The Job class creates a simple job that can be executed asynchronously
    on a remote computer using ssh. The status of the job is managed through
    a number of files that can be quered to identify its execution state.

    I job can be created as follows

        job = Job(name=f"job1",
                  command="/usr/bin/sleep 120",
                  user="user",
                  host="host")

    it will create a n experiment directory where the job specification is
    located. To run it, it needs first to be syncronized and copied to the
    remote host.

        job.rsync()

    After this we can run it with

        job.run()

    Please note the the job runs asynchronously and you can probe its state with

        job.state

    Note this is a property and not a function for the user. The final
    state is called "end". Users can define their onw states and add them
    to the log file so custom actions could be called.

    To retrieve the CURRENT log file as a string you can use the functions

        job.get_log()

    To get the pid on the remote machine we can use

        job.pid

    Note that prior to running the command job.run(), the variable job.pid has
    the value None

    """
    name: str = "TBD"
    id: str = str(uuid.uuid4().hex)
    experiment: str = "experiment"
    directory: str = "./experiment"
    input: str = None
    output: str = None
    log: str = None
    status: str = "ready"
    gpu: str = ""
    arguments: str = ""
    executable: str = ""
    command: str = None
    shell: str = "bash"
    shell_path: str = None
    scriptname: str = None
    remote_command: str = None
    nohup_command: str = None  # BUG: should this just be remote command?
    #      we may not need to store the nohubcommand as it is
    #      just internal
    # placement
    pid: str = None
    host: str = None
    user: str = None

    def __post_init__(self):
        print(self.info())

        Console.ok(f"Creating: {self.name}")
        if self.input is None:
            self.input = f"{self.name}/input"
        if self.output is None:
            self.output = f"{self.name}.out"
        if self.log is None:
            self.log = f"{self.name}.log"
        if self.shell_path is None:
            self.shell_path = f"/usr/bin/{self.shell}"
        if self.command:
            self.set(self.command)

        self.scriptname = f"{self.experiment}/{self.name}/{self.name}.{self.shell}"
        self.generate_command()
        self.generate_script(shell=self.shell)

    def ps(self):
        keys = ["pid", "user", "ppid", "sz", "tty", "%cpu", "%mem", "cmd"]
        keys_str = ",".join(keys)
        command = f"ps --format {keys_str} {self.pid}"
        if not is_local(self.host):
            command = f"ssh {self.user}@{self.host} \"{command}\""
        try:
            lines = Shell.run(command).splitlines()
            lines = ' '.join(lines[1].split()).split(" ", len(keys) - 1)
            i = -1
            entry = {}
            for key in keys:
                i = i + 1
                entry[key] = lines[i]
            return entry
        except:
            return None

    @staticmethod
    def nohup(name=None, shell="bash"):
        """
        returns the nohup command for a remote machine

        :param name: name of the job
        :param shell: name of the shell
        :return: str
        """
        return f"nohup {shell} {name}.{shell} >> {name}-nohup.log 2>&1 &"

    def to_dict(self):
        """
        Returns a dict of the Job

        :return: dict
        """
        return _to_dict(self)

    def order(self):
        """
        returns all keys of the dict represented as dataclass
        :return:
        """
        return self.__dataclass_fields__

    def info(self, banner=None, output="table"):
        """
        Returns an information of the job

        :return: str
        """
        # BUG: see other info commands as banner is not defined
        return str(Printer.write(self, output=output))

    '''
    def info(self):
        """
        Returns an information string of the job

        :return: str
        """
        result = []
        keys = self.__dict__
        for key in keys:
            entry = f"{key} = {keys[key]}"
            result.append(entry)
        return "\n".join(result)
    '''

    def __str__(self):
        """
        Returns a string of the job

        :return: str
        """
        return _to_string(self, f"{self.experiment}/{self.name}/{self.name}")

    def example(self, name: str, user=None):
        """
        Not implemented

        :param name:
        :param user:
        :return:
        """
        user, hostname, cpus = sysinfo()
        self.name = name, hostname, cpus

    def set(self, command: str):
        """
        Sets the command

        :param str command: the command to be executed
        :return: None
        """
        self.command = command.strip()
        if " " in command:
            _command = shlex.split(command)
            self.executable = _command[0]
            self.arguments = " ".join(_command[1:])
        else:
            self.executable = self.command

    def generate_command(self):
        """
        Generates a command to run it remotely

        :return: None
        """
        self.nohup_command = self.nohup(name=self.name, shell=self.shell)
        if is_local(self.host):
            self.remote_command = \
                f"cd {self.directory}/{self.name}; " + \
                f"{self.nohup_command}"
        else:
            self.remote_command = \
                f"ssh {self.user}@{self.host} " + \
                f"\"cd {self.directory}/{self.name} ; " + \
                f"{self.nohup_command}\""

    def generate_script(self, shell="/usr/bin/bash"):
        """
        generates a job script that can be copied with sunc to the remote machine

        :param shell: name of the shell
        :return: None
        """
        os.system(f"mkdir -p {self.experiment}/{self.name}")
        with open(self.scriptname, "w") as f:
            start_line = self.logging("start", append=False)
            end_line = self.logging("end")
            script = "\n".join([
                f"#! {self.shell_path} -x",
                f"echo $$ > {self.name}.pid",
                f"rm -f {self.output}",
                f"rm -f {self.log}",
                f"{start_line}",
                f'echo -ne "# date: " >> {self.log}; date >> {self.log}',
                f"{self.command} >> {self.output}",
                f'echo -ne "# date: " >> {self.log}; date >> {self.log}',
                f"{end_line}",
                "#"])
            f.write(script)

    def logging(self, msg: str, append=True):
        if append:
            return f'echo "# cloudmesh state: {msg}" >> {self.name}.log'
        else:
            return f'echo "# cloudmesh state: {msg}" > {self.name}.log'

    @property
    def state(self):
        """
        returns the state of the remote job from the log file
        :return:
        """
        lines = self.get_process_file(self.log)

        if lines is not None:
            lines = lines.splitlines()

            result = Shell.find_lines_with(lines=lines, what="cloudmesh state:")
            if len(result) == 0:
                self.status = "unkown"
            else:
                self.status = result[-1].split(":", 1)[1].strip()
        else:
            self.status = "unkown"
        return self.status

    @property
    def rpid(self):
        """
        returns the remote pid from the job
        :return:
        """
        if self.pid is not None:
            return self.pid
        try:
            lines = self.get_process_file(f"{self.name}.pid")
        except:
            return None

        if lines is not None:
            self.pid = lines.strip()
        else:
            self.status = "no pid"
            return None
        return self.pid

    def get_process_file(self, name):
        """
        retrieves the contents of the named file in the experiment/job directory

        :param name: name of the file
        :return: content as string
        """
        found = False
        while not found:
            try:
                if is_local(self.host):
                    lines = readfile(f"{self.directory}/{self.name}/{name}")
                else:
                    lines = Shell.run(f"ssh {self.user}@{self.host} \"cat {self.directory}/{self.name}/{name}\"")
                found = True
            except:
                pass
        return lines

    def get_log(self):
        """
        Retrieves the log file form the host machine where the command is executed.

        @return: str
        """
        return self.get_process_file(self.log)

    def get_output(self):
        """
        Retrieves the output file form the host machine where the command is executed.

        @return: str
        """
        return self.get_process_file(self.output)

    def get_log_nohup(self):
        """
        Retrieves the nohup log file form the host machine where the command is executed.

        @return:
        """
        return self.get_process_file(f"{self.name}-nohup.log")

    def reset(self):
        """
        Not yet implementted

        @return: None
        """
        # delete log file
        try:
            os.remove(self.log)
        except:
            pass

    def sync(self, user: str, host: str):
        """
        sync the experiment directory with the host. Only sync if the host
        is not the localhost.

        @param str user: the user name
        @param str host: the host name or ip address

        @return: None
        """
        # only sync if host is not local
        if not is_local(host):
            command = f"rsync -r {self.experiment} {user}@{host}:{self.experiment}"
            os.system(command)

    def run(self):
        """
        run the script on the remote host
        """
        banner(f"Run: {self.name}")
        print("Command:", self.remote_command)
        r = os.system(self.remote_command)
        self.pid = self.rpid
        return self.pid

    def to_yaml(self):
        result = [f'{self.name}:']
        for argument in ["name", "id", "experiment", "directory", "input", "output",
                         "status", "gpu", "command", "shell", "pid", "host", "user"]:
            values = self.to_dict()
            result.append(f"  {argument}: {values[argument]}")
        return "\n".join(result)

    def load_from_yaml(self, content, with_key=True):
        """
        content is a string in yaml format
        """
        job_str = dedent(content).strip()
        data = yaml.safe_load(job_str)
        if with_key:
            name = list(data.keys())[0]
            data = data[name]
        new_job = Job(**data)
        self = new_job

    def kill(self):
        banner(f"Kill: {self.name}")

        if is_local(self.host):
            command = \
                f"cd {self.directory}/{self.name}; " + \
                f'kill -9 $(ps -o pid= --ppid {self.pid});' + \
                f'kill -9 {self.pid};' + \
                f"{self.logging(msg='kill')};"

        else:
            command = \
                f"ssh {self.user}@{self.host} " + \
                f"'" + \
                f"cd {self.directory}/{self.name}; " + \
                f'kill -9 "-$(ps -o pgid= {self.pid} | xargs)";' + \
                f"{self.logging(msg='kill')};" + \
                f"'"

        print("Command:", command)
        r = os.system(command)
        print(f"Return code was: {r}")
        self.status = "kill"
        return r


class Queue:

    def __init__(self,
                 name: str = "TBD",
                 experiment: str = None,
                 filename: str = None,
                 jobs: List = None):

        self.name = name
        self.experiment = experiment or "./experiment"
        self.filename = filename or f"{self.experiment}/{self.name}-queue.yaml"
        if not os.path.exists(self.experiment):
            os.makedirs(self.experiment)
        self.jobs = YamlDB(filename=self.filename)
        if jobs:
            self.add_jobs(jobs)

    def __len__(self):
        return len(self.jobs.data)

    def delete(self, name: str):
        """
        Deletes the job with the given name

        :param name: name of the job
        :return: Job
        """
        try:
            # check if job is running
            # if it is running kill job (not yet implemented in Job class to do)
            # finally delete from queue
            job = Job(**self.jobs[name])
            if job.state == 'start':
                job.kill()
            self.jobs.delete(name)
            self.save()
            return job
        except:
            Console.error(f"Could not delete job:{name}")

    def keys(self):
        return self.jobs.keys()

    def items(self):
        return self.jobs.__dict__["data"].items()

    def values(self):
        return self.jobs.__dict__["data"].values()

    def __getitem__(self, item):
        if type(item) == int:
            print(self.jobs.keys())
            key = list(self.jobs.keys())[item]
        else:
            key = str(item)
        data = self.get(key)
        return dict(data)
        # job = Job(data)
        # return job

    def get(self, name: str) -> dict:
        """
        Returns the job with the given name

        :param name: name of the job
        :return: dict of job
        """
        return self.jobs[name]

    def set(self, job: Job):
        """
        Overwrites the contents of the job. If the job
        does not exist, it will be updated.

        :param job: the job
        """
        self.jobs[job.name] = job.to_dict()

    def search(self, query):
        return self.jobs.search(query)

    def load(self, filename=None):
        filename = filename or self.filename
        self.jobs = YamlDB(filename=filename)

    def add_jobs(self, jobs):
        for job in jobs:
            self.jobs[job.name] = job.to_dict()
            self.save()

    def add(self, job: Job):
        self.jobs[job.name] = job.to_dict()
        self.save()

    def save(self):
        if len(self.jobs.data) > 0:
            self.jobs.save(self.filename)

    def info(self,
             kind="jobs",
             banner=None,
             output="table",
             job=None,
             order=None):

        if banner is not None:
            result = str_banner(banner)
        else:
            result = ""

        data = self.to_dict()
        if job is None:
            if order is None and kind in ["jobs"]:
                order = ["name", "status", "command", "gpu", "output", "log", "experiment"]
                result = result + str(Printer.write(data[kind], order=order, output=output))
            elif order is None and kind in ["queue", "config"]:
                order = ["name", "experiment", "filename"]
                kind = "config"
                data = {
                    data[kind]["name"]: data[kind]
                }
                result = result + str(Printer.write(data, order=order, output=output))
        else:
            job = self.__getitem__(job)
            result = result + str(Printer.attribute(job, output=output))
        return result

    def to_dict(self):
        result = {
            "config": {
                "name": self.name,
                "experiment": self.experiment,
                "filename": self.filename,
            },
            "jobs": {}
        }
        for job in self.jobs:
            result["jobs"][job] = self.jobs[job]
        return result

    def to_json(self, indent=2):
        return json.dumps(self.to_dict(), indent=indent)

    def to_yaml(self):
        return yaml.dump(self.to_dict())

    def __str__(self):
        result = self.to_dict()
        return str(result)


class SchedulerFIFO(Queue):

    def __init__(self,
                 name: str = "TBD",
                 experiment: str = None,
                 filename: str = None,
                 jobs: List = None):
        Queue.__init__(self,
                       name=name,
                       experiment=experiment,
                       filename=filename,
                       jobs=jobs)
        self.scheduler_N = len(self.jobs.data)
        self.scheduler_current_job = 0

    def __iter__(self):
        return self.jobs.__dict__["data"].items()

    def __next__(self):
        key = self.jobs.keys()[self.scheduler_current_job]
        result = self.jobs.data[key]
        self.scheduler_current_job += 1
        return result


@dataclass
class Host:
    user: str = sysinfo()[0]
    name: str = "localhost"
    ip: str = "127.0.0.1"
    status: str = "free"
    job_counter: int = 0
    max_jobs_allowed: int = 1
    cores: int = 1
    threads: int = 1
    gpus: str = ""
    probe_status: bool = False
    probe_time: str = None
    ping_status: bool = False
    ping_time: str = None

    # see also cloudmesh.common.Host.ping/check and so on. we can reuse that
    def ping(self):
        """
        Conducts a ping on the host and updates the probestatus
        :return: ping_status, datetime
        """
        now = datetime.now()
        result = commonHost.ping(hosts=[self.ip], count=4, processors=1)
        self.ping_status = result[0]['success']
        self.ping_time = now.strftime("%d/%m/%Y %H:%M:%S")
        return self.ping_status, self.ping_time

    def probe(self):
        """
        Executes a command on the host and updates the probe_status
        :return: probestatsu, datetime
        """
        raise NotImplementedError

    @staticmethod
    def sync(user, host, experiment):
        """
        Syncronizes the experiment directory to the given host on the user account

        :param user: Name of user
        :param host: Name of the host
        :param experiment: Directory tos syncronize
        :return:
        """

        if not is_local(host):
            if "/" not in experiment:
                experiment = f"./{experiment}"
            command = f"rsync -r {experiment}/* {user}@{host}:{experiment}"
            r = os.system(command)
        else:
            r = 0
        return r == 0

    def to_dict(self):
        """
        Returns a dict of the Job

        :return: dict
        """
        return _to_dict(self)

    def info(self,
             banner=None,
             output="table",
             order=None):

        order = order or ["name",
                          "status",
                          "ip",
                          "job_counter",
                          "max_jobs_allowed",
                          "cores",
                          "threads",
                          "gpus"]

        if banner is not None:
            result = str_banner(banner)
        else:
            result = ""

        data = self.to_dict()
        result = result + str(Printer.attribute(data, order=order, output=output))
        return result


@dataclass
class Cluster:

    def __init__(self,
                 name: str = "TBD",
                 experiment: str = None,
                 filename: str = None,
                 hosts: List = None):
        self.name = name
        self.experiment = experiment or "./experiment"
        self.filename = filename or f"{self.experiment}/{self.name}-cluster.yaml"
        if not os.path.exists(self.experiment):
            os.makedirs(self.experiment)
        self.hosts = YamlDB(filename=self.filename)
        if hosts:
            self.add_hosts(hosts)

    def __getitem__(self, item):
        if type(item) == int:
            print(self.hosts.keys())
            key = list(self.hosts.keys())[item]
        else:
            key = str(item)
        data = self.get(key)
        return data

    def __len__(self):
        return len(self.hosts.data)

    def delete(self, name: str):
        """
        Deletes the host with the given name

        :param name: name of the host
        """
        try:
            self.hosts.delete(name)
        except:
            pass

    def get(self, name: str) -> Host:
        """
        Returns the host with the given name

        :param name: name of the host
        :return: Host
        """
        return self.hosts[name]

    def set(self, host: Host):
        """
        Overwrites the contents of the host. If the host
        does not exist, it will be updated.

        :param host: the host
        """
        self.hosts[host.name] = host.to_dict()

    def search(self, query):
        return self.hosts.search(query)

    def load(self, filename=None):
        filename = filename or self.filename
        self.hosts = YamlDB(filename=filename)

    def add_hosts(self, hosts):
        for host in hosts:
            self.hosts[host.name] = host.to_dict()
            self.save()

    def add(self, host: Host):
        self.hosts[host.name] = host.to_dict()
        self.save()

    def save(self):
        if len(self.hosts.data) > 0:
            self.hosts.save(self.filename)

    def info(self,
             kind="hosts",
             banner=None,
             output="table",
             host=None,
             order=None):

        if banner is not None:
            result = str_banner(banner)
        else:
            result = ""

        data = self.to_dict()
        if host is None:
            if order is None and kind in ["hosts"]:
                # order = order
                result = result + str(Printer.write(data[kind], order=order, output=output))
            elif order is None and kind in ["cluster", "config"]:
                order = ["name", "experiment", "filename"]
                kind = "cluster"
                data = {
                    data[kind]["name"]: data[kind]
                }
                result = result + str(Printer.write(data, order=order, output=output))
        else:
            host = self.__getitem__(host)
            result = result + str(Printer.attribute(host, output=output))
        return result

    def to_dict(self):
        result = {
            "config": {
                "name": self.name,
                "experiment": self.experiment,
                "filename": self.filename,
            },
            "hosts": {}
        }
        for host in self.hosts:
            result["hosts"][host] = self.hosts[host]
        return result

    def to_json(self, indent=2):
        return json.dumps(self.to_dict(), indent=indent)

    def to_yaml(self):
        return yaml.dump(self.to_dict())

    def __str__(self):
        result = self.to_dict()
        return str(result)

    def activate(self, name: str, status: bool = True):
        """
        Activates the host. A host can be disabled with the status set to False.
        Only acive hosts are used.

        This function is important if we find out that a host may not be available
        during long running jobs.

        :param name: Name of the host to activate or deactivate
        :param status: If True the host is active
        """
        if status:
            self.hosts.data[name]["status"] = "active"
        else:
            self.hosts.data[name]["status"] = "inactive"

    def add_policy(self, policy):
        """
        Adds a sceduling policy to select the next available host for scheduling a job.

        :param policy:
        :return:
        """
        pass

    def ping(self, parallelism=1):
        """
        Sends a ping to all hosts that are mared with
        status==active and identifies if they are reachable
        with ping. Each host will be marked with the last time
        the ping was conducted and the result of the ping.

        Please note that cloudmesh.common has a build in
        function for that. So in principal this is already
        implemented.

        see also cloudmesh.common.Host.ping/check and so on. we can reuse that

        :param parallelism:
        :return:
        """

    def probe(self, parallelism=1):
        """

        :param parallelism:
        :return:
        """

    '''
    move this to cluster and fix with yamldb

    def save(self, filename):
        """
        Saves the host specification to a file

        :param filename: The filename
        """
        try:
            host_spec = dedent(
                f"""
                {self.name}:
                    name: {self.name}  
                    user:  {self.user}
                    ip: {self.ip}
                    status: {self.status}
                    job_counter: {self.job_counter}
                    max_jobs_allowed: {self.max_jobs_allowed}
                    cores: {self.cores}
                    threads: {self.threads}
                    gpus: {self.gpus}
                """
            ).strip()
            specification = yaml.safe_load(host_spec)

            config = Configuration(filename)
            config["cloudmesh.jobset.hosts"].update(specification)
            config.save(filename)
        except Exception as e:
            Console.error(f"Host {self.name} could not be added- {e}")
            return ""

    def delete_host(self, config_file):
        """
        Deletes the host from the configuration file

        :param config_file:
        :return:
        """
        spec = Configuration(config_file)

        try:
            job_counter = int(spec[f"cloudmesh.jobset.hosts.{self.name}.job_counter"])
        except Exception as e:
            job_counter = 0

        try:
            if job_counter > 0:
                Console.error(
                    f"Host {self.name} is running {job_counter} jobs. "
                    "Please kill those jobs before deleting this Host.")

            del spec["cloudmesh.jobset.hosts"][self.name]

            spec.save(config_file)

        except KeyError:
            Console.error(f"Host '{self.name}' not found in jobset.")

        except Exception as e:
            Console.error(
                f"Job {self.name} could not be deleted. Please check. Error- {e}"
            )

    def __str__(self):
        return _to_string(self, f"{self.user}@{self.name}")
    '''
