from fastapi import FastAPI
from cloudmesh.queue.jobqueue import JobQueue
from cloudmesh.common.variables import Variables

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

@app.get("/print")
async def print(status=None, job_name=None):
    variables = Variables()

    name = variables["jobset"]

    jobqueue = JobQueue(name=name)
    if status == None and job_name == None:
        out = jobqueue.print_jobs()
    elif status is not None:
        out = jobqueue.print_jobs(
                filter_name="status", filter_value=status
            )
    elif job_name is not None:
        out = jobqueue.print_jobs(
                filter_name="name", filter_value=job_name
            )

    return out 

@app.get("/ps")
async def ps():
    variables = Variables()
    jobqueue = JobQueue(variables["jobset"])

    out = jobqueue.print_jobs(
                filter_name="status", filter_value="submitted"
            )

    return out 

@app.get("/run")
async def run(job_name=None):
    variables = Variables()
    jobqueue = JobQueue(variables["jobset"])

    out = jobqueue.run_job(job_name)

    return out 


@app.get("/kill")
async def kill(job_name=None):
    variables = Variables()
    jobqueue = JobQueue(variables["jobset"])

    out = jobqueue.kill_job(job_name)

    return out 