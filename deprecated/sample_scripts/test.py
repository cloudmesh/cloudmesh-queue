from __future__ import print_function
import time, sys
from docopt import docopt
import logging
from datetime import datetime

usage="""
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

out_dir = arguments.get('--output')
in_dir = arguments.get('--input')
gpu = arguments.get('--gpu')

logging.basicConfig(filename='{out_dir}/test_python_script_{dt}.log'.format(out_dir=out_dir, dt=datetime.now().strftime("%m%d%Y_%H%M%S")),
                    level=logging.DEBUG,
                    format='%(asctime)s|%(filename)s|%(levelname)s|%(message)s')

logging.info("Started the python script at {}".format(datetime.now()))

logging.debug("Preparing debug logs.")


logging.debug("Arguments passed: ")
logging.debug(arguments)

logging.debug("Starting the py script.")

logging.debug("Processing sleep 2")

time.sleep(2)
logging.debug("complete")

logging.debug("Processing another sleep 2")
time.sleep(2)
logging.debug("complete")
