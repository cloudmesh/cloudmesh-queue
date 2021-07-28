# Example of `cms job` to run multiple jobs in parallel

# Table of Contents

<!--TOC-->

- [Example of `cms job` to run multiple jobs in parallel](#example-of-cms-job-to-run-multiple-jobs-in-parallel)
- [Table of Contents](#table-of-contents)
  - [Purpose of the document](#purpose-of-the-document)
  - [Notation](#notation)
  - [Example execution of `cms job`](#example-execution-of-cms-job)
  - [Configuration](#configuration)
  - [Prerequisites](#prerequisites)
  - [Example scripts to be run on remote server](#example-scripts-to-be-run-on-remote-server)
  - [Execution steps](#execution-steps)
    - [Enlist the configured jobs](#enlist-the-configured-jobs)
    - [Execute the jobs in parallel](#execute-the-jobs-in-parallel)
    - [Verify log files generated on the remote server](#verify-log-files-generated-on-the-remote-server)
    - [Check execution start time for all scripts](#check-execution-start-time-for-all-scripts)
    - [Output log files](#output-log-files)
  - [Execution of multiple instances of a job](#execution-of-multiple-instances-of-a-job)
    - [The job configuration](#the-job-configuration)
    - [Enlisting instances of the job](#enlisting-instances-of-the-job)
    - [Submitting both instances of the job for execution](#submitting-both-instances-of-the-job-for-execution)
    - [Generated outputs](#generated-outputs)
    - [Execution timestamps](#execution-timestamps)

<!--TOC-->

## Purpose of the document 

This document demonstrates how can we run multiple jobs in parallel on a remore 
server using command `cms job`. The document runs through examples to indicate 
execution of `shell scripts, python scripts` and `jupyter notebooks` on remote a 
server. 
These steps are performed on a local Windows machine and a remote Linux host. 

## Notation

This document uses same notations as that of `README-example.md`. Please refer 
notation details at following location:

[Notation instructions](https://github.com/cloudmesh/cloudmesh-job/blob/main/README-example.md#notation)

## Example execution of `cms job`

Please refer following document for examples and usage of the command `cms job`  

[Example of `cms job` in Windows, Linux, and macOS](README-example.md)

## Configuration

The `cms job` configuration is defined in a .yaml file. Location of this file 
can be checked as follows:
```bash
$ cms job info
job info
Jobs are defined in: ~/.cloudmesh/job/spec_new.yaml
```

The configuration used for parallel executions is present in following file:  
[spec_new.yaml](https://github.com/cloudmesh/cloudmesh-job/blob/main/tests/sample_scripts/spec_new.yaml)  

This setup intends to run following set of commands on a remote server:
| Type             | Command                                                        |
| ---------------- | -------------------------------------------------------------- |
| Shell script     | test.sh -o=\~/ENV3/output -i=\~/ENV3 -g=4                      |
| Python script    | python test.py --output=\~/ENV3/output --input=\~/ENV3 --gpu=5 |
| Jupyter notebook | papermill --log-output -p gpu 10 test.ipynb test_out.ipynb     |

## Prerequisites

This setup assumes following points:
* ssh access to the remote server from local machine is enabled using rsa keys
  * [Steps to setup ssh access to remote server](https://www.thegeekstuff.com/2008/11/3-steps-to-perform-ssh-login-without-password-using-ssh-keygen-ssh-copy-id/)
* Remote server has python3.6+ installed
  * [Python installation](https://wiki.python.org/moin/BeginnersGuide/Download)
* Remote server has `papermill` installation for execution of jupyter notebooks
  * [Papermill installation and usage](https://papermill.readthedocs.io/en/latest/)

## Example scripts to be run on remote server

This document demonstrates execution of parallel jobs using follwing scripts:
1. Shell script: [test.sh](https://github.com/cloudmesh/cloudmesh-job/blob/main/tests/sample_scripts/test.sh) 
2. Python script: [test.py](https://github.com/cloudmesh/cloudmesh-job/blob/main/tests/sample_scripts/test.py)
3. Jupyter notebook: [test.ipynb](https://github.com/cloudmesh/cloudmesh-job/blob/main/tests/sample_scripts/test.ipynb)

## Execution steps
### Enlist the configured jobs

The list of job indicates that there are three jobs to run:
```bash
(ENV3) $ cms job list
job list
+--------+------------+-----------+--------------------------+-----------------+--------------------------------------------------+--------+
| Number | JobName    | JobStatus | RemoteIp                 | Command         | Arguments                                        | User   |
+--------+------------+-----------+--------------------------+-----------------+--------------------------------------------------+--------+
| 1      | shell_j    | ready     | juliet.futuresystems.org | ./test.sh       | -o ~/ENV3/output -i ~/ENV3 -g 4                  | ketanp |
| 2      | python_j   | ready     | juliet.futuresystems.org | python3 test.py | --output=./output --input=~/ENV3 --gpu=5         | ketanp |
| 3      | notebook_j | ready     | juliet.futuresystems.org | papermill       | --log-output -p gpu 10 -p out_dir ~/ENV3/output  | ketanp |
|        |            |           |                          |                 | test.ipynb test_out.ipynb                        |        |
+--------+------------+-----------+--------------------------+-----------------+--------------------------------------------------+--------+
(ENV3) $
```

### Execute the jobs in parallel
`cms job run`  without any additional arguments allows execution of all configured 
jobs in parallel:

```bash
(ENV3) $ cms job run
job run

(ENV3) $ cms job list
job list
+--------+------------+-----------+--------------------------+-----------------+--------------------------------------------------+--------+
| Number | JobName    | JobStatus | RemoteIp                 | Command         | Arguments                                        | User   |
+--------+------------+-----------+--------------------------+-----------------+--------------------------------------------------+--------+
| 1      | shell_j    | submitted | juliet.futuresystems.org | ./test.sh       | -o ~/ENV3/output -i ~/ENV3 -g 4                  | ketanp |
| 2      | python_j   | submitted | juliet.futuresystems.org | python3 test.py | --output=./output --input=~/ENV3 --gpu=5         | ketanp |
| 3      | notebook_j | submitted | juliet.futuresystems.org | papermill       | --log-output -p gpu 10 -p out_dir ~/ENV3/output  | ketanp |
|        |            |           |                          |                 | test.ipynb test_out.ipynb                        |        |
+--------+------------+-----------+--------------------------+-----------------+--------------------------------------------------+--------+
(ENV3) $
```

### Verify log files generated on the remote server
```bash
(ENV3) [ketanp@j-login1 output]$ ls -lrt
total 24
-rw-r--r-- 1 ketanp users   6 Jul 28 01:39 shell_j_pid.log
-rw-r--r-- 1 ketanp users 293 Jul 28 01:39 test_shell_output_07282021_013917.txt
-rw-r--r-- 1 ketanp users   6 Jul 28 01:39 python_j_pid.log
-rw-r--r-- 1 ketanp users 644 Jul 28 01:39 test_python_script_07282021_013923.log
-rw-r--r-- 1 ketanp users   6 Jul 28 01:39 notebook_j_pid.log
-rw-r--r-- 1 ketanp users 883 Jul 28 01:39 test_notebook.log
(ENV3) [ketanp@j-login1 output]$
```

### Check execution start time for all scripts

From the logs we can confirm following execution start times:
| Type             | Name       | Execution start at           |
| ---------------- | ---------- | ---------------------------- |
| Shell script     | test.sh    | Wed Jul 28 01:39:17 EDT 2021 |
| Python script    | test.py    | 021-07-28 01:39:23.069625    |
| Jupyter notebook | test.ipynb | 2021-07-28 01:39:30.614957   |

```bash
(ENV3) [ketanp@j-login1 output]$ grep 'Started the.*at' test_*
test_shell_output_07282021_013917.txt:Started the shell script at Wed Jul 28 01:39:17 EDT 2021.
test_python_script_07282021_013923.log:2021-07-28 01:39:23,069|test.py|INFO|Started the python script at 2021-07-28 01:39:23.069625
test_notebook.log:2021-07-28 01:39:30,614|<ipython-input-5-c27c21ed9ba7>|DEBUG|Started the notebook execution at 2021-07-28 01:39:30.614957
```

### Output log files

Log files generated by above runs are located at following location:

| Type             | Name       | Log file                                                                                                                                                                  |
| ---------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Shell script     | test.sh    | [test_shell_output_07282021_013917.txt](https://github.com/cloudmesh/cloudmesh-job/blob/main/tests/sample_scripts/sample_outputs/test_shell_output_07282021_013917.txt)   |
| Python script    | test.py    | [test_python_script_07282021_013923.txt](https://github.com/cloudmesh/cloudmesh-job/blob/main/tests/sample_scripts/sample_outputs/test_python_script_07282021_013923.txt) |
| Jupyter notebook | test.ipynb | [test_notebook.txt](https://github.com/cloudmesh/cloudmesh-job/blob/main/tests/sample_scripts/sample_outputs/test_notebook.txt)                                           |


## Execution of multiple instances of a job

`cms job run` can be easily used to submit multiple instances of a job with 
different input arguments. The remote server on which we want to run these jobs 
can be different for each instance.   
Following configuration is used to submit two instances of job `test_multiple_inst.py`
on remote server `juliet.futuresystems.org`. These two instances have same code
of the job however they take distinct values for the argument `--instance`. This
is evident from the logs generated by these executions.

### The job configuration

```yaml
      python_j_101:
        name: python_j_101
        directory: ENV3
        ip: juliet.futuresystems.org
        input: ~/ENV3
        output: ~/ENV3/output
        status: ready
        gpu: ' '
        user: ketanp
        arguments: --output=./output --input=~/ENV3 --gpu=5 --instance=101
        executable: "python3 test_multiple_inst.py"
        shell: bash
      python_j_201:
        name: python_j_201
        directory: ENV3
        ip: juliet.futuresystems.org
        input: ~/ENV3
        output: ~/ENV3/output
        status: ready
        gpu: ' '
        user: ketanp
        arguments: --output=./output --input=~/ENV3 --gpu=3 --instance=201
        executable: "python3 test_multiple_inst.py"
        shell: bash
```

### Enlisting instances of the job

We maintain separate `JobName` and distinct values for `--instance` as see in the
enlisted jobs:

```bash
(ENV3) $ cms job list --status=ready
job list --status=ready
+--------+--------------+-----------+--------------------------+-------------------------------+--------------------------------------------------+--------+
| Number | JobName      | JobStatus | RemoteIp                 | Command                       | Arguments                                        | User   |
+--------+--------------+-----------+--------------------------+-------------------------------+--------------------------------------------------+--------+
| 1      | python_j_101 | ready     | juliet.futuresystems.org | python3 test_multiple_inst.py | --output=./output --input=~/ENV3 --gpu=5         | ketanp |
|        |              |           |                          |                               | --instance=101                                   |        |
| 2      | python_j_201 | ready     | juliet.futuresystems.org | python3 test_multiple_inst.py | --output=./output --input=~/ENV3 --gpu=3         | ketanp |
|        |              |           |                          |                               | --instance=201                                   |        |
+--------+--------------+-----------+--------------------------+-------------------------------+--------------------------------------------------+--------+
(ENV3) $
```

### Submitting both instances of the job for execution

We submit these instances using `cms job run` command:

```bash
(ENV3) $ cms job run

(ENV3) $ cms job list --name=j_
job list --name=j_
+--------+--------------+-----------+--------------------------+-------------------------------+--------------------------------------------------+--------+
| Number | JobName      | JobStatus | RemoteIp                 | Command                       | Arguments                                        | User   |
+--------+--------------+-----------+--------------------------+-------------------------------+--------------------------------------------------+--------+
| 1      | python_j_101 | submitted | juliet.futuresystems.org | python3 test_multiple_inst.py | --output=./output --input=~/ENV3 --gpu=5         | ketanp |
|        |              |           |                          |                               | --instance=101                                   |        |
| 2      | python_j_201 | submitted | juliet.futuresystems.org | python3 test_multiple_inst.py | --output=./output --input=~/ENV3 --gpu=3         | ketanp |
|        |              |           |                          |                               | --instance=201                                   |        |
+--------+--------------+-----------+--------------------------+-------------------------------+--------------------------------------------------+--------+
(ENV3) $
```

 ### Generated outputs

 These executions occur on the remote server and generate following log files:

```bash
(ENV3) [ketanp@j-login1 output]$ ls -lrt
total 16
-rw-r--r-- 1 ketanp users   5 Jul 28 03:36 python_j_101_pid.log
-rw-r--r-- 1 ketanp users 822 Jul 28 03:36 test_python_script_101_07282021_033655.log
-rw-r--r-- 1 ketanp users   5 Jul 28 03:36 python_j_201_pid.log
-rw-r--r-- 1 ketanp users 822 Jul 28 03:37 test_python_script_201_07282021_033700.log
(ENV3) [ketanp@j-login1 output]$
```

### Execution timestamps

Upon verifying the content of these logs, it can be seen that the distinct values
of the argument `--instance` was successfully consumed by these jobs:

```bash
(ENV3) [ketanp@j-login1 output]$ grep 'Started the instance' test_python*log
test_python_script_101_07282021_033655.log:2021-07-28 03:36:55,104|test_multiple_inst.py|INFO|Started the instance 101 of python script at 2021-07-28 03:36:55.104731
test_python_script_201_07282021_033700.log:2021-07-28 03:37:00,028|test_multiple_inst.py|INFO|Started the instance 201 of python script at 2021-07-28 03:37:00.028821
(ENV3) [ketanp@j-login1 output]$
```
