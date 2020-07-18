from cloudmesh.shell.command import command
from cloudmesh.shell.command import PluginCommand
from cloudmesh.common.console import Console
from cloudmesh.common.util import path_expand
from pprint import pprint
from cloudmesh.common.debug import VERBOSE
import os
from cloudmesh.common.variables import Variables
from cloudmesh.common.parameter import Parameter

class JobCommand(PluginCommand):

    # noinspection PyUnusedLocal
    @command
    def do_job(self, args, arguments):
        """
        ::

          Usage:
            job set FILE
            job add FILE
            job add --name=NAME
                    [--diretcory=NAME]
                    --ip=IP
                    [--input=INPUT]
                    [--output=OUTPUT]
                    [--status=STATUS]
                    [--gpu=GPU]
                    [--user=USER]
                    [--directory=DIRECTORY]
                    [--arguments=ARGUMENTS]
                    --executable=EXECUTABLE
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

          This command does some useful things.

          Arguments:
              FILE   a file name

          Options:
              -f      specify the file
              --status=STATUS  the status [default: None]

          Description:

              job set FILE
                sets the jobset to the file name. All other commands will be
                applied to a jobset

              job add FILE
                adds the jobs in the file to the jobset

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

        """

        variables = Variables()
        pprint(variables.__dict__)
        print(variables["gregor"])

        if arguments["--name"] is not None:
            names = Parameter.expand(arguments["--name"])

        if arguments.set:
            # job set FILE
            file = arguments["FILE"]
            variables["jobset"] = file


        elif arguments.add:
            # job add FILE
            Console.error("Not yet implemented")

        elif arguments.status:
            #job status
            Console.error("Not yet implemented")

        elif arguments.list and arguments["--status"]:
            #job list --status=STATUS
            Console.error("Not yet implemented")

        elif arguments.list and arguments["--name"]:
            ##job list --name=NAME
            print (names)
            Console.error("Not yet implemented")

        elif arguments.list:
            #job list
            Console.error("Not yet implemented")

        elif arguments.kill:
            #job kill --name=NAME

            print (names)

            Console.error("Not yet implemented")

        elif arguments.reset:
            #job reset --name=NAME
            name = arguments["--name"]
            Console.error("Not yet implemented")

        elif arguments.delete:
            #job delete --name=NAME
            name = arguments["--name"]
            Console.error("Not yet implemented")

        elif arguments.help:
            #job help
            os.system("cms help job")

        return ""
