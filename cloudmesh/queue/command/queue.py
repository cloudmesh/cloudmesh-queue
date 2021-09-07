import os
from pathlib import Path
# from pprint import pprint
import shutil

from cloudmesh.common.util import banner
from cloudmesh.common.console import Console
# from cloudmesh.common.debug import VERBOSE
from cloudmesh.common.parameter import Parameter
from cloudmesh.common.variables import Variables
from cloudmesh.shell.command import PluginCommand
from cloudmesh.shell.command import command
from cloudmesh.shell.command import map_parameters
# from cloudmesh.common.Printer import Printer
from cloudmesh.common.util import backup_name
# from cloudmesh.configuration.Config import Config
from cloudmesh.configuration.Configuration import Configuration
import oyaml as yaml
from cloudmesh.common.util import yn_choice


class JobCommand(PluginCommand):

    # noinspection PyUnusedLocal
    @command
    def do_queue(self, args, arguments):
        """
        ::

          Usage:
            queue set --experiment=EXPERIMENT
            queue set --file=FILE
            queue template [--name=NAME]
            queue add --file=FILE
            queue add --name=NAME --command=COMMAND
                    [--directory=<DIRECTORY>]
                    [--input=<INPUT>]
                    [--output=<OUTPUT>]
                    [--status=<STATUS>]
                    [--gpu=GPU]
                    [--user=USER]
                    [--shell=<SHELL>]
                    [--log=<LOG>]
                    [--experiment=<EXPERIMENT>]
            queue status
            queue list --status=STATUS
            queue list --name=NAME
            queue list
            queue kill [--name=NAME]
            queue reset [--name=NAME]
            queue delete [--name=NAME]
            queue help
            queue run [--name=NAME]
            queue info
            queue host add --hostname=hostname --ip=IP  --cpus=N
                         [--status=STATUS] [--job_counter=COUNTER]
                         [--max_jobs_allowed=<JOBS>]
            queue host list
            queue host delete --hostname=hostname
            queue scheduler --policy=POLICYNAME
            queue scheduler info
            queue --service start
            queue --service info
            queue --service ps
            queue --service list
            queue --service run
            queue --service view
            queue set --config=CONFIG --name=NAME ATTRIBUTE=VALUE
            queue exec HOST JOB


          This command is a job queuing and scheduling framework. It allows
          users to leverage all the available compute resources to perform
          tasks which have heavy usage of compute power and execution time.

          Arguments:
              FILE   a file name

          Default value of options is indicated in square brackets.
          Options:
            --name=NAME               Job name(s)       Example: 'job[0-5]'
            --ip=<IP>                 Host IP           [default: 127.0.0.1]
            --executable=<EXECUTABLE> Job name          [default: uname]
            --arguments=<ARGUMENTS>   Args for the job  [default:  -a]
            --directory=<DIRECTORY>   Path to run job   [default: .]
            --input=<INPUT>           Input data path   [default: ./data]
            --output=<OUTPUT>         Output path       [default: ./output]
            --status=<STATUS>         Job status        [default: ]
            --user=USER               Remote host user  Example. $USER
            --shell=<SHELL>           Shell to run job  [default: bash]
            --hostname=hostname       Host name         Example. 'juliet'
            --gpu=GPU                 GPUs to use       Example. "0,1", [default: None]
            --cpus=N                  Host CPU count    Example. '12', [default: '1']
            --job_counter=COUNTER     Job count         Example. '2'
            --policy=<POLICYNAME>     Scheduler policy  [default: sequential]
            --max_jobs_allowed=<JOBS> Max jobs allowed  [default: 1]
            --file=<FILE>             Jobset yaml file  [default: ]
            --log=<LOG>               Command logs      [default: .]
            --experiment=<EXPERIMENT> Experiment name   [default: 'experiment']
            --command=COMMAND         Command to run    Example: 'uname -u'
            --config=<CONFIG>         Config to update  [default: jobs]

          Description:

              queue info
                prints the information for the queued jobs

              queue set --file=FILE
                sets the jobset to the file name. All other commands will be
                applied to a jobset

              queue add --file=FILE
                adds the jobs in the file to the jobset

              queue template [--name=NAME]
                creates a queue template  in the jobset

              queue list
                lists all jobs

              queue list --status=open
                lists all jobs with a specific status

              queue list --name=NAME
                lists teh queue with the given name pattern

              queue status
                shows the status of all jobs

              queue kill --name=NAME
                kills the given jobs base on a name pattern such as
                name[01-04] which would kill all jobs with the given names

              queue reset [--name=NAME]
                resets the queue to be rerun

              queue delete --name=NAME
                deletes the given jobs base on a name pattern such as
                name[01-04] which would delete all jobs with the given names

              queue run [--name=NAME]
                Run all jobs from jobset. If --name argument is provided then
                run a specific job

              queue host add --hostname=name --ip=ip --cpus=n
                           .--max_jobs_allowed=x
                Adds a host in jobset yaml file.

              queue host list
                prints all the hosts configured in jobset
            
              queue host delete --hostname=name
                Delete a host from the config

              queue scheduler --policy=random
                Assigns policy name to the scheduler policy

              queue scheduler info
                Shows currently configured scheduler policy

              queue help
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

              The current jobset filename is stored in the cloudmesh variables
              under the variable "jobset". It can be queried with cms set
              jobset. It can be set with

                cms set jobset=VALUE

              We may not even do cms job set VALUE due to this simpler existing
              way of interfacing we can query the variables with

                  variables = Variables()

              and also set them that way

                variables["jobset"] = VALUE.

          Usage examples:
            cms queue info
                Prints location of job queue file.

            cms queue set --file='~/.cloudmesh/job/spec.yaml'
                Sets jobset as the FILE provided. Further process refers jobset.

            cms queue template --name="b[0-1]"
                Creates the jobs b0 and b1 as templates in the jobset.

            cms queue add --name=z[0-1] --command='uname -u'
                       .--input='../data' --output='a,b'
                Creates entries in jobset for jobs z0 and z1 with provided
                arguments.

            cms queue add --file='~/.cloudmesh/another.yaml'
                Adds jobs from FILE to jobset

            cms queue list
                Print all jobs

            cms queue list --name='perform'
                Print all jobs with the phrase 'perform' in job name

            cms queue list --status='ready'
                Print all jobs in status 'ready'

            cms queue status
                Prints all jobs ordered by their status

            cms queue reset --name=NAME
                Resets the status of the job to 'ready'.

            cms queue host add --hostname=name --ip=ip --cpus=n
                             .--max_jobs_allowed=x
                Adds a host in jobset yaml file.

            cms queue host list
                Prints all the hosts configured in jobset

            cms queue host delete --hostname=name
                Delete a host from the config

            cms queue scheduler --policy=random
                Assigns policy name to the scheduler policy

            cms queue scheduler info
                Shows currently configured scheduler policy

            cms queue run --name=ls_j
                Submits job(s) to host decided by the scheduler policy

            cms queue kill --name=ls_j
                Kills the job

            cms queue delete --name=ls_j
                Deletes a job from the jobset. If job is in 'submitted'
                status then it is killed first and then deleted from jobset.

          SERVICE INTERFACE

            cms queue --service start [--port=port]
                starts the rest service

            cms queue --service info
                provides the API interface in a browser

            cms queue --service ps
                lists the running services

            cms queue --service list [--port=port] 
                                   [--status=<STATUS>]
                                   [--name=NAME]
                lists the queued jobs

            cms queue --service queue start
                starts the queue.

            cms queue --service queue stop
                starts the queue.

            cms queue --service view

            cms queue --service run [--name=NAME]
                Submits single or all configured jobs for execution

            cms queue --service kill [--name=NAME]
                Submits single or all configured jobs for execution

        """

        # do the import here to avoid long loading times for other commands
        from cloudmesh.queue.jobqueue import Queue

        map_parameters(
            arguments,
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
            "cpus",
            "policy",
            "max_jobs_allowed",
            "service",
            "file",
            "command",
            "log",
            "experiment",
            "config"
        )

        # status has to be obtained with arguments["--status"]
        # we simply set it to state so its still easy to read
        arguments["state"] = arguments["--status"]
        if arguments["file"] == "":
            arguments["file"] = None

        variables = Variables()
        
        que_name= variables["queue"]
        # VERBOSE(arguments)

        names = Parameter.expand(arguments.name)

        # Instantiate JobQueue without filename to get default filename
        jobqueue = Queue()
        default_location = jobqueue.filename

        #
        # --service
        #
        if arguments.execute:

            hostname = arguments.HOST
            jobname = arguments.JOB

            print(hostname, jobname)

        elif arguments.set and arguments["ATTRIBUTE=VALUE"]:
            # queue set --config=jobs --name=job7 gpu=9

            attribute, value = arguments["ATTRIBUTE=VALUE"].split("=")
            name = arguments.name
            config = arguments.config

            if config == 'scheduler':
                Console.error("Please use `queue scheduler --policy=random`")
                return ""

            jobqueue = Queue()
            jobqueue.set_attribute(config, name, attribute, value)

            Console.ok(f"Updated {attribute} to {value} for {name} in config {config}.")

        elif arguments.service:

            if arguments.start and arguments.queue:

                raise NotImplementedError
                # the service must be started first
                if yn_choice("start the job queue"):
                    pass

            if arguments.stop and arguments.queue:

                raise NotImplementedError
                if yn_choice("stop the job queue"):
                    pass

            elif arguments.start:

                from cloudmesh.queue.service.Manager import Manager

                service = Manager.start()

            elif arguments.info:

                from cloudmesh.queue.service.Manager import Manager

                port = arguments.port or "8000"
                service = Manager.docs(port=port)

            elif arguments.ps:

                from cloudmesh.queue.service.Manager import Manager

                port = arguments.port or "8000"
                service = Manager.ps(port=port,
                                     status='submitted',
                                     job_name=None)

            elif arguments.list:

                from cloudmesh.queue.service.Manager import Manager

                port = arguments.port or "8000"
                service = Manager.show(port=port,
                                       status=arguments["--status"],
                                       job_name=arguments["--name"])

            elif arguments.run:

                from cloudmesh.queue.service.Manager import Manager

                port = arguments.port or "8000"
                service = Manager.show(port=port,
                                       job_name=arguments["--name"])

            elif arguments.kill:

                from cloudmesh.queue.service.Manager import Manager

                port = arguments.port or "8000"
                service = Manager.show(port=port,
                                       job_name=arguments["--name"])

            elif arguments.view:

                raise NotImplementedError

        #
        # NON SERVICE COMMANDS
        #

        elif arguments.info and not arguments.scheduler:
            # cms queue info

            jobset = queue_name or default_location
            Console.msg(f"Jobs are defined in: {jobset}")

            if not Path(jobset).expanduser().exists():
                Console.error("File does not exist")
            else:
                jobqueue.show_list()

            return ""

        elif arguments.template:
            # cms queue template --name=job[1-2]

            names = names or ["job"]
            jobset = queue_name or default_location
            queue_name = jobset
            template = dict()

            backup_jobset = backup_name(jobset)
            shutil.copyfile(Path(jobset).expanduser(), backup_jobset)

            jobqueue = Queue(jobset)
            for name in names:
                template.update(jobqueue.template(name=name))
                jobqueue.add_template(template)

            Console.msg(f"Jobs are defined in: {jobset}")

            jobqueue.show_list()

        elif arguments.set:
            # queue set --file=FILE
            file = arguments["file"]

            if not file.endswith(".yaml"):
                Console.error(
                    "the specification file must be a yaml file "
                    "and end with .yaml"
                )
                return ""

            queue_name = file

            jobqueue = JobQueue()
            name, directory, basename = jobqueue.location(file)

            Console.ok(f"Jobset defined as {basename} located at " f"{directory}")

            jobqueue.show_list()

        elif arguments.add and arguments.file is None and not arguments.host:
            """
            queue add --name=NAME
                    --command=COMMAND
                    [--directory=DIRECTORY]
                    [--input=INPUT]
                    [--output=OUTPUT]
                    [--status=STATUS]
                    [--gpu=GPU]
                    [--user=USER]
                    [--shell=SHELL]
                    [--log=LOG]
                    [--experiment=EXPERIMENT]
            """

            queue_name = queue_name or default_location
            jobqueue = Queue(name=queue_name)
            _name, _directory, _basename = jobqueue.location(
                queue_name
            )
            arguments.names = names

            # Variable arguments
            var_args = ["ip", "input", "output", "gpu"]

            for arg in var_args:
                arguments[f"{arg}_list"] = jobqueue.expand_args(
                    "names", arg, arguments
                )
                if arguments[f"{arg}_list"] == "":
                    return ""

            # VERBOSE(arguments)

            jobqueue.update_spec(arguments, queue_name)

            jobqueue.show_list(hosts=False)

        elif arguments.add and arguments.file:
            """
            queue add --file=FILE

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
            file = Path.expanduser(Path(arguments.file))
            # BUG: possible bug as we could use cloudmesh path_expand
            jobqueue = Queue()
            _name, _directory, _basename = jobqueue.location(file)

            if queue_name is None:
                Console.error(
                    "Jobset not defined. Please use `cms queue set "
                    "FILE` to define the jobset."
                )
                return ""

            if not file.is_file():
                Console.error(f"File {arguments.FILE} not found.")
                return ""

            if not _basename.endswith(".yaml"):
                Console.error(
                    "the specification file must be a yaml file "
                    "and end with .yaml"
                )
                return ""

            jobqueue = Queue(name=queue_name)

            with open(file, "r") as fi:
                spec = yaml.load(fi, Loader=yaml.FullLoader)

            jobqueue.add(spec)

            jobqueue.show_list(hosts=False)

        elif arguments.status:
            # queue status
            jobqueue = Queue(name=queue_name)
            out = jobqueue.print_jobs(sort_var="status")
            banner("Jobs")
            print(out)

        elif arguments.list and arguments["--status"] and not arguments.host:
            # queue list --status=STATUS
            jobqueue = Queue(name=queue_name)
            out = jobqueue.print_jobs(
                filter_name="status", filter_value=arguments["--status"]
            )
            banner("Jobs")
            print(out)

        elif arguments.list and arguments["--name"] and not arguments.host:
            # queue list --name=NAME
            jobqueue = Queue(name=queue_name)
            out = jobqueue.print_jobs(
                filter_name="name", filter_value=arguments["--name"]
            )
            banner("Jobs")
            print(out)

        elif arguments.list and not arguments.host:
            # queue list

            jobqueue = Queue(name=queue_name)
            out = jobqueue.print_jobs()
            banner("Jobs")
            print(out)

        elif arguments.kill:
            # queue kill --name=NAME

            jobqueue = Queue(name=queue_name)
            jobqueue.kill_job(names)

        elif arguments.reset:
            # queue reset --name=NAME

            jobqueue = Queue(name=queue_name)
            spec = Configuration(jobqueue.filename)

            if names is None:
                names = spec["cloudmesh.jobset.jobs"].keys()

            for name in names:
                if not spec["cloudmesh.jobset.jobs"].get(name):
                    Console.error(
                        f"Job {name} not found in jobset "
                        f"{jobqueue.filename}."
                    )
                    continue
                if spec[f"cloudmesh.jobset.jobs.{name}.status"] == "submitted":
                    Console.error(
                        f"Job {name} is already submitted for "
                        "execution. Please kill the job before reset."
                    )
                else:
                    spec[f"cloudmesh.jobset.jobs.{name}.status"] = "ready"
                    Console.ok(f"Status reset for job {name}.")

        elif arguments.run:
            # queue run --name=NAME
            jobqueue = Queue(name=queue_name)
            jobqueue.run_job(names)

            out = jobqueue.print_jobs(
                filter_name="name", filter_value=arguments["--name"]
            )
            print(out)

        elif arguments.delete and not arguments.host:
            # queue delete --name=NAME

            jobqueue = Queue(name=queue_name)
            jobqueue.delete_job(names)

            jobqueue.show_list(hosts=False)

        elif arguments.help:
            # queue help

            os.system("cms help job")

        elif arguments.add and arguments.host:
            # queue hosts add --hostname=NAME --ip=ip --cpus=n

            jobqueue = Queue(name=queue_name)
            jobqueue.addhost(arguments)

            jobqueue.show_list(jobs=False)

        elif arguments.host and arguments.delete:
            # queue delete hosts --hostname=hostname

            jobqueue = Queue(name=queue_name)
            jobqueue.delete_host(host_name=arguments.hostname)

            jobqueue.show_list(jobs=False)

        elif arguments.host and arguments.list:
            # queue list hosts

            jobqueue = Queue(name=queue_name)
            # out = jobqueue.print_hosts()
            # print(out)
            jobqueue.show_list(jobs=False)

        elif arguments.scheduler and arguments.info:
            # queue scheduler info

            jobqueue = Queue(name=queue_name)
            policy = jobqueue.get_policy()
            print()
            Console.info(f"Configured scheduler policy: {policy}")

        elif arguments.scheduler and arguments.policy:
            # queue scheduler --policy=random

            jobqueue = Queue(name=queue_name)
            print()
            jobqueue.update_policy(arguments.policy)

        return ""
