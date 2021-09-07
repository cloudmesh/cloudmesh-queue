import os
from cloudmesh.common.Shell import Shell

from cloudmesh.job.service.server import app


class Manager():

    @staticmethod
    def start():
        os.system("uvicorn cloudmesh.job.service.server:app --reload")

    @staticmethod
    def docs(port=8000):
        url = f"http://127.0.0.1:{port}/docs"
        Shell.browser(url)

    @staticmethod
    def show(port=8000, status=None, job_name=None):
        if status is not None:
            url = f"http://127.0.0.1:{port}/print/?status={status}"
        elif job_name is not None:
            url = f"http://127.0.0.1:{port}/print/?job_name={job_name}"
        else:
            url = f"http://127.0.0.1:{port}/print"

        Shell.browser(url)

    @staticmethod
    def ps(port=8000, status=None, job_name=None):
        if status is not None:
            url = f"http://127.0.0.1:{port}/print/?status={status}"
        else:
            url = f"http://127.0.0.1:{port}/print"

        Shell.browser(url)

    @staticmethod
    def run(port=8000, job_name=None):
        if job_name is not None:
            url = f"http://127.0.0.1:{port}/run/?job_name={job_name}"
        else:
            url = f"http://127.0.0.1:{port}/run"

        Shell.browser(url)

    @staticmethod
    def kill(port=8000, job_name=None):
        if job_name is not None:
            url = f"http://127.0.0.1:{port}/run/?job_name={job_name}"
        else:
            url = f"http://127.0.0.1:{port}/run"

        Shell.browser(url)
