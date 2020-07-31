Documentation
=============
[![image](https://img.shields.io/travis/TankerHQ/cloudmesh-bar.svg?branch=master)](https://travis-ci.org/TankerHQ/cloudmesn-bar)
[![image](https://img.shields.io/pypi/pyversions/cloudmesh-bar.svg)](https://pypi.org/project/cloudmesh-bar)
[![image](https://img.shields.io/pypi/v/cloudmesh-bar.svg)](https://pypi.org/project/cloudmesh-bar/)
[![image](https://img.shields.io/github/license/TankerHQ/python-cloudmesh-bar.svg)](https://github.com/TankerHQ/python-cloudmesh-bar/blob/master/LICENSE)

# Cloudmesh Job

{warning}

{icons}

The 'Job' library of Cloudmesh is a job queuing and scheduling framework. This
 library allows users to leverage all the available compute resources to 
 perform tasks which have heavy usage of compute power and execution time.
 A user can configure all available compute resources as 'hosts' in a 
 configuration file along with the list of jobs to be executed. Then, based 
 on the scheduler policy, user can schedule these jobs on configured hosts. 
 
## Installation and Documentation

Please note that several methods are available which are pointed to in the
installation documentation.

|  | Links |
|---------------|-------|
| Documentation | <https://github.com/cloudmesh/cloudmesh-job/blob/master/README.md> |
| Code | <https://github.com/cloudmesh/cloudmesh-job/tree/master/cloudmesh> |
| Installation Instructions | <https://github.com/cloudmesh/cloudmesh-job/blob/master/README.md#installation> |
| Configuration | <> |
| Available methods | <> |
| Command API | <> |
| Command description | <> |

## Installation

```bash
$ git clone https://github.com/cloudmesh/cloudmesh-job
$ cd cloudmesh-job
$ pip install .
```

*Assumptions:*  
*1. User has completed cloudmesh-common setup in the machine*
 
This library contains a number of functions and APIs that we highlight
here. They are used for configuration and execution of jobs in available 
compute resources.

## Configuration

The current jobset filename is stored in the cloudmesh variables under the 
variable "jobset". It can be queried with cms set jobset. It can be set with 
cms set jobset=VALUE. 

```bash
~ cms set jobset
set jobset
jobset='~\.cloudmesh\job\spec.yaml'
```

Content of the jobset can be created using `cms job template` (Refer API of 
the command.). This configuration file has following content:

```yaml
cloudmesh:
  default:
    user: username
  hosts:
    localhost:
      name: localhost
      ip: localhost
      cpu_count: '2'
      status: free
      job_counter: '2'
    juliet:
      name: juliet
      ip: juliet.futuresystems.org
      cpu_count: '12'
      status: free
      job_counter: '0'
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
Api to configure available compute resources as 'hosts' in the configuration 
file.  
```bash
    cms job hosts add --hostname=name --ip=ip --cpu_count=n
        Adds a host in jobset yaml file.

    cms job list hosts
        Enlists all the hosts configured in jobset
```

### Scheduler
API to inquire and configure a scheduler policy which is used by the `cms 
job run` command to schedule and execute jobs.  
Available scheduler policies:

* sequential - Use first available host
* random     - Use random available host
* smart      - Use a host with highest availability
* frugal     - Use a host with least availability

```bash
    cms job scheduler --policy=random
        Assigns policy name to the scheduler policy

    cms job scheduler info
        Shows currently configured scheduler policy
```

### Jobs
API and to inquire, modify and schedule jobs from the configuration file. 

```bash
    cms job info
        Prints location of job queue file.

    cms job set '~/.cloudmesh/job/spec.yaml'
        Sets jobset as the FILE provided. Further process refers jobset.

    cms job template a.yaml --name="b[0-1]"; less a.yaml
        Creates the jobs b0 and b1 as templates in the jobset.

    cms job add --name=z[0-1] --ip=123,345 --executable='ls'
    --input='..\data' --output='a,b'
        Creates entries in jobset for jobs z0 and z1 with provided
        arguments.

    cms job add '~\.cloudmeshnother.yaml'
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


## API of the command
```bash
  Usage:
    job set FILE
    job template [--name=NAME]
    job add FILE
    job add --name=NAME
            --ip=IP
            --executable=EXECUTABLE
            [--directory=DIRECTORY]
            [--input=INPUT]
            [--output=OUTPUT]
            [--status=STATUS]
            [--gpu=GPU]
            [--user=USER]
            [--arguments=ARGUMENTS]
            [--shell=SHELL]
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
    job hosts add --hostname=hostname --ip=IP --cpu_count=N
                 [--status=STATUS] [--job_counter=COUNTER]
    job list hosts
    job scheduler --policy=POLICYNAME
    job scheduler info

  This command is a job queuing and scheduling framework. It allows users to 
  leverage all the available compute resources to perform tasks which have heavy 
  usage of compute power and execution time.

  Arguments:
      FILE   a file name

  Options:
      name=NAME               Name(s) of jobs.        Ex: 'job[0-5]'  [default: None]
      ip=IP                   IP of the host.         Ex: 127.0.0.1   [default: None]
      executable=EXECUTABLE   The command to be run.  Ex. 'ls'        [default: None]
      directory=DIRECTORY     Location to run job.    Ex. './'        [default: './']
      input=INPUT             Location of input data. Ex. './data'    [default: './data']
      output=OUTPUT           Location of outputs.    Ex. './output'  [default: './output/job_name']
      status=STATUS           Status of the job.      Ex. 'ready'     [default: 'ready']
      gpu=GPU                 Which GPU to use.       Ex. 7           [default: None]
      user=USER               User on remote host     Ex. 'uname'     [default: {System user}]
      arguments=ARGUMENTS     Args for the executable.Ex. '-lisa'     [default: None]
      shell=SHELL             Shell to run job.       Ex. 'bash'      [default: 'bash']
      hostname=hostname       Host name.              Ex. 'juliet'    [default: None]
      cpu_count=N             CPU count of the host.  Ex. '12'        [default: None]
      job_counter=COUNTER     Number of submitted jobsEx. '2'         [default: None]
      policy=POLICYNAME       Scheduler policy.       Ex. 'smart'     [default: 'sequential']
```

## Command description

```bash
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

      job status [--name=NAME] [--status=STATUS]
        sets the status of all jobs to the status

      job reset [--name=NAME]
        resets the job to be rerun

      job delete --name=NAME
        deletes the given jobs base on a name pattern such as
        name[01-04] which would kill all jobs with the given names

      job run [--name=NAME]
        Run all jobs from jobset. If --name argument is provided then
        run a specific job

      job hosts add --hostname=name --ip=ip --cpu_count=n
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

  The current jobset filename is stored in the cloudmesh variables under
  the variable "jobset". It can be queried with cms set jobset. It
  can be set with cms set jobset=VALUE.
  We may not even do cms job set VALUE due to this simpler existing way
  of interfacing we can query the variables with variables = Variables()
  and also set them that way variables["jobset"] = VALUE.
```

## Scope and Limitations

* Command assumes `ssh` access to the remote compute machine.
* If command is to be run on local machine, then `ssh` permission to local 
machine is needed.
* Cloudmesh-common module should be installed. 
