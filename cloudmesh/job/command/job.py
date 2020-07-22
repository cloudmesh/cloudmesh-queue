import os
from pathlib import Path

from cloudmesh.common.console import Console
from cloudmesh.common.debug import VERBOSE
from cloudmesh.common.parameter import Parameter
from cloudmesh.common.variables import Variables
from cloudmesh.shell.command import PluginCommand
from cloudmesh.shell.command import command
from cloudmesh.shell.command import map_parameters
import oyaml as yaml


class JobCommand(PluginCommand):

    # noinspection PyUnusedLocal
    @command
    def do_job(self, args, arguments):
        """
        ::

          Usage:
            job set FILE
            job template FILE [--name=NAME]
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
            job run
            job info

          This command does some useful things.

          Arguments:
              FILE   a file name

          Options:
              -f       specify the file
              --status the status [default: None]

          Description:

              job info
                prints the information for the queued jobs

              job set FILE
                sets the jobset to the file name. All other commands will be
                applied to a jobset

              job add FILE
                adds the jobs in the file to the jobset

              job template FILE
                creates a job template  in the file

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

              job help
                prints the manual page

          Job States:

             done   - job completed
             ready  - ready for scheduling
             failed - job failed
             timeout - timeout

          Job specification:

             The jobs are specified in aa yaml file

             name:
               ip: ip of the host
               input: where the input comes form (locally to ip)
               output: where to store the outout (locally to ip)
               status: the status
               gpu: the GPU specification # string such as "0,2" as defined by the
                    GPU framework e.g. NVIDIA
               user: the userneme on ip to execute the job
               directory: the working directory
               arguments: the arguments passed along # lis of key values
               executable: the executable
               shell: bash # executes the job in the provided shell
                      $(SHELL) will use the default user shell
               timeout: time to live after which the command is
                        interrupted

          The current jobset filename is stored in the cloudmesh variables under
          the variable "jobset". It can queries with cms set jobset. It can be set with
          cms set jobset=VALUE
          We may not even do cms job set VALUE due to this simpler existing way of interfaceing
          we can query the variables with
          variables = Variables() and also set them that way
          variables["jobset"] = VALUE

          Usage examples:
            cms job info
                Prints location of job queue file.

            cms job set '~/.cloudmesh/job/spec.yaml'
                Sets jobset as the FILE provided. Further process refers jobset.

            cms job template a.yaml --name="b[0-1]"; less a.yaml
                Creates the jobs b0 and b1 as templates in the jobset.

            cms job add --name=z[0-1] --ip=123,345 --executable='ls'
            --input='..\data' --output='a,b'
                Creates entries in jobset for jobs z0 and z1 with provided
                arguments.

            cms job add '~\.cloudmesh\another.yaml'
                Adds jobs from FILE to jobset
        """

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
                       "user"
                       )
        # status has to be obtained with arguments["--status"]
        # we simply set it to state so its still easy to read
        arguments["state"] = arguments["--status"]

        variables = Variables()

        VERBOSE(arguments)

        names = Parameter.expand(arguments["--name"])

        file = arguments["FILE"]

        # do the import here to avoid long loading times for other commands

        default_location = "~/.cloudmesh/job/spec.yaml"

        if arguments.info:

            jobset = variables["jobset"] or default_location
            Console.msg(f"Jobs are defined in: {jobset}")
            return ""

        elif arguments.template:

            # TODO: do we need FILE in this call?
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

            name, directory, basename = JobQueue._location(file)
            
            Console.ok(f"Jobset defined as {name} located at"
                       f"{file}")

        elif arguments.add and arguments.FILE is None:

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
            _name, _directory, _basename = JobQueue._location(
                variables["jobset"])

            jobqueue = JobQueue()

            # fixed arguments for all jobs
            arguments.executable = arguments.executable or 'ls'
            arguments.status = arguments.status or 'ready'
            arguments.shell = arguments.shell or 'bash'
            arguments.directory = arguments.directory or '.'

            # Variable arguments
            arguments.names = names
            arguments.ip = arguments.ip or "localhost"
            arguments.input = arguments.input or "../data"
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
            # job add FILE
            # Path.expanduser needed as windows can't interpret "~"
            file = Path.expanduser(Path(arguments.FILE))
            _name, _directory, _basename = JobQueue._location(file)

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

            jobqueue = JobQueue()

            with open(file, 'r') as fi:
                spec = yaml.load(fi, Loader=yaml.FullLoader)

            jobqueue.add(spec)

        elif arguments.status:
            # job status
            Console.error("status - Not yet implemented")

        elif arguments.list and arguments["--status"]:
            # job list --status=STATUS
            Console.error("list status - Not yet implemented")

        elif arguments.list and arguments["--name"]:
            # job list --name=NAME
            VERBOSE(names)
            Console.error("list name - Not yet implemented")

        elif arguments.list:
            # job list
            jobset = variables["jobset"] or default_location
            jobset = Path.expanduser(Path(jobset))
            # op_dict = dict()

            with open(jobset, 'r') as fi:
                spec = yaml.load(fi, Loader=yaml.FullLoader)

            # TODO: use Printer
            for k, v in spec.items():
                print(k, v.get("status"))

            # print(op_dict)

        elif arguments.kill:
            # job kill --name=NAME

            VERBOSE(names)

            Console.error("kill - Not yet implemented")

        elif arguments.reset:
            # job reset --name=NAME
            name = arguments["--name"]
            Console.error("reset - Not yet implemented")

        elif arguments.delete:
            # job delete --name=NAME
            name = arguments["--name"]
            Console.error("delete - Not yet implemented")

        elif arguments.help:
            # job help
            os.system("cms help job")

        return ""
