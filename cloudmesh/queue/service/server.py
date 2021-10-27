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


app = FastAPI(
    title="Cloudmesh Queue: A job queue scheduler for remote/local servers.",
    description="""The `cloudmesh-queue` provides a job queuing and scheduling 
            framework. It includes a library as well as a commandline interface. 
            Both allow users to leverage registered and available compute resources to 
            perform compute intensive tasks with high excution times. 
            A user can configure all available compute resources 
            as 'hosts' in a configuration file along with the list of jobs to be 
            executed. Then, based on the scheduler policy, user can schedule 
            these jobs on configured hosts. """,
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
# user = "user"
# password = "password"

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
    return {"message": "Cloudmesh Queue Server"}

@app.post("/queue/")
def queue_create(name: str,experiment:str=None,credentials: HTTPBasicCredentials = Depends(security)):
    queue = Queue(name=name,experiment=experiment)
    return queue

@app.get("/queue/")
def list_queues(experiment:str=None,credentials: HTTPBasicCredentials = Depends(security)):
    if experiment is None:
        experiment = "experiment"
    r = Shell.run(f'ls ./{experiment} | grep queue.yaml')
    if 'No such file' in r:
        raise HTTPException(status_code=404, detail=f"Directory {experiment} does not exist")
    r = r.splitlines()
    return {"queues": r}

@app.get("/queue/{queue}")
def queue_get(queue: str, experiment: str=None, credentials: HTTPBasicCredentials = Depends(security)):
    queue = __get_queue(queue=queue,experiment=experiment)
    return queue

@app.get("/queue/{queue}/info",response_class=PlainTextResponse)
def queue_info(queue: str, experiment: str=None, credentials: HTTPBasicCredentials = Depends(security)):
    queue = __get_queue(queue=queue,experiment=experiment)
    return queue.info()


@app.get("/queue/{queue}/job/{job}")
def queue_get_job(queue: str, job: str,experiment:str = None, credentials: HTTPBasicCredentials = Depends(security)):
    queue = __get_queue(queue=queue,experiment=experiment)
    try:
        job = queue.get(job)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Job: {job} does not exist in queue.")
    return job

@app.put("/queue/{queue}/refresh", response_class=PlainTextResponse)
def queue_refresh(queue: str,experiment:str = None, credentials: HTTPBasicCredentials = Depends(security)):
    queue = __get_queue(queue=queue,experiment=experiment)
    queue.refresh()
    return queue.info()

@app.post("/queue/{queue}",response_class=PlainTextResponse)
def queue_add_job(queue: str, name: str, command: str,experiment:str = None, input: str=None,output: str=None, \
                  status: str=None, gpu: str=None, user: str=None, host: str=None, \
                  shell: str=None, log: str=None, pyenv: str =None,
                  credentials: HTTPBasicCredentials = Depends(security)):
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

@app.delete("/queue/{queue}/job/{job}",response_class=PlainTextResponse)
def queue_delete_job(queue: str, name: str, experiment:str = None, credentials: HTTPBasicCredentials = Depends(security)):
    queue = __get_queue(queue=queue,experiment=experiment)
    names = Parameter.expand(name)
    for name in names:
        queue.delete(name=name)
    return queue.info()

@app.put("/queue/{queue}/run_fifo")
def queue_run_fifo(queue: str, max_parallel: int, experiment: str = None, timeout:int=10,
                   credentials: HTTPBasicCredentials = Depends(security)):
    #queue run fifo QUEUE [--experiment=EXPERIMENT] --max_parallel=MAX_PARALLEL [--timeout=TIMEOUT]
    queue_obj = __get_queue(queue=queue, experiment=experiment)
    if experiment is not None:
        p = subprocess.Popen([f'cms queue run fifo {queue} --experiment={experiment}'
                              f' --max_parallel={max_parallel} --timeout={timeout}'],
                             shell=True)
    else:
        p = subprocess.Popen([f'cms queue run fifo {queue} --max_parallel={max_parallel} --timeout={timeout}'], shell=True)
    return {'result': f'started fifo scheduler: pid {p.pid}'}

@app.put("/queue/{queue}/run_fifo_multi")
def queue_run_fifo_multi(queue: str, cluster: str, experiment: str = None, timeout:int=10,
                         credentials: HTTPBasicCredentials = Depends(security)):
    # queue run fifo_multi QUEUE [--experiment=EXPERIMENT] [--hosts=HOSTS] [--hostfile=HOSTFILE] [--timeout=TIMEOUT]
    queue_obj = __get_queue(queue=queue, experiment=experiment)
    cluster_obj = __get_cluster(cluster=cluster, experiment=experiment)
    if experiment is not None:
        p = subprocess.Popen([f'cms queue run fifo_multi {queue} --experiment={experiment} '
                              f'--hostfile={cluster} --timeout={timeout}'], shell=True)
    else:
        p = subprocess.Popen([f'cms queue run fifo_multi {queue} --hostfile={cluster} --timeout={timeout}'], shell=True)
    return {'result': f'started fifo_multi scheduler: pid {p.pid}'}

@app.put("/queue/{queue}/reset",response_class=PlainTextResponse)
def queue_reset(queue: str,experiment:str = None, name: str=None, status:str=None,
                credentials: HTTPBasicCredentials = Depends(security)):
    #queue reset QUEUE [--experiment=EXPERIMENT] [--name=NAME] [--status=STATUS]
    queue = __get_queue(queue=queue,experiment=experiment)
    names = Parameter.expand(name)
    result = queue.reset(keys=names, status=status)
    return result

@app.post("/cluster/")
def cluster_create(name: str,experiment:str=None,
                   credentials: HTTPBasicCredentials = Depends(security)):
    cluster = Cluster(name=name,experiment=experiment)
    return cluster

@app.get("/cluster/")
def cluster_list(experiment:str = None, credentials: HTTPBasicCredentials = Depends(security)):
    if experiment is None:
        experiment = 'experiment'
    r = Shell.run(f'ls ./{experiment} | grep cluster.yaml')
    if 'No such file' in r:
        raise HTTPException(status_code=404, detail=f"Directory {experiment} does not exist")
    r = r.splitlines()
    return {"clusters": r}

@app.post("/cluster/{cluster}", response_class=PlainTextResponse)
def cluster_add_host(cluster: str, id: str, name: str,user: str,experiment:str = None, ip: str=None, \
                  status: str=None, gpu: int=None, pyenv: str=None,
                     credentials: HTTPBasicCredentials = Depends(security)):
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

@app.get("/cluster/{cluster}")
def cluster_get(cluster: str, experiment:str = None,
                credentials: HTTPBasicCredentials = Depends(security)):
    cluster = __get_cluster(cluster=cluster,experiment=experiment)
    #return {"cluster": cluster.to_dict()}
    return cluster

@app.get("/cluster/{cluster}/info", response_class=PlainTextResponse)
def cluster_info(cluster: str, experiment:str = None,
                 credentials: HTTPBasicCredentials = Depends(security)):
    cluster = __get_cluster(cluster=cluster,experiment=experiment)
    return cluster.info()

@app.get("/cluster/{cluster}/id/{id}")
def cluster_get_host(cluster: str, id: str,experiment:str = None,
                     credentials: HTTPBasicCredentials = Depends(security)):
    cluster = __get_cluster(cluster=cluster,experiment=experiment)
    try:
        host = cluster.get(id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Host id: {id} does not exist in cluster.")
    return host

@app.delete("/cluster/{cluster}/id/{id}", response_class=PlainTextResponse)
def cluster_delete_host(cluster: str, id: str, experiment:str = None,
                        credentials: HTTPBasicCredentials = Depends(security)):
    cluster = __get_cluster(cluster=cluster,experiment=experiment)
    ids = Parameter.expand(id)
    for host_id in ids:
        cluster.delete(id=host_id)
    return cluster.info()

@app.put("/cluster/{cluster}/id/{id}/activate", response_class=PlainTextResponse)
def cluster_activate_host(cluster: str, id: str,experiment:str = None,
                          credentials: HTTPBasicCredentials = Depends(security)):
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

@app.put("/cluster/{cluster}/id/{id}/deactivate", response_class=PlainTextResponse)
def cluster_deactivate_host(cluster: str, id: str, experiment:str = None,
                            credentials: HTTPBasicCredentials = Depends(security)):
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

@app.put("/cluster/{cluster}/id/{id}/set", response_class=PlainTextResponse)
def cluster_set_host(cluster: str, id: str, key: str, value: str, experiment:str = None,
                     credentials: HTTPBasicCredentials = Depends(security)):
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