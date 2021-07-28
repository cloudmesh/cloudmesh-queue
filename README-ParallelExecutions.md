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
- [single runs](#single-runs)
  - [shell](#shell)
  - [python](#python)
  - [notebook](#notebook)

<!--TOC-->

## Purpose of the document 

This document demonstrates how can we run multiple jobs in parallel on a remore 
server using command `cms job`. The document runs through examples to indicate 
execution of `shell scripts, python scripts` and `jupyter notebooks` on remote a 
server. 
These steps are performed on a local Windows machine and a remote Linux host. 

## Notation

This document uses same notations as of `README-example.md`. Please refer 
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
| Type             | Command                                                      |
| ---------------- | ------------------------------------------------------------ |
| Shell script     | test.sh -o=~/ENV4/output -i=~/ENV4 -g=4                      |
| Python script    | python test.py --output=~/ENV4/output --input=~/ENV4 --gpu=5 |
| Jupyter notebook | papermill --log-output -p gpu 10 test.ipynb test_out.ipynb   |

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
| 1      | shell_j    | ready     | juliet.futuresystems.org | ./test.sh       | -o ~/ENV4/output -i ~/ENV4 -g 4                  | ketanp |
| 2      | python_j   | ready     | juliet.futuresystems.org | python3 test.py | --output=./output --input=~/ENV4 --gpu=5         | ketanp |
| 3      | notebook_j | ready     | juliet.futuresystems.org | papermill       | --log-output -p gpu 10 -p out_dir ~/ENV4/output  | ketanp |
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
| 1      | shell_j    | submitted | juliet.futuresystems.org | ./test.sh       | -o ~/ENV4/output -i ~/ENV4 -g 4                  | ketanp |
| 2      | python_j   | submitted | juliet.futuresystems.org | python3 test.py | --output=./output --input=~/ENV4 --gpu=5         | ketanp |
| 3      | notebook_j | submitted | juliet.futuresystems.org | papermill       | --log-output -p gpu 10 -p out_dir ~/ENV4/output  | ketanp |
|        |            |           |                          |                 | test.ipynb test_out.ipynb                        |        |
+--------+------------+-----------+--------------------------+-----------------+--------------------------------------------------+--------+
(ENV3) $
```

### Verify log files generated on the remote server
```bash
(ENV4) [ketanp@j-login1 output]$ ls -lrt
total 24
-rw-r--r-- 1 ketanp users   6 Jul 28 01:39 shell_j_pid.log
-rw-r--r-- 1 ketanp users 293 Jul 28 01:39 test_shell_output_07282021_013917.txt
-rw-r--r-- 1 ketanp users   6 Jul 28 01:39 python_j_pid.log
-rw-r--r-- 1 ketanp users 644 Jul 28 01:39 test_python_script_07282021_013923.log
-rw-r--r-- 1 ketanp users   6 Jul 28 01:39 notebook_j_pid.log
-rw-r--r-- 1 ketanp users 883 Jul 28 01:39 test_notebook.log
(ENV4) [ketanp@j-login1 output]$
```

### Check execution start time for all scripts
```bash
(ENV4) [ketanp@j-login1 output]$ grep 'Started the.*at' test_*
test_shell_output_07282021_013917.txt:Started the shell script at Wed Jul 28 01:39:17 EDT 2021.
(ENV4) [ketanp@j-login1 output]$
test_python_script_07282021_013923.log:2021-07-28 01:39:23,069|test.py|INFO|Started the python script at 2021-07-28 01:39:23.069625
test_notebook.log:2021-07-28 01:39:30,614|<ipython-input-5-c27c21ed9ba7>|DEBUG|Started the notebook execution at 2021-07-28 01:39:30.614957
```


---
# single runs
## shell
```
(ENV3) [~]: cms job run --name=shell_j
job run --name=shell_j

# ----------------------------------------------------------------------
# command
# ----------------------------------------------------------------------
# 346:run_job C:\Ketan\Masters\CloudComputing\ENV3\cm\cloudmesh-job\cloudmesh\job\jobqueue.py
# ----------------------------------------------------------------------
# ('ssh ketanp@juliet.futuresystems.org "cd ENV4;sh -c \'echo \\$\\$ > '
#  '~/ENV4/output/shell_j_pid.log;exec ./test.sh -o ~/ENV4/output -i ~/ENV4 -g '
#  '4\'"')
# ----------------------------------------------------------------------

win32
(ENV3) [~]:

(ENV4) [ketanp@j-login1 output]$ ls -lrt
total 8
-rw-r--r-- 1 ketanp users   6 Jul 28 00:51 shell_j_pid.log
-rw-r--r-- 1 ketanp users 293 Jul 28 00:51 test_shell_output_07282021_005117.txt
(ENV4) [ketanp@j-login1 output]$


(ENV4) [ketanp@j-login1 output]$ cat test_shell_output_07282021_005117.txt

Started the shell script at Wed Jul 28 00:51:17 EDT 2021.
output will be at:  /N/u/ketanp/ENV4/output/test_shell_output_07282021_005117.txt
input is taken from:  /N/u/ketanp/ENV4
gpu to use is:  4
sleep for 2 sec
Wed Jul 28 00:51:19 EDT 2021
sleep for 2 sec
Wed Jul 28 00:51:21 EDT 2021
END
(ENV4) [ketanp@j-login1 output]$

```
## python
```
(ENV3) [~]: cms job run --name=python_j
job run --name=python_j

win32
(ENV3) [~]:

(ENV4) [ketanp@j-login1 output]$ cat test_python_script_07282021_005940.log
2021-07-28 00:59:40,638|test.py|INFO|Started the python script at 2021-07-28 00:59:40.638116
2021-07-28 00:59:40,638|test.py|DEBUG|Preparing debug logs.
2021-07-28 00:59:40,638|test.py|DEBUG|Arguments passed:
2021-07-28 00:59:40,638|test.py|DEBUG|{'--gpu': '5',
 '--input': '~/ENV4',
 '--output': './output'}
2021-07-28 00:59:40,638|test.py|DEBUG|Starting the py script.
2021-07-28 00:59:40,638|test.py|DEBUG|Processing sleep 2
2021-07-28 00:59:42,640|test.py|DEBUG|complete
2021-07-28 00:59:42,640|test.py|DEBUG|Processing another sleep 2
2021-07-28 00:59:44,642|test.py|DEBUG|complete
2021-07-28 00:59:44,643|test.py|DEBUG|End of the script
(ENV4) [ketanp@j-login1 output]$
```

## notebook
```
(ENV3) $ cms job run --name=notebook_j
job run --name=notebook_j

win32
(ENV3) $

(ENV4) [ketanp@j-login1 output]$ cat test_notebook.log
2021-07-28 01:31:55,526|<ipython-input-5-c27c21ed9ba7>|DEBUG|Started the notebook execution at 2021-07-28 01:31:55.526279
2021-07-28 01:31:55,526|<ipython-input-5-c27c21ed9ba7>|DEBUG|Preparing debug logs.
2021-07-28 01:31:55,526|<ipython-input-5-c27c21ed9ba7>|DEBUG|Arguments passed:
2021-07-28 01:31:55,526|<ipython-input-5-c27c21ed9ba7>|DEBUG|{'out_dir': '/N/u/ketanp/ENV4/output', 'in_dir': '.', 'gpu': 10}
2021-07-28 01:31:55,526|<ipython-input-5-c27c21ed9ba7>|DEBUG|Starting the py script.
2021-07-28 01:31:55,526|<ipython-input-5-c27c21ed9ba7>|DEBUG|Processing sleep 2
2021-07-28 01:31:57,528|<ipython-input-5-c27c21ed9ba7>|DEBUG|complete
2021-07-28 01:31:57,529|<ipython-input-5-c27c21ed9ba7>|DEBUG|Processing another sleep 2
2021-07-28 01:31:59,531|<ipython-input-5-c27c21ed9ba7>|DEBUG|complete
2021-07-28 01:31:59,534|<ipython-input-5-c27c21ed9ba7>|DEBUG|End of the script
(ENV4) [ketanp@j-login1 output]$


---