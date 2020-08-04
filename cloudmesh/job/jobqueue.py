from pathlib import Path
import os, time, sys, multiprocessing, random
import oyaml as yaml
from cloudmesh.common.Shell import Shell
from cloudmesh.configuration.Config import Config
from cloudmesh.configuration.Configuration import Configuration
from cloudmesh.common.console import Console
import subprocess
from cloudmesh.common.util import path_expand
from cloudmesh.common.variables import Variables
from cloudmesh.common.Shell import Shell
from textwrap import dedent
from cloudmesh.common.parameter import Parameter
from cloudmesh.common.debug import VERBOSE
from cloudmesh.common.Printer import Printer


class JobQueue:
    """
    To create, manage and monitor job execution queue
    """

    def __init__(self, filename=None):
        variables = Variables()
        self.filename = filename or \
                        variables["jobset"] or \
                        path_expand("~/.cloudmesh/job/spec.yaml")
        self.name, \
        self.directory, \
        self.basename = \
            JobQueue.location(self.filename)
        if self.directory != "":
            Shell.mkdir(self.directory)

    @staticmethod
    def location(filename):
        """
        Returns name, directory and extension of a file
        :param filename: File name
        :return: file name, extension and file location
        """
        try:
            _directory = os.path.dirname(filename)
        except:
            _directory = ""
        _basename = os.path.basename(filename)
        _name = _basename.split(".")[0]
        return _name, _directory, _basename

    @staticmethod
    def _user():
        """
        Returns value of system user from environment variables
        :return: User name
        """
        user = None
        if sys.platform == 'win32':
            user = os.environ.get('USERNAME')
            hostname = os.environ.get('COMPUTERNAME')
        else:
            user = os.environ.get('USER')
            hostname = os.environ.get('HOSTNAME')
        return user

    @staticmethod
    def _sysinfo():
        """
        Returns value of system hostname and cpu count from environment
        variables. This is working on local machine and populated in template
        only.
        :return: hostname and max cpu_count
        """
        hostname = None
        if sys.platform == 'win32':
            hostname = os.environ.get('COMPUTERNAME')
        else:
            hostname = os.environ.get('HOSTNAME')
        cpu_count = multiprocessing.cpu_count()

        return hostname, cpu_count

    def template(self, name=None):
        """
        Creates a standard template of a job to be added in jobset
        :param name: Name of the job
        :return: Dictionary object of the job to be added in the jobset
        """
        user = JobQueue._user()
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
              """).strip()

        specification = yaml.safe_load(specification)

        return specification

    def add_template(self, specification):
        """
        Adds template in the jobset
        :param specification: dictionary containing jobset configuration
        :return: None, creates sample jobset
        """
        user = JobQueue._user()

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
                    name: {JobQueue._sysinfo()[0]}
                    ip: 127.0.0.1
                    cpu_count: {JobQueue._sysinfo()[1]}
                    status: free
                    job_counter: 0
                scheduler:
                  policy: sequential
            """).strip()

        template = yaml.safe_load(template)
        template['cloudmesh']['jobset'].update({'jobs': specification})

        # VERBOSE(template)

        # Creating the jobset yaml file. This will replace the file if it
        # already exists.
        # TODO: This should take backup of existing yaml file
        with open(jobset, 'w') as fo:
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

        spec['cloudmesh.jobset.jobs'].update(specification)
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
        user = JobQueue._user()
        _spec = {
            'name': arguments.get('names')[idx],
            'directory': arguments.get('directory') or '.',
            'ip': arguments.get('ip_list')[idx] or 'localhost',
            'input': arguments.get('input_list')[idx] or './data',
            'output': arguments.get('output_list')[idx] or './output',
            'status': arguments.get('status') or 'ready',
            'gpu': arguments.get('gpu_list')[idx] or "",
            'user': arguments.get('user') or user,
            'arguments': arguments.get('arguments_list')[idx] or "",
            'executable': arguments.get('executable'),
            'shell': arguments.get('shell') or 'bash'
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
        for idx in range(len(specification['names'])):
            dict_out[specification['names'][idx]] = JobQueue.define(
                specification, idx)
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

        arguments['arg2_expanded'] = Parameter.expand(arguments[arg2])

        if len(arguments[arg1]) == 1 and len(arguments['arg2_expanded']) == 1:
            pass
        elif len(arguments[arg1]) > 1 and len(arguments['arg2_expanded']) == 1:
            arguments['arg2_expanded'] = [arguments[arg2]] * len(arguments[
                                                                     arg1])
        elif len(arguments[arg1]) != len(arguments['arg2_expanded']):
            Console.error(f"Number of {arg2} must match number of {arg1}")
            return ""

        return arguments['arg2_expanded']

    def addhost(self, arguments):
        """
        Adds a new host in jobset yaml file
        :param arguments: dictionary containing host info
        :return: updates the jobset with host info
        """
        config = Config(self.filename)

        tag = arguments.hostname
        config[f'cloudmesh.hosts.{tag}.name'] = arguments.hostname or \
                                                'localhost'
        config[f'cloudmesh.hosts.{tag}.ip'] = arguments.ip or 'localhost'
        config[f'cloudmesh.hosts.{tag}.cpu_count'] = arguments.cpu_count or '0'
        config[f'cloudmesh.hosts.{tag}.status'] = arguments.status or 'free'
        config[f'cloudmesh.hosts.{tag}.job_counter'] = arguments.job_counter \
                                                       or '0'

    def enlist_hosts(self):
        """
        Enlists all hosts configured in jobset
        :return: list of hosts
        """
        config = Config(self.filename)
        order = ['name', 'ip', 'cpu_count', 'status', 'job_counter']
        print(Printer.write(config['cloudmesh.hosts'], order=order))

    @staticmethod
    def _get_hostname(ip, spec):
        """
        Returns hostname for given host ip
        :param ip: host ip
        :param spec: jobset dictionary
        :return: hostname
        """
        for k, v in spec['cloudmesh.hosts'].items():
            if v['ip'] == ip:
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
        return p.get_ip()

    def run_job(self, names=None):
        """
        To run the job on remote machine
        :param names: job names
        :return: job is submitted to the host
        """
        spec = Config(self.filename)

        if names is None:
            names = spec['jobs'].keys()

        for k, v in spec['jobs'].items():

            if k in names:

                ip = JobQueue.get_available_ip(v['ip'], spec)

                if ip is not None:

                    command = f"ssh {v['user']}@{ip} "       \
                              f"\"cd {v['directory']};"      \
                              f"sh -c 'echo \$\$ > {v['output']}/{k}_pid.log;" \
                              f"exec {v['executable']} {v['arguments']}'\""

                    VERBOSE(command)

                    Shell.terminal(command, title=f"Running {k}")
                    time.sleep(5)

                    spec[f'jobs.{k}.status'] = 'submitted'
                    spec[f'jobs.{k}.submitted_to_ip'] = ip
                    hname = JobQueue._get_hostname(ip, spec)
                    ctr = int(spec[f'cloudmesh.hosts.{hname}.job_counter'])
                    spec[f'cloudmesh.hosts.{hname}.job_counter'] = str(ctr + 1)
                else:
                    Console.error(f"Job {k} could not be submitted due to "
                                  f"missing host with ip {ip}")
                    return ""

    def kill_job(self, names=None):
        """
        To kill the job on remote machine
        :param names: job names
        :return: job is killed on the host
        """
        spec = Config(self.filename)

        if names is None:
            names = spec['jobs'].keys()

        for k, v in spec['jobs'].items():

            if k in names:

                ip = v['submitted_to_ip']

                if ip is not None:

                    command = f"ssh {v['user']}@{ip} " \
                              f"\"cd {v['output']};" \
                              f"kill -9 \$(cat {k}_pid.log)\""

                    VERBOSE(command)

                    Shell.terminal(command, title=f"Running {k}")
                    # time.sleep(5)

                    spec[f'jobs.{k}.status'] = 'killed'
                    hname = JobQueue._get_hostname(ip, spec)
                    ctr = int(spec[f'cloudmesh.hosts.{hname}.job_counter'])
                    spec[f'cloudmesh.hosts.{hname}.job_counter']= str(ctr - 1)

                else:
                    Console.error(f"Job {k} could not be killed due to "
                                  f"missing host with ip {ip}")
                    return ""

    def delete_job(self, names=None):
        """
        Deletes a job from jobset. If the job is already submitted for
        execution then it is killed first and then deleted from jobset.
        :param names: list of names of jobs to be deleted
        :return: updates jobset
        """
        spec = Config(self.filename)

        if names is None:
            names = spec['jobs'].keys()

        for name in names:

            try:
                if spec[f'jobs.{name}.status'] == 'submitted':
                    self.kill_job([name])

                del spec['jobs'][name]

                spec.save(self.filename)

            except KeyError:
                Console.error(f"Job '{name}' not found in jobset. ")
            except Exception as e:
                Console.error(f"Job {name} could not be deleted. Please check.")

    def get_policy(self):
        """
        Returns scheduler policy name from jobset
        :return: policy name
        """
        config = Config(self.filename)
        return config['cloudmesh.scheduler.policy']

    def update_policy(self, policy):
        """
        Updates the scheduler policy name
        :return: None
        """
        valid_policies = ['sequential', 'smart', 'frugal', 'random']

        if policy in valid_policies:
            config = Config(self.filename)
            old_policy = config['cloudmesh.scheduler.policy']
            config['cloudmesh.scheduler.policy'] = policy

            Console.info(f"Scheduler policy changed from {old_policy} to "
                         f"{policy}")
        else:
            Console.error(f"Scheduler policy {policy} is not configured."
                          f"Available options are {','.join(valid_policies)}.")
            return ""

    def enlist_jobs(self, filter_name=None, filter_value=None, sort_var=None):
        """
        Enlists all jobs from the jobset. Applies filter based on the
        filter_value and filter_name. Sorting of output is done on sort_var,
        or by default on job order in the jobset.
        :param filter_name: Element name to apply filter on
        :param filter_value: Value of the element to be filtered in
        :param sort_var: Element name to sort the output on
        :return: Prints a table with job list
        """
        spec = Configuration(self.filename)
        op_dict = dict()

        if sort_var is None:
            sort_var = True

        i = 0
        for k, v in spec['cloudmesh.jobset.jobs'].items():
            if filter_name is None:
                i += 1
                if v.get("status") is None:
                    v["status"] = 'Unavailable'
                op_dict[k] = {
                    'Number': i,
                    'JobName': v.get("name"),
                    'JobStatus': v.get("status"),
                    'RemoteIp': v.get("ip"),
                    'Command': v.get("executable"),
                    'Arguments': v.get("arguments"),
                    'User': v.get('user')
                }
            else:
                if filter_name == 'name':
                    # job name can have partial match. Hence separate logic:
                    if filter_value in v[filter_name]:
                        i += 1
                        if v.get("status") is None:
                            v["status"] = 'Unavailable'
                        op_dict[k] = {
                            'Number': i,
                            'JobName': v.get("name"),
                            'JobStatus': v.get("status"),
                            'RemoteIp': v.get("ip"),
                            'Command': v.get("executable"),
                            'Arguments': v.get("arguments"),
                            'User': v.get('user')
                        }
                else:
                    # Exact match on filter_name with filter_value
                    if v[filter_name] == filter_value:
                        i += 1
                        if v.get("status") is None:
                            v["status"] = 'Unavailable'
                        op_dict[k] = {
                            'Number': i,
                            'JobName': v.get("name"),
                            'JobStatus': v.get("status"),
                            'RemoteIp': v.get("ip"),
                            'Command': v.get("executable"),
                            'Arguments': v.get("arguments"),
                            'User': v.get('user')
                        }

        order = ['Number', 'JobName', 'JobStatus', 'RemoteIp', 'Command',
                 'Arguments', 'User']

        print(Printer.write(op_dict, order=order, sort_keys=sort_var))


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

        self.host_data = self.spec['cloudmesh.hosts']
        self.policy = self.spec['cloudmesh.scheduler.policy']
        self.availability = dict()

        for k, v in self.host_data.items():
            available = int(v['cpu_count']) - int(v['job_counter'])
            if available > 0:
                self.availability[v['ip']] = available

        VERBOSE(self.availability)

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
            if self.policy == 'sequential':
                return list(self.availability.keys())[0]
            elif self.policy == 'random':
                return random.choice(list(self.availability))
            elif self.policy == 'smart':
                d = sorted(self.availability, key=lambda x:self.availability[x],
                           reverse=True)
                return d[0]
            elif self.policy == 'frugal':
                d = sorted(self.availability, key=lambda x:self.availability[x],
                           reverse=False)
                return d[0]
            else:
                Console.error(f"Scheduler policy {self.policy} is not "
                              f"configured. Available options are sequential, "
                              f"random, smart, frugal.")
                return None
