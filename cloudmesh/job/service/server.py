from fastapi import FastAPI
from cloudmesh.job.jobqueue import JobQueue
from cloudmesh.common.variables import Variables

app = FastAPI(
    title="Cloudmesh Job: A job scheduler for remote/local servers.",
    description="""The *cloudmesh-job* provides a job queuing and scheduling 
            framework. It includes a library as well as a commandline interface. 
            Both allow users to leverage all the available compute resources to 
            perform tasks which have heavy usage of compute power and high 
            execution time. A user can configure all available compute resources 
            as 'hosts' in a configuration file along with the list of jobs to be 
            executed. Then, based on the scheduler policy, user can schedule 
            these jobs on configured hosts. """,
    )

@app.get("/")
async def root():
    return {"message": "Cloudmesh Job Server"}

@app.get("/enlist")
async def enlist(status=None, job_name=None):
    variables = Variables()
    jobqueue = JobQueue(variables["jobset"])
    if status == None and job_name == None:
        out = jobqueue.enlist_jobs()
    elif status is not None:
        out = jobqueue.enlist_jobs(
                filter_name="status", filter_value=status
            )
    elif job_name is not None:
        out = jobqueue.enlist_jobs(
                filter_name="name", filter_value=job_name
            )

    return out 

@app.get("/ps")
async def ps():
    variables = Variables()
    jobqueue = JobQueue(variables["jobset"])

    out = jobqueue.enlist_jobs(
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