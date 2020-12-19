# Demo of `cms job` in Windows, Linux, and macOS

# Table of Contents

<!--TOC-->

- [Demo of `cms job` in Windows, Linux, and macOS](#demo-of-cms-job-in-windows-linux-and-macos)
- [Table of Contents](#table-of-contents)
  - [Notation](#notation)
  - [Instalation and activation on Windows](#instalation-and-activation-on-windows)
  - [Setting up location of config file](#setting-up-location-of-config-file)
  - [Verification of config file location in `cms job`](#verification-of-config-file-location-in-cms-job)
  - [Creating a template of configuration file](#creating-a-template-of-configuration-file)
  - [Adding a new job in configuration file from another yaml file](#adding-a-new-job-in-configuration-file-from-another-yaml-file)
  - [Adding a new job using command line arguments](#adding-a-new-job-using-command-line-arguments)
  - [Enlisting configured jobs](#enlisting-configured-jobs)
    - [Enlist all jobs](#enlist-all-jobs)
    - [Enlist jobs with particular status](#enlist-jobs-with-particular-status)
    - [Enlist jobs with certain pattern in the job name](#enlist-jobs-with-certain-pattern-in-the-job-name)
    - [Enlist jobs sorted on job status](#enlist-jobs-sorted-on-job-status)
  - [Submit a job for execution on remote host](#submit-a-job-for-execution-on-remote-host)
    - [Execution of `job run` on the local machine](#execution-of-job-run-on-the-local-machine)
    - [Outputs on remote host](#outputs-on-remote-host)
    - [Python script used for testing](#python-script-used-for-testing)
  - [Kill a job on remote host](#kill-a-job-on-remote-host)
    - [Execution on local machine](#execution-on-local-machine)
    - [Remote machine](#remote-machine)
    - [Verify status of the killed job](#verify-status-of-the-killed-job)
  - [Reset status and rerun a job](#reset-status-and-rerun-a-job)
  - [Delete a job from configuration file](#delete-a-job-from-configuration-file)
  - [Remote host management](#remote-host-management)
    - [Configure a new host](#configure-a-new-host)
  - [Enlist hosts](#enlist-hosts)
  - [Job scheduler management](#job-scheduler-management)
    - [Find out currently configured scheduler](#find-out-currently-configured-scheduler)
    - [Re-configure the scheduler](#re-configure-the-scheduler)

<!--TOC-->


This document demonstrates all the functionalities made available by the 
command `cms job`. The document runs through available commands by showing 
sequence of execution and corresponding outputs on local Windows machine and 
a remote Linux host. 

## Notation

For better readability some lines in this documentation have been split over
multiple lines. Please adjust when issuing the commands.

The continuation character is "^" for Windows command prompt, whereas it is 
"\\" on Linux. The continuation character should be added at the end of the 
line to split a command in multiple lines.

This demonstration is done using Windows command prompt. Using `gitbash` is
advised if a Linux like terminal is preferred by users.

We use the prompt `$` in the documentation. This may be looking a bit different on your terminal dependent which one you use. We have the following differences

* Windows CMD.EXE: Instead of $ you will see `C:\>` amd once you activated `ENV3` it will look like `(ENV3) C:\>`
* zsh: typically you will see a %
* bash: typically you will see a $

On Windows you can also use gitbash which gives you teh equivalent of a bash shell in Windows. We recommend using it, but you still can use CMD.EXE or even powershell.

Due to the universality we will simplify our documentation and only use `$` as prompt indicator.


## Installation a venv on Linux, macOS, gitbash on WIndows

```bash
$ python3 -m venv ~/ENV3
```

Whenever you start a new terminal, you need to activate the the ENV3

```console
$ source ~/ENV3/bin/activate
```

## Installation a venv on Windows CMD.EXE

Create a venv using python 3.8 or python 3.9 as `ENV3`

```cmd
C:\>python -m venv ENV3

Whenever you start a new terminal, you need to activate the the ENV3
```cmd
C:\>ENV3\Scripts\activate.bat
```

From now on we will use `(ENV3) $` indicating `(ENV3) C:\>`

## Installation of cloudmesh-job

After you installed and activated your venv
You need to install after the first activation the software as follows

```console
(ENV3) $ mkdir cm
(ENV3) $ cd cm
(ENV3) $ pip install cloudmesh-installer
(ENV3) $ cloudmesh-installer install jobs
```

## Setting up location of config file

Use `cms job set` to configure location of the configuration file with name 
`jobset`. In this example file `spec.yaml` is used as the configuration file.

```console
(ENV3) $ cms job set '~/.cloudmesh/job/spec.yaml'
Jobset defined as spec located at ~\.cloudmesh\job\spec.yaml

(ENV3) $ cms set jobset
jobset='~\.cloudmesh\job\spec.yaml'
```

## Verification of config file location in `cms job` 

```cmd
(ENV3) $ cms job info
Jobs are defined in: ~\.cloudmesh\job\spec.yaml
```

## Creating a template of configuration file

Command `cms job template` can be used to create a sample configuration file:

```
(ENV3) $ cms job template --name=job[1-2]
Jobs are defined in: ~\.cloudmesh\job\spec.yaml
```

This generates following content in ~\.cloudmesh\job\spec.yaml. Please note
this command **replaces existing spec.yaml file** with default content.

```yaml
cloudmesh:
  default:
    user: keTan
  jobset:
    hosts:
      localhost:
        name: DESKTOP-HUC37G2
        ip: 127.0.0.1
        cpu_count: 4
        status: free
        job_counter: 0
    scheduler:
      policy: sequential
    jobs:
      job1:
        name: job1
        directory: .
        ip: 127.0.0.1
        input: .
        output: .
        status: ready
        gpu: ''
        user: keTan
        arguments: -lisa
        executable: ls
        shell: bash
      job2:
        name: job2
        directory: .
        ip: 127.0.0.1
        input: .
        output: .
        status: ready
        gpu: ''
        user: keTan
        arguments: -lisa
        executable: ls
        shell: bash
```

## Adding a new job in configuration file from another yaml file

The command `cms job add FILENAME` allows user to add job(s) from a yaml file
to the configuration file. Jobs from the yaml file are appended to the list
of existing jobs.
 
For the demo purpose, a new yaml file called `new.yaml` is created with 
following content:

```yaml
ls_juliet:
  name: ls_juliet
  directory: cm
  ip: juliet.futuresystems.org
  input: ../data
  output: ./output/ls_juliet
  status: ready
  gpu: ' '
  user: ketanp
  arguments: -lisa; bash
  executable: ls
  shell: bash
  host: null
```

Execution of `cms job add FILENAME` adds this job to the configured list of 
jobs:

Enlist currently configured jobs:

```cmd
(ENV3) $ cms job list
+--------+------------+-----------+-----------+---------+-----------+-------+
| Number | JobName    | JobStatus | RemoteIp  | Command | Arguments | User  |
+--------+------------+-----------+-----------+---------+-----------+-------+
| 1      | job1       | ready     | 127.0.0.1 | ls      | -lisa     | keTan |
| 2      | job2       | ready     | 127.0.0.1 | ls      | -lisa     | keTan |
| 3      | pytest_job | ready     | local     | ls      | -lisa     | user  |
+--------+------------+-----------+-----------+---------+-----------+-------+
```

Adding the job from `new.yaml` and checking list of jobs:

```cmd
(ENV3) $ cms job add '~/.cloudmesh/job/new.yaml'

(ENV3) $ cms job list
+--------+------------+-----------+--------------------------+---------+-------------+--------+
| Number | JobName    | JobStatus | RemoteIp                 | Command | Arguments   | User   |
+--------+------------+-----------+--------------------------+---------+-------------+--------+
| 1      | job1       | ready     | 127.0.0.1                | ls      | -lisa       | keTan  |
| 2      | job2       | ready     | 127.0.0.1                | ls      | -lisa       | keTan  |
| 3      | pytest_job | ready     | local                    | ls      | -lisa       | user   |
| 4      | ls_juliet  | ready     | juliet.futuresystems.org | ls      | -lisa; bash | ketanp |
+--------+------------+-----------+--------------------------+---------+-------------+--------+ 
```

## Adding a new job using command line arguments

Command `cms job add` also allows users to add a new job in the list of 
configured jobs from command line:
Please note `\` is the continuation character in Windows command prompt.

```cmd
(ENV3) $ cms job add --name='sample'                 \
                       --ip=localhost                  \
                       --executable='python sample.py' \
                       --arguments='--gpu=7'           \
                       --directory='./scripts'         \
                       --input='./data'                \
                       --output='./output'             \
                       --status='ready'

(ENV3) $ cms job list
+--------+------------+-----------+--------------------------+------------------+-------------+--------+
| Number | JobName    | JobStatus | RemoteIp                 | Command          | Arguments   | User   |
+--------+------------+-----------+--------------------------+------------------+-------------+--------+
| 1      | job1       | ready     | 127.0.0.1                | ls               | -lisa       | keTan  |
| 2      | job2       | ready     | 127.0.0.1                | ls               | -lisa       | keTan  |
| 3      | pytest_job | ready     | local                    | ls               | -lisa       | user   |
| 4      | ls_juliet  | ready     | juliet.futuresystems.org | ls               | -lisa; bash | ketanp |
| 5      | sample     | ready     | localhost                | python sample.py | --gpu=7     | keTan  |
+--------+------------+-----------+--------------------------+------------------+-------------+--------+
```

## Enlisting configured jobs

Command `cms job list` allows users to enlist all the jobs configured in the 
configuration file. This job also shows some basic details of these jobs such
as job name, job status, executable, remote host IP and the user.
There are few variations of this command as follows:

### Enlist all jobs

```cmd
(ENV3) $ cms job list
+--------+-------------+-----------+--------------------------+------------------+-------------+--------+
| Number | JobName     | JobStatus | RemoteIp                 | Command          | Arguments   | User   |
+--------+-------------+-----------+--------------------------+------------------+-------------+--------+
| 1      | job1        | ready     | 127.0.0.1                | ls               | -lisa       | keTan  |
| 2      | job2        | ready     | 127.0.0.1                | ls               | -lisa       | keTan  |
| 3      | pytest_job  | ready     | local                    | ls               | -lisa       | user   |
| 4      | ls_juliet   | submitted | juliet.futuresystems.org | ls               | -lisa; bash | ketanp |
| 5      | sample      | killed    | localhost                | python sample.py | --gpu=7     | keTan  |
| 6      | pytest_job1 | ready     | localhost                | python sample.py | --gpu=7     | keTan  |
+--------+-------------+-----------+--------------------------+------------------+-------------+--------+
```

### Enlist jobs with particular status

```cmd
(ENV3) $ cms job list --status='submitted'
+--------+-----------+-----------+--------------------------+---------+-------------+--------+
| Number | JobName   | JobStatus | RemoteIp                 | Command | Arguments   | User   |
+--------+-----------+-----------+--------------------------+---------+-------------+--------+
| 1      | ls_juliet | submitted | juliet.futuresystems.org | ls      | -lisa; bash | ketanp |
+--------+-----------+-----------+--------------------------+---------+-------------+--------+
```

### Enlist jobs with certain pattern in the job name

The shown command searches the word 'pytest' in 'JobName' and enlists matching jobs.

```cmd
(ENV3) $ cms job list --name='pytest'
+--------+-------------+-----------+-----------+------------------+-----------+-------+
| Number | JobName     | JobStatus | RemoteIp  | Command          | Arguments | User  |
+--------+-------------+-----------+-----------+------------------+-----------+-------+
| 1      | pytest_job  | ready     | local     | ls               | -lisa     | user  |
| 2      | pytest_job1 | ready     | localhost | python sample.py | --gpu=7   | keTan |
+--------+-------------+-----------+-----------+------------------+-----------+-------+
```

### Enlist jobs sorted on job status

This command outputs list of jobs sorted on the 'JobStatus'.

```cmd
(ENV3) $ cms job status
+--------+-------------+-----------+--------------------------+------------------+-------------+--------+
| Number | JobName     | JobStatus | RemoteIp                 | Command          | Arguments   | User   |
+--------+-------------+-----------+--------------------------+------------------+-------------+--------+
| 5      | sample      | killed    | localhost                | python sample.py | --gpu=7     | keTan  |
| 1      | job1        | ready     | 127.0.0.1                | ls               | -lisa       | keTan  |
| 2      | job2        | ready     | 127.0.0.1                | ls               | -lisa       | keTan  |
| 3      | pytest_job  | ready     | local                    | ls               | -lisa       | user   |
| 6      | pytest_job1 | ready     | localhost                | python sample.py | --gpu=7     | keTan  |
| 4      | ls_juliet   | submitted | juliet.futuresystems.org | ls               | -lisa; bash | ketanp |
+--------+-------------+-----------+--------------------------+------------------+-------------+--------+
```  

## Submit a job for execution on remote host

### Execution of `job run` on the local machine

The `cms job run` command submits a job on a configured host.
All the details of the host and the command are taken from the 
`JobSet` configured in earlier steps.  
This step needs `ssh` access from users local machine to the 
remote host.  

```cmd
(ENV3) $ cms job run --name=test_juliet
```

### Outputs on remote host

Logs and outputs are generated in the remote host as per the 
code present in the job to be run in the remote. In this example
contents of `test.log` is shown. The PID of the job is 
captured in `test_juliet_pid.log`

```cmd
[ketanp@j-login1 test_juliet]$ pwd
/N/u/ketanp/output/test_juliet

[ketanp@j-login1 test_juliet]$ cat test.log
2020-08-02 03:45:04,662|test.py|DEBUG|Preparing debug logs.
2020-08-02 03:45:04,662|test.py|DEBUG|Arguments passed:
2020-08-02 03:45:04,662|test.py|DEBUG|{'--gpu': '7',
 '--input': './data',
 '--output': './output/test_juliet'}
2020-08-02 03:45:04,662|test.py|DEBUG|Starting the py script.
2020-08-02 03:45:04,662|test.py|DEBUG|Processing sleep 20
2020-08-02 03:45:24,682|test.py|DEBUG|complete
2020-08-02 03:45:24,683|test.py|DEBUG|Processing another sleep 20
2020-08-02 03:45:44,690|test.py|DEBUG|complete
2020-08-02 03:45:44,690|test.py|DEBUG|End of the script

[ketanp@j-login1 test_juliet]$ cat test_juliet_pid.log
11092

[ketanp@j-login1 test_juliet]$

```

### Python script used for testing

```python
from __future__ import print_function
import time, sys
from docopt import docopt
import logging

usage="""
Usage:
    test.py --output=OUTPUT --input=INPUT --gpu=GPU

Options:
    --output=OUTPUT    Location of script output
    --input=INPUT      Location of inputs
    --gpu=GPU          GPU to be used for script execution
"""
arguments = docopt(usage)

out_dir = arguments.get('--output')
in_dir = arguments.get('--input')
gpu = arguments.get('--gpu')

logging.basicConfig(filename='{}/test.log'.format(out_dir),
                    level=logging.DEBUG,
                    format='%(asctime)s|%(filename)s|%(levelname)s|%(message)s')

logging.debug("Preparing debug logs.")


logging.debug("Arguments passed: ")
logging.debug(arguments)

logging.debug("Starting the py script.")

logging.debug("Processing sleep 20")

time.sleep(20)
logging.debug("complete")

logging.debug("Processing another sleep 20")
time.sleep(20)
logging.debug("complete")

logging.debug("End of the script")
```

## Kill a job on remote host

### Execution on local machine 

Execution of a job on remote host can be stopped by using
`job kill` command. This command connects to to remote host
and kills the job using the PID stored by `job run` command.
This step changes the status of the job to `killed`.

```cmd
(ENV3) $ cms job run --name=test_juliet

(ENV3) $ cms job kill --name=test_juliet
```

### Remote machine

Following code to monitor execution of job `test.py` on the 
remote host. We run an infinite loop to verify execution of
`test.py`. These steps show that execution of the job starts 
after running `job run` and the job is killed with `job kill`.

```bash
[ketanp@j-login1 test_juliet]$ while [ 1 == 1 ];
> do
> ps -ef | grep 'test.py'
> echo "======================================="
> sleep 3
> done
ketanp   18170  3720  0 04:43 pts/8    00:00:00 grep --color=auto test.py
=======================================
ketanp   18173  3720  0 04:43 pts/8    00:00:00 grep --color=auto test.py
=======================================
ketanp   18182  3720  0 04:43 pts/8    00:00:00 grep --color=auto test.py
=======================================
ketanp   18185 18183  0 04:43 ?        00:00:00 bash -c cd ./;sh -c 'echo $$ > ./output/test_juliet/test_juliet_pid.log;
exec python test.py --input=./data --output=./output/test_juliet --gpu=7'
ketanp   18214 18185  0 04:43 ?        00:00:00 python test.py --input=./data --output=./output/test_juliet --gpu=7
ketanp   18216  3720  0 04:43 pts/8    00:00:00 grep --color=auto test.py
=======================================
ketanp   18185 18183  0 04:43 ?        00:00:00 bash -c cd ./;sh -c 'echo $$ > ./output/test_juliet/test_juliet_pid.log;
exec python test.py --input=./data --output=./output/test_juliet --gpu=7'
ketanp   18214 18185  0 04:43 ?        00:00:00 python test.py --input=./data --output=./output/test_juliet --gpu=7
ketanp   18219  3720  0 04:43 pts/8    00:00:00 grep --color=auto test.py
=======================================
ketanp   18185 18183  0 04:43 ?        00:00:00 bash -c cd ./;sh -c 'echo $$ > ./output/test_juliet/test_juliet_pid.log;
exec python test.py --input=./data --output=./output/test_juliet --gpu=7'
ketanp   18214 18185  0 04:43 ?        00:00:00 python test.py --input=./data --output=./output/test_juliet --gpu=7
ketanp   18231  3720  0 04:43 pts/8    00:00:00 grep --color=auto test.py
=======================================
ketanp   18185 18183  0 04:43 ?        00:00:00 bash -c cd ./;sh -c 'echo $$ > ./output/test_juliet/test_juliet_pid.log;
exec python test.py --input=./data --output=./output/test_juliet --gpu=7'
ketanp   18214 18185  0 04:43 ?        00:00:00 python test.py --input=./data --output=./output/test_juliet --gpu=7
ketanp   18237  3720  0 04:43 pts/8    00:00:00 grep --color=auto test.py
=======================================
ketanp   18276  3720  0 04:43 pts/8    00:00:00 grep --color=auto test.py
=======================================
ketanp   18279  3720  0 04:43 pts/8    00:00:00 grep --color=auto test.py
=======================================
```

### Verify status of the killed job

Verify that the status of the job changes to `killed` with `job list`

```cmd
(ENV3) $ cms job list --name='juliet'
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+
| Number | JobName     | JobStatus | RemoteIp                 | Command        | Arguments                                        | User   |
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+
| 1      | test_juliet | killed    | juliet.futuresystems.org | python test.py | --input=./data --output=./output/test_juliet     | ketanp |
|        |             |           |                          |                | --gpu=7                                          |        |
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+
```

## Reset status and rerun a job

The command `job reser` allows us to reset status of a killed job
and rerun the job on remote host. To achive this, we first confirm 
that the job is in killed status, then run the command `job reset`
which changes the status of the job to `ready` and then we can 
submit this job for remote execution using `job run`.

```cmd
(ENV3) $ cms job list --name='juliet'
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+
| Number | JobName     | JobStatus | RemoteIp                 | Command        | Arguments                                        | User   |
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+
| 1      | test_juliet | killed    | juliet.futuresystems.org | python test.py | --input=./data --output=./output/test_juliet     | ketanp |
|        |             |           |                          |                | --gpu=7                                          |        |
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+


(ENV3) $ cms job reset --name='test_juliet'
Status reset for job test_juliet.


(ENV3) $ cms job list --name='juliet'
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+
| Number | JobName     | JobStatus | RemoteIp                 | Command        | Arguments                                        | User   |
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+
| 1      | test_juliet | ready     | juliet.futuresystems.org | python test.py | --input=./data --output=./output/test_juliet     | ketanp |
|        |             |           |                          |                | --gpu=7                                          |        |
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+


(ENV3) $ cms job run --name=test_juliet


(ENV3) $ cms job list --name='juliet'
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+
| Number | JobName     | JobStatus | RemoteIp                 | Command        | Arguments                                        | User   |
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+
| 1      | test_juliet | submitted | juliet.futuresystems.org | python test.py | --input=./data --output=./output/test_juliet     | ketanp |
|        |             |           |                          |                | --gpu=7                                          |        |
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+
``` 

## Delete a job from configuration file

Command `cms job delete` provides an ability to users to delete a job from 
the configuration file. The delete operation first kills a job if it is in 
`submitted` status and then deletes it from the job set.

- Checking existing list of jobs:

```bash
(ENV3) $ cms job list
+--------+-------------+-----------+--------------------------+------------------+--------------------------------------------------+--------+
| Number | JobName     | JobStatus | RemoteIp                 | Command          | Arguments                                        | User   |
+--------+-------------+-----------+--------------------------+------------------+--------------------------------------------------+--------+
| 1      | job1        | ready     | 127.0.0.1                | ls               | -lisa                                            | keTan  |
| 2      | job2        | ready     | 127.0.0.1                | ls               | -lisa                                            | keTan  |
| 3      | pytest_job  | ready     | local                    | ls               | -lisa                                            | user   |
| 4      | test_juliet | submitted | juliet.futuresystems.org | python test.py   | --input=./data --output=./output/test_juliet     | ketanp |
|        |             |           |                          |                  | --gpu=7                                          |        |
| 5      | sample      | killed    | localhost                | python sample.py | --gpu=7                                          | keTan  |
| 6      | pytest_job1 | submitted | juliet.futuresystems.org | ls               | -lisa                                            | ketanp |
+--------+-------------+-----------+--------------------------+------------------+--------------------------------------------------+--------+
```
- Deleting `sample` job and checking the list again

```bash
(ENV3) $ cms job delete --name=sample


(ENV3) $ cms job list
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+
| Number | JobName     | JobStatus | RemoteIp                 | Command        | Arguments                                        | User   |
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+
| 1      | job1        | ready     | 127.0.0.1                | ls             | -lisa                                            | keTan  |
| 2      | job2        | ready     | 127.0.0.1                | ls             | -lisa                                            | keTan  |
| 3      | pytest_job  | ready     | local                    | ls             | -lisa                                            | user   |
| 4      | test_juliet | submitted | juliet.futuresystems.org | python test.py | --input=./data --output=./output/test_juliet     | ketanp |
|        |             |           |                          |                | --gpu=7                                          |        |
| 5      | pytest_job1 | submitted | juliet.futuresystems.org | ls             | -lisa                                            | ketanp |
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+
```


## Remote host management

### Configure a new host 
Command `cms job hosts` facilitates configuration of remote hosts in the 
configuration file. 


```bash
(ENV3) $ cms job hosts add --hostname='juliet' \
                             --ip='juliet.futuresystems.org' \
                             --cpu_count='12'
```
Checking content of the .yaml file manually
```yaml
  hosts:
    localhost:
      name: DESKTOP-HUC37G2
      ip: 127.0.0.1
      cpu_count: 4
      status: free
      job_counter: '0'
    juliet:
      name: juliet
      ip: juliet.futuresystems.org
      cpu_count: '12'
      status: free
      job_counter: '0'
```

## Enlist hosts

As part of the remote host management process, the command
`job list hosts` allows us to enlist all hosts which are 
configured in the `jobset`

```bash
(ENV3) $ cms job list hosts
job list hosts
+-----------------+--------------------------+-----------+--------+-------------+
| name            | ip                       | cpu_count | status | job_counter |
+-----------------+--------------------------+-----------+--------+-------------+
| DESKTOP-HUC37G2 | 127.0.0.1                | 4         | free   | 0           |
| juliet          | juliet.futuresystems.org | 12        | free   | 0           |
+-----------------+--------------------------+-----------+--------+-------------+
```

## Job scheduler management

The command `cms job scheduler` enables users to configure job scheduler 
policies. These policies come in effect when the host configured with the job
is not available for further job submissions. In such scenario, `cms job 
run` searches the next available host based on the scheduler policy and 
submits the job on that host.
It is assumed that this next host has all input data needed for the job and 
also the output locations. Configurable scheduler policies are as below:

* sequential - Use first available host
* random     - Use random available host
* smart      - Use a host with highest availability
* frugal     - Use a host with least availability
  
### Find out currently configured scheduler

Currently configured scheduler policy can be inquired using `job scheduler info`

```bash
(ENV3) $ cms job scheduler info

INFO: Configured scheduler policy: sequential
```

### Re-configure the scheduler

To modify the scheduler policy:

```bash
(ENV3) $ cms job scheduler --policy=smart

INFO: Scheduler policy changed from sequential to smart
```
