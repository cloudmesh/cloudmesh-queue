import os
from cloudmesh.common.Shell import Shell

from cloudmesh.job.service.server import app

class Manager():

    @staticmethod
    def start():
        os.system("uvicorn cloudmesh.job.service.server:app --reload")

    @staticmethod
    def docs(port=8080):
        url = f"http://127.0.0.1:{port}/docs"
        Shell.browser()
