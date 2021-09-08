from fastapi import FastAPI
from cloudmesh.queue.jobqueue import Job
from cloudmesh.common.variables import Variables

#
# BUG: THis does not work for multiple queues
#

app = FastAPI(
    title="Cloudmesh Job: A job queue scheduler for remote/local servers.",
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


@app.queue_get("/queue/{queue}")
def queue_get(queue: str):
    # just a dummy value so we can define the methods
    return {"queue": queue}


@app.queue_list("/queue/")
def queue_list():
    # just a dummy value so we can define the methods
    return {"queue": "list all queues"}


@app.job_get("/queue/{queue}/job/{job}")
def queue_get(queue: str, job: str):
    # just a dummy value so we can define the methods
    return {"queue": queue, "job": job}


@app.job_list("/queue/{queue}/job")
def job_list():
    # just a dummy value so we can define the methods
    return {"queue": queue}


@app.get("/info")
async def info(status=None, name=None):
    variables = Variables()

    queue_name = variables["jobset"]

    jobqueue = JobQueue(name=queue_name)
    if status is None and name is None:
        result = jobqueue.print_jobs()
    elif status is not None:
        result = jobqueue.print_jobs(
            filter_name="status", filter_value=status
        )
    elif name is not None:
        result = jobqueue.print_jobs(
            filter_name="name", filter_value=name
        )

    return result


@app.get("/ps")
async def ps():
    variables = Variables()
    jobqueue = JobQueue(variables["jobset"])

    result = jobqueue.print_jobs(
        filter_name="status", filter_value="submitted"
    )

    return result


@app.get("/run")
async def run(job_name=None):
    variables = Variables()
    jobqueue = JobQueue(variables["jobset"])

    result = jobqueue.run_job(job_name)

    return result


@app.get("/kill")
async def kill(job_name=None):
    variables = Variables()
    jobqueue = JobQueue(variables["jobset"])

    result = jobqueue.kill_job(job_name)

    return result
