from __future__ import print_function
from cloudmesh.shell.command import command
from cloudmesh.shell.command import PluginCommand
from cloudmesh.common.console import Console
from cloudmesh.common.util import path_expand
from pprint import pprint
from cloudmesh.common.debug import VERBOSE

class JobCommand(PluginCommand):

    # noinspection PyUnusedLocal
    @command
    def do_job(self, args, arguments):
        """
        ::

          Usage:
                job --file=FILE
                job list

          This command does some useful things.

          Arguments:
              FILE   a file name

          Options:
              -f      specify the file

          Description:

              job list
                lists all jobs

              job list --status=open
                lists alsl jobs with a specific status

              job status
                shows the status of all jobs

          Job States:

             done   - job completed
             ready  - ready for scheduling
             failed - job failed

          more to come
          
        """

        #arguments.FILE = arguments['--file'] or None

        #VERBOSE(arguments)


        #if arguments.FILE:
        #    print("option a")
        #    m.list(path_expand(arguments.FILE))
        #
        #elif arguments.list:
        #    print("option b")
        #    m.list("just calling list without parameter")

        Console.error("Not yet implemented")
        return ""
