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
| Installation Instructions | <https://github.com/cloudmesh/get> |

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
