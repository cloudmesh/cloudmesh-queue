from pathlib import Path
import os, time, sys
import oyaml as yaml
from cloudmesh.common.Shell import Shell
from cloudmesh.configuration.Config import Config
from cloudmesh.common.console import Console
import subprocess

class JobQueue:
    """
    To create, manage and monitor job execution queue
    """

    def __init__(self):
        Console.info("JobQueue instantiated")

    @staticmethod
    def update_spec(jobset_location='~/.cloudmesh',
                    jobset_name='spec.yaml',
                    newjob_dict=None,
                    newjobset_location='~/.cloudmesh',
                    newjobset_name=None,
                    verbose=False):
        """
        Adds new jobs to the jobset. New job list taken from input file or
        dictionary.

        :param jobset_location:
        :param jobset_name:
        :param newjob_dict:
        :param newjobset_location:
        :param newjobset_name:
        :param verbose:
        :return:
        """
        if verbose:
            Console.info("Called update_spec")
            print("\tjobset_location:\t", jobset_location)
            print("\tjobset_name:\t", jobset_name)
            print("\tnewjobset_location:\t", newjobset_location)
            print("\tnewjobset_name:\t", newjobset_name)
            print("\tnewjob_dict:\t", newjob_dict)

        jobset = Path.expanduser(Path(jobset_location, jobset_name))

        if newjobset_name:
            new_jobset = Path.expanduser(
                                Path(newjobset_location, newjobset_name))

            with open(new_jobset, 'r') as fi:
                new_spec = yaml.load(fi, Loader=yaml.FullLoader)

            with open(jobset, 'a+') as fo:
                yaml.dump(new_spec, fo, default_flow_style=False)

        elif newjob_dict:
            dict_out = dict()

            if sys.platform == 'win32':
                user = os.environ.get('USERNAME')
            else:
                user = os.environ.get('USER')

            dict_out['name'] = newjob_dict.get('--name')
            dict_out['remotedir'] = newjob_dict.get('--remotedir') or '.'
            dict_out['ip'] = newjob_dict.get('--ip') or 'r-003'
            dict_out['input'] = newjob_dict.get('--input') or './data'
            dict_out['output'] = newjob_dict.get('--output') or './data'
            dict_out['status'] = newjob_dict.get('--status') or 'ready'
            dict_out['gpu'] = newjob_dict.get('--gpu') or None
            dict_out['user'] = newjob_dict.get('--user') or  user
            dict_out['arguments'] = newjob_dict.get('--arguments') or '-lrta'
            dict_out['executable'] = newjob_dict.get('--executable') or 'ls'
            dict_out['shell'] = newjob_dict.get('--shell') or 'bash'

            dict_out1 = {newjob_dict.get('--name'): dict_out}

            if verbose:
                print(dict_out1)

            with open(jobset, 'a+') as fo:
                yaml.dump(dict_out1, fo, default_flow_style=False)

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
