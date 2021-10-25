import os
from cloudmesh.common.Shell import Shell

#
# This manager does not ues DELETE for kill
# This should be more REST like
#


class Manager:

    @staticmethod
    def start():
        os.system("uvicorn cloudmesh.queue.service.server:app --reload")

    '''
    @staticmethod
    def docs(port=8000):
        url = f"http://127.0.0.1:{port}/docs"
        Shell.browser(url)

    @staticmethod
    def job(port=8000, status=None, name=None):
        if status is not None:
            url = f"http://127.0.0.1:{port}/job/?status={status}"
        elif name is not None:
            url = f"http://127.0.0.1:{port}/job/?name={name}"
        else:
            url = f"http://127.0.0.1:{port}/job"

        Shell.browser(url)

    @staticmethod
    def run(port=8000, name=None):
        if name is not None:
            url = f"http://127.0.0.1:{port}/job/run/?name={name}"
        else:
            url = f"http://127.0.0.1:{port}/job/run"

        Shell.browser(url)

    @staticmethod
    def kill(port=8000, name=None):
        if name is not None:
            url = f"http://127.0.0.1:{port}/kill/?name={name}"
        else:
            url = f"http://127.0.0.1:{port}/kill"

        Shell.browser(url)
    '''