import time
import sys
from docopt import docopt
import logging
import tensorflow as tf
import io
import os
import warnings
from contextlib import redirect_stdout
from __future__ import print_function

usage = """
Usage:
    test.py --output=OUTPUT --input=INPUT --gpu=GPU

Options:
    --output=OUTPUT    Location of script output
    --input=INPUT      Location of inputs
    --gpu=GPU          GPU to be used for script execution
"""
print(sys.argv)
print("===")

arguments = docopt(usage)

print(arguments)

out_dir = arguments.get("--output")
in_dir = arguments.get("--input")
gpu = arguments.get("--gpu")


def tf_function():
    """
    A dummy function to run on selected GPU
    """
    a = tf.constant([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    b = tf.constant([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    c = tf.matmul(a, b)

    return c


def call_with_gpu(function_name, gpu_to_use):
    """
    Function to call a subfunction and run it on GPU
    Args:
        function_name (string): The function to be run with gpu
        gpu_to_use (integer): GPU number to be used
    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=FutureWarning)

        logging.getLogger("tensorflow").setLevel(logging.FATAL)

        num_gpus_available = len(
            tf.config.experimental.list_physical_devices("GPU")
        )

        if num_gpus_available > 0:
            tf.debugging.set_log_device_placement(True)

            os.environ["CUDA_VISIBLE_DEVICES"] = gpu_to_use
            logging.debug(f"Execution with GPU: {gpu_to_use}")

            out = io.StringIO()
            with redirect_stdout(out):
                function_name()

            result = out.getvalue()
            logging.debug(result)
            # print(result)


if __name__ == "__main__":
    logging.basicConfig(
        filename="{}/test.log".format(out_dir),
        level=logging.DEBUG,
        format="%(asctime)s|%(filename)s|%(levelname)s|%(message)s",
    )

    logging.debug("Arguments passed: ")
    logging.debug(arguments)
    logging.debug("Start of the script")

    call_with_gpu(function_name=tf_function, gpu_to_use=gpu)

    logging.debug("End of the script")
