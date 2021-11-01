import subprocess
import secrets
import os

from getpass import getpass
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Depends, HTTPException, status

from cloudmesh.queue.jobqueue import Queue
from cloudmesh.queue.jobqueue import Cluster
from cloudmesh.queue.jobqueue import Job
from cloudmesh.queue.jobqueue import Host
from cloudmesh.queue.jobqueue import SchedulerFIFO
from cloudmesh.common.variables import Variables
from cloudmesh.common.Shell import Shell
from cloudmesh.common.parameter import Parameter
from cloudmesh.common.console import Console

import json

from aiofile import async_open
from fastapi import FastAPI, Request

tags_metadata = [
    {
        "name": "queue",
        "description": "Operations on queues.",
        "externalDocs": {
            "description": "Queue external docs.",
            "url": "https://github.com/cloudmesh/cloudmesh-queue/blob/main/README.md#queue",
        },
    },
    {
        "name": "cluster",
        "description": "Operations on clusters",
        "externalDocs": {
            "description": "Cluster external docs.",
            "url": "https://github.com/cloudmesh/cloudmesh-queue/blob/main/README.md#cluster",
        },
    },
]

app = FastAPI(
    title="Cloudmesh Queue: A job queue scheduler for remote/local servers.",
    description="""The [cloudmesh-queue](https://github.com/cloudmesh/cloudmesh-queue#cloudmesh-queue)
            provides a job queuing and scheduling 
            framework. It includes a library as well as a commandline interface. 
            Both allow users to leverage registered and available compute resources to 
            perform compute intensive tasks with high excution times. 
            A user can configure all available compute resources 
            as 'hosts' in a configuration file along with the list of jobs to be 
            executed. Then, based on the scheduler policy, user can schedule 
            these jobs on configured hosts. """, openapi_tags=tags_metadata
)


# uncomment to save json definition to support static page viewing
# raw github link used in url in static_example.html
# e.g url='https://raw.githubusercontent.com/cloudmesh/cloudmesh-queue/main/json_example/openapi.json''
#@app.on_event("startup")
#async def startup():
#    async with async_open("./json_example/openapi.json", 'w+') as afp:
#        await afp.write(json.dumps(app.openapi()))

security = HTTPBasic()

# comment out during dev
user = getpass(prompt='Please enter the username for HTTP Basic Auth: ')
password = getpass(prompt='Please enter the password for HTTP Basic Auth: ')

# uncomment during dev
#user = "user"
#password = "password"

running_queues = []

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, user)
    correct_password = secrets.compare_digest(credentials.password, password)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def __get_queue(queue: str, experiment: str = None):
    if '-queue.yaml' not in queue:
        queue_file_name = queue + '-queue.yaml'
    else:
        queue_file_name = queue
    if experiment is None:
        experiment = "experiment"
    file = os.path.join(experiment, queue_file_name)
    if os.path.exists(file):
        queue = Queue(name=queue, experiment=experiment)
    else:
        raise HTTPException(status_code=404, detail="Queue not found")
    return queue

def __get_cluster(cluster: str, experiment: str = None):
    if '-cluster.yaml' not in cluster:
        cluster_file_name = cluster + '-cluster.yaml'
    else:
        cluster_file_name = cluster
    if experiment is None:
        experiment = "experiment"
    file = os.path.join(experiment, cluster_file_name)
    if os.path.exists(file):
        cluster = Cluster(name=cluster, experiment=experiment)
    else:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return cluster

@app.get("/")
async def root(credentials: HTTPBasicCredentials = Depends(security)):
    """

    """
    return {"message": "Cloudmesh Queue Server"}

@app.post("/queue/",tags=["queue"])
def queue_create(name: str,experiment:str='experiment',credentials: HTTPBasicCredentials = Depends(security)):
    """
    Creates a queue with the given name and experiment.

    This will create a yaml file `"name"-queue.yaml`
    in the server sub-directory `./"experiment`":

    - **name**: the queue must have a name.
    - **experiment**: a user defined sub-directory to store the queue.
    """
    queue = Queue(name=name,experiment=experiment)
    return queue

