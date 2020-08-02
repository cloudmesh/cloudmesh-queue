# Demo of `cms job` in Windows command prompt

## Setting up location of config file
Use `cms job set` to configure location of the configuration file with name 
`jobset`. In this example file `spec.yaml` is used as the configuration file.

```cmd
(ENV3) C:\Study\IUMSDS\Fall2019\CloudComputing\cm\cloudmesh-job>cms job set '~/.cloudmesh/job/spec.yaml'
job set '~/.cloudmesh/job/spec.yaml'
Jobset defined as spec located at~\.cloudmesh\job\spec.yaml

(ENV3) C:\Study\IUMSDS\Fall2019\CloudComputing\cm\cloudmesh-job>cms set jobset
set jobset
jobset='~\.cloudmesh\job\spec.yaml'
```

## Verification of config file location in `cms job` 

```cmd
(ENV3) C:\Study\IUMSDS\Fall2019\CloudComputing\cm\cloudmesh-job>cms job info
job info
Jobs are defined in: ~\.cloudmesh\job\spec.yaml
```

## Creating a template of configuration file
Command `cms job template` can be used to create a sample configuration file:
```
(ENV3) C:\Study\IUMSDS\Fall2019\CloudComputing\cm\cloudmesh-job>cms job template --name=job[1-2]
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
(ENV3) C:\Study\IUMSDS\Fall2019\CloudComputing\cm\cloudmesh-job>cms job list
job list
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file 'C:\Users\kpimp\.cloudmesh\job\spec.yaml'
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
(ENV3) C:\Study\IUMSDS\Fall2019\CloudComputing\cm\cloudmesh-job>cms job add '~/.cloudmesh/job/new.yaml'
job add '~/.cloudmesh/job/new.yaml'
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file 'C:\Users\kpimp\.cloudmesh\job\spec.yaml'

(ENV3) C:\Study\IUMSDS\Fall2019\CloudComputing\cm\cloudmesh-job>cms job list
job list
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file 'C:\Users\kpimp\.cloudmesh\job\spec.yaml'
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
(ENV3) C:\Study\IUMSDS\Fall2019\CloudComputing\cm\cloudmesh-job>cms job add --name='sample' --ip=localhost --executable='python sample.py' --arguments='--gpu=7' --directory='./scripts' --input='./data' --output='./output' --status='ready'
job add --name='sample' --ip=localhost --executable='python sample.py' --arguments='--gpu=7' --directory='./scripts' --input='./data' --output='./output' --status='ready'
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file 'C:\Users\kpimp\.cloudmesh\job\spec.yaml'

(ENV3) C:\Study\IUMSDS\Fall2019\CloudComputing\cm\cloudmesh-job>cms job list
job list
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file 'C:\Users\kpimp\.cloudmesh\job\spec.yaml'
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
(ENV3) C:\Study\IUMSDS\Fall2019\CloudComputing\cm\cloudmesh-job>cms job list
job list
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file 'C:\Users\kpimp\.cloudmesh\job\spec.yaml'
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
(ENV3) C:\Study\IUMSDS\Fall2019\CloudComputing\cm\cloudmesh-job>cms job list --status='submitted'
job list --status='submitted'
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file 'C:\Users\kpimp\.cloudmesh\job\spec.yaml'
+--------+-----------+-----------+--------------------------+---------+-------------+--------+
| Number | JobName   | JobStatus | RemoteIp                 | Command | Arguments   | User   |
+--------+-----------+-----------+--------------------------+---------+-------------+--------+
| 1      | ls_juliet | submitted | juliet.futuresystems.org | ls      | -lisa; bash | ketanp |
+--------+-----------+-----------+--------------------------+---------+-------------+--------+
```
### Enlist jobs with certain pattern in the job name
```cmd
(ENV3) C:\Study\IUMSDS\Fall2019\CloudComputing\cm\cloudmesh-job>cms job list --name='pytest'
job list --name='pytest'
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file 'C:\Users\kpimp\.cloudmesh\job\spec.yaml'
+--------+-------------+-----------+-----------+------------------+-----------+-------+
| Number | JobName     | JobStatus | RemoteIp  | Command          | Arguments | User  |
+--------+-------------+-----------+-----------+------------------+-----------+-------+
| 1      | pytest_job  | ready     | local     | ls               | -lisa     | user  |
| 2      | pytest_job1 | ready     | localhost | python sample.py | --gpu=7   | keTan |
+--------+-------------+-----------+-----------+------------------+-----------+-------+
```
### Enlist jobs sorted on job status
```cmd
(ENV3) C:\Study\IUMSDS\Fall2019\CloudComputing\cm\cloudmesh-job>cms job status
job status
WARNING: The key 'cloudmesh.profile.user' could not be found in the yaml file 'C:\Users\kpimp\.cloudmesh\job\spec.yaml'
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
