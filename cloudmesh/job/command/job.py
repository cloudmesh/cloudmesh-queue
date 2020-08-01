import os
from pathlib import Path

from cloudmesh.common.console import Console
from cloudmesh.common.debug import VERBOSE
from cloudmesh.common.parameter import Parameter
from cloudmesh.common.variables import Variables
from cloudmesh.shell.command import PluginCommand
from cloudmesh.shell.command import command
from cloudmesh.shell.command import map_parameters
from cloudmesh.common.Printer import Printer
from cloudmesh.configuration.Config import Config
import oyaml as yaml


class JobCommand(PluginCommand):

    # noinspection PyUnusedLocal
    @command
    def do_job(self, args, arguments):
        """
        ::

          Usage:
            job set FILE
            job template [--name=NAME]
            job add FILE
            job add --name=NAME
                    --ip=IP
                    --executable=EXECUTABLE
                    [--directory=DIRECTORY]
                    [--input=INPUT]
                    [--output=OUTPUT]
                    [--status=STATUS]
                    [--gpu=GPU]
                    [--user=USER]
                    [--arguments=ARGUMENTS]
                    [--shell=SHELL]
            job status
            job list --status=STATUS
            job list --name=NAME
            job list
            job kill [--name=NAME]
            job reset [--name=NAME]
            job delete [--name=NAME]
            job help
            job run [--name=NAME]
            job info
            job hosts add --hostname=hostname --ip=IP --cpu_count=N
                         [--status=STATUS] [--job_counter=COUNTER]
            job list hosts
            job scheduler --policy=POLICYNAME
            job scheduler info

          This command is a job queuing and scheduling framework. It allows
          users to leverage all the available compute resources to perform
          tasks which have heavy usage of compute power and execution time.

          Arguments:
              FILE   a file name

          Options:
              name=NAME               Name(s) of jobs.        Ex: 'job[0-5]'  [default: None]
              ip=IP                   IP of the host.         Ex: 127.0.0.1   [default: None]
              executable=EXECUTABLE   The command to be run.  Ex. 'ls'        [default: None]
              directory=DIRECTORY     Location to run job.    Ex. './'        [default: './']
              input=INPUT             Location of input data. Ex. './data'    [default: './data']
              output=OUTPUT           Location of outputs.    Ex. './output'  [default: './output/job_name']
              status=STATUS           Status of the job.      Ex. 'ready'     [default: 'ready']
              gpu=GPU                 Which GPU to use.       Ex. 7           [default: None]
              user=USER               User on remote host     Ex. 'uname'     [default: {System user}]
              arguments=ARGUMENTS     Args for the executable.Ex. '-lisa'     [default: None]
              shell=SHELL             Shell to run job.       Ex. 'bash'      [default: 'bash']
              hostname=hostname       Host name.              Ex. 'juliet'    [default: None]
              cpu_count=N             CPU count of the host.  Ex. '12'        [default: None]
              job_counter=COUNTER     Number of submitted jobsEx. '2'         [default: None]
              policy=POLICYNAME       Scheduler policy.       Ex. 'smart'     [default: 'sequential']

          Description:

              job info
                prints the information for the queued jobs

              job set FILE
                sets the jobset to the file name. All other commands will be
                applied to a jobset

              job add FILE
                adds the jobs in the file to the jobset

              job template
                creates a job template  in the jobset

              job list
                lists all jobs

              job list --status=open
                lists all jobs with a specific status

              job list --name=NAME
                lists teh job with the given name pattern

              job status
                shows the status of all jobs

              job kill --name=NAME
                kills the given jobs base on a name pattern such as
                name[01-04] which would kill all jobs with the given names

              job status [--name=NAME] [--status=STATUS]
                sets the status of all jobs to the status

              job reset [--name=NAME]
                resets the job to be rerun

              job delete --name=NAME
                deletes the given jobs base on a name pattern such as
                name[01-04] which would kill all jobs with the given names

              job run [--name=NAME]
                Run all jobs from jobset. If --name argument is provided then
                run a specific job

              job hosts add --hostname=name --ip=ip --cpu_count=n
                Adds a host in jobset yaml file.

              job list hosts
                Enlists all the hosts configured in jobset

              job scheduler --policy=random
                Assigns policy name to the scheduler policy

              job scheduler info
                Shows currently configured scheduler policy

              job help
                prints the manual page

          Job States:

             done   - job completed
             ready  - ready for scheduling
             failed - job failed
             timeout - timeout
             submitted - job submitted to remote machine for execution

          Scheduler policies:

             sequential - Use first available host
             random     - Use random available host
             smart      - Use a host with highest availability
             frugal     - Use a host with least availability

          Job specification:

             The jobs are specified in 'spec.yaml' file

             name:
               ip: ip of the host
               input: where the input comes form (locally to ip)
               output: where to store the outout (locally to ip)
               status: the status
               gpu: the GPU specification # string such as "0,2" as defined by
                    the GPU framework e.g. NVIDIA
               user: the userneme on ip to execute the job
               directory: the working directory
               arguments: the arguments passed along # lis of key values
               executable: the executable
               shell: bash # executes the job in the provided shell
                      $(SHELL) will use the default user shell

          The current jobset filename is stored in the cloudmesh variables under
          the variable "jobset". It can be queried with cms set jobset. It
          can be set with cms set jobset=VALUE.
          We may not even do cms job set VALUE due to this simpler existing way
          of interfacing we can query the variables with variables = Variables()
          and also set them that way variables["jobset"] = VALUE.

          Usage examples:
            cms job info
                Prints location of job queue file.

            cms job set '~/.cloudmesh/job/spec.yaml'
                Sets jobset as the FILE provided. Further process refers jobset.

            cms job template --name="b[0-1]"; less a.yaml
                Creates the jobs b0 and b1 as templates in the jobset.

            cms job add --name=z[0-1] --ip=123,345 --executable='ls'
            --input='..\data' --output='a,b'
                Creates entries in jobset for jobs z0 and z1 with provided
                arguments.

            cms job add '~\.cloudmesh\another.yaml'
                Adds jobs from FILE to jobset

            cms job list
                Enlist all jobs

            cms job list --name='perform'
                Enlist all jobs with the phrase 'perform' in job name

            cms job list --status='ready'
                Enlist all jobs in status 'ready'

            cms job status
                Enlists all jobs ordered by their status

            cms job reset --name=NAME
                Resets the status of the job to 'ready'.

            cms job hosts add --hostname=name --ip=ip --cpu_count=n
                Adds a host in jobset yaml file.

            cms job list hosts
                Enlists all the hosts configured in jobset

            cms job scheduler --policy=random
                Assigns policy name to the scheduler policy

            cms job scheduler info
                Shows currently configured scheduler policy

            cms job run --name=ls_j
                Submits job(s) to host decided by the scheduler policy

            cms job kill --name=ls_j
                Kills the job

            cms job delete --name=ls_j
                Deletes a job from the jobset. If job is in 'submitted'
                status then it is killed first and then deleted from jobset.

        """
        # TODO: create hosts entries based on all IPs used in jobs section

        # do the import here to avoid long loading times for other commands
        from cloudmesh.job.jobqueue import JobQueue

        map_parameters(arguments,
                       "name",
                       "arguments",
                       "gpu",
                       "executable",
                       "input",
                       "ip",
                       "output",
                       "shell",
                       "directory",
                       "user",
                       "hostname",
                       "cpu_count",
                       "policy"
                       )
        # status has to be obtained with arguments["--status"]
        # we simply set it to state so its still easy to read
        arguments["state"] = arguments["--status"]

        variables = Variables()

        VERBOSE(arguments)

        names = Parameter.expand(arguments["--name"])

        file = arguments["FILE"]

        # Instantiate JobQueue without filename to get default filename
        jobqueue = JobQueue()
        default_location = jobqueue.filename

        if arguments.info and not arguments.scheduler:

            jobset = variables["jobset"] or default_location
            Console.msg(f"Jobs are defined in: {jobset}")
            return ""

        elif arguments.template:

            names = names or ["job"]
            jobset = variables["jobset"] or default_location
            variables["jobset"] = jobset

            jobs = JobQueue(jobset)
            for name in names:
                template = jobs.template(name=name)
                jobs.add(template)

            Console.msg(f"Jobs are defined in: {jobset}")

        elif arguments.set:

            # job set FILE
            if not file.endswith(".yaml"):
                Console.error("the specification file must be a yaml file "
                              "and end with .yaml")
                return ""

            variables["jobset"] = file

            # _function s/b renamed as it is no longer private
            name, directory, basename = JobQueue.location(file)

            Console.ok(f"Jobset defined as {name} located at"
                       f"{file}")

        elif arguments.add and arguments.FILE is None \
                and not arguments.hosts:
            """
            job add --name=NAME
                    --ip=IP
                    --executable=EXECUTABLE
                    [--directory=DIRECTORY]
                    [--input=INPUT]
                    [--output=OUTPUT]
                    [--status=STATUS]
                    [--gpu=GPU]
                    [--user=USER]
                    [--arguments=ARGUMENTS]
                    [--shell=SHELL]
            """

            jobset = variables["jobset"] or default_location
            _name, _directory, _basename = JobQueue.location(
                variables["jobset"])

            jobqueue = JobQueue(variables["jobset"])

            # fixed arguments for all jobs
            arguments.executable = arguments.executable or 'ls'
            arguments.status = arguments.status or 'ready'
            arguments.shell = arguments.shell or 'bash'
            arguments.directory = arguments.directory or '.'

            # Variable arguments
            arguments.names = names
            arguments.ip = arguments.ip or "localhost"
            arguments.input = arguments.input or "./data"
            arguments.output = arguments.output or \
                               "./output/" + arguments['--name']
            arguments.gpu = arguments.gpu or " "
            arguments.arguments = arguments.arguments or " "

            var_args = ['ip', 'input', 'output', 'gpu', 'arguments']

            for arg in var_args:
                arguments[f'{arg}_list'] = jobqueue.expand_args('names', arg,
                                                                arguments)
                if arguments[f'{arg}_list'] == "":
                    return ""

            # for debugging
            VERBOSE(arguments)

            # now we need to call the jobset and add the right things
            jobqueue.update_spec(arguments, jobset)

        elif arguments.add and arguments.FILE:
            """
            job add FILE
            
            FILE is supposed to contain job list only in following format
              abcd:
                name: abcd
                directory: .
                ip: local
                input: ./data
                output: ./output/abcd
                status: ready
                gpu: ' '
                user: user
                arguments: -lisa
                executable: ls
                shell: bash
            """
            # Path.expanduser needed as windows can't interpret "~"
            file = Path.expanduser(Path(arguments.FILE))
            _name, _directory, _basename = JobQueue.location(file)

            if variables["jobset"] is None:
                Console.error("Jobset not defined. Please use `cms job set "
                              "FILE` to define the jobset.")
                return ""

            if not file.is_file():
                Console.error(f"File {arguments.FILE} not found.")
                return ""

            if not _basename.endswith(".yaml"):
                Console.error("the specification file must be a yaml file "
                              "and end with .yaml")
                return ""

            jobqueue = JobQueue(variables["jobset"])

            with open(file, 'r') as fi:
                spec = yaml.load(fi, Loader=yaml.FullLoader)

            jobqueue.add(spec)

        elif arguments.status:

            # job status
            jobqueue = JobQueue(variables["jobset"])
            jobqueue.enlist_jobs(sort_var='JobStatus')

        elif arguments.list and arguments["--status"] and \
                not arguments.hosts:

            # job list --status=STATUS
            jobqueue = JobQueue(variables["jobset"])
            jobqueue.enlist_jobs(filter_name='status',
                                 filter_value=arguments["--status"])

        elif arguments.list and arguments["--name"] and not arguments.hosts:
            # job list --name=NAME

            jobqueue = JobQueue(variables["jobset"])
            jobqueue.enlist_jobs(filter_name='name',
                                 filter_value=arguments["--name"])

        elif arguments.list and not arguments.hosts:
            # job list

            jobqueue = JobQueue(variables["jobset"])
            jobqueue.enlist_jobs()

        elif arguments.kill:
            # job kill --name=NAME

            jobqueue = JobQueue(variables["jobset"])
            jobqueue.kill_job(names)

        elif arguments.reset:
            # job reset --name=NAME

            jobqueue = JobQueue(variables["jobset"])
            spec = Config(jobqueue.filename)

            if names is None:
                names = spec['jobs'].keys()

            for name in names:
                if not spec['jobs'].get(name):
                    Console.error(f"Job {name} not found in jobset "
                                  f"{jobqueue.filename}.")
                    continue
                if spec['jobs'][name]['status'] == 'submitted':
                    Console.error(f"Job {name} is already submitted for "
                                "execution. Please kill the job before reset.")
                else:
                    spec[f'jobs.{name}.status'] = 'ready'
                    Console.ok(f"Status reset for job {name}.")

        elif arguments.run:
            # job run --name=NAME

            jobqueue = JobQueue(variables["jobset"])
            jobqueue.run_job(names)

        elif arguments.delete:
            # job delete --name=NAME

            jobqueue = JobQueue(variables["jobset"])
            jobqueue.delete_job(names)

        elif arguments.help:
            # job help

            os.system("cms help job")

        elif arguments.add and arguments.hosts:
            # job hosts add --hostname=NAME --ip=ip --cpu_count=n

            jobqueue = JobQueue(variables["jobset"])
            jobqueue.addhost(arguments)

        elif arguments.hosts and arguments.list:
            # job list hosts

            jobqueue = JobQueue(variables["jobset"])
            jobqueue.enlist_hosts()

        elif arguments.scheduler and arguments.info:
            # job scheduler info

            jobqueue = JobQueue(variables["jobset"])
            policy = jobqueue.get_policy()
            print()
            Console.info(f"Configured scheduler policy: {policy}")

        elif arguments.scheduler and arguments.policy:
            # job scheduler --policy=random

            jobqueue = JobQueue(variables["jobset"])
            print()
            jobqueue.update_policy(arguments.policy)

        return ""
