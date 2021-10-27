# Cloudmesh Queue

Cloudmesh Queue is a job queuing and scheduling framework. It allows
users to leverage all the available compute resources defined in a cluster to perform
tasks which require maximum compute power and execution time. It is implemented as both as cmd line program
and as a rest service with interactive documentation.

![](https://github.com/cloudmesh/cloudmesh-queue/raw/main/images/rest.png)

## Installation

You can get the cloudmesh queue package using the `cloudmesh-installer`.

```
$ mkdir cm
$ cd cm
$ cloudmesh-installer get queue
```

## Cluster

A cluster provides a yaml representation of a set of hosts

We have the following cluster commands implemented.

```
            cluster create [--cluster=CLUSTER]  [--experiment=EXPERIMENT]
            cluster list [--cluster=CLUSTER]  [--experiment=EXPERIMENT]
            cluster add [--cluster=CLUSTER]  [--experiment=EXPERIMENT] --id=ID --name=NAME --user=USER
                                [--ip=IP]
                                [--status=STATUS]
                                [--gpu=GPU]
                                [--pyenv=PYENV]
            cluster delete [--cluster=CLUSTER]  [--experiment=EXPERIMENT] --id=ID
            cluster activate [--cluster=CLUSTER]  [--experiment=EXPERIMENT] --id=ID
            cluster deactivate [--cluster=CLUSTER]  [--experiment=EXPERIMENT] --id=ID
            cluster set [--cluster=CLUSTER]  [--experiment=EXPERIMENT] --id=ID --key=KEY --value=VALUE
```

## Create a Cluster

To create an empty cluster run:

```
cluster create [--cluster=CLUSTER]  [--experiment=EXPERIMENT]
```

Here `CLUSTER` is the name of your cluster and `experiment` is the path of the directory that it should be stored in. If you do not include the string `-cluster.yaml` in your `CLUSTER` argument, it wil be automatically added for you. If you do not include an `experiment` argument, the directory `./experiment` will be assumed.
The default name is `default`.

Example:

```
cluster create a 
```

## Add Hosts to a Cluster

Hosts are a means of execution given a host `name` and `user`. Each host represents one allowed maximum job. To allow multiple jobs to run on the same machine, define multiple hosts for that machine. 

Add hosts to a cluster with:

```
cluster add [--cluster=CLUSTER]  [--experiment=EXPERIMENT] --id=ID --name=NAME --user=USER
                                [--ip=IP]
                                [--status=STATUS]
                                [--gpu=GPU]
                                [--pyenv=PYENV]
```
The `id` argument takes a single or expandable name. For example host[1-10] will create 10 hosts with the same parameters, but different ids.

The `name` argument is the target hostname.

The `user` argument is the target user.

The `ip` argument is the target ip.

The `status` argument is the target status. A default of `active` is assumed. All others will not be assigned jobs.

The `gpu` is the GPUs to be set with the environment variable `CUDA_VISIBLE_DEVICES=`. Only include the numbers, i.e. `0,1` and not the environment variable name.

The `pyenv` is the argument to the `source` command and will be executed before running the job to activate a python environment.

Example:

```
cms cluster add a --id=host[1-4] --name=red --user=pi --gpu=0 --pyenv="'~/ENV3/bin/activate'"
cluster add a --id=host[1-4] --name=red --user=pi --gpu=0 --pyenv='~/ENV3/bin/activate'
INFO: Adding host host1 to cluster a
INFO: Adding host host2 to cluster a
INFO: Adding host host3 to cluster a
INFO: Adding host host4 to cluster a
```

## List Hosts in a Cluster

Lists Hosts in a cluster with 

```
cluster list [--cluster=CLUSTER]  [--experiment=EXPERIMENT]
```

Example:

```
cms cluster list a

+-------+------+------+--------+-----+---------------------+----+------------------+
| id    | name | user | status | gpu | pyenv               | ip | max_jobs_allowed |
+-------+------+------+--------+-----+---------------------+----+------------------+
| host1 | red  | pi   | active | 0   | ~/ENV3/bin/activate |    | 1                |
| host2 | red  | pi   | active | 0   | ~/ENV3/bin/activate |    | 1                |
| host3 | red  | pi   | active | 0   | ~/ENV3/bin/activate |    | 1                |
| host4 | red  | pi   | active | 0   | ~/ENV3/bin/activate |    | 1                |
+-------+------+------+--------+-----+---------------------+----+------------------+
```

## Delete Hosts in a Cluster

Delete Hosts in a Cluster with

```
cluster delete [--cluster=CLUSTER]  [--experiment=EXPERIMENT] --id=ID
```

Example:

```
cms cluster delete a --id=host[3-4]
INFO: Deleting hosts: ['host3', 'host4']
```

## Activate or Deactivate Hosts in a Cluster

Activate or deactivate hsots in a cluster with

```
cluster activate [--cluster=CLUSTER]  [--experiment=EXPERIMENT] --id=ID
cluster deactivate [--cluster=CLUSTER]  [--experiment=EXPERIMENT] --id=ID
```

Some schedulers will only consider hosts in an `active` status. Other statuses will not be scheduled.

## Set Host Attributes in a Cluster

To set any host attribute in a cluster use.

```
cluster set [--cluster=CLUSTER]  [--experiment=EXPERIMENT] --id=ID --key=KEY --value=VALUE
```

Example:
```
cms cluster set a --id=host1 --key=name --value=red02
INFO: Setting host: host1 key: name value: red02 in cluster a
```
## Queue


We have the following queue commands implemented.

```
            queue create [queue=QUEUE] [--experiment=EXPERIMENT]
            queue list [queue=QUEUE] [--experiment=EXPERIMENT]
            queue refresh [queue=QUEUE] [--experiment=EXPERIMENT]
            queue add [queue=QUEUE] [--experiment=EXPERIMENT] --name=NAME --command=COMMAND
                    [--input=INPUT]
                    [--output=OUTPUT]
                    [--status=STATUS]
                    [--gpu=GPU]
                    [--user=USER]
                    [--host=HOST]
                    [--shell=SHELL]
                    [--log=LOG]
                    [--pyenv=PYENV]
            queue delete [queue=QUEUE] [--experiment=EXPERIMENT] --name=NAME
            queue run fifo [queue=QUEUE] [--experiment=EXPERIMENT] --max_parallel=MAX_PARALLEL [--timeout=TIMEOUT]
            queue run fifo_multi [queue=QUEUE] [--experiment=EXPERIMENT] --hosts=HOSTS [--timeout=TIMEOUT]
            queue reset [queue=QUEUE] [--experiment=EXPERIMENT] [--name=NAME] [--status=STATUS]
```

## Create a Queue

To create an empty queue run:

```
queue create [queue=QUEUE] [--experiment=EXPERIMENT]
```

Here `QUEUE` is the name of your queue and `experiment` is the path of the directory that its jobs should be stored in. If you do not include the string `-queue.yaml` in your `QUEUE` argument, it wil be automatically added for you. If you do not include an `experiment` argument, the directory `./experiment` will be assumed.

Example:

```
queue create a 
```
## Add Jobs to a Queue

Add jobs to a queue with:

```
queue add [queue=QUEUE] [--experiment=EXPERIMENT] --name=NAME --command=COMMAND
                    [--input=INPUT]
                    [--output=OUTPUT]
                    [--status=STATUS]
                    [--gpu=GPU]
                    [--user=USER]
                    [--host=HOST]
                    [--shell=SHELL]
                    [--log=LOG]
                    [--pyenv=PYENV]
```

The `name` argument takes a single or expandable name. For example job[1-10] will create 10 jobs with the same parameters, but different names.

The `command` argument is the command line command to run for the job. If there are spaces in the command you are required to encapsulate it in double and single quotes, e.g. `"'sleep 10'"`

The `input` is the location of input used by the command.

The `output` is the location of the output used by the command.

The 'gpu' is the GPUs to be set with the environment variable `CUDA_VISIBLE_DEVICES=`. Only include the numbers, i.e. `0,1` and not the environment variable name.

The `user` and `host` are the user and host that this job are assigned to. Some schedulers require these jobs to be set, others will assign them from a group of hosts.

The `shell` is the shell that will run the command.

The `log` is the location of the log output.

The `pyenv` is the argument to the `source` command and will be executed before running the job to activate a python environment.

Example:

```
cms queue add a --name=job[1-10] --command="'sleep 10'" --user=pi --host=red --gpu=0 --pyenv=~/ENV3/bin/activate

queue add a --name=job[1-10] --command='sleep 10' --user=pi --host=red --gpu=0 --pyenv=~/ENV3/bin/activate
INFO: Adding job job1 to queue a
INFO: Adding job job2 to queue a
INFO: Adding job job3 to queue a
INFO: Adding job job4 to queue a
INFO: Adding job job5 to queue a
INFO: Adding job job6 to queue a
INFO: Adding job job7 to queue a
INFO: Adding job job8 to queue a
INFO: Adding job job9 to queue a
INFO: Adding job job10 to queue a
```

## List Jobs in a Queue

To see a summary of the jobs in a queue user hte list command.

```
queue list [queue=QUEUE] [--experiment=EXPERIMENT]
```

Example:

```
cms queue list a
queue list a
+-------+--------+----------+-----+-----------+-----------+------------+
| name  | status | command  | gpu | output    | log       | experiment |
+-------+--------+----------+-----+-----------+-----------+------------+
| job1  | ready  | sleep 10 | 0   | job1.out  | job1.log  | experiment |
| job2  | ready  | sleep 10 | 0   | job2.out  | job2.log  | experiment |
| job3  | ready  | sleep 10 | 0   | job3.out  | job3.log  | experiment |
| job4  | ready  | sleep 10 | 0   | job4.out  | job4.log  | experiment |
| job5  | ready  | sleep 10 | 0   | job5.out  | job5.log  | experiment |
| job6  | ready  | sleep 10 | 0   | job6.out  | job6.log  | experiment |
| job7  | ready  | sleep 10 | 0   | job7.out  | job7.log  | experiment |
| job8  | ready  | sleep 10 | 0   | job8.out  | job8.log  | experiment |
| job9  | ready  | sleep 10 | 0   | job9.out  | job9.log  | experiment |
| job10 | ready  | sleep 10 | 0   | job10.out | job10.log | experiment |
+-------+--------+----------+-----+-----------+-----------+------------+
```

## Deleting a Job from a Queue.

Delete a job using delete.

```
queue delete [queue=QUEUE] [--experiment=EXPERIMENT] --name=NAME
```

The `name` argument is a single job or an expandable list of names. The job will be killed if still running on a host (if the host is accessible), and deleted from a queue.

Example:

```
cms queue delete a --name=job[9-10]
queue delete a --name=job[9-10]
INFO: Deleting jobs: ['job9', 'job10']
```

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

`timeout` is the time that will consider a host as dead and mark the job as crashed. The default is 10 minutes.

**Prerequisite:** All jobs intended to be run must be assigned a `user` and a `host`. Those jobs not assigned a `user` and `host` will be skipped. 

**Example**

```
cms queue run fifo a --max_parallel=4
queue run fifo a --max_parallel=4
INFO: Running job: job1 on pi@red

# ----------------------------------------------------------------------
# Run: job1
# ----------------------------------------------------------------------

INFO: Running Jobs: ['job1']
INFO: Running job: job2 on pi@red

# ----------------------------------------------------------------------
# Run: job2
# ----------------------------------------------------------------------

INFO: Running Jobs: ['job1', 'job2']
INFO: Running job: job3 on pi@red

# ----------------------------------------------------------------------
# Run: job3
# ----------------------------------------------------------------------

INFO: Running Jobs: ['job1', 'job2', 'job3']
INFO: Running job: job4 on pi@red

# ----------------------------------------------------------------------
# Run: job4
# ----------------------------------------------------------------------

INFO: Running Jobs: ['job1', 'job2', 'job3', 'job4']
INFO: Waiting. At max_parallel jobs=4.
... OUTPUT TRIMED FOR READABILITY
INFO: Ran Jobs: ['job1', 'job2', 'job3', 'job4', 'job5', 'job6', 'job7', 'job8']
INFO: Completed Jobs: ['job1', 'job2', 'job3', 'job4', 'job5', 'job6', 'job7', 'job8']
```

Job assignments are not checked until the queue has reached the job, so the state can be changed after a `queue.run()`, but before a job is considered, but not after a job has already been skipped.

#### Failure considerations

This queue checks for and continues to function in the event of the following failures. When a failure is incurred, the job is skipped and marked with an appropriate status, so the queue can continue to process remaining jobs (if possible).
1. A job that failed to start on a host.
2. A job that crashed on a host.
3. A job that was running on a host that crashed.

#### Recovery from queue manager failure

To recover from a crashed manager that was executing a queue with this scheduler.

1. Recover the manager and determine failure cause.
2. Execute a `queue refresh` to get the latest job states from worker hosts.
3. Re-run the queue with `queue run`

#### Recovery from queue worker failure

To recover from a failed worker host. 

1. Recover the worker host and determine failure cause. 
2. After reboot this host will continue to run the next `ready` jobs assigned to that host.
3. For any job not in an `end` state assigned to that host, change thier status to `ready` in the quueue file.
4. Stop or let the queue finish its current run.
5. Restart the queue with a `queue run`

### SchedulerFIFOMultiHost

This queue is designed to assign a queue of jobs to a list of available hosts in a first come first server manner. Each host can support a differant maximum number of running jobs.

#### Usage

**Input:** A queue yaml file, a `hosts` list of Host() objects.

`timeout` is the time that will consider a host as dead and mark the job as crashed. The default is 10 minutes.

**Example:**

```
cms queue run fifo_multi a --hosts=pi@red,pi@red01,pi@red02
queue run fifo_multi a --hosts=pi@red,pi@red01,pi@red02
INFO: Starting job: job1 on host:pi@red

# ----------------------------------------------------------------------
# Run: job1
# ----------------------------------------------------------------------

INFO: Running Jobs: ['job1']
INFO: Starting job: job2 on host:pi@red01

# ----------------------------------------------------------------------
# Run: job2
# ----------------------------------------------------------------------

INFO: Running Jobs: ['job1', 'job2']
INFO: Starting job: job3 on host:pi@red02

# ----------------------------------------------------------------------
# Run: job3
# ----------------------------------------------------------------------

INFO: Running Jobs: ['job1', 'job2', 'job3']
INFO: Waiting. All hosts running max jobs.
... OUTPUT TRIMED FOR READABILITY
INFO: Ran Jobs: ['job1', 'job2', 'job3', 'job4', 'job5', 'job6', 'job7', 'job8']
INFO: Completed Jobs: ['job1', 'job2', 'job3', 'job4', 'job5', 'job6', 'job7', 'job8']
```

Jobs are not required to be assigned a 'host' or 'user'. The queue will run all `undefined` and `ready` jobs that are in the queue. `host` and `user` assignemnets in the queue file will be **ignored**. The scheduler will assigne the first available host from `hosts`. 

Currently `hosts` is a list of `user@host` arguments that will be allowed 1 max process per host. To allow multiple jobs per host, simply repeat it in the list.  In the future we will provide a cluster yaml file that can be passed in instead.

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
2. Execute a `queue refresh` to get the latest job states from worker hosts.
3. Re-run the queue with `queue run`

#### Recovery from queue worker failure

To recover from a failed worker host. 

1. Recover the worker host and determine failure cause. 
2. After reboot this host will continue to run the next jobs in the queue to that host.
3. For any job not in an `end` state, change their status to `ready` in the quueue file.
4. Stop or let the queue finish its current run.
5. Restart the queue with a `queue run`

## Reset Jobs in a Queue

If you want to rerun jobs in a queue or recover from a crash you will need to reset the jobs. Resetting a job resets the state to a executable state (`undefined` or `start` depending on `user` and `host` assignment.) It also kills the jobs if they are currently running and removes the job directory from the assigned host.

>WARNING: if you simply replace a job using `queue add` or rerun a job without a `reset` you will not get the result you expect, as the files from the last run will still be present.

```
queue reset [queue=QUEUE] [--experiment=EXPERIMENT] [--name=NAME] [--status=STATUS]
```

If you do not specify a `name` or `status`  argument. Then all jobs with a state other than `end` will be reset.

Use the `name` argument to reset specific jobs.

Use the `status` argument to reset jobs with a specific status (one status only).

Example:

```
cms queue reset a --status=end
queue reset a --status=end
job1 	 old_status:end 	 new_state:ready
job2 	 old_status:end 	 new_state:ready
job3 	 old_status:end 	 new_state:ready
job4 	 old_status:end 	 new_state:ready
job5 	 old_status:end 	 new_state:ready
job6 	 old_status:end 	 new_state:ready
job7 	 old_status:end 	 new_state:ready
job8 	 old_status:end 	 new_state:ready
```

## Refreshing a Queue

If your manager crashed during the execution of a queue, you can get the latest status from the workers using a refresh.

```
queue refresh [queue=QUEUE] [--experiment=EXPERIMENT]
```

Example:

```
cms queue refresh a
queue refresh a
INFO: Refreshing Queue: a
job1 	 old_status:start 	 new_state:end
job2 	 old_status:start 	 new_state:end
job3 	 old_status:start 	 new_state:end
```

## Typical Workflow Example

```
cms cluster create a

cms cluster add a --id=host1 --name=red --user=pi --gpu=0
INFO: Adding host host1 to cluster a

cms cluster add a --id=host2 --name=red01 --user=pi --gpu=0
INFO: Adding host host2 to cluster a

cms cluster add a --id=host3 --name=red01 --user=pi --gpu=1
INFO: Adding host host3 to cluster a

cms cluster add a --id=host[4-6] --name=red02 --user=pi
INFO: Adding host host4 to cluster a
INFO: Adding host host5 to cluster a
INFO: Adding host host6 to cluster a


ENV3) anthony@anthony-ubuntu:~/cm/cloudmesh-queue$ cms cluster list a
cluster list a
+-------+-------+------+--------+-----+-------+----+------------------+
| id    | name  | user | status | gpu | pyenv | ip | max_jobs_allowed |
+-------+-------+------+--------+-----+-------+----+------------------+
| host1 | red   | pi   | active | 0   |       |    | 1                |
| host2 | red01 | pi   | active | 0   |       |    | 1                |
| host3 | red01 | pi   | active | 1   |       |    | 1                |
| host4 | red02 | pi   | active |     |       |    | 1                |
| host5 | red02 | pi   | active |     |       |    | 1                |
| host6 | red02 | pi   | active |     |       |    | 1                |
+-------+-------+------+--------+-----+-------+----+------------------+

cms queue create a

cms queue add a --name=job[0-10] --command="'hostname'"
INFO: Adding job job0 to queue a
INFO: Adding job job1 to queue a
INFO: Adding job job2 to queue a
INFO: Adding job job3 to queue a
INFO: Adding job job4 to queue a
INFO: Adding job job5 to queue a
INFO: Adding job job6 to queue a
INFO: Adding job job7 to queue a
INFO: Adding job job8 to queue a
INFO: Adding job job9 to queue a
INFO: Adding job job10 to queue a

cms queue list a
+-------+-----------+----------+-----+-----------+-----------+------------+
| name  | status    | command  | gpu | output    | log       | experiment |
+-------+-----------+----------+-----+-----------+-----------+------------+
| job0  | undefined | hostname |     | job0.out  | job0.log  | experiment |
| job1  | undefined | hostname |     | job1.out  | job1.log  | experiment |
| job2  | undefined | hostname |     | job2.out  | job2.log  | experiment |
| job3  | undefined | hostname |     | job3.out  | job3.log  | experiment |
| job4  | undefined | hostname |     | job4.out  | job4.log  | experiment |
| job5  | undefined | hostname |     | job5.out  | job5.log  | experiment |
| job6  | undefined | hostname |     | job6.out  | job6.log  | experiment |
| job7  | undefined | hostname |     | job7.out  | job7.log  | experiment |
| job8  | undefined | hostname |     | job8.out  | job8.log  | experiment |
| job9  | undefined | hostname |     | job9.out  | job9.log  | experiment |
| job10 | undefined | hostname |     | job10.out | job10.log | experiment |
+-------+-----------+----------+-----+-----------+-----------+------------+

cms queue run fifo_multi a --hostfile=a
queue run fifo_multi a --hostfile=a
INFO: Starting job: job0 on host:pi@red

# ----------------------------------------------------------------------
# Run: job0
# ----------------------------------------------------------------------

INFO: Running Jobs: ['job0']
INFO: Starting job: job1 on host:pi@red01

# ----------------------------------------------------------------------
# Run: job1
# ----------------------------------------------------------------------

INFO: Running Jobs: ['job0', 'job1']
INFO: Starting job: job2 on host:pi@red01

# ----------------------------------------------------------------------
# Run: job2
# ----------------------------------------------------------------------

INFO: Running Jobs: ['job0', 'job1', 'job2']
INFO: Starting job: job3 on host:pi@red02

# ----------------------------------------------------------------------
# Run: job3
# ----------------------------------------------------------------------

INFO: Running Jobs: ['job0', 'job1', 'job2', 'job3']
INFO: Starting job: job4 on host:pi@red02

# ----------------------------------------------------------------------
# Run: job4
# ----------------------------------------------------------------------

INFO: Running Jobs: ['job0', 'job1', 'job2', 'job3', 'job4']
INFO: Starting job: job5 on host:pi@red02

# ----------------------------------------------------------------------
# Run: job5
# ----------------------------------------------------------------------

INFO: Running Jobs: ['job0', 'job1', 'job2', 'job3', 'job4', 'job5']
INFO: Waiting. All hosts running max jobs.
...OUTPUT TRIMMED FOR READABILITY...
INFO: Running Jobs: ['job5', 'job6', 'job7', 'job8', 'job9', 'job10']
INFO: Ran Jobs: ['job0', 'job1', 'job2', 'job3', 'job4', 'job5', 'job6', 'job7', 'job8', 'job9', 'job10']
INFO: Completed Jobs: ['job0', 'job1', 'job2', 'job3', 'job4', 'job5', 'job6', 'job7', 'job8', 'job9', 'job10']
```

## Service

Cloudmesh Queue provides a REST service implementation of the `Queue` and `Cluster`.  The provided commands allow you to run a REST server and interact with them via interactive documentation and HTTP.
It provides a Basic HTTP authentication scheme to authorize users.

### Commands

Below are the service commands.

```
            queue --service start [--port=PORT]
            queue --service info [--port=PORT]
```

### Service Start

Start the REST service wit the below command.

```
queue --service start [--port=PORT]
```

`port` Allows you to manually set the port. The default value is 8000.

**Example:**

```
cms queue --service start --port=8000
```

Successful completion of the command start the rest server on the local host at 127.0.0.1:8000.

### Service Info

The service info command automatically launches the interactive documentation of the REST service in your web browser.
You will be prompted to enter a username and password that will be used for HTTP basic authentication for all rest calls.

```
queue --service info [--port=PORT]
```

**Example:**

```
cms queue --service info [--port=8000]
```

`port` Allows you to manually set the port if the default was not used.

At this point the interactive web documents will be opened in your web browser at the address [127.0.0.1:8000/docs](127.0.0.1:8000/docs).

Below is an example image of the interactive documentation.

![](https://github.com/cloudmesh/cloudmesh-queue/raw/main/images/rest.png)

### Differences from CMD Line Implementation

When running a Queue via the REST service the rest call will start the queue as a subprocess in the background and return immediately,
this is different from the cmd line implementation which will wait until the queue has finished executing to return. To see the latest status 
of the queue use the `queue refresh` command.