@app.get("/queue/",tags=["queue"])
def list_queues(experiment:str='experiment',credentials: HTTPBasicCredentials = Depends(security)):
    """
    Lists the queues stored in the provided experiment directory.

    - **experiment**: a target directory to list its contained queue files.
    """
    if experiment is None:
        experiment = "experiment"
    r = Shell.run(f'ls ./{experiment} | grep queue.yaml')
    if 'No such file' in r:
        raise HTTPException(status_code=404, detail=f"Directory {experiment} does not exist")
    r = r.splitlines()
    return {"queues": r}

@app.put("/queue/ran",response_class=PlainTextResponse,tags=["queue"])
def refresh_and_list_ran_queues(credentials: HTTPBasicCredentials = Depends(security)):
    """
    The server maintains a list of queues that it has run.

    This command will refresh all queues contained in this list and provide
    their information including queue info, pid, cluster used, and current status (running, not running).

    After a queue has determined as not running, it will be removed from the servers list
    of running queuse, and it will no longer be presented by subsequent requests of this command.

    The server's list of ran queues is reset on a server restart.
    """
    response = ""
    for queue, experiment,cluster, pid in running_queues:
        if experiment is None:
            experiment_resolved = 'experiment'
        else:
            experiment_resolved = experiment
        keys = ["pid", "cmd"]
        keys_str = ",".join(keys)
        command = f"ps --format {keys_str} {pid}"
        out = Shell.run(command)
        if pid in out and f'queue={queue}' in out:
            response += f"Queue: {queue} Experiment: {experiment_resolved} Cluster: {cluster} STATUS:Running\n"
        else:
            response += f"Queue: {queue} Experiment: {experiment_resolved} Cluster: {cluster}  STATUS:Not Running\n"
            running_queues.remove((queue, experiment, cluster, pid))
        try:
            queue = __get_queue(queue=queue, experiment=experiment)
            queue.refresh()
            response += queue.info() + '\n\n'
        except:
            response += f"Could not get info for Queue: {queue} Experiment: {experiment_resolved}. It may have been deleted."
    if response == "":
        response = "No ran queues."
    return response

@app.get("/queue/{queue}",tags=["queue"])
def queue_get(queue: str, experiment:str="experiment", credentials: HTTPBasicCredentials = Depends(security)):
    """
    Returns a json representation of the full backing file of the queue `"queue"-queue.yaml`
    in the experiment directory.
    """
    queue = __get_queue(queue=queue,experiment=experiment)
    return queue

@app.get("/queue/{queue}/info",response_class=PlainTextResponse,tags=["queue"])
def queue_info(queue: str, experiment:str="experiment", credentials: HTTPBasicCredentials = Depends(security)):
    """
    Returns a tabular text representation of the following queue fields:
    "name", "status", "command","host","user", "gpu", "output", "log", and "experiment".

    Note the info command does not affect the content of the backing queue-file. To get
    the latest status of a runnig queue use the `Queue Refresh` request.
    """
    queue = __get_queue(queue=queue,experiment=experiment)
    return queue.info()

@app.delete("/queue/{queue}",tags=["queue"])
def queue_delete(queue: str,experiment: str="experiment",credentials: HTTPBasicCredentials = Depends(security)):
    """
    Deletes the queue in the provided experiment directory.
    """
    queue = __get_queue(queue=queue,experiment=experiment)
    os.system(f'rm {queue.filename}')
    return True

@app.get("/queue/{queue}/job/{job}",tags=["queue"])
def queue_get_job(queue: str, job: str,experiment:str = "experiment", credentials: HTTPBasicCredentials = Depends(security)):
    """
    Returns a json representation of the requested job.
    """
    queue = __get_queue(queue=queue,experiment=experiment)
    try:
        job = queue.get(job)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Job: {job} does not exist in queue.")
    return job

@app.put("/queue/{queue}/refresh", response_class=PlainTextResponse,tags=["queue"])
def queue_refresh(queue: str,experiment:str = "experiment", credentials: HTTPBasicCredentials = Depends(security)):
    """
    This refreshes the status of a queue. It is useful for determining the state of a running
    queue. It can be used to recover the latest job status from a queue manager or worker host failure.

    If any jobs are in the state "run" or "start" then the host
    running the job will be queried to get the latest job information.
    
    This info view of the updated queue is returned.
    """
    queue = __get_queue(queue=queue,experiment=experiment)
    queue.refresh()
    return queue.info()

