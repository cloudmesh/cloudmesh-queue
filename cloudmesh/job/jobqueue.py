from pathlib import Path
import os, time, sys, multiprocessing, random
import oyaml as yaml
from cloudmesh.common.Shell import Shell
from cloudmesh.configuration.Config import Config
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
            JobQueue._location(self.filename)
        if self.directory != "":
            Shell.mkdir(self.directory)

    @staticmethod
    def _location(filename):
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
        variables
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
            cloudmesh:
              default:
                user: {user}
              hosts:
                localhost:
                  name: {JobQueue._sysinfo()[0]}
                  ip: 127.0.0.1
                  cpu_count: {JobQueue._sysinfo()[1]}
                  status: free
                  job_counter: 0
              scheduler:
                policy: sequential
            jobs:
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

    def add(self, specification):
        """
        Adds jobs in the jobset
        :param specification: dictionary containing details of the jobs
        :return: None, appends the job in jobset
        """
        # if type(specification) != str:
        #     Console.error("only specify a yaml string")

        if type(specification) != dict:
            Console.error("only specify a yaml dict")

        jobset = Path.expanduser(Path(self.filename))
        Path.mkdir(jobset.parent, exist_ok=True)

        with open(jobset, 'r') as file:
            content = yaml.safe_load(file)
            content['jobs'].update(specification)

        with open(jobset, 'w') as file:
            fruit_list = yaml.safe_dump(content, file)

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
            'ip': arguments.get('ip_list')[idx] or 'r-003',
            'input': arguments.get('input_list')[idx] or './data',
            'output': arguments.get('output_list')[idx] or './data',
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

        jobset = jobset or "~/.cloudmesh/job/spec.yaml"
        jobset = path_expand(jobset)

        dict_out = dict()
        for idx in range(len(specification['names'])):
            dict_out[specification['names'][idx]] = JobQueue.define(
                specification, idx)
        VERBOSE(dict_out)

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
        config[f'cloudmesh.hosts.{tag}.name'] = arguments.hostname
        config[f'cloudmesh.hosts.{tag}.ip'] = arguments.ip
        config[f'cloudmesh.hosts.{tag}.cpu_count'] = arguments.cpu_count
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
        for k, v in spec['cloudmesh']['hosts'].items():
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
        host_data = spec['cloudmesh']['hosts']
        policy = spec['cloudmesh']['scheduler']['policy']
        availability = dict()

        for k, v in host_data.items():
            available = int(v['cpu_count']) - int(v['job_counter'])
            if available > 0:
                availability[v['ip']] = available

        if availability.get(ip):
            return ip
        else:
            if policy == 'sequential':
                # First available host
                return list(availability.keys())[0]
            elif policy == 'random':
                # Random available host
                return random.choice(availability)
            elif policy == 'smart':
                # Host with highest availability
                d = sorted(availability, key=lambda x: availability[x],
                           reverse=True)
                return d[0]
            elif policy == 'frugal':
                # Host with least availability
                d = sorted(availability, key=lambda x: availability[x],
                           reverse=False)
                return d[0]
            else:
                Console.error(f"Scheduler policy {policy} is not configured."
                              "Available options are sequential, random, "
                              "smart, frugal.")
                return None

    def run_job(self, names=None):
        """
        To run the job on remote machine
        :param names: job names
        :return: job is submitted to the host
        """
        jobset = Path.expanduser(Path(self.filename))
        with open(jobset, 'r') as fi:
            spec = yaml.load(fi, Loader=yaml.FullLoader)

        if names is None:
            names = spec['jobs'].keys()

        for k, v in spec['jobs'].items():

            if k in names:

                ip = JobQueue.get_available_ip(v['ip'], spec)

                if ip is not None:
                    command = f"ssh {v['user']}@{ip} "  \
                              f"\"cd {v['directory']}; "    \
                              f"{v['executable']} {v['arguments']}\""

                    Shell.terminal(command, title=f"Running {k}")

                    spec['jobs'][k]['status'] = 'submitted'
                    hname = JobQueue._get_hostname(ip, spec)
                    ctr = int(spec['cloudmesh']['hosts'][hname]['job_counter'])
                    spec['cloudmesh']['hosts'][hname]['job_counter'] = \
                                                                   str(ctr + 1)
                else:
                    Console.error(f"Job {k} could not be submitted due to "
                                  f"missing host with ip {ip}")
                    return ""

        # Updating the status of the job as 'submitted' and increasing the
        # job_counter at host level:
        with open(jobset, 'w') as fo:
            yaml.dump(spec, fo, default_flow_style=False)

