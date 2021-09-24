# Cloudmesh Queue

[![image](https://img.shields.io/travis/TankerHQ/cloudmesh-bar.svg?branch=master)](https://travis-ci.org/TankerHQ/cloudmesn-bar)
[![image](https://img.shields.io/pypi/pyversions/cloudmesh-bar.svg)](https://pypi.org/project/cloudmesh-bar)
[![image](https://img.shields.io/pypi/v/cloudmesh-bar.svg)](https://pypi.org/project/cloudmesh-bar/)
[![image](https://img.shields.io/github/license/TankerHQ/python-cloudmesh-bar.svg)](https://github.com/TankerHQ/python-cloudmesh-bar/blob/main/LICENSE)

The *cloudmesh-job* provides a job queuing and scheduling framework. It 
includes a library as well as a commandline interface. Both
allow users to leverage all the available compute resources to 
perform tasks which have heavy usage of compute power and high execution 
time. A user can configure all available compute resources as 'hosts' in a 
configuration file along with the list of jobs to be executed. Then, based 
on the scheduler policy, user can schedule these jobs on configured hosts. 

# Table of Contents

<!--TOC-->

- [Cloudmesh Job](#cloudmesh-job)
- [Table of Contents](#table-of-contents)
  - [Example](#example)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Available methods](#available-methods)
    - [Hosts](#hosts)
    - [Scheduler](#scheduler)
    - [Jobs](#jobs)
  - [Manual Page](#manual-page)
  - [Tests](#tests)
  - [REST API of `cms job` command](#rest-api-of-cms-job-command)
  - [Alternative Installation and Additional Documentation for Cloudmesh-job](#alternative-installation-and-additional-documentation-for-cloudmesh-job)

<!--TOC-->

## Example

An additional example is documented in

[Example](README-example.md)


## Prerequisites

* Cloudmesh-job uses `ssh` access to the remote compute machine. ssh clients are avalaible on all major platforms including macOS, Linux, Windows.
* It is assumed that you use public keys to authenticate to remote machines. We assume you use ssh-add and/or keychain to avoid issuing passwords when you use the cloudmehs-job
* We do not recommend using passwordless keys as ssh-add and keychain exist to avoid this.
 

## Installation

We assume you have a venv such as ~/ENV in which you have python 3.8 or python 3.9

```bash
(ENV) $ mkdir cm
(ENV) $ cd cm
(ENV) $ pip install cloudmesh-installer
(ENV) $ cloudmesh-installer install job
(ENV) $ cd cloudmesh-job
```


## Configuration

On Windows machines, using `gitbash` to run these commands is advised if a 
Linux like terminal is preferred by users.

The current jobset filename is stored in the cloudmesh variables under the 
variable `jobset`. It can be queried with

```bash
$ cms set jobset
```

It can be set with

```bash
$ cms set jobset=VALUE
```

An example is

```bash
$ cms set jobset
set jobset
jobset='~/.cloudmesh/job/spec.yaml'
```

The content of the jobset can be created using

```bash
cms job template
```

This template configuration will then have the following content:

```yaml
cloudmesh:
  default:
    user: username
  jobset:
    hosts:
      localhost:
        name: localhost
        ip: localhost
        cpus: '2'
        status: free
        job_counter: '2'
        max_jobs_allowed: '1'
      juliet:
        name: juliet
        ip: juliet.futuresystems.org
        cpus: '12'
        status: free
        job_counter: '0'
        max_jobs_allowed: '4'
    scheduler:
      policy: smart
    jobs:
      ls_j:
        name: ls_j
        directory: .
        ip: juliet.futuresystems.org
        input: ./data
        output: ./output/ls_j
        status: ready
        gpu: ' '
        user: username
        arguments: ' '
        executable: 'python test.py'
        shell: bash
        submitted_to_ip: juliet.futuresystems.org
```  

## Available methods
 
### Hosts

To configure available compute resources as 'hosts' in the configuration
file you can use the following command, that will add this new host in the
jobset configuration file.  
To list the hosts we have a convenient list command.

```bash
cms job hosts add --hostname=name --ip=ip --cpus=n --max_jobs_allowed=x
    Adds a host in jobset yaml file.

cms job list hosts
    Enlists all the hosts configured in jobset
```

### Scheduler

One can configure and inquire scheduler a policy
that is used by the `cms job run` command to schedule and 
execute jobs. The following scheduler policies are available:

* sequential - Use first available host
* random     - Use random available host
* smart      - Use a host with highest availability
* frugal     - Use a host with least availability

To confugure or inquire a scheduler, use the following commands:

```bash
cms job scheduler --policy=random
    Assigns policy name to the scheduler policy

cms job scheduler info
    Shows currently configured scheduler policy
```

### Jobs

To schedule, modify and inquire the jobs, please use the following commands:

```bash
cms job info
    Prints location of job queue file.

cms job set '~/.cloudmesh/job/spec.yaml'
    Sets jobset as the FILE provided. Further process refers jobset.

cms job template a.yaml --name="b[0-1]"; less a.yaml
    Creates the jobs b0 and b1 as templates in the jobset.

cms job add --name=z[0-1] --ip=123,345 --executable='ls'
            --input='../data' --output='a,b'
    Creates entries in jobset for jobs z0 and z1 with provided
    arguments.

cms job add '~/.cloudmesh/another.yaml'
    Adds jobs from FILE to jobset

cms job list
    Enlist all jobs

cms job list --name='perform'
    Enlist all jobs with the phrase 'perform' in job name

cms job list --status='ready'
    Enlist all jobs in status 'ready'

cms job status
    Enlists all jobs ordered by their status

cms job reset --name=NAME
    Resets the status of the job to 'ready'.

cms job run --name=ls_j
    Submits job(s) to host decided by the scheduler policy

cms job kill --name=ls_j
    Kills the job

cms job delete --name=ls_j
    Deletes a job from the jobset. If job is in 'submitted'
    status then it is killed first and then deleted from jobset.
``` 

## Manual Page

The abbreviated manual page of the command is

<!--MANUAL-->
```
  job set FILE
  job template [--name=NAME]
  job add FILE
  job add --name=NAME
          [--ip=<IP>]
          [--executable=<EXECUTABLE>]
          [--directory=<DIRECTORY>]
          [--input=<INPUT>]
          [--output=<OUTPUT>]
          [--status=<STATUS>]
          [--gpu=GPU]
          [--user=USER]
          [--arguments=<ARGUMENTS>]
          [--shell=<SHELL>]
  job status
  job list --status=STATUS
  job list --name=NAME
  job list
  job kill [--name=NAME]
  job reset [--name=NAME]
  job delete [--name=NAME]
  job help
  job run [--name=NAME]
  job info
  job hosts add --hostname=hostname --ip=IP  --cpus=N
               [--status=STATUS] [--job_counter=COUNTER]
               [--max_jobs_allowed=<JOBS>]
  job list hosts
  job scheduler --policy=POLICYNAME
  job scheduler info

This command is a job queuing and scheduling framework. It allows
users to leverage all the available compute resources to perform
tasks which have heavy usage of compute power and execution time.

Arguments:
    FILE   a file name

Default value of options is indicated in square brackets.
Options:
  --name=NAME               Job name(s)       Example: 'job[0-5]'
  --ip=<IP>                 Host IP           [default: 127.0.0.1]
  --executable=<EXECUTABLE> Job name          [default: uname]
  --arguments=<ARGUMENTS>   Args for the job  [default:  -a]
  --directory=<DIRECTORY>   Path to run job   [default: .]
  --input=<INPUT>           Input data path   [default: ./data]
  --output=<OUTPUT>         Output path       [default: ./output]
  --status=<STATUS>         Job status        [default: ready]
  --user=USER               Remote host user  Example. $USER
  --shell=<SHELL>           Shell to run job  [default: bash]
  --hostname=hostname       Host name         Example. 'juliet'
  --gpu=GPU                 GPU to use        Example. 7
  --cpus=N             Host CPU count    Example. '12'
  --job_counter=COUNTER     Job count         Example. '2'
  --policy=<POLICYNAME>     Scheduler policy  [default: sequential]
  --max_jobs_allowed=<JOBS> Max jobs allowed  [default: 1]

Description:

    job info
      prints the information for the queued jobs

    job set FILE
      sets the jobset to the file name. All other commands will be
      applied to a jobset

    job add FILE
      adds the jobs in the file to the jobset

    job template
      creates a job template  in the jobset

    job list
      lists all jobs

    job list --status=open
      lists all jobs with a specific status

    job list --name=NAME
      lists teh job with the given name pattern

    job status
      shows the status of all jobs

    job kill --name=NAME
      kills the given jobs base on a name pattern such as
      name[01-04] which would kill all jobs with the given names

    job reset [--name=NAME]
      resets the job to be rerun

    job delete --name=NAME
      deletes the given jobs base on a name pattern such as
      name[01-04] which would kill all jobs with the given names

    job run [--name=NAME]
      Run all jobs from jobset. If --name argument is provided then
      run a specific job

    job hosts add --hostname=name --ip=ip --cpus=n
                 .--max_jobs_allowed=x
      Adds a host in jobset yaml file.

    job list hosts
      Enlists all the hosts configured in jobset

    job scheduler --policy=random
      Assigns policy name to the scheduler policy

    job scheduler info
      Shows currently configured scheduler policy

    job help
      prints the manual page

Job States:

   done   - job completed
   ready  - ready for scheduling
   failed - job failed
   timeout - timeout
   submitted - job submitted to remote machine for execution

Scheduler policies:

   sequential - Use first available host
   random     - Use random available host
   smart      - Use a host with highest availability
   frugal     - Use a host with least availability

Job specification:

   The jobs are specified in 'spec.yaml' file

   name:
     ip: ip of the host
     input: where the input comes form (locally to ip)
     output: where to store the outout (locally to ip)
     status: the status
     gpu: the GPU specification # string such as "0,2" as defined by
          the GPU framework e.g. NVIDIA
     user: the userneme on ip to execute the job
     directory: the working directory
     arguments: the arguments passed along # lis of key values
     executable: the executable
     shell: bash # executes the job in the provided shell
            $(SHELL) will use the default user shell

    The current jobset filename is stored in the cloudmesh variables
    under the variable "jobset". It can be queried with cms set
    jobset. It can be set with

      cms set jobset=VALUE

    We may not even do cms job set VALUE due to this simpler existing
    way of interfacing we can query the variables with

        variables = Variables()

    and also set them that way

      variables["jobset"] = VALUE.

Usage examples:
  cms job info
      Prints location of job queue file.

  cms job set '~/.cloudmesh/job/spec.yaml'
      Sets jobset as the FILE provided. Further process refers jobset.

  cms job template --name="b[0-1]"; less a.yaml
      Creates the jobs b0 and b1 as templates in the jobset.

  cms job add --name=z[0-1] --ip=123,345 --executable='ls'
             .--input='..\data' --output='a,b'
      Creates entries in jobset for jobs z0 and z1 with provided
      arguments.

  cms job add '~/.cloudmesh/another.yaml'
      Adds jobs from FILE to jobset

  cms job list
      Enlist all jobs

  cms job list --name='perform'
      Enlist all jobs with the phrase 'perform' in job name

  cms job list --status='ready'
      Enlist all jobs in status 'ready'

  cms job status
      Enlists all jobs ordered by their status

  cms job reset --name=NAME
      Resets the status of the job to 'ready'.

  cms job hosts add --hostname=name --ip=ip --cpus=n
                   .--max_jobs_allowed=x
      Adds a host in jobset yaml file.

  cms job list hosts
      Enlists all the hosts configured in jobset

  cms job scheduler --policy=random
      Assigns policy name to the scheduler policy

  cms job scheduler info
      Shows currently configured scheduler policy

  cms job run --name=ls_j
      Submits job(s) to host decided by the scheduler policy

  cms job kill --name=ls_j
      Kills the job

  cms job delete --name=ls_j
      Deletes a job from the jobset. If job is in 'submitted'
      status then it is killed first and then deleted from jobset.

```
<!--MANUAL-->


## Tests

We provide two simple pytets that you can customize by setting the host and the
user. The first test checks the usage of the commandline, the second, the
usage of the API.

```bash
$ cms set host='juliet.futuresystems.org'
$ cms set user=$USER

$ pytest -v --capture=no tests/test_01_job_cli.py
$ pytest -v --capture=no tests/test_02_job_api.py
```
- Supporting links 
  - [Pytests](https://github.com/cloudmesh/cloudmesh-job/tree/main/tests)
  - [Pytest results](https://github.com/cloudmesh/cloudmesh-job/tree/main/tests/output)

## REST API of `cms job` command
A REST API is created using FastAPI. This REST API allows users to interact with the 
cloudmesh-job module via a user-friendly interface.

Use following command to start the FastAPI server on localhost:
```bash
(ENV3) $ cms job --service start
```

To launch the REST API from command line, use following command:
```bash
(ENV3) $ cms job --service info
```
This launches the cloudmesh-job API in a browser. The UI is based on OpenAPI:
![cloudmesh-job API](https://github.com/cloudmesh/cloudmesh-job/blob/main/tests/sample_scripts/sample_outputs/API_doc.png)

Documentation of the API is available as below:
![cloudmesh-job API documentation](https://github.com/cloudmesh/cloudmesh-job/blob/main/tests/sample_scripts/sample_outputs/API_redoc.png)



## Alternative Installation and Additional Documentation for Cloudmesh-job

You can safely ignore this section if you installed cloudmehs-job with the previous method.

Please note that several other methods are available which are pointed to in the
installation documentation.

|                           | Links                                                                                  |
| ------------------------- | -------------------------------------------------------------------------------------- |
| Documentation             | <https://github.com/cloudmesh/cloudmesh-job/blob/master/README.md>                     |
| Code                      | <https://github.com/cloudmesh/cloudmesh-job/tree/master/cloudmesh>                     |
| Installation Instructions | <https://github.com/cloudmesh/cloudmesh-job/blob/master/README.md#installation>        |
| Configuration             | <https://github.com/cloudmesh/cloudmesh-job/blob/master/README.md#configuration>       |
| Available methods         | <https://github.com/cloudmesh/cloudmesh-job/blob/master/README.md#available-methods>   |
| Command API               | <https://github.com/cloudmesh/cloudmesh-job/blob/master/README.md#api-of-the-command>  |
| Command description       | <https://github.com/cloudmesh/cloudmesh-job/blob/master/README.md#command-description> |
| Command examples          | <https://github.com/cloudmesh/cloudmesh-job/blob/main/README-example.md>               |

## Start of New Documentation

## Job States

Jobs proceed through various states as they are created, managed by queues and schedulers, and eventually run on worker
host.

The current states are

- **undefined**: this state is a created job that has not been assigned a `user` or a `host`. It is assumed by schedulers that assign jobs to hosts to be ready for execution. This state is not found in `job.log`


- **ready**: this is a job that has been manually assigned or assigned via a scheduler a `host` and `user`. This state is not found in `job.log`
 
 
- **run**: this is a job that has been run with the `job.run()` command. It is a transitionary state to signify the job has been started via a remote shell command, but the script on the executing host may not have logged the `start` state in the `job.log` file. This state is not found in `job.log`.
 
 
- **start**: this is a job that is currently executing on a host. It is written by a script to the `job.log` file.
 
 
- **end**: this is a job that has completed its execution. It is written by the script after completion of the main work. It is found in the `job.log` file.
 
 
- **kill**: this is a job that was killed using the `cms` library. It is in the `job.log` file. Processes killed manually on a host will not exhibit this state.


- **fail_start**: this is a job that failed to start during an execution of `job.run()`, for example a failed name resolution.


- **crash**: this is a job that has been determined to have crashed.
  - In the case that a host is running, the job is in state:`start`, and the pid is no located on the host, then the job can be marked `crash`. This is logged to the `job.log` file.
  - In the case that a host is not responsive, and the job is in state:`start`, then the job can be considered in state `crash`. This case is not logged in `job.log`

## Schedulers

Schedulers are a tool to run and track the execution of jobs in a queue. There are various schedulers with unique behavoirs to meet various workload tasks.

### SchedulerFIFO

This is a simple scheduler that is designed to work on a single host. It executes jobs in a first come first server manner based on their order in the queue yaml file.

#### Usage

**Input:** A queue yaml file, `max_parallel=#`.

`max_parallel` is the maximum number of parallel jobs that will be executed by the host.

**Prerequisite:** All jobs intended to be run must be assigned a `user` and a `host`. Those jobs not assigned a `user` and `host` will be skipped. 

Job assignments are not checked until the queue has reached the job, so the state can be changed after a `queue.run()`, but before a job is considered, but not after a job has already been skipped.

#### Failure considerations

This queue checks for and continues to function in the event of the following failures. When a failure is incurred, the job is skipped and marked with an appropriate status, so the queue can continue to process remaining jobs (if possible).
1. A job that failed to start on a host.
2. A job that crashed on a host.
3. A job that was running on a host that crashed.

#### Recovery from queue manager failure

To recover from a crashed manager that was executing a queue with this scheduler.

1. Recover the manager and determine failure cause.
2. Execute a `queue.refresh()` to get the latest job states from worker hosts.
3. Re-run the queue with `queue.run()`

#### Recovery from queue worker failure

To recover from a failed worker host. 

1. Recover the worker host and determine failure cause. 
2. After reboot this host will continue to run the next `ready` jobs assigned to that host.
3. For any job not in an `end` state assigned to that host, change thier status to `ready` in the quueue file.
4. Stop or let the queue finish its current run.
5. Restart the queue with a `queue.run()`

### SchedulerFIFOMultiHost

This queue is designed to assign a queue of jobs to a list of available hosts in a first come first server manner. Each host can support a differant maximum number of running jobs.

#### Usage

**Input:** A queue yaml file, a `hosts` list of Host() objects.

Jobs are not required to be assigned a 'host' or 'user'. The queue will run all `undefined` and `ready` jobs that are in the queue. `host` and `user` assignemnets in the queue file will be **ignored**. The scheduler will assigne the first available host from `hosts`. 

The jobs are considered in the order they appear in the queue. Their state is not checked until they are considered. If skpped or crashed the job will not be reconsidered. 

#### Failure considerations

This queue checks for and continues to function in the event of the following failures. When a failure is incurred, the job is skipped and marked with an appropriate status, so the queue can continue to process remaining jobs (if possible).
1. A job that failed to start on a host.
2. A job that crashed on a host.
3. A job that was running on a host that crashed.
4. A job will not be assigned to a host that fails a `host.probe()` check.

#### Recovery from queue manager failure

To recover from a crashed manager that was executing a queue with this scheduler.

1. Recover the manager and determine failure cause.
2. Execute a `queue.refresh()` to get the latest job states from worker hosts.
3. Re-run the queue with `queue.run()`

#### Recovery from queue worker failure

To recover from a failed worker host. 

1. Recover the worker host and determine failure cause. 
2. After reboot this host will continue to run the next jobs in the queue to that host.
3. For any job not in an `end` state, change their status to `ready` in the quueue file.
4. Stop or let the queue finish its current run.
5. Restart the queue with a `queue.run()`


