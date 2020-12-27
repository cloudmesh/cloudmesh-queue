###############################################################
# cms set host='juliet.futuresystems.org'
# cms set user=$USER
# cms set gpu=0
#
# pytest -v --capture=no tests/test_03_job_gpu.py
# pytest -v  tests/test_03_job_gpu.py
# pytest -v --capture=no  tests/test_03_job_gpu.py::TestJob::<METHODNAME>
###############################################################
import pytest
from cloudmesh.common.Shell import Shell
from cloudmesh.common.debug import VERBOSE
from cloudmesh.common.util import HEADING
from cloudmesh.common.Benchmark import Benchmark
from cloudmesh.common.variables import Variables
from cloudmesh.configuration.Configuration import Configuration
from cloudmesh.common.console import Console
from textwrap import dedent
from cloudmesh.common.util import path_expand

import oyaml as yaml
import re
import time
import getpass

import os
import warnings
import tensorflow as tf
import logging
import io
from contextlib import redirect_stdout
from __future__ import print_function

Benchmark.debug()

variables = Variables()
print(variables)
# variables["jobset"] = path_expand("./a.yaml")

configured_jobset = variables["jobset"]
remote_host_ip = variables["host"] or "juliet.futuresystems.org"
remote_host_user = variables["user"] or getpass.getuser()
gpu_to_use = variables["gpu"] or 0


def tf_function():
    """
    A dummy function to run on selected GPU
    """
    a = tf.constant([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    b = tf.constant([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    c = tf.matmul(a, b)

    return c


@pytest.mark.incremental
class TestJob:
    def test_setup(self):
        HEADING()

        Benchmark.Start()
        # result = Shell.execute("cms job help", shell=True)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)

            logging.getLogger("tensorflow").setLevel(logging.FATAL)

            num_gpus_available = len(
                tf.config.experimental.list_physical_devices("GPU")
            )

            if num_gpus_available > 0:
                tf.debugging.set_log_device_placement(True)

                os.environ["CUDA_VISIBLE_DEVICES"] = gpu_to_use

                out = io.StringIO()
                with redirect_stdout(out):
                    tf_function()

                result = out.getvalue()
                print(result)
            else:
                Console.error("No GPUs are available to run this test.")

        Benchmark.Stop()
        VERBOSE(result)

        assert "device:GPU:" in result

    def test_benchmark(self):
        HEADING()
        Benchmark.print(csv=True)
