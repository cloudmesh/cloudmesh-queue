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


def _to_string(obj, msg):
    result = [str_banner(msg)]
    for field in obj.__dataclass_fields__:
        try:
            value = getattr(obj, field)
            result.append(f"{field:<20}: {value}")
        except:
            pass
    return "\n".join(result) + "\n"


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
