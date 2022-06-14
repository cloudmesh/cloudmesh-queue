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
    def do_cluster(self, args, arguments):
        """
        ::

          Usage:
            cluster create [--cluster=CLUSTER] [--experiment=EXPERIMENT]
            cluster list [--cluster=CLUSTER]  [--experiment=EXPERIMENT]
            cluster add [--cluster=CLUSTER]  [--experiment=EXPERIMENT] --id=ID --name=NAME --user=USER
                                [--ip=IP]
                                [--status=STATUS]
                                [--gpu=GPU]
                                [--pyenv=PYENV]
            cluster delete [--cluster=CLUSTER]  [--experiment=EXPERIMENT] --id=ID
            cluster activate [--cluster=CLUSTER]  [--experiment=EXPERIMENT] --id=ID
            cluster deactivate [--cluster=CLUSTER]  [--experiment=EXPERIMENT] --id=ID
            cluster set [--cluster=CLUSTER]  [--experiment=EXPERIMENT] --id=ID --key=KEY --value=VALUE


          This command is used to create a yaml file representation of a group of hosts
          called a cluster. It is used as an input into cms queue commands as --hostfile,
          for example to run a queue of jobs on the provided hosts.

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

        map_parameters(
            arguments,
            "name",
            "arguments",
            "gpu",
            "executable",
            "input",
            "ip",
            "id"
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
            "key",
            "value",
            "cluster"
        )

        variables = Variables()

        # que_name = variables["queue"]
        # VERBOSE(arguments)

        ids = Parameter.expand(arguments['--id'])
        #print(f'ids is {ids}')
        #print(f'EXPERIMENT is {arguments.experiment}')
        #print(f'CLUSTER is {arguments.cluster}')

        if arguments.cluster is None:
            arguments.cluster = 'default'

        if not arguments.create:
            cluster_file_name = arguments.cluster
            if '-cluster.yaml' not in cluster_file_name:
                cluster_file_name = arguments.cluster + '-cluster.yaml'

            if arguments.cluster and arguments.experiment is not None:
                file = os.path.join(arguments.experiment, cluster_file_name)
                if os.path.exists(file):
                    cluster = Cluster(name=arguments.cluster,experiment=arguments.experiment)
                else:
                    Console.error(f'Cluster: {file} does not exist')
                    return
            elif arguments.cluster:
                file = os.path.join('./experiment', cluster_file_name)
                if os.path.exists(file):
                    cluster = Cluster(name=arguments.cluster)
                else:
                    Console.error(f'Cluster: {file} does not exist')
                    return
            else:
                Console.error("A CLUSTER argument is required")
                return
        if arguments.experiment is None:
            arguments.experiment = "./experiment"

        if arguments.create:
            if arguments.experiment:
                cluster = Cluster(name=arguments.cluster, experiment=arguments.experiment)
            else:
                cluster = Cluster(name=arguments.cluster)
        elif arguments.list:
            print(cluster.info(order=['id','name','user','status','gpu','pyenv','ip','max_jobs_allowed']))
        elif arguments.add:
            host_args = {}
            if arguments.name: host_args['name'] = arguments.name
            if arguments.user: host_args ['user'] = arguments.user
            if arguments.ip: host_args ['ip'] = arguments.ip
            if arguments['--status']: host_args ['status'] = arguments['--status']
            if arguments.gpu: host_args ['gpu'] = int(arguments.gpu)
            if arguments.pyenv: host_args ['pyenv'] = arguments.pyenv

            for host_id in ids:
                host_args['id'] = host_id
                host = Host(**host_args)
                Console.info(f'Adding host {host.id} to cluster {cluster.name}')
                cluster.add(host)
        elif arguments.delete:
            Console.info(f'Deleting hosts: {ids}')
            for host_id in ids:
                cluster.delete(id=host_id)
        elif arguments.activate:
            for host_id in ids:
                host_dict = cluster.get(id=host_id)
                host = Host(**host_dict)
                host.status = 'active'
                cluster.set(host=host)
                Console.info(f'Activating host {host.id} in cluster {cluster.name}')
        elif arguments.deactivate:
            for host_id in ids:
                host_dict = cluster.get(id=host_id)
                host = Host(**host_dict)
                host.status = 'inactive'
                cluster.set(host=host)
                Console.info(f'Activating host {host.id} in cluster {cluster.name}')

        elif arguments.set:
            for host_id in ids:
                host_dict = cluster.get(id=host_id)
                host_dict[arguments.key] = arguments.value
                host = Host(**host_dict)
                cluster.set(host=host)
                Console.info(f'Setting host: {host.id} key: {arguments.key} value: {arguments.value} in cluster {cluster.name}')

        return ""
