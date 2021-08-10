import multiprocessing
import os
from posixpath import basename
import random
import sys
import time
from pathlib import Path
from textwrap import dedent
from typing import List
import shlex

import oyaml as yaml
from cloudmesh.common.Shell import Shell
from cloudmesh.common.util import banner
from cloudmesh.common.util import str_banner
from cloudmesh.common.Printer import Printer
from cloudmesh.common.Shell import Shell
from cloudmesh.common.console import Console
from cloudmesh.common.parameter import Parameter
from cloudmesh.common.util import path_expand
from cloudmesh.common.variables import Variables
from cloudmesh.configuration.Configuration import Configuration
from cloudmesh.common.debug import VERBOSE
from yamldb import YamlDB
from dataclasses import dataclass
from cloudmesh.common.util import readfile

Console.init()

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
    user: str = "TBD"
    name: str = "TBD"
    ip: str = "127.0.0.1"
    status: str = "free"
    job_counter: int = 0
    max_jobs_allowed: int = 1
    cores: int = 1
    threads: int = 1
    gpus: str = ""

    def info(self, output="print"):
        print(self)

    def __str__(self):
        return _to_string(self, f"{self.user}@{self.name}")

@dataclass
class Job:
    name: str = "TBD"
    experiment: str = "./experiment"
    directory: str = "."
    input: str = None # "./experiment/data"
    output: str = None # "./experiment/output"
    log: str = None # "./experiment/log"
    status: str = "ready"
    gpu: str = ""
    user: str = ""
    arguments: str = ""
    executable: str = ""
    command: str = ""
    shell: str = "bash"

    def to_dict(self):
        return _to_dict(self)

    def order (self):
        return self.__dataclass_fields__

    def __post_init__(self):
        Console.ok(f"Creating: {self.name}")
        if self.input is None:
            self.input = f"{self.experiment}/{self.name}/input"
        if self.output is None:
            self.output = f"{self.experiment}/{self.name}.output"
        if self.log is None:
            self.log = f"{self.experiment}/{self.name}.log"

    @property
    def scriptname(self):
        return f"{self.experiment}/{self.name}-script.{self.shell}"

    def info(self, output="print"):
        print (self)

    def __str__(self):
        return _to_string(self, f"{self.experiment}/{self.name}")

    def example(self, name: str, user=None):
        user, hostname, cpus = sysinfo()
        self.name = name, hostname, cpus

    def set(self, command: str):
        self.command = command
        _command = shlex.split(command)
        if " " in command:
            self.executable = _command[0]
            self.arguments = _command [1:]
        else:
            self.executable = self.command[0]

    def generate_script(self):
        os.system(f"mkdir -p {self.experiment}")
        shell = Shell.which(self.shell)
        with open(self.scriptname, "w") as f:
            start_line = self.logging("start")
            end_line = self.logging("end")
            script = "\n".join([
                f"#! {shell}",
                f"mkdir -p  {self.experiment}",
                f"rm -f {self.output}",
                f"rm -f {self.log}",
                f"{start_line}",
                f"{self.command} >> {self.output}",
                f"{end_line}",
                "#"])
            f.write(script)

    def logging(self, msg: str):
        return f'echo "# cloudmesh state: {msg}" >> {self.log}'

    @property
    def state(self):
        lines = readfile(self.log).splitlines()
        result = Shell.find_lines_with(lines=lines, what="# cloudmesh state:")
        if lines is None:
            status = "not ready"
        else:
            status = lines[-1:][0].split(":", 1)[1].strip()
        self.status = status
        return status

    def reset(self):
        # delete log file
        try:
            os.remove(self.log)
        except:
            pass

