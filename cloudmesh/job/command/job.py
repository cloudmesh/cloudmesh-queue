import os
from pathlib import Path

from cloudmesh.common.console import Console
from cloudmesh.common.debug import VERBOSE
from cloudmesh.common.parameter import Parameter
from cloudmesh.common.variables import Variables
from cloudmesh.shell.command import PluginCommand
from cloudmesh.shell.command import command
from cloudmesh.shell.command import map_parameters


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
              -f      specify the file
              --status=STATUS  the status [default: None]

          Description:

              job info
                prints the informations for the queued jobs

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
          the variable "jobset". It can queries with cms set jobset. It can be set witk
          cms set jobset=VALUE
          We may not even do cms job set VALUE due to this simpler existing way of interfaceing
          we can query the variables with
          variables = Variables() and also set them that way
          variables["jobset"] = VALUE

          Usage example:

            cms job template a.yaml --name="b[0-1]"; less a.yaml

                creates the jobs b0 and b1 as templates in the jobset a.yaml

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
            arguments.names = names
            arguments.ip = arguments.ip or "localhost"

            arguments.ips = ips = Parameter.expand(arguments.ip)

            if len(names) == 1 and len(ips) ==1:

                pass
                # we have one ip and one name

            elif len(names) > 1 and len (ips) == 1:

                # we have multiple names that are all mapped to one ip

                arguments.ips = [arguments.ip] * len(names)

            elif len(names) != len(ips):

                Console.error("number of ips must match number of names")
                return ""

            # executable is always just one arument
            executable = arguments.executable

            # input is just like ip
            # output is just like ip

            status = arguments.status

            # gpu is like ip

            # arguments is like ip

            shell = arguments.shell

            # for debugging

            VERBOSE(arguments)

            #
            # now we need to call the jobset and add the right things ...
            #

        elif arguments.add:
            # job add FILE


            if variables["jobset"] is None:
                Console.error("Jobset not defined. Please use `cms job set "
                              "FILE` to define the jobset.")
                return ""


            jobqueue = JobQueue()


            """
            if file:
                print(f"{file} to be appended in jobset")

                jobqueue.update_spec(
                    jobset_location=_directory,
                    jobset_name=_name,
                    newjobset_location=_directory,
                    newjobset_name=_name,
                    verbose=variables["verbose"])
            else:
                print("Creation of individual entry")

                jobqueue.update_spec(
                    jobset_location=_directory,
                    jobset_name=_name,
                    newjob_dict=arguments,
                    verbose=variables["verbose"])

            """
            # Console.error("Not yet implemented")


        elif arguments.status:
            # job status
            Console.error("Not yet implemented")

        elif arguments.list and arguments["--status"]:
            # job list --status=STATUS
            Console.error("Not yet implemented")

        elif arguments.list and arguments["--name"]:
            # job list --name=NAME
            VERBOSE(names)
            Console.error("Not yet implemented")

        elif arguments.list:
            # job list
            Console.error("Not yet implemented")

        elif arguments.kill:
            # job kill --name=NAME

            VERBOSE(names)

            Console.error("Not yet implemented")

        elif arguments.reset:
            # job reset --name=NAME
            name = arguments["--name"]
            Console.error("Not yet implemented")

        elif arguments.delete:
            # job delete --name=NAME
            name = arguments["--name"]
            Console.error("Not yet implemented")

        elif arguments.help:
            # job help
            os.system("cms help job")

        return ""