# class SubmitQueue:
#     """
#     Performs following tasks:
#     - generate: creates spec.yaml from sweep.py
#     - submit: submits jobs from spec.yaml to target compute resource
#     """
#     def __init__(self, yaml_location="../data"):
#         """
#         Creates an empty yaml file on instantiation
#         :param yaml_location: Local location for yaml file
#         """
#         self.yaml_out = Path(yaml_location, 'spec.yaml')
#         fo = open(self.yaml_out,'w')
#         # fo.write(f"# YAML file to submit jobs on multiple compute
#         # resources\n# User: {getpass.getuser()}\n# Created at: {time.ctime(
#         # )}\n")
#         fo.close()
#         self.yaml_dict = dict()
#         # Counter to be used in the .yaml root node for each job
#         self.ctr = 1
#
#         self.iu_config = Config()
#         self.user = self.iu_config['cloudmesh.iu.user']
#         self.host = self.iu_config['cloudmesh.iu.host']
#         self.port = self.iu_config['cloudmesh.iu.port']
#         self.gpu = self.iu_config['cloudmesh.iu.gpu']
#         self.reservation = self.iu_config['cloudmesh.iu.reservation']
#
#     def generate(self, experiment,
#                  name,
#                  expected_run_time=None,
#                  remote_output=".",
#                  local_output="../data",
#                  remote_mc_name="romeo",
#                  install=None,
#                  run="./cm/cloudmesh-timeseries/cloudmesh/timeseries/predict"
#                      "/lstm-predict-n.py",
#                  parameters=None
#                  ):
#         """
#         Creates the .yaml file spec.yaml at self.yaml_location
#         :param experiment: Experiment name
#         :param name: Job name
#         :param expected_run_time: Expected run time, e.g. 1h
#         :param remote_output: Output directory on remote resource
#         :param local_output: Output directory on local machine
#         :param remote_mc_name: Name of the remote compute resource
#         :param install: Commands to be run before executing predictions
#         :param run: command to be run for predictions
#         :param parameters: dict, additional parameters for the 'run' command
#         :return: submits jobs to remote resource
#         """
#         # Console.info(f"Generating {self.yaml_out}\n")
#
#         if parameters is None:
#             parameters = {'fields': ['Nbeds'], 'daysin': 1, 'n': 2,
#                           'data': './cm/cloudmesh-timeseries/data'}
#         if install is None:
#             if remote_mc_name == 'romeo':
#                 install = f'ssh -t {self.user}@juliet.futuresystems.org "ssh {self.host}"'
#             else:
#                 install = None
#         self.yaml_dict['experiment'] = experiment
#         self.yaml_dict['name'] = name
#         self.yaml_dict['expected_run_time'] = expected_run_time
#         self.yaml_dict['remote_output'] = f'./cm/covid_model/job{self.ctr}'
#         self.yaml_dict['local_output'] = local_output
#         self.yaml_dict['remote_mc_name'] = remote_mc_name
#         self.yaml_dict['install'] = install
#         self.yaml_dict['parameters'] = parameters
#         self.yaml_dict['run'] = run
#
#         self.yaml_dict['state'] = self.yaml_dict['remote_output']+'/status.yaml'
#         self.yaml_dict['status'] = None
#         self.yaml_dict['run_time'] = None
#         self.yaml_dict['gpu'] = self.gpu
#
#         self.out_dict = dict()
#         self.out_dict[f'job{self.ctr}'] = self.yaml_dict
#         self.ctr += 1
#
#         with open(self.yaml_out, 'a+') as fo:
#             yaml.dump(self.out_dict, fo, default_flow_style=False)
#
#         # Console.info(f"Generated {self.yaml_out}\n")
#
#     def submit(self):
#         """
#         Method reads job list from spec.yaml and submits each job to
#         designated remote compute resource
#         :return: None
#         """
#         with open(self.yaml_out, 'r') as fi:
#             spec = yaml.load(fi, Loader=yaml.FullLoader)
#             for job in spec.keys():
#                 args = ' '.join([f"--{k}={v}" for k,v in spec[job][
#                     'parameters'].items()])
#
#                 command = f"{spec[job]['install']} \"{spec[job]['run']} " \
#                           f"{args} --output={spec[job]['remote_output']}\""
#                 print(command)
#
#                 Shell.terminal(command, title=f"Running {job}")
#
#                 spec[job]['status'] = 'Submitted'
#
#         with open(self.yaml_out, 'w') as fo:
#             yaml.dump(spec, fo, default_flow_style=False)
#
#     def get_status(self, job_name='All'):
#         with open(self.yaml_out, 'r') as fi:
#             spec = yaml.load(fi, Loader=yaml.FullLoader)
#
#         f=spec[job_name]['state']
#         command = spec[job_name]['install'] + \
#                   f' \"cat {f} | grep \'current_status\' \"'
#
#         print(command)
#
#         content = Shell.live(command)
#
#         # if Path.is_dir(Path(r"C:\Program Files\Git")):
#         #     p = subprocess.Popen([r"C:\Program Files\Git\git-bash.exe",
#         #                           "-c", f"{command}"],
#         #                           stdout=subprocess.PIPE,
#         #                           stderr=subprocess.PIPE)
#         #     # p.wait()
#         #     print("==================")
#         #     print(p.stdout.decode())
#         #     print(p.stderr.decode())
#         #     print("==================")
#         #     content = 'if'
#         # else:
#         #     content = 'Unknown'
#
#         print("out of command")
#         print(content)