@dataclass
class Queue:
    name : str =  "TBD"
    experiment : str = "./experiment"
    jobs = []

    @property
    def queuefilename(self):
        return f"{self.experiment}/{self.name}-queue.yaml"

    def to_list(self):
        data = []
        for job in self.jobs:
            entry = job.to_dict()
            data.append(entry)
        return data

    def save(self):
        queue = {
            "name": self.name,
            "experiment": self.experiment,
            "jobs": self.to_list()
        }
        with open(self.queuefilename, 'w') as file:
            result = yaml.dump(queue, file)

    def load(self):
        with open(self.queuefilename, 'r') as file:
            result = yaml.load(file, Loader=yaml.SafeLoader)
        self.name = result["name"]
        self.experiment = result["experiment"]


    def add(self, job: Job):
        self.jobs.append(job)
        self.save()

    def delete(self, name: str):
        pass

    def info(self, output="print", order=["name", "status", "command", "gpu", "output", "log", "experiment"]):
        banner(f"Queue: {self.name}")

        data = self.to_list()
        print(Printer.write(data, order=order))


    def add_policy(self, policy):
        pass

    def __str__(self):
        return _to_string(self, f"{self.experiment}/{self.name}")



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


class Database:

    def __init__(self, filename=None):
        pass

    def load(self):
        pass

    def save(self, data):
        pass

    """
    Not yet sure if we do it this way or if load safe is part of cluster, jobs, and hosts
    def load_jobs(self):
        pass

    def save_jobs(self, jobs):
        pass

    def load_hosts(self):
        pass

    def save_hosts(self, hosts):
        pass
    """


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
        specification = dedent(
            f"""
              {name}:
                name: {name}  
                directory: .
                ip: 127.0.0.1
                input: .
                output: .
                status: ready
                gpu: "" 
                user:  {user}
                arguments:  -lisa
                executable: ls
                shell: bash
              """
        ).strip()

        specification = yaml.safe_load(specification)

        return specification

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

        template = dedent(
            f"""
            cloudmesh:
              default:
                user: {user}
              jobset:
                hosts:
                  localhost:
                    user: {user}
                    name: {self.name}
                    ip: 127.0.0.1
                    status: free
                    job_counter: 0
                    max_jobs_allowed: 1
                    cores: 1
                    threads: 1
                    gpus: None
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
        # VERBOSE(spec['jobs'])

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
        
        _spec = {
            "name": arguments.get("names")[idx],
            "directory": arguments.get("directory") or ".",
            "ip": arguments.get("ip_list")[idx] or "localhost",
            "input": arguments.get("input_list")[idx] or "./data",
            "output": arguments.get("output_list")[idx] or "./output",
            "status": arguments.get("status") or "ready",
            "gpu": arguments.get("gpu_list")[idx] or "",
            "user": arguments.get("user") or jobqueue.user,
            "arguments": arguments.get("arguments_list")[idx] or "",
            "executable": arguments.get("executable"),
            "shell": arguments.get("shell") or "bash",
        }
        return _spec

    def update_spec(self, specification, jobset=None):
        """
        Adds new jobs to the jobset. New job list taken from input file or a
        dictionary.
        :param specification: dictionary with all arguments
        :param jobset: jobset file name
        :return: None, adds jobs from specifications into the jobset
        """
        # Remove hardcoded sepc.yaml  s/b instance property self.filename
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
        config = Configuration(self.filename)

        tag = arguments.hostname
        config[f"cloudmesh.jobset.hosts.{tag}.name"] = (
                arguments.hostname or "localhost"
        )
        config[f"cloudmesh.jobset.hosts.{tag}.ip"] = arguments.ip or "localhost"
        config[f"cloudmesh.jobset.hosts.{tag}.cpus"] = (
                arguments.cpus or "0"
        )
        config[f"cloudmesh.jobset.hosts.{tag}.gpus"] = (
                arguments.gpus or "0"
        )
        config[f"cloudmesh.jobset.hosts.{tag}.status"] = (
                arguments.status or "free"
        )
        config[f"cloudmesh.jobset.hosts.{tag}.job_counter"] = (
                arguments.job_counter or "0"
        )
        config[f"cloudmesh.jobset.hosts.{tag}.max_jobs_allowed"] = (
                arguments.max_jobs_allowed or "1"
        )

        Console.ok(f"Host {arguments.hostname} added to jobset.")

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
        result = Printer.write(config["cloudmesh.jobset.hosts"], order=order, 
                               output=format)
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
                            f"sh -c 'echo \$\$ > {v['output']}/{k}_pid.log;"
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
                            f'kill -9 \$(cat {k}_pid.log)"'
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
                    f"Job {name} could not be deleted. Please check. Error-", e
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
            "ip",
            "input",
            "output",
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
            "IP",
            "Input",
            "Output",
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