@app.post("/queue/{queue}",response_class=PlainTextResponse,tags=["queue"])
def queue_add_job(queue: str, name: str, command: str,experiment:str = "experiment", input: str=None,output: str=None, \
                  status: str=None, gpu: str=None, user: str=None, host: str=None, \
                  shell: str=None, log: str=None, pyenv: str =None,
                  credentials: HTTPBasicCredentials = Depends(security)):
    """
    Adds a job to the provided queue.

    - **name**: takes a single or expandable name. For example job[1-10] will create
    10 jobs with the same parameters, and names job1 to job10.
    - **command**: the command that will be run by the job, e.g. `python test.py`
    - **input**: the location of input used by the command.
    - **output**: the location of output created by executing the command.
    - **status**: the status of the job. See
    [here](https://github.com/cloudmesh/cloudmesh-queue/blob/main/README.md#job-states)
    for a full list of job states.
    - **gpu**: is the GPUs to be set with the environment variable
    CUDA_VISIBLE_DEVICES=. Only include the numbers, i.e. 0,1 and not the environment
    variable name.
    - **user** and **host**: The user and host are the user and host that this job are
    assigned to. Some schedulers require these jobs to be set, others will assign them
    from a group of hosts.
    - **shell**: is the shell that will run the command.
    - **log**: is the location of the log output
    - **pyenv**: is the argument to the source command and will be executed before
    running the job to activate a python environment.

    """
    queue = __get_queue(queue=queue,experiment=experiment)
    names = Parameter.expand(name)
    job_args = {}
    if command: job_args['command'] = command
    if input: job_args['input'] = input
    if output: job_args['output'] = output
    if status: job_args['status'] = status
    if gpu: job_args['gpu'] = gpu
    if user: job_args['user'] = user
    if host: job_args['host'] = host
    if shell: job_args['shell'] = shell
    if log: job_args['log'] = log
    if pyenv: job_args['pyenv'] = pyenv

    for name in names:
        job_args['name'] = name
        job = Job(**job_args)
        queue.add(job)
    return queue.info()

@app.delete("/queue/{queue}/job/{job}",response_class=PlainTextResponse,tags=["queue"])
def queue_delete_job(queue: str, name: str, experiment:str = "experiment", credentials: HTTPBasicCredentials = Depends(security)):
    """
    Deletes the expandable list of jobs provided by the **name** argument, e.g. `name=job[1-10]`.
    """
    queue = __get_queue(queue=queue,experiment=experiment)
    names = Parameter.expand(name)
    for name in names:
        queue.delete(name=name)
    return queue.info()

@app.put("/queue/{queue}/run_fifo",tags=["queue"])
def queue_run_fifo(queue: str, max_parallel: int, experiment: str = "experiment", timeout:int=10,
                   credentials: HTTPBasicCredentials = Depends(security)):
    """
    Runs the queue with a simple fifo scheduler.

    - **max_parallel**: is the maximum number of parallel jobs that will be executed by the scheduler.
    - **timeout**: is the time that will consider a host as dead and mark the job as crashed.
    The default is 10 minutes.

    **Prerequisites**: All jobs intended to be run must be assigned a `user` and a `host`.
    Those jobs not assigned a `user` and `host` will be skipped.

    **Failure Recovery**: See
    [here](https://github.com/cloudmesh/cloudmesh-queue/blob/main/README.md#failure-considerations)
    for failure recovery instructions.
    """
    #queue run fifo QUEUE [--experiment=EXPERIMENT] --max_parallel=MAX_PARALLEL [--timeout=TIMEOUT]
    queue_obj = __get_queue(queue=queue, experiment=experiment)
    if experiment is not None:
        p = subprocess.Popen([f'cms queue run fifo --queue={queue} --experiment={experiment}'
                              f' --max_parallel={max_parallel} --timeout={timeout}'],
                             shell=True)
        cluster = 'None'
        running_queues.append((queue, experiment, cluster, str(p.pid)))
    else:
        p = subprocess.Popen([f'cms queue run fifo --queue={queue} --max_parallel={max_parallel} --timeout={timeout}'], shell=True)
        cluster = 'None'
        running_queues.append((queue, experiment, cluster, str(p.pid)))
    return {'result': f'started fifo scheduler: pid {p.pid}'}

