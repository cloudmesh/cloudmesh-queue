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
            queue create [--queue=QUEUE] [--experiment=EXPERIMENT]
            queue info [--queue=QUEUE] [--experiment=EXPERIMENT]
            queue refresh [--queue=QUEUE] [--experiment=EXPERIMENT]
            queue add [--queue=QUEUE] [--experiment=EXPERIMENT] --name=NAME --command=COMMAND
                    [--input=INPUT]
                    [--output=OUTPUT]
                    [--status=STATUS]
                    [--gpu=GPU]
                    [--user=USER]
                    [--host=HOST]
                    [--shell=SHELL]
                    [--log=LOG]
                    [--pyenv=PYENV]
            queue delete [--queue=QUEUE] [--experiment=EXPERIMENT] --name=NAME
            queue run fifo [--queue=QUEUE] [--experiment=EXPERIMENT] --max_parallel=MAX_PARALLEL [--timeout=TIMEOUT]
            queue run fifo_multi [--queue=QUEUE] [--experiment=EXPERIMENT] [--hosts=HOSTS] [--hostfile=HOSTFILE] [--timeout=TIMEOUT]
            queue reset [--queue=QUEUE] [--experiment=EXPERIMENT] [--name=NAME] [--status=STATUS]
            queue --service start [--port=PORT]
            queue --service info [--port=PORT]

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
        from cloudmesh.queue.jobqueue import Cluster
        from cloudmesh.common.Shell import Shell

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
            "hostfile",
            "max_parallel",
            "timeout",
            "port",
            "queue"
        )

        variables = Variables()

        # que_name = variables["queue"]
        # VERBOSE(arguments)

        names = Parameter.expand(arguments.name)

        #print(f'EXPERIMENT is {arguments.experiment}')
        #print(f'QUEUE is {arguments.QUEUE}')
       # print(f'queue is {arguments.queue}')

        if arguments.queue is None:
            arguments.queue = 'default'

        if not arguments.create and not arguments["--service"]:
            queue_file_name = arguments.queue
            if '-queue.yaml' not in queue_file_name:
                queue_file_name = arguments.queue + '-queue.yaml'

            if arguments.queue and arguments.experiment is not None:
                file = os.path.join(arguments.experiment, queue_file_name)
                if os.path.exists(file):
                    queue = Queue(name=arguments.queue,experiment=arguments.experiment)
                else:
                    Console.error(f'Queue: {file} does not exist')
                    return
            elif arguments.queue:
                file = os.path.join('./experiment', queue_file_name)
                if os.path.exists(file):
                    queue = Queue(name=arguments.queue)
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
                queue = Queue(name=arguments.queue,experiment=arguments.experiment)
            else:
                queue = Queue(name=arguments.queue)
        elif arguments.info and not arguments['--service']:
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
            if arguments.experiment: job_args['experiment'] = arguments.experiment

            for name in names:
                job_args['name'] = name
                job = Job(**job_args)
                Console.info(f'Adding job {job.name} to queue {queue.name}')
                queue.add(job)
        elif arguments.run and arguments.fifo:
            if arguments.timeout:
                timeout=int(arguments.timeout)
            else:
                timeout=10

            scheduler = SchedulerFIFO(name=arguments.queue, experiment=arguments.experiment,
                                      max_parallel=int(arguments.max_parallel),timeout_min=timeout)

            ran_jobs = scheduler.run()
            Console.info(f"Ran Jobs: {ran_jobs}")
            completed_jobs = scheduler.wait_on_running()
            Console.info(f"Completed Jobs: {completed_jobs}")
        elif arguments.run and arguments.fifo_multi:

            if arguments['--hosts'] is None and arguments.hostfile is None:
                Console.warning("Please provide a --hosts or --hostfile argument")
                return

            if arguments.timeout:
                timeout=int(arguments.timeout)
            else:
                timeout=10

            if arguments['--hosts']:
                args = arguments['--hosts'].split(',')
                hosts = []
                for pair in args:
                    user,host = pair.split('@')
                    hosts.append(Host(user=user,name=host))
            else:
                if not "-cluster.yaml" in arguments.hostfile:
                   name = arguments.hostfile
                   filename = arguments.hostfile + '-cluster.yaml'
                   filepath = arguments.experiment + "/" + filename
                else:
                    name = arguments.hostfile.replace("-cluster.yaml", "")
                    filename = arguments.hostfile
                    filepath = arguments.experiment + "/" + filename

                cluster = Cluster(name=name, filename=filepath)
                hosts = cluster.get_free_hosts()
                if hosts == []:
                    Console.warning(f"No free hosts found in cluster {filename}")
                    return

            scheduler = SchedulerFIFOMultiHost(name=arguments.queue, experiment=arguments.experiment,
                                               hosts=hosts, timeout_min=timeout)
            ran_jobs = scheduler.run()
            Console.info(f"Ran Jobs: {ran_jobs}")
            completed_jobs = scheduler.wait_on_running()
            Console.info(f"Completed Jobs: {completed_jobs}")

        elif arguments.reset:
            status = arguments['--status'] if arguments['--status'] else None
            keys = names if arguments.name else None
            print(queue.reset(keys=keys,status=status))

        elif arguments["--service"] and arguments.start:
            if arguments.port is None:
                os.system("cd ~/cm/cloudmesh-queue; uvicorn cloudmesh.queue.service.server:app")
            else:
                os.system(f"cd ~/cm/cloudmesh-queue; uvicorn cloudmesh.queue.service.server:app --port={arguments.port}")
        elif arguments["--service"] and arguments.info:
            if arguments.port is not None:
                port =":" + arguments.port
            else:
                port = ':8000'
            url = f"http://127.0.0.1{port}/docs"
            Shell.browser(url)

        return ""
