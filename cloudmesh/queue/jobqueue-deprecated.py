import json
import multiprocessing
import os
import platform
import random
import shlex
import socket
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import List

import oyaml as yaml
from cloudmesh.common.Printer import Printer
from cloudmesh.common.Shell import Shell
from cloudmesh.common.console import Console
from cloudmesh.common.parameter import Parameter
from cloudmesh.common.util import banner
from cloudmesh.common.util import path_expand
from cloudmesh.common.util import readfile
from cloudmesh.common.util import str_banner
from cloudmesh.common.variables import Variables
from cloudmesh.configuration.Configuration import Configuration

from yamldb.YamlDB import YamlDB

Console.init()


def is_local(host):
    return host in ["127.0.0.1",
                    "localhost",
                    socket.gethostname(),
                    # just in case socket.gethostname() does not work  we also try the following:
                    platform.node(),
                    socket.gethostbyaddr(socket.gethostname())[0]
                    ]


def sysinfo():
    # this may alredy axist in common, if not it should be updated or integrated.

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

    @staticmethod
    def sync(user, host, experiment):

        if not is_local(host):
            if "/" not in experiment:
                experiment = f"./{experiment}"
            command = f"rsync -r {experiment}/* {user}@{host}:{experiment}"
            r = os.system(command)
        else:
            r = 0
        return r == 0

    def info(self, output="print"):
        print(self)

    def to_dict(self):
        return _to_dict(self)

    def save(self, config_file):
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

            config = Configuration(config_file)
            config["cloudmesh.jobset.hosts"].update(specification)
            config.save(config_file)
        except Exception as e:
            Console.error(f"Host {self.name} could not be added- {e}")
            return ""

    def delete_host(self, config_file):
        spec = Configuration(config_file)

        try:
            job_counter = int(spec[f"cloudmesh.jobset.hosts.{self.name}.job_counter"])
        except Exception as e:
            job_counter = 0

        try:
            if job_counter > 0:
                Console.error(
                    f"Host {self.name} is running {job_counter} jobs. Please kill those jobs before deleting this Host.")

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
        result = []
        result.append(f'{self.name}:')
        for argument in ["name", "id", "experiment", "directory", "input", "output",
                         "status", "gpu", "command", "shell", "pid", "host", "user"]:
            values = self.to_dict()
            result.append(f"  {argument}: {values[argument]}")
        return ("\n".join(result))

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

    def delete(self, name: str) -> Job:
        """
        Returns the job with the given name

        :param name: name of the job
        :return: Job
        """
        try:
            # check if job is running
            # if it is running kill job (not yet implemented in Job class to do)
            # finally delete from queue
            self.jobs.delete(name)
        except:
            pass

    def get(self, name: str) -> Job:
        """
        Returns the job with the given name

        :param name: name of the job
        :return: Job
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
        print ("LLL", self.jobs)
        if len(self.jobs.data) > 0:
            self.jobs.save(self.filename)

    def delete(self, name: str):
        self.jobs.delete(name)

    def info(self,
             output="print",
             order=["name", "status", "command", "gpu", "output", "log", "experiment"]):
        banner(f"Queue: {self.name}")

        data = self.to_list()
        print(Printer.write(data, order=order))

    def add_policy(self, policy):
        pass

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


@dataclass
class Cluster:
    hosts: List[Host]

    def add_host(self, host: Host):
        pass

    def remove_host(self, name: str):
        pass

    def disable_host(self, name: str):
        pass

    def enable_host(self, name: str):
        pass

    def add_policy(self, policy):
        pass

    def info(self, output="table"):
        for host in self.hosts:
            data = host.info(output=output)
            print(data)


class JobQueue:
    """
    To create, manage and monitor job execution queue
    """

    def __init__(self, filename=None):
        """

        @param filename:
        """
        # TOD: evaluate if jobset should be nem for the variable?
        self.hostname = None
        self.user = None
        variables = Variables()
        self.filename = filename or variables["jobset"] or path_expand("~/.cloudmesh/job/spec.yaml")
        self.name, self.directory, self.basename = self.location(self.filename)
        if self.directory != "":
            Shell.mkdir(self.directory)
        self._sysinfo()

    def location(self, filename):
        """
        Returns name, directory and extension of a file
        :param filename: File name
        :return: file name, extension and file location
        """
        try:
            self.directory = os.path.dirname(filename)
        except:
            self.directory = ""

        self.basename = os.path.basename(filename)
        self.name = self.basename.split(".")[0]

        return self.name, self.directory, self.basename

    def _sysinfo(self):
        """
        Returns value of system user from environment variables
        :return: User name
        """
        self.user = None
        if sys.platform == "win32":
            self.user = os.environ.get("USERNAME")
            self.hostname = os.environ.get("COMPUTERNAME")
        else:
            self.user = os.environ.get("USER")
            self.hostname = os.environ.get("HOSTNAME")
        self.cpus = multiprocessing.cpu_count()

    def template(self, name=None, user=None):
        """
        Creates a standard template of a job to be added in jobset
        :param name: Name of the job
        :return: Dictionary object of the job to be added in the jobset
        """
        if user is None:
            user = self.user
        name = name or "job"

        job = Job(name=name, user=user)
        spec = job.to_dict()

        return {f"{name}": spec}

    def add_template(self, specification):
        """
        Adds template in the jobset
        :param specification: dictionary containing jobset configuration
        :return: None, creates sample jobset
        """
        user = self.user

        if type(specification) != dict:
            Console.error("only specify a yaml dict")

        jobset = Path.expanduser(Path(self.filename))
        Path.mkdir(jobset.parent, exist_ok=True)

        default_host = Host()
        host_spec = default_host.to_dict()

        template = dedent(
            f"""
            cloudmesh:
              default:
                user: {user}
              jobset:
                hosts:
                  {default_host.name}:
                    {host_spec}
                scheduler:
                  policy: sequential
            """
        ).strip()

        template = yaml.safe_load(template)
        template["cloudmesh"]["jobset"].update({"jobs": specification})

        # VERBOSE(template)

        with open(jobset, "w") as fo:
            yaml.safe_dump(template, fo)

    def add(self, specification):
        """
        Adds jobs in the jobset
        :param specification: dictionary containing details of the jobs
        :return: None, appends the job in jobset
        """
        if type(specification) != dict:
            Console.error("only specify a yaml dict")

        jobset = Path.expanduser(Path(self.filename))
        Path.mkdir(jobset.parent, exist_ok=True)

        spec = Configuration(self.filename)

        spec["cloudmesh.jobset.jobs"].update(specification)
        # VERBOSE(spec)

        spec.save(self.filename)

    @staticmethod
    def define(arguments, idx):
        """
        Creates a dictionary object for individual jobs
        :param arguments: dictionary with job arguments
        :param idx: index of the job to be processed
        :return: dictionary for individual jobs
        """

        jobqueue = JobQueue()
        default = Job()

        job = Job(
            name=arguments.get("names")[idx],
            experiment=arguments.experiment or default.experiment,
            directory=arguments.directory or default.directory,
            input=arguments.input_list[idx] or default.input,
            output=arguments.output_list[idx] or default.output,
            log=arguments.log or default.log,
            status=arguments.status or default.status,
            gpu=arguments.gpu_list[idx] or default.gpu,
            user=arguments.user or jobqueue.user,
            command=arguments.command or default.command,
            shell=arguments.shell or default.shell,
        )

        _spec = job.to_dict()

        return _spec

    def update_spec(self, specification, jobset=None):
        """
        Adds new jobs to the jobset. New job list taken from input file or a
        dictionary.
        :param specification: dictionary with all arguments
        :param jobset: jobset file name
        :return: None, adds jobs from specifications into the jobset
        """
        jobset = jobset or self.filename
        jobset = path_expand(jobset)

        dict_out = dict()

        for idx in range(len(specification["names"])):
            dict_out[specification["names"][idx]] = JobQueue.define(
                specification, idx
            )

        # VERBOSE(dict_out)

        self.add(dict_out)

    @staticmethod
    def expand_args(arg1, arg2, arguments):
        """
        Method expands arg2 and compares its length with len(arg1)
        :param arg1: Argument indicating number of jobs involved, eg. 'names'
        :param arg2: Argument to be expanded, eg 'ip'
        :param arguments: dictionary containing arg1 and arg2
        :return: array of expanded arg2
        """

        arguments["arg2_expanded"] = Parameter.expand(arguments[arg2])

        if len(arguments[arg1]) == 1 and len(arguments["arg2_expanded"]) == 1:
            pass
        elif len(arguments[arg1]) > 1 and len(arguments["arg2_expanded"]) == 1:
            arguments["arg2_expanded"] = [arguments[arg2]] * len(
                arguments[arg1]
            )
        elif len(arguments[arg1]) != len(arguments["arg2_expanded"]):
            Console.error(f"Number of {arg2} must match number of {arg1}")
            return ""

        return arguments["arg2_expanded"]

    def addhost(self, arguments):
        """
        Adds a new host in jobset yaml file
        :param arguments: dictionary containing host info
        :return: updates the jobset with host info
        """
        default = Host()

        new_host = Host(
            user=arguments.host_username or default.user,
            name=arguments.hostname or default.name,
            ip=arguments.ip or default.ip,
            status=arguments.status or default.status,
            job_counter=arguments.job_counter or default.job_counter,
            max_jobs_allowed=arguments.max_jobs_allowed or default.max_jobs_allowed,
            cores=arguments.cores or default.cores,
            threads=arguments.threads or default.threads,
            gpus=arguments.gpus or default.gpus
        )

        new_host.save(config_file=self.filename)

        Console.ok(f"Host {arguments.hostname} added to jobset.")

    def delete_host(self, host_name):
        """
        Deletes a host sepc from config

        Args:
            host_name (str): Host name to delete
            config_file (str): Config file
        """
        host = Host(name=host_name)
        host.delete_host(config_file=self.filename)

        Console.ok(f"Host {host_name} is removed from jobset.")

    def print_hosts(self, format='table'):
        """
        Lists all hosts configured in jobset
        :return: list of hosts
        """
        config = Configuration(self.filename)
        order = [
            "name",
            "user",
            "ip",
            "status",
            "job_counter",
            "max_jobs_allowed",
            "gpus",
            "cores",
            "threads"
        ]
        result = Printer.write(config["cloudmesh.jobset.hosts"], order=order, output=format)

        return result

    @staticmethod
    def _get_hostname(ip, spec):
        """
        Returns hostname for given host ip
        :param ip: host ip
        :param spec: jobset dictionary
        :return: hostname
        """
        for k, v in spec["cloudmesh.jobset.hosts"].items():
            if v["ip"] == ip:
                return k

    @staticmethod
    def get_available_ip(ip, spec):
        """
        Finds out host IP which is available for processing the job. If the
        host configured in jobs section is not available then this method
        refers to the scheduler.policy to decide which host to use.

        :param ip: IP configured in jobset in the job section
        :param spec: jobset dictionary
        :return: IP of available host
        """
        p = Policy(ip, spec)
        available_ip = p.get_ip()

        if ip != available_ip:
            Console.info(
                f"Host {ip} is unavailable, hence submitted the job "
                f"on available host {available_ip}"
            )
        return available_ip

    def run_job(self, names=None):
        """
        To run the job on remote machine
        :param names: job names
        :return: job is submitted to the host
        """
        spec = Configuration(self.filename)
        submitted = {}

        if names is None:
            names = spec["cloudmesh.jobset.jobs"].keys()

        for k, v in spec["cloudmesh.jobset.jobs"].items():

            if k in names:

                ip = JobQueue.get_available_ip(v["ip"], spec)

                if ip is not None:

                    if v["status"] == "ready":
                        command = (
                            f"ssh {v['user']}@{ip} "
                            f"\"cd {v['directory']};"
                            f"sh -c 'echo $$ > {v['output']}/{k}_pid.log;"
                            f"exec {v['executable']} {v['arguments']}'\""
                        )
                        # VERBOSE(command)

                        Console.info(f"INFO: Submitting {k} to {v['ip']}:")
                        Shell.terminal(command, title=f"Running {k}")
                        time.sleep(5)

                        spec[f"cloudmesh.jobset.jobs.{k}.status"] = "submitted"
                        spec[f"cloudmesh.jobset.jobs.{k}.submitted_to_ip"] = ip
                        hname = JobQueue._get_hostname(ip, spec)
                        ctr = int(
                            spec[f"cloudmesh.jobset.hosts.{hname}.job_counter"]
                        )
                        spec[f"cloudmesh.jobset.hosts.{hname}.job_counter"] = str(
                            ctr + 1
                        )

                        submitted[k] = {
                            "name": v['name'],
                            "user": v['user'],
                            "ip": v['ip'],
                            "submitted_to_ip": ip,
                            "status": 'submitted',
                            "executable": v['executable'],
                            "arguments": v['arguments'],
                            "execution_root": v['directory'],
                            "pid_location": f"{v['output']}/{k}_pid.log",
                        }
                    else:
                        Console.info(
                            f"Job skipped: The job {k} is not ready."
                            f"Current status is {v['status']}."
                        )
                        submitted[k] = {
                            "name": v['name'],
                            "user": v['user'],
                            "ip": v['ip'],
                            "status": 'skipped',
                            "previous_status": v['status'],
                            "executable": v['executable'],
                            "arguments": v['arguments'],
                        }
                else:
                    Console.error(
                        f"Job {k} could not be submitted due to "
                        f"missing host with ip {ip}"
                    )
                    submitted[k] = {
                        "name": v['name'],
                        "user": v['user'],
                        "ip": v['ip'],
                        "status": 'error in submission',
                        "executable": v['executable'],
                        "arguments": v['arguments'],
                    }
                    return submitted

        return submitted

    def kill_job(self, names=None):
        """
        To kill the job on remote machine
        :param names: job names
        :return: job is killed on the host
        """
        spec = Configuration(self.filename)
        killed = {}

        if names is None:
            names = spec["cloudmesh.jobset.jobs"].keys()

        for k, v in spec["cloudmesh.jobset.jobs"].items():

            if k in names:

                if v["status"] == "submitted":

                    ip = v.get("submitted_to_ip")

                    if ip is not None:

                        command = (
                            f"ssh {v['user']}@{ip} "
                            f"\"cd {v['output']};"
                            f'kill -9 $(cat {k}_pid.log)"'
                        )

                        # VERBOSE(command)

                        Shell.terminal(command, title=f"Running {k}")
                        # time.sleep(5)

                        spec[f"cloudmesh.jobset.jobs.{k}.status"] = "killed"
                        hname = JobQueue._get_hostname(ip, spec)
                        ctr = int(
                            spec[f"cloudmesh.jobset.hosts.{hname}.job_counter"]
                        )
                        spec[f"cloudmesh.jobset.hosts.{hname}.job_counter"] = str(
                            ctr - 1
                        )

                        killed[k] = {
                            "name": v['name'],
                            "user": v['user'],
                            "ip": v['ip'],
                            "status": 'killed',
                            "executable": v['executable'],
                            "arguments": v['arguments'],
                        }
                    else:
                        Console.error(
                            f"Job {k} could not be killed due to "
                            f"missing host with ip {ip}"
                        )
                        return ""

        return killed

    def delete_job(self, names=None):
        """
        Deletes a job from jobset. If the job is already submitted for
        execution then it is killed first and then deleted from jobset.
        :param names: list of names of jobs to be deleted
        :return: updates jobset
        """
        spec = Configuration(self.filename)

        if names is None:
            names = spec["cloudmesh.jobset.jobs"].keys()

        for name in names:

            try:
                if spec[f"cloudmesh.jobset.jobs.{name}.status"] == "submitted":
                    self.kill_job([name])

                del spec["cloudmesh.jobset.jobs"][name]

                spec.save(self.filename)

            except KeyError:
                Console.error(f"Job '{name}' not found in jobset. ")
            except Exception as e:
                Console.error(
                    f"Job {name} could not be deleted. Please check. Error- {e}"
                )

    def get_policy(self):
        """
        Returns scheduler policy name from jobset
        :return: policy name
        """
        config = Configuration(self.filename)
        return config["cloudmesh.jobset.scheduler.policy"]

    def update_policy(self, policy):
        """
        Updates the scheduler policy name
        :return: None
        """
        valid_policies = ["sequential", "smart", "frugal", "random"]

        if policy in valid_policies:
            config = Configuration(self.filename)
            old_policy = config["cloudmesh.jobset.scheduler.policy"]
            config["cloudmesh.jobset.scheduler.policy"] = policy

            Console.info(
                f"Scheduler policy changed from {old_policy} to " f"{policy}"
            )
        else:
            Console.error(
                f"Scheduler policy {policy} is not configured."
                f"Available options are {','.join(valid_policies)}."
            )
            return ""

    def print_jobs(self, filter_name=None, filter_value=None,
                   sort_var=None, format='table'):
        """
        Lists all jobs from the jobset. Applies filter based on the
        filter_value and filter_name. Sorting of output is done on sort_var,
        or by default on job order in the jobset.
        :param filter_name: Element name to apply filter on
        :param filter_value: Value of the element to be filtered in
        :param sort_var: Element name to sort the output on
        :param format: Format of the output, table/csv/json/html
        :return: Prints a table with job list
        """
        spec = Configuration(self.filename)
        jobs = spec["cloudmesh.jobset.jobs"]

        for k, entry in jobs.items():
            if entry.get("status") is None:
                entry["status"] = "Unavailable"

        if filter_name is None:
            result = jobs
        else:
            result = []
            for k, entry in jobs.items():
                # Applying partial match
                if filter_value in entry[filter_name]:
                    result.append(entry)

        order = [
            "name",
            "directory",
            "experiment",
            "input",
            "output",
            "log",
            "status",
            "gpu",
            "arguments",
            "executable",
            "shell",
            "user"
        ]
        header = [
            "Name",
            "Directory",
            "Experiment",
            "Input",
            "Output",
            "Log",
            "Status",
            "GPU",
            "Arguments",
            "Executable",
            "Shell",
            "User"
        ]
        out = Printer.write(result, order=order,
                            sort_keys=sort_var, output=format)
        return out

    def show_list(self, jobs=True, hosts=True, format='table'):
        """
        Method shows list of jobs and/or hosts from the config file.

        Args:
            jobs (bool, optional): To show jod list. Defaults to True.
            hosts (bool, optional): To show host list. Defaults to True.
            format (str, optional): Output format. Defaults to 'table'.

        Returns:
            string: Returns the list in the format defined by format.
        """
        if hosts:
            banner("Hosts")
            print(self.print_hosts(format=format))

        if jobs:
            banner("Jobs")
            print(self.print_jobs(format=format))

    def set_attribute(self, config, name, attribute, value):
        """
        Sets given value for the attribute
        Args:
            config (str): Config type, jobs or hosts
            name (str): Job/Host name
            attribute (str): Attribute
            value (Any): Value of the attribute

        Returns:
            [None]: Updates the value.
        """
        spec = Configuration(self.filename)
        config_types = spec["cloudmesh.jobset"].keys()

        if config not in config_types:
            Console.error(f"Config type {config} is not implemented in config file {self.filename}")

        try:
            spec[f"cloudmesh.jobset.{config}.{name}.{attribute}"] = value
        except KeyError:
            Console.error(f"Attribute {attribute} is not found in config file {self.filename}")
        except Exception as e:
            Console.error(f"Could not set {attribute} to {value}: {e}")


class Policy:
    """
    Class returns available host IP based on the scheduler policy
    """

    def __init__(self, ip, spec):
        """
        Instantiate the class and fetch scheduler.policy, available IPs
        :param spec: Content of jobset
        :param ip: IP of the host configured for the job
        """
        self.ip = ip
        self.spec = spec

        self.host_data = self.spec["cloudmesh.jobset.hosts"]
        self.policy = self.spec["cloudmesh.jobset.scheduler.policy"]
        self.availability = dict()

        for k, v in self.host_data.items():
            # available = int(v["cpus"]) - int(v["job_counter"])
            available = int(v["max_jobs_allowed"]) - int(v["job_counter"])
            if available > 0:
                self.availability[v["ip"]] = available

        # VERBOSE(self.availability)

    def get_ip(self):
        """
        Method to return available IP. If any new scheduler policy is
        configured, then this method should be coded accordingly.

            Configured Scheduler policies:
             sequential - Use first available host
             random     - Use random available host
             smart      - Use a host with highest availability
             frugal     - Use a host with least availability

        :return: IP of available host
        """
        if self.availability.get(self.ip):
            return self.ip
        else:
            if self.policy == "sequential":
                return list(self.availability.keys())[0]
            elif self.policy == "random":
                return random.choice(list(self.availability))
            elif self.policy == "smart":
                d = sorted(
                    self.availability,
                    key=lambda x: self.availability[x],
                    reverse=True,
                )
                return d[0]
            elif self.policy == "frugal":
                d = sorted(
                    self.availability,
                    key=lambda x: self.availability[x],
                    reverse=False,
                )
                return d[0]
            else:
                Console.error(
                    f"Scheduler policy {self.policy} is not "
                    f"configured. Available options are sequential, "
                    f"random, smart, frugal."
                )
                return None