@app.put("/queue/{queue}/run_fifo_multi",tags=["queue"])
def queue_run_fifo_multi(queue: str, cluster: str, experiment: str = "experiment", timeout:int=10,
                         credentials: HTTPBasicCredentials = Depends(security)):
    """
        Runs the queue with a fifo scheduler that assigns jobs to hosts provided in a cluster definition.

        - **cluster**: jobs will be assigned to active hosts contained in this cluster.
        This cluster definition must be in the same **experiment** directory as the queue.
        - **timeout**: is the time that will consider a host as dead and mark the job as crashed.
        The default is 10 minutes.

        All jobs in the queue with a state "undefined" or "ready" will be executed.

        **Failure Recovery**: See
        [here](https://github.com/cloudmesh/cloudmesh-queue/blob/main/README.md#failure-considerations-1)
        for failure recovery instructions.
        """
    # queue run fifo_multi QUEUE [--experiment=EXPERIMENT] [--hosts=HOSTS] [--hostfile=HOSTFILE] [--timeout=TIMEOUT]
    queue_obj = __get_queue(queue=queue, experiment=experiment)
    cluster_obj = __get_cluster(cluster=cluster, experiment=experiment)
    if experiment is not None:
        p = subprocess.Popen([f'cms queue run fifo_multi --queue={queue} --experiment={experiment} '
                              f'--hostfile={cluster} --timeout={timeout}'], shell=True)
        running_queues.append((queue,experiment, cluster, str(p.pid)))
    else:
        p = subprocess.Popen([f'cms queue run fifo_multi --queue={queue} --hostfile={cluster} --timeout={timeout}'], shell=True)
        running_queues.append((queue,experiment, cluster, str(p.pid)))
    return {'result': f'started fifo_multi scheduler: pid {p.pid}'}

@app.put("/queue/{queue}/stop",response_class=PlainTextResponse,tags=["queue"])
def queue_stop(queue: str, experiment: str = "experiment"):
    """
    Stops the execution of a queue and its running jobs. Returns a info representation of the
    queue after it has been stopped.
    """
    for q, exp, cluster, pid in running_queues:
        if q == queue and exp == experiment:
            keys = ["pid", "cmd"]
            keys_str = ",".join(keys)
            command = f"ps --format {keys_str} {pid}"
            out = Shell.run(command)
            if pid in out and f'queue={queue}' in out:
                Console.info(f'Killing queue pid {pid}')
                command = f'kill -9 $(ps -o pid= --ppid {pid});' + \
                          f'kill -9 {pid};'
                os.system(command)
        else:
            raise HTTPException(status_code=404, detail=f"Queue {queue} ps could not be found")
        queue = __get_queue(queue=queue, experiment=experiment)
        queue.refresh()
        keys = queue.keys()
        for key in keys:
            job = Job(**queue.get(key))
            if job.status == 'run' or job.status == "start":
                job.kill()
        running_queues.remove((q, exp,cluster, pid))
        queue.refresh()
        return queue.info()

@app.put("/queue/{queue}/reset",response_class=PlainTextResponse,tags=["queue"])
def queue_reset(queue: str,experiment:str = "experiment", name: str=None, status:str=None,
                credentials: HTTPBasicCredentials = Depends(security)):
    """
    Resets the status of a queue and removes the job directories from remote hosts.

    If you do not specify a **name** or **status**  argument. Then all jobs with
    a state other than `end` will be reset.

    Use the **name** argument to reset specific jobs.

    Use the **status** argument to reset jobs with a specific status (one status only,
    e.g. status = end).

    If you want to rerun jobs in a queue or recover from a crash you will need to
    reset the jobs. Resetting a job resets the state to a executable state (`undefined`
    or `start` depending on `user` and `host` assignment.) It also kills the jobs if they
    are currently running and removes the job directory from the assigned host.

    >WARNING: if you simply replace a job using `queue add` or rerun a job without a
     `reset` you will not get the result you expect, as the job files from the last run
     will not have been deleted.
    """
    #queue reset QUEUE [--experiment=EXPERIMENT] [--name=NAME] [--status=STATUS]
    queue = __get_queue(queue=queue,experiment=experiment)
    names = Parameter.expand(name)
    result = queue.reset(keys=names, status=status)
    return result

