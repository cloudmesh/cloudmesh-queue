import json
import multiprocessing
import os
import shlex
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
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
from cloudmesh.common.util import path_expand
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
    status: str = "undefined"
    gpu: str = None
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
    pyenv: str = None
    last_probe_check: str = None

    def __post_init__(self):
        #print(self.info())

        #Console.ok(f"Creating: {self.name}")
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
        if self.host and self.user and self.status == 'undefined':
            self.status = 'ready'

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

    def check_host_running(self):
        host = Host(name=self.host,user=self.user)
        probe_status, probe_time = host.probe()
        if not probe_status:
            if self.status == 'start' or self.status =='run':
                self.status = 'crash'
        return probe_status

    def check_host_running2(self,timeout_min=10):
        if self.last_probe_check is None:
            raise ValueError ('Job last_probe_time is None')

        last_probe_time = datetime.strptime(self.last_probe_check, "%d/%m/%Y %H:%M:%S")

        if datetime.now() > last_probe_time + timedelta(minutes=timeout_min):
            host = Host(name=self.host, user=self.user)
            probe_status, probe_time = host.probe()
            self.last_probe_check = probe_time
            if not probe_status:
                if self.status == 'start' or self.status == 'run':
                    self.status = 'crash'
                return False
        return True

    def check_running(self):
        ps = self.ps()
        if ps is None:
            return False
        return True

    def check_crashed(self,timeout_min=10):
        if not is_local(self.host) and (self.status == 'start' or self.status == 'run') \
                and not self.check_host_running2():
            return True
        elif self.state == 'start' and not self.check_running():
            time.sleep(5) # TODO make this more deterministic
            if self.state == 'start':
                if is_local(self.host):
                    command = \
                        f"cd {self.directory}/{self.name}; " + \
                        f"{self.logging(msg='crash')};"
                else:
                    command = f"ssh {self.user}@{self.host} " + \
                              f"'" + \
                              f"cd {self.directory}/{self.name}; " + \
                              f"{self.logging(msg='crash')};" + \
                              f"'"
                os.system(command)
                return True
        elif self.status == 'start':
            return False
        return None

    def remove_dir(self):
        if is_local(self.host):
            command = \
                f"cd {self.directory}; " + \
                f"rm -rf ./{self.name};"
        else:
            command = f"ssh {self.user}@{self.host} " + \
                      f"'" + \
                      f"cd {self.directory}; " + \
                      f"rm -rf ./{self.name} ;" + \
                      f"'"
        r = os.system(command)
        if r != 0:
            Console.warning(f'Could not delete {self.name} dir on {self.user}@{self.host}')

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
        return Printer.attribute(self.to_dict(), output=output)

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
            pyenv_cmd = ''
            if self.pyenv is not None:
                pyenv_cmd = f'source {self.pyenv}; '
            gpu_cmd = ''
            if self.gpu is not None:
                gpu_cmd = f'export CUDA_VISIBLE_DEVICES={self.gpu}'
            script = "\n".join([
                f"#! {self.shell_path} -x",
                f"echo $$ > {self.name}.pid",
                f"rm -f {self.output}",
                f"rm -f {self.log}",
                f"{start_line}",
                f'echo -ne "# date: " >> {self.log}; date >> {self.log}' + pyenv_cmd + gpu_cmd,
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
            if len(result) != 0:
                self.status = result[-1].split(":", 1)[1].strip()

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

        try:
            int(self.pid)
        except:
            self.pid = None
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
                    #BUG if host is unreachable
                found = True
            except:
                if 'log' in name:
                    # file does not exist until command run
                    return ''
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
        # print("Command:", self.remote_command)
        r = os.system(self.remote_command)
        self.pid = self.rpid
        self.status='run'
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
        if not self.check_running():
            Console.info(f'Job {self.name} could not be killed, not running ps {self.pid} on {self.host}')
            return
        if self.pid is None:
            # job has not been started nothing to kill
            return None
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

        #print("Command:", command)
        r = os.system(command)
        Console.info(f"Job kill return code was: {r}")
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
        self.experiment = path_expand(self.experiment)
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
            Console.warning(f"Could not delete job:{name}")

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
        #job = Job(**data)
        #return job

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
        self.save()

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
        #if len(self.jobs.data) > 0:
        self.jobs.save(self.filename)

    def refresh(self, keys=None):
        if keys is None:
            keys = self.keys()
        else:
            for key in keys:
                if key not in self.keys():
                    keys.remove(key)
        updates = False
        result = ''
        for key in keys:
            job = Job(**self.get(key))
            old_state = job.status
            new_state = job.state
            if old_state != new_state:
                updates = True
                self.set(job)
                result += f'{job.name} \t old_status:{old_state} \t new_state:{new_state}\n'
        if updates:
            self.save()
            return result
        else:
            return 'No job status changes.'

    def reset(self, keys=None, status=None):
        if keys is None:
            keys = self.keys()
        else:
            for key in keys:
                if key not in self.keys():
                    keys.remove(key)
        updates = False
        result = ''
        for key in keys:
            job = Job(**self.get(key))
            old_state = job.status
            if (status is None and job.status != 'end') or job.status == status:
                if job.status == 'start' or job.status == 'run':
                    job.kill()
                job.remove_dir()
                if job.user and job.host:
                    new_state = 'ready'
                else:
                    new_state = 'undefined'
                job.status = new_state
                job.pid=None
                if old_state != new_state:
                    updates = True
                    self.set(job)
                    result += f'{job.name} \t old_status:{old_state} \t new_state:{new_state}\n'
        if updates:
            self.save()
            return result
        else:
            return 'No job status changes.'

    def get_hosts(self):
        hosts = []
        for key in self.keys():
            job = Job(**self.get(key))
            user = job.user
            host = job.host
            if user is not None and host is not None and (user,host) not in hosts:
                hosts.append((user,host))
        result = []
        for user,host in hosts:
            result.append(Host(user=user,name=host))
        return result


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
                 jobs: List = None,
                 max_parallel: int = 1,
                 timeout_min: int = 10):
        Queue.__init__(self,
                       name=name,
                       experiment=experiment,
                       filename=filename,
                       jobs=jobs)
        self.running = 0
        self.scheduler_N = len(self.jobs.data)
        self.scheduler_current_job = 0
        self.max_parallel = max_parallel
        self.running_jobs = []
        self.completed_jobs = []
        self.ran_jobs = []
        self.timeout_min = timeout_min

    def __next__(self):
        found_job = False
        self.refresh(keys=self.running_jobs)
        while (not found_job) and (self.scheduler_current_job < len(self.jobs.data)):
            key = list(self.jobs.keys())[self.scheduler_current_job]
            result = self.jobs.data[key]
            if result['status'] == 'ready':
                found_job = True
            self.scheduler_current_job += 1
            #all jobs must be defined prior to calling
        if not found_job:
            return None
        else:
            return result

    def check_if_jobs_finished(self):
        self.refresh()
        for job in self.running_jobs:
            try:
                if self.get(job)['status'] == 'end':
                    self.running_jobs.remove(job)
                    self.completed_jobs.append(job)
                    self.running -= 1
                    return True
            except:
                # job deleted or renamed in queue
                self.running_jobs.remove(job)
                self.running -= 1
                return True
        return False

    def check_for_crashes(self):
        for job in self.running_jobs:
            job = Job(**self.get(job))
            crashed = job.check_crashed(timeout_min=self.timeout_min)
            self.set(job)
            if crashed:
                Console.warning(f'Job {job.name} status:CRASH')
                job.status = 'crash'
                self.set(job)
                self.running_jobs.remove(job.name)
                self.running -= 1

    def run(self):
        next_job = self.__next__()
        while next_job is not None:
            job = Job(**next_job)
            while self.running == self.max_parallel:
                Console.info(f"Waiting. At max_parallel jobs={self.max_parallel}.")
                time.sleep(1)
                finished = self.check_if_jobs_finished()
                if not finished:
                    self.check_for_crashes()
            Console.info(f'Running job: {job.name} on {job.user}@{job.host}')
            pid = job.run()
            host = Host(name=job.host, user=job.user)
            probe_status, probe_time = host.probe()
            job.last_probe_check = probe_time
            if pid is None:
                # pid was a shell error or none
                Console.warning(f'Job {job.name} failed to start.')
                job.status='fail_start'
                self.set(job)
                next_job = self.__next__()
                continue
            self.running += 1
            self.running_jobs.append(job.name)
            self.ran_jobs.append(job.name)
            Console.info(f"Running Jobs: {self.running_jobs}")
            self.set(job)
            next_job = self.__next__()
        return self.ran_jobs

    def wait_on_running(self):
        time.sleep(1)
        while len(self.running_jobs) > 0:
            finished = self.check_if_jobs_finished()
            if not finished:
                self.check_for_crashes()
        return self.completed_jobs


class SchedulerTestFIFO(Queue):

    def __init__(self,
                 name: str = "TBD",
                 experiment: str = None,
                 filename: str = None,
                 jobs: List = None,
                 max_parallel: int = 1):
        Queue.__init__(self,
                       name=name,
                       experiment=experiment,
                       filename=filename,
                       jobs=jobs)
        self.running = 0
        # when a job starts we need to increment running only if running <= max_parallel
        self.scheduler_N = len(self.jobs.data)
        self.scheduler_current_job = 0

    def __iter__(self):
        # get an update from all hosts in the queue
        # get from all host the current status (a function to be added to queue)
        # def refresh: called _
        return self.jobs.__dict__["data"].items()

    def __next__(self):
        # def refresh: called
        # needs to filter out unqualified jobs, jobs such as inative host, finished job, killed job,
        # status: undefined(no host assigned to job), defined (with host associated), running, killed, end
        key = self.jobs.keys()[self.scheduler_current_job]
        result = self.jobs.data[key]
        self.scheduler_current_job += 1
        return result


class SchedulerFIFOMultiHost(Queue):

    def __init__(self,
                 name: str = "TBD",
                 experiment: str = None,
                 filename: str = None,
                 jobs: List = None,
                 hosts: list = [],
                 timeout_min: int = 10):
        Queue.__init__(self,
                       name=name,
                       experiment=experiment,
                       filename=filename,
                       jobs=jobs)
        self.scheduler_N = len(self.jobs.data)
        self.scheduler_current_job = 0
        self.hosts = hosts
        self.running_jobs = []
        self.job_hosts = {}
        self.completed_jobs = []
        self.ran_jobs = []
        if self.hosts == [] or self.hosts is None:
            raise ValueError('No hosts provided to scheduler.')

    def __next__(self):
        found_job = False
        self.refresh(keys=self.running_jobs)
        while (not found_job) and (self.scheduler_current_job < len(self.jobs.data)):
            key = list(self.jobs.keys())[self.scheduler_current_job]
            result = self.jobs.data[key]
            if result['status'] == 'undefined' or result['status'] == 'ready':
                found_job = True
            self.scheduler_current_job += 1
        if not found_job:
            return None
        else:
            return result

    def get_host(self, name):
        for host in self.hosts:
            if host.name == name:
                return host

    def check_for_crashes(self):
        for job in self.running_jobs:
            job = Job(**self.get(job))
            crashed = job.check_crashed()
            self.set(job)
            if crashed:
                Console.warning(f'Job {job.name} status:CRASH')
                job.status = 'crash'
                self.set(job)
                self.running_jobs.remove(job.name)
                host = self.get_host(self.get(job.name)['host'])
                host.job_counter -= 1

    def check_if_jobs_finished(self):
        self.refresh(self.running_jobs)
        some_finished = False
        for job in self.running_jobs:
            try:
                if self.get(job)['status'] == 'end' or \
                self.get(job)['status'] == 'kill':
                    self.running_jobs.remove(job)
                    self.completed_jobs.append(job)
                    host = self.get_host(self.get(job)['host'])
                    host.job_counter -= 1
                    some_finished = True
                    return some_finished
            except:
                # job deleted or renamed in queue
                self.running_jobs.remove(job)
                host = self.job_hosts[job]
                host.job_counter -= 1
                some_finished = True
                return some_finished
        return some_finished

    def assign_host(self, job):
        # finds next available host for job
        found_host = False
        assigned_host = None
        while not found_host:
            for host in self.hosts:
                if host.job_counter < host.max_jobs_allowed:
                    probe_status, probe_time = host.probe()
                    if probe_status:
                        job.host = host.name
                        job.user = host.user
                        job.status = 'ready'
                        job.last_probe_check = probe_time
                        job.generate_command()
                        self.set(job)
                        assigned_host = host
                        return assigned_host
                    else:
                        Console.warning(f'Host {host.name} not responding to probe check.'
                                        f' Not assigning jobs to {host.name}')
            Console.info(f"Waiting. All hosts running max jobs.")
            time.sleep(1)
            some_finished = self.check_if_jobs_finished()
            if not some_finished:
                # only check for crashes if queue still full to reduce wait times
                self.check_for_crashes()
        return assigned_host

    def run(self):
        next_job = self.__next__()
        while next_job is not None:
            job = Job(**next_job)
            host = self.assign_host(job)
            host.job_counter += 1
            Console.info(f'Starting job: {job.name} on host:{job.user}@{job.host}')
            pid = job.run()
            if pid is None:
                # pid was a shell error or None
                Console.warning(f'Job {job.name} failed to start.')
                job.status='fail_start'
                self.set(job)
                next_job = self.__next__()
                continue
            self.set(job)
            self.running_jobs.append(job.name)
            self.job_hosts[job.name] = host
            self.ran_jobs.append(job.name)
            Console.info(f"Running Jobs: {self.running_jobs}")
            next_job = self.__next__()
        return self.ran_jobs

    def wait_on_running(self):
        time.sleep(1)
        while len(self.running_jobs) > 0:
            finished = self.check_if_jobs_finished()
            if not finished:
                self.check_for_crashes()
        return self.completed_jobs

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
        now = datetime.now()
        result = commonHost.check(hosts=f'{self.name}',username=self.user)
        self.probe_status = result[0]['success']
        hostname = result[0]['stdout']
        if self.name != hostname and self.name != 'localhost':
            Console.warning(f'Host probe returned different hostname:"{hostname}"'
                            f' than self.name: {self.name}.')
            self.probe_status = False
        self.probe_time = now.strftime("%d/%m/%Y %H:%M:%S")
        return self.probe_status, self.probe_time

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

    def keys(self):
        return self.hosts.keys()

    def items(self):
        return self.hosts.__dict__["data"].items()

    def values(self):
        return self.hosts.__dict__["data"].values()

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

    def get_free_hosts(self):
        hosts = []
        for key in self.keys():
            host = Host(**self.get(key))
            if host.status =='free':
                hosts.append(host)
        return hosts

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
