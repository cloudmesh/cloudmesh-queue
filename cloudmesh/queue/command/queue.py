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
            queue create QUEUE [--experiment=EXPERIMENT]
            queue list QUEUE [--experiment=EXPERIMENT]
            queue refresh QUEUE [--experiment=EXPERIMENT]
            queue add QUEUE [--experiment=EXPERIMENT] --name=NAME --command=COMMAND
                    [--input=INPUT]
                    [--output=OUTPUT]
                    [--status=STATUS]
                    [--gpu=GPU]
                    [--user=USER]
                    [--host=HOST]
                    [--shell=SHELL]
                    [--log=LOG]
                    [--pyenv=PYENV]
            queue delete QUEUE [--experiment=EXPERIMENT] --name=NAME
            queue run fifo QUEUE [--experiment=EXPERIMENT] --max_parallel=MAX_PARALLEL
            queue run fifo_multi QUEUE [--experiment=EXPERIMENT] --hosts=HOSTS
            queue reset QUEUE [--experiment=EXPERIMENT] [--name=NAME] [--status=STATUS]

          This command is a job queuing and scheduling framework. It allows
          users to leverage all the available compute resources to perform
          tasks which have heavy usage of compute power and execution time.

          Arguments:


          Default value of options is indicated in square brackets.
          Options:



          Description:



          Job States:



          Scheduler policies:


          Job specification:



          Usage examples:


          SERVICE INTERFACE



        """

        #do the import here to avoid long loading times for other commands

        from cloudmesh.queue.jobqueue import Queue
        from cloudmesh.queue.jobqueue import Job
        from cloudmesh.queue.jobqueue import SchedulerFIFO
        from cloudmesh.queue.jobqueue import SchedulerFIFOMultiHost
        from cloudmesh.queue.jobqueue import Host

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
            "host",
            "hosts"
            "cpus",
            "policy",
            "max_jobs_allowed",
            "service",
            "file",
            "command",
            "log",
            "experiment",
            "config",
            "pyenv",
            "max_parallel"
        )

        variables = Variables()

        # que_name = variables["queue"]
        # VERBOSE(arguments)

        names = Parameter.expand(arguments.name)

        #print(f'EXPERIMENT is {arguments.experiment}')
        #print(f'QUEUE is {arguments.QUEUE}')

        if not arguments.create:
            queue_file_name = arguments.QUEUE
            if '-queue.yaml' not in queue_file_name:
                queue_file_name = arguments.QUEUE + '-queue.yaml'

            if arguments.QUEUE and arguments.experiment is not None:
                file = os.path.join(arguments.experiment, queue_file_name)
                if os.path.exists(file):
                    queue = Queue(name=arguments.QUEUE,experiment=arguments.experiment)
                else:
                    Console.error(f'Queue: {file} does not exist')
                    return
            elif arguments.QUEUE:
                file = os.path.join('./experiment', queue_file_name)
                if os.path.exists(file):
                    queue = Queue(name=arguments.QUEUE)
                else:
                    Console.error(f'Queue: {file} does not exist')
                    return
            else:
                Console.error("A QUEUE argument is required")
                return
        if arguments.experiment is None:
            arguments.experiment = "./experiment"
        #print(queue)

        if arguments.create:
            if arguments.experiment:
                queue = Queue(name=arguments.QUEUE,experiment=arguments.experiment)
            else:
                queue = Queue(name=arguments.QUEUE)
        elif arguments.list:
            print(queue.info())
        elif arguments.refresh:
            Console.info(f'Refreshing Queue: {queue.name}')
            print(queue.refresh())
        elif arguments.delete:
            Console.info(f'Deleting jobs: {names}')
            for name in names:
                queue.delete(name=name)
        elif arguments.add:
            #TODO --command="'ls -a'" notice this requires "''" to work correctly
            job_args = {}
            if arguments.command: job_args['command'] = arguments.command
            if arguments.input: job_args['input'] = arguments.input
            if arguments.output: job_args['output'] = arguments.output
            if arguments['--status']: job_args['status'] = arguments['--status']
            if arguments.gpu: job_args['gpu'] = arguments.gpu
            if arguments.user: job_args['user'] = arguments.user
            if arguments.host: job_args['host'] = arguments.host
            if arguments.shell: job_args['shell'] = arguments.shell
            if arguments.log: job_args['log'] = arguments.log
            if arguments.pyenv: job_args['pyenv'] = arguments.pyenv

            for name in names:
                job_args['name'] = name
                job = Job(**job_args)
                Console.info(f'Adding job {job.name} to queue {queue.name}')
                queue.add(job)
        elif arguments.run and arguments.fifo:

            scheduler = SchedulerFIFO(name=arguments.QUEUE, experiment=arguments.experiment,
                                      max_parallel=int(arguments.max_parallel))
            hosts = queue.get_hosts()
            for host in hosts:
                Host.sync(user=host.user,host=host.name,experiment=arguments.experiment)
            ran_jobs = scheduler.run()
            Console.info(f"Ran Jobs: {ran_jobs}")
            completed_jobs = scheduler.wait_on_running()
            Console.info(f"Completed Jobs: {completed_jobs}")
        elif arguments.run and arguments.fifo_multi:
            args = arguments['--hosts'].split(',')
            hosts = []
            for pair in args:
                user,host = pair.split('@')
                hosts.append(Host(user=user,name=host))
            for host in hosts:
                Host.sync(user=host.user,host=host.name,experiment=arguments.experiment)
            scheduler = SchedulerFIFOMultiHost(name=arguments.QUEUE, experiment=arguments.experiment,hosts=hosts)
            ran_jobs = scheduler.run()
            Console.info(f"Ran Jobs: {ran_jobs}")
            completed_jobs = scheduler.wait_on_running()
            Console.info(f"Completed Jobs: {completed_jobs}")

        elif arguments.reset:
            status = arguments['--status'] if arguments['--status'] else None
            keys = names if arguments.name else None
            print(queue.reset(keys=keys,status=status))

        return ""