@app.post("/cluster/",tags=["cluster"])
def cluster_create(name: str,experiment: str="experiment",
                   credentials: HTTPBasicCredentials = Depends(security)):
    """
        Creates a cluster with the given name and experiment.

        This will create a yaml file `"name"-cluster.yaml`
        in the server sub-directory `./"experiment`":

        - **name**: the cluster must have a name.
        - **experiment**: a user defined sub-directory to store the cluster.
        """
    cluster = Cluster(name=name,experiment=experiment)
    return cluster

@app.get("/cluster/",tags=["cluster"])
def cluster_list(experiment:str = None, credentials: HTTPBasicCredentials = Depends(security)):
    """
        Lists the clusters stored in the provided experiment directory.

        - **experiment**: a target directory to list its contained queue files.
        """
    if experiment is None:
        experiment = 'experiment'
    r = Shell.run(f'ls ./{experiment} | grep cluster.yaml')
    if 'No such file' in r:
        raise HTTPException(status_code=404, detail=f"Directory {experiment} does not exist")
    r = r.splitlines()
    return {"clusters": r}

@app.post("/cluster/{cluster}", response_class=PlainTextResponse,tags=["cluster"])
def cluster_add_host(cluster: str, id: str, name: str,user: str,experiment:str = "experiment", ip: str=None, \
                  status: str=None, gpu: int=None, pyenv: str=None,
                     credentials: HTTPBasicCredentials = Depends(security)):
    """
    Add a host to the cluster.

    - **id**: an expandable unique id for the hosts being added, e.g. host0[1-10]
     will create ten hosts with ids: host01 through host10
     - **name**: the hostname of the machine that will be accessed
     - **user**: the username for the target host machine.
     - **status**: the status of the host. The default status(**active**) can be assigned jobs by a scheduler, all others will not.
     - **gpu**: is the GPUs to be set with the environment variable
    CUDA_VISIBLE_DEVICES=. Only include the numbers, i.e. 0,1 and not the environment
    variable name.
      - **pyenv**: is the argument to the source command and will be executed before
    running the job to activate a python environment.

    All hosts allow 1 maximum job when a scheduler is assigning jobs. To run multiple
    jobs on the same machine, define multiple hosts for that machine.

    """
    cluster = __get_cluster(cluster=cluster,experiment=experiment)
    ids = Parameter.expand(id)
    host_args = {}
    if name: host_args['name'] = name
    if user: host_args['user'] = user
    if ip: host_args['ip'] = ip
    if status: host_args['status'] = status
    if gpu: host_args['gpu'] = gpu
    if pyenv: host_args['pyenv'] = pyenv

    for host_id in ids:
        host_args['id'] = host_id
        host = Host(**host_args)
        Console.info(f'Adding host {host.id} to cluster {cluster.name}')
        cluster.add(host)
    return cluster.info()

@app.get("/cluster/{cluster}",tags=["cluster"])
def cluster_get(cluster: str, experiment:str = "experiment",
                credentials: HTTPBasicCredentials = Depends(security)):
    """
        Returns a json representation of the full backing file of the cluster `"cluster"-cluster.yaml`
        in the experiment directory.
        """
    cluster = __get_cluster(cluster=cluster,experiment=experiment)
    #return {"cluster": cluster.to_dict()}
    return cluster

