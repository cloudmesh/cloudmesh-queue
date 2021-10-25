import subprocess

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from cloudmesh.queue.jobqueue import Queue
from cloudmesh.queue.jobqueue import Cluster
from cloudmesh.queue.jobqueue import Job
from cloudmesh.queue.jobqueue import Host
from cloudmesh.queue.jobqueue import SchedulerFIFO
from cloudmesh.common.variables import Variables
from cloudmesh.common.Shell import Shell
from cloudmesh.common.parameter import Parameter
from cloudmesh.common.console import Console

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


@app.get("/")
async def root():
    return {"message": "Cloudmesh Job Queue Server"}

@app.post("/queue/")
def queue_create(name: str,experiment:str=None):
    if name is None:
        result = "Please provide a queue name"
    queue = Queue(name=name,experiment=experiment)
    return queue

@app.get("/queue/")
def list_queues():
    r = Shell.run('ls ./experiment | grep queue.yaml')
    r = r.splitlines()
    return {"queues": r}

@app.get("/queue/{queue}")
def queue_get(queue: str, experiment: str=None):
    queue = Queue(name=queue)
    return queue

@app.get("/queue/{queue}/info",response_class=PlainTextResponse)
def queue_info(queue: str, experiment: str=None):
    queue = Queue(name=queue)
    return queue.info()


@app.get("/queue/{queue}/job/{job}")
def queue_get_job(queue: str, job: str):
    queue = Queue(name=queue)
    job = queue.get(job)
    return job

@app.put("/queue/{queue}/refresh", response_class=PlainTextResponse)
def queue_refresh(queue: str):
    queue = Queue(name=queue)
    queue.refresh()
    return queue.info()

@app.post("/queue/{queue}",response_class=PlainTextResponse)
def queue_add_job(queue: str, name: str, command: str,input: str=None,output: str=None, \
                  status: str=None, gpu: str=None, user: str=None, host: str=None, \
                  shell: str=None, log: str=None, pyenv: str =None):
    queue = Queue(name=queue)
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
def queue_delete_job(queue: str, name: str):
    queue = Queue(name=queue)
    names = Parameter.expand(name)
    for name in names:
        queue.delete(name=name)
    return queue.info()

@app.put("/queue/{queue}/run_fifo")
def queue_run_fifo(queue: str, max_parallel: int, timeout:int=10):
    #queue run fifo QUEUE [--experiment=EXPERIMENT] --max_parallel=MAX_PARALLEL [--timeout=TIMEOUT]
    #p = subprocess.Popen(['cms', 'queue', 'run', 'fifo', queue,
    #                      f'--max_parallel={max_parallel}',f'--timeout={timeout}'], shell=True)
    p = subprocess.Popen([f'cms queue run fifo {queue} --max_parallel={max_parallel} --timeout={timeout}'], shell=True)
    #p = subprocess.Popen(['cms help'], shell=True)
    return {'result': f'started fifo scheduler: pid {p.pid}'}

@app.put("/queue/{queue}/run_fifo_multi")
def queue_run_fifo_multi(queue: str, cluster: str, timeout:int=10):
    # queue run fifo_multi QUEUE [--experiment=EXPERIMENT] [--hosts=HOSTS] [--hostfile=HOSTFILE] [--timeout=TIMEOUT]
    p = subprocess.Popen([f'cms queue run fifo_multi {queue} --hostfile={cluster} --timeout={timeout}'], shell=True)
    return {'result': f'started fifo scheduler: pid {p.pid}'}

@app.put("/queue/{queue}/reset",response_class=PlainTextResponse)
def queue_reset(queue: str, name: str=None, status:str=None):
    #queue reset QUEUE [--experiment=EXPERIMENT] [--name=NAME] [--status=STATUS]
    queue = Queue(name=queue)
    names = Parameter.expand(name)
    result = queue.reset(keys=names, status=status)
    #return {"result": result.splitlines()}
    return result

@app.post("/cluster/")
def cluster_create(name: str,experiment:str=None):
    if name is None:
        result = "Please provide a cluster name"
    cluster = Cluster(name=name,experiment=experiment)
    #return {"cluster": cluster.to_dict()}
    return cluster

@app.get("/cluster/")
def cluster_list():
    r = Shell.run('ls ./experiment | grep cluster.yaml')
    r = r.splitlines()
    return {"clusters": r}

@app.post("/cluster/{cluster}", response_class=PlainTextResponse)
def cluster_add_host(cluster: str, id: str, name: str,user: str,ip: str=None, \
                  status: str=None, gpu: int=None, pyenv: str=None):
    cluster = Cluster(name=cluster)
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
def cluster_get(cluster: str, experiment: str=None):
    cluster = Cluster(name=cluster)
    #return {"cluster": cluster.to_dict()}
    return cluster

@app.get("/cluster/{cluster}/info", response_class=PlainTextResponse)
def cluster_info(cluster: str, experiment: str=None):
    cluster = Cluster(name=cluster)
    return cluster.info()

@app.get("/cluster/{cluster}/id/{id}")
def cluster_get_host(cluster: str, id: str):
    cluster = Cluster(name=cluster)
    host = cluster.get(id)
    return host

@app.delete("/cluster/{cluster}/id/{id}", response_class=PlainTextResponse)
def cluster_delete_host(cluster: str, id: str):
    cluster = Cluster(name=cluster)
    ids = Parameter.expand(id)
    for host_id in ids:
        cluster.delete(id=host_id)
    return cluster.info()

@app.put("/cluster/{cluster}/id/{id}/activate", response_class=PlainTextResponse)
def cluster_activate_host(cluster: str, id: str):
    cluster = Cluster(name=cluster)
    ids = Parameter.expand(id)
    for host_id in ids:
        host_dict = cluster.get(id=host_id)
        host = Host(**host_dict)
        host.status = 'active'
        cluster.set(host=host)
        Console.info(f'Activating host {host.id} in cluster {cluster.name}')
    return cluster.info()

@app.put("/cluster/{cluster}/id/{id}/deactivate", response_class=PlainTextResponse)
def cluster_deactivate_host(cluster: str, id: str):
    cluster = Cluster(name=cluster)
    ids = Parameter.expand(id)
    for host_id in ids:
        host_dict = cluster.get(id=host_id)
        host = Host(**host_dict)
        host.status = 'inactive'
        cluster.set(host=host)
        Console.info(f'Deactivating host {host.id} in cluster {cluster.name}')
    return cluster.info()

@app.put("/cluster/{cluster}/id/{id}/set", response_class=PlainTextResponse)
def cluster_set_host(cluster: str, id: str, key: str, value: str):
    cluster = Cluster(name=cluster)
    ids = Parameter.expand(id)
    for host_id in ids:
        host_dict = cluster.get(id=host_id)
        host_dict[key] = value
        host = Host(**host_dict)
        cluster.set(host=host)
        Console.info(f'Setting host: {host.id} key: {key} value: {value} in cluster {cluster.name}')
    return cluster.info()