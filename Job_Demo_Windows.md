- [Demo of `cms job` in Windows command prompt](#demo-of--cms-job--in-windows-command-prompt)
  * [Setting up location of config file](#setting-up-location-of-config-file)
  * [Verification of config file location in `cms job`](#verification-of-config-file-location-in--cms-job-)
  * [Creating a template of configuration file](#creating-a-template-of-configuration-file)
  * [Adding a new job in configuration file from another yaml file](#adding-a-new-job-in-configuration-file-from-another-yaml-file)
  * [Adding a new job using command line arguments](#adding-a-new-job-using-command-line-arguments)
  * [Enlisting configured jobs](#enlisting-configured-jobs)
    + [Enlist all jobs](#enlist-all-jobs)
    + [Enlist jobs with certain status](#enlist-jobs-with-certain-status)
    + [Enlist jobs with certain pattern in the job name](#enlist-jobs-with-certain-pattern-in-the-job-name)
    + [Enlist jobs sorted on job status](#enlist-jobs-sorted-on-job-status)
  * [Submit a job for execution on remote host](#submit-a-job-for-execution-on-remote-host)
    + [Outputs on remote host](#outputs-on-remote-host)
    + [Python script used for testing](#python-script-used-for-testing)
  * [Kill a job on remote host](#kill-a-job-on-remote-host)
  * [Reset status and rerun a job](#reset-status-and-rerun-a-job)
  * [Add a host](#add-a-host)
  
# Demo of `cms job` in Windows command prompt

## Setting up location of config file
Use `cms job set` to configure location of the configuration file with name 
`jobset`. In this example file `spec.yaml` is used as the configuration file.

```cmd
(ENV3) C:\>cms job set '~/.cloudmesh/job/spec.yaml'
job set '~/.cloudmesh/job/spec.yaml'
Jobset defined as spec located at ~\.cloudmesh\job\spec.yaml

(ENV3) C:\>cms set jobset
set jobset
jobset='~\.cloudmesh\job\spec.yaml'
```

## Verification of config file location in `cms job` 

```cmd
(ENV3) C:\>cms job info
job info
Jobs are defined in: ~\.cloudmesh\job\spec.yaml
```

## Creating a template of configuration file
Command `cms job template` can be used to create a sample configuration file:
```
(ENV3) C:\>cms job template --name=job[1-2]
job template --name=job[1-2]
Jobs are defined in: ~\.cloudmesh\job\spec.yaml
```
This generates following content in ~\.cloudmesh\job\spec.yaml. Please note 
this command **replaces existing spec.yaml file** with default content.
```yaml
cloudmesh:
  default:
    user: keTan
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

Currently configured jobs:
```cmd
(ENV3) C:\>cms job list
job list
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file '~\.cloudmesh\job\spec.yaml'
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
(ENV3) C:\>cms job add '~/.cloudmesh/job/new.yaml'
job add '~/.cloudmesh/job/new.yaml'
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file '~\.cloudmesh\job\spec.yaml'

(ENV3) C:\>cms job list
job list
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file '~\.cloudmesh\job\spec.yaml'
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
```cmd
(ENV3) C:\>cms job add --name='sample' --ip=localhost --executable='python sample.py' --arguments='--gpu=7' --directory='./scripts' --input='./data' --output='./output' --status='ready'
job add --name='sample' --ip=localhost --executable='python sample.py' --arguments='--gpu=7' --directory='./scripts' --input='./data' --output='./output' --status='ready'
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file '~\.cloudmesh\job\spec.yaml'

(ENV3) C:\>cms job list
job list
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file '~\.cloudmesh\job\spec.yaml'
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
There are few variation of this command as follows:
### Enlist all jobs
```cmd
(ENV3) C:\>cms job list
job list
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file '~\.cloudmesh\job\spec.yaml'
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
### Enlist jobs with certain status
```cmd
(ENV3) C:\>cms job list --status='submitted'
job list --status='submitted'
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file '~\.cloudmesh\job\spec.yaml'
+--------+-----------+-----------+--------------------------+---------+-------------+--------+
| Number | JobName   | JobStatus | RemoteIp                 | Command | Arguments   | User   |
+--------+-----------+-----------+--------------------------+---------+-------------+--------+
| 1      | ls_juliet | submitted | juliet.futuresystems.org | ls      | -lisa; bash | ketanp |
+--------+-----------+-----------+--------------------------+---------+-------------+--------+
```
### Enlist jobs with certain pattern in the job name
```cmd
(ENV3) C:\>cms job list --name='pytest'
job list --name='pytest'
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file '~\.cloudmesh\job\spec.yaml'
+--------+-------------+-----------+-----------+------------------+-----------+-------+
| Number | JobName     | JobStatus | RemoteIp  | Command          | Arguments | User  |
+--------+-------------+-----------+-----------+------------------+-----------+-------+
| 1      | pytest_job  | ready     | local     | ls               | -lisa     | user  |
| 2      | pytest_job1 | ready     | localhost | python sample.py | --gpu=7   | keTan |
+--------+-------------+-----------+-----------+------------------+-----------+-------+
```
### Enlist jobs sorted on job status
```cmd
(ENV3) C:\>cms job status
job status
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file '~\.cloudmesh\job\spec.yaml'
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

```cmd
(ENV3) C:\>cms job run --name=test_juliet
job run --name=test_juliet
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file '~\.cloudmesh\job\spec.yaml'
```

### Outputs on remote host
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

<!--
<table style="width: 100%">
    <colgroup>
       <col span="1" style="width: 30%;">
       <col span="1" style="width: 70%;">
    </colgroup>
-->
<table "width:200px; height:250px;overflow:hidden">
<tr>
<th> Local machine </th>
<th> Remote host </th>
</tr>
<tr>
<td>

```cmd
(ENV3) C:\>cms job run --name=test_juliet
job run --name=test_juliet
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file 
'~\.cloudmesh\job\spec.yaml'


(ENV3) C:\>cms job kill --name=test_juliet
job kill --name=test_juliet
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file 
'~\.cloudmesh\job\spec.yaml'
```

</td>
<td>

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
^C
[ketanp@j-login1 test_juliet]$

```

</td>
</tr>
</table>

```cmd
(ENV3) C:\>cms job list --name='juliet'
job list --name='juliet'
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file '~\.cloudmesh\job\spec.yaml'
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+
| Number | JobName     | JobStatus | RemoteIp                 | Command        | Arguments                                        | User   |
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+
| 1      | test_juliet | killed    | juliet.futuresystems.org | python test.py | --input=./data --output=./output/test_juliet     | ketanp |
|        |             |           |                          |                | --gpu=7                                          |        |
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+

```

## Reset status and rerun a job

```cmd
(ENV3) C:\>cms job list --name='juliet'
job list --name='juliet'
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file '~\.cloudmesh\job\spec.yaml'
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+
| Number | JobName     | JobStatus | RemoteIp                 | Command        | Arguments                                        | User   |
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+
| 1      | test_juliet | killed    | juliet.futuresystems.org | python test.py | --input=./data --output=./output/test_juliet     | ketanp |
|        |             |           |                          |                | --gpu=7                                          |        |
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+


(ENV3) C:\>cms job reset --name='test_juliet'
job reset --name='test_juliet'
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file '~\.cloudmesh\job\spec.yaml'
Status reset for job test_juliet.


(ENV3) C:\>cms job list --name='juliet'
job list --name='juliet'
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file '~\.cloudmesh\job\spec.yaml'
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+
| Number | JobName     | JobStatus | RemoteIp                 | Command        | Arguments                                        | User   |
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+
| 1      | test_juliet | ready     | juliet.futuresystems.org | python test.py | --input=./data --output=./output/test_juliet     | ketanp |
|        |             |           |                          |                | --gpu=7                                          |        |
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+


(ENV3) C:\>cms job run --name=test_juliet
job run --name=test_juliet
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file '~\.cloudmesh\job\spec.yaml'


(ENV3) C:\>cms job list --name='juliet'
job list --name='juliet'
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file '~\.cloudmesh\job\spec.yaml'
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+
| Number | JobName     | JobStatus | RemoteIp                 | Command        | Arguments                                        | User   |
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+
| 1      | test_juliet | submitted | juliet.futuresystems.org | python test.py | --input=./data --output=./output/test_juliet     | ketanp |
|        |             |           |                          |                | --gpu=7                                          |        |
+--------+-------------+-----------+--------------------------+----------------+--------------------------------------------------+--------+

(ENV3) C:\>
``` 


## Add a host

```cmd
(ENV3) C:\>cms job hosts add --hostname='juliet' --ip='juliet.futuresystems.org' --cpu_count='12'
job hosts add --hostname='juliet' --ip='juliet.futuresystems.org' --cpu_count='12'
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file '~\.cloudmesh\job\spec.yaml'
```
```yaml
  hosts:
    localhost:
      name: DESKTOP-HUC37G2
      ip: 127.0.0.1
      cpu_count: 4
      status: free
      job_counter: '1'
    juliet:
      name: juliet
      ip: juliet.futuresystems.org
      cpu_count: '12'
      status: free
      job_counter: '0'
```