@app.get("/cluster/{cluster}/info", response_class=PlainTextResponse,tags=["cluster"])
def cluster_info(cluster: str, experiment:str = "experiment",
                 credentials: HTTPBasicCredentials = Depends(security)):
    """
        Returns a tabular text representation of the following cluster fields:
        "id", "name", "user", "status", "gpu", "pyenv", "ip", "max_jobs_allowed".
        """
    cluster = __get_cluster(cluster=cluster,experiment=experiment)
    return cluster.info()

@app.delete("/cluster/{cluster}",tags=["cluster"])
def cluster_delete(cluster: str,experiment: str="experiment",credentials: HTTPBasicCredentials = Depends(security)):
    """
        Deletes the cluster in the provided experiment directory.
        """
    cluster = __get_cluster(cluster=cluster,experiment=experiment)
    os.system(f'rm {cluster.filename}')
    return True

@app.get("/cluster/{cluster}/id/{id}",tags=["cluster"])
def cluster_get_host(cluster: str, id: str,experiment:str = "experiment",
                     credentials: HTTPBasicCredentials = Depends(security)):
    """
        Returns a json representation of the requested host.
        """
    cluster = __get_cluster(cluster=cluster,experiment=experiment)
    try:
        host = cluster.get(id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Host id: {id} does not exist in cluster.")
    return host

@app.delete("/cluster/{cluster}/id/{id}", response_class=PlainTextResponse,tags=["cluster"])
def cluster_delete_host(cluster: str, id: str, experiment:str = "experiment",
                        credentials: HTTPBasicCredentials = Depends(security)):
    """
        Deletes the expandable list of hosts provided by the **name** argument, e.g. `name=host[1-10]`.
        """
    cluster = __get_cluster(cluster=cluster,experiment=experiment)
    ids = Parameter.expand(id)
    for host_id in ids:
        cluster.delete(id=host_id)
    return cluster.info()

@app.put("/cluster/{cluster}/id/{id}/activate", response_class=PlainTextResponse,tags=["cluster"])
def cluster_activate_host(cluster: str, id: str,experiment:str = "experiment",
                          credentials: HTTPBasicCredentials = Depends(security)):
    """
    Sets the status of the expandable list of host ids **id** to **active**.
    """
    cluster = __get_cluster(cluster=cluster,experiment=experiment)
    ids = Parameter.expand(id)
    for host_id in ids:
        try:
            host_dict = cluster.get(id=host_id)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Host id: {host_id} does not exist in cluster {cluster.name}.")
        host = Host(**host_dict)
        host.status = 'active'
        cluster.set(host=host)
        Console.info(f'Activating host {host.id} in cluster {cluster.name}')
    return cluster.info()

@app.put("/cluster/{cluster}/id/{id}/deactivate", response_class=PlainTextResponse,tags=["cluster"])
def cluster_deactivate_host(cluster: str, id: str, experiment:str = "experiment",
                            credentials: HTTPBasicCredentials = Depends(security)):
    """
    Sets the status of the expandable list of host ids **id** to **inactive**.
    """
    cluster = __get_cluster(cluster=cluster,experiment=experiment)
    ids = Parameter.expand(id)
    for host_id in ids:
        try:
            host_dict = cluster.get(id=host_id)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Host id: {host_id} does not exist in cluster {cluster.name}.")
        host = Host(**host_dict)
        host.status = 'inactive'
        cluster.set(host=host)
        Console.info(f'Deactivating host {host.id} in cluster {cluster.name}')
    return cluster.info()

@app.put("/cluster/{cluster}/id/{id}/set", response_class=PlainTextResponse,tags=["cluster"])
def cluster_set_host(cluster: str, id: str, key: str, value: str, experiment:str = "experiment",
                     credentials: HTTPBasicCredentials = Depends(security)):
    """
    Sets the **key** of the expandable list of host ids **id** to the value **value**.
    """
    cluster = __get_cluster(cluster=cluster,experiment=experiment)
    ids = Parameter.expand(id)
    for host_id in ids:
        try:
            host_dict = cluster.get(id=host_id)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Host id: {host_id} does not exist in cluster {cluster.name}.")
        host_dict[key] = value
        host = Host(**host_dict)
        cluster.set(host=host)
        Console.info(f'Setting host: {host.id} key: {key} value: {value} in cluster {cluster.name}')
    return cluster.info()